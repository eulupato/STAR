from pathlib import Path


def test_voice_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "voice" / "manager.py").exists()
    assert (root / "voice" / "chatterbox_worker.py").exists()
    assert (root / "voice" / "audio_input.py").exists()
    assert (root / "voice" / "vad.py").exists()
    assert (root / "voice" / "segmenter.py").exists()


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


def test_vad_runtime_has_no_network_or_downloader():
    root = Path(__file__).resolve().parents[1]
    source = (root / "voice" / "vad.py").read_text(encoding="utf-8").lower()
    assert "urllib" not in source
    assert "requests" not in source
    assert "http://" not in source
    assert "https://" not in source
    assert "download_silero" not in source
