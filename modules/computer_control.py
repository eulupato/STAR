"""Ferramentas locais e leves da STAR Foundation.

Este módulo executa apenas ações simples e auditáveis. Ações destrutivas ou que
podem causar perda de trabalho permanecem bloqueadas até existir Permission
Manager/confirmador apropriado.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import ctypes
import os
import shutil
import subprocess
import urllib.parse
import webbrowser

APP_COMMANDS = {
    "explorer": ("explorer.exe",),
    "calculator": ("calc.exe",),
    "notepad": ("notepad.exe",),
    "vscode": ("code",),
    "powershell": ("powershell.exe",),
    "terminal": ("cmd.exe",),
}
LEGACY_ALIASES = {
    "explorador": "explorer", "explorer": "explorer", "arquivos": "explorer",
    "calculadora": "calculator", "calc": "calculator", "notepad": "notepad",
    "bloco de notas": "notepad", "vs code": "vscode", "vscode": "vscode",
    "visual studio code": "vscode", "powershell": "powershell", "terminal": "terminal",
}

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


def network_required_message() -> str:
    return "Esse comando usa internet. Ative o modo ONLINE nas configurações da STAR."


def _windows_key(vk: int, presses: int = 1) -> str:
    if os.name != "nt":
        return "Este controle do sistema está disponível apenas no Windows por enquanto."
    user32 = ctypes.windll.user32
    for _ in range(max(1, int(presses))):
        user32.keybd_event(vk, 0, 0, 0)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    return "ok"


def open_app(name: str) -> str:
    target = str(name or "").strip().lower()
    target = LEGACY_ALIASES.get(target, target)
    if target == "browser":
        webbrowser.open("https://www.google.com")
        return "Abri o navegador."
    if target == "spotify":
        try:
            os.startfile("spotify:")
            return "Abri o Spotify."
        except (OSError, AttributeError):
            webbrowser.open("https://open.spotify.com")
            return "Abri o Spotify no navegador."
    if target == "discord":
        try:
            os.startfile("discord:")
            return "Abri o Discord."
        except (OSError, AttributeError):
            webbrowser.open("https://discord.com/app")
            return "Abri o Discord no navegador."
    command = APP_COMMANDS.get(target)
    if command:
        executable = command[0]
        if target == "vscode" and shutil.which(executable) is None:
            raise ValueError("VS Code não foi encontrado no PATH.")
        subprocess.Popen(command, shell=False)
        labels = {"explorer": "Explorador de Arquivos", "calculator": "Calculadora", "notepad": "Bloco de Notas", "vscode": "VS Code", "powershell": "PowerShell", "terminal": "Terminal"}
        return f"Abri {labels.get(target, target)}."
    raise ValueError(f"Ainda não tenho um atalho configurado para {name}.")


def web_search(query: str) -> str:
    query = str(query or "").strip()
    if not query: return "O que você quer que eu pesquise?"
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote_plus(query))
    return f"Pesquisando por: {query}."


def spotify_search(query: str) -> str:
    query = str(query or "").strip()
    if not query: return open_app("spotify")
    webbrowser.open("https://open.spotify.com/search/" + urllib.parse.quote(query))
    return f"Procurei {query} no Spotify."


def find_files(query: str, root: str | Path | None = None, limit: int = 20):
    root_path = Path(root) if root else Path.home()
    q = str(query or "").strip().lower()
    if not q: return []
    hits = []
    try:
        for path in root_path.rglob("*"):
            if q in path.name.lower():
                hits.append(path)
                if len(hits) >= limit: break
    except (PermissionError, OSError):
        pass
    return hits


def local_time() -> str:
    return f"Agora são {datetime.now():%H:%M}."


def local_date() -> str:
    return f"Hoje é {datetime.now():%d/%m/%Y}."


def volume_up() -> str:
    result = _windows_key(VK_VOLUME_UP, presses=2)
    return "Aumentei o volume." if result == "ok" else result


def volume_down() -> str:
    result = _windows_key(VK_VOLUME_DOWN, presses=2)
    return "Abaixei o volume." if result == "ok" else result


def volume_mute() -> str:
    result = _windows_key(VK_VOLUME_MUTE)
    return "Alternei o mudo do sistema." if result == "ok" else result


def media_play_pause() -> str:
    result = _windows_key(VK_MEDIA_PLAY_PAUSE)
    return "Play/pause enviado." if result == "ok" else result


def media_next() -> str:
    result = _windows_key(VK_MEDIA_NEXT_TRACK)
    return "Pulei para a próxima faixa." if result == "ok" else result


def media_previous() -> str:
    result = _windows_key(VK_MEDIA_PREV_TRACK)
    return "Voltei para a faixa anterior." if result == "ok" else result


def take_screenshot() -> str:
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise RuntimeError("Pillow/ImageGrab não está disponível.") from exc
    folder = Path.home() / "Pictures" / "STAR"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / datetime.now().strftime("Screenshot_%Y%m%d_%H%M%S.png")
    try:
        ImageGrab.grab().save(path)
    except Exception as exc:
        raise RuntimeError(f"Não consegui capturar a tela: {exc}") from exc
    return f"Capturei a tela em {path}."


def parse(text: str, allow_network: bool = False):
    """Compatibilidade com chamadas antigas; parser oficial fica em core.commands."""
    from core.agents import AgentManager
    return AgentManager().dispatch(text, network_enabled=allow_network, remote=False)
