from __future__ import annotations

from core.attention_salience import AttentionSalience
from core.foundations import FoundationSuite
from core.global_workspace import GlobalCognitiveWorkspace
from core.internal_models import IntegratedInternalModels
from core.knowledge_integration import KnowledgeIntegrationEngine
from core.learning_evolution import LearningEvolution
from core.memory_continuity import MemoryContinuity
from core.metacognition import Metacognition
from core.mind import CognitiveSuite
from core.mind_loop import MindLoop
from core.multimodal_perception import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    INTEGRATED_REFERENCES,
    PERCEPTION_POLICY,
    REQUIRED_MODALITIES,
    VARIANTS_PER_NODE,
    MultimodalPerception,
    SensorFusion,
)
from core.planning_decision import PlanningDecision
from core.reasoning_simulation import ReasoningSimulation
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _knowledge_stack():
    mind = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(mind.epistemics, mind.graph)
    return mind, knowledge


def _cognitive_stack():
    mind, knowledge = _knowledge_stack()
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
        max_active=16,
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
    perception = MultimodalPerception(knowledge, max_observations=32, max_fusions=16)
    workspace.attach_perception(perception)
    loop.attach_perception(perception)
    return perception, workspace, loop, mind, knowledge


def test_b25_exact_1b_and_id_boundaries():
    _mind, knowledge = _knowledge_stack()
    perception = MultimodalPerception(knowledge)
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert perception.catalog.content_id(0, 0) == "PER-B25-0000000001"
    assert perception.catalog.content_id(499, 1_999_999) == "PER-B25-1000000000"
    assert perception.catalog.get_variant("PER-B25-1000000001") is None


def test_required_modalities_and_existing_references_are_truthful():
    required = {"vision", "audio", "voice", "screen", "location", "sensors", "motion", "objects", "people", "environment", "time"}
    assert set(REQUIRED_MODALITIES) == required
    assert "modules.vision" in INTEGRATED_REFERENCES["vision"]
    assert "voice.audio_input.AudioRecorder" in INTEGRATED_REFERENCES["audio"]
    assert INTEGRATED_REFERENCES["location"] == ()
    assert INTEGRATED_REFERENCES["sensors"] == ()
    assert PERCEPTION_POLICY["automatic_camera_start"] is False
    assert PERCEPTION_POLICY["automatic_microphone_start"] is False
    assert PERCEPTION_POLICY["automatic_location_access"] is False


def test_no_provider_is_claimed_attached_at_startup():
    _mind, knowledge = _knowledge_stack()
    perception = MultimodalPerception(knowledge)
    status = perception.provider_status()
    assert all(item["provider_attached"] is False for item in status.values())
    assert perception.workspace_available() is False
    assert perception.workspace_observations() == []


def test_ingest_preserves_source_context_and_buffer_is_bounded():
    _mind, knowledge = _knowledge_stack()
    perception = MultimodalPerception(knowledge, max_observations=32)
    first = perception.ingest(
        "vision",
        "door visible",
        source="unit-camera",
        reference="frame://1",
        confidence=0.8,
        features={"door_state": "closed"},
        objects=["door"],
        environment="room",
    )
    assert first["epistemic_kind"] == "observation"
    assert first["canonical_fact"] is False
    assert first["fabricated"] is False
    assert first["source"] == "unit-camera"
    for i in range(60):
        perception.ingest("time", f"tick {i}", source="unit-clock")
    assert perception.snapshot()["observations_buffered"] == 32
    assert len(perception.recent(limit=64)) == 32


def test_sensor_fusion_combines_modalities_and_preserves_conflicts():
    _mind, knowledge = _knowledge_stack()
    perception = MultimodalPerception(knowledge)
    perception.ingest(
        "vision", "door looks closed", source="camera", reference="frame://1",
        confidence=0.9, features={"door_state": "closed"}, objects=["door"], environment="hall",
    )
    perception.ingest(
        "sensors", "contact sensor says open", source="contact-sensor", reference="sensor://door/1",
        confidence=0.95, features={"door_state": "open"}, objects=["door"], events=["state_change"],
    )
    fusion = perception.fuse_recent(limit=8)
    assert fusion["status"] == "fused"
    assert set(fusion["modalities"]) == {"vision", "sensors"}
    assert "door" in fusion["objects"]
    assert fusion["contradictions"]
    assert fusion["contradictions"][0]["feature"] == "door_state"
    assert fusion["epistemic_kind"] == "inference"
    assert fusion["canonical_fact"] is False
    assert fusion["sensor_fusion"] is True
    assert len(fusion["sources"]) == 2


def test_sensor_fusion_input_window_is_bounded():
    fusion = SensorFusion(max_inputs=8)
    observations = [
        {
            "observation_id": f"o{i}", "modality": "sensors", "content": f"reading {i}",
            "confidence": 0.5, "importance": 0.5, "risk": 0.0, "urgency": 0.0,
            "features": {}, "objects": (), "people": (), "events": (), "sounds": (),
            "movements": (), "environment": None, "location": None, "source": "test",
            "reference": None, "observed_at": "t",
        }
        for i in range(100)
    ]
    result = fusion.fuse(observations, fusion_id="f1")
    assert len(result["source_observations"]) == 8
    assert len(result["relations"]) <= 64


