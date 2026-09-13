from pathlib import Path

from core.cognition_runtime import CognitiveRuntime
from core.goal_engine import GoalEngine
from core.guardian import Guardian
from core.m_drive_manager import MDriveManager
from core.mdrives import MDriveRegistry
from core.scientific_graph import ScientificGraphIndexer
from core.scientific_simulation import ScientificSimulationEngine
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


def test_cognitive_runtime_prioritizes_context_and_routes_registered_engine():
    cognition = CognitiveRuntime()
    cognition.observe("user_input", "estudar equações diferenciais", relevance=0.9, user_priority=0.9)
    cognition.observe("ambient", "ruído de fundo", relevance=0.1, user_priority=0.1)
    selected = cognition.context.select("equações", limit=1)
    assert selected[0]["kind"] == "user_input"
    assert cognition.router.choose("math", network_enabled=False)["name"] == "math_sympy"
    assert cognition.router.choose("research", network_enabled=False) is None
    assert cognition.router.choose("research", network_enabled=True)["name"] == "research_hub"


def test_hashing_embeddings_are_deterministic_and_normalized():
    backend = HashingEmbeddingBackend(128)
    a, b = backend.encode(["física quântica e partículas", "física quântica e partículas"])
    assert a == b
    norm = sum(x*x for x in a) ** 0.5
    assert abs(norm - 1.0) < 1e-9


def test_scientific_simulation_validates_physics_and_stability():
    simulation = ScientificSimulationEngine()
    orbit = simulation.two_body_orbit(dt=20.0, duration=600.0)
    assert orbit["model"] == "two-body-newtonian-2d"
    assert orbit["relative_energy_drift"] < 1e-5
    heat = simulation.heat_1d([0, 1, 0], alpha=0.1, dx=1.0, dt=0.1, steps=5)
    assert heat["stability_ratio"] <= 0.5


def test_scientific_graph_exposes_canonical_curriculum_without_inventing_causality():
    graph = ScientificGraphIndexer()
    stats = graph.stats()
    assert stats["themes_available"] == 56
    assert stats["concepts_available"] >= 885
    assert stats["causal_relation_inference"] is False
    assert graph.concept_node_id(1) == "curriculum:concept:0001"


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


def test_mdrive_manager_loads_new_root_and_legacy_without_duplicate_id(tmp_path: Path):
    new_root, old_root = tmp_path / "m_drives", tmp_path / "packs"
    for root, name in ((new_root, "Novo"), (old_root, "Legado")):
        drive = root / "same"; drive.mkdir(parents=True)
        (drive / "manifest.json").write_text('{"id":"same","name":"' + name + '","content_file":"knowledge.json"}', encoding="utf-8")
        (drive / "knowledge.json").write_text('[{"title":"teste","answer":"ok"}]', encoding="utf-8")
    manager = MDriveManager(new_root, legacy_root=old_root, auto_removable=False)
    assert manager.stats()["mdrives"] == 1
    assert manager.list()["same"]["manifest"]["name"] == "Novo"
    assert manager.answer("teste") == "ok"


def test_create_star_exposes_mdrives_and_integrated_evolution():
    from main import create_star
    star = create_star()
    assert star.mdrives is star.packs
    assert star.evolution.guardian.stats()["default_deny_unknown"] is True
    assert star.evolution.cognition.router.choose("math")["name"] == "math_sympy"
