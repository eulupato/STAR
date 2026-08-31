APP_NAME = "STAR"
VERSION = "1.9"
AUTHOR = "Lu"
THEME = "dark"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
MENU_WIDTH = 1100
MENU_HEIGHT = 700
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

EXTERNAL_AI_ENABLED = False

# Voz oficial da STAR.
VOICE_ENGINE = "Chatterbox"
VOICE_CLONE_ENGINE = "Chatterbox"
VOICE_MODE = "official"

# Motor rápido disponível somente quando escolhido explicitamente.
VOICE_FAST_ENGINE = "Piper"
VOICE_FALLBACK_ON_ERROR = False

# O caminho padrão é privado/local. O gerenciador também detecta
# star_reference.* e, se necessário, escolhe uma referência de áudio
# existente em voice/reference sem enviá-la ao GitHub.
VOICE_REFERENCE = "voice/reference/star_reference.mp3"

STT_ENGINE = "faster-whisper"
STT_MODEL = "tiny"
PIPER_VOICE = "pt_BR-faber-medium"

RELEASE_CHANNEL = "stable"
RELEASE_STATUS = "final"
