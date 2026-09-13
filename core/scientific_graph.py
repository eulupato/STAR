"""Indexação canônica do currículo científico no Knowledge Graph da STAR.

O grafo existente continua sendo a única fonte de persistência. Este indexador cria
nós de tema/conceito/domínio e relações verificáveis pela taxonomia; não inventa
relações causais/científicas que a fonte não declara.
"""
from __future__ import annotations

from collections import defaultdict

from core.curriculum_knowledge import CONCEPTS
from core.curriculum_taxonomy import THEMES
from database.cognitive_store import CognitiveStore


class ScientificGraphIndexer:
    def __init__(self, store: CognitiveStore | None = None):
        self.store = store or CognitiveStore()

    @staticmethod
    def theme_node_id(theme_id: int) -> str:
        return f"curriculum:theme:{int(theme_id):03d}"

    @staticmethod
    def concept_node_id(concept_index: int) -> str:
        return f"curriculum:concept:{int(concept_index):04d}"

    @staticmethod
    def owner_node_id(owner: str) -> str:
        return "curriculum:owner:" + str(owner).strip().lower().replace(" ", "_")

    def index_curriculum(self, *, include_peer_links: bool = True, peer_limit_per_theme: int = 8) -> dict:
        theme_by_id = {theme.id: theme for theme in THEMES}
        concepts_by_theme: dict[int, list] = defaultdict(list)
        node_count = edge_count = 0

        for theme in THEMES:
            self.store.upsert_node(
                self.theme_node_id(theme.id),
                "curriculum_theme",
                theme.label,
                data={"owner": theme.owner, "evidence_class": theme.evidence_class},
            )
            node_count += 1
            owner_id = self.owner_node_id(theme.owner)
            self.store.upsert_node(owner_id, "knowledge_domain", theme.owner, data={"source": "curriculum_taxonomy"})
            self.store.add_edge(self.theme_node_id(theme.id), owner_id, "owned_by", metadata={"source": "curriculum_taxonomy"})
            node_count += 1; edge_count += 1

        seen_owners = set()
        for concept in CONCEPTS:
            concept_id = self.concept_node_id(concept.index)
            self.store.upsert_node(concept_id, "canonical_concept", concept.label,
                data={"key": concept.key, "aliases": list(concept.aliases), "owners": list(concept.owners),
                      "themes": list(concept.theme_ids), "evidence_class": concept.evidence_class,
                      "sources": list(concept.sources)}, confidence=1.0)
            node_count += 1
            for theme_id in concept.theme_ids:
                self.store.add_edge(concept_id, self.theme_node_id(theme_id), "belongs_to",
                    metadata={"source": "curriculum_taxonomy", "canonical": True})
                concepts_by_theme[theme_id].append(concept)
                edge_count += 1
            for owner in concept.owners:
                owner_id = self.owner_node_id(owner)
                if owner not in seen_owners:
                    seen_owners.add(owner)
                self.store.add_edge(concept_id, owner_id, "domain_member", metadata={"source": "curriculum_taxonomy"})
                edge_count += 1

        peer_edges = 0
        if include_peer_links:
            limit = max(0, min(int(peer_limit_per_theme), 32))
            for theme_id, concepts in concepts_by_theme.items():
                # Relações de navegação, não causalidade: liga vizinhos canônicos do
                # mesmo tema com grau limitado para evitar um grafo densíssimo.
                for index, concept in enumerate(concepts):
                    for peer in concepts[index + 1:index + 1 + limit]:
                        self.store.add_edge(self.concept_node_id(concept.index), self.concept_node_id(peer.index),
                                            "co_theme", weight=0.5,
                                            metadata={"theme_id": theme_id, "source": "curriculum_taxonomy"})
                        peer_edges += 1
        edge_count += peer_edges
        return {"themes": len(THEMES), "concepts": len(CONCEPTS), "nodes_touched": node_count,
                "edges_touched": edge_count, "peer_edges": peer_edges,
                "relation_policy": "taxonomy-derived only; no invented causal relation"}

    def neighbors_for_concept(self, concept_index: int, *, relation: str | None = None, limit: int = 50) -> list[dict]:
        return self.store.neighbors(self.concept_node_id(concept_index), relation=relation, limit=limit)

    def stats(self) -> dict:
        return {"status": "alpha-local", "source": "canonical curriculum taxonomy",
                "themes_available": len(THEMES), "concepts_available": len(CONCEPTS),
                "materialization": "explicit/on-demand", "causal_relation_inference": False}
