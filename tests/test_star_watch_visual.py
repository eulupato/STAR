from clients.star_watch_app import StarWatchApp
from clients.star_watch_visual import (
    STATE_THEMES,
    TARGET_FRAME_MS,
    VISUAL_STYLE,
    VISUAL_SYSTEM_VERSION,
    StarWatchVisualApp,
)


def test_visual_shell_reuses_functional_watch_app():
    assert issubclass(StarWatchVisualApp, StarWatchApp)
    assert VISUAL_SYSTEM_VERSION == "1.0.0"
    assert VISUAL_STYLE == "plasma-orbit"


def test_visual_states_cover_real_watch_states():
    assert set(STATE_THEMES) == {
        "idle",
        "listening",
        "thinking",
        "speaking",
        "error",
    }
    assert STATE_THEMES["idle"].label == "PRONTA"
    assert STATE_THEMES["listening"].label == "OUVINDO"
    assert STATE_THEMES["thinking"].label == "PENSANDO"
    assert STATE_THEMES["speaking"].label == "RESPONDENDO"
    assert STATE_THEMES["error"].label == "ATENÇÃO"


def test_thinking_and_speaking_use_star_symbol():
    assert STATE_THEMES["thinking"].icon == "star"
    assert STATE_THEMES["speaking"].icon == "star"
    assert STATE_THEMES["idle"].icon == "triangle"
    assert STATE_THEMES["listening"].icon == "triangle"


def test_visual_animation_targets_about_thirty_fps():
    assert 30 <= TARGET_FRAME_MS <= 35
