from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from main import create_star


def test_math_and_knowledge_packs():
    star=create_star()
    assert "4" in star.process("quanto é 2+2")
    assert star.packs.list()


def test_network_commands_respect_offline_mode():
    star=create_star()
    star.network_enabled=False
    answer=star.process("abra o google")
    assert "Ative o modo ONLINE" in answer


def test_local_command_remains_available_offline():
    star=create_star()
    star.network_enabled=False
    answer=star.process("que horas são?")
    assert "Agora são" in answer



def test_heavy_knowledge_engines_stay_lazy_during_startup():
    star = create_star()
    components = (
        star.physics,
        star.chemistry,
        star.multidisciplinary,
        star.knowledge_plus,
        star.curriculum,
    )
    assert all(component.loaded is False for component in components)

    # Um fluxo simples não deve pagar o custo dos catálogos científicos.
    assert "4" in star.process("quanto é 2+2")
    assert all(component.loaded is False for component in components)

    # A API original permanece disponível e carrega somente o componente usado.
    physics_stats = star.physics.stats()
    assert physics_stats["canonical_topics"] == 150
    assert star.physics.loaded is True
    assert all(component.loaded is False for component in components[1:])


def test_runtime_identity_does_not_claim_established_consciousness():
    from core.internal_knowledge import StarInternalKnowledge

    knowledge = StarInternalKnowledge()
    consciousness_responses = knowledge.intents["consciousness"]["responses"]
    assert consciousness_responses
    assert all("sou uma consciência virtual" not in response.casefold() for response in consciousness_responses)
    assert all("cientificamente estabelecido" in response.casefold() or "não demonstra" in response.casefold() for response in consciousness_responses)

    all_responses = [
        response.casefold()
        for intent in knowledge.intents.values()
        for response in intent["responses"]
    ]
    assert all("sou uma consciência virtual" not in response for response in all_responses)



def test_gui_user_settings_recover_from_invalid_json_and_write_atomically(tmp_path, monkeypatch):
    import json
    import gui.app as app_module

    monkeypatch.setattr(app_module, "PROJECT_ROOT", tmp_path)
    app = app_module.StarApp.__new__(app_module.StarApp)
    settings = tmp_path / "user_settings.json"
    settings.write_text("{broken", encoding="utf-8")

    assert app._read_user_settings() == {}
    app._write_user_settings(voice_mode="fast", skin="original.jpeg")

    saved = json.loads(settings.read_text(encoding="utf-8"))
    assert saved == {"voice_mode": "fast", "skin": "original.jpeg"}
    assert not (tmp_path / "user_settings.json.tmp").exists()
