from core.media_intents import parse_media_intent
from modules.media_controller import MediaController


def test_media_controller_normalizes_youtube_urls():
    assert MediaController.normalize_youtube_url().startswith("https://www.youtube.com/")
    assert (
        MediaController.normalize_youtube_url("https://youtu.be/abc123")
        == "https://www.youtube.com/watch?v=abc123"
    )
    assert (
        MediaController.normalize_youtube_url("https://example.com/video")
        == "https://www.youtube.com/"
    )
    assert (
        MediaController.normalize_youtube_url(
            "https://www.youtube.com.evil.example/watch?v=abc"
        )
        == "https://www.youtube.com/"
    )


def test_media_controller_is_lazy_and_safe_when_closed():
    media = MediaController()
    state = media.state()
    assert state["opened"] is False
    assert media.fullscreen() is False
    assert media.restore() is False
    assert media.close() is True


def test_media_intent_routes_youtube_to_star_tv():
    assert parse_media_intent("STAR, abrir YouTube na TV")["action"] == "open_youtube"
    assert parse_media_intent("ampliar a TV")["action"] == "fullscreen"
    assert parse_media_intent("pausar a televisão")["action"] == "pause"
    assert parse_media_intent("sair da tela cheia da TV")["action"] == "restore"
    assert parse_media_intent("volume da TV 35")["value"] == 35
    assert parse_media_intent("volume da TV para 42")["value"] == 42
