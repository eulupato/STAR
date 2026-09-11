import json
from pathlib import Path

from clients.star_watch_app import (
    PeopleStore,
    SimulatorProviders,
    StarWatchModel,
    WATCH_APP_VERSION,
    WATCH_MODES,
)


def test_watch_version_and_modes_are_stable():
    assert WATCH_APP_VERSION == "0.4.0"
    keys = [mode.key for mode in WATCH_MODES]
    assert keys == [
        "voice",
        "search",
        "health",
        "gps",
        "vision",
        "people",
        "measure",
        "media",
        "weather",
        "settings",
    ]
    assert len(keys) == len(set(keys))


def test_star_ring_rotates_wraps_and_opens_selected_mode():
    model = StarWatchModel()
    assert model.selected_mode.key == "voice"

    model.rotate(1)
    assert model.selected_mode.key == "search"
    assert model.press() == "search"

    assert model.back() == "home"
    model.rotate(-2)
    assert model.selected_mode.key == "settings"


def test_press_inside_mode_returns_home():
    model = StarWatchModel()
    model.active_mode = "measure"
    assert model.press() == "home"


def test_simulated_hardware_is_always_labeled_as_simulated():
    model = StarWatchModel()
    providers = SimulatorProviders(model)

    health = providers.health()
    gps = providers.gps()
    measure = providers.measure()

    assert health["simulated"] is True
    assert gps["simulated"] is True
    assert measure["simulated"] is True
    assert "SIMULAÇÃO" in health["message"]
    assert "SIMULAÇÃO" in gps["message"]
    assert "SIMULAÇÃO" in measure["message"]


def test_hardware_providers_can_be_disabled():
    model = StarWatchModel()
    model.simulation_enabled = False
    providers = SimulatorProviders(model)

    assert providers.health()["available"] is False
    assert providers.gps()["available"] is False
    assert providers.measure()["available"] is False


def test_people_store_is_local_and_round_trips(tmp_path):
    path = tmp_path / "people.json"
    store = PeopleStore(path)

    assert store.list() == []
    item = store.add("Maria", "amiga da escola", "foto.jpg")

    assert item["name"] == "Maria"
    assert store.list() == [
        {
            "name": "Maria",
            "notes": "amiga da escola",
            "image_path": "foto.jpg",
        }
    ]


def test_manifest_declares_watch_first_v04():
    manifest = json.loads(Path("STAR_MANIFEST.json").read_text(encoding="utf-8"))
    watch = manifest["star_watch_app"]
    profile = manifest["device_ecosystem"]["profiles"]["watch"]

    assert watch["version"] == "0.4.0"
    assert watch["product_direction"] == "watch-first"
    assert watch["interaction"]["ring_rotate"] is True
    assert watch["interaction"]["ring_press"] is True
    assert profile["shape"] == "circle"
    assert profile["home_style"] == "plasma-core-ring"
