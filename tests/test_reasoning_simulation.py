from __future__ import annotations

from copy import deepcopy
import pytest

from core.attention_salience import AttentionSalience
from core.memory_continuity import MemoryContinuity
from core.mind import CognitiveSuite
from core.reasoning_simulation import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    REASONING_BRANCHES,
    REASONING_POLICY,
    VARIANTS_PER_NODE,
    ReasoningSimulation,
)
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _stack():
    mind = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(mind.epistemics, mind.graph)
    memory = MemoryContinuity(knowledge, memory=mind.memory, graph=mind.graph)
    attention = AttentionSalience(knowledge, memory_continuity=memory, state=StarState())
    engine = ReasoningSimulation(
        knowledge,
        reasoning=mind.reasoning,
        simulation=mind.simulation,
        verifier=mind.verifier,
        memory_continuity=memory,
        attention_salience=attention,
    )
    return engine, mind, knowledge, memory, attention


def test_b18_exact_1b_and_boundaries():
    engine, *_ = _stack()
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert engine.catalog.content_id(0, 0) == "RSN-B18-0000000001"
    assert engine.catalog.content_id(499, 1_999_999) == "RSN-B18-1000000000"
    assert engine.catalog.get_variant("RSN-B18-0000000001") is not None
    assert engine.catalog.get_variant("RSN-B18-1000000000") is not None
    assert engine.catalog.get_variant("RSN-B18-1000000001") is None


def test_b18_covers_requested_topics():
    haystack = " ".join(b.key + " " + b.label + " " + " ".join(b.subtopics) for b in REASONING_BRANCHES).casefold()
    for topic in ("causalidade", "analogia", "abstração", "generalização", "exceções", "contrafactuais",
                  "simulação", "previsão", "prediction error", "risco", "consequências", "reversibilidade"):
        assert topic.casefold() in haystack


def test_b18_reuses_existing_reasoning_simulation_and_verifier():
    engine, mind, *_ = _stack()
    assert engine.reasoning is mind.reasoning
    assert engine.simulation is mind.simulation
    assert engine.verifier is mind.verifier
    assert len(mind.CAPABILITIES) == 15


def test_context_selection_is_bounded_without_loading_all_candidates():
    engine, _mind, _knowledge, _memory, attention = _stack()
    consumed = {"count": 0}
    def candidates():
        for i in range(10000):
            consumed["count"] += 1
            yield {"id": str(i), "content": f"candidate {i}", "importance": i / 10000}
    result = engine.select_context(candidates(), limit=5)
    assert len(result["selected"]) <= 5
    assert result["bounded"] is True
    assert consumed["count"] <= attention.max_candidates + 1


def test_causal_analysis_preserves_evidence_and_keeps_hypothesis():
    engine, *_ = _stack()
    evidence = [{"source": "A", "stance": "support"}]
    before = deepcopy(evidence)
    result = engine.causal_analysis("X", "Y", evidence=evidence, alternatives=["Z"], confounders=["C"])
    assert evidence == before
    assert result["causal_claim_proven"] is False
    assert result["epistemic_kind"] == "hypothesis"
    assert result["verification_needed"] is True
    assert result["original_evidence_mutated"] is False


def test_analogy_and_generalization_remain_inferences():
    engine, *_ = _stack()
    analogy = engine.analogy("sistema A", "sistema B", mappings=[{"a": "b"}], limits=["escala diferente"])
    assert analogy["epistemic_kind"] == "inference"
    assert analogy["analogy_proves_equivalence"] is False
    general = engine.generalize([1, 2, 3], scope="amostra local", exceptions=[4])
    assert general["epistemic_kind"] == "inference"
    assert general["universal_claim"] is False
    assert general["requires_new_cases_for_verification"] is True


def test_counterfactual_and_simulation_do_not_mutate_baseline():
    engine, *_ = _stack()
    facts = {"temperature": 20, "door": "closed"}
    original = deepcopy(facts)
    cf = engine.counterfactual(facts, changed_assumption={"door": "open"}, projected_consequences=["heat loss"])
    assert facts == original
    assert cf["baseline"] == original
    assert cf["counterfactual_is_history"] is False
    assert cf["original_facts_mutated"] is False

    state = {"x": 1, "y": 2}
    state_before = deepcopy(state)
    sim = engine.simulate_state(state, {"x": 9}, assumptions=["isolated change"])
    assert state == state_before
    assert sim["initial_state"] == state_before
    assert sim["simulated_state"]["x"] == 9
    assert sim["simulation_is_observation"] is False
    assert sim["original_state_mutated"] is False


