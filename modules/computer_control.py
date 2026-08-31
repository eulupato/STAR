"""Ferramentas locais da STAR V1.9.

Ações locais simples podem funcionar offline. Recursos que abrem serviços da
internet respeitam o estado ONLINE/OFFLINE recebido pelo STAR Core.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import subprocess
import urllib.parse
import webbrowser

APP_ALIASES = {
    "explorador": "explorer",
    "explorer": "explorer",
    "calculadora": "calc",
    "notepad": "notepad",
    "bloco de notas": "notepad",
}


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
        subprocess.Popen(command, shell=False)
        return f"Abri {name}."
    raise ValueError(f"Ainda não tenho um atalho configurado para {name}.")


def web_search(query: str) -> str:
    query = str(query).strip()
    if not query:
        return "O que você quer que eu pesquise?"
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote_plus(query))
    return f"Pesquisando por: {query}."


def spotify_search(query: str) -> str:
    query = str(query).strip()
    if not query:
        return open_app("spotify")
    webbrowser.open("https://open.spotify.com/search/" + urllib.parse.quote(query))
    return f"Procurei {query} no Spotify."


def find_files(query: str, root: str | Path | None = None, limit: int = 20):
    root_path = Path(root) if root else Path.home()
    q = str(query).strip().lower()
    if not q:
        return []
    hits = []
    try:
        for path in root_path.rglob("*"):
            if q in path.name.lower():
                hits.append(path)
                if len(hits) >= limit:
                    break
    except (PermissionError, OSError):
        pass
    return hits


def local_time() -> str:
    now = datetime.now()
    return f"Agora são {now:%H:%M}, {now:%d/%m/%Y}."


def _needs_network_message() -> str:
    return "Esse comando usa internet. Ative o modo ONLINE nas configurações da STAR."


def parse(text: str, allow_network: bool = False):
    s = " ".join(str(text).strip().lower().split())
    if not s:
        return None

    if any(k in s for k in ("que horas", "qual a hora", "horário", "horario")):
        return local_time()

    if "spotify" in s:
        if not allow_network:
            return _needs_network_message()
        query = s.split("spotify", 1)[1].strip(" .,:;- ")
        for prefix in ("e toca ", "e toque ", "toca ", "toque ", "procura ", "pesquisa ", "buscar "):
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
        return spotify_search(query)

    browser = any(k in s for k in ("google", "chrome", "navegador"))
    if browser and any(k in s for k in ("abre", "abrir", "abra")):
        if not allow_network:
            return _needs_network_message()
        query = ""
        markers = ("e veja", "e pesquise", "e pesquisa", "pesquise", "pesquisa", "veja o", "veja")
        for marker in markers:
            if marker in s:
                query = s.split(marker, 1)[1].strip(" .,:;- ")
                break
        if query:
            open_app("google")
            return web_search(query)
        return open_app("google")

    for prefix in ("pesquise ", "pesquisa ", "procure ", "procura ", "buscar ", "busque "):
        if s.startswith(prefix):
            if not allow_network:
                return _needs_network_message()
            return web_search(s[len(prefix):])

    for marker in ("procure arquivo ", "procurar arquivo ", "encontre o arquivo ", "encontre arquivo "):
        if s.startswith(marker):
            query = s[len(marker):].strip()
            hits = find_files(query)
            if not hits:
                return "Não encontrei arquivos com esse nome."
            return "Encontrei: " + "; ".join(str(p) for p in hits)

    if "abrir " in s or s.startswith("abra ") or s.startswith("abre "):
        remainder = s.replace("abra ", "", 1).replace("abre ", "", 1).replace("abrir ", "", 1).strip(" .,:;- ")
        if remainder in APP_ALIASES:
            return open_app(remainder)

    return None
