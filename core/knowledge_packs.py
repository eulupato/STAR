"""Knowledge Pack Manager local e tolerante a falhas."""
from __future__ import annotations

import json
from pathlib import Path

from core.logging_config import get_logger

log = get_logger("knowledge.packs")


class KnowledgePackManager:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.packs = {}
        self.scan()

    def scan(self):
        self.packs = {}
        for manifest in sorted(self.root.rglob("manifest.json")):
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                name = data.get("id") or data.get("name") or manifest.parent.name
                self.packs[str(name)] = {
                    "manifest": data,
                    "path": str(manifest.parent),
                    "available": True,
                }
            except (OSError, json.JSONDecodeError) as exc:
                log.error("Knowledge Pack inválido em %s: %s", manifest, exc)
        return self.packs

    def list(self):
        return dict(self.packs)
