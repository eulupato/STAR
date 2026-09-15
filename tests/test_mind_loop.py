from __future__ import annotations

from copy import deepcopy

from core.attention_salience import AttentionSalience
from core.foundations import FoundationSuite
from core.global_workspace import GlobalCognitiveWorkspace
from core.internal_models import IntegratedInternalModels
from core.knowledge_integration import KnowledgeIntegrationEngine
from core.learning_evolution import LearningEvolution
from core.memory_continuity import MemoryContinuity
from core.metacognition import Metacognition
from core.mind import CognitiveSuite
from core.mind_loop import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    MIND_LOOP_POLICY,
    MIND_LOOP_STAGES,
    VARIANTS_PER_NODE,
    MindLoop,
)
from core.planning_decision import PlanningDecision
from core.reasoning_simulation import ReasoningSimulation
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _stack(max_active=16):
    mind = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(mind.epistemics, mind.graph)
    memory = MemoryContinuity(knowledge, memory=mind.memory, graph=mind.graph)
    attention = AttentionSalience(knowledge, memory_continuity=memory, state=StarState())
    foundations = FoundationSuite()
    models = IntegratedInternalModels(
        knowledge,
        foundation_models=foundations.models,
        memory_continuity=memory,
        attention_salience=attention,
    )
    reasoning = ReasoningSimulation(
        knowledge,
        reasoning=mind.reasoning,
        simulation=mind.simulation,
        verifier=mind.verifier,
        memory_continuity=memory,
        attention_salience=attention,
        internal_models=models,
    )
    planning = PlanningDecision(
        knowledge,
        planner=mind.planner,
        reasoning_simulation=reasoning,
        memory_continuity=memory,
        attention_salience=attention,
        internal_models=models,
        operational_boundary=foundations.boundary,
    )
    meta = Metacognition(
        knowledge,
        base_engine=mind.metacognition,
        verifier=mind.verifier,
        memory_continuity=memory,
        attention_salience=attention,
        reasoning_simulation=reasoning,
        planning_decision=planning,
    )
    learning = LearningEvolution(
        knowledge,
        memory_continuity=memory,
        reasoning_simulation=reasoning,
        metacognition=meta,
        self_improvement=mind.self_improvement,
        attention_salience=attention,
    )
    integration = KnowledgeIntegrationEngine(
        knowledge,
        internal_models=models,
        metacognition=meta,
        learning_evolution=learning,
        reasoning_simulation=reasoning,
        attention_salience=attention,
    )
    workspace = GlobalCognitiveWorkspace(
        knowledge,
        attention_salience=attention,
        memory_continuity=memory,
        planning=planning,
        internal_models=models,
        knowledge_integration=integration,
        max_active=max_active,
    )
    loop = MindLoop(
        knowledge,
        global_workspace=workspace,
        memory_continuity=memory,
        attention_salience=attention,
        internal_models=models,
        reasoning_simulation=reasoning,
        metacognition=meta,
        planning_decision=planning,
        learning_evolution=learning,
        knowledge_integration=integration,
        operational_boundary=foundations.boundary,
    )
    return loop, mind, knowledge, memory, attention, models, reasoning, planning, meta, learning, integration, workspace


def test_b24_exact_1b_and_id_boundaries():
    loop, *_ = _stack()
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert loop.catalog.content_id(0, 0) == "LOOP-B24-0000000001"
    assert loop.catalog.content_id(499, 1_999_999) == "LOOP-B24-1000000000"
    assert loop.catalog.get_variant("LOOP-B24-1000000001") is None


def test_pipeline_has_all_17_required_stages_in_order():
    loop, *_ = _stack()
    result = loop.run_cycle("hello", goal="answer")
    assert result["sequence"] == (
        "PERCEBER", "CONTEXTO", "WORKING MEMORY", "SALIÊNCIA", "MEMÓRIA",
        "CONHECIMENTO", "MODELOS", "INTERPRETAÇÃO", "SIMULAÇÃO",
        "METACOGNIÇÃO", "JULGAMENTO", "DECISÃO", "AÇÃO", "RESULTADO",
        "EXPERIÊNCIA", "APRENDIZADO", "ATUALIZAÇÃO",
    )
    assert list(result["stages"]) == list(result["stage_keys"])


def test_cycle_is_bounded_and_never_loads_full_logical_space():
    loop, *_ = _stack(max_active=12)
    stream = ({"content": f"candidate {i}", "source": "stream", "importance": 0.5} for i in range(10000))
    result = loop.run_cycle("candidate", context_candidates=stream, active_limit=12)
    assert result["active_count"] <= 12
    assert result["active_limit"] == 12
    assert result["bounded_retrieval"] is True
    assert result["loads_full_previous_blocks"] is False
    assert len(result["stages"]["memoria"]["items"]) <= 8
    assert len(result["stages"]["conhecimento"]["items"]) <= 8


def test_perception_is_not_fabricated_without_provider_or_explicit_input():
    loop, *_ = _stack()
    result = loop.run_cycle("context only")
    perception = result["stages"]["perceber"]
    assert perception["status"] == "unavailable"
    assert perception["items"] == []
    assert perception["fabricated"] is False


