"""Ponte LAN experimental para dispositivos STAR.

Sensores e interfaces ficam nos endpoints; STAR Core continua como única fonte
de processamento. Telemetria é autenticada, bounded e entregue ao bridge físico
B25/B27. Dispositivo pareado não recebe autoridade operacional por isso.
"""
from __future__ import annotations

from collections import deque
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import socket
import threading
import time
from urllib.parse import urlparse

from core.device_runtime import DeviceRuntime
from core.world_state import WorldStateService

MAX_JSON_BYTES = 64 * 1024
MAX_MEDIA_BYTES = 16 * 1024 * 1024
PROTOCOL_VERSION = 1
PAIRING_RATE_LIMIT = 8
PAIRING_RATE_WINDOW_SECONDS = 60.0
DEVICE_RATE_LIMIT = 120
DEVICE_RATE_WINDOW_SECONDS = 60.0

_CONTENT_EXTENSIONS = {
    "audio/mp4": ".m4a", "audio/m4a": ".m4a", "audio/aac": ".aac",
    "audio/wav": ".wav", "audio/x-wav": ".wav",
    "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
}


def _token_hash(token: str) -> str:
    return sha256(str(token).encode("utf-8")).hexdigest()


def _safe_device_id(value: str) -> str:
    text = "".join(ch for ch in str(value or "") if ch.isalnum() or ch in "-_.")
    return text[:80] or "unknown-device"


def _safe_metadata(value):
    if not isinstance(value, dict):
        return {}
    result = {}
    for key in ("platform", "form_factor", "os_version", "app_version"):
        if key in value:
            result[key] = str(value.get(key) or "")[:80]
    for key in ("screen_width", "screen_height"):
        if key in value:
            try:
                result[key] = max(0, min(10000, int(value.get(key))))
            except (TypeError, ValueError):
                pass
    return result


def _now_ms() -> int:
    return int(time.time() * 1000)


class _RateLimiter:
    def __init__(self, limit: int, window_seconds: float):
        self.limit = max(1, int(limit)); self.window_seconds = max(1.0, float(window_seconds))
        self._events = {}; self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic(); normalized = str(key or "unknown")[:160]
        with self._lock:
            events = self._events.setdefault(normalized, deque()); cutoff = now - self.window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now); return True


