"""Sistema de voz local da STAR.

STT: faster-whisper no ambiente principal.
TTS: Chatterbox Multilingual em worker persistente no .voice_venv.
Playback: sounddevice no processo principal.
Nenhum serviço externo de voz é usado.
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
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise RuntimeError(f"Gravação não encontrada: {audio_path}")
        with self._lock:
            try:
                self._load()
                segments, _info = self.model.transcribe(
                    str(audio_path),
                    language="pt",
                    beam_size=3,
                    vad_filter=True,
                    condition_on_previous_text=False,
                    temperature=0.0,
                )
                text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
                if not text:
                    raise RuntimeError("Não consegui entender a fala.")
                self.last_error = None
                return text
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
                raise


class ChatterboxTTS:
    """Mantém o Chatterbox vivo em um processo separado e só troca mensagens JSON."""

    def __init__(self):
        self.process = None
        self.last_error = None
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return VOICE_PYTHON.exists() and REFERENCE.exists()

    def _stop(self) -> None:
        process = self.process
        self.process = None
        if process is None:
            return
        try:
            if process.stdin:
                process.stdin.write(json.dumps({"command": "shutdown"}) + "\n")
                process.stdin.flush()
        except Exception:
            pass
        try:
            process.terminate()
            process.wait(timeout=3)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def _start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        if not self.configured:
            raise RuntimeError("Chatterbox não configurado. Execute INSTALAR_VOZ.bat e verifique a referência da voz.")

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

        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            if self.process is None or self.process.poll() is not None:
                raise RuntimeError("O processo do Chatterbox terminou durante a inicialização.")
            line = self.process.stdout.readline() if self.process.stdout else ""
            if not line:
                continue
            line = line.rstrip("\r\n")
            if line == "STAR_CHATTERBOX_MODEL_READY":
                return
            if line.startswith("STAR_CHATTERBOX_RESULT="):
                data = json.loads(line.split("=", 1)[1])
                raise RuntimeError(data.get("error") or "Falha ao carregar o Chatterbox.")

        raise TimeoutError("Chatterbox demorou mais de 5 minutos para carregar.")

    def synthesize(self, text: str) -> Path:
        text = str(text).strip()
        if not text:
            raise ValueError("Texto vazio para síntese.")

        with self._lock:
            for attempt in (1, 2):
                try:
                    self._start()
                    OUTPUT.mkdir(parents=True, exist_ok=True)
                    output_name = f"star_{time.time_ns()}.wav"
                    request = {
                        "text": text,
                        "output": output_name,
                        "exaggeration": 0.5,
                        "cfg_weight": 0.35,
                        "temperature": 0.75,
                    }
                    if not self.process or not self.process.stdin or not self.process.stdout:
                        raise RuntimeError("Worker do Chatterbox não está disponível.")

                    self.process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
                    self.process.stdin.flush()
                    deadline = time.monotonic() + 300
                    while time.monotonic() < deadline:
                        line = self.process.stdout.readline()
                        if not line:
                            if self.process.poll() is not None:
                                raise RuntimeError("O worker do Chatterbox terminou antes da resposta.")
                            continue
                        if not line.startswith("STAR_CHATTERBOX_RESULT="):
                            continue
                        data = json.loads(line.split("=", 1)[1])
                        if not data.get("ok"):
                            raise RuntimeError(data.get("error") or "Chatterbox falhou ao gerar o áudio.")
                        path = Path(data.get("path", ""))
                        if not path.exists() or path.stat().st_size < 1000:
                            raise RuntimeError("O WAV gerado é inexistente ou inválido.")
                        self.last_error = None
                        return path
                    raise TimeoutError("Chatterbox demorou mais de 5 minutos para gerar a fala.")
                except Exception:
                    if attempt == 1:
                        self._stop()
                        continue
                    raise

    def close(self) -> None:
        with self._lock:
            self._stop()


class VoiceManager:
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
            data, rate = sf.read(str(path), dtype="float32", always_2d=False)
            if getattr(data, "size", 0) == 0:
                raise RuntimeError("O WAV gerado não contém amostras.")
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

    def close(self) -> None:
        self.tts.close()