def test_explicit_perception_enters_workspace_as_observation_candidate():
    loop, *_ = _stack()
    result = loop.run_cycle(
        "what happened",
        perception=[{"content": "door sound", "confidence": 0.8, "importance": 0.9, "entities": ["door"]}],
        active_limit=8,
    )
    assert result["stages"]["perceber"]["status"] == "provided"
    assert any(item.get("source") == "perception" for item in result["stages"]["contexto"]["workspace"]["active"])


def test_models_interpretation_simulation_and_metacognition_are_integrated():
    loop, *_ = _stack()
    current = {"door": "closed"}
    current_copy = deepcopy(current)
    result = loop.run_cycle(
        "open the door?",
        goal="evaluate opening",
        current_state=current,
        desired_state={"door": "open"},
        options=[{"id": "open", "label": "Open", "changes": {"door": "open"}, "utility": 0.8, "reversibility": 0.9}],
    )
    assert result["stages"]["modelos"]["model"] == "SITUATION MODEL"
    assert result["stages"]["interpretacao"]["epistemic_kind"] == "inference"
    assert result["stages"]["simulacao"]["simulation_is_observation"] is False
    assert result["stages"]["metacognicao"]["operational_authorization"] is False
    assert current == current_copy


def test_decision_and_action_never_execute_even_when_boundary_is_eligible():
    loop, *_ = _stack()
    result = loop.run_cycle(
        "evaluate",
        goal="choose safe option",
        current_state={"state": "a"},
        desired_state={"state": "b"},
        options=[{"id": "b", "label": "Go B", "changes": {"state": "b"}, "utility": 0.9, "reversibility": 1.0}],
        permission=True,
        capability=True,
        safety_ok=True,
        authorization_source="unit-test",
    )
    assert result["stages"]["decisao"]["execution_performed"] is False
    assert result["stages"]["acao"]["eligible_for_separate_execution"] is True
    assert result["stages"]["acao"]["execution_performed"] is False
    assert result["execution_performed"] is False


def test_no_result_means_no_experience_learning_or_update_is_invented():
    loop, *_ = _stack()
    result = loop.run_cycle("think about this", goal="understand")
    assert result["stages"]["resultado"]["observed"] is False
    assert result["stages"]["resultado"]["fabricated"] is False
    assert result["stages"]["experiencia"]["recorded"] is False
    assert result["stages"]["aprendizado"]["performed"] is False
    assert result["stages"]["atualizacao"]["performed"] is False


def test_observed_audited_result_becomes_experience_learning_and_situation_update():
    loop, _mind, _knowledge, memory, *_ = _stack()
    result = loop.run_cycle(
        "test outcome",
        goal="learn from outcome",
        observed_result={"outcome": "worked"},
        result_source="unit-test",
        result_reference="test://b24/outcome",
        predicted_value=0.4,
        observed_value=0.8,
        learning_observations=["worked once", "worked twice"],
    )
    experience = result["stages"]["experiencia"]
    assert experience["recorded"] is True
    assert memory.memory_record(experience["memory_id"])["kind"] == "autobiographical"
    assert result["stages"]["aprendizado"]["performed"] is True
    assert result["stages"]["aprendizado"]["code_mutation"] is False
    assert result["stages"]["atualizacao"]["performed"] is True
    assert result["stages"]["atualizacao"]["canonical_promotion_performed"] is False


def test_observed_result_without_audit_reference_is_not_persisted_as_experience():
    loop, *_ = _stack()
    result = loop.run_cycle("outcome", observed_result="something happened")
    assert result["stages"]["resultado"]["observed"] is True
    assert result["stages"]["experiencia"]["recorded"] is False
    assert result["stages"]["experiencia"]["reason"] == "source_and_reference_required"
    assert result["stages"]["atualizacao"]["performed"] is False


def test_namespace_shared_graph_policy_taxonomy_and_handler():
    loop, mind, knowledge, *_ = _stack()
    namespace = knowledge.store.get_namespace("B24")
    assert namespace and namespace["logical_capacity"] == 1_000_000_000
    assert loop.graph is mind.graph
    assert MIND_LOOP_POLICY["loads_full_previous_blocks"] is False
    assert MIND_LOOP_POLICY["action_stage_executes_tools"] is False
    assert MIND_LOOP_POLICY["learning_can_modify_core_code"] is False
    taxonomy = loop.materialize_taxonomy("loop_control")
    assert taxonomy["branches_materialized"] == 5
    assert taxonomy["parallel_loop_store"] is False
    assert "BLOCO 24" in loop.handle("status bloco 24")
    assert loop.handle("oi") is None


def test_attached_perception_provider_is_consumed_only_through_bounded_buffer():
    class Provider:
        def workspace_observations(self, limit=16):
            return [{"content": f"sensor {i}", "importance": 0.7} for i in range(100)][:limit]

    loop, *_ = _stack(max_active=8)
    loop.attach_perception(Provider())
    result = loop.run_cycle("sensor", active_limit=8)
    assert result["stages"]["perceber"]["status"] == "provider"
    assert len(result["stages"]["perceber"]["items"]) <= 16
    assert result["active_count"] <= 8
