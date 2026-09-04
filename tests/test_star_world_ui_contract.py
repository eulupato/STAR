from pathlib import Path

from core.islands import get_islands, get_subarea


def test_star_world_topology_matches_official_structure():
    islands = get_islands()
    assert "casa" in islands
    assert "laboratorio" in islands
    assert "jardim" in islands
    assert "central_criacao" not in islands
    assert "observatorio" not in islands
    assert get_subarea("casa", "cozinha") is not None
    assert get_subarea("casa", "quarto") is not None
    assert get_subarea("casa", "closet") is not None
    assert get_subarea("laboratorio", "central_criacao") is not None
    assert get_subarea("jardim", "observatorio") is not None


def test_cura_keeps_controlled_repair_contract():
    cura = get_islands()["cura"]
    assert cura["flow"] == [
        "diagnóstico",
        "identificação do problema",
        "proposta de correção",
        "validação",
        "aplicação",
        "teste",
    ]
    assert "liberdade irrestrita" in cura["safety_note"]


def test_gui_keeps_menu_hub_chat_contract():
    source = (Path(__file__).resolve().parents[1] / "gui" / "app.py").read_text(encoding="utf-8")
    assert "self.window.after(220, self.show_hub)" in source
    assert "def show_hub" in source
    assert "def show_chat" in source
    assert "def show_settings" in source
    assert "def show_kitchen" in source
    assert "def show_closet" in source
    assert "def show_garden" in source
    assert "def show_observatory" in source