def test_numeric_simulation_delegates_to_existing_lab():
    engine, *_ = _stack()
    result = engine.run_numeric_simulation("exponential", initial=2, rate=0.0, duration=1, steps=3)
    assert result["kind"] == "exponential"
    assert result["result"]["final"] == pytest.approx(2.0)
    assert result["simulation_is_observation"] is False
    with pytest.raises(ValueError):
        engine.run_numeric_simulation("unknown")


def test_prediction_and_prediction_error_preserve_status():
    engine, _mind, _knowledge, memory, *_ = _stack()
    prediction = engine.prediction("resultado X", basis=["evidence A"], confidence=0.7, horizon="tomorrow")
    assert prediction["epistemic_kind"] == "prediction"
    assert prediction["certainty"] is False
    assert prediction["observed"] is False
    assert memory.working.get("b18:last_prediction") is not None
    error = engine.prediction_error(10, 12, context="unit-test")
    assert error["signed_error"] == pytest.approx(2.0)
    assert error["absolute_error"] == pytest.approx(2.0)
    assert error["prediction_rewritten_as_fact"] is False
    assert error["observed_value_preserved"] is True


def test_risk_consequences_and_reversibility_do_not_authorize():
    engine, *_ = _stack()
    result = engine.assess_risk([
        {"consequence": "A", "probability": 0.8, "impact": 0.9, "reversibility": 0.1},
        {"consequence": "B", "probability": 0.2, "impact": 0.4, "reversibility": 0.9},
    ])
    assert len(result["items"]) == 2
    assert 0 <= result["max_risk"] <= 1
    assert result["risk_is_permission"] is False
    assert result["operational_authorization"] is False


def test_derived_conclusion_goes_to_working_memory_not_facts():
    engine, _mind, _knowledge, memory, *_ = _stack()
    premises = [{"fact": "A"}, {"fact": "B"}]
    original = deepcopy(premises)
    result = engine.derive_conclusion(premises, "C pode seguir de A e B", confidence=0.66)
    assert premises == original
    assert result["epistemic_kind"] == "inference"
    assert result["canonical_fact"] is False
    assert result["requires_verification"] is True
    assert result["original_facts_mutated"] is False
    assert memory.working.get(result["working_memory_id"]) is not None


def test_verification_reuses_truth_verifier_without_promoting_claim():
    engine, *_ = _stack()
    result = engine.verify_claim("claim", [{"source": "s", "stance": "support", "credibility": 1.0}])
    assert result["claim"] == "claim"
    assert result["verdict"] in {"supported", "insufficient_evidence", "disputed_or_mixed", "refuted"}


def test_b18_namespace_graph_and_policy():
    engine, mind, knowledge, *_ = _stack()
    ns = knowledge.store.get_namespace("B18")
    assert ns and ns["logical_capacity"] == 1_000_000_000
    assert engine.graph is mind.graph
    taxonomy = engine.materialize_taxonomy("causality")
    assert taxonomy["branches_materialized"] == 5
    assert taxonomy["parallel_reasoning_engine_created"] is False
    assert taxonomy["parallel_simulation_lab_created"] is False
    assert REASONING_POLICY["inference_is_fact"] is False
    assert REASONING_POLICY["simulation_is_observation"] is False
    assert REASONING_POLICY["prediction_is_certainty"] is False
    assert REASONING_POLICY["counterfactual_is_history"] is False
    assert REASONING_POLICY["derived_conclusion_mutates_original_facts"] is False


def test_b18_handle_is_nonintrusive():
    engine, *_ = _stack()
    assert "BLOCO 18" in engine.handle("status bloco 18")
    assert "RSN-B18-0000000001" in engine.handle("RSN-B18-0000000001")
    assert engine.handle("oi, tudo bem?") is None
