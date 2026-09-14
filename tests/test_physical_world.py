from uuid import uuid4

import pytest

from core.mind import CognitiveSuite
from core.physical_world import (
    MATRIX_AXES,
    PHYSICAL_ADDRESSABLE_CONTENTS,
    PHYSICAL_CANONICAL_NODES,
    PHYSICAL_SUBTHEMES,
    PHYSICAL_TOPICS,
    PHYSICAL_VARIANTS_PER_NODE,
    PhysicalWorldCatalog,
    PhysicalWorldModel,
)
from core.star_core import StarCore
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _model():
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    return PhysicalWorldModel(knowledge), knowledge, suite


def _canonical_fact(suite: CognitiveSuite, marker: str, text: str | None = None):
    source_id = suite.epistemics.register_source(
        f"unit://physical/{marker}",
        source_type="test",
        title=f"Fonte física {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        text or f"Conhecimento físico canônico validado para {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://physical-claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência física independente {marker}",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
        reliability=1.0,
    )
    suite.epistemics.transition(
        record["record_id"],
        "VERIFIED",
        reason="evidência física rastreável suficiente para teste",
        actor="unit-test",
    )
    return suite.epistemics.transition(
        record["record_id"],
        "CANONICAL",
        reason="claim físico apto a conhecimento canônico",
        actor="unit-test",
    )


def test_block4_catalog_is_exactly_1b_and_distributed_over_topics_subthemes_and_matrix():
    catalog = PhysicalWorldCatalog()
    stats = catalog.stats()

    assert len(PHYSICAL_TOPICS) == 50
    assert len(PHYSICAL_SUBTHEMES) == 10
    assert PHYSICAL_CANONICAL_NODES == 500
    assert PHYSICAL_VARIANTS_PER_NODE == 2_000_000
    assert PHYSICAL_ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["addressable_contents"] == 1_000_000_000
    assert stats["materialization"] == "on-demand"

    product = 1
    for _name, values in MATRIX_AXES:
        product *= len(values)
    assert product == 2_000_000

    first = catalog.content_id(0, 0)
    last = catalog.content_id(499, 1_999_999)
    assert first == "PHY-B04-0000000001"
    assert last == "PHY-B04-1000000000"
    assert catalog.get_variant(first)["topic"] == "matter"
    assert catalog.get_variant(last)["topic"] == "risk"
    assert catalog.get_variant("PHY-B04-1000000001") is None

    variant = catalog.get_variant("PHY-B04-0000000001")
    assert {name.lower() for name, _values in MATRIX_AXES}.issubset(variant)


def test_block4_contains_every_requested_physical_foundation_theme():
    keys = {key for key, _label in PHYSICAL_TOPICS}
    required = {
        "matter", "objects", "surfaces", "space", "volume", "mass", "weight", "density",
        "shape", "size", "distance", "position", "direction", "orientation", "motion",
        "velocity", "acceleration", "force", "equilibrium", "gravity", "impact", "collision",
        "friction", "pressure", "temperature", "heat", "cold", "sound", "light", "shadow",
        "reflection", "electricity", "magnetism", "liquids", "gases", "solids",
        "object_permanence", "affordances", "materials", "time", "causality", "prediction",
    }
    assert required <= keys


def test_physical_world_registers_b04_on_same_universal_architecture():
    model, knowledge, _suite = _model()
    namespace = knowledge.store.get_namespace("B04")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert model.knowledge is knowledge
    assert model.stats()["knowledge_source"] == "BLOCO 3 universal knowledge"
    assert model.stats()["epistemic_source"] == "BLOCO 2"


def test_object_permanence_preserves_occluded_objects_without_inventing_new_state():
    model, _knowledge, _suite = _model()
    marker = uuid4().hex
    observed = model.observe_object(
        marker,
        label="copo",
        material="glass",
        properties=["transparent", "container"],
        state="rest",
        environment="table",
        position={"x": 1.0, "y": 2.0, "z": 0.8},
    )
    assert observed["existence_status"] == "present_observed"
    assert observed["state_confidence"] == 1.0

    hidden = model.mark_unobserved(marker, reason="occluded by another object")
    assert hidden["existence_status"] == "present_inferred"
    assert hidden["visibility"] == "unobserved"
    assert hidden["position"] == observed["position"]
    assert hidden["state_confidence"] < 1.0

    with pytest.raises(ValueError, match="evidência"):
        model.remove_object(marker, evidence="")
    removed = model.remove_object(marker, evidence="sensor confirmou retirada da cena")
    assert removed["existence_status"] == "removed_or_transformed"


def test_affordances_are_inferences_and_physical_predictions_are_bounded():
    model, _knowledge, _suite = _model()
    affordances = model.infer_affordances(["handle", "small", "reflective"])
    assert {"grasp", "carry", "reflect_light"} <= set(affordances["affordances"])
    assert affordances["epistemic_kind"] == "inference"

    collision = model.predict_interaction(
        object_label="copo de vidro",
        material="glass",
        properties=["brittle", "fragile"],
        state="moving",
        environment="indoor floor",
        action="drop impact",
    )
    assert collision["epistemic_kind"] == "inference"
    assert collision["operational_authorization"] is False
    assert collision["requires_measurement_for_quantitative_prediction"] is True
    assert any("fratura" in item for item in collision["consequences"])
    assert collision["risk"] in {"moderate", "high", "unknown_requires_measurement"}

    electrical = model.predict_interaction(
        object_label="condutor",
        material="metal",
        properties=["conductive"],
        state="rest",
        environment="wet area",
        action="energize electric voltage",
    )
    assert electrical["risk"] == "high"
    assert electrical["operational_authorization"] is False


def test_block4_reuses_existing_scientific_physics_catalog_instead_of_duplicating_it():
    model, _knowledge, _suite = _model()
    reference = model.physics_reference("segunda lei de newton")
    assert reference is not None
    assert reference["topic_id"] == "newton_second"
    assert reference["formula"]
    assert reference["source"]
    assert reference["reuse"] == "core.physics_knowledge_150k"


def test_physical_canonical_knowledge_uses_block2_gate_and_block3_storage():
    model, knowledge, suite = _model()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(
        f"unit://physical-discovered/{marker}",
        source_type="test",
        reliability=1.0,
    )
    discovered = suite.epistemics.discover(
        f"Claim físico ainda descoberto {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://physical-discovered-claim/{marker}",
        source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        model.promote_canonical_physical(
            discovered["record_id"],
            f"Massa física {marker}",
            topic="mass",
        )

    canonical = _canonical_fact(suite, marker)
    item = model.promote_canonical_physical(
        canonical["record_id"],
        f"Massa física {marker}",
        topic="mass",
        aliases=[f"massa-{marker}"],
        properties={"quantity": "mass", "unit": "kg"},
        subtopics=["measurement"],
        contexts=["physical_world"],
        summary="Grandeza física materializada com proveniência epistêmica.",
    )
    assert item["namespace"] == "B04"
    assert item["canonical_claim_id"] == canonical["record_id"]
    categories = {(f["facet_type"], f["facet_value"]) for f in item["facets"]}
    assert ("category", "physical_world") in categories
    assert ("category", "mass") in categories

    traced = knowledge.trace(item["knowledge_id"])
    assert traced["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"
    assert traced["canonical_claim"]["evidence"]


def test_block4_handlers_and_star_core_integration_are_explicit_and_non_intrusive():
    model, _knowledge, _suite = _model()
    assert "BLOCO 4" in model.handle("status bloco 4")
    assert "PHY-B04-0000000001" in model.handle("PHY-B04-0000000001")
    assert model.handle("uma conversa cotidiana sem comando físico") is None

    class Router:
        def route(self, request):
            return {"response_type": "local"}

    class Executive:
        def execute(self, request, route):
            return "fallback"

    class State:
        def get_state(self):
            return {}

    core = StarCore(Router(), Executive(), State())
    assert core.mind.physical_world is core.physical_world
    assert core.physical_world.knowledge is core.knowledge
    response = core._process_portuguese("status bloco 4")
    assert "BLOCO 4" in response
    assert core.last_intent == "physical_world"
