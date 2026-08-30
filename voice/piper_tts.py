"""TTS rápido e local da STAR usando Piper.

Piper fica no .venv principal, carrega o modelo uma vez e transmite os chunks
para o alto-falante. Chatterbox continua como motor opcional de voz clonada,
mas não é usado no caminho rápido padrão em CPU.
"""
from __future__ import annotations

from pathlib import Path
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "voice" / "models" / "piper"
MODEL_NAME = "pt_BR-faber-medium"
MODEL_PATH = MODEL_DIR / f"{MODEL_NAME}.onnx"


class PiperTTS:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = Path(model_path)
        self.voice = None
        self.last_error = None
        self.last_elapsed = 0.0
        self._load_lock = threading.Lock()

    @property
    def configured(self) -> bool:
        try:
            import piper  # noqa: F401
        except Exception:
            return False
        return self.model_path.exists() and self.model_path.with_suffix(self.model_path.suffix + ".json").exists()

    def _load(self) -> None:
        if self.voice is not None:
            return
        with self._load_lock:
            if self.voice is not None:
                return
            if not self.configured:
                raise RuntimeError(
                    f"Modelo Piper não encontrado: {self.model_path}. Execute INSTALAR_VOZ.bat."
                )
            from piper import PiperVoice
            self.voice = PiperVoice.load(str(self.model_path), use_cuda=False)

    def warmup(self) -> None:
        """Carrega o modelo sem falar; útil para eliminar atraso na primeira resposta."""
        self._load()

    def speak(self, text: str) -> bool:
        text = str(text).strip()
        if not text:
            return True
        started = time.perf_counter()
        try:
            self._load()
            import sounddevice as sd
            import numpy as np
            from piper import SynthesisConfig

            cfg = SynthesisConfig(
                volume=1.0,
                length_scale=0.95,
                noise_scale=0.667,
                noise_w_scale=0.8,
                normalize_audio=True,
            )
            stream = None
            sample_rate = None
            channels = None
            try:
                for chunk in self.voice.synthesize(text, syn_config=cfg):
                    if sample_rate is None:
                        sample_rate = int(chunk.sample_rate)
                        channels = max(1, int(chunk.sample_channels))
                        stream = sd.OutputStream(
                            samplerate=sample_rate,
                            channels=channels,
                            dtype="float32",
                            blocksize=0,
                        )
                        stream.start()
                    audio = np.asarray(chunk.audio_float_array, dtype=np.float32)
                    if channels > 1 and audio.ndim == 1:
                        audio = audio.reshape(-1, channels)
                    if stream is not None and audio.size:
                        stream.write(audio)
            finally:
                if stream is not None:
                    try:
                        stream.stop()
                    finally:
                        stream.close()
            self.last_elapsed = time.perf_counter() - started
            self.last_error = None
            return True
        except Exception as exc:
            self.last_elapsed = time.perf_counter() - started
            self.last_error = f"{type(exc).__name__}: {exc}"
            return False

    def speak_async(self, text: str, callback=None):
        def run():
            ok = self.speak(text)
            if callback:
                callback(ok, self.last_error)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread
