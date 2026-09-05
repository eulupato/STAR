from pathlib import Path

from core.islands import get_islands, get_subarea, status_label
from gui.world_state import WorldState


def test_star_world_has_single_topology_and_required_islands():
    islands = get_islands()
    assert list(islands) == [
        "casa", "laboratorio", "biblioteca", "estudio_musica", "atelie",
        "jardim", "correio", "cura", "herois", "idiomas",
    ]
    assert "central_criacao" not in islands
    assert "observatorio" not in islands
    assert get_subarea("laboratorio", "central_criacao")["enterable"] is True
    assert set(get_islands()["jardim"]["subareas"]) == {"plantacao", "natureza", "mar", "observatorio"}
    assert set(get_islands()["casa"]["subareas"]) == {"sala", "cozinha", "quarto", "closet"}


def test_cura_contract_is_controlled():
    cura = get_islands()["cura"]
    flow = " > ".join(cura["flow"])
    for expected in ("diagnóstico", "identificação", "proposta", "validação", "aplicação autorizada", "teste"):
        assert expected in flow
    assert "irrestrita" in cura["safety_note"].lower()


def test_status_labels_are_honest():
    assert status_label("available") == "DISPONÍVEL"
    assert status_label("experimental") == "EXPERIMENTAL"
    assert status_label("development") == "EM DESENVOLVIMENTO"


def test_world_state_persists_visual_state_outside_cognitive_memory(tmp_path):
    state = WorldState(tmp_path)
    state.append("tv_favorites", "https://youtu.be/example")
    state.set("cultivation", {"manjericao": "regado"})
    reloaded = WorldState(tmp_path)
    assert "https://youtu.be/example" in reloaded.get("tv_favorites")
    assert reloaded.get("cultivation")["manjericao"] == "regado"
    assert reloaded.path.parent.name == "runtime"


def test_app_contains_all_functional_environment_entrypoints():
    root = Path(__file__).parents[1] / "gui"
    sources = "\n".join(
        (root / name).read_text(encoding="utf-8")
        for name in ("app.py", "menu_hub.py", "world_scene.py", "world_home_garden.py", "world_workspaces.py", "world_systems.py", "shell.py")
    )
    for method in (
        "show_menu", "show_hub", "show_living_room", "show_kitchen", "show_bedroom", "show_closet",
        "show_plantation", "show_nature", "show_sea", "show_observatory", "show_laboratory",
        "show_creation_center", "show_library", "show_music_studio", "show_atelier", "show_cura",
        "show_mail", "show_heroes", "show_languages", "show_chat", "show_settings",
    ):
        assert f"def {method}" in sources
    assert "warmup_stt_async" not in sources
    assert "window.after(60, self._check_response_queue)" in sources
