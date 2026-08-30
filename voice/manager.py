"""Gerenciador unificado de voz da STAR V1.9.

Arquitetura rápida:
  microfone -> faster-whisper tiny -> STAR Core -> Piper -> sounddevice

Chatterbox permanece disponível como motor de voz clonada de alta fidelidade,
mas fica fora do caminho normal para evitar minutos de espera em CPU.
Nenhum serviço externo de voz é usado.
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
        # tiny + int8 é o perfil de baixa latência para a máquina atual sem GPU.
        self.model = WhisperModel(
            self.model_size,
            device="cpu",
            compute_type="int8",
            cpu_threads=max(1, min(6, os.cpu_count() or 2)),
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


class VoiceManager:
    def __init__(self):
        self.stt = LocalSpeechToText()
        self._tts_lock = threading.Lock()
        self.last_error = None
        self.last_tts_engine = "Piper"
        try:
            from voice.piper_tts import PiperTTS
            self.piper = PiperTTS()
        except Exception:
            self.piper = None

    @property
    def configured(self) -> bool:
        return bool(self.piper and self.piper.configured)

    @property
    def stt_configured(self) -> bool:
        return self.stt.configured

    @property
    def tts_description(self) -> str:
        if self.configured:
            return "Piper PT-BR (rápido)"
        return "Piper não instalado"

    def transcribe(self, audio_path: Path) -> str:
        return self.stt.transcribe(audio_path)

    def warmup_stt(self) -> None:
        self.stt.warmup()

    def warmup_tts(self) -> None:
        if self.piper:
            self.piper.warmup()

    def speak(self, text: str) -> bool:
        with self._tts_lock:
            try:
                if not self.piper or not self.piper.configured:
                    raise RuntimeError(
                        "Piper não está configurado. Execute INSTALAR_VOZ.bat para baixar o modelo PT-BR."
                    )
                ok = self.piper.speak(text)
                self.last_error = self.piper.last_error
                self.last_tts_engine = "Piper"
                return ok
            except Exception as exc:
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

    def test_audio_async(self, callback=None):
        return self.speak_async("Olá! Eu sou a STAR. Minha voz local está pronta.", callback)

    def close(self) -> None:
        # Piper não mantém subprocesso; apenas encerra reprodução em andamento.
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
