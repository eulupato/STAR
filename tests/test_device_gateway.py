import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.device_gateway import DeviceGateway
from clients import device_client


class FakeStar:
    def __init__(self):
        self.last_allow_actions = None

    def process(self, text, allow_actions=True):
        self.last_allow_actions = allow_actions
        return f"STAR:{text}"


class ExplodingStar:
    def process(self, text, allow_actions=True):
        raise RuntimeError("detalhe interno secreto")


def _request(url, method="GET", payload=None, headers=None):
    data = None
    request_headers = dict(headers or {})
    if payload is not None:
        if isinstance(payload, bytes):
            data = payload
        else:
            data = json.dumps(payload).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(url, data=data, method=method, headers=request_headers)
    with urllib.request.urlopen(request, timeout=3) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _error_json(exc):
    return json.loads(exc.read().decode("utf-8"))


def _request_bytes(url, method="GET", payload=None, headers=None):
    data = None
    request_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(url, data=data, method=method, headers=request_headers)
    with urllib.request.urlopen(request, timeout=3) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read()


class FakeVoiceManager:
    def __init__(self):
        self.mode = "official"
        self.tts_description = "fake voice"

    def transcribe(self, _path): return "fala remota"
    def close(self): return None

    def set_voice_mode(self, mode):
        self.mode = mode
        return mode

    def speak_async(self, text, callback=None):
        self.last_spoken = str(text)
        if callback:
            callback(True, None)
        return None

    def synthesize_to_wav(self, text, path):
        import wave
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000)
            wav.writeframes(b"\x00\x00" * max(160, len(str(text)) * 20))
        return path


def _pair(base, device_id="watch-test", code="123456"):
    _, paired = _request(
        base + "/v1/pair",
        method="POST",
        payload={
            "pairing_code": code,
            "device_id": device_id,
            "name": "STAR Watch",
            "capabilities": ["microphone", "camera", "display"],
            "metadata": {
                "platform": "android",
                "form_factor": "watch",
                "os_version": "8.1",
                "app_version": "0.2.0",
            },
        },
    )
    return paired


def _auth_headers(token, device_id="watch-test"):
    return {
        "Authorization": f"Bearer {token}",
        "X-STAR-Device": device_id,
    }


def test_gateway_pairs_routes_and_returns_adaptive_runtime(tmp_path):
    star = FakeStar()
    gateway = DeviceGateway(
        star,
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        manifest_path=ROOT / "STAR_MANIFEST.json",
        pairing_code="123456",
    ).start()
    try:
        base = f"http://127.0.0.1:{gateway.port}"
        status, health = _request(base + "/v1/health")
        assert status == 200
        assert health["status"] == "online"
        assert health["runtime_revision"]

        paired = _pair(base)
        token = paired["token"]
        assert paired["runtime"]["form_factor"] == "watch"
        assert paired["runtime"]["features"]["remote_pc_actions"] is False

        headers = _auth_headers(token)
        _, runtime = _request(base + "/v1/runtime", headers=headers)
        assert runtime["form_factor"] == "watch"
        assert runtime["labels"]["speak"]

        heartbeat_headers = dict(headers)
        heartbeat_headers["X-STAR-Runtime"] = runtime["revision"]
        _, heartbeat = _request(
            base + "/v1/heartbeat",
            method="POST",
            payload={},
            headers=heartbeat_headers,
        )
        assert heartbeat["runtime_changed"] is False

        _, result = _request(
            base + "/v1/text",
            method="POST",
            payload={"text": "olá"},
            headers=headers,
        )
        assert result["response"] == "STAR:olá"
        assert result["voice_started"] is False
        assert star.last_allow_actions is False

        _, world = _request(base + "/v1/world", headers=headers)
        assert world["scenario"] == "cosmic_crystal"
        assert world["day_phase"] in {"dawn", "day", "sunset", "night"}

        _, timezone_result = _request(
            base + "/v1/world/timezone",
            method="POST",
            payload={"timezone": "America/Sao_Paulo"},
            headers=headers,
        )
        assert timezone_result["world"]["timezone"] == "America/Sao_Paulo"

        registry = json.loads((tmp_path / "devices.json").read_text(encoding="utf-8"))
        record = registry["watch-test"]
        assert record["metadata"]["form_factor"] == "watch"
        assert "token_sha256" in record
        assert len(record["token_sha256"]) == 64
        assert "token" not in record
    finally:
        gateway.stop()


