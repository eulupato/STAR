from __future__ import annotations

from core.attention_salience import AttentionSalience
from core.foundations import FoundationSuite
from core.internal_models import IntegratedInternalModels
from core.knowledge_integration import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    INTEGRATION_BRANCHES,
    INTEGRATION_POLICY,
    VARIANTS_PER_NODE,
    KnowledgeIntegrationEngine,
)
from core.learning_evolution import LearningEvolution
from core.memory_continuity import MemoryContinuity
from core.metacognition import Metacognition
from core.mind import CognitiveSuite
from core.reasoning_simulation import ReasoningSimulation
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _stack():
    mind=CognitiveSuite(); knowledge=UniversalKnowledgeArchitecture(mind.epistemics,mind.graph)
    memory=MemoryContinuity(knowledge,memory=mind.memory,graph=mind.graph)
    attention=AttentionSalience(knowledge,memory_continuity=memory,state=StarState())
    foundations=FoundationSuite()
    models=IntegratedInternalModels(knowledge,foundation_models=foundations.models,memory_continuity=memory,attention_salience=attention)
    reasoning=ReasoningSimulation(knowledge,reasoning=mind.reasoning,simulation=mind.simulation,verifier=mind.verifier,memory_continuity=memory,attention_salience=attention,internal_models=models)
    meta=Metacognition(knowledge,base_engine=mind.metacognition,verifier=mind.verifier,memory_continuity=memory,attention_salience=attention,reasoning_simulation=reasoning)
    learning=LearningEvolution(knowledge,memory_continuity=memory,reasoning_simulation=reasoning,metacognition=meta,self_improvement=mind.self_improvement,attention_salience=attention)
    engine=KnowledgeIntegrationEngine(knowledge,internal_models=models,metacognition=meta,learning_evolution=learning,reasoning_simulation=reasoning,attention_salience=attention)
    return engine,mind,knowledge,models,foundations


def test_b22_exact_1b_and_boundaries():
    engine,*_=_stack()
    assert CANONICAL_NODES==500 and VARIANTS_PER_NODE==2_000_000 and ADDRESSABLE_CONTENTS==1_000_000_000
    assert engine.catalog.content_id(0,0)=="KINT-B22-0000000001"
    assert engine.catalog.content_id(499,1_999_999)=="KINT-B22-1000000000"
    assert engine.catalog.get_variant("KINT-B22-1000000001") is None


def test_b22_covers_required_effects_and_models():
    hay=" ".join(b.label+" "+" ".join(b.subtopics) for b in INTEGRATION_BRANCHES).casefold()
    for topic in ("relação","expectativa","previsão","interpretação","contexto","julgamento","world model","human model","social model","self model","situation model"):
        assert topic.casefold() in hay


def test_integration_updates_same_b15_frames_not_parallel_models():
    engine,_mind,_knowledge,models,foundations=_stack()
    before=models.model_view("world_model")["epistemic_counts"]["inferences"]
    result=engine.integrate("céu nublado",source="sensor",reference="obs://cloud",models=["world"],epistemic_kind="inference",confidence=.8)
    after=models.model_view("world_model")["epistemic_counts"]["inferences"]
    assert after==before+1
    assert foundations.models.snapshot("world_model")["inferences"][-1]["value"]["knowledge_ref"]==result["knowledge_ref"]
    assert result["copies_source_datasets"] is False


def test_noncanonical_fact_is_not_silently_recorded_as_fact():
    engine,*_=_stack()
    result=engine.integrate("claim",source="source",reference="r",models=["world"],epistemic_kind="fact",canonical=False)
    assert result["epistemic_kind"]=="inference"
    assert result["model_effects"][0]["frame_kind"]=="inferences"
    assert result["canonical"] is False


def test_canonical_fact_can_enter_world_fact_with_source_but_not_self_identity():
    engine,_mind,_knowledge,models,_foundations=_stack()
    world=engine.integrate("Earth is a planet",source="B03 canonical",reference="kg://earth",models=["world"],epistemic_kind="fact",canonical=True,confidence=.95)
    assert world["model_effects"][0]["frame_kind"]=="facts"
    self_result=engine.integrate("version-like statement",source="B03 canonical",reference="kg://self",models=["self"],epistemic_kind="fact",canonical=True)
    assert self_result["model_effects"][0]["frame_kind"]=="inferences"
    assert self_result["self_identity_mutation"] is False
    assert self_result["permission_granted"] is False
    assert models.model_view("self_model")["epistemic_counts"]["facts"]==0


def test_relations_expectations_predictions_interpretations_and_judgments_integrate():
    engine,_mind,_knowledge,models,_foundations=_stack()
    result=engine.integrate(
        "novo dado",source="unit",reference="k://1",models=["world","situation"],epistemic_kind="observation",
        relations=[{"target":"objeto B","relation":"related_to"}],expectations=["estado provável"],
        predictions=["pode mudar"],interpretations=["leitura contextual"],judgments=["relevante"],
        context={"place":"lab"},confidence=.7,
    )
    assert len(result["relations"])==1
    assert result["expectations"] and result["predictions"] and result["interpretations"] and result["judgments"]
    situation=models.model_view("situation_model")
    assert situation["context"]["integrated_context"]["place"]=="lab"
    assert situation["context"]["temporary"] is True


def test_human_social_knowledge_stays_nondeterministic_inference():
    engine,*_=_stack()
    result=engine.integrate("grupo X costuma variar",source="study",reference="paper://1",models=["human","social"],epistemic_kind="inference",interpretations=["não determina indivíduo"])
    assert all(effect["frame_kind"]=="inferences" for effect in result["model_effects"])
    assert INTEGRATION_POLICY["human_knowledge_determines_individual_traits"] is False


def test_situation_integration_uses_existing_cooperation_and_is_temporary():
    engine,*_=_stack()
    result=engine.integrate_situation("porta aberta",source="sensor",reference="obs://door",active_entities=["porta"],evidence=["frame-1"],goal="monitorar",risk=.2,urgency=.1)
    assert result["temporary"] is True
    assert result["situation"]["copied_source_datasets"] is False
    assert result["operational_authorization"] is False


def test_metacognitive_assessment_is_available_before_integration():
    engine,*_=_stack()
    result=engine.assess_before_integration("claim",source="s",confidence=.3,contradictions=[{"claim":"opposite"}])
    assert result["has_contradictions"] is True
    assert result["needs_review"] is True


def test_original_content_and_inputs_are_not_mutated():
    engine,*_=_stack()
    context={"nested":{"x":1}}; relations=[{"target":"B","relation":"part_of"}]
    context_before={"nested":{"x":1}}; rel_before=[{"target":"B","relation":"part_of"}]
    result=engine.integrate("A",source="s",reference="r",models=["world"],context=context,relations=relations)
    assert context==context_before and relations==rel_before
    assert result["original_knowledge_mutated"] is False


def test_namespace_graph_policy_and_nonintrusive_handler():
    engine,mind,knowledge,*_=_stack()
    ns=knowledge.store.get_namespace("B22")
    assert ns and ns["logical_capacity"]==1_000_000_000
    assert engine.graph is mind.graph
    mat=engine.materialize_taxonomy("world_model")
    assert mat["branches_materialized"]==5 and mat["parallel_models_created"] is False
    assert INTEGRATION_POLICY["storage_alone_is_integration"] is False
    assert INTEGRATION_POLICY["self_knowledge_redefines_identity"] is False
    assert "BLOCO 22" in engine.handle("status bloco 22")
    assert engine.handle("oi") is None
