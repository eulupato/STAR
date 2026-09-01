"""Knowledge Graph leve sobre o Entity Store."""
from __future__ import annotations

from .store import KnowledgeStore


class KnowledgeGraph:
    def __init__(self, store: KnowledgeStore):
        self.store = store

    def neighbors(self, entity_id: str, predicate: str | None = None):
        return self.store.relations(entity_id, predicate)

    def related_names(self, entity_id: str, predicate: str | None = None) -> list[str]:
        return [item.target_name for item in self.neighbors(entity_id, predicate)]
