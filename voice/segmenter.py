"""Segmentação de fala do STAR Voice V0.1.

Recebe probabilidades de VAD e forma segmentos de áudio com pre-roll, histerese,
post-roll, duração mínima e limite máximo. Não conhece STT, TTS ou GUI.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum

import numpy as np

from config import VAD_CONFIG


class SpeechEvent(str, Enum):
    SILENCE = "silence"
    SPEECH_START = "speech_start"
    SPEECH_ACTIVE = "speech_active"
    SPEECH_END = "speech_end"
    SEGMENT_DROPPED = "segment_dropped"


@dataclass(frozen=True)
class Segment:
    audio: np.ndarray
    sample_rate: int
    start_ms: float
    end_ms: float
    speech_duration_ms: float
    forced: bool = False

    @property
    def duration_ms(self) -> float:
        return 1000.0 * self.audio.size / self.sample_rate


@dataclass(frozen=True)
class SegmentUpdate:
    event: SpeechEvent
    timestamp_ms: float
    probability: float
    segment: Segment | None = None


class SpeechSegmenter:
    """Máquina de estados simples para transformar VAD em utterances."""

    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(VAD_CONFIG if config is None else config)
        self.sample_rate = int(cfg["sample_rate"])
        self.chunk_samples = int(cfg["chunk_samples"])
        self.threshold = float(cfg["threshold"])
        self.neg_threshold = max(
            self.threshold - float(cfg["neg_threshold_offset"]), 0.01
        )
        self.min_speech_ms = float(cfg["min_speech_ms"])
        self.min_silence_ms = float(cfg["min_silence_ms"])
        self.pre_roll_ms = float(cfg["pre_roll_ms"])
        self.post_roll_ms = float(cfg["post_roll_ms"])
        self.max_segment_duration_ms = float(cfg["max_segment_duration_ms"])
        self.chunk_ms = 1000.0 * self.chunk_samples / self.sample_rate

        if self.sample_rate <= 0 or self.chunk_samples <= 0:
            raise ValueError("sample_rate e chunk_samples devem ser positivos.")
        if not 0.0 < self.threshold <= 1.0:
            raise ValueError("threshold deve estar em (0, 1].")
        if self.min_silence_ms < self.post_roll_ms:
            raise ValueError("min_silence_ms deve ser >= post_roll_ms.")
        if self.pre_roll_ms < 0 or self.post_roll_ms < 0:
            raise ValueError("pre_roll_ms/post_roll_ms não podem ser negativos.")

        pre_roll_chunks = max(1, int(np.ceil(self.pre_roll_ms / self.chunk_ms)))
        self._pre_roll: deque[np.ndarray] = deque(maxlen=pre_roll_chunks)
        self.reset()

    @property
    def in_speech(self) -> bool:
        return self._in_speech

    def reset(self) -> None:
        self._pre_roll.clear()
        self._in_speech = False
        self._segment_chunks: list[np.ndarray] = []
        self._segment_start_ms = 0.0
        self._trigger_ms = 0.0
        self._last_speech_end_ms = 0.0
        self._trailing_silence_ms = 0.0
        self._next_timestamp_ms = 0.0

    def _validate_chunk(self, chunk: np.ndarray) -> np.ndarray:
        data = np.asarray(chunk, dtype=np.float32)
        if data.ndim == 2 and 1 in data.shape:
            data = data.reshape(-1)
        if data.ndim != 1 or data.size != self.chunk_samples:
            raise ValueError(
                f"Chunk deve ser mono com {self.chunk_samples} amostras; shape={data.shape}."
            )
        return data

    def feed(
        self,
        chunk: np.ndarray,
        probability: float,
        *,
        timestamp_ms: float | None = None,
    ) -> SegmentUpdate:
        data = self._validate_chunk(chunk)
        prob = float(probability)
        if not 0.0 <= prob <= 1.0:
            raise ValueError("probability deve estar em [0, 1].")

        ts = self._next_timestamp_ms if timestamp_ms is None else float(timestamp_ms)
        self._next_timestamp_ms = ts + self.chunk_ms

        if not self._in_speech:
            if prob < self.threshold:
                self._pre_roll.append(data.copy())
                return SegmentUpdate(SpeechEvent.SILENCE, ts, prob)

            pre_chunks = list(self._pre_roll)
            self._pre_roll.clear()
            pre_ms = len(pre_chunks) * self.chunk_ms
            self._segment_chunks = [*pre_chunks, data.copy()]
            self._segment_start_ms = max(0.0, ts - pre_ms)
            self._trigger_ms = ts
            self._last_speech_end_ms = ts + self.chunk_ms
            self._trailing_silence_ms = 0.0
            self._in_speech = True
            return SegmentUpdate(SpeechEvent.SPEECH_START, ts, prob)

        self._segment_chunks.append(data.copy())
        if prob >= self.neg_threshold:
            self._last_speech_end_ms = ts + self.chunk_ms
            self._trailing_silence_ms = 0.0
        else:
            self._trailing_silence_ms += self.chunk_ms

        total_audio_ms = len(self._segment_chunks) * self.chunk_ms
        if total_audio_ms >= self.max_segment_duration_ms:
            segment = self._finalize(ts + self.chunk_ms, forced=True)
            return SegmentUpdate(SpeechEvent.SPEECH_END, ts, prob, segment)

        if self._trailing_silence_ms >= self.min_silence_ms:
            segment = self._finalize(ts + self.chunk_ms, forced=False)
            if segment is None:
                return SegmentUpdate(SpeechEvent.SEGMENT_DROPPED, ts, prob)
            return SegmentUpdate(SpeechEvent.SPEECH_END, ts, prob, segment)

        return SegmentUpdate(SpeechEvent.SPEECH_ACTIVE, ts, prob)

    def _finalize(self, observed_end_ms: float, *, forced: bool) -> Segment | None:
        speech_duration_ms = max(0.0, self._last_speech_end_ms - self._trigger_ms)
        chunks = self._segment_chunks

        if not forced and self._trailing_silence_ms > self.post_roll_ms:
            trim_ms = self._trailing_silence_ms - self.post_roll_ms
            trim_chunks = int(np.floor(trim_ms / self.chunk_ms))
            if trim_chunks > 0:
                chunks = chunks[:-trim_chunks]

        audio = (
            np.concatenate(chunks).astype(np.float32, copy=False)
            if chunks
            else np.empty(0, dtype=np.float32)
        )
        end_ms = self._segment_start_ms + 1000.0 * audio.size / self.sample_rate
        start_ms = self._segment_start_ms

        self._in_speech = False
        self._segment_chunks = []
        self._trailing_silence_ms = 0.0
        self._pre_roll.clear()

        if speech_duration_ms < self.min_speech_ms:
            return None
        return Segment(
            audio=audio,
            sample_rate=self.sample_rate,
            start_ms=start_ms,
            end_ms=min(end_ms, observed_end_ms),
            speech_duration_ms=speech_duration_ms,
            forced=forced,
        )

    def flush(self) -> Segment | None:
        """Finaliza fala corrente no shutdown, sem adicionar silêncio artificial."""
        if not self._in_speech:
            return None
        return self._finalize(self._next_timestamp_ms, forced=True)
