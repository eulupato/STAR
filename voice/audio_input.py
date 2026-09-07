"""Captura de áudio do microfone da STAR."""
from dataclasses import dataclass
from pathlib import Path
import os
import queue
import tempfile
import time
import numpy as np

from config import VAD_CONFIG


class AudioRecorder:
    def __init__(self, samplerate=16000, channels=1):
        self.samplerate=samplerate
        self.channels=channels
        self.stream=None
        self.frames=[]
        self.recording=False
        self.last_error=None

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
        self.frames=[]
        self.last_error=None

        def callback(indata, frames, time_info, status):
            if status:
                self.last_error=str(status)
            self.frames.append(indata.copy())

        self.stream=sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="float32",
            callback=callback,
        )
        self.stream.start()
        self.recording=True

    def stop(self):
        stream=self.stream
        self.stream=None
        self.recording=False
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
            self.stream=None
            self.recording=False
            raise

        if not self.frames:
            raise RuntimeError("Nenhum áudio foi capturado.")

        import soundfile as sf

        data=np.concatenate(self.frames, axis=0)
        fd, name=tempfile.mkstemp(prefix="star_mic_", suffix=".wav")
        os.close(fd)
        out=Path(name)
        sf.write(str(out), data, self.samplerate, subtype="PCM_16")
        return out


class AudioInputError(RuntimeError):
    """Falha explícita de captura contínua de áudio."""


@dataclass(frozen=True)
class AudioChunk:
    samples: np.ndarray
    timestamp_ms: float


class ContinuousAudioInput:
    """Captura experimental contínua, limitada e não bloqueante para V0.1.

    A fila guarda no máximo ``input_queue_seconds`` de PCM mono float32. Quando
    o consumidor atrasa, o chunk mais antigo é descartado; a thread de callback do
    dispositivo nunca bloqueia esperando processamento.
    """

    def __init__(
        self,
        *,
        samplerate: int | None = None,
        channels: int = 1,
        blocksize: int | None = None,
        queue_seconds: float | None = None,
        device=None,
    ) -> None:
        self.samplerate = int(samplerate or VAD_CONFIG["sample_rate"])
        self.channels = int(channels)
        self.blocksize = int(blocksize or VAD_CONFIG["chunk_samples"])
        self.queue_seconds = float(
            queue_seconds if queue_seconds is not None else VAD_CONFIG["input_queue_seconds"]
        )
        self.device = device
        if self.samplerate <= 0 or self.channels != 1 or self.blocksize <= 0:
            raise ValueError("ContinuousAudioInput requer sample rate positivo, mono e blocksize positivo.")
        if self.queue_seconds <= 0:
            raise ValueError("queue_seconds deve ser positivo.")

        chunks_per_second = self.samplerate / self.blocksize
        self.max_chunks = max(1, int(np.ceil(self.queue_seconds * chunks_per_second)))
        self._queue: queue.Queue[AudioChunk] = queue.Queue(maxsize=self.max_chunks)
        self.stream = None
        self.running = False
        self.last_error: str | None = None
        self.dropped_chunks = 0

    @property
    def available(self) -> bool:
        try:
            import sounddevice  # noqa: F401
            return True
        except Exception:
            return False

    @property
    def buffered_ms(self) -> float:
        return self._queue.qsize() * self.blocksize * 1000.0 / self.samplerate

    @property
    def buffer_memory_bytes(self) -> int:
        return self.max_chunks * self.blocksize * np.dtype(np.float32).itemsize

    def _clear_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _enqueue(self, samples: np.ndarray, timestamp_ms: float) -> None:
        chunk = AudioChunk(np.asarray(samples, dtype=np.float32).copy(), float(timestamp_ms))
        try:
            self._queue.put_nowait(chunk)
            return
        except queue.Full:
            self.dropped_chunks += 1
        try:
            self._queue.get_nowait()
        except queue.Empty:
            pass
        try:
            self._queue.put_nowait(chunk)
        except queue.Full:
            self.dropped_chunks += 1

    def start(self) -> None:
        if self.running:
            return
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise AudioInputError("sounddevice não está instalado.") from exc

        self._clear_queue()
        self.last_error = None
        self.dropped_chunks = 0

        def callback(indata, frames, time_info, status):
            if status:
                self.last_error = f"AUDIO_STREAM_STATUS: {status}"
            if frames != self.blocksize:
                self.last_error = (
                    f"AUDIO_CHUNK_SIZE_ERROR: esperado {self.blocksize}, recebido {frames}"
                )
                return
            data = np.asarray(indata, dtype=np.float32)
            if data.ndim != 2 or data.shape[1] != 1:
                self.last_error = f"AUDIO_FORMAT_ERROR: shape={data.shape}"
                return
            self._enqueue(data[:, 0], time.monotonic_ns() / 1_000_000.0)

        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=1,
                dtype="float32",
                blocksize=self.blocksize,
                device=self.device,
                callback=callback,
            )
            self.stream.start()
        except Exception as exc:
            self.stream = None
            self.running = False
            self.last_error = f"AUDIO_DEVICE_ERROR: {type(exc).__name__}: {exc}"
            raise AudioInputError(self.last_error) from exc
        self.running = True

    def read_chunk(self, timeout: float = 0.5) -> AudioChunk | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self) -> None:
        stream = self.stream
        self.stream = None
        self.running = False
        if stream is None:
            return
        try:
            stream.stop()
        finally:
            stream.close()
