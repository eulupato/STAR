"""Biblioteca local de fotos da STAR.

A biblioteca é apenas um índice de caminhos locais. Não copia, envia nem
versiona imagens pessoais.
"""
from __future__ import annotations

from pathlib import Path


class PhotoLibrary:
    SUPPORTED = {".png", ".jpg", ".jpeg", ".webp"}

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser()

    def list_images(self, limit: int = 500) -> list[Path]:
        safe_limit = max(1, min(int(limit), 5000))
        if not self.root.exists() or not self.root.is_dir():
            return []

        items = []
        for path in self.root.rglob("*"):
            try:
                if (
                    path.is_file()
                    and path.suffix.lower() in self.SUPPORTED
                    and path.stat().st_size > 0
                ):
                    items.append(path)
            except OSError:
                continue

        def sort_key(path: Path):
            try:
                modified = path.stat().st_mtime
            except OSError:
                modified = 0.0
            return (-modified, path.name.casefold(), str(path))

        items.sort(key=sort_key)
        return items[:safe_limit]
