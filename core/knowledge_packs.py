"""Knowledge Packs locais e removíveis da STAR V1.9.

A V1.9 mantém o mecanismo deliberadamente simples: packs estruturados são
carregados e consultados por busca lexical determinística. Mídias removíveis
podem expor packs em STAR_KNOWLEDGE/packs sem copiar o conteúdo para o GitHub.
Embeddings, RAG e ingestão automática de PDF pertencem à V3.0.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import re
import string
import time
import unicodedata

MAX_MANIFEST_BYTES = 1024 * 1024
MAX_CONTENT_BYTES = 64 * 1024 * 1024


def _normalize(text):
    value = unicodedata.normalize("NFD", str(text or "").lower())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def _token_score(query, candidate):
    query_tokens = set(query.split())
    candidate_tokens = set(candidate.split())
    if not query_tokens or not candidate_tokens:
        return 0.0
    intersection = len(query_tokens & candidate_tokens)
    union = len(query_tokens | candidate_tokens)
    return intersection / union if union else 0.0


def _unique_paths(paths):
    result = []
    seen = set()
    for raw in paths:
        try:
            path = Path(raw).expanduser().resolve()
        except (OSError, RuntimeError):
            continue
        key = os.path.normcase(str(path))
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def _as_pack_root(path: Path):
    path = Path(path)
    direct = path if path.name.lower() == "packs" else path / "STAR_KNOWLEDGE" / "packs"
    return direct if direct.is_dir() else None


def discover_removable_pack_roots():
    """Descobre apenas a pasta explícita STAR_KNOWLEDGE/packs em mídias montadas."""
    candidates = []

    configured = os.getenv("STAR_KNOWLEDGE_DRIVES", "").strip()
    if configured:
        for item in configured.split(os.pathsep):
            item = item.strip()
            if item:
                candidate = _as_pack_root(Path(item))
                if candidate:
                    candidates.append(candidate)

    if os.name == "nt":
        for letter in string.ascii_uppercase:
            candidate = Path(f"{letter}:/STAR_KNOWLEDGE/packs")
            if candidate.is_dir():
                candidates.append(candidate)
    else:
        for base in (Path("/media"), Path("/mnt"), Path("/run/media")):
            if not base.is_dir():
                continue
            try:
                for candidate in base.glob("**/STAR_KNOWLEDGE/packs"):
                    if candidate.is_dir():
                        candidates.append(candidate)
            except OSError:
                continue

    return _unique_paths(candidates)


class KnowledgePackManager:
    CONTENT_NAMES = ("knowledge.jsonl", "knowledge.json")

    def __init__(
        self,
        root,
        external_roots=None,
        auto_removable=True,
        removable_refresh_seconds=5.0,
    ):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.external_roots = _unique_paths(external_roots or [])
        self.auto_removable = bool(auto_removable)
        self.removable_refresh_seconds = max(1.0, float(removable_refresh_seconds))
        self.packs = {}
        self.entries = []
        self.conflicts = []
        self._discovered_roots = []
        self._last_removable_check = 0.0
        self.scan()

    def _roots(self):
        roots = [self.root, *self.external_roots]
        if self.auto_removable:
            roots.extend(self._discovered_roots)
        return _unique_paths(roots)

    def scan(self):
        if self.auto_removable:
            self._discovered_roots = discover_removable_pack_roots()
            self._last_removable_check = time.monotonic()

        self.packs = {}
        self.entries = []
        self.conflicts = []

        for root in self._roots():
            if not root.is_dir():
                continue
            storage = "local" if root == self.root else "removable"
            try:
                manifests = sorted(root.rglob("manifest.json"))
            except OSError:
                continue

            for manifest_path in manifests:
                manifest = self._read_manifest(manifest_path)
                if manifest is None:
                    continue

                pack_id = manifest.get("id") or manifest.get("name") or manifest_path.parent.name
                pack_id = str(pack_id).strip()
                if not pack_id:
                    continue
                if pack_id in self.packs:
                    self.conflicts.append(
                        {
                            "id": pack_id,
                            "kept": self.packs[pack_id]["path"],
                            "ignored": str(manifest_path.parent),
                        }
                    )
                    continue

                pack_entries = self._load_entries(manifest_path.parent, manifest, pack_id)
                self.packs[pack_id] = {
                    "manifest": manifest,
                    "path": str(manifest_path.parent),
                    "available": True,
                    "entries": len(pack_entries),
                    "storage": storage,
                }
                self.entries.extend(pack_entries)

        return self.packs

    def refresh_removable(self, force=False):
        if not self.auto_removable:
            return False
        now = time.monotonic()
        if not force and now - self._last_removable_check < self.removable_refresh_seconds:
            return False
        discovered = discover_removable_pack_roots()
        self._last_removable_check = now
        if {str(path) for path in discovered} == {str(path) for path in self._discovered_roots}:
            return False
        self._discovered_roots = discovered
        self.scan()
        return True

    def list(self):
        self.refresh_removable()
        return self.packs

    def stats(self):
        self.refresh_removable()
        return {
            "packs": len(self.packs),
            "entries": len(self.entries),
        }

    def storage_stats(self):
        self.refresh_removable()
        local = sum(1 for pack in self.packs.values() if pack.get("storage") == "local")
        removable = sum(1 for pack in self.packs.values() if pack.get("storage") == "removable")
        return {"local": local, "removable": removable, "conflicts": len(self.conflicts)}

    def search(self, query, threshold=0.62):
        self.refresh_removable()
        normalized_query = _normalize(query)
        if not normalized_query:
            return None

        best = None
        best_score = 0.0

        for entry in self.entries:
            for candidate in entry["_search_texts"]:
                if normalized_query == candidate:
                    score = 1.0
                elif len(candidate.split()) >= 3 and (
                    candidate in normalized_query or normalized_query in candidate
                ):
                    score = 0.94
                else:
                    lexical = _token_score(normalized_query, candidate)
                    similarity = SequenceMatcher(None, normalized_query, candidate).ratio()
                    score = max(lexical, similarity * 0.82)

                if score > best_score:
                    best_score = score
                    best = entry

        if best is None or best_score < threshold:
            return None

        result = {key: value for key, value in best.items() if key != "_search_texts"}
        result["score"] = round(best_score, 4)
        return result

    def answer(self, query):
        result = self.search(query)
        if not result:
            return None
        return result.get("answer") or result.get("content")

    @staticmethod
    def _bounded_text(path: Path, max_bytes: int):
        if path.stat().st_size > max_bytes:
            raise ValueError(f"Arquivo excede o limite de {max_bytes} bytes: {path.name}")
        return path.read_text(encoding="utf-8")

    def _read_manifest(self, path):
        try:
            data = json.loads(self._bounded_text(path, MAX_MANIFEST_BYTES))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def _load_entries(self, pack_dir, manifest, pack_id):
        declared = manifest.get("content_file")
        candidates = [declared] if declared else list(self.CONTENT_NAMES)
        pack_root = Path(pack_dir).resolve()

        for filename in candidates:
            if not filename or not isinstance(filename, str):
                continue
            try:
                path = (pack_root / filename).resolve()
            except (OSError, RuntimeError):
                continue
            if path != pack_root and pack_root not in path.parents:
                continue
            if not path.is_file():
                continue
            try:
                raw_entries = self._read_content(path)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                return []

            entries = []
            for position, raw in enumerate(raw_entries):
                entry = self._prepare_entry(raw, pack_id, manifest, position)
                if entry:
                    entries.append(entry)
            return entries

        return []

    def _read_content(self, path):
        text = self._bounded_text(path, MAX_CONTENT_BYTES)
        if path.suffix.lower() == ".jsonl":
            entries = []
            for line in text.splitlines():
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
            return entries

        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            return data["entries"]
        raise ValueError("Knowledge JSON deve ser uma lista ou conter 'entries'.")

    @staticmethod
    def _prepare_entry(raw, pack_id, manifest, position):
        if not isinstance(raw, dict):
            return None

        answer = str(raw.get("answer") or raw.get("content") or "").strip()
        title = str(raw.get("title") or raw.get("topic") or "").strip()
        aliases = raw.get("aliases") or raw.get("questions") or []
        keywords = raw.get("keywords") or []

        if isinstance(aliases, str):
            aliases = [aliases]
        if isinstance(keywords, str):
            keywords = [keywords]
        if not isinstance(aliases, list) or not isinstance(keywords, list):
            return None
        if not answer:
            return None

        search_values = [title, *aliases, *keywords]
        normalized = []
        for value in search_values:
            item = _normalize(value)
            if item and item not in normalized:
                normalized.append(item)
        if not normalized:
            return None

        source = raw.get("source") or {}
        if not isinstance(source, dict):
            source = {"reference": str(source)}

        return {
            "id": raw.get("id") or f"{pack_id}:{position}",
            "pack_id": pack_id,
            "pack_name": manifest.get("name") or pack_id,
            "title": title,
            "answer": answer,
            "source": source,
            "_search_texts": normalized,
        }
