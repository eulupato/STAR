"""Universal Knowledge Engine da STAR V3."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from core.logging_config import get_logger
from .entities import Entity, KnowledgeSource, Relationship
from .graph import KnowledgeGraph
from .store import KnowledgeStore, normalize_search_text

log = get_logger("knowledge")


@dataclass
class SearchResult:
    source: str
    title: str
    score: float
    entity: Entity | None = None
    payload: dict | None = None


class KnowledgeEngine:
    def __init__(self, db_path: str | Path, pack_manager=None, event_bus=None):
        self.store = KnowledgeStore(db_path)
        self.graph = KnowledgeGraph(self.store)
        self.pack_manager = pack_manager
        self.event_bus = event_bus
        self.last_entity: Entity | None = None

    def _event(self, event_type: str, payload=None):
        if self.event_bus is None:
            return
        try:
            self.event_bus.publish(event_type, payload or {}, "knowledge")
        except Exception as exc:
            log.warning("Falha ao publicar evento %s: %s", event_type, exc)

    def upsert_entity(self, entity: Entity) -> str:
        entity_id = self.store.upsert_entity(entity)
        self._event("ENTITY_UPSERTED", {"entity_id": entity_id, "name": entity.name})
        return entity_id

    def search_entities(self, query: str = "", filters: dict | None = None, limit: int = 20) -> list[Entity]:
        self._event("KNOWLEDGE_SEARCHED", {"query": query, "filters": filters or {}})
        results = self.store.search(query, filters=filters, limit=limit)
        self._event("KNOWLEDGE_RESULT", {"query": query, "count": len(results)})
        return results

    def universal_search(self, query: str, working_memory=None, limit: int = 12) -> list[SearchResult]:
        results: list[SearchResult] = []
        seen: set[str] = set()

        for entity in self.store.search(query, limit=limit):
            key = f"entity:{entity.id}"
            if key in seen:
                continue
            seen.add(key)
            normalized_query = set(normalize_search_text(query).split())
            normalized_entity = set(normalize_search_text(
                " ".join([entity.name, *entity.aliases, *(entity.tags or [])])
            ).split())
            overlap = len(normalized_query & normalized_entity)
            score = 1.0 + overlap
            results.append(
                SearchResult(
                    source="entity_database",
                    title=entity.name,
                    score=score,
                    entity=entity,
                )
            )

        if working_memory is not None:
            for key, value in working_memory.facts().items():
                haystack = normalize_search_text(f"{key} {value}")
                if normalize_search_text(query) and normalize_search_text(query) in haystack:
                    result_key = f"memory:{key}:{value}"
                    if result_key not in seen:
                        seen.add(result_key)
                        results.append(
                            SearchResult(
                                source="working_memory",
                                title=str(key),
                                score=0.8,
                                payload={"value": value},
                            )
                        )

        if self.pack_manager is not None:
            try:
                packs = self.pack_manager.list()
            except Exception as exc:
                log.warning("Falha ao consultar Knowledge Packs: %s", exc)
                packs = {}
            q = normalize_search_text(query)
            for pack_id, pack in packs.items():
                manifest = pack.get("manifest", {})
                searchable = normalize_search_text(
                    " ".join([
                        str(pack_id),
                        str(manifest.get("name", "")),
                        str(manifest.get("description", "")),
                        " ".join(manifest.get("topics", []) or []),
                    ])
                )
                if q and all(token in searchable for token in q.split()):
                    key = f"pack:{pack_id}"
                    if key not in seen:
                        seen.add(key)
                        results.append(
                            SearchResult(
                                source="knowledge_pack",
                                title=str(manifest.get("name") or pack_id),
                                score=0.6,
                                payload={"id": pack_id, "manifest": manifest},
                            )
                        )

        results.sort(key=lambda item: (-item.score, item.title.lower()))
        return results[: max(1, int(limit))]

    def resolve_entity(self, name_or_alias: str, universe: str | None = None) -> Entity | None:
        exact = self.store.find_exact(name_or_alias, universe=universe)
        if exact:
            return exact
        results = self.store.search(name_or_alias, filters={"universe": universe} if universe else None, limit=1)
        return results[0] if results else None

    def answer(self, text: str, context: dict | None = None) -> str | None:
        raw = str(text or "").strip()
        if not raw:
            return None
        context = dict(context or {})
        resolved_text = str(context.get("resolved_text") or raw)

        patterns = (
            r"^(?:quem (?:e|é)|quem foi|fale sobre|me fale sobre)\s+(.+?)[?!.]*$",
            r"^(?:o que sabe sobre|o que voce sabe sobre|o que você sabe sobre)\s+(.+?)[?!.]*$",
        )
        name = None
        for pattern in patterns:
            match = re.match(pattern, resolved_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                break

        if name:
            entity = self.resolve_entity(name)
            if entity:
                self.last_entity = entity
                self._event("ENTITY_SELECTED", {"entity_id": entity.id, "name": entity.name})
                return self.format_entity(entity)

        place_match = re.match(
            r"^(?:onde|de onde)\s+(.+?)\s+(?:nasceu|vem|veio)[?!.]*$",
            resolved_text,
            re.IGNORECASE,
        )
        if place_match:
            entity = self.resolve_entity(place_match.group(1).strip())
            if entity:
                self.last_entity = entity
                place = entity.origin_place or entity.origin
                if place:
                    return f"{entity.name}: {place}."

        origin_match = re.match(
            r"^(?:qual (?:e|é) a origem de|qual a origem de|origem de)\s+(.+?)[?!.]*$",
            resolved_text,
            re.IGNORECASE,
        )
        if origin_match:
            entity = self.resolve_entity(origin_match.group(1).strip())
            if entity:
                self.last_entity = entity
                origin = entity.origin or entity.origin_place
                if origin:
                    return f"{entity.name}: {origin}."

        relation_match = re.match(
            r"^(?:quais|quem sao|quem são)\s+(aliados|inimigos|equipes|afiliacoes|afiliações)\s+(?:de|do|da)\s+(.+?)[?!.]*$",
            resolved_text,
            re.IGNORECASE,
        )
        if relation_match:
            relation_name = normalize_search_text(relation_match.group(1))
            target = relation_match.group(2).strip()
            entity = self.resolve_entity(target)
            if entity:
                self.last_entity = entity
                predicates = {
                    "aliados": "ally",
                    "inimigos": "enemy",
                    "equipes": "team",
                    "afiliacoes": "affiliation",
                }
                predicate = predicates.get(relation_name, relation_name)
                names = []
                if relation_name == "equipes":
                    names.extend(entity.team)
                elif relation_name == "afiliacoes":
                    names.extend(entity.affiliations)
                names.extend(self.graph.related_names(entity.id, predicate))

                unique = []
                seen = set()
                for item in names:
                    key = normalize_search_text(item)
                    if key and key not in seen:
                        seen.add(key)
                        unique.append(item)
                if unique:
                    return f"{entity.name}: " + ", ".join(unique) + "."

        group_match = re.match(
            r"^quais personagens (?:dos|do|da) (.+?) (?:possuem|tem|têm) (.+?)[?!.]*$",
            resolved_text,
            re.IGNORECASE,
        )
        if group_match:
            team = group_match.group(1).strip()
            trait = group_match.group(2).strip()
            matches = self.store.search(
                "",
                filters={
                    "category": "character",
                    "team": team,
                    "power": trait,
                },
                limit=25,
            )
            if not matches:
                matches = self.store.search(
                    "",
                    filters={
                        "category": "character",
                        "team": team,
                        "ability": trait,
                    },
                    limit=25,
                )
            if matches:
                return ", ".join(entity.name for entity in matches) + "."

        search_match = re.match(
            r"^(?:pesquise|procure|buscar|busque)\s+(.+?)[?!.]*$",
            resolved_text,
            re.IGNORECASE,
        )
        if search_match:
            results = self.universal_search(search_match.group(1), limit=8)
            if results:
                return "Encontrei: " + ", ".join(item.title for item in results) + "."

        return None

    @staticmethod
    def format_entity(entity: Entity) -> str:
        parts = [entity.name]
        if entity.universe:
            parts.append(f"Universo: {entity.universe}")
        if entity.publisher:
            parts.append(f"Editora: {entity.publisher}")
        if entity.description:
            parts.append(entity.description)
        if entity.powers:
            parts.append("Poderes: " + ", ".join(entity.powers[:8]))
        if entity.abilities:
            parts.append("Habilidades: " + ", ".join(entity.abilities[:8]))
        if entity.team:
            parts.append("Equipes: " + ", ".join(entity.team[:8]))
        if entity.first_appearance:
            parts.append("Primeira aparição: " + entity.first_appearance)
        return " | ".join(parts)

    def status(self) -> dict:
        return {
            "active": True,
            "entities": self.store.count(),
            "heroes": self.store.count("character"),
            "database": str(self.store.path),
            "local_first": True,
        }
