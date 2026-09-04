from pathlib import Path

from core.islands import get_islands, get_subarea


ROOT = Path(__file__).resolve().parents[1]
GUI_SOURCE = (ROOT / "gui" / "app.py").read_text(encoding="utf-8")
THEME_SOURCE = (ROOT / "gui" / "theme.py").read_text(encoding="utf-8")


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
    assert "self.window.after(220, self.show_hub)" in GUI_SOURCE
    assert "def show_hub" in GUI_SOURCE
    assert "def show_chat" in GUI_SOURCE
    assert "def show_settings" in GUI_SOURCE
    assert "def show_kitchen" in GUI_SOURCE
    assert "def show_closet" in GUI_SOURCE
    assert "def show_garden" in GUI_SOURCE
    assert "def show_observatory" in GUI_SOURCE


def test_hover_does_not_redraw_whole_canvas_recursively():
    """Regressão: Enter/Leave não pode apagar/recriar o item sob o cursor."""
    menu_hover = GUI_SOURCE.split("def _menu_hover", 1)[1].split("def _menu_leave", 1)[0]
    menu_leave = GUI_SOURCE.split("def _menu_leave", 1)[1].split("def _menu_click", 1)[0]
    hub_hover = GUI_SOURCE.split("def _hub_hover", 1)[1].split("def _hub_leave", 1)[0]
    hub_leave = GUI_SOURCE.split("def _hub_leave", 1)[1].split("@staticmethod", 1)[0]
    assert "_render_menu(" not in menu_hover
    assert "_render_menu(" not in menu_leave
    assert "_render_hub(" not in hub_hover
    assert "_render_hub(" not in hub_leave


def test_rendering_is_debounced_and_stipple_heavy_gradient_removed():
    assert "def _schedule_render" in GUI_SOURCE
    assert "canvas.bind(\"<Configure>\", lambda _e: self._schedule_render" in GUI_SOURCE
    assert "stipple=" not in THEME_SOURCE
