import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_watch_pc_reuses_core_without_star_world():
    source = (ROOT / "clients" / "star_watch_pc.py").read_text(encoding="utf-8")

    assert "from main import create_star" in source
    assert "DeviceRuntime" in source
    assert "AudioRecorder" in source
    assert "VoiceManager" in source
    assert "allow_actions=False" in source
    assert "from gui." not in source
    assert "world_systems" not in source
    assert "StarApp" not in source


def test_watch_plasma_home_reuses_existing_client_and_stays_visual_only():
    source = (ROOT / "clients" / "star_watch_visual.py").read_text(encoding="utf-8")

    assert "class PlasmaStarWatchPC(StarWatchPC)" in source
    assert "from star_watch_pc import StarWatchPC" in source
    assert "ImageFilter" in source
    assert "_render_plasma_frame" in source
    assert "PLASMA_CACHE_FRAMES" in source
    assert "FRAME_TICK_MS = 16" in source
    assert "_build_plasma_cache_async" in source
    assert "persistent minimal plasma core" in source
    assert "from main import create_star" not in source
    assert "VoiceManager" not in source
    assert "AudioRecorder" not in source
    assert "STAR World" in source


def test_watch_plasma_home_keeps_voice_flow_on_home_and_reveals_star():
    source = (ROOT / "clients" / "star_watch_visual.py").read_text(encoding="utf-8")

    assert "self._voice_from_home = self.screen == \"home\"" in source
    assert "if self._voice_from_home:" in source
    assert "self.screen = \"home\"" in source
    assert "def _interaction_error" in source
    assert "def _voice_output_error" in source
    assert "if self.state in {\"thinking\", \"speaking\"}:" in source
    assert "return 1.0" in source
    assert "logo_animation_started" in source


def test_main_can_build_core_without_importing_gui_at_module_load():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    before_main = source.split("def main():", 1)[0]

    assert "def create_star():" in source
    assert "from gui.app import StarApp" not in before_main
    assert "from gui.app import StarApp" in source.split("def main():", 1)[1]


def test_watch_runtime_declares_visual_identity_and_honest_features():
    manifest = json.loads((ROOT / "STAR_MANIFEST.json").read_text(encoding="utf-8"))
    ecosystem = manifest["device_ecosystem"]
    watch = ecosystem["profiles"]["watch"]
    features = ecosystem["features"]
    theme = ecosystem["theme"]

    assert watch["shape"] == "rounded_square"
    assert watch["energy_frame"] is True
    assert watch["plasma_border"] is True
    assert watch["plasma_core"] is True
    assert watch["home_style"] == "minimal_plasma_core"
    assert watch["home_shows_clock"] is False
    assert watch["home_shows_navigation"] is False
    assert watch["home_status_label"] is True
    assert watch["logo_style"] == "plasma_core_inverted_triangle_star"
    assert watch["logo_animation_ms"] == 720
    assert watch["screens"] == ["home", "talk", "health", "gps", "vision", "settings"]

    assert features["voice_input"] is True
    assert features["camera_transport"] is True
    assert features["vision_analysis"] is False
    assert features["health_transport"] is False
    assert features["location_transport"] is False
    assert features["remote_pc_actions"] is False
    assert features["privileged_actions"] is False

    for key in ("energy_blue", "energy_cyan", "energy_violet", "energy_pink"):
        assert theme[key].startswith("#") and len(theme[key]) == 7


def test_android_watch_keeps_transport_ids_and_connects_visual_state():
    layout_path = (
        ROOT
        / "clients"
        / "star_watch_android"
        / "app"
        / "src"
        / "main"
        / "res"
        / "layout"
        / "activity_main.xml"
    )
    visual_path = (
        ROOT
        / "clients"
        / "star_watch_android"
        / "app"
        / "src"
        / "main"
        / "java"
        / "com"
        / "star"
        / "watch"
        / "StarVisualView.java"
    )
    layout = layout_path.read_text(encoding="utf-8")
    visual = visual_path.read_text(encoding="utf-8")

    for view_id in (
        "serverInput",
        "pairCodeInput",
        "messageInput",
        "statusText",
        "responseText",
        "pairButton",
        "sendButton",
        "voiceButton",
        "cameraButton",
    ):
        assert f"@+id/{view_id}" in layout

    assert "com.star.watch.StarVisualView" in layout
    assert "TOQUE NO NÚCLEO PARA FALAR" in layout
    assert "@android:color/transparent" in layout
    assert "LOGO_ANIMATION_MS = 720L" in visual
    assert "syncStateFromUi" in visual
    assert "R.id.statusText" in visual
    assert "R.id.responseText" in visual
    assert "starPath" in visual
    assert "LinearGradient" in visual


def test_watch_pc_launcher_uses_project_virtualenv_and_plasma_renderer():
    launcher = (ROOT / "INICIAR_STAR_WATCH_PC.bat").read_text(encoding="utf-8")
    assert r".venv\Scripts\python.exe" in launcher
    assert r"clients\star_watch_visual.py" in launcher
