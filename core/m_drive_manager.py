"""Loader oficial de M.drives com leitura compatível de Knowledge Packs legados."""
from __future__ import annotations

import os
from pathlib import Path
import string
import time

from core.knowledge_packs import KnowledgePackManager, _unique_paths


def _as_mdrive_root(path: Path):
    path = Path(path)
    if path.name.lower() in {"m_drives", "packs"}:
        return path if path.is_dir() else None
    for name in ("m_drives", "packs"):
        candidate = path / "STAR_KNOWLEDGE" / name
        if candidate.is_dir():
            return candidate
    return None


def discover_removable_mdrive_roots():
    """Descobre STAR_KNOWLEDGE/m_drives e mantém packs legados como fallback."""
    candidates = []
    configured = os.getenv("STAR_KNOWLEDGE_DRIVES", "").strip()
    if configured:
        for item in configured.split(os.pathsep):
            item = item.strip()
            if item:
                candidate = _as_mdrive_root(Path(item))
                if candidate:
                    candidates.append(candidate)
    if os.name == "nt":
        for letter in string.ascii_uppercase:
            for name in ("m_drives", "packs"):
                candidate = Path(f"{letter}:/STAR_KNOWLEDGE/{name}")
                if candidate.is_dir():
                    candidates.append(candidate)
    else:
        for base in (Path("/media"), Path("/mnt"), Path("/run/media")):
            if not base.is_dir():
                continue
            try:
                for name in ("m_drives", "packs"):
                    for candidate in base.glob(f"**/STAR_KNOWLEDGE/{name}"):
                        if candidate.is_dir():
                            candidates.append(candidate)
            except OSError:
                continue
    return _unique_paths(candidates)


class MDriveManager(KnowledgePackManager):
    """Mesmo loader seguro da Foundation, com identidade pública M.drive."""

    def __init__(self, root, *, legacy_root=None, external_roots=None, auto_removable=True, removable_refresh_seconds=5.0):
        self.legacy_root = Path(legacy_root).resolve() if legacy_root else None
        roots = list(external_roots or [])
        if self.legacy_root and self.legacy_root.exists():
            roots.append(self.legacy_root)
        self._mdrive_auto_removable = bool(auto_removable)
        self._mdrive_refresh_seconds = max(1.0, float(removable_refresh_seconds))
        self._mdrive_discovered = []
        self._mdrive_last_check = 0.0
        super().__init__(root, external_roots=roots, auto_removable=False, removable_refresh_seconds=removable_refresh_seconds)

    def _roots(self):
        return _unique_paths([self.root, *self.external_roots, *self._mdrive_discovered])

    def scan(self):
        if self._mdrive_auto_removable:
            self._mdrive_discovered = discover_removable_mdrive_roots()
            self._mdrive_last_check = time.monotonic()
        self.packs = {}; self.entries = []; self.conflicts = []
        for root in self._roots():
            if not root.is_dir():
                continue
            storage = "local" if root == self.root else ("legacy" if self.legacy_root and root == self.legacy_root else "removable")
            try:
                manifests = sorted(root.rglob("manifest.json"))
            except OSError:
                continue
            for manifest_path in manifests:
                manifest = self._read_manifest(manifest_path)
                if manifest is None:
                    continue
                drive_id = str(manifest.get("id") or manifest.get("name") or manifest_path.parent.name).strip()
                if not drive_id:
                    continue
                if drive_id in self.packs:
                    self.conflicts.append({"id": drive_id, "kept": self.packs[drive_id]["path"], "ignored": str(manifest_path.parent)})
                    continue
                entries = self._load_entries(manifest_path.parent, manifest, drive_id)
                self.packs[drive_id] = {"manifest": manifest, "path": str(manifest_path.parent), "available": True,
                                        "entries": len(entries), "storage": storage, "kind": "m.drive"}
                self.entries.extend(entries)
        return self.packs

    def refresh_removable(self, force=False):
        if not self._mdrive_auto_removable:
            return False
        now = time.monotonic()
        if not force and now - self._mdrive_last_check < self._mdrive_refresh_seconds:
            return False
        discovered = discover_removable_mdrive_roots(); self._mdrive_last_check = now
        if {str(x) for x in discovered} == {str(x) for x in self._mdrive_discovered}:
            return False
        self._mdrive_discovered = discovered
        self.scan(); return True

    def stats(self):
        base = super().stats()
        return {**base, "mdrives": base["packs"], "legacy_name": "Knowledge Packs"}

    def storage_stats(self):
        self.refresh_removable()
        local = sum(1 for drive in self.packs.values() if drive.get("storage") == "local")
        legacy = sum(1 for drive in self.packs.values() if drive.get("storage") == "legacy")
        removable = sum(1 for drive in self.packs.values() if drive.get("storage") == "removable")
        return {"local": local, "legacy": legacy, "removable": removable, "conflicts": len(self.conflicts)}


KnowledgePackManagerCompat = KnowledgePackManager
