from uuid import uuid4
import unicodedata

import pytest

from core.human_contexts import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    HUMAN_CONTEXT_BRANCHES,
    HUMAN_CONTEXT_DOMAINS,
    HUMAN_CONTEXT_LENSES,
    INTERPRETATION_POLICY,
    REQUESTED_TOPICS,
    VARIANT_AXES,
    VARIANTS_PER_NODE,
    HumanContextCatalog,
    HumanContextFoundations,
)
from core.mind import CognitiveSuite
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _norm(text):
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return " ".join(value.replace("_", " ").split())


def _block():
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    block = HumanContextFoundations(knowledge)
    return block, knowledge, suite


def _canonical_fact(suite: CognitiveSuite, marker: str):
    source_id = suite.epistemics.register_source(
        f"unit://human-context/{marker}",
        source_type="test",
        title=f"Fonte contextual {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        f"Conhecimento contextual humano validado {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://human-context-claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência contextual rastreável {marker}",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
        reliability=1.0,
    )
    suite.epistemics.transition(record["record_id"], "VERIFIED", reason="evidência rastreável", actor="unit-test")
    return suite.epistemics.transition(record["record_id"], "CANONICAL", reason="claim geral apto ao B10", actor="unit-test")


def test_block10_catalog_is_exactly_1b_and_on_demand():
    catalog = HumanContextCatalog()
    stats = catalog.stats()
    assert len(HUMAN_CONTEXT_DOMAINS) == 13
    assert len(HUMAN_CONTEXT_BRANCHES) == 50
    assert len(HUMAN_CONTEXT_LENSES) == 10
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_knowledge_rows"] == 0
    assert catalog.content_id(0, 0) == "CTX-B10-0000000001"
    assert catalog.content_id(499, 1_999_999) == "CTX-B10-1000000000"
    assert catalog.get_variant("CTX-B10-1000000001") is None


def test_block10_variant_space_uses_exact_requested_nine_dimensions():
    sizes = {name: len(values) for name, values in VARIANT_AXES}
    assert list(sizes) == ["person", "age", "environment", "relation", "need", "risk", "norm", "culture", "context"]
    assert sizes == {
        "person": 10, "age": 5, "environment": 5, "relation": 5,
        "need": 4, "risk": 4, "norm": 4, "culture": 5, "context": 5,
    }
    product = 1
    for size in sizes.values():
        product *= size
    assert product == 2_000_000
    item = HumanContextCatalog().get_variant("CTX-B10-1000000000")
    for dimension in sizes:
        assert dimension in item


def test_block10_contains_all_requested_topics_and_contextual_subtopics():
    corpus = _norm(" ".join(
        [branch.label for branch in HUMAN_CONTEXT_BRANCHES]
        + [topic for branch in HUMAN_CONTEXT_BRANCHES for topic in branch.subtopics]
        + list(REQUESTED_TOPICS)
    ))
    for topic in REQUESTED_TOPICS:
        assert _norm(topic) in corpus, topic
    assert "acessibilidade" in corpus
    assert "consentimento" in corpus
    assert "assentimento" in corpus
    assert "animais de servico" in corpus
    assert "salvaguarda" in corpus


def test_block10_registers_b10_on_same_universal_architecture():
    block, knowledge, _suite = _block()
    namespace = knowledge.store.get_namespace("B10")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert block.knowledge is knowledge
    assert block.graph is knowledge.graph
    assert block.stats()["knowledge_graph"] == "shared knowledge_nodes/knowledge_edges"
    assert block.stats()["parallel_context_database"] is False
    assert block.stats()["parallel_context_graph"] is False


def test_block10_taxonomy_uses_shared_graph_and_links_blocks6_to9():
    block, _knowledge, suite = _block()
    result = block.materialize_taxonomy("autonomia")
    assert result["knowledge_graph"] == "shared"
    assert result["parallel_context_graph_created"] is False
    assert result["branches_materialized"] == 3
    labels = {item["label"] for item in suite.graph.neighbors("CTX-TAX-ROOT")}
    assert "Vida, Corpo e Necessidades Humanas" in labels
    assert "Mente Humana e Psicologia" in labels
    assert "Linguagem e Comunicação" in labels
    assert "Sociedade e Cultura" in labels
    assert "Autonomia, consentimento e decisão apoiada" in labels


def test_block10_contextualization_preserves_capacity_privacy_autonomy_and_limits():
    block, _knowledge, _suite = _block()
    result = block.contextualize_human_situation(
        "uma pessoa precisa de ajuda para atravessar um espaço movimentado",
        person="pessoa com deficiência",
        age="adulto",
        environment="espaço público",
        relation="estranho oferecendo ajuda",
        need="participação e segurança",
        risk="ambiental",
        norm="ética e regras locais",
        culture="contexto local",
        context="rotina",
        observations=["movimento intenso", "preferência da pessoa ainda não perguntada"],
    )
    assert result["epistemic_kind"] == "inference"
    assert result["certainty"] == "context_dependent"
    assert result["age_determines_capacity"] is False
    assert result["disability_determines_inability"] is False
    assert result["consent_assumed"] is False
    assert result["privacy_voided_by_public_space"] is False
    assert result["autonomy_voided_by_emergency"] is False
    assert result["operational_authorization"] is False
    assert result["missing_dimensions"] == []


def test_block10_policy_handles_touch_emergency_disability_and_animals_without_overreach():
    assert INTERPRETATION_POLICY["age_is_automatic_capacity"] is False
    assert INTERPRETATION_POLICY["disability_is_inability"] is False
    assert INTERPRETATION_POLICY["support_need_is_fixed_from_label"] is False
    assert INTERPRETATION_POLICY["touch_is_automatically_permitted"] is False
    assert INTERPRETATION_POLICY["social_distance_is_universal_constant"] is False
    assert INTERPRETATION_POLICY["emergency_cancels_autonomy_or_privacy"] is False
    assert INTERPRETATION_POLICY["animal_behavior_is_certain_from_category"] is False
    assert INTERPRETATION_POLICY["contextual_inference_is_operational_authorization"] is False
    assert INTERPRETATION_POLICY["consent_and_boundary_context_required"] is True


def test_block10_canonical_knowledge_keeps_block2_gate():
    block, knowledge, suite = _block()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(f"unit://context-discovered/{marker}", source_type="test", reliability=1.0)
    discovered = suite.epistemics.discover(
        f"Claim contextual descoberto {marker}", epistemic_kind="fact",
        origin_type="unit_test", origin_ref=f"unit://context-discovered-claim/{marker}", source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        block.promote_canonical_context_knowledge(
            discovered["record_id"], f"Conhecimento contextual {marker}",
            domain="autonomia", branch="autonomy",
        )

    canonical = _canonical_fact(suite, marker)
    item = block.promote_canonical_context_knowledge(
        canonical["record_id"], f"Conhecimento contextual {marker}",
        domain="autonomia", branch="autonomy",
        properties={"scope": "general"}, contexts=["human_context"],
        summary="Conhecimento contextual humano geral.",
    )
    assert item["namespace"] == "B10"
    assert item["properties"]["age_is_automatic_capacity"] is False
    assert item["properties"]["disability_is_inability"] is False
    assert item["properties"]["contextual_inference_is_operational_authorization"] is False
    trace = knowledge.trace(item["knowledge_id"])
    assert trace["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"
    assert trace["canonical_claim"]["evidence"]


def test_block10_variant_and_handlers_are_explicit_and_nonintrusive():
    item = HumanContextCatalog().get_variant("CTX-B10-0000000001")
    assert item["domain"] == "life_stages"
    assert item["branch"] == "infants"
    assert item["lens"] == "concept"
    assert "Pessoa=" in item["prompt"]
    assert "autorização operacional" in item["prompt"]

    block, _knowledge, _suite = _block()
    assert "BLOCO 10" in block.handle("status bloco 10")
    assert "CTX-B10-0000000001" in block.handle("CTX-B10-0000000001")
    assert "não trata idade" in block.handle("idade define capacidade")
    assert "autorização irrestrita" in block.handle("toque e consentimento")
    assert block.handle("uma conversa cotidiana sem comando contextual") is None
