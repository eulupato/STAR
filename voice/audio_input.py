"""Captura de áudio local e detecção de atividade de voz da STAR.

Mantém o gravador manual existente e acrescenta um VAD adaptativo opcional para
conversa mãos-livres. O VAD trabalha somente com energia local do microfone,
não depende de cloud, não persiste áudio bruto e entrega segmentos temporários
para o STT existente.
"""
from __future__ import annotations

from pathlib import Path
import os
import tempfile
import threading
import time

import numpy as np


class AudioRecorder:
    """Gravador manual preservado para compatibilidade com a interface atual."""

    def __init__(self, samplerate=16000, channels=1):
        self.samplerate = samplerate
        self.channels = channels
        self.stream = None
        self.frames = []
        self.recording = False
        self.last_error = None

    @property
    def available(self):
        try:
            import sounddevice  # noqa: F401
            return True
        except Exception:
            return False

    def start(self):
        import sounddevice as sd

        if self.recording:
            return
        self.frames = []
        self.last_error = None

        def callback(indata, frames, time_info, status):
            del frames, time_info
            if status:
                self.last_error = str(status)
            self.frames.append(indata.copy())

        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="float32",
            callback=callback,
        )
        self.stream.start()
        self.recording = True

    def stop(self):
        stream = self.stream
        self.stream = None
        self.recording = False
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()

    def stop_to_wav(self):
        if not self.recording:
            return None

        try:
            self.stop()
        except Exception:
            self.stream = None
            self.recording = False
            raise

        if not self.frames:
            raise RuntimeError("Nenhum áudio foi capturado.")

        import soundfile as sf

        data = np.concatenate(self.frames, axis=0)
        fd, name = tempfile.mkstemp(prefix="star_mic_", suffix=".wav")
        os.close(fd)
        out = Path(name)
        sf.write(str(out), data, self.samplerate, subtype="PCM_16")
        return out