class DeviceRegistry:
    """Registro local: persiste hash do token, nunca o bearer token bruto."""

    def __init__(self, path: Path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock(); self.devices = {}; self._load()

    def _load(self) -> None:
        if not self.path.exists(): return
        try: data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return
        if isinstance(data, dict): self.devices = data

    def _save(self) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.devices, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def pair(self, device_id: str, name: str, capabilities, token: str, metadata=None) -> None:
        device_id = _safe_device_id(device_id)
        if not isinstance(capabilities, list): capabilities = []
        now = _now_ms()
        record = {
            "name": str(name or "STAR Device")[:120],
            "capabilities": [str(item)[:80] for item in capabilities[:32]],
            "metadata": _safe_metadata(metadata), "token_sha256": _token_hash(token),
            "paired_at": now, "last_seen": now,
        }
        with self._lock:
            self.devices[device_id] = record; self._save()

    def authenticate(self, device_id: str, token: str) -> bool:
        device_id = _safe_device_id(device_id)
        with self._lock:
            record = self.devices.get(device_id)
            if not record: return False
            expected = record.get("token_sha256")
            if not expected or not secrets.compare_digest(expected, _token_hash(token)): return False
            record["last_seen"] = _now_ms(); return True

    def public_record(self, device_id: str):
        device_id = _safe_device_id(device_id)
        with self._lock:
            record = self.devices.get(device_id)
            if not record: return None
            return {key: value for key, value in record.items() if key != "token_sha256"}


class _GatewayHandler(BaseHTTPRequestHandler):
    server_version = "STARDeviceGateway/0.3"

    @property
    def gateway(self): return self.server.gateway

    def log_message(self, format, *args):
        if self.gateway.verbose: super().log_message(format, *args)

    def _json(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff"); self.end_headers(); self.wfile.write(body)

    def _binary(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status); self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff"); self.end_headers(); self.wfile.write(body)

    def _read_body(self, limit: int) -> bytes:
        try: length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc: raise ValueError("Content-Length inválido.") from exc
        if length <= 0: return b""
        if length > limit: raise OverflowError("Payload acima do limite permitido.")
        return self.rfile.read(length)

    def _read_json(self):
        raw = self._read_body(MAX_JSON_BYTES)
        if not raw: return {}
        try: payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise ValueError("JSON inválido.") from exc
        if not isinstance(payload, dict): raise ValueError("O corpo JSON deve ser um objeto.")
        return payload

    def _auth(self):
        device_id = self.headers.get("X-STAR-Device", ""); authorization = self.headers.get("Authorization", "")
        token = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
        if not device_id or not token or not self.gateway.registry.authenticate(device_id, token): return None
        return _safe_device_id(device_id)

    def _rate_limited(self, device_id: str) -> bool:
        if self.gateway.allow_device_request(device_id): return False
        self._json(429, {"error": "rate_limited"}); return True

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/v1/health":
            self._json(200, {"service": "STAR Device Gateway", "status": "online", "protocol": PROTOCOL_VERSION,
                             "runtime_revision": self.gateway.runtime.revision, "mode": "lan",
                             "sensor_transport": self.gateway.sensor_hub is not None, "speech_transport": True})
            return
        if path in {"/v1/device", "/v1/runtime", "/v1/world"}:
            device_id = self._auth()
            if not device_id: self._json(401, {"error": "unauthorized"}); return
            if self._rate_limited(device_id): return
            if path == "/v1/device":
                record = self.gateway.registry.public_record(device_id)
                self._json(200, {"device_id": device_id, "device": record})
            elif path == "/v1/runtime":
                record = self.gateway.registry.public_record(device_id)
                self._json(200, self.gateway.runtime.profile_for(record))
            else:
                self._json(200, self.gateway.world_state.snapshot(online=bool(getattr(self.gateway.star, "network_enabled", False))))
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/v1/pair":
                client_ip = self.client_address[0] if self.client_address else "unknown"
                if not self.gateway.allow_pair_attempt(client_ip): self._json(429, {"error": "rate_limited"}); return
                self._pair(); return
            device_id = self._auth()
            if not device_id: self._json(401, {"error": "unauthorized"}); return
            if self._rate_limited(device_id): return
            if path == "/v1/heartbeat":
                record = self.gateway.registry.public_record(device_id); runtime = self.gateway.runtime.profile_for(record)
                client_revision = self.headers.get("X-STAR-Runtime", "")
                self._json(200, {"ok": True, "server_time": _now_ms(), "runtime_revision": runtime["revision"],
                                 "runtime_changed": client_revision != runtime["revision"]})
            elif path == "/v1/text": self._text(device_id)
            elif path == "/v1/audio": self._audio(device_id)
            elif path == "/v1/speech": self._speech(device_id)
            elif path == "/v1/voice-mode": self._voice_mode(device_id)
            elif path == "/v1/world/timezone": self._world_timezone(device_id)
            elif path == "/v1/world/scenario": self._world_scenario(device_id)
            elif path == "/v1/world/skin": self._world_skin(device_id)
            elif path == "/v1/image": self._image(device_id)
            elif path == "/v1/sensors": self._sensors(device_id)
            else: self._json(404, {"error": "not_found"})
        except OverflowError as exc: self._json(413, {"error": "payload_too_large", "detail": str(exc)})
        except ValueError as exc: self._json(400, {"error": "bad_request", "detail": str(exc)})
        except Exception as exc:
            self.gateway.last_error = f"{type(exc).__name__}: {exc}"
            self._json(500, {"error": "internal_error"})

    def _pair(self):
        payload = self._read_json(); supplied = str(payload.get("pairing_code") or "").strip()
        if not secrets.compare_digest(supplied, self.gateway.pairing_code): self._json(403, {"error": "invalid_pairing_code"}); return
        device_id = _safe_device_id(payload.get("device_id")); token = secrets.token_urlsafe(32)
        self.gateway.registry.pair(device_id=device_id, name=payload.get("name") or "STAR Device",
                                   capabilities=payload.get("capabilities") or [], metadata=payload.get("metadata") or {}, token=token)
        record = self.gateway.registry.public_record(device_id); runtime = self.gateway.runtime.profile_for(record)
        self._json(200, {"ok": True, "device_id": device_id, "token": token, "protocol": PROTOCOL_VERSION, "runtime": runtime})

    def _text(self, device_id: str):
        payload = self._read_json(); value = str(payload.get("text") or "").strip()
        if not value: raise ValueError("Texto vazio.")
        client_ip = self.client_address[0] if self.client_address else ""
        allow_actions = self.gateway.is_trusted_local_surface(device_id, client_ip)
        response = self.gateway.process_text(value, allow_actions=allow_actions)
        voice_started = False
        if bool(payload.get("speak", False)):
            manager = self.gateway._get_voice_manager()
            manager.speak_async(response)
            voice_started = True
        self._json(200, {
            "ok": True,
            "device_id": device_id,
            "response": response,
            "voice_started": voice_started,
        })

    def _world_timezone(self, device_id: str):
        payload = self._read_json()
        timezone_id = str(payload.get("timezone") or "").strip()
        if not timezone_id:
            raise ValueError("Fuso horário vazio.")
        self._json(200, {
            "ok": True,
            "device_id": device_id,
            "world": self.gateway.world_state.set_timezone(timezone_id),
        })

    def _world_scenario(self, device_id: str):
        payload = self._read_json()
        scenario_id = str(payload.get("scenario") or "").strip()
        if not scenario_id:
            raise ValueError("Cenário vazio.")
        self._json(200, {
            "ok": True,
            "device_id": device_id,
            "world": self.gateway.world_state.set_scenario(scenario_id),
        })

    def _world_skin(self, device_id: str):
        payload = self._read_json()
        skin_id = str(payload.get("skin") or "").strip()
        if not skin_id:
            raise ValueError("Skin vazia.")
        self._json(200, {
            "ok": True,
            "device_id": device_id,
            "world": self.gateway.world_state.set_skin(skin_id),
        })

    def _audio(self, device_id: str):
        body = self._read_body(MAX_MEDIA_BYTES)
        if not body: raise ValueError("Áudio vazio.")
        content_type = self.headers.get("Content-Type", "audio/mp4").split(";", 1)[0].strip().lower()
        path = self.gateway.save_media("audio", device_id, content_type, body)
        try:
            transcript = self.gateway.transcribe(path)
            response = self.gateway.process_text(transcript)
        finally:
            try: path.unlink(missing_ok=True)
            except OSError: pass
        self._json(200, {"ok": True, "device_id": device_id, "transcript": transcript, "response": response})

    def _speech(self, device_id: str):
        payload = self._read_json(); text = str(payload.get("text") or "").strip()
        if not text: raise ValueError("Texto vazio para fala.")
        path = self.gateway.synthesize_speech(text, device_id)
        try:
            self._binary(200, path.read_bytes(), "audio/wav")
        finally:
            try: path.unlink(missing_ok=True)
            except OSError: pass

    def _voice_mode(self, device_id: str):
        payload = self._read_json()
        mode = str(payload.get("mode") or "").strip().lower()
        if mode not in {"official", "fast"}:
            raise ValueError("Modo de voz inválido.")
        manager = self.gateway._get_voice_manager()
        manager.set_voice_mode(mode)
        self._json(200, {
            "ok": True,
            "device_id": device_id,
            "mode": manager.mode,
            "description": manager.tts_description,
        })

    def _image(self, device_id: str):
        body = self._read_body(MAX_MEDIA_BYTES)
        if not body: raise ValueError("Imagem vazia.")
        content_type = self.headers.get("Content-Type", "image/jpeg").split(";", 1)[0].strip().lower()
        path = self.gateway.save_media("image", device_id, content_type, body)
        runtime = getattr(self.gateway.star, "perception_runtime", None)
        if runtime is None:
            self._json(200, {"ok": True, "device_id": device_id, "stored": path.name, "vision_available": False,
                             "message": "Imagem recebida; runtime perceptivo indisponível nesta sessão."}); return
        try:
            result = runtime.ingest_image(path, source=f"device:{device_id}:image")
            semantic = result.get("semantic") or {}
            scene = str(semantic.get("scene") or "").strip() if isinstance(semantic, dict) else ""
            message = scene or f"Imagem recebida e registrada no B25 ({result.get('faces_detected', 0)} rosto(s) detectado(s))."
            self._json(200, {"ok": True, "device_id": device_id, "stored": path.name, "vision_available": True,
                             "semantic_available": bool(result.get("semantic_available")), "message": message})
        except Exception as exc:
            self.gateway.last_error = f"vision:{type(exc).__name__}: {exc}"
            self._json(200, {"ok": True, "device_id": device_id, "stored": path.name, "vision_available": False,
                             "vision_error_type": type(exc).__name__,
                             "message": "Imagem recebida, mas a análise perceptiva local não ficou disponível."})

    def _sensors(self, device_id: str):
        if self.gateway.sensor_hub is None: raise ValueError("bridge de sensores indisponível")
        payload = self._read_json(); record = self.gateway.registry.public_record(device_id) or {}
        result = self.gateway.sensor_hub.ingest(device_id, payload, capabilities=record.get("capabilities") or ())
        # Não ecoa coordenadas/telemetria inteira desnecessariamente ao cliente.
        self._json(200, {"ok": True, "device_id": device_id, "accepted": result["accepted"], "rejected": result["rejected"],
                         "operational_authorization": False})


class DeviceGateway:
    """Servidor LAN leve que entrega entradas autenticadas ao mesmo StarCore."""

    def __init__(self, star, host: str = "0.0.0.0", port: int = 8765, runtime_dir: Path | None = None,
                 manifest_path: Path | None = None, pairing_code: str | None = None, verbose: bool = False,
                 pairing_rate_limit: int = PAIRING_RATE_LIMIT, pairing_rate_window_seconds: float = PAIRING_RATE_WINDOW_SECONDS,
                 device_rate_limit: int = DEVICE_RATE_LIMIT, device_rate_window_seconds: float = DEVICE_RATE_WINDOW_SECONDS,
                 voice_manager=None, world_state=None):
        self.star = star; self.host = host; self.port = int(port)
        self.runtime_dir = Path(runtime_dir or Path.cwd() / "runtime" / "oni"); self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.registry = DeviceRegistry(self.runtime_dir / "devices.json")
        self.runtime = DeviceRuntime(Path(manifest_path or Path.cwd() / "STAR_MANIFEST.json"))
        self.sensor_hub = getattr(star, "device_sensors", None)
        self.world_state = world_state or WorldStateService()
        self.pairing_code = pairing_code or f"{secrets.randbelow(1_000_000):06d}"
        self.verbose = verbose; self.last_error = None
        self._pair_limiter = _RateLimiter(pairing_rate_limit, pairing_rate_window_seconds)
        self._device_limiter = _RateLimiter(device_rate_limit, device_rate_window_seconds)
        self._star_lock = threading.Lock(); self._voice_lock = threading.Lock()
        self._voice_manager = voice_manager
        self._owns_voice_manager = voice_manager is None
        self._thread = None
        self._session_id = secrets.token_hex(12)
        self._session_path = self.runtime_dir / "local_session.json"
        self.server = ThreadingHTTPServer((self.host, self.port), _GatewayHandler); self.server.daemon_threads = True
        self.server.gateway = self; self.port = int(self.server.server_address[1])

    @property
    def lan_host(self) -> str:
        if self.host not in {"0.0.0.0", "::"}: return self.host
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("192.0.2.1", 9)); address = sock.getsockname()[0]; return address or "127.0.0.1"
        except OSError:
            try: return socket.gethostbyname(socket.gethostname())
            except OSError: return "127.0.0.1"
        finally: sock.close()

    @property
    def url(self) -> str: return f"http://{self.lan_host}:{self.port}"
    def allow_pair_attempt(self, client_ip: str) -> bool: return self._pair_limiter.allow(client_ip)
    def allow_device_request(self, device_id: str) -> bool: return self._device_limiter.allow(_safe_device_id(device_id))

    def is_trusted_local_surface(self, device_id: str, client_ip: str) -> bool:
        return (
            _safe_device_id(device_id) == "star-world-pc"
            and str(client_ip or "") in {"127.0.0.1", "::1"}
        )

    def _write_local_session(self) -> None:
        payload = {
            "session_id": self._session_id,
            "local_url": f"http://127.0.0.1:{self.port}",
            "lan_url": self.url,
            "pairing_code": self.pairing_code,
            "protocol": PROTOCOL_VERSION,
            "runtime_revision": self.runtime.revision,
        }
        temp = self._session_path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self._session_path)

    def start(self, background: bool = True):
        self._write_local_session()
        if background:
            if self._thread and self._thread.is_alive(): return self
            self._thread = threading.Thread(target=self.server.serve_forever, name="star-device-gateway", daemon=True); self._thread.start()
        else: self.server.serve_forever()
        return self

    def stop(self) -> None:
        try: self.server.shutdown()
        finally: self.server.server_close()
        if self._thread and self._thread.is_alive(): self._thread.join(timeout=1.0)
        try:
            current = json.loads(self._session_path.read_text(encoding="utf-8"))
            if current.get("session_id") == self._session_id:
                self._session_path.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError):
            pass
        manager = self._voice_manager
        if manager is not None and self._owns_voice_manager:
            try: manager.close()
            except Exception: pass

    def process_text(self, text_value: str, *, allow_actions: bool = False) -> str:
        with self._star_lock:
            return str(self.star.process(text_value, allow_actions=bool(allow_actions)))

    def _get_voice_manager(self):
        with self._voice_lock:
            if self._voice_manager is None:
                from config import VOICE_CHAT_MODE
                from voice.manager import VoiceManager
                self._voice_manager = VoiceManager()
                self._voice_manager.set_voice_mode(VOICE_CHAT_MODE)
            return self._voice_manager

    def transcribe(self, path: Path) -> str: return self._get_voice_manager().transcribe(path)

    def synthesize_speech(self, text: str, device_id: str) -> Path:
        folder = self.runtime_dir / "outbox" / "speech"
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{_now_ms()}_{_safe_device_id(device_id)}_{secrets.token_hex(4)}.wav"
        return self._get_voice_manager().synthesize_to_wav(text, folder / filename)

    def save_media(self, kind: str, device_id: str, content_type: str, data: bytes) -> Path:
        extension = _CONTENT_EXTENSIONS.get(content_type)
        if extension is None: raise ValueError(f"Tipo de mídia não suportado: {content_type}")
        folder = self.runtime_dir / "inbox" / kind; folder.mkdir(parents=True, exist_ok=True)
        filename = f"{_now_ms()}_{_safe_device_id(device_id)}{extension}"; path = folder / filename; path.write_bytes(data); return path
