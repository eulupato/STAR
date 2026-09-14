from uuid import uuid4

import pytest

from core.attention_salience import AttentionSalience
from core.foundations import FoundationSuite
from core.internal_models import (
    ADDRESSABLE_PER_MODEL,
    ASPECTS,
    INTERNAL_MODEL_POLICY,
    MODEL_AREAS,
    MODEL_LABELS,
    MODEL_LENSES,
    MODEL_ORDER,
    NODES_PER_MODEL,
    TOTAL_B15_ADDRESSABLE,
    VARIANT_AXES,
    VARIANTS_PER_NODE,
    IntegratedInternalModels,
    InternalModelsCatalog,
)
from core.memory_continuity import MemoryContinuity
from core.mind import CognitiveSuite
from core.self_model import SelfModel
from core.star_identity import StarIdentity
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _stack():
    identity = StarIdentity()
    foundations = FoundationSuite(identity=identity)
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    state = StarState()
    self_model = SelfModel(knowledge, identity=identity, state=state, mind=suite)
    memory = MemoryContinuity(
        knowledge,
        memory=suite.memory,
        graph=suite.graph,
        projects=suite.projects,
        self_model=self_model,
    )
    attention = AttentionSalience(
        knowledge,
        memory_continuity=memory,
        state=state,
        self_model=self_model,
    )
    models = IntegratedInternalModels(
        knowledge,
        foundation_models=foundations.models,
        self_model=self_model,
        memory_continuity=memory,
        attention_salience=attention,
    )
    return models, foundations, knowledge, suite, self_model, memory, attention


def test_b15_has_exactly_five_models_and_1b_each():
    catalog = InternalModelsCatalog()
    stats = catalog.stats()
    assert MODEL_ORDER == (
        "world_model", "human_model", "social_model", "self_model", "situation_model"
    )
    assert all(len(MODEL_AREAS[name]) == 10 for name in MODEL_ORDER)
    assert len(ASPECTS) == 5
    assert len(MODEL_LENSES) == 10
    assert NODES_PER_MODEL == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_PER_MODEL == 1_000_000_000
    assert TOTAL_B15_ADDRESSABLE == 5_000_000_000
    assert stats["total_addressable"] == 5_000_000_000
    assert stats["prepopulated_model_rows"] == 0


def test_b15_variant_axes_multiply_to_two_million():
    sizes = {name: len(values) for name, values in VARIANT_AXES}
    assert sizes == {
        "epistemic_class": 10,
        "temporal_scope": 10,
        "context_scope": 10,
        "relation_mode": 10,
        "confidence": 5,
        "salience": 4,
        "update_mode": 10,
    }
    product = 1
    for value in sizes.values():
        product *= value
    assert product == 2_000_000


def test_each_model_has_independent_1b_address_range():
    catalog = InternalModelsCatalog()
    assert catalog.content_id("world", 0, 0) == "WORLD-B15-0000000001"
    assert catalog.content_id("human", 499, 1_999_999) == "HUMAN-B15-1000000000"
    assert catalog.content_id("social", 0, 0) == "SOCIAL-B15-0000000001"
    assert catalog.content_id("self", 499, 1_999_999) == "SELF-B15-1000000000"
    assert catalog.content_id("situation", 499, 1_999_999) == "SITUATION-B15-1000000000"
    assert catalog.get_variant("WORLD-B15-1000000001") is None


def test_catalog_decodes_model_specific_area_aspect_and_lens():
    item = InternalModelsCatalog().get_variant("WORLD-B15-0000000001")
    assert item["model"] == "world_model"
    assert item["area"] == "physical_environment"
    assert item["aspect"] == "elements"
    assert item["lens"] == "definition"
    assert "não copiar conhecimento" in item["prompt"]


def test_b15_reuses_exact_b1_cognitive_models_object():
    models, foundations, _knowledge, _suite, _self_model, _memory, _attention = _stack()
    assert models.foundation_models is foundations.models
    assert models.foundation_models.names() == MODEL_ORDER
    assert models.stats()["parallel_models_created"] is False


def test_record_delegates_to_b1_frame_instead_of_parallel_storage():
    models, foundations, _knowledge, _suite, _self_model, _memory, _attention = _stack()
    marker = uuid4().hex
    models.record("world", "observations", {"event": marker}, source="unit-test", confidence=0.8)
    snapshot = foundations.models.snapshot("world_model")
    assert snapshot["observations"][-1]["value"]["event"] == marker
    assert snapshot["observations"][-1]["source"] == "unit-test"
    assert snapshot["observations"][-1]["confidence"] == pytest.approx(0.8)


def test_fact_recording_keeps_b1_provenance_rule():
    models, _foundations, _knowledge, _suite, _self_model, _memory, _attention = _stack()
    with pytest.raises(ValueError, match="fonte/proveniência"):
        models.record("human", "facts", "fato sem fonte")
    recorded = models.record("human", "facts", "fato com fonte", source="unit-test")
    assert recorded["epistemic_class"] == "facts"


