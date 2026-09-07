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


def test_chatterbox_worker_uses_manager_reference_env(monkeypatch, tmp_path):
    from voice.chatterbox_worker import reference_path

    reference = (tmp_path / "star-authorized-reference.wav").resolve()
    monkeypatch.setenv("STAR_VOICE_REFERENCE", str(reference))
    assert reference_path() == reference


def test_chatterbox_worker_rejects_directories_as_reference_contract():
    root = Path(__file__).resolve().parents[1]
    source = (root / "voice" / "chatterbox_worker.py").read_text(encoding="utf-8")

    assert "if not ref.is_file():" in source
    assert "if not ref.exists():" not in source
    assert "Diretórios não são aceitos como referência" in source


def test_chatterbox_worker_has_no_generic_tts_fallback():
    root = Path(__file__).resolve().parents[1]
    source = (root / "voice" / "chatterbox_worker.py").read_text(encoding="utf-8").lower()

    assert "piper" not in source
    assert "pyttsx3" not in source
