"""Captura de áudio local e detecção de atividade de voz da STAR.

Mantém o gravador manual existente e acrescenta um VAD adaptativo opcional para
conversa mãos-livres. O VAD trabalha somente com energia local do microfone,
não depende de cloud, não persiste áudio bruto e entrega segmentos temporários
para o STT existente.
"""
from __future__ import annotations

from collections import deque
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


class VoiceTurnAssembler:
    """Agrupa segmentos acústicos em um único turno linguístico.

    O VAD responde à pergunta física "a sala ficou quieta?". Este assembler
    responde à pergunta conversacional "o pensamento parece ter terminado?".
    Assim uma pausa curta no meio de uma frase não vira dois pedidos separados.

    A lógica é deliberadamente pequena e determinística. Ela não tenta entender
    semanticamente a conversa inteira e não substitui o Context Engine da STAR.
    """

    CONTINUATIONS = {
        "e", "ou", "mas", "porque", "pois", "se", "quando", "enquanto",
        "que", "quem", "cujo", "cuja", "para", "de", "do", "da", "dos",
        "das", "em", "no", "na", "nos", "nas", "com", "sem", "por",
        "pelo", "pela", "sobre", "entre", "até", "como", "então",
        "and", "or", "but", "because", "if", "when", "while", "that",
        "to", "of", "in", "on", "with", "from", "about",
    }
    IMMEDIATE_SHORT = {
        "pare", "para", "espera", "espere", "cancela", "cancelar",
        "chega", "silêncio", "silencio", "não", "nao", "sim", "star",
        "stop", "wait", "cancel", "enough", "quiet", "no", "yes",
    }

    def __init__(
        self,
        on_utterance,
        *,
        settle_ms: int = 280,
        continue_ms: int = 1350,
        max_hold_ms: int = 5500,
    ):
        self.on_utterance = on_utterance
        self.settle_ms = max(0, int(settle_ms))
        self.continue_ms = max(self.settle_ms, int(continue_ms))
        self.max_hold_ms = max(self.continue_ms, int(max_hold_ms))
        self._lock = threading.RLock()
        self._held = ""
        self._first_at = 0.0
        self._timer = None
        self._generation = 0

    @staticmethod
    def _clean(text: str) -> str:
        return " ".join(str(text or "").strip().split())

    @classmethod
    def hold_for(cls, text: str, *, settle_ms=280, continue_ms=1350) -> int:
        value = cls._clean(text)
        if not value:
            return int(continue_ms)

        if value.endswith((".", "!", "?")):
            return 0

        stripped = value.rstrip()
        if stripped.endswith((",", ";", ":", "-", "–", "—")):
            return int(continue_ms)

        words = stripped.casefold().split()
        normalized = " ".join(word.strip(".,!?;:") for word in words)

        # Em português, "para" é tanto preposição quanto comando. Um comando
        # curto explícito deve ganhar do heurístico de continuação para não
        # transformar "STAR, para" em uma espera artificial longa.
        if normalized in cls.IMMEDIATE_SHORT:
            return int(settle_ms)

        last = words[-1].strip(".,!?;:") if words else ""
        if last in cls.CONTINUATIONS:
            return int(continue_ms)

        if len(words) <= 2:
            return int(continue_ms)

        return int(settle_ms)

    def _cancel_timer_locked(self) -> None:
        timer = self._timer
        self._timer = None
        if timer is not None:
            timer.cancel()

    def _emit_generation(self, generation: int) -> None:
        with self._lock:
            if generation != self._generation:
                return
            value = self._held.strip()
            self._held = ""
            self._first_at = 0.0
            self._timer = None
            self._generation += 1
        if value:
            self.on_utterance(value)

    def speech_started(self) -> None:
        """Nova fala audível mantém o turno aberto sem perder texto já transcrito."""
        with self._lock:
            if not self._held:
                return
            self._cancel_timer_locked()
            elapsed_ms = (time.monotonic() - self._first_at) * 1000.0
            remaining = max(0, self.max_hold_ms - int(elapsed_ms))
            self._generation += 1
            generation = self._generation
            timer = threading.Timer(
                max(0.05, remaining / 1000.0),
                self._emit_generation,
                args=(generation,),
            )
            timer.daemon = True
            self._timer = timer
            timer.start()

    def feed(self, text: str) -> str:
        fragment = self._clean(text)
        if not fragment:
            return self.held()

        with self._lock:
            now = time.monotonic()
            if not self._held:
                self._first_at = now
                self._held = fragment
            else:
                self._held = f"{self._held} {fragment}".strip()

            self._cancel_timer_locked()
            elapsed_ms = (now - self._first_at) * 1000.0
            wait_ms = self.hold_for(
                self._held,
                settle_ms=self.settle_ms,
                continue_ms=self.continue_ms,
            )
            wait_ms = min(wait_ms, max(0, self.max_hold_ms - int(elapsed_ms)))

            self._generation += 1
            generation = self._generation

            if wait_ms <= 0:
                value = self._held
                self._held = ""
                self._first_at = 0.0
                self._generation += 1
            else:
                timer = threading.Timer(
                    wait_ms / 1000.0,
                    self._emit_generation,
                    args=(generation,),
                )
                timer.daemon = True
                self._timer = timer
                timer.start()
                return self._held

        if value:
            self.on_utterance(value)
        return value

    def flush(self) -> str:
        with self._lock:
            self._cancel_timer_locked()
            value = self._held.strip()
            self._held = ""
            self._first_at = 0.0
            self._generation += 1
        if value:
            self.on_utterance(value)
        return value

    def cancel(self) -> None:
        with self._lock:
            self._cancel_timer_locked()
            self._held = ""
            self._first_at = 0.0
            self._generation += 1

    def held(self) -> str:
        with self._lock:
            return self._held


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
        pre_roll_ms: int = 300,
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
        self.pre_roll_ms = max(0, min(int(pre_roll_ms), 1000))
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
        # Mantém uma pequena janela anterior ao disparo do VAD para não cortar
        # fonemas iniciais de frases curtas como "Olá, STAR".
        self._pre_roll_frames = deque()
        self._pre_roll_samples = 0
        self._pre_roll_limit = max(
            0,
            int(self.samplerate * self.pre_roll_ms / 1000.0),
        )
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

    def _remember_pre_roll_locked(self, samples: np.ndarray) -> None:
        if self._pre_roll_limit <= 0:
            return
        block = samples.copy()
        self._pre_roll_frames.append(block)
        self._pre_roll_samples += int(block.shape[0])
        while self._pre_roll_frames and self._pre_roll_samples > self._pre_roll_limit:
            removed = self._pre_roll_frames.popleft()
            self._pre_roll_samples -= int(removed.shape[0])

    def _take_pre_roll_locked(self) -> list[np.ndarray]:
        frames = [frame.copy() for frame in self._pre_roll_frames]
        self._pre_roll_frames.clear()
        self._pre_roll_samples = 0
        return frames

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
                # Sempre preserve um pequeno pré-roll antes do gatilho. Isso
                # evita perder o início da primeira palavra quando o volume
                # cruza o limiar alguns milissegundos depois da fala começar.
                if self._armed_at == 0.0:
                    self._remember_pre_roll_locked(samples)

                if self._energy > self._threshold:
                    if self._armed_at == 0.0:
                        self._armed_at = now
                        self._segment_frames = self._take_pre_roll_locked()
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
            self._pre_roll_frames.clear()
            self._pre_roll_samples = 0
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
                "pre_roll_ms": int(self.pre_roll_ms),
                "last_error": self.last_error,
                "raw_audio_persisted": False,
                "temporary_segments_only": True,
            }
