class EmotionManager:
    """Gerenciador simples de estado emocional visual da STAR."""

    VALID_EMOTIONS = {
        "neutral", "happy", "sad", "angry", "surprised",
        "thinking", "confused", "listening", "speaking",
        "curious", "confident",
    }

    def __init__(self):
        self.current_emotion = "neutral"

    def set_emotion(self, emotion):
        if emotion not in self.VALID_EMOTIONS:
            raise ValueError(f"Emoção inválida: {emotion}")
        self.current_emotion = emotion

    def get_emotion(self):
        return self.current_emotion

    def reset(self):
        self.current_emotion = "neutral"
