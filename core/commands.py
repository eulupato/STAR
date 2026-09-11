"""Registro central de comandos de voz da STAR.

A STAR continua sendo uma única entidade. Este módulo transforma frases naturais
em intents estruturadas; os agentes apenas executam capacidades especializadas.

A lista de exemplos é gerada a partir de templates + slots. Isso evita manter
milhares de `if/elif` duplicados e permite testar/expandir o vocabulário de forma
determinística.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class CommandMatch:
    intent: str
    agent: str
    slots: dict
    risk: str = "read"
    remote_safe: bool = True


def normalize_text(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^\w\s:+./-]", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def strip_wake_word(text: str) -> str:
    value = normalize_text(text)
    for prefix in ("ei star ", "ok star ", "ola star ", "star "):
        if value.startswith(prefix):
            return value[len(prefix):].strip()
    return value


APP_TARGETS = {
    "explorador": ("explorer", "computer"), "explorer": ("explorer", "computer"),
    "arquivos": ("explorer", "file"), "calculadora": ("calculator", "computer"),
    "calc": ("calculator", "computer"), "bloco de notas": ("notepad", "computer"),
    "notepad": ("notepad", "computer"), "spotify": ("spotify", "music"),
    "google": ("browser", "web"), "chrome": ("browser", "web"),
    "navegador": ("browser", "web"), "browser": ("browser", "web"),
    "vs code": ("vscode", "coding"), "vscode": ("vscode", "coding"),
    "visual studio code": ("vscode", "coding"), "discord": ("discord", "computer"),
    "terminal": ("terminal", "coding"), "powershell": ("powershell", "coding"),
}

OPEN_PREFIXES = ("abra ", "abre ", "abrir ", "inicie ", "inicia ", "iniciar ", "execute ", "executa ", "rodar ")
CLOSE_PREFIXES = ("feche ", "fecha ", "fechar ", "encerre ", "encerra ", "encerrar ")
WEB_PREFIXES = ("pesquise ", "pesquisa ", "pesquisar ", "procure ", "procura ", "procurar ", "busque ", "buscar ", "google ")
FILE_PREFIXES = ("procure arquivo ", "procure o arquivo ", "encontre arquivo ", "encontre o arquivo ", "busque arquivo ", "busque o arquivo ", "ache arquivo ", "ache o arquivo ")
SPOTIFY_PREFIXES = ("toque no spotify ", "toca no spotify ", "procure no spotify ", "pesquise no spotify ", "spotify toca ", "spotify toque ", "spotify procure ")
VOLUME_UP = {"aumente o volume", "aumenta o volume", "suba o volume", "sobe o volume", "volume mais alto", "deixe mais alto", "mais volume"}
VOLUME_DOWN = {"abaixe o volume", "abaixa o volume", "diminua o volume", "diminui o volume", "volume mais baixo", "deixe mais baixo", "menos volume"}
MUTE = {"mute o audio", "mute o som", "silencie o audio", "silencie o som", "tire o som", "sem som"}
MEDIA_TOGGLE = {"pause a musica", "pausa a musica", "pause", "pausa", "continue a musica", "continua a musica", "retome a musica", "retoma a musica", "play pause"}
MEDIA_NEXT = {"proxima musica", "proxima faixa", "pule a musica", "pula a musica", "avance a musica"}
MEDIA_PREVIOUS = {"musica anterior", "faixa anterior", "volte a musica", "volta a musica", "musica de antes"}
SCREENSHOT = {"tire um print", "tira um print", "tire uma captura de tela", "tira uma captura de tela", "capture a tela", "salve um print", "screenshot"}
LOCK_PC = {"bloqueie o computador", "bloqueia o computador", "trave o computador", "trava o computador", "bloqueie o pc"}
TIME_QUERIES = {"que horas sao", "qual a hora", "me diga as horas", "me fale as horas", "horario agora", "hora agora"}
DATE_QUERIES = {"que dia e hoje", "qual a data de hoje", "me diga a data", "data de hoje", "qual e a data"}
AGENT_QUERIES = {"quais agentes voce tem", "liste seus agentes", "lista de agentes", "mostre os agentes", "quais agentes estao disponiveis"}
COMMAND_QUERIES = {"quantos comandos de voz voce tem", "quantos comandos voce entende", "lista de comandos", "mostre seus comandos de voz", "o que eu posso falar"}


def _target_from_tail(tail: str):
    tail = tail.strip(" .,:;-/")
    for article in ("o ", "a "):
        if tail.startswith(article):
            tail = tail[len(article):].strip()
            break
    for phrase in sorted(APP_TARGETS, key=len, reverse=True):
        if tail == phrase or tail.startswith(phrase + " "):
            target, agent = APP_TARGETS[phrase]
            return target, agent
    return None, None


def match_command(text: str) -> CommandMatch | None:
    s = strip_wake_word(text)
    if not s:
        return None
    if s in TIME_QUERIES: return CommandMatch("time", "personal_assistant", {})
    if s in DATE_QUERIES: return CommandMatch("date", "personal_assistant", {})
    if s in AGENT_QUERIES: return CommandMatch("agents_status", "orchestrator", {})
    if s in COMMAND_QUERIES: return CommandMatch("commands_status", "voice_command", {})
    if s in VOLUME_UP: return CommandMatch("volume_up", "computer", {}, risk="write")
    if s in VOLUME_DOWN: return CommandMatch("volume_down", "computer", {}, risk="write")
    if s in MUTE: return CommandMatch("volume_mute", "computer", {}, risk="write")
    if s in MEDIA_TOGGLE: return CommandMatch("media_toggle", "music", {}, risk="write")
    if s in MEDIA_NEXT: return CommandMatch("media_next", "music", {}, risk="write")
    if s in MEDIA_PREVIOUS: return CommandMatch("media_previous", "music", {}, risk="write")
    if s in SCREENSHOT: return CommandMatch("screenshot", "computer", {}, risk="write")
    if s in LOCK_PC: return CommandMatch("lock_pc", "security", {}, risk="confirm", remote_safe=False)
    for prefix in FILE_PREFIXES:
        if s.startswith(prefix):
            query = s[len(prefix):].strip()
            if query: return CommandMatch("find_file", "file", {"query": query})
    for prefix in SPOTIFY_PREFIXES:
        if s.startswith(prefix):
            query = s[len(prefix):].strip()
            if query: return CommandMatch("spotify_search", "music", {"query": query}, risk="network")
    for prefix in WEB_PREFIXES:
        if s.startswith(prefix):
            query = s[len(prefix):].strip()
            if query: return CommandMatch("web_search", "research", {"query": query}, risk="network")
    for prefix in OPEN_PREFIXES:
        if s.startswith(prefix):
            target, agent = _target_from_tail(s[len(prefix):].strip())
            if target:
                network = target in {"spotify", "browser", "discord"}
                return CommandMatch("open_app", agent, {"target": target}, risk="network" if network else "write")
    for prefix in CLOSE_PREFIXES:
        if s.startswith(prefix):
            target, agent = _target_from_tail(s[len(prefix):].strip())
            if target: return CommandMatch("close_app", agent, {"target": target}, risk="confirm", remote_safe=False)
    return None


_RESEARCH_TOPICS = (
    "inteligencia artificial", "astronomia", "fisica quantica", "matematica", "biologia", "quimica", "historia do brasil", "geografia", "filosofia", "psicologia", "neurociencia", "engenharia", "robotica", "programacao python", "seguranca digital", "linux", "windows", "android", "ios", "smartwatch", "microcontroladores", "arduino", "raspberry pi", "impressao 3d", "eletronica", "musica", "teoria musical", "composicao", "producao musical", "mixagem", "masterizacao", "cinema", "animacao", "pixel art", "design", "literatura", "portugues", "ingles", "espanhol", "economia", "estatistica", "probabilidade", "calculo", "algebra linear", "mecanica", "termodinamica", "eletromagnetismo", "optica", "relatividade", "cosmologia", "genetica", "ecologia", "botanica", "zoologia", "medicina", "nutricao", "meteorologia", "oceanografia", "geologia", "nanotecnologia", "ciencia dos materiais", "baterias", "energia solar", "energias renovaveis", "redes neurais", "modelos de linguagem", "visao computacional", "reconhecimento de voz", "sintese de voz", "bancos de dados", "redes de computadores", "algoritmos", "estruturas de dados", "git", "github", "vscode", "privacidade", "criptografia", "hardware", "processadores", "placas de video", "memoria ram", "armazenamento", "bluetooth", "wifi", "internet das coisas", "automacao residencial", "realidade virtual", "realidade aumentada", "exploracao espacial", "sistema solar", "buracos negros", "estrelas", "planetas", "fauna brasileira", "flora brasileira", "sustentabilidade", "clima", "fotografia", "audio digital", "sintetizadores", "violao", "piano", "canto"
)
_FILE_TOPICS = ("star", "roadmap", "matematica", "fisica", "quimica", "biologia", "musica", "letra", "beat", "projeto", "trabalho", "pdf", "livro", "planilha", "apresentacao", "foto", "video", "audio", "codigo", "python", "notas", "documento", "contrato", "recibo", "faculdade", "escola", "pesquisa", "backup", "star watch")
_MUSIC_TOPICS = ("minhas curtidas", "minha playlist", "lofi", "jazz", "rock", "rap", "trap", "mpb", "samba", "pagode", "funk", "reggae", "eletronica", "instrumental", "piano", "violao", "musica para estudar", "musica para treinar", "musica calma", "musica animada")


def voice_command_examples() -> tuple[str, ...]:
    """Gera catálogo auditável de frases úteis sem duplicar regras de execução."""
    phrases = set()
    for wake in ("", "star ", "ei star "):
        for prefix in OPEN_PREFIXES[:6]:
            for target in APP_TARGETS: phrases.add(f"{wake}{prefix}{target}".strip())
        for prefix in CLOSE_PREFIXES[:4]:
            for target in APP_TARGETS: phrases.add(f"{wake}{prefix}{target}".strip())
        for prefix in WEB_PREFIXES[:6]:
            for topic in _RESEARCH_TOPICS: phrases.add(f"{wake}{prefix}{topic}".strip())
        for prefix in FILE_PREFIXES[:6]:
            for topic in _FILE_TOPICS: phrases.add(f"{wake}{prefix}{topic}".strip())
        for prefix in SPOTIFY_PREFIXES[:5]:
            for topic in _MUSIC_TOPICS: phrases.add(f"{wake}{prefix}{topic}".strip())
        for group in (VOLUME_UP, VOLUME_DOWN, MUTE, MEDIA_TOGGLE, MEDIA_NEXT, MEDIA_PREVIOUS, SCREENSHOT, TIME_QUERIES, DATE_QUERIES, AGENT_QUERIES, COMMAND_QUERIES):
            for phrase in group: phrases.add(f"{wake}{phrase}".strip())
    return tuple(sorted(phrases))


def command_count() -> int:
    return len(voice_command_examples())


def stt_hotwords() -> str:
    return ("STAR, Spotify, VS Code, Visual Studio Code, Discord, PowerShell, smartwatch, GitHub, navegador, explorador, calculadora, screenshot, volume, música, arquivo, pesquisa, projeto, laboratório, biblioteca")
