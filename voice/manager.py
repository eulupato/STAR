"""Gerenciador único de voz da STAR.

STT: faster-whisper local no ambiente principal.
TTS: Chatterbox local em .voice_venv, geração de WAV.
Playback: sounddevice no processo principal.
Não depende de serviços de voz externos.
"""
from __future__ import annotations

import os
import subprocess
import threading
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICE_PYTHON = ROOT / ".voice_venv" / "Scripts" / "python.exe"
REFERENCE = ROOT / "voice" / "reference" / "star_reference.mp3"
OUTPUT = ROOT / "voice" / "output"


class LocalSpeechToText:
    """Reconhecimento de fala local com faster-whisper."""

    def __init__(self, model_size: str | None = None):
        self.model_size = model_size or os.getenv("STAR_STT_MODEL", "base")
        self.model = None
        self.last_error = None
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
            cpu_threads=max(1, min(4, os.cpu_count() or 2)),
            num_workers=1,
        )

    def transcribe(self, audio_path: Path) -> str:
        if not audio_path or not Path(audio_path).exists():
            raise RuntimeError("Arquivo de áudio da gravação não encontrado.")
        with self._lock:
            try:
                self._load()
                segments, _info = self.model.transcribe(
                    str(audio_path),
                    language="pt",
                    beam_size=3,
                    vad_filter=True,
                    condition_on_previous_text=False,
                )
                text = " ".join(seg.text.strip() for seg in segments if seg.text.strip()).strip()
                if not text:
                    raise RuntimeError("Não consegui entender a fala.")
                self.last_error = None
                return text
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
                raise


class ChatterboxTTS:
    """Geração local persistente via worker Chatterbox."""

    def __init__(self):
        self.last_error = None
        self.process = None
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return VOICE_PYTHON.exists() and REFERENCE.exists()

    def _start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        if not self.configured:
            raise RuntimeError(
                "Chatterbox não configurado. Execute INSTALAR_CHATTERBOX.bat "
                "e mantenha voice/reference/star_reference.mp3 disponível."
            )
        self.process = subprocess.Popen(
            [str(VOICE_PYTHON), str(ROOT / "voice" / "chatterbox_worker.py")],
            cwd=str(ROOT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        deadline = time.time() + 300
        while time.time() < deadline:
            line = self.process.stdout.readline() if self.process.stdout else ""
            if not line:
                if self.process.poll() is not None:
                    raise RuntimeError(self._worker_error())
                continue
            if line.startswith("STAR_CHATTERBOX_MODEL_READY"):
                return
            if line.startswith("STAR_CHATTERBOX_RESULT="):
                data = json.loads(line.split("=", 1)[1])
                raise RuntimeError(data.get("error") or "Falha ao inicializar Chatterbox.")
        raise TimeoutError("Chatterbox demorou mais de 5 minutos para inicializar.")

    def _worker_error(self) -> str:
        err = ""
        if self.process is not None and self.process.stderr:
            try:
                err = self.process.stderr.read()[-2000:]
            except Exception:
                pass
        return err or "O worker do Chatterbox terminou sem informar o motivo."

    def synthesize(self, text: str) -> Path:
        if not str(text).strip():
            raise ValueError("Texto vazio para síntese.")
        with self._lock:
            self._start()
            OUTPUT.mkdir(parents=True, exist_ok=True)
            name = f"star_{time.time_ns()}.wav"
            request = {
                "text": str(text),
                "output": name,
                "exaggeration": 0.5,
                "cfg_weight": 0.4,
                "temperature": 0.8,
            }
            assert self.process is not None and self.process.stdin and self.process.stdout
            self.process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
            self.process.stdin.flush()
            deadline = time.time() + 300
            while time.time() < deadline:
                line = self.process.stdout.readline()
                if not line:
                    if self.process.poll() is not None:
                        raise RuntimeError(self._worker_error())
                    continue
                if not line.startswith("STAR_CHATTERBOX_RESULT="):
                    continue
                data = json.loads(line.split("=", 1)[1])
                if not data.get("ok"):
                    raise RuntimeError(data.get("error") or "Chatterbox falhou ao gerar a voz.")
                path = Path(data["path"])
                if not path.exists() or path.stat().st_size < 100:
                    raise RuntimeError("Chatterbox informou sucesso, mas o WAV não existe ou está vazio.")
                self.last_error = None
                return path
            raise TimeoutError("Chatterbox demorou mais de 5 minutos para gerar a fala.")

    def close(self) -> None:
        with self._lock:
            if self.process is None:
                return
            try:
                if self.process.stdin:
                    self.process.stdin.write(json.dumps({"command": "shutdown"}) + "\n")
                    self.process.stdin.flush()
            except Exception:
                pass
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process = None


class VoiceManager:
    """Orquestra STT + TTS + reprodução local."""

    def __init__(self):
        self.stt = LocalSpeechToText()
        self.tts = ChatterboxTTS()
        self.last_error = None
        self._play_lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return self.tts.configured

    @property
    def stt_configured(self) -> bool:
        return self.stt.configured

    def transcribe(self, audio_path: Path) -> str:
        return self.stt.transcribe(audio_path)

    def speak(self, text: str) -> bool:
        path = None
        try:
            path = self.tts.synthesize(text)
            import sounddevice as sd
            import soundfile as sf
            data, rate = sf.read(str(path), dtype="float32")
            if getattr(data, "size", 0) == 0:
                raise RuntimeError("O WAV gerado não contém amostras.")
            with self._play_lock:
                sd.stop()
                sd.play(data, rate)
                sd.wait()
            self.last_error = None
            return True
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            return False
        finally:
            if path:
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass

    def speak_async(self, text: str, callback=None):
        def run():
            ok = self.speak(text)
            if callback:
                callback(ok, self.last_error)
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

    def test_audio_async(self, callback=None):
        return self.speak_async(
            "Olá! Eu sou a STAR. Minha voz local está funcionando.",
            callback,
        )

    def close(self) -> None:
        self.tts.close()
