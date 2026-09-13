from pathlib import Path

from core.cure import CureSystem
from core.people import PeopleStore
from core.web_knowledge import WebKnowledgeEngine


class ExplodingSession:
    """Se qualquer chamada HTTP ocorrer, o teste deve falhar imediatamente."""

    def get(self, *args, **kwargs):  # pragma: no cover - só executa em regressão
        raise AssertionError("rede acessada em modo offline")


def test_web_knowledge_never_touches_http_when_offline():
    web = WebKnowledgeEngine(session=ExplodingSession())
    result = web.search("teste offline", network_enabled=False)
    assert result["ok"] is False
    assert result["reason"] == "network_disabled"


def test_star_network_gate_controls_shared_weather_provider():
    from main import create_star

    star = create_star()
    assert star.network_enabled is False
    assert star.weather.enabled is False
    assert "OFFLINE" in star.now_status(include_weather=True)

    star.network_enabled = True
    assert star.weather.enabled is True

    # Sempre devolve o Core ao estado offline para não contaminar outros testes.
    star.network_enabled = False
    assert star.weather.enabled is False


def test_people_store_declares_local_non_biometric_policy():
    people = PeopleStore()
    stats = people.stats()
    assert stats["network_required"] is False
    assert stats["face_recognition"] is False
    assert stats["sensitive_trait_inference"] is False
    assert stats["gps_exif_ingested"] is False
    assert "SHA-256" in stats["image_fingerprint"]


def test_cure_repairs_verified_python_corruption_from_known_good(tmp_path: Path):
    root = tmp_path / "project"
    runtime = tmp_path / "runtime-cure"
    (root / "core").mkdir(parents=True)
    (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (root / "config.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "STAR_MANIFEST.json").write_text('{"name":"STAR"}', encoding="utf-8")
    target = root / "core" / "demo.py"
    target.write_text("def value():\n    return 1\n", encoding="utf-8")

    cure = CureSystem(root=root, runtime_dir=runtime)
    initial = cure.mark_known_good("pytest-known-good")
    assert initial["health"]["healthy"] is True
    assert cure.verify_integrity()["clean"] is True

    target.write_text("def broken(:\n", encoding="utf-8")
    unhealthy = cure.health_check(deep=True)
    assert unhealthy["healthy"] is False
    assert any(item["kind"] == "python_syntax" for item in unhealthy["failures"])

    report = cure.auto_repair()
    assert report.applied is True
    assert report.validated is True
    assert report.tests_passed is True
    assert cure.health_check(deep=True)["healthy"] is True
    assert "return 1" in target.read_text(encoding="utf-8")


def test_cure_does_not_erase_healthy_intentional_drift(tmp_path: Path):
    root = tmp_path / "project"
    runtime = tmp_path / "runtime-cure"
    (root / "core").mkdir(parents=True)
    (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (root / "config.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "STAR_MANIFEST.json").write_text('{"name":"STAR"}', encoding="utf-8")
    target = root / "core" / "demo.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")

    cure = CureSystem(root=root, runtime_dir=runtime)
    cure.mark_known_good("pytest-known-good")
    target.write_text("VALUE = 2\n", encoding="utf-8")

    report = cure.auto_repair()
    assert report.validated is True
    assert report.applied is False
    assert report.tests_passed is True
    assert target.read_text(encoding="utf-8") == "VALUE = 2\n"
