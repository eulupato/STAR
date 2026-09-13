"""Indexação canônica de conhecimento no Knowledge Graph da STAR.

O grafo existente continua sendo a única fonte de persistência. O indexador cria
relações explicitamente derivadas das taxonomias; não inventa relações causais ou
teológicas que as fontes não declaram.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256

from core.curriculum_knowledge import CONCEPTS
from core.curriculum_taxonomy import THEMES
from database.cognitive_store import CognitiveStore


class ScientificGraphIndexer:
    """Indexador histórico do currículo, agora também aceita a taxonomia cultural.

    O nome da classe é preservado por compatibilidade com o alpha já integrado.
    """

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

    @staticmethod
    def culture_subject_node_id(subject_key: str) -> str:
        return "culture:subject:" + str(subject_key).strip().lower()

    @staticmethod
    def culture_aspect_node_id(aspect_index: int) -> str:
        return f"culture:aspect:{int(aspect_index):02d}"

    @staticmethod
    def culture_region_node_id(region: str) -> str:
        import re
        import unicodedata
        value = "".join(ch for ch in unicodedata.normalize("NFD", str(region).lower()) if unicodedata.category(ch) != "Mn")
        value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
        return "culture:region:" + value

    @staticmethod
    def source_family_node_id(source: str) -> str:
        digest = sha256(str(source).encode("utf-8")).hexdigest()[:16]
        return f"culture:source:{digest}"

    def index_curriculum(self, *, include_peer_links: bool = True, peer_limit_per_theme: int = 8) -> dict:
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
            node_count += 1
            edge_count += 1

        for concept in CONCEPTS:
            concept_id = self.concept_node_id(concept.index)
            self.store.upsert_node(
                concept_id,
                "canonical_concept",
                concept.label,
                data={
                    "key": concept.key,
                    "aliases": list(concept.aliases),
                    "owners": list(concept.owners),
                    "themes": list(concept.theme_ids),
                    "evidence_class": concept.evidence_class,
                    "sources": list(concept.sources),
                },
                confidence=1.0,
            )
            node_count += 1
            for theme_id in concept.theme_ids:
                self.store.add_edge(
                    concept_id,
                    self.theme_node_id(theme_id),
                    "belongs_to",
                    metadata={"source": "curriculum_taxonomy", "canonical": True},
                )
                concepts_by_theme[theme_id].append(concept)
                edge_count += 1
            for owner in concept.owners:
                self.store.add_edge(
                    concept_id,
                    self.owner_node_id(owner),
                    "domain_member",
                    metadata={"source": "curriculum_taxonomy"},
                )
                edge_count += 1

        peer_edges = 0
        if include_peer_links:
            limit = max(0, min(int(peer_limit_per_theme), 32))
            for theme_id, concepts in concepts_by_theme.items():
                for index, concept in enumerate(concepts):
                    for peer in concepts[index + 1:index + 1 + limit]:
                        self.store.add_edge(
                            self.concept_node_id(concept.index),
                            self.concept_node_id(peer.index),
                            "co_theme",
                            weight=0.5,
                            metadata={"theme_id": theme_id, "source": "curriculum_taxonomy"},
                        )
                        peer_edges += 1
        edge_count += peer_edges
        return {
            "themes": len(THEMES),
            "concepts": len(CONCEPTS),
            "nodes_touched": node_count,
            "edges_touched": edge_count,
            "peer_edges": peer_edges,
            "relation_policy": "taxonomy-derived only; no invented causal relation",
        }

    def index_cultural(self) -> dict:
        """Liga religiões/magia ao mesmo grafo sem materializar 5M variações."""
        from core.religion_magic_knowledge import _sources
        from core.religion_magic_taxonomy import ASPECTS, SUBJECTS

        nodes = edges = 0
        for aspect_index, aspect in enumerate(ASPECTS, 1):
            self.store.upsert_node(
                self.culture_aspect_node_id(aspect_index),
                "cultural_aspect",
                aspect,
                data={"source": "religion_magic_taxonomy"},
            )
            nodes += 1

        seen_regions = set()
        seen_sources = set()
        for subject in SUBJECTS:
            subject_id = self.culture_subject_node_id(subject.key)
            self.store.upsert_node(
                subject_id,
                "cultural_subject",
                subject.label,
                data={
                    "family": subject.family,
                    "region": subject.region,
                    "access_policy": subject.access_policy,
                    "source_families": list(_sources(subject)),
                },
            )
            nodes += 1

            region_id = self.culture_region_node_id(subject.region)
            if region_id not in seen_regions:
                seen_regions.add(region_id)
                self.store.upsert_node(region_id, "cultural_region", subject.region, data={"source": "religion_magic_taxonomy"})
                nodes += 1
            self.store.add_edge(subject_id, region_id, "associated_region", metadata={"source": "religion_magic_taxonomy"})
            edges += 1

            for aspect_index in range(1, len(ASPECTS) + 1):
                self.store.add_edge(
                    subject_id,
                    self.culture_aspect_node_id(aspect_index),
                    "has_study_aspect",
                    weight=0.2,
                    metadata={"source": "religion_magic_taxonomy", "canonical": True},
                )
                edges += 1

            for source in _sources(subject):
                source_id = self.source_family_node_id(source)
                if source_id not in seen_sources:
                    seen_sources.add(source_id)
                    self.store.upsert_node(source_id, "source_family", source, data={"scope": "cultural-research"})
                    nodes += 1
                self.store.add_edge(subject_id, source_id, "recommended_source_family", weight=0.7,
                                    metadata={"source": "religion_magic_taxonomy"})
                edges += 1

        return {
            "subjects": len(SUBJECTS),
            "aspects": len(ASPECTS),
            "nodes_touched": nodes,
            "edges_touched": edges,
            "five_million_variants_materialized": False,
            "policy": "index canonical structure only; preserve community access policy and epistemic framing",
        }

    def neighbors_for_concept(self, concept_index: int, *, relation: str | None = None, limit: int = 50) -> list[dict]:
        return self.store.neighbors(self.concept_node_id(concept_index), relation=relation, limit=limit)

    def neighbors_for_cultural_subject(self, subject_key: str, *, relation: str | None = None, limit: int = 80) -> list[dict]:
        return self.store.neighbors(self.culture_subject_node_id(subject_key), relation=relation, limit=limit)

    def stats(self) -> dict:
        from core.religion_magic_taxonomy import SUBJECTS
        return {
            "status": "alpha-local",
            "scientific_source": "canonical curriculum taxonomy",
            "themes_available": len(THEMES),
            "concepts_available": len(CONCEPTS),
            "cultural_subjects_available": len(SUBJECTS),
            "materialization": "explicit/on-demand canonical graph",
            "causal_relation_inference": False,
            "theological_truth_inference": False,
        }
