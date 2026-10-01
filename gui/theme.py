"""Tokens visuais "Cosmic Crystal" da STAR.

Derivados das referências da orb violeta de filamentos e da estrela
cristalina de 8 pontas. Sem imports de Tk para permanecer testável headless.
"""
from __future__ import annotations

# Fundo e superfícies
BG_VOID = "#05030D"
BG_DEEP = "#0E0923"
PANEL = "#160F2E"
PANEL_EDGE = "#3A2467"
PANEL_HOVER = "#2A1B4F"
INPUT_BG = "#1C1438"

# Texto
TEXT = "#F3EEFF"
MUTED = "#A99CC9"

# Orb
ORB_CORE = "#57388F"
ORB_MID = "#7E58B3"
ORB_GLOW = "#C49EE0"

# Cristal
CRYSTAL_BLUE = "#555F9F"
CRYSTAL_MID = "#638CBF"
CRYSTAL_LILAC = "#A192C6"
CRYSTAL_LIGHT = "#B5AFD3"
CRYSTAL_PINK = "#E6B8E0"
CRYSTAL_HI = "#E6DCEA"

# Semântica de status
ACCENT_OK = "#76E2A0"
ACCENT_WARN = "#FFD36E"
ACCENT_ERR = "#FF7C87"

# Estados de toggle (verde/vermelho escurecidos para combinar com o violeta)
TOGGLE_ON = "#1F5A48"
TOGGLE_OFF_ALERT = "#5A2645"
RECORDING = "#8B3360"

FONT_FAMILY = "Segoe UI"

STATE_COLORS = {
    "neutral": {"primary": "#7E58B3", "secondary": "#3A2467", "glow": "#C49EE0"},
    "listening": {"primary": "#638CBF", "secondary": "#555F9F", "glow": "#B5AFD3"},
    "thinking": {"primary": "#A192C6", "secondary": "#7E58B3", "glow": "#C49EE0"},
    "speaking": {"primary": "#E6B8E0", "secondary": "#A192C6", "glow": "#E6DCEA"},
    "error": {"primary": "#FF7C87", "secondary": "#7E58B3", "glow": "#FFD36E"},
}

# Parâmetros de animação por estado (velocidade de rotação, pulso, wobble)
STATE_MOTION = {
    "neutral": {"speed": 0.35, "pulse": 0.03, "wobble": 0.04},
    "listening": {"speed": 0.55, "pulse": 0.06, "wobble": 0.07},
    "thinking": {"speed": 0.95, "pulse": 0.04, "wobble": 0.10},
    "speaking": {"speed": 0.70, "pulse": 0.09, "wobble": 0.08},
    "error": {"speed": 0.25, "pulse": 0.02, "wobble": 0.02},
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def rgb_to_hex(rgb) -> str:
    r, g, b = (max(0, min(255, int(round(c)))) for c in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def mix(color_a: str, color_b: str, t: float) -> str:
    """Interpola duas cores hex (t=0 → a, t=1 → b)."""
    t = max(0.0, min(1.0, float(t)))
    a, b = hex_to_rgb(color_a), hex_to_rgb(color_b)
    return rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))
