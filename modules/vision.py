"""STAR Vision — portal de realidade aumentada e filtros gestuais.

A camada de controle deste módulo não importa OpenCV/MediaPipe no startup da STAR.
As dependências pesadas são carregadas somente pelo cliente de câmera. Assim o
Core continua utilizável mesmo em máquinas sem webcam ou stack de visão.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "clients" / "star_vision_portal.py"

PORTAL_FILTERS = (
    {"key": "grid", "name": "Grid", "description": "grade holográfica sobre a cena"},
    {"key": "neon", "name": "Neon", "description": "duotone por faixas de luminância"},
    {"key": "halftone", "name": "Halftone", "description": "trama de pontos monocromática"},
    {"key": "chromatic", "name": "Chromatic", "description": "separação RGB e scanlines"},
    {"key": "thermal", "name": "Thermal", "description": "mapa térmico pseudocolorido"},
    {"key": "vintage", "name": "Vintage", "description": "sépia, vinheta e grão"},
    {"key": "frosted", "name": "Frosted", "description": "vidro fosco luminoso"},
    {"key": "magenta", "name": "Magenta", "description": "halftone rosa/magenta"},
)

OPEN_COMMANDS = {
    "abra o portal visual", "abra o portal de visao", "abra o portal star",
    "ative o portal visual", "ative o portal de visao", "inicie o portal visual",
    "inicie o portal de visao", "portal visual", "portal de realidade aumentada",
    "open vision portal", "open star vision portal",
}
STOP_COMMANDS = {
    "feche o portal visual", "feche o portal de visao", "pare o portal visual",
    "encerre o portal visual", "close vision portal", "stop vision portal",
}
FILTER_COMMANDS = {
    "quais filtros visuais", "liste os filtros visuais", "filtros do portal",
    "quais filtros do portal", "vision filters", "list vision filters",
}
STATUS_COMMANDS = {
    "status do portal visual", "status da visao", "status do star vision",
    "vision portal status", "vision status",
}


@dataclass
class GestureHysteresis:
    """Detecta o gesto de fechamento com histerese para evitar múltiplos disparos."""

    close_ratio: float = 0.17
    reopen_ratio: float = 0.29
    closed: bool = False

    def update(self, portal_width: float, frame_width: float) -> bool:
        if frame_width <= 0:
            return False
        ratio = float(portal_width) / float(frame_width)
        if not self.closed and ratio <= self.close_ratio:
            self.closed = True
            return True
        if self.closed and ratio >= self.reopen_ratio:
            self.closed = False
        return False


_portal_process: subprocess.Popen | None = None


def dependency_status() -> dict[str, bool]:
    """Retorna disponibilidade sem importar as bibliotecas pesadas."""
    return {
        "opencv": importlib.util.find_spec("cv2") is not None,
        "mediapipe": importlib.util.find_spec("mediapipe") is not None,
        "numpy": importlib.util.find_spec("numpy") is not None,
    }


def dependencies_ready() -> bool:
    return all(dependency_status().values())


def filter_summary() -> str:
    items = "; ".join(f"{item['name']} — {item['description']}" for item in PORTAL_FILTERS)
    return f"STAR Vision Portal possui {len(PORTAL_FILTERS)} filtros: {items}."


def portal_running() -> bool:
    global _portal_process
    if _portal_process is None:
        return False
    if _portal_process.poll() is None:
        return True
    _portal_process = None
    return False


def vision_status() -> str:
    deps = dependency_status()
    installed = ", ".join(name for name, ok in deps.items() if ok) or "nenhuma"
    missing = ", ".join(name for name, ok in deps.items() if not ok) or "nenhuma"
    state = "ativo" if portal_running() else "parado"
    return (
        f"STAR Vision Portal: {state}. Dependências presentes: {installed}. "
        f"Ausentes: {missing}. Filtros disponíveis: {len(PORTAL_FILTERS)}."
    )


def launch_portal(camera_index: int = 0) -> str:
    """Inicia o cliente de câmera local sem bloquear o Core."""
    global _portal_process
    if portal_running():
        return "O STAR Vision Portal já está aberto."
    missing = [name for name, ok in dependency_status().items() if not ok]
    if missing:
        return (
            "STAR Vision Portal está instalado no sistema, mas faltam dependências locais: "
            + ", ".join(missing)
            + ". Execute `pip install -r requirements-vision.txt`."
        )
    if not CLIENT.is_file():
        return "Cliente STAR Vision Portal não foi encontrado."
    try:
        _portal_process = subprocess.Popen(
            [sys.executable, str(CLIENT), "--camera", str(int(camera_index))],
            cwd=str(ROOT),
        )
    except (OSError, ValueError) as exc:
        _portal_process = None
        return f"Não consegui iniciar o STAR Vision Portal: {exc}"
    return (
        "STAR Vision Portal iniciado. Mostre as duas mãos com indicador e polegar visíveis; "
        "aproxime as mãos para trocar o filtro. Q ou Esc fecha a câmera."
    )


def stop_portal() -> str:
    global _portal_process
    if not portal_running():
        return "O STAR Vision Portal já está fechado."
    try:
        _portal_process.terminate()
        _portal_process.wait(timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        try:
            _portal_process.kill()
        except OSError:
            pass
    _portal_process = None
    return "STAR Vision Portal encerrado."


def _normalize_command(text: str) -> str:
    from core.commands import normalize_text

    value = normalize_text(text)
    for prefix in ("star ", "ei star ", "ok star ", "ola star ", "hey star "):
        if value.startswith(prefix):
            return value[len(prefix):].strip()
    return value


def handle_vision_command(text: str, *, allow_actions: bool = True) -> str | None:
    """Intercepta somente comandos explícitos do Vision Portal."""
    command = _normalize_command(text)
    if command in FILTER_COMMANDS:
        return filter_summary()
    if command in STATUS_COMMANDS:
        return vision_status()
    if command in OPEN_COMMANDS:
        if not allow_actions:
            return (
                "O comando existe, mas abrir a câmera do PC exige execução local. "
                "O Watch/Mobile não pode ativar remotamente o STAR Vision Portal."
            )
        return launch_portal()
    if command in STOP_COMMANDS:
        if not allow_actions:
            return "Encerrar o STAR Vision Portal exige execução local no PC."
        return stop_portal()
    return None
