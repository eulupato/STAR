"""Registro central de comandos naturais da STAR.

As frases são descritas como famílias de intents + slots/variáveis. Isso permite
milhares de variações auditáveis sem milhares de ``if/elif``. O matcher continua
leve e aceita valores livres em comandos de pesquisa, arquivos, música e clima.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
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


WAKE_PREFIXES = ("", "star ", "ei star ", "ok star ", "ola star ", "hey star ")
POLITE_SUFFIXES = ("", " por favor")


def strip_wake_word(text: str) -> str:
    value = normalize_text(text)
    for prefix in WAKE_PREFIXES[1:]:
        if value.startswith(prefix):
            value = value[len(prefix):].strip()
            break
    if value.startswith("por favor "):
        value = value[len("por favor "):].strip()
    if value.endswith(" por favor"):
        value = value[: -len(" por favor")].strip()
    return value


APP_TARGETS = {
    "explorador": ("explorer", "computer"),
    "explorer": ("explorer", "computer"),
    "arquivos": ("explorer", "file"),
    "calculadora": ("calculator", "computer"),
    "calc": ("calculator", "computer"),
    "bloco de notas": ("notepad", "computer"),
    "notepad": ("notepad", "computer"),
    "spotify": ("spotify", "music"),
    "google": ("browser", "web"),
    "chrome": ("browser", "web"),
    "navegador": ("browser", "web"),
    "browser": ("browser", "web"),
    "vs code": ("vscode", "coding"),
    "vscode": ("vscode", "coding"),
    "visual studio code": ("vscode", "coding"),
    "discord": ("discord", "computer"),
    "terminal": ("terminal", "coding"),
    "powershell": ("powershell", "coding"),
}

OPEN_PREFIXES = (
    "abra ", "abre ", "abrir ", "inicie ", "inicia ", "iniciar ",
    "execute ", "executa ", "rodar ", "rode ", "lance ", "abrir o ",
)
CLOSE_PREFIXES = (
    "feche ", "fecha ", "fechar ", "encerre ", "encerra ", "encerrar ",
    "termine ", "finalize ",
)
WEB_PREFIXES = (
    "pesquise ", "pesquisa ", "pesquisar ", "procure ", "procura ", "procurar ",
    "busque ", "buscar ", "google ", "pesquise na web ",
)
FILE_PREFIXES = (
    "procure arquivo ", "procure o arquivo ", "encontre arquivo ",
    "encontre o arquivo ", "busque arquivo ", "busque o arquivo ",
    "ache arquivo ", "ache o arquivo ", "localize arquivo ", "localize o arquivo ",
)
SPOTIFY_PREFIXES = (
    "toque no spotify ", "toca no spotify ", "procure no spotify ",
    "pesquise no spotify ", "spotify toca ", "spotify toque ", "spotify procure ",
    "spotify pesquise ", "coloque no spotify ", "bote no spotify ",
)
WEATHER_LOCATION_PREFIXES = (
    "como esta o tempo em ", "como ta o tempo em ", "qual o clima em ",
    "clima em ", "tempo em ", "previsao do tempo em ", "temperatura em ",
    "como esta o clima em ",
)

VOLUME_UP = {
    "aumente o volume", "aumenta o volume", "suba o volume", "sobe o volume",
    "volume mais alto", "deixe mais alto", "mais volume", "aumente o som",
}
VOLUME_DOWN = {
    "abaixe o volume", "abaixa o volume", "diminua o volume", "diminui o volume",
    "volume mais baixo", "deixe mais baixo", "menos volume", "abaixe o som",
}
MUTE = {
    "mute o audio", "mute o som", "silencie o audio", "silencie o som",
    "tire o som", "sem som", "fique sem som",
}
MEDIA_TOGGLE = {
    "pause a musica", "pausa a musica", "pause", "pausa", "continue a musica",
    "continua a musica", "retome a musica", "retoma a musica", "play pause",
}
MEDIA_NEXT = {
    "proxima musica", "proxima faixa", "pule a musica", "pula a musica",
    "avance a musica", "avanca a musica",
}
MEDIA_PREVIOUS = {
    "musica anterior", "faixa anterior", "volte a musica", "volta a musica",
    "musica de antes", "faixa de antes",
}
SCREENSHOT = {
    "tire um print", "tira um print", "tire uma captura de tela",
    "tira uma captura de tela", "capture a tela", "salve um print", "screenshot",
}
LOCK_PC = {
    "bloqueie o computador", "bloqueia o computador", "trave o computador",
    "trava o computador", "bloqueie o pc",
}
TIME_QUERIES = {
    "que horas sao", "qual a hora", "me diga as horas", "me fale as horas",
    "horario agora", "hora agora", "que horas e agora",
}
DATE_QUERIES = {
    "que dia e hoje", "qual a data de hoje", "me diga a data", "data de hoje",
    "qual e a data", "qual a data",
}
WEATHER_QUERIES = {
    "como esta o tempo", "como ta o tempo", "qual o clima", "clima agora",
    "tempo agora", "qual a temperatura", "temperatura agora",
    "esta chovendo", "vai chover", "como esta o clima",
}
AGENT_QUERIES = {
    "quais agentes voce tem", "liste seus agentes", "lista de agentes",
    "mostre os agentes", "quais agentes estao disponiveis",
}
COMMAND_QUERIES = {
    "quantos comandos de voz voce tem", "quantos comandos voce entende",
    "lista de comandos", "mostre seus comandos de voz", "o que eu posso falar",
}
COMMAND_VARIABLE_QUERIES = {
    "quais variaveis dos comandos", "quais variaveis voce aceita",
    "mostre as variaveis dos comandos", "como funcionam as variaveis dos comandos",
}


def _target_from_tail(tail: str):
    tail = tail.strip(" .,:;-/")
    for article in ("o ", "a "):
        if tail.startswith(article):
            tail = tail[len(article):].strip()
            break
    for phrase in sorted(APP_TARGETS, key=len, reverse=True):
        if tail == phrase or tail.startswith(phrase + " "):
            return APP_TARGETS[phrase]
    return None, None


def match_command(text: str) -> CommandMatch | None:
    s = strip_wake_word(text)
    if not s:
        return None

    if s in TIME_QUERIES:
        return CommandMatch("time", "personal_assistant", {})
    if s in DATE_QUERIES:
        return CommandMatch("date", "personal_assistant", {})
    if s in WEATHER_QUERIES:
        return CommandMatch("weather_current", "personal_assistant", {}, risk="network")
    if s in AGENT_QUERIES:
        return CommandMatch("agents_status", "orchestrator", {})
    if s in COMMAND_QUERIES:
        return CommandMatch("commands_status", "voice_command", {})
    if s in COMMAND_VARIABLE_QUERIES:
        return CommandMatch("command_variables", "voice_command", {})
    if s in VOLUME_UP:
        return CommandMatch("volume_up", "computer", {}, risk="write")
    if s in VOLUME_DOWN:
        return CommandMatch("volume_down", "computer", {}, risk="write")
    if s in MUTE:
        return CommandMatch("volume_mute", "computer", {}, risk="write")
    if s in MEDIA_TOGGLE:
        return CommandMatch("media_toggle", "music", {}, risk="write")
    if s in MEDIA_NEXT:
        return CommandMatch("media_next", "music", {}, risk="write")
    if s in MEDIA_PREVIOUS:
        return CommandMatch("media_previous", "music", {}, risk="write")
    if s in SCREENSHOT:
        return CommandMatch("screenshot", "computer", {}, risk="write", remote_safe=False)
    if s in LOCK_PC:
        return CommandMatch("lock_pc", "security", {}, risk="confirm", remote_safe=False)

    for prefix in WEATHER_LOCATION_PREFIXES:
        if s.startswith(prefix):
            location = s[len(prefix):].strip()
            if location:
                return CommandMatch(
                    "weather_current",
                    "personal_assistant",
                    {"location": location},
                    risk="network",
                )

    for prefix in FILE_PREFIXES:
        if s.startswith(prefix):
            query = s[len(prefix):].strip()
            if query:
                return CommandMatch("find_file", "file", {"query": query}, remote_safe=False)

    for prefix in SPOTIFY_PREFIXES:
        if s.startswith(prefix):
            query = s[len(prefix):].strip()
            if query:
                return CommandMatch("spotify_search", "music", {"query": query}, risk="network")

    for prefix in WEB_PREFIXES:
        if s.startswith(prefix):
            query = s[len(prefix):].strip()
            if query:
                return CommandMatch("web_search", "research", {"query": query}, risk="network")

    for prefix in OPEN_PREFIXES:
        if s.startswith(prefix):
            target, agent = _target_from_tail(s[len(prefix):].strip())
            if target:
                network = target in {"spotify", "browser", "discord"}
                remote_safe = target not in {"terminal", "powershell"}
                return CommandMatch(
                    "open_app",
                    agent,
                    {"target": target},
                    risk="network" if network else "write",
                    remote_safe=remote_safe,
                )

    for prefix in CLOSE_PREFIXES:
        if s.startswith(prefix):
            target, agent = _target_from_tail(s[len(prefix):].strip())
            if target:
                return CommandMatch(
                    "close_app",
                    agent,
                    {"target": target},
                    risk="confirm",
                    remote_safe=False,
                )
    return None


_RESEARCH_TOPICS = (
    "inteligencia artificial", "astronomia", "fisica quantica", "matematica",
    "biologia", "quimica", "historia do brasil", "geografia", "filosofia",
    "psicologia", "neurociencia", "engenharia", "robotica", "programacao python",
    "seguranca digital", "linux", "windows", "android", "ios", "smartwatch",
    "microcontroladores", "arduino", "raspberry pi", "impressao 3d", "eletronica",
    "musica", "teoria musical", "composicao", "producao musical", "mixagem",
    "masterizacao", "cinema", "animacao", "pixel art", "design", "literatura",
    "portugues", "ingles", "espanhol", "economia", "estatistica", "probabilidade",
    "calculo", "algebra linear", "mecanica", "termodinamica", "eletromagnetismo",
    "optica", "relatividade", "cosmologia", "genetica", "ecologia", "botanica",
    "zoologia", "medicina", "nutricao", "meteorologia", "oceanografia", "geologia",
    "nanotecnologia", "ciencia dos materiais", "baterias", "energia solar",
    "energias renovaveis", "redes neurais", "modelos de linguagem",
    "visao computacional", "reconhecimento de voz", "sintese de voz",
    "bancos de dados", "redes de computadores", "algoritmos", "estruturas de dados",
    "git", "github", "vscode", "privacidade", "criptografia", "hardware",
    "processadores", "placas de video", "memoria ram", "armazenamento", "bluetooth",
    "wifi", "internet das coisas", "automacao residencial", "realidade virtual",
    "realidade aumentada", "exploracao espacial", "sistema solar", "buracos negros",
    "estrelas", "planetas", "fauna brasileira", "flora brasileira",
    "sustentabilidade", "clima", "fotografia", "audio digital", "sintetizadores",
    "violao", "piano", "canto", "computacao quantica", "ciberseguranca",
    "engenharia aeroespacial", "biotecnologia", "materiais 2d", "fusao nuclear",
)
_FILE_TOPICS = (
    "star", "roadmap", "matematica", "fisica", "quimica", "biologia", "musica",
    "letra", "beat", "projeto", "trabalho", "pdf", "livro", "planilha",
    "apresentacao", "foto", "video", "audio", "codigo", "python", "notas",
    "documento", "contrato", "recibo", "faculdade", "escola", "pesquisa",
    "backup", "star watch", "manifest", "teste", "relatorio",
)
_MUSIC_TOPICS = (
    "minhas curtidas", "minha playlist", "lofi", "jazz", "rock", "rap", "trap",
    "mpb", "samba", "pagode", "funk", "reggae", "eletronica", "instrumental",
    "piano", "violao", "musica para estudar", "musica para treinar",
    "musica calma", "musica animada", "r&b", "soul", "boom bap", "jazz rap",
)
_WEATHER_LOCATIONS = (
    "sao paulo", "rio de janeiro", "porto alegre", "curitiba", "florianopolis",
    "brasilia", "salvador", "recife", "fortaleza", "manaus", "belem",
    "belo horizonte", "caxias do sul", "porto", "lisboa", "coimbra", "braga",
    "londres", "paris", "berlim", "madrid", "roma", "toquio", "nova york",
    "toronto", "sydney", "buenos aires", "montevideu", "santiago", "oslo",
)


def command_variables() -> dict[str, dict]:
    return {
        "open_app.target": {
            "type": "enum",
            "examples": tuple(sorted(APP_TARGETS)),
            "description": "aplicativo/ferramenta reconhecida",
        },
        "close_app.target": {
            "type": "enum",
            "examples": tuple(sorted(APP_TARGETS)),
            "description": "aplicativo a fechar; requer confirmação",
        },
        "web_search.query": {
            "type": "free_text",
            "examples": _RESEARCH_TOPICS[:12],
            "description": "consulta livre de pesquisa",
        },
        "find_file.query": {
            "type": "free_text",
            "examples": _FILE_TOPICS[:12],
            "description": "nome ou fragmento do arquivo",
        },
        "spotify_search.query": {
            "type": "free_text",
            "examples": _MUSIC_TOPICS[:12],
            "description": "música, artista, álbum ou playlist",
        },
        "weather_current.location": {
            "type": "free_text",
            "examples": _WEATHER_LOCATIONS[:12],
            "description": "cidade/região opcional; sem valor usa localização contextual",
        },
    }


@lru_cache(maxsize=1)
def voice_command_examples() -> tuple[str, ...]:
    """Gera um catálogo auditável com mais de 4 mil frases realmente matcháveis."""
    base_phrases: set[str] = set()

    for prefix in OPEN_PREFIXES[:10]:
        for target in APP_TARGETS:
            base_phrases.add(f"{prefix}{target}".strip())
    for prefix in CLOSE_PREFIXES:
        for target in APP_TARGETS:
            base_phrases.add(f"{prefix}{target}".strip())
    for prefix in WEB_PREFIXES:
        for topic in _RESEARCH_TOPICS:
            base_phrases.add(f"{prefix}{topic}".strip())
    for prefix in FILE_PREFIXES:
        for topic in _FILE_TOPICS:
            base_phrases.add(f"{prefix}{topic}".strip())
    for prefix in SPOTIFY_PREFIXES:
        for topic in _MUSIC_TOPICS:
            base_phrases.add(f"{prefix}{topic}".strip())
    for prefix in WEATHER_LOCATION_PREFIXES:
        for location in _WEATHER_LOCATIONS:
            base_phrases.add(f"{prefix}{location}".strip())

    static_groups = (
        VOLUME_UP, VOLUME_DOWN, MUTE, MEDIA_TOGGLE, MEDIA_NEXT, MEDIA_PREVIOUS,
        SCREENSHOT, LOCK_PC, TIME_QUERIES, DATE_QUERIES, WEATHER_QUERIES,
        AGENT_QUERIES, COMMAND_QUERIES, COMMAND_VARIABLE_QUERIES,
    )
    for group in static_groups:
        base_phrases.update(group)

    phrases: set[str] = set()
    for wake in WAKE_PREFIXES:
        for phrase in base_phrases:
            for polite in POLITE_SUFFIXES:
                phrases.add(f"{wake}{phrase}{polite}".strip())
    return tuple(sorted(phrases))


def command_count() -> int:
    return len(voice_command_examples())


def stt_hotwords() -> str:
    return (
        "STAR, Spotify, VS Code, Visual Studio Code, Discord, PowerShell, smartwatch, "
        "GitHub, navegador, explorador, calculadora, screenshot, volume, música, arquivo, "
        "pesquisa, projeto, laboratório, biblioteca, clima, temperatura, previsão do tempo"
    )