def test_local_star_world_surface_keeps_local_pc_actions(tmp_path):
    star = FakeStar()
    gateway = DeviceGateway(
        star,
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        manifest_path=ROOT / "STAR_MANIFEST.json",
        pairing_code="123456",
    ).start()
    try:
        base = f"http://127.0.0.1:{gateway.port}"
        paired = _pair(base, device_id="star-world-pc")
        headers = _auth_headers(paired["token"], device_id="star-world-pc")
        _, result = _request(
            base + "/v1/text",
            method="POST",
            payload={"text": "ação local"},
            headers=headers,
        )
        assert result["response"] == "STAR:ação local"
        assert star.last_allow_actions is True
    finally:
        gateway.stop()


def test_gateway_streams_core_voice_and_cleans_audio_files(tmp_path):
    gateway = DeviceGateway(
        FakeStar(),
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        manifest_path=ROOT / "STAR_MANIFEST.json",
        pairing_code="123456",
    ).start()
    gateway._voice_manager = FakeVoiceManager()
    try:
        base = f"http://127.0.0.1:{gateway.port}"
        paired = _pair(base)
        headers = _auth_headers(paired["token"])

        status, content_type, wav = _request_bytes(
            base + "/v1/speech",
            method="POST",
            payload={"text": "Olá pelo relógio"},
            headers=headers,
        )
        assert status == 200
        assert content_type.startswith("audio/wav")
        assert wav[:4] == b"RIFF"
        speech_dir = tmp_path / "outbox" / "speech"
        assert not list(speech_dir.glob("*.wav"))

        _, spoken = _request(
            base + "/v1/text",
            method="POST",
            payload={"text": "fale comigo", "speak": True},
            headers=headers,
        )
        assert spoken["response"] == "STAR:fale comigo"
        assert spoken["voice_started"] is True
        assert gateway._voice_manager.last_spoken == "STAR:fale comigo"

        _, audio = _request(
            base + "/v1/audio",
            method="POST",
            payload=b"fake-audio",
            headers={**headers, "Content-Type": "audio/wav"},
        )
        assert audio["transcript"] == "fala remota"
        assert audio["response"] == "STAR:fala remota"
        inbox = tmp_path / "inbox" / "audio"
        assert not list(inbox.glob("*"))
    finally:
        gateway.stop()


def test_gateway_rejects_unauthenticated_requests(tmp_path):
    gateway = DeviceGateway(
        FakeStar(),
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        manifest_path=ROOT / "STAR_MANIFEST.json",
        pairing_code="123456",
    ).start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{gateway.port}/v1/text",
            data=b'{"text":"teste"}',
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request, timeout=3)
            assert False, "A requisição sem autenticação deveria falhar."
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
    finally:
        gateway.stop()


def test_pairing_is_rate_limited(tmp_path):
    gateway = DeviceGateway(
        FakeStar(),
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        manifest_path=ROOT / "STAR_MANIFEST.json",
        pairing_code="123456",
        pairing_rate_limit=2,
        pairing_rate_window_seconds=60,
    ).start()
    try:
        base = f"http://127.0.0.1:{gateway.port}"
        for _ in range(2):
            try:
                _pair(base, code="000000")
                assert False, "Código inválido deveria ser rejeitado."
            except urllib.error.HTTPError as exc:
                assert exc.code == 403

        try:
            _pair(base, code="000000")
            assert False, "Terceira tentativa deveria atingir rate limit."
        except urllib.error.HTTPError as exc:
            assert exc.code == 429
            assert _error_json(exc)["error"] == "rate_limited"
    finally:
        gateway.stop()


