import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice.audio_input import ContinuousAudioInput
from voice.segmenter import SpeechEvent, SpeechSegmenter
from voice.vad import SileroVAD, VADModelNotFoundError, default_model_path


def _chunk(value: float = 0.0) -> np.ndarray:
    return np.full(512, value, dtype=np.float32)


def _segmenter_config(**overrides):
    config = {
        "sample_rate": 16000,
        "chunk_samples": 512,
        "threshold": 0.5,
        "neg_threshold_offset": 0.15,
        "min_speech_ms": 64,
        "min_silence_ms": 96,
        "pre_roll_ms": 64,
        "post_roll_ms": 32,
        "max_segment_duration_ms": 5000,
        "input_queue_seconds": 2.0,
    }
    config.update(overrides)
    return config


def test_missing_model_is_explicit_and_does_not_download(tmp_path):
    vad = SileroVAD(tmp_path / "missing.onnx")
    with pytest.raises(VADModelNotFoundError, match="voice.install_models"):
        vad.load()
    assert vad.ready is False


def test_vad_runtime_source_has_no_network_capability():
    source = (ROOT / "voice" / "vad.py").read_text(encoding="utf-8").lower()
    assert "urllib" not in source
    assert "requests" not in source
    assert "http://" not in source
    assert "https://" not in source


def test_default_model_path_is_inside_star_voice_models():
    path = default_model_path()
    assert path.is_relative_to(ROOT)
    assert path.as_posix().endswith("voice/models/vad/silero_vad.onnx")


def test_silero_onnx_contract_uses_context_state_and_sample_rate(tmp_path, monkeypatch):
    model = tmp_path / "silero_vad.onnx"
    model.write_bytes(b"fake")

    class FakeSession:
        def __init__(self):
            self.calls = []

        def get_inputs(self):
            return [SimpleNamespace(name="input"), SimpleNamespace(name="state"), SimpleNamespace(name="sr")]

        def run(self, _outputs, inputs):
            self.calls.append({key: np.array(value, copy=True) for key, value in inputs.items()})
            probability = np.array([[0.8]], dtype=np.float32)
            state = np.asarray(inputs["state"], dtype=np.float32) + 1.0
            return [probability, state]

    session = FakeSession()
    vad = SileroVAD(model)
    monkeypatch.setattr(vad, "_create_session", lambda: session)

    assert vad.process_chunk(_chunk(0.1)) == pytest.approx(0.8)
    assert vad.process_chunk(_chunk(0.2)) == pytest.approx(0.8)

    first, second = session.calls
    assert first["input"].shape == (1, 576)
    assert first["state"].shape == (2, 1, 128)
    assert first["sr"].shape == ()
    assert int(first["sr"]) == 16000
    assert np.all(first["input"][:, :64] == 0.0)
    assert np.all(second["state"] == 1.0)
    assert np.allclose(second["input"][:, :64], 0.1)


def test_silero_reset_reuses_loaded_session(tmp_path, monkeypatch):
    model = tmp_path / "silero_vad.onnx"
    model.write_bytes(b"fake")

    class FakeSession:
        def get_inputs(self):
            return [SimpleNamespace(name="input"), SimpleNamespace(name="state"), SimpleNamespace(name="sr")]

        def run(self, _outputs, inputs):
            return [np.array([[0.4]], dtype=np.float32), np.ones((2, 1, 128), dtype=np.float32)]

    session = FakeSession()
    vad = SileroVAD(model)
    monkeypatch.setattr(vad, "_create_session", lambda: session)
    vad.process_chunk(_chunk())
    vad.reset()
    assert vad.ready is True
    assert vad.last_probability == 0.0
    assert vad._session is session
    assert np.all(vad._state == 0.0)


def test_segmenter_preserves_pre_roll_and_only_small_post_roll():
    segmenter = SpeechSegmenter(_segmenter_config())
    probabilities = [0.0, 0.0, 0.9, 0.9, 0.9, 0.1, 0.1, 0.1]
    result = None
    for probability in probabilities:
        update = segmenter.feed(_chunk(probability), probability)
        if update.segment is not None:
            result = update.segment

    assert result is not None
    # 2 pre-roll + 3 fala + 1 post-roll = 6 chunks de 32 ms.
    assert result.audio.size == 6 * 512
    assert result.duration_ms == pytest.approx(192.0)
    assert result.start_ms == pytest.approx(0.0)


