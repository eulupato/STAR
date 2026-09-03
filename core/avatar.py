from pathlib import Path


class AvatarManager:
    """Gerencia estados visuais do avatar e fallbacks honestos da STAR."""

    VALID_EMOTIONS = {
        "neutral", "happy", "sad", "angry", "surprised",
        "thinking", "confused", "listening", "speaking",
        "curious", "confident",
    }

    EMOTION_INDICATORS = {
        "neutral": "",
        "happy": "😊",
        "sad": "😢",
        "angry": "😠",
        "surprised": "😮",
        "thinking": "💭",
        "confused": "❓",
        "listening": "🎧",
        "speaking": "💬",
        "curious": "🤔",
        "confident": "✨",
    }

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.avatar_dir = self.base_dir / "assets" / "avatar"
        self.current_emotion = "neutral"

    def set_emotion(self, emotion):
        if emotion not in self.VALID_EMOTIONS:
            raise ValueError(f"Emoção inválida: {emotion}")
        self.current_emotion = emotion

    def get_emotion(self):
        return self.current_emotion

    def get_image_path(self):
        return self.avatar_dir / f"{self.current_emotion}.png"

    @staticmethod
    def _valid_image_file(path):
        path = Path(path)
        return path.exists() and path.is_file() and path.stat().st_size > 0

    def image_exists(self):
        return self._valid_image_file(self.get_image_path())

    def get_available_emotions(self):
        return sorted(
            emotion
            for emotion in self.VALID_EMOTIONS
            if self._valid_image_file(self.avatar_dir / f"{emotion}.png")
        )

    def resolve_display_asset(self, emotion=None, fallback_path=None):
        """Retorna (imagem, indicador) sem fingir que um sprite ausente existe.

        Se houver sprite específico, o indicador fica vazio. Caso contrário,
        usa a skin/fallback real e adiciona um símbolo visual da emoção.
        """
        emotion = str(emotion or self.current_emotion)
        if emotion not in self.VALID_EMOTIONS:
            emotion = "neutral"

        specific = self.avatar_dir / f"{emotion}.png"
        if (
            emotion == "neutral"
            and fallback_path
            and self._valid_image_file(fallback_path)
        ):
            return Path(fallback_path), ""

        if self._valid_image_file(specific):
            return specific, ""

        if fallback_path and self._valid_image_file(fallback_path):
            return Path(fallback_path), self.EMOTION_INDICATORS.get(emotion, "")

        neutral = self.avatar_dir / "neutral.png"
        if self._valid_image_file(neutral):
            return neutral, self.EMOTION_INDICATORS.get(emotion, "")

        return None, self.EMOTION_INDICATORS.get(emotion, "⭐")
