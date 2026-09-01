"""Registro genérico de ferramentas locais da STAR V3."""
from __future__ import annotations


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, func, enabled=True, description=""):
        self._tools[str(name)] = {
            "func": func,
            "enabled": bool(enabled),
            "description": str(description),
        }

    def available(self):
        return [
            name
            for name, item in self._tools.items()
            if item["enabled"]
        ]

    def call(self, name, *args, **kwargs):
        item = self._tools.get(str(name))
        if item is None or not item["enabled"]:
            raise RuntimeError(f"Ferramenta indisponível: {name}")
        return item["func"](*args, **kwargs)
