"""Adaptador de Ollama reservado para uma fase futura.

O arquivo permanece no projeto para não perder o trabalho anterior, mas o fluxo
normal da STAR não o importa nem o chama. A proteção adicional exige que
EXTERNAL_AI_ENABLED esteja explicitamente ativado.
"""

import time

from config import EXTERNAL_AI_ENABLED


class OllamaModel:
    def __init__(self, model_name="qwen3:8b", host="http://127.0.0.1:11434"):
        self.model_name = model_name
        self.host = host

    def _ensure_enabled(self):
        if not EXTERNAL_AI_ENABLED:
            raise RuntimeError("Ollama está reservado para a futura fase de IA e permanece desativado.")

    def is_available(self):
        self._ensure_enabled()
        import requests
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.ok
        except requests.RequestException:
            return False

    def generate(self, prompt, identity, state=None, route=None):
        self._ensure_enabled()
        import requests
        system_prompt = f"""
Você é um componente cognitivo utilizado pela arquitetura STAR.

IDENTIDADE FUNDAMENTAL DA STAR:
{identity}

ESTADO COMPUTACIONAL ATUAL:
{state}

REGRAS:
- Você é um componente da STAR, não a STAR inteira.
- O modelo não define a identidade da STAR.
- Não invente informações.
- Responda em português.
""".strip()
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.7},
        }
        start = time.perf_counter()
        response = requests.post(f"{self.host}/api/generate", json=payload, timeout=180)
        print(f"📡 Ollama respondeu em: {time.perf_counter() - start:.3f}s")
        response.raise_for_status()
        return response.json().get("response", "")
