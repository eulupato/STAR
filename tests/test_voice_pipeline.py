import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice.manager import FastPiperTTS, LocalSpeechToText, VoiceManager


def test_voice_manager_has_local_components():
    manager = VoiceManager()
    assert isinstance(manager.stt, LocalSpeechToText)
    assert isinstance(manager.piper, FastPiperTTS)
    assert manager.stt_configured == manager.stt.configured
    assert isinstance(manager.tts_description, str)
    manager.close()


def test_voice_paths_are_local_and_optional():
    manager = VoiceManager()
    assert manager.piper.model_path.is_relative_to(ROOT)
    assert manager.piper.configured in (True, False)
    manager.close()


def test_no_external_voice_service_is_required():
    # O VoiceManager não importa SDK/API de serviços externos para TTS/STT.
    manager = VoiceManager()
    assert manager.last_tts_engine in {"Piper", "indisponível"}
    manager.close()
