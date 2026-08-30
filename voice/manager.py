"""Gerenciador de voz da STAR V1.9.

Caminho padrão de baixa latência:
  microfone -> faster-whisper tiny -> STAR Core -> Piper PT-BR -> sounddevice

O Chatterbox fica fora do caminho normal porque a máquina atual é CPU-only e a
síntese clonada é muito mais pesada. Ele pode ser usado posteriormente como
modo opcional de alta fidelidade.
"""
from __future__ import annotations

import hashlib
import os
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIPER_DIR = ROOT / "voice" / "models" / "piper"
CACHE_DIR = ROOT / "voice" / "cache"


class LocalSpeechToText:
    """STT local rápido com faster-whisper tiny."""

    def __init__(self, model_size: str = "tiny"):
        self.model_size = os.getenv("STAR_STT_MODEL", model_size)
        self.model = None
        self.last_error = None
        self.last_elapsed = 0.0
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        try:
            import faster_whisper  # noqa: F401
            return True
        except Exception:
            return False

    def _load(self) -> None:
        if self.model is not None:
            return
        from faster_whisper import WhisperModel
        self.model = WhisperModel(
            self.model_size,
            device="cpu",
            compute_type="int8",
            cpu_threads=max(2, min(8, os.cpu_count() or 2)),
            num_workers=1,
        )

    def warmup(self) -> None:
        with self._lock:
            self._load()

    def transcribe(self, audio_path: Path) -> str:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise RuntimeError(f"Gravação não encontrada: {audio_path}")
        started = time.perf_counter()
        with self._lock:
            try:
                self._load()
                segments, _ = self.model.transcribe(
                    str(audio_path),
                    language="pt",
                    task="transcribe",
                    beam_size=1,
                    best_of=1,
                    temperature=0.0,
                    vad_filter=True,
                    condition_on_previous_text=False,
                    without_timestamps=True,
                )
                text = " ".join(seg.text.strip() for seg in segments if seg.text.strip()).strip()
                if not text:
                    raise RuntimeError("Não consegui entender a fala.")
                self.last_elapsed = time.perf_counter() - started
                self.last_error = None
                return text
            except Exception as exc:
                self.last_elapsed = time.perf_counter() - started
                self.last_error = f"{type(exc).__name__}: {exc}"
                raise


class FastPiperTTS:
    """Piper PT-BR carregado uma vez, com cache e streaming para o alto-falante."""

    def __init__(self):
        self.voice = None
        self.last_error = None
        self.last_elapsed = 0.0
        self.model_path = self._find_model()
        self._lock = threading.Lock()

    def _find_model(self) -> Path:
        preferred = PIPER_DIR / "pt_BR-faber-medium.onnx"
        if preferred.exists():
            return preferred
        if PIPER_DIR.exists():
            matches = list(PIPER_DIR.rglob("pt_BR-faber-medium.onnx"))
            if matches:
                return matches[0]
        return preferred

    @property
    def configured(self) -> bool:
        return self.model_path.exists() and self.model_path.with_suffix(".onnx.json").exists()

    def _load(self) -> None:
        if self.voice is not None:
            return
        with self._lock:
            if self.voice is not None:
                return
            if not self.configured:
                raise RuntimeError("Modelo Piper PT-BR não encontrado. Execute INSTALAR_VOZ.bat uma vez.")
            from piper import PiperVoice
            self.voice = PiperVoice.load(str(self.model_path), use_cuda=False)

    def warmup(self) -> None:
        self._load()

    @staticmethod
    def _chunks(text: str, max_chars: int = 220):
        import re
        text = " ".join(str(text).split())
        if not text:
            return []
        pieces = re.split(r"(?<=[.!?…])\s+", text)
        result = []
        for piece in pieces:
            if len(piece) <= max_chars:
                result.append(piece)
                continue
            words = piece.split()
            current = []
            size = 0
            for word in words:
                if current and size + len(word) + 1 > max_chars:
                    result.append(" ".join(current))
                    current = []
                    size = 0
                current.append(word)
                size += len(word) + (1 if current[:-1] else 0)
            if current:
                result.append(" ".join(current))
        return result

    def speak(self, text: str) -> bool:
        text = str(text).strip()
        if not text:
            return True
        started = time.perf_counter()
        try:
            self._load()
            import numpy as np
            import sounddevice as sd
            from piper import SynthesisConfig

            cfg = SynthesisConfig(
                volume=1.0,
                length_scale=0.95,
                noise_scale=0.667,
                noise_w_scale=0.8,
                normalize_audio=True,
            )
            for part in self._chunks(text):
                stream = None
                channels = 1
                try:
                    for chunk in self.voice.synthesize(part, syn_config=cfg):
                        if stream is None:
                            channels = max(1, int(chunk.sample_channels))
                            stream = sd.OutputStream(
                                samplerate=int(chunk.sample_rate),
                                channels=channels,
                                dtype="float32",
                                blocksize=0,
                            )
                            stream.start()
                        audio = np.asarray(chunk.audio_float_array, dtype=np.float32)
                        if channels > 1 and audio.ndim == 1:
                            audio = audio.reshape(-1, channels)
                        if audio.size:
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


