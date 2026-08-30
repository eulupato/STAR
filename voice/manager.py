"""Gerenciador unificado de voz da STAR V1.9.

Caminho rápido padrão:
  microfone -> faster-whisper tiny -> STAR Core -> Piper -> sounddevice

Piper fica carregado no processo principal para evitar recarga por frase.
Chatterbox permanece como motor opcional para voz clonada: a máquina atual
roda CPU-only, então ele não é usado no caminho normal de baixa latência.
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class LocalSpeechToText:
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
                segments, _info = self.model.transcribe(
                    str(audio_path),
                    language="pt",
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
    """TTS neural local de baixa latência, carregado uma única vez."""

    def __init__(self):
        self.voice = None
        self.last_error = None
        self.last_elapsed = 0.0
        self.model_path = ROOT / "voice" / "models" / "piper" / "pt_BR-faber-medium.onnx"
        self._lock = threading.Lock()

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
                raise RuntimeError(
                    "Modelo Piper PT-BR não encontrado. Execute INSTALAR_VOZ.bat."
                )
            from piper import PiperVoice
            self.voice = PiperVoice.load(str(self.model_path), use_cuda=False)

    def warmup(self) -> None:
        self._load()

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
            stream = None
            channels = 1
            try:
                for chunk in self.voice.synthesize(text, syn_config=cfg):
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
    """Fallback imediato usando SAPI/pyttsx3 do Windows."""

    def speak(self, text: str) -> bool:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 185)
            engine.setProperty("volume", 1.0)
            engine.say(str(text))
            engine.runAndWait()
            engine.stop()
            return True
        except Exception:
            return False


class VoiceManager:
    def __init__(self):
        self.stt = LocalSpeechToText()
        self.piper = FastPiperTTS()
        self.fallback = WindowsFallbackTTS()
        self.last_error = None
        self.last_tts_engine = "Piper"
        self._tts_lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return self.piper.configured or True  # fallback do Windows mantém saída disponível

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
        # Pré-carrega fora da GUI para não introduzir o atraso de primeira fala.
        try:
            self.stt.warmup()
        except Exception as exc:
            self.last_error = f"STT: {type(exc).__name__}: {exc}"
        try:
            self.piper.warmup()
        except Exception as exc:
            self.last_error = f"TTS: {type(exc).__name__}: {exc}"

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
            self.last_error = piper_error or "Piper e voz do Windows falharam."
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

    def close(self) -> None:
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
