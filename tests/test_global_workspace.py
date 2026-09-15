from __future__ import annotations

from core.attention_salience import AttentionSalience
from core.foundations import FoundationSuite
from core.global_workspace import ADDRESSABLE_CONTENTS, CANONICAL_NODES, VARIANTS_PER_NODE, WORKSPACE_POLICY, GlobalCognitiveWorkspace
from core.internal_models import IntegratedInternalModels
from core.memory_continuity import MemoryContinuity
from core.mind import CognitiveSuite
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _stack(max_active=16):
    mind=CognitiveSuite(); knowledge=UniversalKnowledgeArchitecture(mind.epistemics,mind.graph)
    memory=MemoryContinuity(knowledge,memory=mind.memory,graph=mind.graph)
    attention=AttentionSalience(knowledge,memory_continuity=memory,state=StarState())
    foundations=FoundationSuite(); models=IntegratedInternalModels(knowledge,foundation_models=foundations.models,memory_continuity=memory,attention_salience=attention)
    workspace=GlobalCognitiveWorkspace(knowledge,attention_salience=attention,memory_continuity=memory,self_model=None,internal_models=models,max_active=max_active)
    return workspace,mind,knowledge,memory,attention,models


def test_b23_exact_1b_and_boundaries():
    ws,*_=_stack()
    assert CANONICAL_NODES==500 and VARIANTS_PER_NODE==2_000_000 and ADDRESSABLE_CONTENTS==1_000_000_000
    assert ws.catalog.content_id(0,0)=="GWS-B23-0000000001"
    assert ws.catalog.content_id(499,1_999_999)=="GWS-B23-1000000000"
    assert ws.catalog.get_variant("GWS-B23-1000000001") is None


def test_required_components_are_represented():
    ws,*_=_stack(); status=ws.component_status()
    assert set(status)=={"perception","salience","attention","memory","knowledge","language","planning","executive","self","situation"}
    assert status["perception"]=="unavailable"
    assert status["memory"]=="available" and status["attention"]=="available"


def test_workspace_active_window_is_bounded():
    ws,*_=_stack(max_active=12)
    candidates=({"content":f"item {i}","source":"stream","importance":i/1000} for i in range(1000))
    result=ws.activate(candidates=candidates,limit=12)
    assert result["active_count"]<=12
    assert result["max_active"]==12
    assert result["bounded"] is True
    assert result["workspace_is_persistent_memory"] is False


def test_memory_retrieval_is_limited_and_can_be_activated():
    ws,_mind,_knowledge,memory,*_=_stack()
    for i in range(12):memory.remember("semantic",f"alpha memory {i}",source="unit",reference=f"m://{i}")
    retrieved=ws.retrieve("alpha",memory_limit=4,knowledge_limit=2)
    assert len([x for x in retrieved if x["source"]=="memory"])<=4
    result=ws.activate(query="alpha",limit=8)
    assert result["active_count"]<=8


def test_perception_can_be_supplied_without_claiming_provider_availability():
    ws,*_=_stack()
    result=ws.activate(perception=[{"content":"sound event","confidence":.7,"importance":.8}],limit=4)
    assert any(x.get("source")=="perception" for x in result["active"])
    assert result["component_status"]["perception"]=="unavailable"


def test_attach_perception_changes_capability_status_only_when_provider_exists():
    ws,*_=_stack()
    assert ws.component_status()["perception"]=="unavailable"
    ws.attach_perception(object())
    assert ws.component_status()["perception"]=="available"


def test_language_goal_plan_self_situation_are_references_not_execution():
    ws,*_=_stack(max_active=16)
    result=ws.activate(language_input="hello",goal="finish task",plan_artifact={"goal":"finish task","status":"planned"},limit=16)
    sources={x.get("source") for x in result["active"]}
    assert "language" in sources or "planning" in sources or "situation" in sources
    assert result["execution_performed"] is False
    assert result["operational_authorization"] is False


def test_active_index_searches_only_workspace_items():
    ws,*_=_stack()
    ws.activate(candidates=[{"content":"unique zebra context","source":"test","importance":1.0},{"content":"other item","source":"test","importance":.5}],limit=8)
    hits=ws.lookup_active("zebra")
    assert hits and "zebra" in hits[0]["content"]
    assert len(hits)<=8


def test_broadcast_is_bounded_and_does_not_execute():
    ws,*_=_stack();ws.activate(candidates=[{"content":"x","source":"test"}],limit=4)
    b=ws.broadcast()
    assert b["bounded"] is True and b["execution_performed"] is False
    assert len(b["active"])<=ws.max_active


def test_snapshot_and_policy_reject_full_space_loading():
    ws,*_=_stack(); snap=ws.snapshot()
    assert snap["policy"]["loads_full_logical_space"] is False
    assert snap["policy"]["workspace_is_persistent_memory"] is False
    assert WORKSPACE_POLICY["priority_is_permission"] is False


def test_namespace_graph_taxonomy_and_handler():
    ws,mind,knowledge,*_=_stack()
    ns=knowledge.store.get_namespace("B23");assert ns and ns["logical_capacity"]==1_000_000_000
    assert ws.graph is mind.graph
    mat=ws.materialize_taxonomy("workspace_control")
    assert mat["branches_materialized"]==5 and mat["persistent_workspace_created"] is False
    assert "BLOCO 23" in ws.handle("status bloco 23")
    assert ws.handle("oi") is None
