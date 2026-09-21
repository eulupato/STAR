import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice.audio_input import VoiceActivityDetector
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



def test_voice_runtime_snapshot_is_observable_without_loading_models():
    manager = VoiceManager()
    snapshot = manager.runtime_snapshot()
    assert snapshot["mode"] in {"official", "fast"}
    assert snapshot["is_speaking"] is False
    assert snapshot["speech_cancellations"] == 0
    assert snapshot["barge_ins"] == 0
    assert "stt_configured" in snapshot
    assert "official_voice_configured" in snapshot
    manager.close()


def test_barge_in_only_cancels_active_speech():
    manager = VoiceManager()
    assert manager.barge_in() is False

    manager._speaking.set()
    assert manager.barge_in() is True
    manager._speaking.clear()

    snapshot = manager.runtime_snapshot()
    assert snapshot["barge_ins"] == 1
    assert snapshot["speech_cancellations"] == 1
    assert snapshot["last_cancel_reason"] == "barge_in"
    manager.close()


def test_adaptive_vad_detects_sustained_voice_and_releases_after_silence():
    import numpy as np

    vad = VoiceActivityDetector(
        trigger_over_floor=2.0,
        start_ms=80,
        silence_ms=120,
        max_ms=5000,
    )

    now = 1.0
    quiet = np.full((160, 1), 0.001, dtype=np.float32)
    loud = np.full((160, 1), 0.20, dtype=np.float32)
    silence = np.zeros((160, 1), dtype=np.float32)

    for _ in range(50):
        now += 0.01
        started, ended, _ = vad._process_block(quiet, now, False)
        assert started is False
        assert ended is None

    saw_start = False
    for _ in range(8):
        now += 0.03
        started, ended, _ = vad._process_block(loud, now, False)
        saw_start = saw_start or started
        assert ended is None

    assert saw_start is True

    completed = None
    for _ in range(30):
        now += 0.05
        _, ended, _ = vad._process_block(silence, now, False)
        if ended is not None:
            completed = ended
            break

    assert completed is not None
    frames, duration_ms = completed
    assert frames
    assert duration_ms >= 120
    assert vad.status()["segments"] == 1


def test_vad_guard_raises_trigger_while_star_is_speaking():
    import numpy as np

    vad = VoiceActivityDetector(trigger_over_floor=2.0, guard_boost=3.0)
    quiet = np.full((160, 1), 0.001, dtype=np.float32)
    now = 1.0

    for _ in range(50):
        now += 0.01
        vad._process_block(quiet, now, False)

    vad._process_block(quiet, now + 0.01, False)
    normal_threshold = vad.status()["threshold"]
    vad._process_block(quiet, now + 0.02, True)
    guarded_threshold = vad.status()["threshold"]

    assert guarded_threshold > normal_threshold
    assert vad.status()["guard"] is True
