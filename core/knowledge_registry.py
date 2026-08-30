"""Registro local de Knowledge Packs.

Prepara a arquitetura para futuros pendrives: um pacote pode declarar a ilha,
versão e conteúdo. A instalação real não é feita automaticamente nesta versão.
"""

import json
from pathlib import Path


class KnowledgeRegistry:
    def __init__(self, root=None):
        project_root = Path(__file__).resolve().parent.parent
        self.root = Path(root) if root else project_root / "knowledge" / "packs"
        self.root.mkdir(parents=True, exist_ok=True)

    def scan(self):
        packs = []
        for manifest in sorted(self.root.glob("*/manifest.json")):
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                data["path"] = str(manifest.parent)
                packs.append(data)
            except (OSError, json.JSONDecodeError):
                continue
        return packs
