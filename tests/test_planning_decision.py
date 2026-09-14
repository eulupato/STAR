from __future__ import annotations

from copy import deepcopy
import pytest

from core.attention_salience import AttentionSalience
from core.foundations import FoundationSuite
from core.memory_continuity import MemoryContinuity
from core.mind import CognitiveSuite
from core.planning_decision import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    PLANNING_BRANCHES,
    PLANNING_POLICY,
    STAGES,
    VARIANTS_PER_NODE,
    PlanningDecision,
)
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
    foundations = FoundationSuite()
    planning = PlanningDecision(
        knowledge,
        planner=mind.planner,
        reasoning_simulation=reasoning,
        memory_continuity=memory,
        attention_salience=attention,
        operational_boundary=foundations.boundary,
    )
    return planning, mind, knowledge, memory, attention, reasoning, foundations


def _options():
    return [
        {
            "id": "safe",
            "label": "Mudança reversível",
            "changes": {"mode": "target"},
            "utility": 0.8,
            "reversibility": 0.95,
            "consequences": [
                {"consequence": "retrabalho pequeno", "probability": 0.2, "impact": 0.2, "reversibility": 0.95}
            ],
        },
        {
            "id": "risky",
            "label": "Mudança irreversível",
            "changes": {"mode": "target"},
            "utility": 0.9,
            "reversibility": 0.05,
            "consequences": [
                {"consequence": "falha grave", "probability": 0.9, "impact": 0.95, "reversibility": 0.05}
            ],
        },
    ]


def test_b19_exact_1b_and_boundaries():
    planning, *_ = _stack()
    assert len(STAGES) == 10
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert planning.catalog.content_id(0, 0) == "PLAN-B19-0000000001"
    assert planning.catalog.content_id(499, 1_999_999) == "PLAN-B19-1000000000"
    assert planning.catalog.get_variant("PLAN-B19-0000000001") is not None
    assert planning.catalog.get_variant("PLAN-B19-1000000000") is not None
    assert planning.catalog.get_variant("PLAN-B19-1000000001") is None


def test_b19_pipeline_is_exact_and_requested_topics_are_covered():
    assert tuple(STAGES) == (
        "goal", "current_state", "desired_state", "obstacles", "options",
        "simulation", "risk", "plan", "decision", "verification",
    )
    haystack = " ".join(
        branch.key + " " + branch.label + " " + " ".join(branch.subtopics)
        for branch in PLANNING_BRANCHES
    ).casefold()
    for topic in (
        "objetivo", "estado atual", "estado desejado", "obstáculo", "opção",
        "simulação", "risco", "plano", "decisão", "verificação",
    ):
        assert topic.casefold() in haystack


def test_b19_reuses_official_planner_and_b18_without_changing_mind_contract():
    planning, mind, *_rest = _stack()
    assert planning.planner is mind.planner
    assert planning.reasoning_simulation.reasoning is mind.reasoning
    assert planning.reasoning_simulation.simulation is mind.simulation
    assert len(mind.CAPABILITIES) == 15


def test_b19_context_selection_is_bounded():
    planning, _mind, _knowledge, _memory, attention, *_ = _stack()
    consumed = {"count": 0}

    def candidates():
        for i in range(10000):
            consumed["count"] += 1
            yield {"id": str(i), "content": f"candidate {i}", "importance": i / 10000}

    result = planning.select_context(candidates(), limit=5)
    assert len(result["selected"]) <= 5
    assert result["bounded"] is True
    assert consumed["count"] <= attention.max_candidates + 1


def test_b19_full_pipeline_preserves_inputs_and_selects_option():
    planning, *_ = _stack()
    current = {"mode": "current", "stable": True}
    desired = {"mode": "target"}
    obstacles = ["dependency A"]
    options = _options()
    before = deepcopy((current, desired, obstacles, options))

    result = planning.plan_decision(
        "Migrar de forma segura",
        current_state=current,
        desired_state=desired,
        obstacles=obstacles,
        options=options,
        constraints=["não executar automaticamente"],
    )

    assert (current, desired, obstacles, options) == before
    assert result["pipeline"] == (
        "OBJETIVO", "ESTADO ATUAL", "ESTADO DESEJADO", "OBSTÁCULOS", "OPÇÕES",
        "SIMULAÇÃO", "RISCO", "PLANO", "DECISÃO", "VERIFICAÇÃO",
    )
    assert result["decision"]["selected_option"] == "safe"
    assert result["decision"]["decision_is_execution"] is False
    assert result["execution_performed"] is False
    assert result["verification"]["passed"] is True