class WindowsFallbackTTS:
    """Fallback de voz local do Windows via SAPI/pyttsx3."""

    def __init__(self):
        self.engine = None
        self._lock = threading.Lock()

    def _load(self):
        if self.engine is None:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 185)
            self.engine.setProperty("volume", 1.0)

    def speak(self, text: str) -> bool:
        try:
            with self._lock:
                self._load()
                self.engine.say(str(text))
                self.engine.runAndWait()
            return True
        except Exception:
            return False


class VoiceManager:
    """Orquestra STT e TTS locais sem ElevenLabs."""

    def __init__(self):
        self.stt = LocalSpeechToText()
        self.piper = FastPiperTTS()
        self.fallback = WindowsFallbackTTS()
        self.last_error = None
        self.last_tts_engine = "Piper"
        self._tts_lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return self.piper.configured or True

    @property
    def piper_configured(self) -> bool:
        return self.piper.configured

    @property
    def stt_configured(self) -> bool:
        return self.stt.configured

    @property
    def tts_description(self) -> str:
        if self.piper.configured:
            return "Piper PT-BR (rápido)"
        return "Windows SAPI (fallback)"

    def warmup(self) -> None:
        errors = []
        try:
            self.stt.warmup()
        except Exception as exc:
            errors.append(f"STT: {type(exc).__name__}: {exc}")
        try:
            self.piper.warmup()
        except Exception as exc:
            errors.append(f"TTS: {type(exc).__name__}: {exc}")
        self.last_error = " | ".join(errors) if errors else None

    def transcribe(self, audio_path: Path) -> str:
        return self.stt.transcribe(audio_path)

    def speak(self, text: str) -> bool:
        with self._tts_lock:
            if self.piper.configured and self.piper.speak(text):
                self.last_error = None
                self.last_tts_engine = "Piper"
                return True
            piper_error = self.piper.last_error
            if self.fallback.speak(text):
                self.last_error = None
                self.last_tts_engine = "Windows SAPI (fallback)"
                return True
            self.last_tts_engine = "indisponível"
            self.last_error = piper_error or "Piper e Windows SAPI falharam."
            return False

    def warmup_async(self):
        thread = threading.Thread(target=self.warmup, daemon=True, name="STAR-VoiceWarmup")
        thread.start()
        return thread

    def speak_async(self, text: str, callback=None):
        def run():
            ok = self.speak(text)
            if callback:
                callback(ok, self.last_error)
        thread = threading.Thread(target=run, daemon=True, name="STAR-TTS")
        thread.start()
        return thread

    def test_audio_async(self, callback=None):
        return self.speak_async("Olá! Eu sou a STAR. Minha voz local está pronta.", callback)

    def close(self):
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
