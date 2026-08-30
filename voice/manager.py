"""Sistema de voz local da STAR.

Entrada: faster-whisper local.
Saída: Chatterbox local em .voice_venv.
Reprodução: sounddevice no .venv principal.
Nenhum serviço externo de voz é necessário.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICE_PYTHON = ROOT / ".voice_venv" / "Scripts" / "python.exe"
REFERENCE = ROOT / "voice" / "reference" / "star_reference.mp3"
OUTPUT = ROOT / "voice" / "output"


class LocalSpeechToText:
    """Reconhecimento local em português usando faster-whisper."""

    def __init__(self, model_size: str = "base"):
        self.model_size = os.getenv("STAR_STT_MODEL", model_size)
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

    def _load(self):
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
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise RuntimeError(f"Gravação não encontrada: {audio_path}")
        with self._lock:
            try:
                self._load()
                segments, _ = self.model.transcribe(
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
    """Worker persistente do Chatterbox, somente para geração de WAV."""

    def __init__(self):
        self.process = None
        self.last_error = None
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return VOICE_PYTHON.exists() and REFERENCE.exists()

    def _worker_error(self) -> str:
        if not self.process:
            return "Worker não iniciado."
        return "O worker do Chatterbox foi encerrado sem confirmar a geração do áudio."

    def _start(self):
        if self.process is not None and self.process.poll() is None:
            return
        if not self.configured:
            raise RuntimeError("Chatterbox não configurado. Execute INSTALAR_CHATTERBOX.bat e mantenha a referência da voz.")
        self.process = subprocess.Popen(
            [str(VOICE_PYTHON), str(ROOT / "voice" / "chatterbox_worker.py")],
            cwd=str(ROOT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
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
            line = line.rstrip()
            if line == "STAR_CHATTERBOX_MODEL_READY":
                return
            if line.startswith("STAR_CHATTERBOX_RESULT="):
                data = json.loads(line.split("=", 1)[1])
                raise RuntimeError(data.get("error") or "Falha ao carregar o Chatterbox.")
        raise TimeoutError("Chatterbox levou mais de 5 minutos para carregar.")

    def synthesize(self, text: str) -> Path:
        if not str(text).strip():
            raise ValueError("Texto vazio para síntese.")
        with self._lock:
            self._start()
            OUTPUT.mkdir(parents=True, exist_ok=True)
            name = f"star_{time.time_ns()}.wav"
            request = {"text": str(text), "output": name, "exaggeration": 0.5, "cfg_weight": 0.35, "temperature": 0.75}
            if not self.process or not self.process.stdin or not self.process.stdout:
                raise RuntimeError("Worker do Chatterbox não está disponível.")
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
                    raise RuntimeError(data.get("error") or "Chatterbox falhou.")
                path = Path(data.get("path", ""))
                if not path.exists() or path.stat().st_size < 1000:
                    raise RuntimeError("O Chatterbox informou sucesso, mas o WAV não está válido.")
                self.last_error = None
                return path
            raise TimeoutError("Chatterbox levou mais de 5 minutos para gerar a fala.")

    def close(self):
        with self._lock:
            if not self.process:
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
    """Pipeline completo: STT local -> STAR -> TTS local -> áudio."""

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
                raise RuntimeError("O áudio gerado não contém amostras.")
            with self._play_lock:
                sd.stop()
                sd.play(data, rate, blocking=True)
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
        return self.speak_async("Olá! Eu sou a STAR. Minha voz local está funcionando.", callback)

    def close(self):
        self.tts.close()
