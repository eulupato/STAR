from core.release import APP_NAME, RELEASE_CHANNEL, RELEASE_STATUS, VERSION

AUTHOR = "Lu"
THEME = "dark"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
MENU_WIDTH = 1100
MENU_HEIGHT = 700
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

EXTERNAL_AI_ENABLED = False

# Ponte experimental de dispositivos. Permanece desligada por padrão para não
# alterar o comportamento da Foundation. INICIAR_STAR_WATCH.bat ativa via env.
DEVICE_GATEWAY_ENABLED = False
DEVICE_GATEWAY_HOST = "0.0.0.0"
DEVICE_GATEWAY_PORT = 8765

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

# Conversão de voz é uma capacidade separada do TTS. Seed-VC permanece opcional,
# local e lazy; sua ausência nunca impede a STAR de iniciar, ouvir ou falar.
VOICE_CONVERSION_ENGINE = "Seed-VC"
VOICE_CONVERSION_ENABLED = True
VOICE_CONVERSION_HOME = "voice/external/seed-vc"

# O caminho padrão é privado/local. O gerenciador também detecta
# star_reference.* e, se necessário, escolhe uma referência de áudio
# existente em voice/reference sem enviá-la ao GitHub.
VOICE_REFERENCE = "voice/reference/star_reference.mp3"

STT_ENGINE = "faster-whisper"
STT_MODEL = "tiny"
PIPER_VOICE = "pt_BR-faber-medium"