def test_short_noise_is_dropped():
    segmenter = SpeechSegmenter(_segmenter_config(min_speech_ms=64))
    events = []
    for probability in [0.9, 0.1, 0.1, 0.1]:
        events.append(segmenter.feed(_chunk(probability), probability))
    assert events[-1].event == SpeechEvent.SEGMENT_DROPPED
    assert events[-1].segment is None


def test_short_natural_pause_does_not_split_utterance():
    segmenter = SpeechSegmenter(_segmenter_config(min_silence_ms=128, post_roll_ms=32))
    segments = []
    probabilities = [0.9, 0.9, 0.1, 0.1, 0.1, 0.9, 0.9, 0.1, 0.1, 0.1, 0.1]
    for probability in probabilities:
        update = segmenter.feed(_chunk(probability), probability)
        if update.segment is not None:
            segments.append(update.segment)
    assert len(segments) == 1


def test_two_utterances_create_two_segments():
    segmenter = SpeechSegmenter(_segmenter_config())
    segments = []
    probabilities = [
        0.0, 0.9, 0.9, 0.9, 0.1, 0.1, 0.1,
        0.0, 0.9, 0.9, 0.9, 0.1, 0.1, 0.1,
    ]
    for probability in probabilities:
        update = segmenter.feed(_chunk(probability), probability)
        if update.segment is not None:
            segments.append(update.segment)
    assert len(segments) == 2
    assert all(segment.duration_ms > 0 for segment in segments)


def test_segmenter_rejects_invalid_probability_and_chunk():
    segmenter = SpeechSegmenter(_segmenter_config())
    with pytest.raises(ValueError, match="probability"):
        segmenter.feed(_chunk(), 1.5)
    with pytest.raises(ValueError, match="512"):
        segmenter.feed(np.zeros(100, dtype=np.float32), 0.0)


def test_continuous_input_buffer_is_bounded_and_drops_oldest():
    audio = ContinuousAudioInput(queue_seconds=0.064)
    assert audio.max_chunks == 2
    for index in range(6):
        audio._enqueue(_chunk(index / 10.0), float(index))
    assert audio._queue.qsize() == audio.max_chunks
    assert audio.dropped_chunks >= 4
    assert audio.buffer_memory_bytes == 2 * 512 * 4


def test_continuous_input_start_stop_is_deterministic(monkeypatch):
    class FakeStream:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.started = False
            self.stopped = False
            self.closed = False

        def start(self):
            self.started = True
            callback = self.kwargs["callback"]
            callback(np.zeros((512, 1), dtype=np.float32), 512, None, None)

        def stop(self):
            self.stopped = True

        def close(self):
            self.closed = True

    created = []

    def input_stream(**kwargs):
        stream = FakeStream(**kwargs)
        created.append(stream)
        return stream

    monkeypatch.setitem(sys.modules, "sounddevice", SimpleNamespace(InputStream=input_stream))
    audio = ContinuousAudioInput()
    audio.start()
    assert audio.running is True
    assert audio.read_chunk(timeout=0.01) is not None
    audio.start()  # idempotente
    assert len(created) == 1
    audio.stop()
    assert audio.running is False
    assert created[0].stopped is True
    assert created[0].closed is True
    audio.stop()  # idempotente


def test_installer_pins_silero_version_url_and_sha256():
    from voice import install_models

    assert install_models.SILERO_VERSION == "v6.2.1"
    assert install_models.SILERO_VERSION in install_models.SILERO_URL
    assert install_models.SILERO_URL.endswith("/src/silero_vad/data/silero_vad.onnx")
    assert len(install_models.SILERO_SHA256) == 64
    int(install_models.SILERO_SHA256, 16)


def test_requirements_use_onnxruntime_without_pytorch_stack():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "onnxruntime>=1.23,<2" in requirements
    assert "torch==" not in requirements
    assert "torchaudio" not in requirements
    assert "silero-vad" not in requirements