class VoiceActivityDetector:
    """VAD adaptativo local para mãos-livres e barge-in.

    A detecção usa RMS + noise floor adaptativo + histerese. Isso separa a
    decisão rápida "há alguém falando?" do STT, que continua responsável apenas
    por entender as palavras. Durante a fala da STAR o limiar é elevado para
    reduzir auto-disparo por eco; fala humana suficientemente acima do ambiente
    ainda pode interromper o TTS.

    Nenhum áudio é gravado em background fora de um segmento detectado. Cada
    segmento vira um WAV temporário e cabe ao consumidor apagá-lo após o STT.
    """

    def __init__(
        self,
        samplerate: int = 16000,
        channels: int = 1,
        *,
        trigger_over_floor: float = 2.6,
        guard_boost: float = 2.4,
        release_ratio: float = 0.60,
        start_ms: int = 110,
        silence_ms: int = 650,
        max_ms: int = 20000,
        floor_up: float = 0.0008,
        floor_down: float = 0.02,
    ):
        self.samplerate = int(samplerate)
        self.channels = int(channels)
        self.trigger_over_floor = max(1.2, float(trigger_over_floor))
        self.guard_boost = max(1.0, float(guard_boost))
        self.release_ratio = max(0.1, min(float(release_ratio), 0.95))
        self.start_ms = max(40, int(start_ms))
        self.silence_ms = max(200, int(silence_ms))
        self.max_ms = max(2000, int(max_ms))
        self.floor_up = max(0.00001, min(float(floor_up), 0.2))
        self.floor_down = max(0.0001, min(float(floor_down), 0.5))

        self.stream = None
        self.running = False
        self.last_error = None
        self.segment_count = 0
        self.false_starts = 0

        self._lock = threading.RLock()
        self._on_start = None
        self._on_end = None
        self._on_level = None
        self._on_error = None
        self._guard_provider = None

        self._floor = 0.01
        self._energy = 0.0
        self._threshold = 0.026
        self._armed_at = 0.0
        self._speaking = False
        self._speech_started_at = 0.0
        self._last_loud = 0.0
        self._segment_frames = []
        self._guard = False
        self._calibration_blocks = 0

    @property
    def available(self) -> bool:
        try:
            import sounddevice  # noqa: F401
            import soundfile  # noqa: F401
            return True
        except Exception:
            return False

    @staticmethod
    def _dispatch(callback, *args) -> None:
        if callback is None:
            return

        def run():
            try:
                callback(*args)
            except Exception:
                # Callback de UI/STT não pode derrubar a thread de áudio.
                pass

        threading.Thread(
            target=run,
            daemon=True,
            name="STAR-VAD-Callback",
        ).start()

    def _guard_active(self) -> bool:
        provider = self._guard_provider
        if provider is None:
            return False
        try:
            return bool(provider())
        except Exception:
            return False

    def _reset_segment_locked(self) -> None:
        self._armed_at = 0.0
        self._speaking = False
        self._speech_started_at = 0.0
        self._last_loud = 0.0
        self._segment_frames = []

    def _emit_segment(self, frames, duration_ms: float) -> None:
        if not frames:
            return
        out = None
        try:
            import soundfile as sf

            data = np.concatenate(frames, axis=0)
            if data.size == 0:
                return
            fd, name = tempfile.mkstemp(prefix="star_vad_", suffix=".wav")
            os.close(fd)
            out = Path(name)
            sf.write(str(out), data, self.samplerate, subtype="PCM_16")
            callback = self._on_end
            if callback is None:
                out.unlink(missing_ok=True)
                return
            callback(out, float(duration_ms))
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            self._dispatch(self._on_error, self.last_error)
            if out is not None:
                try:
                    out.unlink(missing_ok=True)
                except Exception:
                    pass

    def _process_block(self, data: np.ndarray, now: float, guard: bool):
        """Processa um bloco; separado da callback para ficar testável."""
        started = False
        ended = None
        level = 0.0

        samples = np.asarray(data, dtype=np.float32)
        if samples.size == 0:
            return started, ended, level

        energy = float(np.sqrt(np.mean(samples * samples)))

        with self._lock:
            self._energy += (energy - self._energy) * 0.5
            level = min(1.0, self._energy * 12.0)
            self._guard = bool(guard)

            if not self._speaking and self._armed_at == 0.0:
                if self._calibration_blocks < 40:
                    rate = 0.08
                    self._calibration_blocks += 1
                else:
                    rate = self.floor_up if self._energy > self._floor else self.floor_down
                self._floor += (self._energy - self._floor) * rate
                self._floor = max(self._floor, 0.0015)

            boost = self.guard_boost if guard else 1.0
            self._threshold = max(
                0.0035,
                self._floor * self.trigger_over_floor * boost,
            )
            release = self._threshold * self.release_ratio

            if not self._speaking:
                if self._energy > self._threshold:
                    if self._armed_at == 0.0:
                        self._armed_at = now
                        self._segment_frames = [samples.copy()]
                    else:
                        self._segment_frames.append(samples.copy())

                    if (now - self._armed_at) * 1000.0 >= self.start_ms:
                        self._speaking = True
                        self._speech_started_at = self._armed_at
                        self._last_loud = now
                        started = True
                elif self._armed_at != 0.0:
                    self.false_starts += 1
                    self._reset_segment_locked()
            else:
                self._segment_frames.append(samples.copy())
                if self._energy > release:
                    self._last_loud = now

                quiet_ms = (now - self._last_loud) * 1000.0
                run_ms = (now - self._speech_started_at) * 1000.0
                if quiet_ms >= self.silence_ms or run_ms >= self.max_ms:
                    frames = self._segment_frames
                    duration_ms = run_ms
                    self.segment_count += 1
                    self._reset_segment_locked()
                    ended = (frames, duration_ms)

        return started, ended, level

    def _audio_callback(self, indata, frames, time_info, status):
        del frames, time_info
        if status:
            self.last_error = str(status)
        try:
            started, ended, level = self._process_block(
                indata.copy(),
                time.perf_counter(),
                self._guard_active(),
            )
            if self._on_level is not None:
                try:
                    self._on_level(level)
                except Exception:
                    pass
            if started:
                self._dispatch(self._on_start)
            if ended is not None:
                segment_frames, duration_ms = ended
                threading.Thread(
                    target=self._emit_segment,
                    args=(segment_frames, duration_ms),
                    daemon=True,
                    name="STAR-VAD-Segment",
                ).start()
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            self._dispatch(self._on_error, self.last_error)

    def start(
        self,
        *,
        on_start=None,
        on_end=None,
        on_level=None,
        on_error=None,
        guard_provider=None,
    ) -> None:
        if self.running:
            return
        if not self.available:
            raise RuntimeError(
                "VAD local indisponível: instale sounddevice e soundfile."
            )

        import sounddevice as sd

        self._on_start = on_start
        self._on_end = on_end
        self._on_level = on_level
        self._on_error = on_error
        self._guard_provider = guard_provider
        self.last_error = None

        with self._lock:
            self._reset_segment_locked()
            self._floor = 0.01
            self._energy = 0.0
            self._threshold = 0.026
            self._calibration_blocks = 0

        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="float32",
                callback=self._audio_callback,
            )
            self.stream.start()
            self.running = True
        except Exception as exc:
            self.stream = None
            self.running = False
            self.last_error = f"{type(exc).__name__}: {exc}"
            raise

    def stop(self) -> None:
        stream = self.stream
        self.stream = None
        self.running = False
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()
        with self._lock:
            self._reset_segment_locked()

    def status(self) -> dict:
        with self._lock:
            return {
                "available": self.available,
                "running": bool(self.running),
                "energy": round(float(self._energy), 6),
                "noise_floor": round(float(self._floor), 6),
                "threshold": round(float(self._threshold), 6),
                "speaking": bool(self._speaking),
                "armed": bool(self._armed_at),
                "guard": bool(self._guard),
                "segments": int(self.segment_count),
                "false_starts": int(self.false_starts),
                "last_error": self.last_error,
                "raw_audio_persisted": False,
                "temporary_segments_only": True,
            }
