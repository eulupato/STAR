import json
from pathlib import Path

from clients import star_watch_app as watch_base
# A camada oficial do simulador integra AGORA/IDIOMA no mesmo catálogo de modos.
import clients.star_watch_language  # noqa: F401

PeopleStore = watch_base.PeopleStore
SimulatorProviders = watch_base.SimulatorProviders
StarWatchModel = watch_base.StarWatchModel
WATCH_APP_VERSION = watch_base.WATCH_APP_VERSION


def test_watch_version_and_integrated_modes_are_stable():
    assert WATCH_APP_VERSION == "0.4.0"
    keys = [mode.key for mode in watch_base.WATCH_MODES]
    assert keys == [
        "voice",
        "now",
        "search",
        "health",
        "gps",
        "vision",
        "people",
        "measure",
        "media",
        "weather",
        "language",
        "settings",
    ]
    assert len(keys) == len(set(keys))


def test_star_ring_rotates_wraps_and_opens_selected_mode():
    model = StarWatchModel()
    assert model.selected_mode.key == "voice"

    model.rotate(1)
    assert model.selected_mode.key == "now"
    assert model.press() == "now"

    assert model.back() == "home"
    model.rotate(-2)
    assert model.selected_mode.key == "language"


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


def test_legacy_people_store_remains_only_as_base_compatibility(tmp_path):
    # A camada oficial star_watch_language substitui este store por star.people.
    # O teste preserva apenas o contrato legado da classe base para não quebrar
    # imports externos V0.4 durante a migração.
    path = tmp_path / "people.json"
    store = PeopleStore(path)

    assert store.list() == []
    item = store.add("Maria", "amiga da escola", "foto.jpg")
    assert item["name"] == "Maria"
    assert store.list()[0]["notes"] == "amiga da escola"


def test_manifest_declares_watch_first_v04_and_now_surface():
    manifest = json.loads(Path("STAR_MANIFEST.json").read_text(encoding="utf-8"))
    watch = manifest["star_watch_app"]
    profile = manifest["device_ecosystem"]["profiles"]["watch"]

    assert watch["version"] == "0.4.0"
    assert watch["product_direction"] == "watch-first"
    assert watch["interaction"]["ring_rotate"] is True
    assert watch["interaction"]["ring_press"] is True
    assert watch["interaction"]["swipe_now_page"] is True
    assert "now" in watch["modes"]
    assert "now" in profile["screens"]
    assert profile["shape"] == "circle"
    assert profile["home_style"] == "plasma-core-ring"
