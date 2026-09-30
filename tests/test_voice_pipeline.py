import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice import audio_devices
from voice.manager import (
    ChatterboxOfficialTTS,
    FastPiperTTS,
    LocalSpeechToText,
    VoiceManager,
    prepare_tts_text,
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



def test_tts_text_removes_emojis_without_changing_portuguese():
    text = "Perfeito! ✨⭐ Vamos continuar amanhã. 😊"
    assert prepare_tts_text(text) == "Perfeito! Vamos continuar amanhã."


def test_tts_text_removes_emoji_sequences_and_flags():
    text = "Tudo certo 👩‍💻🇧🇷! Seguimos."
    assert prepare_tts_text(text) == "Tudo certo! Seguimos."


def test_tts_text_keeps_normal_punctuation_and_accents():
    text = "Olá, Lu! Você está bem? Sim: estou ótima."
    assert prepare_tts_text(text) == text


def test_fast_mode_prefers_routable_piper(monkeypatch):
    monkeypatch.delenv("STAR_VOICE_FAST_PREFERENCE", raising=False)
    manager = VoiceManager()
    manager.set_voice_mode("fast")
    assert manager.fast_preference == "piper"
    if manager.piper.configured:
        assert manager.tts_description.startswith("Piper PT-BR")
    manager.close()


class _FakeDefault:
    device = (0, 1)


class _FakeSoundDevice:
    default = _FakeDefault()
    _devices = [
        {"name": "Primary Sound Capture Driver", "hostapi": 1,
         "max_input_channels": 2, "max_output_channels": 0,
         "default_samplerate": 44100.0},
        {"name": "TV HDMI", "hostapi": 0,
         "max_input_channels": 0, "max_output_channels": 2,
         "default_samplerate": 44100.0},
        {"name": "Speakers Realtek", "hostapi": 1,
         "max_input_channels": 0, "max_output_channels": 2,
         "default_samplerate": 44100.0},
        {"name": "Speakers Realtek", "hostapi": 0,
         "max_input_channels": 0, "max_output_channels": 2,
         "default_samplerate": 44100.0},
    ]
    _hostapis = [
        {"name": "MME"},
        {"name": "Windows DirectSound"},
    ]

    @classmethod
    def query_devices(cls, index=None):
        return cls._devices if index is None else cls._devices[index]

    @classmethod
    def query_hostapis(cls):
        return cls._hostapis


def test_audio_output_override_prefers_directsound_duplicate(monkeypatch):
    monkeypatch.setenv("STAR_AUDIO_OUTPUT_DEVICE", "Speakers Realtek")
    selected = audio_devices.resolve_audio_device(
        "output", _FakeSoundDevice
    )
    assert selected == 2
