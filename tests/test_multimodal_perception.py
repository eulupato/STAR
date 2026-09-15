from core.mind import CognitiveSuite
from core.multimodal_perception import (
    ADDRESSABLE_CONTENTS, CANONICAL_NODES, VARIANTS_PER_NODE, MultimodalPerception,
)
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _perception():
    mind = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(mind.epistemics, mind.graph)
    return MultimodalPerception(knowledge), knowledge


def test_b25_exact_1b_and_on_demand_boundaries():
    perception, _ = _perception()
    assert CANONICAL_NODES == 1000
    assert VARIANTS_PER_NODE == 1_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert perception.catalog.content_id(0, 0) == "PERCEPT-B25-0000000001"
    assert perception.catalog.content_id(999, 999_999) == "PERCEPT-B25-1000000000"
    assert perception.catalog.get_variant("PERCEPT-B25-1000000001") is None
    assert perception.stats()["buffered_observations"] == 0


def test_ingest_preserves_observation_provenance_and_never_authorizes():
    perception, _ = _perception()
    item = perception.ingest(
        "vision",
        {"content": "person near door", "confidence": .8, "entities": ["person", "door"]},
        source="unit-camera",
    )
    assert item["modality"] == "vision"
    assert item["source"] == "unit-camera"
    assert item["epistemic_kind"] == "observation"
    assert item["fabricated"] is False
    assert item["operational_authorization"] is False


def test_sensor_fusion_combines_cross_modal_evidence_bounded():
    perception, _ = _perception()
    a = perception.ingest("vision", {"content": "door opened", "event_key": "door-open", "confidence": .8, "entities": ["door"]})
    b = perception.ingest("audio", {"content": "door opening sound", "event_key": "door-open", "confidence": .7, "entities": ["door"]})
    fused = perception.fuse([a, b], limit=4)
    assert len(fused) == 1
    assert fused[0]["cross_modal"] is True
    assert fused[0]["modalities"] == ("audio", "vision")
    assert fused[0]["confidence"] > .8
    assert fused[0]["fabricated"] is False
    assert len(fused[0]["evidence_ids"]) == 2


def test_fusion_preserves_conflict_instead_of_erasing_it():
    perception, _ = _perception()
    a = perception.ingest("vision", {"content": "door open", "event_key": "door-state", "confidence": .8})
    b = perception.ingest("sensor", {"content": "door closed", "event_key": "door-state", "confidence": .9})
    fused = perception.fuse([a, b])
    assert fused[0]["conflict"] is True
    assert "door open" in fused[0]["content"]
    assert "door closed" in fused[0]["content"]


def test_provider_polling_is_bounded_and_fail_closed():
    perception, _ = _perception()

    class Provider:
        def workspace_observations(self, limit=16):
            return [{"content": f"frame {i}", "confidence": .6} for i in range(1000)][:limit]

    perception.attach_provider("vision", Provider())
    items = perception.workspace_observations(limit=8)
    assert len(items) <= 8
    assert perception.stats()["buffered_observations"] <= perception.MAX_BUFFER

    class Broken:
        def workspace_observations(self, limit=16):
            raise RuntimeError("camera offline")

    perception.attach_provider("audio", Broken())
    perception.workspace_observations(limit=8)  # indisponibilidade não fabrica sinal
    assert perception.stats()["fabricates_observations"] is False


def test_unknown_modality_and_empty_observation_are_rejected():
    perception, _ = _perception()
    try:
        perception.ingest("telepathy", {"content": "x"})
        assert False
    except ValueError:
        pass
    try:
        perception.ingest("vision", {})
        assert False
    except ValueError:
        pass
