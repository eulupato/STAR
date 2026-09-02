"""Knowledge Packs locais da STAR V1.9.

A V1.9 mantém o mecanismo deliberadamente simples: packs estruturados são
carregados uma vez no startup e consultados por busca lexical determinística.
Embeddings, RAG e ingestão automática de PDF pertencem à V3.0.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import unicodedata


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


class KnowledgePackManager:
    CONTENT_NAMES = ("knowledge.jsonl", "knowledge.json")

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.packs = {}
        self.entries = []
        self.scan()

    def scan(self):
        self.packs = {}
        self.entries = []

        for manifest_path in sorted(self.root.rglob("manifest.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            pack_id = manifest.get("id") or manifest.get("name") or manifest_path.parent.name
            pack_entries = self._load_entries(manifest_path.parent, manifest, pack_id)

            self.packs[pack_id] = {
                "manifest": manifest,
                "path": str(manifest_path.parent),
                "available": True,
                "entries": len(pack_entries),
            }
            self.entries.extend(pack_entries)

        return self.packs

    def list(self):
        return self.packs

    def stats(self):
        return {
            "packs": len(self.packs),
            "entries": len(self.entries),
        }

    def search(self, query, threshold=0.62):
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

    def _load_entries(self, pack_dir, manifest, pack_id):
        declared = manifest.get("content_file")
        candidates = [declared] if declared else list(self.CONTENT_NAMES)

        for filename in candidates:
            if not filename:
                continue
            path = pack_dir / filename
            if not path.is_file():
                continue
            try:
                raw_entries = self._read_content(path)
            except (OSError, json.JSONDecodeError, ValueError):
                return []

            entries = []
            for position, raw in enumerate(raw_entries):
                entry = self._prepare_entry(raw, pack_id, manifest, position)
                if entry:
                    entries.append(entry)
            return entries

        return []

    @staticmethod
    def _read_content(path):
        if path.suffix.lower() == ".jsonl":
            entries = []
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
            return entries

        data = json.loads(path.read_text(encoding="utf-8"))
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
