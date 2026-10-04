from datetime import datetime
import json
from zoneinfo import ZoneInfo

import pytest

from core.world_state import WorldStateService


def test_world_state_defaults_to_shared_cosmic_scenario(tmp_path):
    service = WorldStateService(tmp_path / "user_settings.json")
    snap = service.snapshot(datetime(2026, 10, 4, 12, 0, tzinfo=ZoneInfo("UTC")))
    assert snap["scenario"] == "cosmic_crystal"
    assert snap["day_phase"] == "day"
    assert snap["timezone"] == "local"


@pytest.mark.parametrize(
    ("hour", "phase"),
    [(6, "dawn"), (9, "day"), (18, "sunset"), (23, "night")],
)
def test_world_state_day_phase(hour, phase, tmp_path):
    path = tmp_path / "user_settings.json"
    path.write_text(json.dumps({"timezone": "UTC"}), encoding="utf-8")
    service = WorldStateService(path)
    snap = service.snapshot(datetime(2026, 10, 4, hour, 0, tzinfo=ZoneInfo("UTC")))
    assert snap["day_phase"] == phase


def test_world_state_timezone_persists_without_overwriting_other_preferences(tmp_path):
    path = tmp_path / "user_settings.json"
    path.write_text(json.dumps({"skin": "casual.jpg", "voice_mode": "fast"}), encoding="utf-8")
    service = WorldStateService(path)

    snap = service.set_timezone("America/Sao_Paulo")

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["timezone"] == "America/Sao_Paulo"
    assert saved["skin"] == "casual.jpg"
    assert saved["voice_mode"] == "fast"
    assert snap["timezone"] == "America/Sao_Paulo"


def test_world_state_rejects_invalid_timezone(tmp_path):
    service = WorldStateService(tmp_path / "user_settings.json")
    with pytest.raises(ValueError):
        service.set_timezone("STAR/Nowhere")


def test_world_state_migrates_legacy_skin_and_persists_3d_skin(tmp_path):
    path = tmp_path / "user_settings.json"
    path.write_text(
        json.dumps({"skin": "legofshopping.jpeg", "voice_mode": "official"}),
        encoding="utf-8",
    )
    service = WorldStateService(path)

    assert service.snapshot()["skin"] == "rock_simple"
    snap = service.set_skin("rich_red")

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["skin"] == "legofshopping.jpeg"
    assert saved["world_skin"] == "rich_red"
    assert saved["voice_mode"] == "official"
    assert snap["skin"] == "rich_red"


def test_world_state_rejects_unknown_3d_skin(tmp_path):
    service = WorldStateService(tmp_path / "user_settings.json")
    with pytest.raises(ValueError):
        service.set_skin("invented_skin")
