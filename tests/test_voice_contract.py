from pathlib import Path


def test_voice_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "voice" / "manager.py").exists()
    assert (root / "voice" / "chatterbox_worker.py").exists()
    assert (root / "voice" / "audio_input.py").exists()


def test_voice_manager_imports_without_loading_models():
    from voice.manager import VoiceManager, LocalSpeechToText, ChatterboxTTS
    assert VoiceManager is not None
    assert LocalSpeechToText is not None
    assert ChatterboxTTS is not None