def test_model_views_reference_existing_blocks_without_copying_datasets():
    models, _foundations, _knowledge, _suite, _self_model, _memory, _attention = _stack()
    world = models.model_view("world")
    human = models.model_view("human")
    social = models.model_view("social")
    self_view = models.model_view("self")
    situation = models.model_view("situation")
    assert {item["block"] for item in world["shared_sources"]} >= {"B04", "B05", "B11"}
    assert {item["block"] for item in human["shared_sources"]} >= {"B06", "B07", "B10", "B13"}
    assert {item["block"] for item in social["shared_sources"]} >= {"B08", "B09", "B10", "B13"}
    assert {item["block"] for item in self_view["shared_sources"]} >= {"B12", "B13", "B14"}
    assert {item["block"] for item in situation["shared_sources"]} >= {"B01", "B12", "B13", "B14"}
    assert all(view["copies_source_knowledge"] is False for view in (world, human, social, self_view, situation))


def test_cooperation_updates_existing_situation_model_with_bounded_context():
    models, foundations, _knowledge, _suite, self_model, memory, attention = _stack()
    self_model.set_objectives(["preservar continuidade"])
    attention.set_active_goal("g", "validar situação integrada", priority=0.9)
    for index in range(12):
        memory.working.add(f"contexto {index}", source="unit-test")
    result = models.cooperate(
        current_input="analise a situação",
        goal="validar B15",
        active_entities=[f"entity-{i}" for i in range(30)],
        evidence=[f"evidence-{i}" for i in range(30)],
        risk=0.4,
        urgency=0.6,
    )
    context = foundations.models.snapshot("situation_model")["context"]
    assert context["goal"] == "validar B15"
    assert len(context["active_entities"]) == 16
    assert len(context["evidence"]) == 16
    assert len(context["recent_memory_refs"]) == 8
    assert context["temporary"] is True
    assert context["operational_authorization"] is False
    assert result["copied_source_datasets"] is False
    assert result["operational_authorization"] is False


def test_situation_model_cooperates_with_all_five_views_as_one_star():
    models, _foundations, _knowledge, _suite, _self_model, _memory, _attention = _stack()
    result = models.cooperate(current_input="agora", goal="integrar modelos")
    assert result["cooperating_models"] == tuple(MODEL_LABELS[name] for name in MODEL_ORDER)
    assert result["shared_data"] is True
    assert result["context"]["source_models"] == (
        "world_model", "human_model", "social_model", "self_model"
    )


def test_materialized_taxonomy_uses_one_shared_graph_and_situation_links_other_views():
    models, _foundations, knowledge, suite, _self_model, _memory, _attention = _stack()
    result = models.materialize_taxonomy()
    assert result["models_materialized"] == 5
    assert result["aspects_materialized"] == 250
    assert result["knowledge_graph"] == "shared"
    assert result["parallel_models_created"] is False
    assert result["copies_source_knowledge"] is False
    assert models.graph is knowledge.graph is suite.graph
    situation_neighbors = suite.graph.neighbors("MODELS-B15-SITUATION_MODEL")
    integrated = {item["label"] for item in situation_neighbors if item["relation"] == "integrates_view"}
    assert integrated >= {"WORLD MODEL", "HUMAN MODEL", "SOCIAL MODEL", "SELF MODEL"}


def test_materialize_single_situation_model_still_creates_reference_nodes_not_copies():
    models, _foundations, _knowledge, suite, _self_model, _memory, _attention = _stack()
    result = models.materialize_taxonomy("situation")
    assert result["models_materialized"] == 1
    assert result["aspects_materialized"] == 50
    neighbors = suite.graph.neighbors("MODELS-B15-SITUATION_MODEL")
    assert sum(item["relation"] == "integrates_view" for item in neighbors) == 4


def test_b15_namespace_has_5b_capacity_while_each_model_is_1b():
    models, _foundations, knowledge, _suite, _self_model, _memory, _attention = _stack()
    namespace = knowledge.store.get_namespace("B15")
    assert namespace["logical_capacity"] == 5_000_000_000
    assert models.stats()["catalog"]["addressable_per_model"] == 1_000_000_000


def test_self_model_namespace_snapshot_is_dynamic_and_sees_b13_b14_b15_after_integration():
    models, _foundations, _knowledge, _suite, self_model, _memory, _attention = _stack()
    namespaces = {item["namespace"] for item in self_model.knowledge_snapshot()["registered_namespaces"]}
    assert {"B13", "B14", "B15"}.issubset(namespaces)
    assert all(item["registered"] is True for item in self_model.knowledge_snapshot()["registered_namespaces"])


def test_policy_preserves_one_star_and_no_operational_authority():
    assert INTERNAL_MODEL_POLICY["parallel_models_created"] is False
    assert INTERNAL_MODEL_POLICY["copies_source_knowledge"] is False
    assert INTERNAL_MODEL_POLICY["shared_knowledge_graph"] is True
    assert INTERNAL_MODEL_POLICY["one_star"] is True
    assert INTERNAL_MODEL_POLICY["model_is_star"] is False
    assert INTERNAL_MODEL_POLICY["self_model_redefines_identity"] is False
    assert INTERNAL_MODEL_POLICY["operational_authorization"] is False


def test_handlers_are_explicit_and_nonintrusive():
    models, _foundations, _knowledge, _suite, _self_model, _memory, _attention = _stack()
    status = models.handle("status bloco 15")
    assert "5 modelos" in status
    assert "5000000000" in status
    variant = models.handle("SELF-B15-0000000001")
    assert "SELF MODEL" in variant
    view = models.handle("visão situation model")
    assert "SITUATION MODEL" in view
    assert models.handle("uma conversa comum sem comando de modelo") is None
