from uuid import uuid4
import unicodedata

import pytest

from core.human_psychology import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    INTERPRETATION_POLICY,
    PSYCHOLOGY_BRANCHES,
    PSYCHOLOGY_DOMAINS,
    PSYCHOLOGY_LENSES,
    REQUESTED_TOPICS,
    VARIANTS_PER_NODE,
    HumanPsychologyFoundations,
    PsychologyCatalog,
)
from core.mind import CognitiveSuite
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _norm(text):
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return " ".join(value.replace("_", " ").split())


def _psychology():
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    psych = HumanPsychologyFoundations(knowledge)
    return psych, knowledge, suite


def _canonical_fact(suite: CognitiveSuite, marker: str):
    source_id = suite.epistemics.register_source(
        f"unit://psychology/{marker}", source_type="test", title=f"Fonte psicológica {marker}",
        reliability=1.0, reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        f"Conhecimento psicológico geral validado {marker}", epistemic_kind="fact",
        origin_type="unit_test", origin_ref=f"unit://psychology-claim/{marker}",
        source_id=source_id, confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"], f"Evidência psicológica rastreável {marker}",
        evidence_type="primary_source", stance="support", source_id=source_id,
        strength=1.0, reliability=1.0,
    )
    suite.epistemics.transition(record["record_id"], "VERIFIED", reason="evidência rastreável", actor="unit-test")
    return suite.epistemics.transition(record["record_id"], "CANONICAL", reason="claim geral apto ao B07", actor="unit-test")


def test_block7_catalog_is_exactly_1b_and_on_demand():
    catalog = PsychologyCatalog()
    stats = catalog.stats()
    assert len(PSYCHOLOGY_DOMAINS) == 13
    assert len(PSYCHOLOGY_BRANCHES) == 50
    assert len(PSYCHOLOGY_LENSES) == 20
    assert CANONICAL_NODES == 1_000
    assert VARIANTS_PER_NODE == 1_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_knowledge_rows"] == 0
    assert catalog.content_id(0, 0) == "PSY-B07-0000000001"
    assert catalog.content_id(999, 999_999) == "PSY-B07-1000000000"
    assert catalog.get_variant("PSY-B07-1000000001") is None


def test_block7_contains_all_requested_topics_and_contextual_depth():
    corpus = _norm(" ".join(
        [b.label for b in PSYCHOLOGY_BRANCHES]
        + [topic for b in PSYCHOLOGY_BRANCHES for topic in b.subtopics]
    ))
    for topic in REQUESTED_TOPICS:
        assert _norm(topic) in corpus, topic
    assert "interpretações alternativas" in " ".join(x for b in PSYCHOLOGY_BRANCHES for x in b.subtopics)
    assert "diferenças culturais" in " ".join(x for b in PSYCHOLOGY_BRANCHES for x in b.subtopics)
    assert "variação individual" in " ".join(x for b in PSYCHOLOGY_BRANCHES for x in b.subtopics)


def test_block7_registers_b07_on_same_universal_architecture():
    psych, knowledge, _suite = _psychology()
    namespace = knowledge.store.get_namespace("B07")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert psych.knowledge is knowledge
    assert psych.graph is knowledge.graph
    assert psych.stats()["knowledge_graph"] == "shared knowledge_nodes/knowledge_edges"


def test_block7_taxonomy_materializes_into_shared_graph_and_links_block6():
    psych, _knowledge, suite = _psychology()
    result = psych.materialize_taxonomy("teoria da mente")
    assert result["knowledge_graph"] == "shared"
    assert result["diagnostic_engine_created"] is False
    assert result["branches_materialized"] == 4
    root_neighbors = suite.graph.neighbors("PSY-TAX-ROOT")
    labels = {x["label"] for x in root_neighbors}
    assert "Vida, Corpo e Necessidades Humanas" in labels
    assert "Teoria da mente e cognição social" in labels
    branch_neighbors = suite.graph.neighbors("PSY-BR-THEORY_OF_MIND", relation="has_part")
    assert any(x["node_type"] == "psychology_subtopic" for x in branch_neighbors)


