import pytest

from core.foundations import (
    COGNITIVE_CYCLE,
    COGNITIVE_MODEL_DEFINITIONS,
    FOUNDATION_ADDRESSABLE_CONTENTS,
    INVIOLABLE_DISTINCTIONS,
    CognitiveModels,
    FoundationSuite,
    FoundationalContentCatalog,
    OperationalBoundary,
)
from core.star_identity import StarIdentity


def test_block1_has_exact_cycle_models_and_inviolable_distinctions():
    suite = FoundationSuite(identity=StarIdentity())
    stats = suite.stats()

    assert [stage["label"] for stage in COGNITIVE_CYCLE] == [
        "PERCEBER",
        "IDENTIFICAR",
        "COMPREENDER",
        "CONTEXTUALIZAR",
        "RELACIONAR",
        "PREVER",
        "INTERPRETAR",
        "DECIDIR",
        "AGIR",
        "OBSERVAR",
        "APRENDER",
    ]
    assert stats["cycle_stages"] == 11
    assert stats["cognitive_models"] == 5
    assert tuple(COGNITIVE_MODEL_DEFINITIONS) == (
        "world_model",
        "human_model",
        "social_model",
        "self_model",
        "situation_model",
    )
    assert stats["inviolable_distinctions"] == 7
    assert {item["statement"] for item in INVIOLABLE_DISTINCTIONS.values()} == {
        "MODELO ≠ STAR",
        "CORPO ≠ STAR",
        "IA ≠ STAR",
        "PENSAR ≠ AGIR",
        "CURIOSIDADE ≠ AUTORIZAÇÃO",
        "INFERÊNCIA ≠ FATO",
        "AUTONOMIA COGNITIVA ≠ AUTONOMIA OPERACIONAL",
    }
    assert "MODELO ≠ STAR" in suite.principles()


def test_foundational_catalog_is_exactly_1b_and_materialized_on_demand():
    catalog = FoundationalContentCatalog()
    stats = catalog.stats()

    assert FOUNDATION_ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["canonical_nodes"] == 1_000
    assert stats["variants_per_node"] == 1_000_000
    assert stats["addressable_contents"] == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_fact_rows"] == 0

    first = catalog.content_id(0, 0)
    last = catalog.content_id(999, 999_999)
    assert first == "FOUND-0000000001"
    assert last == "FOUND-1000000000"
    assert catalog.get_variant(first)["id"] == first
    assert catalog.get_variant(last)["id"] == last
    assert catalog.get_variant("FOUND-1000000001") is None


def test_inference_stays_separate_from_fact_and_fact_requires_provenance():
    models = CognitiveModels()
    inference = models.record(
        "world_model",
        "inferences",
        "o objeto pode estar em movimento",
        confidence=0.6,
    )
    assert inference["epistemic_class"] == "inferences"

    with pytest.raises(ValueError):
        models.record("world_model", "facts", "o objeto está em movimento")

    fact = models.record(
        "world_model",
        "facts",
        "sensor registrou deslocamento",
        source="sensor:camera-1",
        confidence=0.95,
    )
    assert fact["epistemic_class"] == "facts"
    situation = models.situation()
    assert situation["world"]["inferences"][0]["value"] != situation["world"]["facts"][0]["value"]


def test_cognitive_autonomy_curiosity_and_inference_never_grant_operational_authority():
    boundary = OperationalBoundary()

    denied = boundary.evaluate(
        "abrir arquivo",
        permission=False,
        capability=True,
        safety_ok=True,
        curiosity=True,
        inference_available=True,
        cognitive_autonomy=True,
    )
    assert denied["can_act"] is False
    assert "permission" in denied["missing"]

    allowed = boundary.evaluate(
        "ler arquivo autorizado",
        permission=True,
        capability=True,
        safety_ok=True,
        curiosity=False,
        inference_available=False,
        authorization_source="permission-manager:test",
    )
    assert allowed["can_act"] is True
    assert allowed["authorization_source"] == "permission-manager:test"


def test_foundation_handlers_are_explicit_and_do_not_capture_normal_chat():
    suite = FoundationSuite(identity=StarIdentity())

    status = suite.handle("status bloco 1")
    assert "1000000000" in status
    assert "11 etapas" in status

    principles = suite.handle("princípios invioláveis")
    assert "PENSAR ≠ AGIR" in principles
    assert "INFERÊNCIA ≠ FATO" in principles

    item = suite.handle("FOUND-0000000001")
    assert "FOUND-0000000001" in item
    assert suite.handle("uma conversa normal") is None
