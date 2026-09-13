"""STAR Vision — controle do STAR Vision Portal V1.

O módulo mantém toda a lógica leve e testável sem importar OpenCV ou MediaPipe no
startup. As dependências de visão só são carregadas pelo cliente da câmera.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "clients" / "star_vision_portal.py"

PORTAL_FILTERS = (
    {"key": "hologram", "name": "Hologram", "description": "grade ciano, scanlines e brilho Plasma"},
    {"key": "neon", "name": "Neon", "description": "duotone responsivo à luminância"},
    {"key": "halftone", "name": "Halftone", "description": "trama de pontos monocromática"},
    {"key": "chromatic", "name": "Chromatic", "description": "aberração RGB com scanlines"},
    {"key": "thermal", "name": "Thermal", "description": "mapa térmico pseudocolorido"},
    {"key": "vintage", "name": "Vintage", "description": "sépia, vinheta e grão controlado"},
    {"key": "frosted", "name": "Frosted", "description": "vidro fosco luminoso"},
    {"key": "magenta", "name": "Magenta", "description": "halftone rosa/magenta"},
    {"key": "edges", "name": "Edges", "description": "contornos luminosos sobre fundo escuro"},
    {"key": "night", "name": "Night", "description": "visão noturna com contraste adaptativo"},
    {"key": "xray", "name": "X-Ray", "description": "negativo frio com realce de bordas"},
    {"key": "cyber", "name": "Cyber", "description": "paleta ciano/violeta com posterização"},
)

OPEN_COMMANDS = {
    "abra o portal visual", "abra o portal de visao", "abra o portal star",
    "ative o portal visual", "ative o portal de visao", "inicie o portal visual",
    "inicie o portal de visao", "portal visual", "portal de realidade aumentada",
    "star vision", "star vision portal", "open vision portal", "open star vision portal",
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
    """Gesto de fechamento com histerese, cooldown e confirmação temporal."""

    close_ratio: float = 0.17
    reopen_ratio: float = 0.29
    confirm_frames: int = 3
    cooldown_seconds: float = 0.55
    closed: bool = False
    _close_frames: int = 0
    _last_trigger: float = -999.0

    def update(self, portal_width: float, frame_width: float, now: float | None = None) -> bool:
        if frame_width <= 0:
            return False
        now = time.monotonic() if now is None else float(now)
        ratio = float(portal_width) / float(frame_width)

        if self.closed:
            if ratio >= self.reopen_ratio:
                self.closed = False
                self._close_frames = 0
            return False

        if ratio <= self.close_ratio:
            self._close_frames += 1
        else:
            self._close_frames = 0

        if self._close_frames < max(1, int(self.confirm_frames)):
            return False
        if now - self._last_trigger < self.cooldown_seconds:
            return False

        self.closed = True
        self._close_frames = 0
        self._last_trigger = now
        return True


@dataclass
class AdaptivePointSmoother:
    """EMA adaptativa: suave parado, responsiva quando a mão acelera."""

    min_alpha: float = 0.16
    max_alpha: float = 0.64
    speed_for_max: float = 90.0
    points: list[tuple[float, float]] | None = None

    def reset(self) -> None:
        self.points = None

    def update(self, points: list[tuple[float, float]]) -> list[tuple[float, float]]:
        clean = [(float(x), float(y)) for x, y in points]
        if self.points is None or len(self.points) != len(clean):
            self.points = clean
            return list(clean)

        out: list[tuple[float, float]] = []
        for (px, py), (x, y) in zip(self.points, clean):
            speed = math.hypot(x - px, y - py)
            t = min(1.0, speed / max(1e-6, self.speed_for_max))
            alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * t
            sx = px + alpha * (x - px)
            sy = py + alpha * (y - py)
            out.append((sx, sy))
        self.points = out
        return list(out)


@dataclass
class GeometryGate:
    """Recusa polígonos pequenos/degenerados e saltos absurdos entre frames."""

    min_area_ratio: float = 0.008
    max_jump_ratio: float = 0.25
    _last_center: tuple[float, float] | None = None

    @staticmethod
    def polygon_area(points: list[tuple[float, float]]) -> float:
        if len(points) < 3:
            return 0.0
        total = 0.0
        for index, (x1, y1) in enumerate(points):
            x2, y2 = points[(index + 1) % len(points)]
            total += x1 * y2 - x2 * y1
        return abs(total) * 0.5

    def accept(self, points: list[tuple[float, float]], frame_w: int, frame_h: int) -> bool:
        if frame_w <= 0 or frame_h <= 0 or len(points) != 4:
            return False
        area = self.polygon_area(points)
        if area < frame_w * frame_h * self.min_area_ratio:
            return False
        center = (
            sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points),
        )
        if self._last_center is not None:
            diagonal = math.hypot(frame_w, frame_h)
            jump = math.hypot(center[0] - self._last_center[0], center[1] - self._last_center[1])
            if diagonal > 0 and jump / diagonal > self.max_jump_ratio:
                self._last_center = center
                return False
        self._last_center = center
        return True


@dataclass
class PerformanceGovernor:
    """Escolhe escala de processamento visando fluidez em hardware variado."""

    target_fps: float = 30.0
    scale: float = 1.0
    _samples: list[float] = field(default_factory=list)

    def update(self, fps: float) -> float:
        if fps <= 0:
            return self.scale
        self._samples.append(float(fps))
        if len(self._samples) > 20:
            self._samples.pop(0)
        if len(self._samples) < 10:
            return self.scale
        avg = sum(self._samples) / len(self._samples)
        if avg < self.target_fps * 0.68:
            self.scale = max(0.55, self.scale - 0.1)
            self._samples.clear()
        elif avg > self.target_fps * 1.22 and self.scale < 1.0:
            self.scale = min(1.0, self.scale + 0.05)
            self._samples.clear()
        return self.scale


_portal_process: subprocess.Popen | None = None


def dependency_status() -> dict[str, bool]:
    return {
        "opencv": importlib.util.find_spec("cv2") is not None,
        "mediapipe": importlib.util.find_spec("mediapipe") is not None,
        "numpy": importlib.util.find_spec("numpy") is not None,
    }


def dependencies_ready() -> bool:
    return all(dependency_status().values())


def filter_summary() -> str:
    items = "; ".join(f"{item['name']} — {item['description']}" for item in PORTAL_FILTERS)
    return f"STAR Vision Portal V1 possui {len(PORTAL_FILTERS)} filtros: {items}."


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
        f"STAR Vision Portal V1: {state}. Dependências presentes: {installed}. "
        f"Ausentes: {missing}. Filtros: {len(PORTAL_FILTERS)}."
    )


def launch_portal(camera_index: int = 0) -> str:
    global _portal_process
    if portal_running():
        return "O STAR Vision Portal já está aberto."
    missing = [name for name, ok in dependency_status().items() if not ok]
    if missing:
        return (
            "STAR Vision Portal está integrado, mas faltam dependências opcionais: "
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
        "STAR Vision Portal V1 iniciado. Abra as duas mãos com indicador e polegar visíveis; "
        "aproxime as mãos para avançar o filtro. Setas trocam filtros e Q/Esc fecha."
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
    command = _normalize_command(text)
    if command in FILTER_COMMANDS:
        return filter_summary()
    if command in STATUS_COMMANDS:
        return vision_status()
    if command in OPEN_COMMANDS:
        if not allow_actions:
            return (
                "O comando existe, mas abrir a câmera do PC exige execução local. "
                "Watch/Mobile não podem ativar remotamente a webcam."
            )
        return launch_portal()
    if command in STOP_COMMANDS:
        if not allow_actions:
            return "Encerrar o STAR Vision Portal exige execução local no PC."
        return stop_portal()
    return None
