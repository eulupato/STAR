import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice.manager import (
    ChatterboxOfficialTTS,
    FastPiperTTS,
    LocalSpeechToText,
    VoiceManager,
)


def test_voice_manager_has_local_components():
    manager = VoiceManager()
    assert isinstance(manager.stt, LocalSpeechToText)
    assert isinstance(manager.official, ChatterboxOfficialTTS)
    assert isinstance(manager.piper, FastPiperTTS)
    assert manager.stt_configured == manager.stt.configured
    assert isinstance(manager.tts_description, str)
    assert manager.mode in {"official", "fast"}
    manager.close()


def test_voice_paths_are_local_and_optional():
    manager = VoiceManager()
    assert manager.piper.model_path.is_relative_to(ROOT)
    assert manager.official.worker_path.is_relative_to(ROOT)
    assert manager.piper.configured in (True, False)
    assert manager.official.configured in (True, False)
    manager.close()


def test_default_mode_prefers_official_voice():
    manager = VoiceManager()
    assert manager.mode == "official"
    assert manager.fallback_on_error is False
    manager.close()


def test_official_mode_does_not_silently_select_piper():
    manager = VoiceManager()
    if not manager.official.configured:
        assert "INDISPONÍVEL" in manager.tts_description
        assert "Piper" not in manager.tts_description
    manager.close()


def test_missing_components_are_explainable():
    engine = ChatterboxOfficialTTS()
    assert isinstance(engine.missing_components, list)
    assert isinstance(engine.status_message, str)


def test_no_external_voice_service_is_required():
    manager = VoiceManager()
    assert manager.last_tts_engine == "não executado"
    manager.close()
