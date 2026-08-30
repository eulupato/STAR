APP_NAME = "STAR"
VERSION = "1.9.1"
AUTHOR = "Lu"
THEME = "dark"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
MENU_WIDTH = 1100
MENU_HEIGHT = 700
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

EXTERNAL_AI_ENABLED = False

VOICE_ENGINE = "Chatterbox"
VOICE_FAST_ENGINE = "Piper"
VOICE_CLONE_ENGINE = "Chatterbox"
VOICE_MODE = "official"

# Referência local autorizada. Pode ser sobrescrita por STAR_VOICE_REFERENCE.
VOICE_REFERENCE = "voice/reference/star_reference.mp3"

# Em modo official, NÃO cair silenciosamente para uma voz genérica.
# Para usar Piper manualmente, escolha STAR_VOICE_MODE=fast.
VOICE_FALLBACK_ON_ERROR = False

STT_ENGINE = "faster-whisper"
STT_MODEL = "tiny"
PIPER_VOICE = "pt_BR-faber-medium"

RELEASE_CHANNEL = "stable"
RELEASE_STATUS = "hotfix"
