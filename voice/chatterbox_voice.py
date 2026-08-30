"""Motor local de voz da STAR usando Chatterbox Multilingual."""

from pathlib import Path
import threading
import time

ROOT = Path(__file__).resolve().parent.parent

REF = ROOT / "voice" / "reference" / "star_reference.mp3"
OUT = ROOT / "voice" / "output"


class ChatterboxVoice:

    def __init__(self):
        self.model = None
        self.device = None
        self.last_error = None
        self._lock = threading.Lock()

    def _load(self):
        """Carrega o modelo apenas uma vez."""

        if self.model is not None:
            return

        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        # Seleciona GPU NVIDIA caso disponível.
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        print(f"🎙️ STAR Voice Engine usando: {self.device}")

        # API compatível com Chatterbox 0.1.7
        self.model = ChatterboxMultilingualTTS.from_pretrained(
            self.device
        )

        print("🎙️ Chatterbox carregado com sucesso.")

    @property
    def configured(self):
        """Verifica se existe um áudio de referência."""

        return REF.exists()

    def synthesize(self, text):
        """Gera um arquivo WAV usando a voz de referência."""

        if not text or not str(text).strip():
            raise ValueError("Não é possível sintetizar um texto vazio.")

        if not self.configured:
            raise RuntimeError(
                f"Áudio de referência não encontrado: {REF}"
            )

        with self._lock:

            self._load()

            OUT.mkdir(
                parents=True,
                exist_ok=True
            )

            import torchaudio as ta

            print("🎙️ Gerando voz da STAR...")

            wav = self.model.generate(
                str(text),
                language_id="pt",
                audio_prompt_path=str(REF)
            )

            path = OUT / (
                f"star_{int(time.time() * 1000)}.wav"
            )

            ta.save(
                str(path),
                wav,
                self.model.sr
            )

            print(f"🎙️ Áudio gerado: {path}")

            return path

    def speak(self, text):
        """Gera e reproduz a voz."""

        try:

            path = self.synthesize(text)

            import pygame

            if not pygame.mixer.get_init():

                pygame.mixer.init()

            pygame.mixer.music.load(str(path))

            pygame.mixer.music.set_volume(1.0)

            pygame.mixer.music.play()

            print("🔊 STAR está falando...")

            while pygame.mixer.music.get_busy():

                pygame.time.Clock().tick(30)

            self.last_error = None

            return True

        except Exception as e:

            self.last_error = (
                f"{type(e).__name__}: {e}"
            )

            print(
                f"❌ Erro no sistema de voz: "
                f"{self.last_error}"
            )

            return False

    def speak_async(self, text, callback=None):
        """Executa a fala em uma thread separada."""

        def run():

            ok = self.speak(text)

            if callback:

                callback(
                    ok,
                    self.last_error
                )

        thread = threading.Thread(
            target=run,
            daemon=True
        )

        thread.start()

        return thread