from pathlib import Path


def test_voice_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "voice" / "manager.py").exists()
    assert (root / "voice" / "chatterbox_worker.py").exists()
    assert (root / "voice" / "audio_input.py").exists()


def test_voice_manager_imports_without_loading_models():
    from voice.manager import VoiceManager, LocalSpeechToText, ChatterboxOfficialTTS
    assert VoiceManager is not None
    assert LocalSpeechToText is not None
    assert ChatterboxOfficialTTS is not None


def test_launcher_does_not_require_fixed_reference_filename():
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "INICIAR_STAR.bat").read_text(encoding="utf-8")
    assert "if not exist \"voice\\reference\\star_reference.mp3\"" not in launcher.lower()


def test_local_voice_test_uses_python_diagnostic_as_source_of_truth():
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "TESTAR_VOZ_LOCAL.bat").read_text(encoding="utf-8")
    assert "-m voice.diagnostics" in launcher


def test_launcher_allows_degraded_voice_startup():
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "INICIAR_STAR.bat").read_text(encoding="utf-8")
    assert 'import PIL, sqlalchemy, numpy' in launcher
    assert "A STAR iniciara sem voz completa" in launcher
    assert 'import PIL, sounddevice, soundfile, faster_whisper' not in launcher
