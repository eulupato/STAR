"""Gerenciador de voz local da STAR.

Objetivos atuais:
- modo "official" usa SOMENTE a voz oficial Chatterbox;
- não cair silenciosamente para Piper quando a referência/Chatterbox falhar;
- diagnóstico detalha exatamente o componente ausente;
- modo "fast" oferece resposta falada de baixa latência para a interface;
- no Windows, prefere uma voz SAPI PT-BR/feminina quando disponível e usa Piper como fallback.

Nenhum serviço externo de voz é necessário.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path

from core.logging_config import get_logger

log = get_logger("voice")

ROOT = Path(__file__).resolve().parent.parent
VOICE_DIR = ROOT / "voice"
PIPER_DIR = VOICE_DIR / "models" / "piper"
CHATTERBOX_WORKER = VOICE_DIR / "chatterbox_worker.py"
REFERENCE_DIR = VOICE_DIR / "reference"
SUPPORTED_REFERENCE_EXTENSIONS = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")


def prepare_tts_text(text: str) -> str:
    """Remove emojis e símbolos decorativos antes de enviar texto ao TTS.

    A GUI continua exibindo a resposta original; somente a cópia falada é limpa.
    Isso evita leituras literais como "faísca" ou "estrela branca".
    """
    import re

    value = str(text or "")
    emoji_pattern = re.compile(
        "["
        "\\U0001F1E6-\\U0001F1FF"
        "\\U0001F300-\\U0001FAFF"
        "\\u2300-\\u23FF"
        "\\u2600-\\u27BF"
        "\\u2B00-\\u2BFF"
        "\\u200D"
        "\\u20E3"
        "\\uFE0E-\\uFE0F"
        "]+"
    )
    value = emoji_pattern.sub(" ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\s+([,.;:!?])", r"\1", value)
    return value


def _reference_score(path: Path):
    """Prefere referências curtas/compactas e nomes explicitamente STAR."""
    name = path.name.lower()
    explicit = 0 if name.startswith("star_reference") else 1
    short_hint = 0 if any(token in name for token in ("35s", "30s", "short", "curta")) else 1
    try:
        size = path.stat().st_size
    except OSError:
        size = 10**18
    return (explicit, short_hint, size, name)


def _resolve_reference_path() -> Path:
    """Resolve a referência oficial sem depender do nome original do arquivo.

    Ordem:
    1. STAR_VOICE_REFERENCE / VOICE_REFERENCE se existir;
    2. star_reference.* em voice/reference;
    3. qualquer áudio local em voice/reference, escolhendo de forma determinística.

    O áudio continua privado e não é versionado.
    """
    try:
        from config import VOICE_REFERENCE
    except Exception:
        VOICE_REFERENCE = "voice/reference/star_reference.mp3"

    raw = os.getenv("STAR_VOICE_REFERENCE", VOICE_REFERENCE).strip()
    configured = Path(raw).expanduser()
    if not configured.is_absolute():
        configured = ROOT / configured
    configured = configured.resolve()
    if configured.exists():
        return configured

    if REFERENCE_DIR.exists():
        named = []
        all_audio = []
        for path in REFERENCE_DIR.iterdir():
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_REFERENCE_EXTENSIONS:
                continue
            all_audio.append(path.resolve())
            if path.stem.lower() == "star_reference":
                named.append(path.resolve())

        if named:
            return sorted(named, key=_reference_score)[0]
        if all_audio:
            return sorted(all_audio, key=_reference_score)[0]

    return configured


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
    """Piper PT-BR para o modo rápido explicitamente escolhido."""

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
    """Voz oficial da STAR via worker persistente do Chatterbox."""

    def __init__(self, reference_path: Path | None = None):
        self.reference_path = Path(reference_path or _resolve_reference_path()).resolve()
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
    def missing_components(self) -> list[str]:
        missing = []
        if not self.python_path.exists():
            missing.append(f"ambiente Chatterbox ausente: {self.python_path}")
        if not self.worker_path.exists():
            missing.append(f"worker ausente: {self.worker_path}")
        if not self.reference_path.exists():
            missing.append(f"referência de voz ausente: {self.reference_path}")
        return missing

    @property
    def configured(self) -> bool:
        return not self.missing_components

    @property
    def status_message(self) -> str:
        if self.configured:
            return "configurada"
        return "; ".join(self.missing_components)

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
        except Exception as exc:
            log.debug("Falha ao limpar processo de voz: %s", exc)

    def cancel(self) -> None:
        self._cleanup_process()

    def _start(self) -> None:
        if self.ready:
            return
        if not self.configured:
            raise RuntimeError(
                "Voz oficial não configurada: " + self.status_message
            )

        with self._start_lock:
            if self.ready:
                return

            self._cleanup_process()
            creationflags = (
                getattr(subprocess, "CREATE_NO_WINDOW", 0)
                if os.name == "nt"
                else 0
            )
            env = os.environ.copy()
            env["STAR_VOICE_REFERENCE"] = str(self.reference_path)

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
                env=env,
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
                        raise RuntimeError(
                            payload.get("error") or "Falha ao carregar Chatterbox."
                        )

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
                raise RuntimeError(
                    payload.get("error") or "Falha ao gerar voz oficial."
                )
            return Path(payload["path"])

    @staticmethod
    def _play_wav(
        path: Path,
        cancel_event: threading.Event | None = None,
    ) -> bool:
        import numpy as np
        import sounddevice as sd
        import soundfile as sf

        data, sample_rate = sf.read(
            str(path),
            dtype="float32",
            always_2d=True,
        )
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
                chunk = np.asarray(
                    data[start:start + block],
                    dtype=np.float32,
                )
                if chunk.size:
                    stream.write(chunk)
        return True

    def speak(
        self,
        text: str,
        cancel_event: threading.Event | None = None,
    ) -> bool:
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
                except OSError as exc:
                    log.debug("Falha ao remover áudio temporário: %s", exc)

    def close(self) -> None:
        process = self._process
        if process is not None and process.poll() is None:
            try:
                if process.stdin is not None:
                    process.stdin.write(
                        json.dumps({"command": "shutdown"}) + "\n"
                    )
                    process.stdin.flush()
                    process.wait(timeout=1.0)
            except Exception:
                self._cleanup_process()

        self._process = None
        self._ready = False


class WindowsFallbackTTS:
    """TTS local rápido via Windows SAPI/pyttsx3.

    O motor é criado dentro da thread que fala para evitar reutilizar objetos
    COM/SAPI entre threads diferentes. Quando possível, prioriza uma voz
    portuguesa feminina instalada no Windows.
    """

    FEMALE_HINTS = ("maria", "francisca", "helena", "female", "feminina")

    def __init__(self):
        self.engine = None
        self.voice_name = None
        self.last_error = None
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        try:
            import pyttsx3  # noqa: F401
            return True
        except Exception:
            return False

    @staticmethod
    def _voice_text(voice) -> str:
        parts = [
            str(getattr(voice, "id", "") or ""),
            str(getattr(voice, "name", "") or ""),
            str(getattr(voice, "gender", "") or ""),
        ]
        for lang in getattr(voice, "languages", []) or []:
            if isinstance(lang, bytes):
                try:
                    lang = lang.decode("utf-8", errors="ignore")
                except Exception:
                    lang = str(lang)
            parts.append(str(lang))
        return " ".join(parts).lower()

    @classmethod
    def _voice_score(cls, voice):
        text = cls._voice_text(voice)
        is_pt = any(token in text for token in ("pt-br", "pt_br", "portuguese", "português", "brazil"))
        is_female = (
            "female" in text
            or "feminina" in text
            or any(hint in text for hint in cls.FEMALE_HINTS)
        )
        if is_pt and is_female:
            rank = 0
        elif is_female:
            rank = 1
        elif is_pt:
            rank = 2
        else:
            rank = 3
        return (rank, str(getattr(voice, "name", "") or getattr(voice, "id", "")))

    def _configure_engine(self, engine):
        engine.setProperty("rate", 185)
        engine.setProperty("volume", 1.0)
        voices = list(engine.getProperty("voices") or [])
        if voices:
            chosen = sorted(voices, key=self._voice_score)[0]
            engine.setProperty("voice", chosen.id)
            self.voice_name = str(getattr(chosen, "name", "") or chosen.id)
        else:
            self.voice_name = "voz padrão do Windows"

    def cancel(self) -> None:
        engine = self.engine
        if engine is not None:
            try:
                engine.stop()
            except Exception as exc:
                log.debug("Falha não crítica no backend de voz: %s", exc)

    def speak(
        self,
        text: str,
        cancel_event: threading.Event | None = None,
    ) -> bool:
        if cancel_event is not None and cancel_event.is_set():
            self.last_error = "cancelled"
            return False

        try:
            import pyttsx3

            with self._lock:
                engine = pyttsx3.init()
                self.engine = engine
                self._configure_engine(engine)

                if cancel_event is not None and cancel_event.is_set():
                    self.last_error = "cancelled"
                    return False

                engine.say(str(text))
                engine.runAndWait()

                if cancel_event is not None and cancel_event.is_set():
                    self.last_error = "cancelled"
                    return False

                self.last_error = None
                return True
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            return False
        finally:
            engine = self.engine
            self.engine = None
            if engine is not None:
                try:
                    engine.stop()
                except Exception:
                    pass


class VoiceManager:
    """Orquestra STT e TTS locais.

    official:
        Chatterbox + referência local.
        Se falhar, ERRO VISÍVEL por padrão. Não usa voz genérica escondida.

    fast:
        Windows SAPI de baixa latência quando disponível; Piper PT-BR como fallback.
    """

    def __init__(self):
        try:
            from config import VOICE_FALLBACK_ON_ERROR, VOICE_MODE
        except Exception:
            VOICE_MODE = "official"
            VOICE_FALLBACK_ON_ERROR = False

        self.mode = os.getenv(
            "STAR_VOICE_MODE",
            VOICE_MODE,
        ).strip().lower()

        if self.mode not in {"official", "fast"}:
            self.mode = "official"

        env_fallback = os.getenv("STAR_VOICE_FALLBACK_ON_ERROR")
        if env_fallback is None:
            self.fallback_on_error = bool(VOICE_FALLBACK_ON_ERROR)
        else:
            self.fallback_on_error = env_fallback.strip().lower() in {
                "1", "true", "yes", "on"
            }

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
        if self.mode == "official":
            return self.official.configured
        return self.piper.configured or self.fallback.configured

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
        if self.mode == "official":
            if self.official.configured:
                return f"Voz oficial STAR (Chatterbox local • {self.official.reference_path.name})"
            return "Voz oficial INDISPONÍVEL — " + self.official.status_message

        if self.fallback.configured:
            suffix = f" • {self.fallback.voice_name}" if self.fallback.voice_name else ""
            return f"Windows SAPI (modo rápido{suffix})"
        if self.piper.configured:
            return "Piper PT-BR (modo rápido)"
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

        if self.mode == "official":
            if not self.official.configured:
                errors.append(
                    "Voz oficial: " + self.official.status_message
                )
            else:
                try:
                    self.official.warmup()
                except Exception as exc:
                    errors.append(
                        f"Voz oficial: {type(exc).__name__}: {exc}"
                    )

            if self.fallback_on_error:
                try:
                    self.piper.warmup()
                except Exception as exc:
                    errors.append(f"Piper: {type(exc).__name__}: {exc}")
        else:
            try:
                self.piper.warmup()
            except Exception as exc:
                errors.append(f"Piper: {type(exc).__name__}: {exc}")

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

        try:
            self.fallback.cancel()
        except Exception:
            pass

        if self._speaking.is_set():
            self.official.cancel()

    def _speak_fast(
        self,
        text: str,
        event: threading.Event,
    ) -> bool:
        # No Windows, SAPI costuma responder quase imediatamente e permite
        # escolher uma voz PT-BR/feminina instalada. Piper permanece como
        # fallback determinístico se o SAPI não estiver disponível.
        if self.fallback.configured and self.fallback.speak(text, event):
            self.last_error = None
            label = self.fallback.voice_name or "voz local"
            self.last_tts_engine = f"Windows SAPI — {label}"
            return True

        if event.is_set() or self.fallback.last_error == "cancelled":
            self.last_error = "Fala cancelada."
            return False

        sapi_error = self.fallback.last_error

        if self.piper.configured and self.piper.speak(text, event):
            self.last_error = None
            self.last_tts_engine = "Piper — modo rápido"
            return True

        if event.is_set() or self.piper.last_error == "cancelled":
            self.last_error = "Fala cancelada."
            return False

        self.last_tts_engine = "indisponível"
        self.last_error = (
            sapi_error
            or self.piper.last_error
            or "Windows SAPI e Piper falharam."
        )
        return False

    def speak(
        self,
        text: str,
        cancel_event: threading.Event | None = None,
    ) -> bool:
        event = cancel_event or self._current_cancel_event()
        spoken_text = prepare_tts_text(text)

        # A GUI mantém os emojis; apenas o áudio é higienizado.
        if not spoken_text:
            self.last_error = None
            self.last_tts_engine = "nenhuma fala necessária"
            return True

        with self._tts_lock:
            if event.is_set():
                self.last_error = "Fala cancelada."
                return False

            if self.mode == "fast":
                return self._speak_fast(spoken_text, event)

            if not self.official.configured:
                self.last_tts_engine = "voz oficial indisponível"
                self.last_error = (
                    "A STAR está em modo de voz oficial, mas: "
                    + self.official.status_message
                    + ". Piper não foi usado automaticamente."
                )
                if self.fallback_on_error:
                    return self._speak_fast(spoken_text, event)
                return False

            if self.official.speak(spoken_text, event):
                self.last_error = None
                self.last_tts_engine = "Chatterbox — voz oficial STAR"
                return True

            if event.is_set() or self.official.last_error == "cancelled":
                self.last_error = "Fala cancelada."
                return False

            official_error = self.official.last_error or "erro desconhecido"
            self.last_tts_engine = "voz oficial falhou"
            self.last_error = (
                "A voz oficial Chatterbox falhou: "
                + official_error
                + ". Piper não foi usado automaticamente."
            )

            if self.fallback_on_error:
                return self._speak_fast(spoken_text, event)
            return False

    def warmup_stt_async(self):
        """Pré-carrega somente o reconhecimento de fala.

        A interface usa este caminho para não gastar minutos carregando
        Chatterbox durante o startup.
        """
        def run():
            try:
                self.stt.warmup()
            except Exception as exc:
                self.last_error = f"STT: {type(exc).__name__}: {exc}"

        thread = threading.Thread(
            target=run,
            daemon=True,
            name="STAR-STTWarmup",
        )
        thread.start()
        return thread

    def warmup_async(self):
        """Warmup completo, mantido para diagnósticos/testes explícitos."""
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

        thread = threading.Thread(
            target=run,
            daemon=True,
            name="STAR-TTS",
        )
        thread.start()
        return thread

    def test_audio_async(self, callback=None):
        """Testa o modo atualmente selecionado."""
        return self.speak_async(
            "Olá! Eu sou a STAR. Este é o teste da minha voz.",
            callback,
        )

    def test_official_audio_async(self, callback=None):
        """Testa explicitamente o Chatterbox, mesmo se o chat estiver em modo rápido."""
        self.cancel_speech()
        event = self._current_cancel_event()

        def run():
            self._speaking.set()
            try:
                with self._tts_lock:
                    if not self.official.configured:
                        ok = False
                        error = "Voz oficial não configurada: " + self.official.status_message
                        self.last_tts_engine = "voz oficial indisponível"
                    else:
                        ok = self.official.speak(
                            "Olá! Eu sou a STAR. Este é o teste da minha voz oficial.",
                            event,
                        )
                        error = self.official.last_error
                        if ok:
                            self.last_tts_engine = "Chatterbox — voz oficial STAR"
            finally:
                self._speaking.clear()

            self.last_error = error
            if callback:
                callback(ok, error)

        thread = threading.Thread(
            target=run,
            daemon=True,
            name="STAR-OfficialVoiceTest",
        )
        thread.start()
        return thread

    def close(self):
        self.cancel_speech()
        try:
            self.official.close()
        except Exception:
            pass
