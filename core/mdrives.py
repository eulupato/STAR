"""M.drives: módulos removíveis de memória/conhecimento da STAR.

M.drive = Memory + Drive/Pendrive. Esta camada substitui o nome público
"Knowledge Pack" sem quebrar instalações anteriores: manifests legados em
``knowledge/packs`` continuam legíveis e podem ser migrados explicitamente.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
import shutil


SUPPORTED_ENTRY_SUFFIXES = {".json", ".jsonl", ".txt", ".md", ".csv", ".pdf"}


@dataclass(frozen=True)
class MDriveInfo:
    drive_id: str
    name: str
    version: str
    path: str
    legacy: bool
    domains: tuple[str, ...]
    entries: int
    manifest: dict


class MDriveRegistry:
    """Descobre M.drives locais com compatibilidade de leitura legada."""

    def __init__(self, root=None, *, legacy_root=None):
        project_root = Path(__file__).resolve().parent.parent
        self.root = Path(root) if root else project_root / "knowledge" / "m_drives"
        self.legacy_root = Path(legacy_root) if legacy_root else project_root / "knowledge" / "packs"
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _entry_count(folder: Path, manifest: dict) -> int:
        declared = manifest.get("entries")
        if isinstance(declared, int) and declared >= 0:
            return declared
        count = 0
        for path in folder.rglob("*"):
            if path.is_file() and path.name != "manifest.json" and path.suffix.lower() in SUPPORTED_ENTRY_SUFFIXES:
                count += 1
        return count

    @staticmethod
    def _normalize(manifest: dict, folder: Path, *, legacy: bool) -> MDriveInfo:
        name = str(manifest.get("name") or manifest.get("title") or folder.name).strip() or folder.name
        drive_id = str(manifest.get("id") or manifest.get("drive_id") or folder.name).strip()
        version = str(manifest.get("version") or "1")
        domains_raw = manifest.get("domains") or manifest.get("subjects") or []
        if isinstance(domains_raw, str):
            domains_raw = [domains_raw]
        domains = tuple(sorted({str(x).strip() for x in domains_raw if str(x).strip()}))
        normalized = dict(manifest)
        normalized.update({
            "id": drive_id,
            "name": name,
            "version": version,
            "kind": "m.drive",
            "legacy_knowledge_pack": bool(legacy),
        })
        return MDriveInfo(
            drive_id=drive_id,
            name=name,
            version=version,
            path=str(folder),
            legacy=bool(legacy),
            domains=domains,
            entries=MDriveRegistry._entry_count(folder, normalized),
            manifest=normalized,
        )

    def _scan_root(self, root: Path, *, legacy: bool) -> list[MDriveInfo]:
        if not root.exists():
            return []
        drives: list[MDriveInfo] = []
        for manifest_path in sorted(root.glob("*/manifest.json")):
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    continue
                drives.append(self._normalize(data, manifest_path.parent, legacy=legacy))
            except (OSError, json.JSONDecodeError, UnicodeError):
                continue
        return drives

    def scan(self, *, include_legacy: bool = True) -> list[dict]:
        """Retorna manifests normalizados; M.drive atual vence duplicata legada."""
        current = self._scan_root(self.root, legacy=False)
        by_id = {item.drive_id.casefold(): item for item in current}
        if include_legacy:
            for item in self._scan_root(self.legacy_root, legacy=True):
                by_id.setdefault(item.drive_id.casefold(), item)
        return [asdict(item) for item in sorted(by_id.values(), key=lambda x: (x.name.casefold(), x.drive_id.casefold()))]

    def resolve(self, name_or_id: str) -> dict | None:
        needle = str(name_or_id).strip().casefold()
        for drive in self.scan():
            if drive["drive_id"].casefold() == needle or drive["name"].casefold() == needle:
                return drive
        return None

    def stats(self) -> dict:
        drives = self.scan()
        return {
            "name": "M.drives",
            "meaning": "Memory + Drives/Pendrives",
            "drives": len(drives),
            "legacy_drives": sum(1 for d in drives if d["legacy"]),
            "entries": sum(int(d["entries"]) for d in drives),
            "root": str(self.root),
            "legacy_root": str(self.legacy_root),
        }

    def migrate_legacy(self, *, dry_run: bool = True) -> dict:
        """Copia M.drives legados para o novo diretório; nunca apaga a origem."""
        planned, migrated, skipped = [], [], []
        for item in self._scan_root(self.legacy_root, legacy=True):
            source = Path(item.path)
            target = self.root / source.name
            planned.append({"source": str(source), "target": str(target), "id": item.drive_id})
            if target.exists():
                skipped.append(item.drive_id)
                continue
            if not dry_run:
                shutil.copytree(source, target)
                migrated.append(item.drive_id)
        return {"dry_run": bool(dry_run), "planned": planned, "migrated": migrated, "skipped": skipped}


KnowledgeRegistry = MDriveRegistry
