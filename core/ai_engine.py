"""Engine opcional de modelo de linguagem para recursos da STAR.

Na STAR Foundation este componente permanece desativado por padrão. A identidade,
memória, decisões e capacidades fundamentais da STAR não dependem dele. Chamadores
podem fornecer um timeout menor para superfícies interativas sem alterar o padrão
legado de operações mais longas.
"""

from config import EXTERNAL_AI_ENABLED


class AIEngine:
    def __init__(self, model="qwen3:8b", host="http://localhost:11434", enabled=None):
        self.model = model
        self.host = host
        self.url = f"{host}/api/chat"
        self.enabled = EXTERNAL_AI_ENABLED if enabled is None else bool(enabled)

    def _ensure_enabled(self):
        if not self.enabled:
            raise RuntimeError("AIEngine está desativado na STAR V1.9 Foundation.")

    def is_available(self, *, timeout=3.0):
        self._ensure_enabled()
        import requests
        try:
            return requests.get(self.host, timeout=max(0.1, float(timeout))).status_code == 200
        except requests.RequestException:
            return False

    def generate(self, message, context=None, *, timeout=120.0):
        self._ensure_enabled()
        import json
        import requests

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": message})
        response = requests.post(
            self.url,
            json={"model": self.model, "messages": messages, "stream": True},
            stream=True,
            timeout=max(0.5, float(timeout)),
        )
        response.raise_for_status()
        content = []
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            data = json.loads(line)
            content.append(data.get("message", {}).get("content", ""))
            if data.get("done", False):
                break
        return "".join(content)