def test_block7_behavior_interpretation_never_becomes_diagnosis_trait_or_intention():
    psych, _knowledge, _suite = _psychology()
    result = psych.interpret_behavior("uma pessoa desviou o olhar", context="conversa breve")
    assert result["epistemic_kind"] == "inference"
    assert result["certainty"] == "underdetermined"
    assert len(result["possible_interpretations"]) >= 7
    assert result["alternative_interpretations_required"] is True
    assert result["exceptions_required"] is True
    assert result["diagnosis"] is None
    assert result["mental_disorder_candidates"] == []
    assert result["stable_personality_label"] is None
    assert result["intention"] is None
    assert result["intention_certainty"] is False
    assert result["single_observation_is_pattern"] is False


def test_block7_repeated_behavior_still_does_not_create_certainty():
    psych, _knowledge, _suite = _psychology()
    result = psych.interpret_behavior(
        "evita falar em reuniões", context="trabalho", repeated_pattern=True,
        corroborating_evidence=["observado em três reuniões"],
    )
    assert result["repeated_pattern"] is True
    assert result["certainty"] == "underdetermined"
    assert result["diagnosis"] is None
    assert result["stable_personality_label"] is None
    assert any("longitudinal" in x for x in result["possible_interpretations"])


def test_block7_policy_forbids_automatic_psychological_profiles():
    assert INTERPRETATION_POLICY["isolated_behavior_is_diagnosis"] is False
    assert INTERPRETATION_POLICY["isolated_behavior_is_stable_trait"] is False
    assert INTERPRETATION_POLICY["expression_is_intention"] is False
    assert INTERPRETATION_POLICY["inferred_intention_is_certainty"] is False
    assert INTERPRETATION_POLICY["automatic_mental_disorder_inference"] is False
    assert INTERPRETATION_POLICY["automatic_personality_label"] is False
    assert INTERPRETATION_POLICY["personal_psychological_profile_created"] is False


def test_block7_canonical_knowledge_keeps_block2_gate_and_general_scope():
    psych, knowledge, suite = _psychology()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(f"unit://psych-discovered/{marker}", source_type="test", reliability=1.0)
    discovered = suite.epistemics.discover(
        f"Claim psicológico descoberto {marker}", epistemic_kind="fact", origin_type="unit_test",
        origin_ref=f"unit://psych-discovered-claim/{marker}", source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        psych.promote_canonical_psychology_knowledge(
            discovered["record_id"], f"Conhecimento psicológico {marker}",
            domain="cognição", branch="cognition",
        )

    canonical = _canonical_fact(suite, marker)
    item = psych.promote_canonical_psychology_knowledge(
        canonical["record_id"], f"Conhecimento psicológico {marker}",
        domain="cognição", branch="cognition",
        properties={"scope": "general"}, contexts=["educational"],
        summary="Conhecimento psicológico geral, não diagnóstico.",
    )
    assert item["namespace"] == "B07"
    assert item["properties"]["diagnostic_use"] is False
    assert item["properties"]["automatic_personality_label"] is False
    assert item["properties"]["intention_certainty"] is False
    assert item["properties"]["personal_psychological_profile"] is False
    trace = knowledge.trace(item["knowledge_id"])
    assert trace["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"
    assert trace["canonical_claim"]["evidence"]


def test_block7_reference_reuses_multidisciplinary_psychology_without_canonicalizing():
    psych, _knowledge, _suite = _psychology()
    result = psych.reference("memória")
    assert result is not None
    assert result["provider"] == "core.multidisciplinary_knowledge"
    assert result["subject"] == "psychology_sociology"
    assert result["diagnostic"] is False
    assert result["canonicalized"] is False


def test_block7_variant_and_handlers_preserve_boundary():
    item = PsychologyCatalog().get_variant("PSY-B07-0000000001")
    assert item["domain"] == "perception_attention"
    assert item["branch"] == "sensory_perception"
    assert item["lens"] == "concept"
    assert "possibilidades" in item["prompt"]
    assert "Nunca converter comportamento isolado" in item["prompt"]

    psych, _knowledge, _suite = _psychology()
    assert "BLOCO 7" in psych.handle("status bloco 7")
    assert "PSY-B07-0000000001" in psych.handle("PSY-B07-0000000001")
    assert "não transforma comportamento isolado" in psych.handle("diagnóstico psicológico automático")
    assert psych.handle("uma conversa cotidiana sem comando psicológico") is None
