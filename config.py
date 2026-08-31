APP_NAME = "STAR"
VERSION = "2.0"
AUTHOR = "Lu"
THEME = "dark"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
MENU_WIDTH = 1100
MENU_HEIGHT = 700
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

EXTERNAL_AI_ENABLED = False

# MIND V2
MIND_ENABLED = True
MIND_EVENT_HISTORY = 256
MIND_WORKING_MEMORY_TURNS = 24

# Voz oficial da STAR.
VOICE_ENGINE = "Chatterbox"
VOICE_CLONE_ENGINE = "Chatterbox"
VOICE_MODE = "official"
# A interface usa fala rápida por padrão; o Chatterbox oficial continua disponível.
VOICE_CHAT_MODE = "fast"

# Motor rápido disponível somente quando escolhido explicitamente.
VOICE_FAST_ENGINE = "Windows SAPI / Piper"
VOICE_FAST_PREFERENCE = "sapi"
VOICE_FALLBACK_ON_ERROR = False

# O caminho padrão é privado/local. O gerenciador também detecta
# star_reference.* e, se necessário, escolhe uma referência de áudio
# existente em voice/reference sem enviá-la ao GitHub.
VOICE_REFERENCE = "voice/reference/star_reference.mp3"

STT_ENGINE = "faster-whisper"
STT_MODEL = "tiny"
PIPER_VOICE = "pt_BR-faber-medium"

RELEASE_CHANNEL = "development"
RELEASE_STATUS = "mind-foundation"
