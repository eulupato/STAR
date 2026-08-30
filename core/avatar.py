from pathlib import Path


class AvatarManager:
    """Gerencia os estados visuais do avatar da STAR."""

    VALID_EMOTIONS = {
        "neutral", "happy", "sad", "angry", "surprised",
        "thinking", "confused", "listening", "speaking",
        "curious", "confident",
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

    def image_exists(self):
        path = self.get_image_path()
        return path.exists() and path.stat().st_size > 0

    def get_available_emotions(self):
        return sorted(
            emotion for emotion in self.VALID_EMOTIONS
            if (self.avatar_dir / f"{emotion}.png").exists()
            and (self.avatar_dir / f"{emotion}.png").stat().st_size > 0
        )
