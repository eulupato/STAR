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


def test_media_controller_is_lazy_and_safe_when_closed():
    media = MediaController()
    state = media.state()
    assert state["opened"] is False
    assert media.fullscreen() is False
    assert media.restore() is False
    assert media.close() is True
