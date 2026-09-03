"""Biblioteca local de fotos da STAR.

A biblioteca é apenas um índice de caminhos locais. Não copia, envia nem
versiona imagens pessoais.
"""
from __future__ import annotations

from pathlib import Path
import shutil


class PhotoLibrary:
    SUPPORTED = {".png", ".jpg", ".jpeg", ".webp"}

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser()

    def ensure_root(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root

    def import_images(
        self,
        paths,
        *,
        limit: int = 200,
    ) -> list[Path]:
        """Copia imagens escolhidas para a biblioteca local.

        Arquivos inválidos são ignorados. Colisões de nome recebem sufixo
        incremental; a origem nunca é apagada.
        """
        root = self.ensure_root()
        safe_limit = max(1, min(int(limit), 1000))
        imported: list[Path] = []

        for raw in list(paths or [])[:safe_limit]:
            source = Path(raw).expanduser()
            try:
                if (
                    not source.is_file()
                    or source.suffix.lower() not in self.SUPPORTED
                    or source.stat().st_size <= 0
                ):
                    continue
            except OSError:
                continue

            try:
                if source.resolve().parent == root.resolve():
                    imported.append(source)
                    continue
            except OSError:
                pass

            target = root / source.name
            counter = 2
            while target.exists():
                target = (
                    root
                    / f"{source.stem}_{counter}{source.suffix.lower()}"
                )
                counter += 1

            try:
                shutil.copy2(source, target)
            except OSError:
                continue
            imported.append(target)

        return imported

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
