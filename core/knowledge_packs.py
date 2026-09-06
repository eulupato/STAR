"""Knowledge Packs locais e removíveis da STAR V1.9.

A V1.9 mantém o mecanismo deliberadamente simples: packs estruturados são
carregados e consultados por busca lexical determinística. Mídias removíveis
podem expor packs em STAR_KNOWLEDGE/packs sem copiar o conteúdo para o GitHub.
Catálogos grandes e somente-inventário podem ser instalados em knowledge/local/
e são carregados sob demanda, sem inflar o boot da STAR.

Embeddings, RAG e ingestão automática de PDF pertencem à V3.0.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import hashlib
import json
import os
from pathlib import Path
import re
import string
import time
import unicodedata

MAX_MANIFEST_BYTES = 1024 * 1024
MAX_CONTENT_BYTES = 64 * 1024 * 1024
MAX_CATALOG_BYTES = 16 * 1024 * 1024
MAX_CATALOG_RESULTS = 500


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
    CATALOG_TYPES = {"PERSONAGEM": "character", "EQUIPE": "team"}

    def __init__(
        self,
        root,
        external_roots=None,
        auto_removable=True,
        removable_refresh_seconds=5.0,
        local_catalog_root=None,
    ):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.external_roots = _unique_paths(external_roots or [])
        self.auto_removable = bool(auto_removable)
        self.removable_refresh_seconds = max(1.0, float(removable_refresh_seconds))
        self.local_catalog_root = Path(
            local_catalog_root or (self.root.parent / "local")
        ).expanduser().resolve()
        self.packs = {}
        self.entries = []
        self.conflicts = []
        self._catalog_cache = {}
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
        self._catalog_cache = {}

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
                catalog = self._catalog_descriptor(manifest_path.parent, manifest, pack_id)
                self.packs[pack_id] = {
                    "manifest": manifest,
                    "path": str(manifest_path.parent),
                    "available": True,
                    "entries": len(pack_entries),
                    "storage": storage,
                    "catalog": catalog,
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

    def list_entries(self, pack_id=None):
        """Retorna entradas públicas sem os textos internos usados pelo índice."""
        self.refresh_removable()
        selected = self.entries
        if pack_id is not None:
            wanted = str(pack_id)
            selected = [entry for entry in selected if entry.get("pack_id") == wanted]
        return [
            {key: value for key, value in entry.items() if key != "_search_texts"}
            for entry in selected
        ]

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

    def search(self, query, threshold=0.62, pack_id=None):
        """Busca lexical opcionalmente restrita a um pack específico."""
        self.refresh_removable()
        normalized_query = _normalize(query)
        if not normalized_query:
            return None

        best = None
        best_score = 0.0
        wanted_pack = None if pack_id is None else str(pack_id)

        for entry in self.entries:
            if wanted_pack is not None and entry.get("pack_id") != wanted_pack:
                continue
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

    def answer(self, query, pack_id=None):
        result = self.search(query, pack_id=pack_id)
        if not result:
            return None
        return result.get("answer") or result.get("content")

    def catalog_stats(self, pack_id):
        """Retorna estado/contagens do catálogo grande associado a um pack sem carregá-lo."""
        self.refresh_removable()
        pack = self.packs.get(str(pack_id))
        if not pack:
            return {
                "available": False,
                "total": 0,
                "characters": 0,
                "teams": 0,
                "expected_total": 0,
            }
        descriptor = dict(pack.get("catalog") or {})
        return {
            "available": bool(descriptor.get("available")),
            "total": int(descriptor.get("total") or 0),
            "characters": int(descriptor.get("characters") or 0),
            "teams": int(descriptor.get("teams") or 0),
            "expected_total": int(descriptor.get("expected_total") or 0),
            "path": descriptor.get("path"),
            "source": descriptor.get("source") or {},
            "loaded": str(pack_id) in self._catalog_cache,
        }

    def catalog_list(self, pack_id, entity_type=None, limit=120, offset=0):
        """Lista uma janela pequena do catálogo sem despejar 100k itens na GUI."""
        cache = self._load_catalog(str(pack_id))
        if not cache:
            return []
        key = self._catalog_type_key(entity_type)
        items = cache[key]
        limit = max(1, min(int(limit), MAX_CATALOG_RESULTS))
        offset = max(0, int(offset))
        return [self._public_catalog_item(item, str(pack_id)) for item in items[offset:offset + limit]]

    def catalog_search(self, query, pack_id, entity_type=None, limit=120):
        """Busca rápida no inventário local sem fuzzy pesado/RAG."""
        normalized_query = _normalize(query)
        if not normalized_query:
            return self.catalog_list(pack_id, entity_type=entity_type, limit=limit)

        cache = self._load_catalog(str(pack_id))
        if not cache:
            return []
        items = cache[self._catalog_type_key(entity_type)]
        limit = max(1, min(int(limit), MAX_CATALOG_RESULTS))

        ranked = []
        for item in items:
            candidate = item["_normalized"]
            if normalized_query == candidate:
                rank = 0
            elif candidate.startswith(normalized_query):
                rank = 1
            elif f" {normalized_query}" in candidate:
                rank = 2
            elif normalized_query in candidate:
                rank = 3
            else:
                continue
            ranked.append((rank, len(candidate), item["title"].casefold(), item))

        ranked.sort(key=lambda row: (row[0], row[1], row[2]))
        return [self._public_catalog_item(row[3], str(pack_id)) for row in ranked[:limit]]

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

    def _catalog_descriptor(self, pack_dir, manifest, pack_id):
        spec = manifest.get("catalog")
        if not isinstance(spec, dict):
            return {
                "available": False,
                "total": 0,
                "characters": 0,
                "teams": 0,
                "expected_total": 0,
            }

        counts = spec.get("expected_counts") or {}
        if not isinstance(counts, dict):
            counts = {}
        expected_characters = self._safe_int(counts.get("characters"))
        expected_teams = self._safe_int(counts.get("teams"))
        expected_total = self._safe_int(counts.get("total")) or (
            expected_characters + expected_teams
        )

        filename = spec.get("file") or "catalog.tsv"
        if not isinstance(filename, str) or not filename.strip():
            filename = "catalog.tsv"
        filename = filename.strip()

        path = self._resolve_catalog_path(pack_dir, pack_id, filename)
        meta = self._read_catalog_meta(path) if path else {}
        characters = self._safe_int(meta.get("characters")) or expected_characters
        teams = self._safe_int(meta.get("teams")) or expected_teams
        total = self._safe_int(meta.get("total")) or (
            characters + teams if characters or teams else expected_total
        )

        source = spec.get("source") or {}
        if not isinstance(source, dict):
            source = {"reference": str(source)}

        return {
            "available": bool(path and path.is_file()),
            "path": str(path) if path else None,
            "file": filename,
            "total": total if path else 0,
            "characters": characters if path else 0,
            "teams": teams if path else 0,
            "expected_total": expected_total,
            "expected_characters": expected_characters,
            "expected_teams": expected_teams,
            "source": source,
            "meta": meta,
        }

    def _resolve_catalog_path(self, pack_dir, pack_id, filename):
        """Resolve somente dois locais autorizados: overlay local ou o próprio pack."""
        relative = Path(filename)
        if relative.is_absolute() or ".." in relative.parts:
            return None

        local_root = (self.local_catalog_root / str(pack_id)).resolve()
        local_candidate = (local_root / relative).resolve()
        if local_candidate == local_root or local_root in local_candidate.parents:
            if local_candidate.is_file():
                return local_candidate

        pack_root = Path(pack_dir).resolve()
        bundled = (pack_root / relative).resolve()
        if bundled == pack_root or pack_root in bundled.parents:
            if bundled.is_file():
                return bundled
        return None

    def _read_catalog_meta(self, catalog_path):
        if not catalog_path:
            return {}
        meta_path = catalog_path.with_name("catalog.meta.json")
        if not meta_path.is_file():
            return {}
        try:
            data = json.loads(self._bounded_text(meta_path, MAX_MANIFEST_BYTES))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _load_catalog(self, pack_id):
        self.refresh_removable()
        if pack_id in self._catalog_cache:
            return self._catalog_cache[pack_id]

        pack = self.packs.get(pack_id)
        if not pack:
            return None
        descriptor = pack.get("catalog") or {}
        path_value = descriptor.get("path")
        if not descriptor.get("available") or not path_value:
            return None

        path = Path(path_value)
        try:
            text = self._bounded_text(path, MAX_CATALOG_BYTES)
        except (OSError, UnicodeDecodeError, ValueError):
            return None

        items = []
        characters = []
        teams = []
        seen = set()

        for line in text.splitlines():
            line = line.strip()
            if not line or line.casefold() == "tipo\tentrada":
                continue
            if "\t" not in line:
                continue
            raw_type, title = line.split("\t", 1)
            raw_type = raw_type.strip().upper()
            title = title.strip()
            entity_type = self.CATALOG_TYPES.get(raw_type)
            if not entity_type or not title:
                continue

            exact_key = (raw_type, title)
            if exact_key in seen:
                continue
            seen.add(exact_key)

            item = {
                "pack_id": pack_id,
                "title": title,
                "entity_type": entity_type,
                "_normalized": _normalize(title),
            }
            items.append(item)
            if entity_type == "character":
                characters.append(item)
            else:
                teams.append(item)

        cache = {
            "all": items,
            "characters": characters,
            "teams": teams,
        }
        self._catalog_cache[pack_id] = cache

        descriptor["total"] = len(items)
        descriptor["characters"] = len(characters)
        descriptor["teams"] = len(teams)
        return cache

    @staticmethod
    def _catalog_type_key(entity_type):
        if entity_type is None:
            return "all"
        value = str(entity_type).strip().lower()
        if value in {"personagem", "personagens", "character", "characters"}:
            return "characters"
        if value in {"equipe", "equipes", "team", "teams"}:
            return "teams"
        return "all"

    def _public_catalog_item(self, item, pack_id):
        source = ((self.packs.get(pack_id) or {}).get("catalog") or {}).get("source") or {}
        raw_type = "PERSONAGEM" if item.get("entity_type") == "character" else "EQUIPE"
        title = str(item.get("title") or "")
        stable = hashlib.sha1(f"{raw_type}\0{title}".encode("utf-8")).hexdigest()[:20]
        continuity = self._extract_catalog_universe(title)
        return {
            "id": f"{pack_id}:catalog:{stable}",
            "pack_id": pack_id,
            "title": title,
            "entity_type": item.get("entity_type"),
            "source": {
                "type": source.get("type") or "community_catalog",
                "reference": source.get("reference") or "Marvel Database/Fandom",
                "url": source.get("url"),
                "official": bool(source.get("official", False)),
            },
            "metadata": {
                "publisher": "Marvel",
                "universe": "Marvel",
                "continuity": continuity,
                "catalog_only": True,
                "image_status": "missing_authorized_asset",
            },
        }

    @staticmethod
    def _extract_catalog_universe(title):
        match = re.search(
            r"\(([^()]*(?:Earth|Multiverse|Mojoverse|Ideaverse|Void|Limbo|Timeline|Verse)[^()]*)\)\s*$",
            title,
            re.I,
        )
        if match:
            return match.group(1).strip()
        return "Marvel Database"

    @staticmethod
    def _safe_int(value):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

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

        aliases = [str(value).strip() for value in aliases if str(value).strip()]
        keywords = [str(value).strip() for value in keywords if str(value).strip()]
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
        metadata = raw.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {"value": str(metadata)}

        return {
            "id": raw.get("id") or f"{pack_id}:{position}",
            "pack_id": pack_id,
            "pack_name": manifest.get("name") or pack_id,
            "title": title,
            "answer": answer,
            "aliases": aliases,
            "keywords": keywords,
            "source": source,
            "metadata": metadata,
            "_search_texts": normalized,
        }
