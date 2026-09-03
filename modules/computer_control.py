"""Ferramentas locais controladas da STAR.

Ações só são executadas quando a frase contém um comando explícito. Recursos
de internet respeitam o estado ONLINE/OFFLINE recebido pelo STAR Core.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import re
import subprocess
import urllib.parse
import webbrowser

from core.logging_config import get_logger

log = get_logger("computer")

APP_ALIASES = {
    "explorador": "explorer",
    "explorer": "explorer",
    "calculadora": "calc",
    "notepad": "notepad",
    "bloco de notas": "notepad",
}

_OPEN_VERBS = r"(?:abra|abre|abrir)"
_SEARCH_VERBS = r"(?:pesquise|pesquisa|procure|procura|buscar|busque)"


def open_app(name: str) -> str:
    name = str(name).strip().lower()
    if name in {"google", "chrome", "navegador", "browser"}:
        webbrowser.open("https://www.google.com")
        return "Abri o Google."

    if name == "spotify":
        try:
            os.startfile("spotify:")
            return "Abri o Spotify."
        except (OSError, AttributeError):
            webbrowser.open("https://open.spotify.com")
            return "Abri o Spotify no navegador."

    command = APP_ALIASES.get(name)
    if command:
        subprocess.Popen([command], shell=False)
        return f"Abri {name}."

    raise ValueError(f"Ainda não tenho um atalho configurado para {name}.")


def web_search(query: str) -> str:
    query = str(query).strip()
    if not query:
        return "O que você quer que eu pesquise?"
    webbrowser.open(
        "https://www.google.com/search?q="
        + urllib.parse.quote_plus(query)
    )
    return f"Pesquisando por: {query}."


def spotify_search(query: str) -> str:
    query = str(query).strip()
    if not query:
        return open_app("spotify")
    webbrowser.open(
        "https://open.spotify.com/search/"
        + urllib.parse.quote(query)
    )
    return f"Procurei {query} no Spotify."


def find_files(
    query: str,
    root: str | Path | None = None,
    limit: int = 20,
):
    root_path = Path(root) if root else Path.home()
    q = str(query).strip().casefold()
    safe_limit = max(1, min(int(limit), 1000))
    if not q or not root_path.exists():
        return []

    hits = []

    def onerror(error):
        log.debug("Busca de arquivos ignorou pasta inacessível: %s", error)

    for current, directories, files in os.walk(
        root_path,
        topdown=True,
        onerror=onerror,
        followlinks=False,
    ):
        for name in [*directories, *files]:
            if q in name.casefold():
                hits.append(Path(current) / name)
                if len(hits) >= safe_limit:
                    return hits
    return hits


def local_time() -> str:
    now = datetime.now()
    return f"Agora são {now:%H:%M}, {now:%d/%m/%Y}."


def _needs_network_message() -> str:
    return "Esse comando usa internet. Ative o modo ONLINE nas configurações da STAR."


def _normalize_command(text: str) -> str:
    value = " ".join(str(text or "").strip().lower().split())
    value = re.sub(r"^star\s*[,;:]?\s*", "", value)
    return value.strip()


def parse(text: str, allow_network: bool = False):
    s = _normalize_command(text)
    if not s:
        return None

    # Menções negativas não devem disparar ações.
    if re.match(r"^(?:não|nao)\b", s):
        return None

    if any(
        phrase in s
        for phrase in ("que horas", "qual a hora", "horário", "horario")
    ):
        return local_time()

    spotify_open = re.match(
        rf"^{_OPEN_VERBS}\s+(?:o\s+)?spotify\b(?:\s+(.*))?$",
        s,
    )
    spotify_suffix = re.match(
        rf"^(?:toca|toque|{_SEARCH_VERBS})\s+(.+?)\s+(?:no|na)\s+spotify$",
        s,
    )
    spotify_prefix = re.match(
        rf"^spotify\s+(?:toca|toque|{_SEARCH_VERBS})\s+(.+)$",
        s,
    )

    if spotify_open or spotify_suffix or spotify_prefix:
        if not allow_network:
            return _needs_network_message()

        query = ""
        if spotify_open:
            query = (spotify_open.group(1) or "").strip(" .,:;- ")
            query = re.sub(
                r"^(?:e\s+)?(?:toca|toque|pesquise|pesquisa|procure|procura|buscar|busque)\s+",
                "",
                query,
            )
        elif spotify_suffix:
            query = spotify_suffix.group(1).strip(" .,:;- ")
        elif spotify_prefix:
            query = spotify_prefix.group(1).strip(" .,:;- ")

        return spotify_search(query)

    browser_open = re.match(
        rf"^{_OPEN_VERBS}\s+(?:o\s+)?(?:google|chrome|navegador|browser)\b(?:\s+(.*))?$",
        s,
    )
    if browser_open:
        if not allow_network:
            return _needs_network_message()

        tail = (browser_open.group(1) or "").strip(" .,:;- ")
        search = re.match(
            r"^(?:e\s+)?(?:veja|pesquise|pesquisa|procure|procura|buscar|busque)\s+(.+)$",
            tail,
        )
        if search:
            return web_search(search.group(1).strip())
        return open_app("google")

    file_search = re.match(
        r"^(?:procure|procurar|encontre)\s+(?:o\s+)?arquivo\s+(.+)$",
        s,
    )
    if file_search:
        query = file_search.group(1).strip()
        hits = find_files(query)
        if not hits:
            return "Não encontrei arquivos com esse nome."
        return "Encontrei: " + "; ".join(str(path) for path in hits)

    explicit_web_search = re.match(
        rf"^{_SEARCH_VERBS}\s+(?:(?:na|pela)\s+(?:internet|web)|no\s+google)\s+(.+)$",
        s,
    )
    if explicit_web_search:
        if not allow_network:
            return _needs_network_message()
        return web_search(explicit_web_search.group(1).strip())

    app_open = re.match(
        rf"^{_OPEN_VERBS}\s+(.+?)\s*$",
        s,
    )
    if app_open:
        remainder = app_open.group(1).strip(" .,:;- ")
        if remainder in APP_ALIASES:
            return open_app(remainder)

    return None
