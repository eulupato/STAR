from __future__ import annotations

from core.affective_personality import AffectivePersonality
from core.attention_salience import AttentionSalience
from core.learning_evolution import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    LEARNING_BRANCHES,
    LEARNING_POLICY,
    VARIANTS_PER_NODE,
    LearningEvolution,
)
from core.memory_continuity import MemoryContinuity
from core.metacognition import Metacognition
from core.mind import CognitiveSuite
from core.reasoning_simulation import ReasoningSimulation
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _stack():
    mind=CognitiveSuite(); knowledge=UniversalKnowledgeArchitecture(mind.epistemics,mind.graph)
    memory=MemoryContinuity(knowledge,memory=mind.memory,graph=mind.graph)
    state=StarState(); attention=AttentionSalience(knowledge,memory_continuity=memory,state=state)
    reasoning=ReasoningSimulation(knowledge,reasoning=mind.reasoning,simulation=mind.simulation,verifier=mind.verifier,memory_continuity=memory,attention_salience=attention)
    meta=Metacognition(knowledge,base_engine=mind.metacognition,verifier=mind.verifier,memory_continuity=memory,attention_salience=attention,reasoning_simulation=reasoning)
    personality=AffectivePersonality(knowledge,state=state,memory_continuity=memory)
    learning=LearningEvolution(knowledge,memory_continuity=memory,reasoning_simulation=reasoning,metacognition=meta,affective_personality=personality,self_improvement=mind.self_improvement,attention_salience=attention)
    return learning,mind,knowledge,memory,personality


def test_b21_exact_1b_and_boundaries():
    learning,*_=_stack()
    assert CANONICAL_NODES==500 and VARIANTS_PER_NODE==2_000_000 and ADDRESSABLE_CONTENTS==1_000_000_000
    assert learning.catalog.content_id(0,0)=="LEARN-B21-0000000001"
    assert learning.catalog.content_id(499,1_999_999)=="LEARN-B21-1000000000"
    assert learning.catalog.get_variant("LEARN-B21-1000000001") is None


def test_b21_covers_requested_topics():
    hay=" ".join(b.label+" "+" ".join(b.subtopics) for b in LEARNING_BRANCHES).casefold()
    for topic in ("experiência","generalização","prediction error","revisão","consolidação","adaptação","evolução","desenvolvimento cognitivo"):
        assert topic.casefold() in hay


def test_experience_requires_auditable_reference_and_persists():
    learning,_mind,_knowledge,memory,_personality=_stack()
    result=learning.record_experience("teste real",source="unit",reference="test://1")
    record=memory.memory_record(result["memory_id"])
    assert record["kind"]=="autobiographical"
    assert record["metadata"]["reference"]=="test://1"


def test_prediction_error_preserves_predicted_observed_and_history():
    learning,_mind,_knowledge,memory,_personality=_stack()
    result=learning.prediction_feedback(10,15,source="sensor",reference="obs://1",context="test")
    assert result["prediction_error"]["predicted"]==10
    assert result["prediction_error"]["observed"]==15
    assert result["history_rewritten"] is False
    assert memory.memory_record(result["memory_id"])["kind"]=="error"


def test_generalization_remains_inference_in_working_memory():
    learning,_mind,_knowledge,memory,_personality=_stack()
    result=learning.generalize([1,2,3],scope="local",exceptions=[4],source="unit",reference="test://g")
    assert result["epistemic_kind"]=="inference"
    assert result["canonical_fact"] is False
    assert memory.working.get(result["working_memory_id"]) is not None


def test_revision_preserves_original_and_links_new_version():
    learning,_mind,_knowledge,memory,_personality=_stack()
    old=memory.remember("semantic","versão antiga",source="unit",reference="old://1")
    revised=learning.revise_memory(old["memory_id"],"versão revisada",source="unit",reference="new://1",reason="nova evidência")
    assert revised["original_memory_id"]==old["memory_id"]
    assert revised["original_preserved"] is True
    assert memory.memory_record(old["memory_id"])["content"]=="versão antiga"
    assert memory.memory_record(revised["memory_id"])["content"]=="versão revisada"


def test_consolidation_reuses_b13_and_preserves_sources():
    learning,_mind,_knowledge,memory,_personality=_stack()
    a=memory.remember("episodic","evento a",source="u",reference="a")
    b=memory.remember("episodic","evento b",source="u",reference="b")
    result=learning.consolidate([a["memory_id"],b["memory_id"]],"síntese",source="u",reference="c")
    assert result["source_memories_preserved"] is True
    assert result["canonical_promotion_performed"] is False


def test_personality_adaptation_is_bounded_and_uses_audited_experience():
    learning,_mind,_knowledge,_memory,personality=_stack()
    exp=learning.record_experience("experiência",source="unit",reference="exp://1")
    before=personality.persistent_axis("curiosity")
    result=learning.adapt_personality(exp["memory_id"],{"curiosity":1.0},source="unit",reference="adapt://1",learning_rate=1.0)
    after=personality.persistent_axis("curiosity")
    assert result["learning_rate"]<=0.1
    assert after>=before
    assert result["identity_mutation"] is False
    assert result["code_mutation"] is False


def test_metacognitive_consistency_preserves_contradictions():
    learning,*_=_stack()
    result=learning.assess_consistency("A",sources=["s1","s2"],contradictions=[{"a":1}],confidence=.8)
    assert result["has_contradictions"] is True
    assert result["needs_review"] is True


def test_learning_cycle_does_not_promote_or_modify_code():
    learning,*_=_stack()
    result=learning.learning_cycle("evento",source="unit",reference="cycle://1",predicted=1,observed=2,observations=[1,2],scope="local")
    assert result["automatic_code_modification"] is False
    assert result["canonical_promotion_performed"] is False
    assert result["experience"]["persistent"] is True


def test_self_improvement_evaluates_but_never_patches_code():
    learning,*_=_stack()
    result=learning.evaluate_learning("b21","accuracy",.75,{"sample":1})
    assert result["recorded"] is True
    assert result["automatic_patch"] is False
    denied=learning.code_change_request("patch core")
    assert denied["allowed"] is False and denied["automatic"] is False


def test_namespace_graph_policy_and_handler():
    learning,mind,knowledge,*_=_stack()
    ns=knowledge.store.get_namespace("B21")
    assert ns and ns["logical_capacity"]==1_000_000_000
    assert learning.graph is mind.graph
    mat=learning.materialize_taxonomy("adaptation")
    assert mat["branches_materialized"]==5 and mat["parallel_learning_database"] is False
    assert LEARNING_POLICY["automatic_code_modification"] is False
    assert LEARNING_POLICY["revision_erases_source"] is False
    assert "BLOCO 21" in learning.handle("status bloco 21")
    assert learning.handle("oi") is None
