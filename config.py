import os
from pathlib import Path

from core.release import (
    STAR_CODENAME,
    STAR_RELEASE_CHANNEL,
    STAR_RELEASE_STATUS,
    STAR_VERSION,
)

PROJECT_ROOT = Path(__file__).resolve().parent

# O runtime é LOCAL-first. Bibliotecas do ecossistema Hugging Face não podem
# baixar artefatos implicitamente durante o uso normal da STAR. Instaladores
# explícitos importam huggingface_hub antes deste módulo e realizam a etapa de
# download de forma intencional.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

APP_NAME = "STAR"
VERSION = STAR_VERSION
CODENAME = STAR_CODENAME

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
MENU_WIDTH = 1100
MENU_HEIGHT = 700
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

EXTERNAL_AI_ENABLED = False

MIND_ENABLED = True
MIND_EVENT_HISTORY = 256
MIND_WORKING_MEMORY_TURNS = 24

KNOWLEDGE_ENABLED = True
KNOWLEDGE_DB = "knowledge/local/star_knowledge.db"
KNOWLEDGE_RESULT_LIMIT = 12

VOICE_MODE = "official"
VOICE_CHAT_MODE = "fast"
VOICE_FAST_PREFERENCE = "sapi"
VOICE_FALLBACK_ON_ERROR = False
VOICE_REFERENCE = "voice/reference/star_reference.mp3"

# O runtime recebe um caminho local absoluto, nunca o identificador remoto
# "tiny". Somado a HF_HUB_OFFLINE, isso impede download ao usar o microfone.
STT_MODEL_NAME = "tiny"
STT_MODEL = str(
    (PROJECT_ROOT / "voice" / "models" / "whisper" / STT_MODEL_NAME).resolve()
)
PIPER_MODEL = "pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx"

RELEASE_CHANNEL = STAR_RELEASE_CHANNEL
RELEASE_STATUS = STAR_RELEASE_STATUS
