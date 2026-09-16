"""Engine opcional de modelo local para recursos da STAR.

Modelos permanecem recursos substituíveis: identidade, memória, decisão, fatos,
permissões e execução pertencem à arquitetura STAR. O engine apenas descobre,
seleciona e consulta um servidor Ollama explicitamente habilitado pelo chamador.
"""
from __future__ import annotations

from config import EXTERNAL_AI_ENABLED


class AIEngine:
    def __init__(self, model="qwen3:8b", host="http://localhost:11434", enabled=None):
        self.model = str(model or "qwen3:8b").strip()
        self.host = str(host or "http://localhost:11434").rstrip("/")
        self.url = f"{self.host}/api/chat"
        self.enabled = EXTERNAL_AI_ENABLED if enabled is None else bool(enabled)
        self._resolved_once = False

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

    def list_models(self, *, timeout=1.5) -> tuple[str, ...]:
        """Lista modelos Ollama instalados sem baixar nada."""
        self._ensure_enabled()
        import requests
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=max(0.1, float(timeout)))
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError, TypeError):
            return ()
        names = []
        for item in payload.get("models", ()) if isinstance(payload, dict) else ():
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("model") or "").strip()
            if name and name not in names:
                names.append(name)
        return tuple(names)

    @staticmethod
    def _model_matches(installed: str, wanted: str) -> bool:
        installed = str(installed or "").casefold()
        wanted = str(wanted or "").casefold()
        if not installed or not wanted:
            return False
        if installed == wanted:
            return True
        return installed.split(":", 1)[0] == wanted.split(":", 1)[0]

    def resolve_model(self, preferred=None, *, candidates=(), timeout=1.5, fallback_any: bool = True) -> str | None:
        """Seleciona um modelo já instalado, preferindo o configurado."""
        installed = self.list_models(timeout=timeout)
        if not installed:
            return None
        wanted = str(preferred or self.model or "").strip()
        for name in installed:
            if self._model_matches(name, wanted):
                self.model = name
                self._resolved_once = True
                return name
        for candidate in tuple(candidates or ()):
            for name in installed:
                if self._model_matches(name, candidate) or str(candidate).casefold() in name.casefold():
                    self.model = name
                    self._resolved_once = True
                    return name
        if fallback_any:
            self.model = installed[0]
            self._resolved_once = True
            return installed[0]
        return None

    def pull_model(self, model=None, *, timeout=900.0) -> str:
        """Baixa um modelo somente quando o chamador pede explicitamente."""
        self._ensure_enabled()
        import requests
        name = str(model or self.model or "").strip()
        if not name:
            raise ValueError("modelo vazio")
        response = requests.post(
            f"{self.host}/api/pull",
            json={"name": name, "stream": False},
            timeout=max(5.0, float(timeout)),
        )
        response.raise_for_status()
        self.model = name
        self._resolved_once = True
        return name

    def generate(self, message, context=None, *, timeout=12.0, images=None):
        self._ensure_enabled()
        import json
        import requests

        if not self._resolved_once:
            self.resolve_model(preferred=self.model, timeout=min(max(float(timeout) / 10.0, 0.25), 1.5))

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        user_message = {"role": "user", "content": str(message or "")}
        image_values = [str(value) for value in (images or ()) if str(value)]
        if image_values:
            user_message["images"] = image_values
        messages.append(user_message)
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
