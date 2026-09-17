from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine

import modules.automation as automation
from core.body_proprioception import BodyActuationExecutor, BodyProprioception
from core.device_sensors import DeviceSensorHub
from core.foundations import OperationalBoundary
from core.mind import CognitiveSuite
from core.multimodal_perception import MultimodalPerception
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _physical_stack():
    mind = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(mind.epistemics, mind.graph)
    perception = MultimodalPerception(knowledge)
    body = BodyProprioception(
        knowledge,
        perception=perception,
        operational_boundary=OperationalBoundary(),
    )
    star = SimpleNamespace(
        multimodal_perception=perception,
        body_proprioception=body,
        proactivity=None,
    )
    return DeviceSensorHub(star), body, perception


def test_sensor_hub_requires_declared_capability_and_never_grants_permission():
    hub, _, _ = _physical_stack()
    payload = {
        "samples": [{
            "kind": "location",
            "latitude": -29.16,
            "longitude": -51.18,
            "accuracy_m": 7.5,
        }]
    }

    denied = hub.ingest("watch-1", payload, capabilities=["microphone"])
    assert denied["accepted"] == 0
    assert "capacidade não declarada" in denied["rejected"][0]["reason"]

    accepted = hub.ingest("watch-1", payload, capabilities=["location"])
    assert accepted["accepted"] == 1
    assert accepted["operational_authorization"] is False
    assert accepted["hardware_attested"] is False
    observation = accepted["observations"][0]
    assert observation["modality"] == "location"
    assert observation["operational_authorization"] is False
    assert observation["attributes"]["endpoint_reported"] is True
    assert observation["attributes"]["hardware_attested"] is False


def test_health_sensor_is_context_not_diagnosis():
    hub, _, _ = _physical_stack()
    result = hub.ingest(
        "watch-health",
        {"kind": "heart_rate", "bpm": 72, "accuracy": "sensor"},
        capabilities=["heart_rate"],
    )
    assert result["accepted"] == 1
    observation = result["observations"][0]
    assert observation["attributes"]["health_data"] is True
    assert observation["attributes"]["diagnosis"] is False


def test_b27_forward_kinematics_two_link_arm():
    _, body, _ = _physical_stack()
    body.configure(
        body_id="test-arm",
        joints=[
            {"name": "shoulder", "type": "revolute", "a": 1.0, "alpha": 0.0, "d": 0.0, "min": -3.1416, "max": 3.1416},
            {"name": "elbow", "type": "revolute", "a": 1.0, "alpha": 0.0, "d": 0.0, "min": -3.1416, "max": 3.1416},
        ],
    )
    pose = body.forward_kinematics([0.0, 0.0])
    assert pose["position"]["x"] == pytest.approx(2.0, abs=1e-8)
    assert pose["position"]["y"] == pytest.approx(0.0, abs=1e-8)
    assert pose["position"]["z"] == pytest.approx(0.0, abs=1e-8)
    assert pose["executed"] is False


def test_b27_inverse_kinematics_converges_without_actuating():
    _, body, _ = _physical_stack()
    body.configure(
        body_id="test-arm",
        joints=[
            {"name": "shoulder", "type": "revolute", "a": 1.0, "min": -3.1416, "max": 3.1416},
            {"name": "elbow", "type": "revolute", "a": 1.0, "min": -3.1416, "max": 3.1416},
        ],
    )
    result = body.inverse_kinematics(
        {"x": 1.0, "y": 1.0, "z": 0.0},
        initial=[0.2, 0.2],
        tolerance=1e-4,
        max_iterations=200,
    )
    assert result["converged"] is True
    assert result["residual"] <= 1e-3
    assert result["executed"] is False


class _FakeBodyEndpoint:
    def __init__(self):
        self.calls = []

    def execute_motion(self, command):
        self.calls.append(command)
        return {"ok": True, "controller": "fake-test"}

    def read_proprioception(self):
        return {"position": [0.0, 0.0, 0.0], "confidence": 1.0}


def test_actuation_executor_is_separate_and_requires_all_boundary_gates():
    _, body, _ = _physical_stack()
    endpoint = _FakeBodyEndpoint()
    body.attach_endpoint(endpoint)
    executor = BodyActuationExecutor(body)

    denied = executor.execute(
        {"joint": "j1", "target": 0.2},
        permission=False,
        capability=True,
        safety_ok=True,
        authorization_source=None,
    )
    assert denied["executed"] is False
    assert denied["reason"] == "boundary_denied"
    assert endpoint.calls == []

    allowed = executor.execute(
        {"joint": "j1", "target": 0.2},
        permission=True,
        capability=True,
        safety_ok=True,
        authorization_source="explicit-test-authorization",
    )
    assert allowed["executed"] is True
    assert len(endpoint.calls) == 1
    assert body.request_motion(
        {"joint": "j1", "target": 0.3},
        permission=True,
        capability=True,
        safety_ok=True,
        authorization_source="test",
    )["body_module_actuates_hardware"] is False


def test_agenda_persists_and_scheduler_emits_reminder_without_actions(monkeypatch):
    test_engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    monkeypatch.setattr(automation, "engine", test_engine)
    agenda = automation.AgendaManager()
    now = datetime.now(timezone.utc)
    item = agenda.add("beber água", now - timedelta(seconds=1))

    # Uma segunda instância vê o mesmo item: persistência pertence ao store SQL,
    # não à memória do objeto AgendaManager.
    agenda_again = automation.AgendaManager()
    assert agenda_again.get(item["id"])["title"] == "beber água"

    scheduler = automation.ProactiveScheduler(agenda_again, poll_seconds=1.0)
    fired = scheduler.tick(now=now)
    assert len(fired) == 1
    assert fired[0]["kind"] == "reminder_due"
    assert fired[0]["notify"] is True
    assert scheduler.stats()["executes_actions"] is False
    assert agenda_again.get(item["id"])["status"] == "completed"


def test_agenda_understands_relative_reminder_without_starting_background_thread(monkeypatch):
    test_engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    monkeypatch.setattr(automation, "engine", test_engine)
    agenda = automation.AgendaManager()
    now = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
    item = agenda.parse_and_add("me lembre em 15 minutos de testar a STAR", now=now)
    assert item is not None
    assert item["title"] == "testar a STAR"
    due = datetime.fromisoformat(item["due_at"])
    assert due == now + timedelta(minutes=15)