def test_authenticated_device_requests_are_rate_limited(tmp_path):
    gateway = DeviceGateway(
        FakeStar(),
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        manifest_path=ROOT / "STAR_MANIFEST.json",
        pairing_code="123456",
        device_rate_limit=2,
        device_rate_window_seconds=60,
    ).start()
    try:
        base = f"http://127.0.0.1:{gateway.port}"
        paired = _pair(base)
        headers = _auth_headers(paired["token"])

        _request(base + "/v1/runtime", headers=headers)
        _request(base + "/v1/device", headers=headers)

        request = urllib.request.Request(base + "/v1/runtime", headers=headers)
        try:
            urllib.request.urlopen(request, timeout=3)
            assert False, "Terceira requisição autenticada deveria atingir rate limit."
        except urllib.error.HTTPError as exc:
            assert exc.code == 429
            assert _error_json(exc)["error"] == "rate_limited"
    finally:
        gateway.stop()


def test_internal_errors_are_not_exposed_to_remote_device(tmp_path):
    gateway = DeviceGateway(
        ExplodingStar(),
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        manifest_path=ROOT / "STAR_MANIFEST.json",
        pairing_code="123456",
    ).start()
    try:
        base = f"http://127.0.0.1:{gateway.port}"
        paired = _pair(base)
        headers = _auth_headers(paired["token"])
        request = urllib.request.Request(
            base + "/v1/text",
            data=json.dumps({"text": "teste"}).encode("utf-8"),
            method="POST",
            headers={**headers, "Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request, timeout=3)
            assert False, "Falha interna deveria retornar HTTP 500."
        except urllib.error.HTTPError as exc:
            assert exc.code == 500
            payload = _error_json(exc)
            assert payload == {"error": "internal_error"}
            assert "detalhe interno secreto" not in json.dumps(payload)

        assert "detalhe interno secreto" in gateway.last_error
    finally:
        gateway.stop()


def test_local_surface_client_reuses_pc_core_and_voice(tmp_path, monkeypatch):
    star = FakeStar()
    voice = FakeVoiceManager()
    gateway = DeviceGateway(
        star,
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        manifest_path=ROOT / "STAR_MANIFEST.json",
        pairing_code="123456",
        voice_manager=voice,
    ).start()
    monkeypatch.setattr(device_client, "SESSION_PATH", tmp_path / "local_session.json")
    try:
        client = device_client.StarEndpointClient("mobile")
        assert client.process_text("olá do mobile") == "STAR:olá do mobile"
        assert star.last_allow_actions is False

        wav = tmp_path / "input.wav"
        wav.write_bytes(b"fake-audio")
        transcript, answer = client.process_audio(wav)
        assert transcript == "fala remota"
        assert answer == "STAR:fala remota"

        changed = client.set_voice_mode("fast")
        assert changed["mode"] == "fast"
        assert voice.mode == "fast"

        speech = client.speech("resposta compartilhada")
        assert speech[:4] == b"RIFF"

        session = json.loads((tmp_path / "local_session.json").read_text(encoding="utf-8"))
        assert session["local_url"] == f"http://127.0.0.1:{gateway.port}"
        assert session["pairing_code"] == "123456"
    finally:
        gateway.stop()

    assert not (tmp_path / "local_session.json").exists()


def test_gateway_lazy_voice_manager_uses_chat_mode(tmp_path):
    from config import VOICE_CHAT_MODE

    gateway = DeviceGateway(
        FakeStar(),
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        manifest_path=ROOT / "STAR_MANIFEST.json",
        pairing_code="123456",
    ).start()
    try:
        manager = gateway._get_voice_manager()
        assert manager.mode == VOICE_CHAT_MODE
    finally:
        gateway.stop()


def test_remote_voice_adapter_matches_gui_voice_contract(monkeypatch):
    fake_sd = type("FakeSoundDevice", (), {"stop": staticmethod(lambda: None)})
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)
    adapter = device_client.RemoteVoiceAdapter(object())

    adapter._speaking = True
    assert adapter.is_speaking is True
    assert adapter.cancel_speech(reason="test") is True
    assert adapter.is_speaking is False

    adapter._speaking = True
    assert adapter.barge_in() is True
    assert adapter.is_speaking is False
    assert callable(adapter.test_audio_async)
    assert callable(adapter.test_official_audio_async)
