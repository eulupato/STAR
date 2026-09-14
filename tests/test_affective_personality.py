from __future__ import annotations

import pytest

from core.affective_personality import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    PERSONALITY_BRANCHES,
    PERSONALITY_POLICY,
    VARIANTS_PER_NODE,
    AffectivePersonality,
)
from core.memory_continuity import MemoryContinuity
from core.mind import CognitiveSuite
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _stack():
    mind = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(mind.epistemics, mind.graph)
    memory = MemoryContinuity(knowledge, memory=mind.memory, graph=mind.graph)
    state = StarState()
    personality = AffectivePersonality(
        knowledge,
        state=state,
        memory_continuity=memory,
    )
    return personality, state, memory, knowledge, mind


def test_b17_exact_1b_and_boundaries():
    personality, *_ = _stack()
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    stats = personality.catalog.stats()
    assert stats["addressable_contents"] == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert personality.catalog.content_id(0, 0) == "PERS-B17-0000000001"
    assert personality.catalog.content_id(499, 1_999_999) == "PERS-B17-1000000000"
    assert personality.catalog.get_variant("PERS-B17-0000000001") is not None
    assert personality.catalog.get_variant("PERS-B17-1000000000") is not None
    assert personality.catalog.get_variant("PERS-B17-1000000001") is None


def test_b17_covers_requested_affect_and_personality_topics():
    haystack = " ".join(
        branch.key + " " + branch.label + " " + " ".join(branch.subtopics)
        for branch in PERSONALITY_BRANCHES
    ).casefold()
    for topic in (
        "valência", "energia", "curiosidade", "cautela", "familiaridade", "confiança",
        "interesse", "alerta", "preferências", "estilo", "história", "relações",
        "experiências", "personalidade adaptativa",
    ):
        assert topic.casefold() in haystack


def test_current_affect_reuses_official_star_state_and_session_context():
    personality, state, *_ = _stack()
    state.update(energy=73, curiosity=61, confidence=84)
    personality.update_session_affect(valence=-0.25, caution=0.8, familiarity=0.7, interest=0.9, alert=0.6, context="unit-test")
    snapshot = personality.current_state()
    assert snapshot["energy"] == pytest.approx(0.73)
    assert snapshot["curiosity"] == pytest.approx(0.61)
    assert snapshot["confidence"] == pytest.approx(0.84)
    assert snapshot["valence"] == pytest.approx(-0.25)
    assert snapshot["caution"] == pytest.approx(0.8)
    assert snapshot["familiarity"] == pytest.approx(0.7)
    assert snapshot["interest"] == pytest.approx(0.9)
    assert snapshot["alert"] == pytest.approx(0.6)
    assert snapshot["personality_is_identity"] is False
    assert snapshot["operational_authorization"] is False


def test_persistent_axis_survives_component_reinitialization():
    personality, state, memory, knowledge, _mind = _stack()
    written = personality.set_axis(
        "caution",
        0.67,
        source="unit-test",
        reference="test://b17-axis-persistence",
        reason="test persistence",
    )
    assert written["value"] == pytest.approx(0.67)
    second = AffectivePersonality(knowledge, state=state, memory_continuity=memory)
    assert second.persistent_axis("caution") == pytest.approx(0.67)
    assert second.current_state()["persistent_baselines"]["caution"] == pytest.approx(0.67)


def test_personality_axis_history_is_append_only():
    personality, *_ = _stack()
    personality.set_axis("interest", 0.41, source="unit-test", reference="test://interest-1")
    personality.set_axis("interest", 0.62, source="unit-test", reference="test://interest-2")
    history = personality.axis_history("interest", limit=10)
    assert len(history) >= 2
    assert history[0]["id"] > history[-1]["id"]
    assert history[0]["metadata"]["value"] == pytest.approx(0.62)
    assert any(item["metadata"].get("value") == pytest.approx(0.41) for item in history)


