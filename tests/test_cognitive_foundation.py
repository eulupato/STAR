from uuid import uuid4

import pytest

from core.cognitive_catalog import (
    CognitiveContentCatalog,
    FOUNDATION_VIEWS_PER_NODE,
)
from core.mind import CognitiveSuite


def test_foundation_contains_full_world_and_continuous_cognition_matrix():
    catalog = CognitiveContentCatalog()
    stats = catalog.foundation.stats()

    assert stats["world_domains"] == 200
    assert stats["cognitive_domains"] == 85
    assert stats["world_subtopics"] >= 860
    assert stats["cognitive_subtopics"] >= 170
    assert stats["total_nodes"] == (
        stats["world_domains"]
        + stats["world_subtopics"]
        + stats["cognitive_domains"]
        + stats["cognitive_subtopics"]
    )
    assert stats["views_per_node"] == 1_000_000_000
    assert stats["total_addressable_views"] == stats["total_nodes"] * 1_000_000_000


def test_foundation_views_are_real_canonical_content_not_empty_addresses():
    catalog = CognitiveContentCatalog().foundation

    first = catalog.materialize("WORLD-001", 1)
    last = catalog.materialize("COG-085-S014", FOUNDATION_VIEWS_PER_NODE)

    assert first["id"] == "WORLD-001-0000000001"
    assert last["id"] == "COG-085-S014-1000000000"
    assert first["canonical_content"].strip()
    assert last["canonical_content"].strip()
    assert first["derived_view_is_independent_fact"] is False
    assert last["requires_external_provenance_for_new_facts"] is True
    assert len(first["view"]) == 9
    assert len(last["view"]) == 9


def test_scientific_and_epistemic_corrections_are_attached():
    catalog = CognitiveContentCatalog().foundation

    physical = catalog.materialize("WORLD-001-S001", 1)
    causality = catalog.materialize("WORLD-008", 1)
    cfc = catalog.materialize("COG-082", 1)

    physical_rules = " ".join(x["statement"] for x in physical["corrections"])
    causality_rules = " ".join(x["statement"] for x in causality["corrections"])
    cfc_rules = " ".join(x["statement"] for x in cfc["corrections"])

    assert "Massa e peso" in physical_rules
    assert "Correlação não implica causalidade" in causality_rules
    assert "não mede porcentagem de consciência" in cfc_rules


def test_continuous_cognitive_state_uses_five_models_and_never_claims_consciousness():
    suite = CognitiveSuite()
    status = suite.continuous.status()

    assert status["models"] == ["world", "human", "social", "self", "situation"]
    assert status["persistent"] is True
    assert status["consciousness_claim"] is False
    assert suite.continuous.state["identity_core"]["mutable_by_learning"] is False
    assert suite.continuous.state["consciousness_claim"] is False


def test_claims_require_provenance_and_enter_quarantine_by_default():
    suite = CognitiveSuite()

    with pytest.raises(ValueError):
        suite.continuous.integrate_claim(
            "afirmação sem origem",
            source="",
            source_type="",
        )

    marker = uuid4().hex
    claim = suite.continuous.integrate_claim(
        f"claim de teste {marker}",
        source=f"unit:{marker}",
        source_type="test",
        confidence=0.75,
    )
    assert claim["status"] == "QUARANTINED"
    assert claim["confidence"] == 0.75


def test_experience_updates_autobiography_without_becoming_universal_rule():
    suite = CognitiveSuite()
    marker = uuid4().hex

    memory_id = suite.continuous.record_experience(
        f"evento {marker}",
        context="teste",
        result="resultado observado",
        consequence="consequência local",
        learning="hipótese a revisar",
    )
    assert memory_id > 0
    recalled = suite.memory.recall(marker, kinds=("autobiographical",))
    assert recalled
    assert suite.continuous.state["models"]["situation"]["events"][-1]["content"] == f"evento {marker}"


def test_personality_plasticity_is_gradual_and_core_identity_is_not_writable():
    suite = CognitiveSuite()
    before = suite.continuous.state["personality"]["curiosity"]

    with pytest.raises(ValueError):
        suite.continuous.adapt_personality(
            "curiosity", 0.5, evidence_count=1, source="single_event"
        )

    after = suite.continuous.adapt_personality(
        "curiosity", 0.5, evidence_count=3, source="repeated_pattern"
    )
    assert 0.0 <= after <= 1.0
    assert after - before <= 0.0200001
    assert suite.continuous.state["identity_core"]["name"] == "STAR"
