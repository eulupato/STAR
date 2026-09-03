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



class _FakeStdin:
    def __init__(self):
        self.lines = []

    def write(self, value):
        self.lines.append(value)

    def flush(self):
        return None


class _FakeProcess:
    def __init__(self):
        self.stdin = _FakeStdin()
        self.stdout = None
        self.stderr = None
        self.returncode = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        if self.returncode is not None:
            return self.returncode
        if self.terminated or self.killed:
            self.returncode = 0
            return 0
        import subprocess
        raise subprocess.TimeoutExpired("fake", timeout)

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True


def test_media_close_detaches_process_before_cleanup_finishes():
    media = MediaController()
    process = _FakeProcess()
    media._process = process
    media._state.opened = True
    media._state.ready = True

    assert media.close(wait=False) is True
    state = media.state()

    assert state["opened"] is False
    assert state["ready"] is False
    assert media._process is None
    commands = "".join(process.stdin.lines)
    assert '"command": "hide"' in commands
    assert '"command": "close"' in commands


def test_media_state_exposes_starting_and_ready_flags():
    media = MediaController()
    state = media.state()
    assert state["starting"] is False
    assert state["ready"] is False
