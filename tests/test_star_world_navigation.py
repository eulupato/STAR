from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gui.navigation import NavigationManager, ROUTES
from main import create_star
from core.islands import get_islands


def test_menu_start_flow_targets_hub_and_house():
    nav = NavigationManager()
    assert nav.current == "menu"
    nav.go("hub")
    assert nav.current == "hub"
    nav.go("house")
    assert nav.current == "house"
    assert nav.context == "Casa"


def test_house_rooms_have_expected_context_and_back_route():
    nav = NavigationManager(current="house")
    nav.go("kitchen")
    assert nav.context == "Casa > Cozinha"
    assert nav.back() == "house"

    nav.go("bedroom")
    nav.go("closet")
    assert nav.context == "Casa > Quarto > Closet"
    assert nav.back() == "bedroom"


def test_overlay_returns_to_previous_world_route():
    nav = NavigationManager(current="living_room")
    nav.open_overlay("settings")
    assert nav.current == "settings"
    assert nav.close_overlay() == "living_room"

    nav.open_overlay("chat")
    assert nav.current == "chat"
    assert nav.close_overlay() == "living_room"


def test_all_navigation_routes_have_labels():
    for key, route in ROUTES.items():
        assert route.name == key
        assert route.label


def test_house_and_heroes_are_functional_islands():
    islands = get_islands()
    assert islands["casa"]["status"] == "available"
    assert islands["herois"]["status"] == "partial"
    assert "sala" in islands["casa"]["subareas"]
    assert "cozinha" in islands["casa"]["subareas"]
    assert "quarto" in islands["casa"]["subareas"]
    assert "closet" in islands["casa"]["subareas"]
    assert "album" in islands["casa"]["subareas"]


def test_star_core_accepts_optional_ui_context_without_breaking_process():
    star = create_star()
    star.ui_context = "Casa > Cozinha"
    answer = star.process("quem é seu criador?")
    assert isinstance(answer, str)
    assert answer
    assert star.ui_context == "Casa > Cozinha"


def test_heroes_route_returns_to_hub():
    nav = NavigationManager(current="hub")
    nav.go("heroes")
    assert nav.context == "Heróis"
    assert nav.back() == "hub"


def test_nested_overlays_preserve_world_context():
    nav = NavigationManager(current="bedroom")
    nav.open_overlay("chat")
    assert nav.return_route == "bedroom"

    nav.open_overlay("settings")
    assert nav.return_route == "chat"
    assert nav.close_overlay() == "chat"
    assert nav.return_route == "bedroom"
    assert nav.close_overlay() == "bedroom"
    assert nav.return_route is None


def test_direct_world_navigation_clears_overlay_stack():
    nav = NavigationManager(current="bedroom")
    nav.open_overlay("chat")
    nav.go("hub")
    assert nav.current == "hub"
    assert nav.return_route is None


def test_full_world_back_chain_has_no_cycles():
    nav = NavigationManager()
    nav.go("hub")
    nav.go("house")
    nav.go("bedroom")
    nav.go("closet")
    nav.go("gallery")

    assert nav.back() == "closet"
    assert nav.back() == "bedroom"
    assert nav.back() == "house"
    assert nav.back() == "hub"
    assert nav.back() == "menu"


def test_global_hub_navigation_discards_stale_room_history():
    nav = NavigationManager()
    nav.go("hub")
    nav.go("house")
    nav.go("bedroom")
    nav.go("hub")

    assert nav.current == "hub"
    assert nav.history == ["menu"]
    assert nav.back() == "menu"


def test_back_from_overlay_closes_overlay_instead_of_using_world_history():
    nav = NavigationManager()
    nav.go("hub")
    nav.go("house")
    nav.open_overlay("chat")
    assert nav.back() == "house"
    assert nav.return_route is None
