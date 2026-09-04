import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.device_gateway import DeviceGateway


class FakeStar:
    def process(self, text):
        return f"STAR:{text}"


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


def test_gateway_pairs_and_routes_text_to_same_core(tmp_path):
    gateway = DeviceGateway(
        FakeStar(),
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
        pairing_code="123456",
    ).start()
    try:
        base = f"http://127.0.0.1:{gateway.port}"
        status, health = _request(base + "/v1/health")
        assert status == 200
        assert health["status"] == "online"

        _, paired = _request(
            base + "/v1/pair",
            method="POST",
            payload={
                "pairing_code": "123456",
                "device_id": "watch-test",
                "name": "STAR Watch",
                "capabilities": ["microphone", "camera", "display"],
            },
        )
        token = paired["token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "X-STAR-Device": "watch-test",
        }
        _, result = _request(
            base + "/v1/text",
            method="POST",
            payload={"text": "olá"},
            headers=headers,
        )
        assert result["response"] == "STAR:olá"

        registry = json.loads((tmp_path / "devices.json").read_text(encoding="utf-8"))
        assert "token" not in json.dumps(registry)
        assert len(registry["watch-test"]["token_sha256"]) == 64
    finally:
        gateway.stop()


def test_gateway_rejects_unauthenticated_requests(tmp_path):
    gateway = DeviceGateway(
        FakeStar(),
        host="127.0.0.1",
        port=0,
        runtime_dir=tmp_path,
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
