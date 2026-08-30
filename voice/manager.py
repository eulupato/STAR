"""Gerenciador de voz local da STAR V1.9 FINAL.

Pipeline:
  microfone -> faster-whisper tiny -> STAR Core -> voz oficial Chatterbox
                                                   -> Piper/SAPI fallback

A voz oficial usa a referência local da STAR quando o Chatterbox está preparado.
Piper permanece como fallback rápido. Nenhum serviço externo de voz é necessário.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICE_DIR = ROOT / "voice"
PIPER_DIR = VOICE_DIR / "models" / "piper"
REFERENCE_PATH = VOICE_DIR / "reference" / "star_reference.mp3"
CHATTERBOX_WORKER = VOICE_DIR / "chatterbox_worker.py"


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
                text = " ".join(
                    segment.text.strip()
                    for segment in segments
                    if segment.text.strip()
                ).strip()
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
    """Piper PT-BR carregado uma vez e reproduzido em streaming."""

    def __init__(self):
        self.voice = None
        self.last_error = None
        self.last_elapsed = 0.0
        self.model_path = self._find_model()
        self._load_lock = threading.Lock()

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
        return (
            self.model_path.exists()
            and self.model_path.with_suffix(".onnx.json").exists()
        )

    def _load(self) -> None:
        if self.voice is not None:
            return
        with self._load_lock:
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

            current = []
            current_size = 0
            for word in piece.split():
                extra = len(word) + (1 if current else 0)
                if current and current_size + extra > max_chars:
                    result.append(" ".join(current))
                    current = []
                    current_size = 0
                    extra = len(word)
                current.append(word)
                current_size += extra
            if current:
                result.append(" ".join(current))
        return result

    def speak(self, text: str, cancel_event: threading.Event | None = None) -> bool:
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
                if cancel_event is not None and cancel_event.is_set():
                    self.last_error = "cancelled"
                    return False

                stream = None
                channels = 1
                try:
                    for chunk in self.voice.synthesize(part, syn_config=cfg):
                        if cancel_event is not None and cancel_event.is_set():
                            self.last_error = "cancelled"
                            return False

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


class ChatterboxOfficialTTS:
    """Voz oficial da STAR via worker persistente do Chatterbox.

    O modelo roda no .voice_venv (Python 3.11) e usa somente a referência local
    voice/reference/star_reference.mp3. O áudio de referência não é versionado.
    """

    def __init__(self):
        self.reference_path = REFERENCE_PATH
        self.worker_path = CHATTERBOX_WORKER
        self.python_path = self._find_python()
        self.last_error = None
        self.last_elapsed = 0.0
        self._process = None
        self._ready = False
        self._start_lock = threading.Lock()
        self._io_lock = threading.Lock()

    @staticmethod
    def _find_python() -> Path:
        candidates = [
            ROOT / ".voice_venv" / "Scripts" / "python.exe",
            ROOT / ".voice_venv" / "bin" / "python",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    @property
    def configured(self) -> bool:
        return (
            self.python_path.exists()
            and self.worker_path.exists()
            and self.reference_path.exists()
        )

    @property
    def ready(self) -> bool:
        return bool(
            self._ready
            and self._process is not None
            and self._process.poll() is None
        )

    def _cleanup_process(self) -> None:
        process = self._process
        self._process = None
        self._ready = False
        if process is None:
            return
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=0.8)
                except subprocess.TimeoutExpired:
                    process.kill()
        except Exception:
            pass

    def cancel(self) -> None:
        self._cleanup_process()

    def _start(self) -> None:
        if self.ready:
            return
        if not self.configured:
            raise RuntimeError(
                "Voz oficial não configurada. Verifique .voice_venv e "
                "voice/reference/star_reference.mp3."
            )

        with self._start_lock:
            if self.ready:
                return

            self._cleanup_process()
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            self._process = subprocess.Popen(
                [str(self.python_path), str(self.worker_path)],
                cwd=str(ROOT),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creationflags,
            )

            if self._process.stdout is None:
                raise RuntimeError("Worker Chatterbox iniciou sem saída de protocolo.")

            while True:
                line = self._process.stdout.readline()
                if not line:
                    code = self._process.poll()
                    raise RuntimeError(
                        f"Worker Chatterbox encerrou antes de ficar pronto (código {code})."
                    )
                line = line.strip()
                if line == "STAR_CHATTERBOX_MODEL_READY":
                    self._ready = True
                    self.last_error = None
                    return
                if line.startswith("STAR_CHATTERBOX_RESULT="):
                    payload = json.loads(line.split("=", 1)[1])
                    if not payload.get("ok"):
                        raise RuntimeError(payload.get("error") or "Falha ao carregar Chatterbox.")

    def warmup(self) -> None:
        self._start()

    def _generate(self, text: str) -> Path:
        self._start()
        process = self._process
        if process is None or process.stdin is None or process.stdout is None:
            raise RuntimeError("Worker Chatterbox indisponível.")

        request = {
            "text": text,
            "exaggeration": 0.5,
            "cfg_weight": 0.35,
            "temperature": 0.75,
        }
        process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
        process.stdin.flush()

        while True:
            line = process.stdout.readline()
            if not line:
                code = process.poll()
                raise RuntimeError(
                    f"Worker Chatterbox encerrou durante a síntese (código {code})."
                )
            line = line.strip()
            if not line.startswith("STAR_CHATTERBOX_RESULT="):
                continue
            payload = json.loads(line.split("=", 1)[1])
            if not payload.get("ok"):
                raise RuntimeError(payload.get("error") or "Falha ao gerar voz oficial.")
            return Path(payload["path"])

    @staticmethod
    def _play_wav(path: Path, cancel_event: threading.Event | None = None) -> bool:
        import numpy as np
        import sounddevice as sd
        import soundfile as sf

        data, sample_rate = sf.read(str(path), dtype="float32", always_2d=True)
        channels = int(data.shape[1]) if data.ndim == 2 else 1
        block = 4096

        with sd.OutputStream(
            samplerate=int(sample_rate),
            channels=channels,
            dtype="float32",
        ) as stream:
            for start in range(0, len(data), block):
                if cancel_event is not None and cancel_event.is_set():
                    return False
                chunk = np.asarray(data[start:start + block], dtype=np.float32)
                if chunk.size:
                    stream.write(chunk)
        return True

    def speak(self, text: str, cancel_event: threading.Event | None = None) -> bool:
        text = str(text).strip()
        if not text:
            return True

        started = time.perf_counter()
        output_path = None
        try:
            if cancel_event is not None and cancel_event.is_set():
                self.last_error = "cancelled"
                return False

            with self._io_lock:
                output_path = self._generate(text)
                if cancel_event is not None and cancel_event.is_set():
                    self.last_error = "cancelled"
                    return False

                ok = self._play_wav(output_path, cancel_event)
                if not ok:
                    self.last_error = "cancelled"
                    return False

            self.last_elapsed = time.perf_counter() - started
            self.last_error = None
            return True
        except Exception as exc:
            self.last_elapsed = time.perf_counter() - started
            self.last_error = f"{type(exc).__name__}: {exc}"
            self._cleanup_process()
            return False
        finally:
            if output_path is not None:
                try:
                    output_path.unlink(missing_ok=True)
                except Exception:
                    pass

    def close(self) -> None:
        process = self._process
        if process is not None and process.poll() is None:
            try:
                if process.stdin is not None:
                    process.stdin.write(json.dumps({"command": "shutdown"}) + "\n")
                    process.stdin.flush()
                    process.wait(timeout=1.0)
            except Exception:
                self._cleanup_process()
        self._process = None
        self._ready = False


class WindowsFallbackTTS:
    """Último fallback local via SAPI/pyttsx3."""

    def __init__(self):
        self.engine = None
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        try:
            import pyttsx3  # noqa: F401
            return True
        except Exception:
            return False

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
    """Orquestra STT e TTS locais da STAR.

    Modo padrão: official.
      1. Chatterbox + referência da STAR
      2. Piper PT-BR como fallback rápido
      3. Windows SAPI como último fallback

    Defina STAR_VOICE_MODE=fast para forçar Piper quando a prioridade for latência.
    """

    def __init__(self):
        try:
            from config import VOICE_MODE
        except Exception:
            VOICE_MODE = "official"

        self.mode = os.getenv("STAR_VOICE_MODE", VOICE_MODE).strip().lower()
        if self.mode not in {"official", "fast"}:
            self.mode = "official"

        self.stt = LocalSpeechToText()
        self.official = ChatterboxOfficialTTS()
        self.piper = FastPiperTTS()
        self.fallback = WindowsFallbackTTS()

        self.last_error = None
        self.last_tts_engine = "não executado"
        self._tts_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._cancel_event = threading.Event()
        self._speaking = threading.Event()

    @property
    def configured(self) -> bool:
        return (
            self.official.configured
            or self.piper.configured
            or self.fallback.configured
        )

    @property
    def piper_configured(self) -> bool:
        return self.piper.configured

    @property
    def official_voice_configured(self) -> bool:
        return self.official.configured

    @property
    def stt_configured(self) -> bool:
        return self.stt.configured

    @property
    def tts_description(self) -> str:
        if self.mode == "official" and self.official.configured:
            return "Voz oficial STAR (Chatterbox local)"
        if self.piper.configured:
            return "Piper PT-BR (fallback rápido)"
        if self.fallback.configured:
            return "Windows SAPI (fallback)"
        return "TTS indisponível"

    def set_voice_mode(self, mode: str) -> None:
        mode = str(mode).strip().lower()
        if mode not in {"official", "fast"}:
            raise ValueError("Modo de voz deve ser 'official' ou 'fast'.")
        self.cancel_speech()
        self.mode = mode

    def warmup(self) -> None:
        errors = []
        try:
            self.stt.warmup()
        except Exception as exc:
            errors.append(f"STT: {type(exc).__name__}: {exc}")

        try:
            self.piper.warmup()
        except Exception as exc:
            errors.append(f"Piper: {type(exc).__name__}: {exc}")

        if self.mode == "official" and self.official.configured:
            try:
                self.official.warmup()
            except Exception as exc:
                errors.append(f"Voz oficial: {type(exc).__name__}: {exc}")

        self.last_error = " | ".join(errors) if errors else None

    def transcribe(self, audio_path: Path) -> str:
        return self.stt.transcribe(audio_path)

    def _current_cancel_event(self) -> threading.Event:
        with self._state_lock:
            return self._cancel_event

    def cancel_speech(self) -> None:
        with self._state_lock:
            previous = self._cancel_event
            previous.set()
            self._cancel_event = threading.Event()

        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass

        if self._speaking.is_set():
            self.official.cancel()

    def speak(self, text: str, cancel_event: threading.Event | None = None) -> bool:
        event = cancel_event or self._current_cancel_event()

        with self._tts_lock:
            if event.is_set():
                self.last_error = "Fala cancelada."
                return False

            if self.mode == "official" and self.official.configured:
                if self.official.speak(text, event):
                    self.last_error = None
                    self.last_tts_engine = "Chatterbox — voz oficial STAR"
                    return True
                if event.is_set() or self.official.last_error == "cancelled":
                    self.last_error = "Fala cancelada."
                    return False
                official_error = self.official.last_error
            else:
                official_error = None

            if self.piper.configured and self.piper.speak(text, event):
                self.last_error = None
                self.last_tts_engine = "Piper — fallback rápido"
                return True
            if event.is_set() or self.piper.last_error == "cancelled":
                self.last_error = "Fala cancelada."
                return False

            piper_error = self.piper.last_error
            if self.fallback.speak(text):
                self.last_error = None
                self.last_tts_engine = "Windows SAPI — fallback"
                return True

            self.last_tts_engine = "indisponível"
            self.last_error = (
                official_error
                or piper_error
                or "Voz oficial, Piper e Windows SAPI falharam."
            )
            return False

    def warmup_async(self):
        thread = threading.Thread(
            target=self.warmup,
            daemon=True,
            name="STAR-VoiceWarmup",
        )
        thread.start()
        return thread

    def speak_async(self, text: str, callback=None):
        self.cancel_speech()
        event = self._current_cancel_event()

        def run():
            self._speaking.set()
            try:
                ok = self.speak(text, event)
                error = self.last_error
            finally:
                self._speaking.clear()
            if callback:
                callback(ok, error)

        thread = threading.Thread(target=run, daemon=True, name="STAR-TTS")
        thread.start()
        return thread

    def test_audio_async(self, callback=None):
        return self.speak_async(
            "Olá! Eu sou a STAR. Esta é a minha voz oficial.",
            callback,
        )

    def close(self):
        self.cancel_speech()
        try:
            self.official.close()
        except Exception:
            pass
