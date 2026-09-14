from uuid import uuid4

import pytest

from core.mind import CognitiveSuite
from core.star_core import StarCore
from core.universal_knowledge import (
    UNIVERSAL_ADDRESSABLE_CONTENTS,
    UniversalKnowledgeArchitecture,
    UniversalKnowledgeCatalog,
)


def _architecture():
    suite = CognitiveSuite()
    return UniversalKnowledgeArchitecture(suite.epistemics, suite.graph), suite


def _canonical_fact(suite: CognitiveSuite, marker: str, text: str | None = None):
    source_id = suite.epistemics.register_source(
        f"unit://universal/{marker}",
        source_type="test",
        title=f"Fonte universal {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        text or f"Conhecimento canônico universal validado para {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência independente para {marker}",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
        reliability=1.0,
    )
    suite.epistemics.transition(
        record["record_id"],
        "VERIFIED",
        reason="evidência rastreável suficiente para teste",
        actor="unit-test",
    )
    canonical = suite.epistemics.transition(
        record["record_id"],
        "CANONICAL",
        reason="claim apto a conhecimento canônico",
        actor="unit-test",
    )
    return canonical, source_id


def test_block3_catalog_is_exactly_1b_per_namespace_and_supports_independent_blocks():
    catalog = UniversalKnowledgeCatalog()
    stats = catalog.stats("B03")

    assert UNIVERSAL_ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["canonical_nodes"] == 1_000
    assert stats["variants_per_node"] == 1_000_000
    assert stats["addressable_contents"] == 1_000_000_000
    assert stats["materialization"] == "on-demand"

    first = catalog.content_id("B03", 0, 0)
    last = catalog.content_id("B03", 999, 999_999)
    assert first == "UK-B03-0000000001"
    assert last == "UK-B03-1000000000"
    assert catalog.get_variant(first)["namespace"] == "B03"
    assert catalog.get_variant(last)["id"] == last
    assert catalog.get_variant("UK-B03-1000000001") is None

    architecture, _ = _architecture()
    namespaces = {item["namespace"]: item for item in architecture.stats()["namespaces"]}
    assert namespaces["B01"]["logical_capacity"] == 1_000_000_000
    assert namespaces["B02"]["logical_capacity"] == 1_000_000_000
    assert namespaces["B03"]["logical_capacity"] == 1_000_000_000

    extra = architecture.register_namespace(
        "B99",
        "BLOCO FUTURO DE TESTE",
        logical_capacity=1_000_000_000,
        source="unit-test",
    )
    assert extra["logical_capacity"] == 1_000_000_000
    assert architecture.catalog.content_id("B99", 999, 999_999) == "UK-B99-1000000000"


def test_canonical_knowledge_requires_canonical_epistemic_claim_and_deduplicates():
    architecture, suite = _architecture()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(
        f"unit://not-canonical/{marker}",
        source_type="test",
        reliability=1.0,
    )
    discovered = suite.epistemics.discover(
        f"Claim ainda descoberto {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://discovered/{marker}",
        source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        architecture.promote_canonical(
            discovered["record_id"],
            f"Conceito {marker}",
        )

    canonical, _ = _canonical_fact(suite, marker)
    created = architecture.promote_canonical(
        canonical["record_id"],
        f"Conceito Universal {marker}",
        knowledge_type="concept",
        summary=f"Resumo rastreável {marker}",
        aliases=[f"Alias Universal {marker}", f"AU {marker}"],
        properties={"marker": marker, "quality": "canonical"},
        categories=[f"Categoria {marker}"],
        subtopics=[f"Subtema {marker}"],
        contexts=["unit-test"],
        rules=["usar somente com claim canônico"],
        exceptions=["claim retraído não é atual"],
    )
    assert created["created"] is True
    assert created["canonical_claim_id"] == canonical["record_id"]
    assert created["properties"]["marker"] == marker
    assert len(created["aliases"]) == 2
    assert {facet["facet_type"] for facet in created["facets"]} == {"category", "subtopic", "context"}

    duplicate = architecture.promote_canonical(
        canonical["record_id"],
        f"Conceito Universal {marker}",
        knowledge_type="concept",
    )
    assert duplicate["knowledge_id"] == created["knowledge_id"]
    assert duplicate["created"] is False

    traced = architecture.trace(created["knowledge_id"])
    assert traced["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"
    assert traced["canonical_claim"]["origin_source"]["source_id"] is not None
    assert traced["canonical_claim"]["evidence"]


def test_universal_query_indexes_aliases_facets_cache_and_updates():
    architecture, suite = _architecture()
    marker = uuid4().hex
    canonical, _ = _canonical_fact(suite, marker)
    knowledge = architecture.promote_canonical(
        canonical["record_id"],
        f"Entidade Principal {marker}",
        knowledge_type="entity",
        aliases=[f"Apelido Único {marker}"],
        categories=[f"Grupo Único {marker}"],
        summary=f"Resumo inicial {marker}",
    )

    before = architecture.cache.stats()
    first = architecture.query(f"Apelido Único {marker}")
    middle = architecture.cache.stats()
    second = architecture.query(f"Apelido Único {marker}")
    after = architecture.cache.stats()

    assert first and first[0]["knowledge_id"] == knowledge["knowledge_id"]
    assert second[0]["knowledge_id"] == knowledge["knowledge_id"]
    assert middle["misses"] == before["misses"] + 1
    assert after["hits"] == middle["hits"] + 1

    facet_hits = architecture.query_facet("category", f"Grupo Único {marker}")
    assert facet_hits and facet_hits[0]["knowledge_id"] == knowledge["knowledge_id"]

    architecture.update(
        knowledge["knowledge_id"],
        summary=f"Resumo atualizado {marker}",
        properties={"updated": True},
    )
    updated = architecture.get(knowledge["knowledge_id"])
    assert updated["summary"] == f"Resumo atualizado {marker}"
    assert updated["properties"]["updated"] is True
    assert updated["revision"] >= 2
    assert architecture.cache.stats()["entries"] == 0


def test_semantic_relations_taxonomy_crosslinks_events_and_graph_are_shared():
    architecture, suite = _architecture()
    marker_a = uuid4().hex
    marker_b = uuid4().hex
    claim_a, _ = _canonical_fact(suite, marker_a)
    claim_b, _ = _canonical_fact(suite, marker_b)
    child = architecture.promote_canonical(
        claim_a["record_id"],
        f"Filho {marker_a}",
        knowledge_type="concept",
    )
    parent = architecture.promote_canonical(
        claim_b["record_id"],
        f"Pai {marker_b}",
        knowledge_type="category",
    )

    architecture.add_taxonomy(child["knowledge_id"], parent["knowledge_id"], relation="is_a")
    architecture.add_cross_link(child["knowledge_id"], parent["knowledge_id"], label="ponte interdisciplinar")
    event = architecture.record_event(
        child["knowledge_id"],
        "observed_update",
        source_record_id=claim_a["record_id"],
        payload={"marker": marker_a},
    )

    child_edges = suite.graph.neighbors(child["knowledge_id"])
    parent_edges = suite.graph.neighbors(parent["knowledge_id"])
    assert any(edge["relation"] == "is_a" for edge in child_edges)
    assert any(edge["relation"] == "cross_link" for edge in child_edges)
    assert any(edge["relation"] == "broader_than" for edge in parent_edges)
    assert event["payload"]["marker"] == marker_a

    traced = architecture.trace(child["knowledge_id"])
    assert any(item["relation"] == "is_a" for item in traced["semantic_relations"])
    assert any(item["event_type"] == "observed_update" for item in traced["events"])
    assert traced["pipeline"] == [
        "CANONICAL KNOWLEDGE",
        "CLAIMS",
        "EVIDENCE",
        "KNOWLEDGE GRAPH",
        "SEMANTIC RELATIONS",
        "INDEXES",
        "CACHE",
        "STAR",
    ]


def test_retracted_claims_are_only_kept_as_historical_links():
    architecture, suite = _architecture()
    marker = uuid4().hex
    canonical, source_id = _canonical_fact(suite, marker)
    knowledge = architecture.promote_canonical(
        canonical["record_id"],
        f"Conhecimento Histórico {marker}",
    )
    other = suite.epistemics.discover(
        f"Claim retraído auxiliar suficientemente distinto {uuid4().hex}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://retracted/{marker}",
        source_id=source_id,
    )
    suite.epistemics.retract(other["record_id"], reason="teste de retração", actor="unit-test")

    with pytest.raises(ValueError, match="historical"):
        architecture.link_claim(knowledge["knowledge_id"], other["record_id"], role="supporting")
    historical = architecture.link_claim(
        knowledge["knowledge_id"],
        other["record_id"],
        role="historical",
    )
    assert historical["role"] == "historical"


def test_block3_handlers_and_star_core_integration_are_explicit_and_non_intrusive():
    architecture, _ = _architecture()
    assert "BLOCO 3" in architecture.handle("status bloco 3")
    assert "UK-B03-0000000001" in architecture.handle("UK-B03-0000000001")
    assert architecture.handle("uma conversa normal que não é comando") is None

    class Router:
        def route(self, request):
            return {"response_type": "local"}

    class Executive:
        def execute(self, request, route):
            return "fallback"

    class State:
        def get_state(self):
            return {}

    core = StarCore(Router(), Executive(), State())
    assert core.mind.knowledge is core.knowledge
    response = core._process_portuguese("status bloco 3")
    assert "BLOCO 3" in response
    assert core.last_intent == "universal_knowledge"
