"""Cliente leve das superfícies PC-simuladas para o STAR Core único.

Mobile/Watch não constroem outro Core: conectam-se ao Device Gateway iniciado
pela superfície PC. O mesmo contrato é usado pelos clientes físicos.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
import threading
import urllib.error
import urllib.request

from voice.audio_devices import resolve_audio_device

ROOT = Path(__file__).resolve().parents[1]
SESSION_PATH = ROOT / "runtime" / "oni" / "local_session.json"


class GatewayUnavailable(RuntimeError):
    pass


class SurfaceMemory:
    """Evita um segundo writer de chat no star.db nas superfícies clientes."""

    def save(self, *_args, **_kwargs):
        return None

    def close(self):
        return None
class StarEndpointClient:
    def __init__(self, profile: str):
        self.profile = "watch" if profile == "watch" else "mobile"
        self.device_id = f"{self.profile}-pc-simulator"
        self.base_url = ""
        self.token = ""
        self.runtime_revision = ""
        self._lock = threading.RLock()

    def _load_session(self) -> dict:
        try:
            data = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GatewayUnavailable(
                "STAR Core não está disponível. Inicie INICIAR_PC.bat primeiro."
            ) from exc
        local_url = str(data.get("local_url") or "").rstrip("/")
        code = str(data.get("pairing_code") or "").strip()
        if not local_url or not code:
            raise GatewayUnavailable("Sessão local da STAR está incompleta.")
        self.base_url = local_url
        return data

    def _request(self, path: str, *, method="GET", payload=None, raw=None,
                 content_type="application/json", authenticated=True,
                 accept="application/json", timeout=120):
        if not self.base_url:
            self._load_session()
        headers = {"Accept": accept}
        body = raw
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        if body is not None:
            headers["Content-Type"] = content_type
        if authenticated:
            self._ensure_paired()
            headers["Authorization"] = f"Bearer {self.token}"
            headers["X-STAR-Device"] = self.device_id
            if self.runtime_revision:
                headers["X-STAR-Runtime"] = self.runtime_revision
        request = urllib.request.Request(
            self.base_url + path, data=body, method=method, headers=headers
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
                return data, response.headers.get("Content-Type", "")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise GatewayUnavailable(
                "Não consegui alcançar o STAR Core. Confirme que INICIAR_PC.bat está aberto."
            ) from exc

    def _request_json(self, path: str, **kwargs) -> dict:
        raw, _ = self._request(path, **kwargs)
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GatewayUnavailable("Resposta inválida do STAR Core.") from exc
        if not isinstance(data, dict):
            raise GatewayUnavailable("Resposta inesperada do STAR Core.")
        return data

    def _ensure_paired(self):
        with self._lock:
            if self.token:
                return
            session = self._load_session()
            payload = {
                "pairing_code": str(session["pairing_code"]),
                "device_id": self.device_id,
                "name": f"STAR {self.profile.title()} PC Simulator",
                "capabilities": ["microphone", "display", "speaker"],
                "metadata": {
                    "platform": "windows",
                    "form_factor": "watch" if self.profile == "watch" else "phone",
                    "app_version": "simulator",
                },
            }
            data = self._request_json(
                "/v1/pair", method="POST", payload=payload, authenticated=False
            )
            self.token = str(data.get("token") or "")
            runtime = data.get("runtime") or {}
            self.runtime_revision = str(runtime.get("revision") or "")
            if not self.token:
                raise GatewayUnavailable("O STAR Core não concluiu o pareamento local.")

    def health(self) -> dict:
        self._load_session()
        return self._request_json("/v1/health", authenticated=False)

    def process_text(self, text: str) -> str:
        data = self._request_json("/v1/text", method="POST", payload={"text": text})
        return str(data.get("response") or "")

    def process_audio(self, path: Path) -> tuple[str, str]:
        path = Path(path)
        content_type = "audio/wav" if path.suffix.lower() == ".wav" else "audio/mp4"
        data = self._request_json(
            "/v1/audio", method="POST", raw=path.read_bytes(), content_type=content_type
        )
        return str(data.get("transcript") or ""), str(data.get("response") or "")

    def upload_image(self, path: Path) -> dict:
        path = Path(path)
        content_types = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp",
        }
        content_type = content_types.get(path.suffix.lower())
        if content_type is None:
            raise ValueError("Formato de imagem não suportado pelo endpoint.")
        return self._request_json(
            "/v1/image", method="POST", raw=path.read_bytes(), content_type=content_type
        )

    def speech(self, text: str) -> bytes:
        raw, content_type = self._request(
            "/v1/speech", method="POST", payload={"text": text},
            accept="audio/wav", timeout=240
        )
        if "audio/" not in content_type:
            raise GatewayUnavailable("O STAR Core não devolveu áudio válido.")
        return raw

    def set_voice_mode(self, mode: str) -> dict:
        normalized = "fast" if str(mode).lower() == "fast" else "official"
        return self._request_json(
            "/v1/voice-mode", method="POST", payload={"mode": normalized}
        )

    def close(self):
        self.token = ""


class RemoteVoiceAdapter:
    def __init__(self, client: StarEndpointClient):
        self.client = client
        self.mode = "official"
        self.last_tts_engine = "STAR Core"
        self.last_error = None
        self._generation = 0
        self._speaking = False
        self._lock = threading.Lock()

    @property
    def stt_configured(self):
        return True

    @property
    def tts_description(self):
        return "voz oficial gerada pelo STAR Core"

    def set_voice_mode(self, mode: str):
        self.mode = "fast" if str(mode).lower() == "fast" else "official"
        try:
            data = self.client.set_voice_mode(self.mode)
            self.mode = str(data.get("mode") or self.mode)
            self.last_error = None
        except Exception as exc:
            self.last_error = str(exc)
        return self.mode

    def warmup_stt_async(self):
        return None

    @property
    def is_speaking(self):
        with self._lock:
            return bool(self._speaking)

    def cancel_speech(self, reason: str = "manual"):
        with self._lock:
            was_speaking = bool(self._speaking)
            self._generation += 1
            self._speaking = False
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        return was_speaking

    def barge_in(self):
        if not self.is_speaking:
            return False
        self.cancel_speech(reason="barge_in")
        return True

    def _play(self, wav: bytes, generation: int):
        try:
            import soundfile as sf
            import sounddevice as sd
            audio, rate = sf.read(io.BytesIO(wav), dtype="float32", always_2d=False)
            with self._lock:
                if generation != self._generation:
                    return
                self._speaking = True
            sd.play(
                audio,
                rate,
                device=resolve_audio_device("output", sd),
            )
            sd.wait()
        except Exception as exc:
            self.last_error = str(exc)
            raise
        finally:
            with self._lock:
                if generation == self._generation:
                    self._speaking = False

    def speak_async(self, text: str, callback=None):
        self.cancel_speech()
        with self._lock:
            generation = self._generation

        def worker():
            ok, error = True, None
            try:
                wav = self.client.speech(str(text))
                self._play(wav, generation)
                self.last_tts_engine = "STAR Core"
                self.last_error = None
            except Exception as exc:
                ok, error = False, str(exc)
                self.last_error = error
            if callback is not None:
                callback(ok, error)

        threading.Thread(target=worker, daemon=True, name="STAR-RemoteSpeech").start()

    def test_audio_async(self, callback=None):
        self.speak_async("Olá! Eu sou a STAR. Este é o teste da minha voz.", callback)

    def test_official_audio_async(self, callback=None):
        self.speak_async("Teste da voz oficial da STAR.", callback)

    def close(self):
        self.cancel_speech()


class RemoteSurfaceBrain:
    is_remote_endpoint = True

    def __init__(self, profile: str):
        from core.language_manager import LanguageManager
        self.client = StarEndpointClient(profile)
        self.language = LanguageManager()
        self.surface_memory = SurfaceMemory()
        self.surface_voice = RemoteVoiceAdapter(self.client)
        self.proactivity = None
        self.network_enabled = False

    def process(self, text: str, allow_actions=False):
        return self.client.process_text(str(text))

    def process_audio(self, path: Path):
        return self.client.process_audio(Path(path))

    def process_image(self, path: Path, text: str = ""):
        result = self.client.upload_image(Path(path))
        prompt = str(text or "").strip()
        if prompt:
            return self.client.process_text(prompt)
        return str(result.get("message") or "Imagem recebida pelo STAR Core.")

    def close_surface(self):
        self.surface_voice.close()
        self.client.close()
