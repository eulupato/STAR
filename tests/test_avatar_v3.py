from pathlib import Path

from core.avatar import AvatarManager


def test_avatar_uses_real_skin_with_emotion_indicator_when_sprite_is_missing(tmp_path):
    manager = AvatarManager()
    skin = tmp_path / "skin.jpeg"
    skin.write_bytes(b"not-empty")

    path, indicator = manager.resolve_display_asset(
        "happy",
        fallback_path=skin,
    )

    assert path == skin
    assert indicator == "😊"


def test_avatar_neutral_prefers_selected_skin(tmp_path):
    manager = AvatarManager()
    skin = tmp_path / "skin.jpeg"
    skin.write_bytes(b"not-empty")

    path, indicator = manager.resolve_display_asset(
        "neutral",
        fallback_path=skin,
    )

    assert path == skin
    assert indicator == ""


def test_avatar_invalid_emotion_falls_back_safely(tmp_path):
    manager = AvatarManager()
    skin = tmp_path / "skin.jpeg"
    skin.write_bytes(b"not-empty")

    path, indicator = manager.resolve_display_asset(
        "does-not-exist",
        fallback_path=skin,
    )

    assert Path(path) == skin
    assert indicator == ""