def test_b19_compares_simulation_risk_reversibility_and_desired_state():
    planning, *_ = _stack()
    results = planning.compare_options({"mode": "current"}, {"mode": "target"}, _options())
    assert len(results) == 2
    assert results[0]["id"] == "safe"
    for item in results:
        assert item["simulation"]["simulation_is_observation"] is False
        assert item["risk"]["risk_is_permission"] is False
        assert 0.0 <= item["comparison_score"] <= 1.0
        assert item["execution_performed"] is False
        assert item["operational_authorization"] is False


def test_b19_default_boundary_denies_execution():
    planning, *_ = _stack()
    result = planning.plan_decision(
        "Planejar teste",
        current_state={"x": 0},
        desired_state={"x": 1},
        options=[{"label": "alterar", "changes": {"x": 1}}],
    )
    boundary = result["execution_boundary"]
    assert boundary["can_act"] is False
    assert set(boundary["missing"]) == {"permission", "capability", "safety_ok"}
    assert boundary["planning_granted_permission"] is False
    assert boundary["execution_performed"] is False


def test_b19_even_eligible_boundary_does_not_execute():
    planning, *_ = _stack()
    result = planning.plan_decision(
        "Preparar ação elegível",
        current_state={"x": 0},
        desired_state={"x": 1},
        options=[{"label": "alterar", "changes": {"x": 1}}],
        permission=True,
        capability=True,
        safety_ok=True,
        authorization_source="explicit-test",
    )
    boundary = result["execution_boundary"]
    assert boundary["can_act"] is True
    assert boundary["execution_performed"] is False
    assert boundary["planning_granted_permission"] is False
    assert result["execution_performed"] is False


def test_b19_plan_uses_existing_planner_steps_and_working_memory():
    planning, _mind, _knowledge, memory, *_ = _stack()
    result = planning.plan_decision(
        "Atualizar software com segurança",
        current_state={"version": 1},
        desired_state={"version": 2},
        options=[{"label": "update", "changes": {"version": 2}, "reversibility": 0.9}],
    )
    assert len(result["plan"]["steps"]) >= 5
    wm = memory.working.get("b19:last_plan")
    assert wm is not None
    assert wm["metadata"]["block"] == "B19"
    assert wm["metadata"]["execution_performed"] is False


def test_b19_record_decision_requires_auditable_reference_and_persists_decision():
    planning, mind, _knowledge, _memory, *_ = _stack()
    artifact = planning.plan_decision(
        "Escolher alternativa",
        current_state={"x": 0},
        desired_state={"x": 1},
        options=[{"label": "A", "changes": {"x": 1}}],
    )
    with pytest.raises(ValueError):
        planning.record_decision(artifact, source="unit-test", reference="")

    stored = planning.record_decision(artifact, source="unit-test", reference="test:b19:decision")
    assert stored["persistent"] is True
    recalled = mind.memory.recall("Decisão B19", kinds=["decision"], limit=10)
    assert any("Escolher alternativa" in item["content"] for item in recalled)


def test_b19_verification_detects_incomplete_artifact():
    planning, *_ = _stack()
    result = planning.verify_plan({"goal": "x", "current_state": {}, "desired_state": {}, "options": [], "plan": {}, "decision": {}, "execution_performed": False})
    assert result["passed"] is False
    assert "options_compared" in result["failed"]
    assert "plan_present" in result["failed"]
    assert "decision_present" in result["failed"]


def test_b19_namespace_graph_and_policy():
    planning, mind, knowledge, *_ = _stack()
    namespace = knowledge.store.get_namespace("B19")
    assert namespace and namespace["logical_capacity"] == 1_000_000_000
    assert planning.graph is mind.graph
    taxonomy = planning.materialize_taxonomy("decision")
    assert taxonomy["branches_materialized"] == 5
    assert taxonomy["parallel_planner_created"] is False
    assert PLANNING_POLICY["planning_is_execution"] is False
    assert PLANNING_POLICY["decision_is_execution"] is False
    assert PLANNING_POLICY["recommendation_is_permission"] is False
    assert PLANNING_POLICY["automatic_execution"] is False


def test_b19_fallback_option_remains_nonexecuting_when_options_missing():
    planning, *_ = _stack()
    result = planning.plan_decision("Coletar contexto", current_state={}, desired_state={})
    assert len(result["options"]) == 1
    assert "coletar" in result["options"][0]["label"].casefold()
    assert result["execution_performed"] is False
    assert result["execution_boundary"]["can_act"] is False


def test_b19_handle_is_explicit_and_nonintrusive():
    planning, *_ = _stack()
    assert "BLOCO 19" in planning.handle("status bloco 19")
    assert "PLAN-B19-0000000001" in planning.handle("PLAN-B19-0000000001")
    assert planning.handle("oi, tudo bem?") is None
