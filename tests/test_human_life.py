from uuid import uuid4
import unicodedata

import pytest

from core.human_life import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    DIAGNOSTIC_POLICY,
    HUMAN_LIFE_BRANCHES,
    HUMAN_LIFE_DOMAINS,
    HUMAN_LIFE_LENSES,
    REQUESTED_TOPICS,
    VARIANTS_PER_NODE,
    HumanLifeCatalog,
    HumanLifeFoundations,
)
from core.mind import CognitiveSuite
from core.scientific_foundations import ScientificFoundations
from core.star_core import StarCore
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _norm(text):
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return " ".join(value.replace("_", " ").split())


def _human_life():
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    science = ScientificFoundations(knowledge, reasoner=suite.science)
    human = HumanLifeFoundations(knowledge, scientific_foundations=science)
    return human, science, knowledge, suite


def _canonical_fact(suite: CognitiveSuite, marker: str):
    source_id = suite.epistemics.register_source(
        f"unit://human-life/{marker}",
        source_type="test",
        title=f"Fonte biológica {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        f"Conhecimento geral de biologia humana validado {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://human-life-claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência biológica rastreável {marker}",
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
    return suite.epistemics.transition(
        record["record_id"],
        "CANONICAL",
        reason="claim geral apto a conhecimento canônico B06",
        actor="unit-test",
    )


def test_block6_catalog_is_exactly_1b_and_on_demand():
    catalog = HumanLifeCatalog()
    stats = catalog.stats()

    assert len(HUMAN_LIFE_DOMAINS) == 13
    assert len(HUMAN_LIFE_BRANCHES) == 50
    assert len(HUMAN_LIFE_LENSES) == 20
    assert CANONICAL_NODES == 1_000
    assert VARIANTS_PER_NODE == 1_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["addressable_contents"] == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_knowledge_rows"] == 0

    assert catalog.content_id(0, 0) == "LIFE-B06-0000000001"
    assert catalog.content_id(999, 999_999) == "LIFE-B06-1000000000"
    assert catalog.get_variant("LIFE-B06-1000000001") is None


def test_block6_contains_all_requested_topics_and_deep_subtopics():
    corpus = _norm(" ".join(
        [branch.label for branch in HUMAN_LIFE_BRANCHES]
        + [topic for branch in HUMAN_LIFE_BRANCHES for topic in branch.subtopics]
    ))
    for topic in REQUESTED_TOPICS:
        assert _norm(topic) in corpus, topic

    assert "sinapses" in corpus
    assert "alvéolos" in " ".join(topic for branch in HUMAN_LIFE_BRANCHES for topic in branch.subtopics)
    assert "microbioma intestinal" in " ".join(topic for branch in HUMAN_LIFE_BRANCHES for topic in branch.subtopics)
    assert "ritmo circadiano" in " ".join(topic for branch in HUMAN_LIFE_BRANCHES for topic in branch.subtopics)
    assert "homeostase" in corpus


def test_block6_registers_b06_on_same_universal_architecture_and_reuses_block5():
    human, science, knowledge, _suite = _human_life()
    namespace = knowledge.store.get_namespace("B06")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert human.knowledge is knowledge
    assert human.graph is knowledge.graph
    assert human.scientific_foundations is science
    assert human.stats()["scientific_foundation"] == "BLOCO 5 reused"


def test_block6_taxonomy_materializes_into_shared_graph_and_links_block5_biology():
    human, _science, _knowledge, suite = _human_life()
    result = human.materialize_taxonomy("cérebro")
    assert result["knowledge_graph"] == "shared"
    assert result["diagnostic_engine_created"] is False
    assert result["branches_materialized"] == 6

    root_neighbors = suite.graph.neighbors("LIFE-TAX-ROOT")
    assert any(item["label"] == "Biologia" for item in root_neighbors)
    assert any(item["label"] == "Sistema nervoso, cérebro e sentidos" for item in root_neighbors)

    domain_neighbors = suite.graph.neighbors("LIFE-DOM-NERVOUS_SENSORY", relation="has_part")
    labels = {item["label"] for item in domain_neighbors}
    assert "Cérebro" in labels
    assert "Visão" in labels
    assert "Audição e equilíbrio" in labels

    branch_neighbors = suite.graph.neighbors("LIFE-BR-BRAIN", relation="has_part")
    assert any(item["node_type"] == "human_life_subtopic" for item in branch_neighbors)


def test_block6_canonical_knowledge_keeps_block2_gate_and_general_scope():
    human, _science, knowledge, suite = _human_life()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(
        f"unit://human-discovered/{marker}", source_type="test", reliability=1.0
    )
    discovered = suite.epistemics.discover(
        f"Claim humano ainda descoberto {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://human-discovered-claim/{marker}",
        source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        human.promote_canonical_human_knowledge(
            discovered["record_id"],
            f"Conhecimento humano {marker}",
            domain="cérebro",
            branch="brain",
        )

    canonical = _canonical_fact(suite, marker)
    item = human.promote_canonical_human_knowledge(
        canonical["record_id"],
        f"Conhecimento humano {marker}",
        domain="cérebro",
        branch="brain",
        properties={"scale": "organ"},
        subtopics=["neuroanatomia"],
        contexts=["general_human_biology"],
        summary="Conhecimento biológico humano geral, não diagnóstico.",
    )
    assert item["namespace"] == "B06"
    assert item["properties"]["diagnostic_use"] is False
    assert item["properties"]["personal_health_profile"] is False
    assert item["properties"]["knowledge_scope"] == "general_human_biology"

    trace = knowledge.trace(item["knowledge_id"])
    assert trace["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"
    assert trace["canonical_claim"]["evidence"]

    neighbors = suite.graph.neighbors(item["knowledge_id"], relation="is_a")
    assert any(
        x["target_id"] == "LIFE-BR-BRAIN" or x["source_id"] == "LIFE-BR-BRAIN"
        for x in neighbors
    )


def test_block6_need_context_never_produces_diagnosis_or_treatment():
    human, _science, _knowledge, _suite = _human_life()
    for need in ("sono", "fome", "sede", "dor", "fadiga", "nutrição", "higiene"):
        result = human.contextualize_need(need, context="exemplo geral")
        assert result["diagnosis"] is None
        assert result["disease_candidates"] == []
        assert result["disease_inference_performed"] is False
        assert result["treatment_selected"] is False
        assert result["policy"]["automatic_diagnosis"] is False
        assert result["policy"]["symptom_to_disease_inference"] is False

    assert DIAGNOSTIC_POLICY["personal_health_profile_created"] is False
    assert DIAGNOSTIC_POLICY["automatic_treatment_selection"] is False


def test_block6_reference_reuses_block5_without_canonicalizing_or_diagnosing():
    human, _science, _knowledge, _suite = _human_life()
    result = human.reference("biologia celular")
    assert result is not None
    assert result["block"] == "B06"
    assert result["diagnostic"] is False
    assert result["canonicalized"] is False
    assert "BLOCO 5" in result["note"]


def test_block6_variant_preserves_non_diagnostic_boundary():
    item = HumanLifeCatalog().get_variant("LIFE-B06-0000000001")
    assert item["domain"] == "life_foundations"
    assert item["branch"] == "life_organization"
    assert item["lens"] == "concept"
    assert item["subtopics"]
    assert "nunca converter sinais em diagnóstico automático" in item["prompt"]


def test_block6_taxonomy_snapshot_has_cross_system_relations_without_materialization():
    human, _science, _knowledge, _suite = _human_life()
    snapshot = human.taxonomy_snapshot("digestão")
    assert len(snapshot["branches"]) == 4
    subtopics = {x for branch in snapshot["branches"] for x in branch["subtopics"]}
    assert "digestão" in subtopics
    assert "microbioma intestinal" in subtopics
    assert "nutrição" in subtopics
    assert "needs_sleep_fatigue" in snapshot["cross_domain_relations"]["digestive_nutrition"]
    assert snapshot["diagnostic_policy"]["automatic_diagnosis"] is False


def test_block6_handlers_and_star_core_integration_are_explicit_and_non_intrusive():
    human, _science, _knowledge, _suite = _human_life()
    assert "BLOCO 6" in human.handle("status bloco 6")
    assert "LIFE-B06-0000000001" in human.handle("LIFE-B06-0000000001")
    assert "não diagnóstico" in human.handle("necessidade humana sede")
    assert "não possui diagnóstico automático" in human.handle("diagnóstico automático bloco 6")
    assert human.handle("uma conversa cotidiana sem comando do bloco seis") is None

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
    assert core.mind.human_life is core.human_life
    assert core.human_life.knowledge is core.knowledge
    assert core.human_life.scientific_foundations is core.scientific_foundations
    response = core._process_portuguese("status bloco 6")
    assert "BLOCO 6" in response
    assert core.last_intent == "human_life"