def test_preferences_and_style_are_persistent_records_not_prompt_only():
    personality, state, memory, knowledge, _mind = _stack()
    personality.set_preference("response_density", "concise", source="unit-test", reference="test://preference")
    personality.set_style("reasoning", "structured", source="unit-test", reference="test://style")
    second = AffectivePersonality(knowledge, state=state, memory_continuity=memory)
    assert second.preference("response_density")["value"] == "concise"
    assert second.style("reasoning")["value"] == "structured"
    assert PERSONALITY_POLICY["personality_is_prompt_only"] is False


def test_experience_is_auditable_and_adaptation_is_bounded():
    personality, *_ = _stack()
    experience = personality.record_experience(
        "Uma validação importante encontrou um erro antes do merge.",
        source="unit-test",
        reference="test://experience-validated-error",
        valence=-0.3,
        intensity=0.8,
        meaning="valorizar verificação antes de decisão irreversível",
    )
    memory_id = experience["memory_id"]
    old = personality.persistent_axis("caution")
    adapted = personality.adapt_from_experience(
        memory_id,
        {"caution": 1.0, "confidence": -0.5},
        source="unit-test",
        reference="test://adaptation-1",
        learning_rate=0.9,
    )
    assert adapted["learning_rate"] == pytest.approx(0.1)
    caution_update = next(item for item in adapted["updates"] if item["axis"] == "caution")
    assert caution_update["value"] <= min(1.0, old + 0.100001)
    assert adapted["source_experience_preserved"] is True
    assert adapted["identity_mutation"] is False
    assert adapted["fundamental_values_mutation"] is False
    assert adapted["operational_authorization"] is False


def test_adaptation_rejects_non_autobiographical_or_missing_experience():
    personality, *_ = _stack()
    with pytest.raises(ValueError):
        personality.adapt_from_experience(999999999, {"caution": 0.2}, source="unit-test", reference="test://missing")
    with pytest.raises(ValueError):
        personality.record_experience("sem referência", source="unit-test", reference="")


def test_relationship_history_reuses_b13_social_memory():
    personality, _state, memory, *_ = _stack()
    result = personality.record_relationship(
        "Pessoa Teste",
        "cooperação em uma tarefa",
        source="unit-test",
        reference="test://relationship-1",
        familiarity=0.4,
    )
    assert result["kind"] == "social"
    assert result["persistent"] is True
    recalled = memory.recall("Pessoa Teste", kinds=["social"])
    assert any("Pessoa Teste" in item["content"] for item in recalled)
    assert result["familiarity"] == pytest.approx(0.4)


def test_b17_reuses_same_database_and_shared_graph():
    personality, _state, _memory, knowledge, mind = _stack()
    namespace = knowledge.store.get_namespace("B17")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert personality.graph is mind.graph
    taxonomy = personality.materialize_taxonomy("adaptive_personality")
    assert taxonomy["branches_materialized"] == 5
    assert taxonomy["knowledge_graph"] == "shared"
    assert taxonomy["parallel_identity"] is False
    assert taxonomy["parallel_personality_database"] is False


def test_b17_policy_keeps_identity_values_and_permissions_separate():
    assert PERSONALITY_POLICY["personality_is_identity"] is False
    assert PERSONALITY_POLICY["affect_is_identity"] is False
    assert PERSONALITY_POLICY["preference_is_fundamental_rule"] is False
    assert PERSONALITY_POLICY["confidence_is_permission"] is False
    assert PERSONALITY_POLICY["automatic_identity_rewrite"] is False
    assert PERSONALITY_POLICY["automatic_values_rewrite"] is False
    assert PERSONALITY_POLICY["history_is_append_only"] is True
    assert PERSONALITY_POLICY["operational_authorization"] is False


def test_b17_handle_is_nonintrusive():
    personality, *_ = _stack()
    assert "BLOCO 17" in personality.handle("status bloco 17")
    assert "PERS-B17-0000000001" in personality.handle("PERS-B17-0000000001")
    assert personality.handle("qual é a capital do brasil?") is None


def test_persistent_writes_require_auditable_source_and_reference():
    personality, *_ = _stack()
    with pytest.raises(ValueError):
        personality.set_axis("alert", 0.4, source="", reference="test://x")
    with pytest.raises(ValueError):
        personality.set_preference("x", "y", source="unit-test", reference="")