def test_provider_collection_requires_permission_and_does_not_poll_silently():
    _mind, knowledge = _knowledge_stack()
    perception = MultimodalPerception(knowledge)

    class Provider:
        calls = 0

        def read_observations(self, limit=8):
            self.calls += 1
            return [{"content": "sound", "source": "test-mic", "sounds": ["beep"], "confidence": 0.8}]

    provider = Provider()
    perception.register_provider("audio", provider)
    denied = perception.collect(["audio"], permission=False)
    assert denied["denied"] is True
    assert denied["providers_called"] is False
    assert provider.calls == 0
    allowed = perception.collect(["audio"], permission=True)
    assert provider.calls == 1
    assert allowed["count"] == 1
    assert perception.recent(modality="audio", limit=1)[0]["sounds"] == ("beep",)


def test_workspace_observations_are_bounded_and_side_effect_free():
    _mind, knowledge = _knowledge_stack()
    perception = MultimodalPerception(knowledge)
    for i in range(20):
        perception.ingest("motion", f"movement {i}", source="motion-test", movements=[f"m{i}"])
    before = perception.snapshot()["observations_buffered"]
    items = perception.workspace_observations(limit=6)
    after = perception.snapshot()["observations_buffered"]
    assert len(items) == 6
    assert before == after
    assert all(item["source"].startswith("perception:") for item in items)


def test_b23_reports_idle_until_real_observation_then_available():
    perception, workspace, *_ = _cognitive_stack()
    assert workspace.component_status()["perception"] == "idle"
    perception.ingest("screen", "settings visible", source="explicit-screen", reference="screen://1")
    assert workspace.component_status()["perception"] == "available"
    result = workspace.activate(perception=perception.workspace_observations(limit=8), limit=8)
    assert any(item.get("source") == "perception" for item in result["active"])


def test_b24_does_not_fake_provider_data_and_consumes_b25_buffer_when_present():
    perception, _workspace, loop, *_ = _cognitive_stack()
    empty = loop.run_cycle("check environment", active_limit=8)
    assert empty["stages"]["perceber"]["status"] == "idle"
    assert empty["stages"]["perceber"]["items"] == []
    assert empty["stages"]["perceber"]["fabricated"] is False
    perception.ingest(
        "environment", "room is quiet", source="explicit-observation", reference="obs://room/1",
        environment="room", sounds=["quiet"], confidence=0.8,
    )
    observed = loop.run_cycle("check environment", active_limit=8)
    assert observed["stages"]["perceber"]["status"] == "provider"
    assert observed["stages"]["perceber"]["items"]
    assert any(item.get("source") == "perception" for item in observed["stages"]["contexto"]["workspace"]["active"])


def test_fused_observation_reaches_workspace_with_objects_people_environment_and_time():
    perception, workspace, _loop, *_ = _cognitive_stack()
    perception.ingest(
        "vision", "person near table", source="vision-test", reference="frame://2",
        people=["person-a"], objects=["table"], environment="room", confidence=0.7,
    )
    perception.ingest(
        "audio", "voice heard", source="audio-test", reference="audio://2",
        people=["person-a"], sounds=["voice"], confidence=0.8,
    )
    fusion = perception.fuse_recent(limit=8)
    assert "person-a" in fusion["people"]
    assert "table" in fusion["objects"]
    assert "room" in fusion["environments"]
    candidates = perception.workspace_observations(limit=4)
    result = workspace.activate(perception=candidates, limit=4)
    assert any((item.get("metadata") or {}).get("sensor_fusion") for item in result["active"] if item.get("source") == "perception")


def test_namespace_shared_graph_taxonomy_policy_and_handler():
    mind, knowledge = _knowledge_stack()
    perception = MultimodalPerception(knowledge)
    namespace = knowledge.store.get_namespace("B25")
    assert namespace and namespace["logical_capacity"] == 1_000_000_000
    assert perception.graph is mind.graph
    taxonomy = perception.materialize_taxonomy("sensor_fusion")
    assert taxonomy["branches_materialized"] == 5
    assert taxonomy["parallel_sensor_store"] is False
    assert PERCEPTION_POLICY["fused_perception_is_canonical_fact"] is False
    assert "BLOCO 25" in perception.handle("status bloco 25")
    assert perception.handle("oi") is None


def test_sensor_fusion_never_promotes_canonical_or_grants_operational_permission():
    _mind, knowledge = _knowledge_stack()
    perception = MultimodalPerception(knowledge)
    perception.ingest("location", "position supplied", source="explicit-location", reference="loc://1", location="zone-a")
    perception.ingest("time", "timestamp supplied", source="system-clock", reference="clock://1")
    fusion = perception.fuse_recent(limit=4)
    assert fusion["canonical_fact"] is False
    assert fusion["operational_authorization"] is False
    assert fusion["fabricated"] is False
    assert set(fusion["modalities"]) == {"location", "time"}
