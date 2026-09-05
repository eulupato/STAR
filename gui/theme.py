"""Tema visual oficial da interface 2D STAR OS.

As cores seguem ``STAR_MANIFEST.json``. As funções de desenho são leves e
reutilizáveis para evitar reconstruções caras durante hover.
"""
from __future__ import annotations

import random

BG = "#080B12"
BG_ALT = "#0B1220"
PANEL = "#111827"
PANEL_2 = "#121B2B"
PANEL_3 = "#182338"
BORDER = "#2A3951"
TEXT = "#FFFFFF"
MUTED = "#A8B0C0"
SOFT = "#6F788B"
GOLD = "#F6D35F"
PINK = "#F18ACB"
BLUE = "#6CC8FF"
BLUE_SOFT = "#A8DEFF"
GREEN = "#75D99C"
RED = "#FF7C87"
WHITE = "#FFFFFF"

BODY_FONT = ("Segoe UI", 10)
BODY_BOLD = ("Segoe UI", 10, "bold")
SMALL_FONT = ("Segoe UI", 8)
SMALL_BOLD = ("Segoe UI", 8, "bold")
PIXEL_TITLE = ("Courier New", 18, "bold")
PIXEL_LABEL = ("Courier New", 9, "bold")


def round_rect(canvas, x1, y1, x2, y2, radius=18, **kwargs):
    """Retângulo arredondado via polygon/smooth, sem dependências extras."""
    radius = max(2, min(radius, abs(x2 - x1) / 2, abs(y2 - y1) / 2))
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=12, **kwargs)


def draw_starfield(canvas, width, height, *, seed=1, clouds=False):
    """Desenha fundo espacial determinístico e barato.

    O desenho acontece apenas em criação/resize com debounce; não existe loop de
    redraw por hover.
    """
    canvas.delete("star_bg")
    canvas.create_rectangle(0, 0, width, height, fill=BG, outline="", tags="star_bg")
    rng = random.Random(seed)
    count = max(45, min(145, int(width * height / 10000)))
    for _ in range(count):
        x = rng.randint(4, max(5, width - 4))
        y = rng.randint(4, max(5, int(height * .82)))
        size = rng.choice((1, 1, 1, 2, 2, 3))
        color = rng.choice(("#FFFFFF", "#BFD8FF", "#8AA0C5", "#F7D5EC"))
        canvas.create_rectangle(x, y, x + size, y + size, fill=color, outline="", tags="star_bg")
    if clouds:
        for base_x, base_y, scale in ((.08, .28, 1.0), (.66, .25, .9), (.02, .62, .8), (.74, .58, 1.15)):
            x = width * base_x; y = height * base_y
            color = "#171C2B"
            canvas.create_oval(x, y, x + 130*scale, y + 48*scale, fill=color, outline="", tags="star_bg")
            canvas.create_oval(x + 45*scale, y - 26*scale, x + 125*scale, y + 45*scale, fill=color, outline="", tags="star_bg")
            canvas.create_oval(x + 95*scale, y + 4*scale, x + 205*scale, y + 53*scale, fill=color, outline="", tags="star_bg")
    canvas.tag_lower("star_bg")
