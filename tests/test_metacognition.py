from __future__ import annotations

from core.attention_salience import AttentionSalience
from core.memory_continuity import MemoryContinuity
from core.metacognition import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    METACOGNITION_POLICY,
    METACOGNITIVE_BRANCHES,
    VARIANTS_PER_NODE,
    Metacognition,
)
from core.mind import CognitiveSuite
from core.reasoning_simulation import ReasoningSimulation
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _stack():
    mind = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(mind.epistemics, mind.graph)
    memory = MemoryContinuity(knowledge, memory=mind.memory, graph=mind.graph)
    attention = AttentionSalience(knowledge, memory_continuity=memory, state=StarState())
    reasoning = ReasoningSimulation(
        knowledge,
        reasoning=mind.reasoning,
        simulation=mind.simulation,
        verifier=mind.verifier,
        memory_continuity=memory,
        attention_salience=attention,
    )
    meta = Metacognition(
        knowledge,
        base_engine=mind.metacognition,
        verifier=mind.verifier,
        memory_continuity=memory,
        attention_salience=attention,
        reasoning_simulation=reasoning,
    )
    return meta, mind, knowledge, memory, attention, reasoning


def test_b20_exact_1b_and_boundaries():
    meta, *_ = _stack()
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert meta.catalog.content_id(0, 0) == "META-B20-0000000001"
    assert meta.catalog.content_id(499, 1_999_999) == "META-B20-1000000000"
    assert meta.catalog.get_variant("META-B20-1000000000") is not None
    assert meta.catalog.get_variant("META-B20-1000000001") is None


def test_b20_covers_requested_questions():
    haystack = " ".join(b.label + " " + " ".join(b.subtopics) for b in METACOGNITIVE_BRANCHES).casefold()
    for topic in (
        "o que sabe", "o que não sabe", "o que acredita", "o que inferiu", "confiança",
        "fonte", "contradições", "precisa pesquisar", "precisa perguntar", "precisa revisar",
    ):
        assert topic.casefold() in haystack


def test_b20_reuses_existing_metacognition_engine():
    meta, mind, *_ = _stack()
    assert meta.base_engine is mind.metacognition
    assert len(mind.CAPABILITIES) == 15


def test_assessment_distinguishes_knowledge_belief_inference_and_unknown():
    meta, *_ = _stack()
    result = meta.assess(
        "qual é o estado?",
        local_answer=True,
        confidence=0.9,
        sources=["source-A"],
        belief="parece estável",
        inference="pode continuar estável",
    )
    assert result["knows"] is True
    assert result["does_not_know"] is False
    assert result["belief_is_fact"] is False
    assert result["inference_is_fact"] is False
    assert result["has_source"] is True
    assert result["operational_authorization"] is False


def test_unknown_without_source_requests_research_but_not_network_permission():
    meta, *_ = _stack()
    result = meta.assess("dado ausente", local_answer=False, confidence=0.1, sources=[], network_allowed=False)
    assert result["does_not_know"] is True
    assert result["needs_research"] is True
    assert result["research_need_grants_network_permission"] is False
    assert result["recommended_action"] == "research_when_authorized"


def test_missing_context_requests_question_before_research():
    meta, *_ = _stack()
    result = meta.assess(
        "faça isso",
        local_answer=False,
        confidence=0.0,
        missing_context=["qual arquivo", "qual objetivo"],
    )
    assert result["needs_question"] is True
    assert result["recommended_action"] == "ask"


def test_contradictions_are_preserved_and_trigger_review():
    meta, *_ = _stack()
    contradictions = [{"claim":"A"}, {"claim":"not A"}]
    result = meta.assess(
        "A?",
        local_answer=True,
        confidence=0.8,
        sources=["s1", "s2"],
        contradictions=contradictions,
    )
    assert result["has_contradictions"] is True
    assert result["contradictions"] == contradictions
    assert result["needs_review"] is True
    assert result["knows"] is False


def test_current_information_requires_research_even_with_local_answer():
    meta, *_ = _stack()
    result = meta.assess(
        "estado atual",
        local_answer=True,
        confidence=0.95,
        sources=["local-cache"],
        current_information=True,
        network_allowed=True,
    )
    assert result["needs_research"] is True
    assert result["recommended_action"] in {"research_if_network_allowed", "review"}


def test_context_selection_is_bounded():
    meta, _mind, _knowledge, _memory, attention, _reasoning = _stack()
    consumed = {"count": 0}
    def stream():
        for i in range(10000):
            consumed["count"] += 1
            yield {"id": str(i), "content": f"candidate {i}", "importance": 0.5}
    result = meta.assess("avaliar", candidates=stream())
    assert result["context_bounded"] is True
    assert len(result["selected_context"]) <= 16
    assert consumed["count"] <= attention.max_candidates + 1


def test_verifier_readiness_does_not_promote_claim():
    meta, *_ = _stack()
    result = meta.verify_readiness("claim", [{"source":"s", "stance":"support", "credibility":1.0}])
    assert result["canonical_promotion_performed"] is False
    assert "verdict" in result


def test_prediction_error_can_trigger_review_without_rewriting_history():
    meta, *_ = _stack()
    result = meta.monitor_prediction(10, 20, context="test")
    assert result["review_recommended"] is True
    assert result["history_rewritten"] is False
    assert result["prediction_error"]["prediction_rewritten_as_fact"] is False


def test_namespace_graph_policy_and_nonintrusive_handler():
    meta, mind, knowledge, *_ = _stack()
    ns = knowledge.store.get_namespace("B20")
    assert ns and ns["logical_capacity"] == 1_000_000_000
    assert meta.graph is mind.graph
    materialized = meta.materialize_taxonomy("knowledge_state")
    assert materialized["branches_materialized"] == 5
    assert materialized["parallel_metacognition_engine_created"] is False
    assert METACOGNITION_POLICY["belief_is_fact"] is False
    assert METACOGNITION_POLICY["confidence_is_truth"] is False
    assert METACOGNITION_POLICY["contradictions_are_silently_erased"] is False
    assert "BLOCO 20" in meta.handle("status bloco 20")
    assert "META-B20-0000000001" in meta.handle("META-B20-0000000001")
    assert meta.handle("oi") is None
