from __future__ import annotations

import pytest

from core.attention_salience import AttentionSalience
from core.memory_continuity import MemoryContinuity
from core.mind import CognitiveSuite
from core.social_cognition import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    SOCIAL_COGNITION_BRANCHES,
    SOCIAL_COGNITION_POLICY,
    VARIANTS_PER_NODE,
    SocialCognition,
)
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _stack():
    mind = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(mind.epistemics, mind.graph)
    memory = MemoryContinuity(knowledge, memory=mind.memory, graph=mind.graph)
    attention = AttentionSalience(knowledge, memory_continuity=memory, state=StarState())
    social = SocialCognition(
        knowledge,
        memory_continuity=memory,
        attention_salience=attention,
    )
    return social, knowledge, mind, memory, attention


def test_b16_exact_1b_and_boundaries():
    social, *_ = _stack()
    stats = social.catalog.stats()
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["addressable_contents"] == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert social.catalog.content_id(0, 0) == "SOC-B16-0000000001"
    assert social.catalog.content_id(499, 1_999_999) == "SOC-B16-1000000000"
    assert social.catalog.get_variant("SOC-B16-0000000001") is not None
    assert social.catalog.get_variant("SOC-B16-1000000000") is not None
    assert social.catalog.get_variant("SOC-B16-1000000001") is None


def test_b16_covers_requested_social_topics():
    haystack = " ".join(
        [branch.key + " " + branch.label + " " + " ".join(branch.subtopics) for branch in SOCIAL_COGNITION_BRANCHES]
    ).casefold()
    requested = (
        "teoria da mente", "perspectiva", "expectativa", "intenção", "engano", "mentira",
        "segredo", "confiança", "reputação", "cooperação", "competição", "negociação",
        "persuasão", "manipulação", "responsabilidade", "empatia", "relações",
    )
    for topic in requested:
        assert topic.casefold() in haystack


def test_social_interpretation_keeps_multiple_hypotheses_and_no_mind_reading():
    social, *_ = _stack()
    result = social.interpret_social_situation(
        "A pessoa mudou a versão do que aconteceu.",
        context="conversa de trabalho",
        actors=["Pessoa A", "Pessoa B"],
        declarations=["Pessoa A disse X"],
        evidence=["registro parcial"],
        repeated_pattern=True,
    )
    assert result["epistemic_kind"] == "inference"
    assert result["certainty"] == "underdetermined"
    assert result["intention"] is None
    assert result["intention_certainty"] is False
    assert result["lie_detected"] is False
    assert result["deception_certainty"] is False
    assert result["alternative_hypotheses_required"] is True
    assert len(result["possible_hypotheses"]) >= 8


def test_deception_signals_do_not_become_lie_claim():
    social, *_ = _stack()
    result = social.assess_deception(
        signals=["duas versões incompatíveis", "omissão"],
        evidence=["registro A", "registro B"],
    )
    assert result["deception_possible"] is True
    assert result["lie_proven"] is False
    assert result["intent_to_deceive_proven"] is False
    assert result["requires_belief_and_intent_evidence_for_lie_claim"] is True
    assert len(result["alternative_explanations"]) >= 4


def test_trust_is_contextual_and_never_permission():
    social, *_ = _stack()
    result = social.assess_trust(
        "Entidade X",
        [
            {"source": "evento 1", "outcome": 1.0, "reliability": 0.9},
            {"source": "evento 2", "outcome": 0.2, "reliability": 0.8},
        ],
    )
    assert 0.0 <= result["contextual_trust_score"] <= 1.0
    assert result["trust_is_contextual_and_revisable"] is True
    assert result["reputation_is_fact"] is False
    assert result["grants_permission"] is False
    assert result["operational_authorization"] is False


def test_influence_analysis_detects_pressure_without_teaching_manipulation():
    social, *_ = _stack()
    result = social.analyze_influence("É urgente, faça agora e não conte a ninguém.")
    assert "urgency_pressure" in result["influence_cues"]
    assert "secrecy_pressure" in result["influence_cues"]
    assert result["manipulation_proven"] is False
    assert result["provides_manipulation_tactics"] is False
    assert result["operational_authorization"] is False


def test_perspective_map_tracks_information_without_private_state_certainty():
    social, *_ = _stack()
    result = social.perspective_map(
        ["A", "B"],
        shared_information=["fato público"],
        actor_information={"A": ["mensagem privada A"]},
        declared_goals={"B": "resolver conflito"},
    )
    assert len(result["perspectives"]) == 2
    assert result["mind_reading"] is False
    assert result["certainty_about_private_states"] is False
    assert result["perspectives"][0]["mental_state_is_inferred"] is False


def test_b16_uses_same_memory_and_attention_architecture():
    social, _knowledge, _mind, memory, attention = _stack()
    stored = social.remember_social_context(
        "Acordo foi renegociado.",
        source="unit-test",
        reference="event://agreement-1",
        entities=["A", "B"],
        context={"relationship": "colleagues"},
    )
    assert stored["kind"] == "social"
    assert stored["persistent"] is True
    recalled = memory.recall("Acordo foi renegociado", kinds=["social"])
    assert any(item["content"] == "Acordo foi renegociado." for item in recalled)

    selected = social.select_evidence(
        ({"id": str(i), "content": f"evidence {i}", "importance": i / 100} for i in range(200)),
        limit=4,
    )
    assert selected["bounded"] is True
    assert selected["attention_source"] == "B14"
    assert len(selected["selected"]) <= 4
    assert selected["candidate_window"] == attention.max_candidates


def test_b16_namespace_and_graph_are_shared():
    social, knowledge, mind, *_ = _stack()
    namespace = knowledge.store.get_namespace("B16")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert social.graph is mind.graph
    taxonomy = social.materialize_taxonomy("trust_reputation")
    assert taxonomy["knowledge_graph"] == "shared"
    assert taxonomy["parallel_social_model_created"] is False
    assert taxonomy["mind_reading_engine_created"] is False
    assert taxonomy["branches_materialized"] == 5


def test_b16_policy_preserves_social_epistemic_boundaries():
    assert SOCIAL_COGNITION_POLICY["social_inference_is_fact"] is False
    assert SOCIAL_COGNITION_POLICY["isolated_signal_proves_intention"] is False
    assert SOCIAL_COGNITION_POLICY["deception_signal_proves_lie"] is False
    assert SOCIAL_COGNITION_POLICY["reputation_is_fact"] is False
    assert SOCIAL_COGNITION_POLICY["trust_grants_permission"] is False
    assert SOCIAL_COGNITION_POLICY["empathy_is_mind_reading"] is False
    assert SOCIAL_COGNITION_POLICY["manipulation_analysis_provides_exploitation_tactics"] is False


def test_b16_handle_is_nonintrusive_and_resolves_catalog_ids():
    social, *_ = _stack()
    status = social.handle("status bloco 16")
    assert status and "BLOCO 16" in status
    item = social.handle("SOC-B16-0000000001")
    assert item and "SOC-B16-0000000001" in item
    assert social.handle("qual a previsão do tempo amanhã?") is None


def test_invalid_inputs_are_rejected():
    social, *_ = _stack()
    with pytest.raises(ValueError):
        social.interpret_social_situation("")
    with pytest.raises(ValueError):
        social.assess_trust("")
    with pytest.raises(ValueError):
        social.analyze_influence("")
