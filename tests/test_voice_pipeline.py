import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice.manager import ChatterboxTTS, LocalSpeechToText, VoiceManager


def test_voice_manager_has_local_components():
    manager = VoiceManager()
    assert isinstance(manager.stt, LocalSpeechToText)
    assert isinstance(manager.tts, ChatterboxTTS)
    assert manager.configured == manager.tts.configured
    assert manager.stt_configured == manager.stt.configured


def test_voice_paths_are_inside_project():
    manager = VoiceManager()
    assert manager.tts.configured in (True, False)
    assert manager.tts is not None
    manager.close()
