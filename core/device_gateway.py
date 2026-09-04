"""Ponte LAN experimental para dispositivos STAR.

A V1.9 não implementa o ECOSYSTEM da V9.0. Este módulo fornece somente a
infraestrutura mínima e opt-in necessária para prototipar clientes mobile/watch
sem mover raciocínio para o dispositivo.

Princípio: sensores e interfaces ficam nos endpoints; o STAR Core continua
sendo a única fonte de processamento e resposta.
"""
from __future__ import annotations

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

MAX_JSON_BYTES = 64 * 1024
MAX_MEDIA_BYTES = 16 * 1024 * 1024
PROTOCOL_VERSION = 1

_CONTENT_EXTENSIONS = {
    "audio/mp4": ".m4a",
    "audio/m4a": ".m4a",
    "audio/aac": ".aac",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
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


class DeviceRegistry:
    """Registro local que persiste somente hashes dos tokens de pareamento."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.devices = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(data, dict):
            self.devices = data

    def _save(self) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(self.devices, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def pair(self, device_id: str, name: str, capabilities, token: str, metadata=None) -> None:
        device_id = _safe_device_id(device_id)
        if not isinstance(capabilities, list):
            capabilities = []
        now = _now_ms()
        record = {
            "name": str(name or "STAR Device")[:120],
            "capabilities": [str(item)[:80] for item in capabilities[:32]],
            "metadata": _safe_metadata(metadata),
            "token_sha256": _token_hash(token),
            "paired_at": now,
            "last_seen": now,
        }
        with self._lock:
            self.devices[device_id] = record
            self._save()

    def authenticate(self, device_id: str, token: str) -> bool:
        device_id = _safe_device_id(device_id)
        with self._lock:
            record = self.devices.get(device_id)
            if not record:
                return False
            expected = record.get("token_sha256")
            if not expected or not secrets.compare_digest(expected, _token_hash(token)):
                return False
            record["last_seen"] = _now_ms()
            return True

    def public_record(self, device_id: str):
        device_id = _safe_device_id(device_id)
        with self._lock:
            record = self.devices.get(device_id)
            if not record:
                return None
            return {key: value for key, value in record.items() if key != "token_sha256"}


class _GatewayHandler(BaseHTTPRequestHandler):
    server_version = "STARDeviceGateway/0.2"

    @property
    def gateway(self):
        return self.server.gateway

    def log_message(self, format, *args):
        if self.gateway.verbose:
            super().log_message(format, *args)

    def _json(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self, limit: int) -> bytes:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Content-Length inválido.") from exc
        if length <= 0:
            return b""
        if length > limit:
            raise OverflowError("Payload acima do limite permitido.")
        return self.rfile.read(length)

    def _read_json(self):
        raw = self._read_body(MAX_JSON_BYTES)
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("JSON inválido.") from exc
        if not isinstance(payload, dict):
            raise ValueError("O corpo JSON deve ser um objeto.")
        return payload

    def _auth(self):
        device_id = self.headers.get("X-STAR-Device", "")
        authorization = self.headers.get("Authorization", "")
        token = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
        if not device_id or not token:
            return None
        if not self.gateway.registry.authenticate(device_id, token):
            return None
        return _safe_device_id(device_id)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/v1/health":
            self._json(
                200,
                {
                    "service": "STAR Device Gateway",
                    "status": "online",
                    "protocol": PROTOCOL_VERSION,
                    "runtime_revision": self.gateway.runtime.revision,
                    "mode": "lan",
                },
            )
            return

        if path in {"/v1/device", "/v1/runtime"}:
            device_id = self._auth()
            if not device_id:
                self._json(401, {"error": "unauthorized"})
                return
            record = self.gateway.registry.public_record(device_id)
            if path == "/v1/device":
                self._json(200, {"device_id": device_id, "device": record})
            else:
                self._json(200, self.gateway.runtime.profile_for(record))
            return

        self._json(404, {"error": "not_found"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/v1/pair":
                self._pair()
                return

            device_id = self._auth()
            if not device_id:
                self._json(401, {"error": "unauthorized"})
                return

            if path == "/v1/heartbeat":
                record = self.gateway.registry.public_record(device_id)
                runtime = self.gateway.runtime.profile_for(record)
                client_revision = self.headers.get("X-STAR-Runtime", "")
                self._json(
                    200,
                    {
                        "ok": True,
                        "server_time": _now_ms(),
                        "runtime_revision": runtime["revision"],
                        "runtime_changed": client_revision != runtime["revision"],
                    },
                )
            elif path == "/v1/text":
                self._text(device_id)
            elif path == "/v1/audio":
                self._audio(device_id)
            elif path == "/v1/image":
                self._image(device_id)
            else:
                self._json(404, {"error": "not_found"})
        except OverflowError as exc:
            self._json(413, {"error": "payload_too_large", "detail": str(exc)})
        except ValueError as exc:
            self._json(400, {"error": "bad_request", "detail": str(exc)})
        except Exception as exc:
            self.gateway.last_error = f"{type(exc).__name__}: {exc}"
            self._json(500, {"error": "internal_error", "detail": str(exc)})

    def _pair(self):
        payload = self._read_json()
        supplied = str(payload.get("pairing_code") or "").strip()
        if not secrets.compare_digest(supplied, self.gateway.pairing_code):
            self._json(403, {"error": "invalid_pairing_code"})
            return

        device_id = _safe_device_id(payload.get("device_id"))
        token = secrets.token_urlsafe(32)
        self.gateway.registry.pair(
            device_id=device_id,
            name=payload.get("name") or "STAR Device",
            capabilities=payload.get("capabilities") or [],
            metadata=payload.get("metadata") or {},
            token=token,
        )
        record = self.gateway.registry.public_record(device_id)
        runtime = self.gateway.runtime.profile_for(record)
        self._json(
            200,
            {
                "ok": True,
                "device_id": device_id,
                "token": token,
                "protocol": PROTOCOL_VERSION,
                "runtime": runtime,
            },
        )

    def _text(self, device_id: str):
        payload = self._read_json()
        text = str(payload.get("text") or "").strip()
        if not text:
            raise ValueError("Texto vazio.")
        response = self.gateway.process_text(text)
        self._json(200, {"ok": True, "device_id": device_id, "response": response})

    def _audio(self, device_id: str):
        body = self._read_body(MAX_MEDIA_BYTES)
        if not body:
            raise ValueError("Áudio vazio.")
        content_type = self.headers.get("Content-Type", "audio/mp4").split(";", 1)[0].strip().lower()
        path = self.gateway.save_media("audio", device_id, content_type, body)
        transcript = self.gateway.transcribe(path)
        response = self.gateway.process_text(transcript)
        self._json(
            200,
            {
                "ok": True,
                "device_id": device_id,
                "transcript": transcript,
                "response": response,
            },
        )

    def _image(self, device_id: str):
        body = self._read_body(MAX_MEDIA_BYTES)
        if not body:
            raise ValueError("Imagem vazia.")
        content_type = self.headers.get("Content-Type", "image/jpeg").split(";", 1)[0].strip().lower()
        path = self.gateway.save_media("image", device_id, content_type, body)
        self._json(
            200,
            {
                "ok": True,
                "device_id": device_id,
                "stored": path.name,
                "vision_available": False,
                "message": "Imagem recebida pelo STAR Core. O Vision Engine permanece planejado para a V5.0.",
            },
        )


class DeviceGateway:
    """Servidor LAN leve que entrega entradas de dispositivos ao mesmo StarCore."""

    def __init__(
        self,
        star,
        host: str = "0.0.0.0",
        port: int = 8765,
        runtime_dir: Path | None = None,
        manifest_path: Path | None = None,
        pairing_code: str | None = None,
        verbose: bool = False,
    ):
        self.star = star
        self.host = host
        self.port = int(port)
        self.runtime_dir = Path(runtime_dir or Path.cwd() / "runtime" / "oni")
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.registry = DeviceRegistry(self.runtime_dir / "devices.json")
        self.runtime = DeviceRuntime(Path(manifest_path or Path.cwd() / "STAR_MANIFEST.json"))
        self.pairing_code = pairing_code or f"{secrets.randbelow(1_000_000):06d}"
        self.verbose = verbose
        self.last_error = None
        self._star_lock = threading.Lock()
        self._voice_lock = threading.Lock()
        self._voice_manager = None
        self._thread = None
        self.server = ThreadingHTTPServer((self.host, self.port), _GatewayHandler)
        self.server.daemon_threads = True
        self.server.gateway = self
        self.port = int(self.server.server_address[1])

    @property
    def lan_host(self) -> str:
        if self.host not in {"0.0.0.0", "::"}:
            return self.host
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("192.0.2.1", 9))
            address = sock.getsockname()[0]
            return address or "127.0.0.1"
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return "127.0.0.1"
        finally:
            sock.close()

    @property
    def url(self) -> str:
        return f"http://{self.lan_host}:{self.port}"

    def start(self, background: bool = True):
        if background:
            if self._thread and self._thread.is_alive():
                return self
            self._thread = threading.Thread(
                target=self.server.serve_forever,
                name="star-device-gateway",
                daemon=True,
            )
            self._thread.start()
        else:
            self.server.serve_forever()
        return self

    def stop(self) -> None:
        try:
            self.server.shutdown()
        finally:
            self.server.server_close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def process_text(self, text: str) -> str:
        with self._star_lock:
            return str(self.star.process(text, allow_actions=False))

    def _get_voice_manager(self):
        with self._voice_lock:
            if self._voice_manager is None:
                from voice.manager import VoiceManager
                self._voice_manager = VoiceManager()
            return self._voice_manager

    def transcribe(self, path: Path) -> str:
        return self._get_voice_manager().transcribe(path)

    def save_media(self, kind: str, device_id: str, content_type: str, data: bytes) -> Path:
        extension = _CONTENT_EXTENSIONS.get(content_type)
        if extension is None:
            raise ValueError(f"Tipo de mídia não suportado: {content_type}")
        folder = self.runtime_dir / "inbox" / kind
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{_now_ms()}_{_safe_device_id(device_id)}{extension}"
        path = folder / filename
        path.write_bytes(data)
        return path
