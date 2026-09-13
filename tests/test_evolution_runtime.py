from pathlib import Path

from core.goal_engine import GoalEngine
from core.guardian import Guardian
from core.mdrives import MDriveRegistry
from core.semantic_rag import HashingEmbeddingBackend
from core.senses import Observation, SensorFusionBuffer


def test_guardian_default_deny_and_safe_read():
    guardian = Guardian()
    assert guardian.authorize("unknown.action", confirmed=True).allowed is False
    assert guardian.authorize("read.files", confirmed=False).allowed is True
    assert guardian.authorize("read.files", remote=True, confirmed=False).reason == "remote_not_allowed"
    assert guardian.authorize("file.write", confirmed=False).reason == "confirmation_required"


def test_guardian_idempotent_claims():
    guardian = Guardian()
    payload = {"x": 123, "test": "evolution-runtime"}
    key = guardian.claim_key("test.idempotent", payload)
    first = guardian.claim_once("test.idempotent", payload, claim_key=key)
    if first["claimed"]:
        guardian.complete_claim(key, {"ok": True})
    second = guardian.claim_once("test.idempotent", payload, claim_key=key)
    assert second["claimed"] is False
    assert second["status"] == "completed"


def test_goal_engine_dependencies_and_checkpoint():
    engine = GoalEngine()
    goal = engine.create("pytest-goal", "validar execução durável", tasks=[
        {"key": "a", "title": "A", "handler": "echo", "payload": {"value": 2}},
        {"key": "b", "title": "B", "handler": "echo", "payload": {"value": 3}, "depends_on": ["a"]},
    ])
    assert [x["task_key"] for x in engine.ready_tasks(goal["goal_id"])] == ["a"]
    task_a = goal["tasks"][0]
    engine.update_task(task_a["task_id"], "completed", result={"value": 2})
    assert [x["task_key"] for x in engine.ready_tasks(goal["goal_id"])] == ["b"]
    checkpoint_id = engine.checkpoint(goal["goal_id"], "pytest")
    assert checkpoint_id > 0
    assert engine.latest_checkpoint(goal["goal_id"])["label"] == "pytest"


def test_hashing_embeddings_are_deterministic_and_normalized():
    backend = HashingEmbeddingBackend(128)
    a, b = backend.encode(["física quântica e partículas", "física quântica e partículas"])
    assert a == b
    norm = sum(x*x for x in a) ** 0.5
    assert abs(norm - 1.0) < 1e-9


def test_senses_contract_does_not_claim_semantic_vision():
    fusion = SensorFusionBuffer()
    fusion.ingest(Observation("temperature", "sim", {"c": 25.0}))
    snapshot = fusion.fuse_snapshot()
    assert "temperature" in snapshot["modalities"]
    assert snapshot["semantic_scene_understanding"] is False


def test_mdrives_prefers_new_name_and_keeps_legacy_compatibility(tmp_path: Path):
    new_root, old_root = tmp_path / "m_drives", tmp_path / "packs"
    (new_root / "physics").mkdir(parents=True); (old_root / "physics").mkdir(parents=True)
    (new_root / "physics" / "manifest.json").write_text('{"id":"physics","name":"Physics M.drive","version":"2"}', encoding="utf-8")
    (old_root / "physics" / "manifest.json").write_text('{"id":"physics","name":"Old Physics","version":"1"}', encoding="utf-8")
    registry = MDriveRegistry(new_root, legacy_root=old_root)
    drives = registry.scan()
    assert len(drives) == 1
    assert drives[0]["name"] == "Physics M.drive"
    assert drives[0]["legacy"] is False
