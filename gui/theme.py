"""Tema visual STAR inspirado no protótipo Base44, sem dependência web."""
from __future__ import annotations

import random
import tkinter as tk

BG = "#070c18"
BG_ALT = "#0b1220"
PANEL = "#0e1627"
PANEL_2 = "#131d31"
PANEL_3 = "#1b2639"
BORDER = "#26324a"
TEXT = "#f3f6ff"
MUTED = "#8b96aa"
SOFT = "#5f6b80"
BLUE = "#5aa6ff"
BLUE_SOFT = "#8fd0ff"
PINK = "#f39bc2"
GOLD = "#ffd36e"
GREEN = "#75d99c"
RED = "#ff7f8f"
WHITE = "#ffffff"

TITLE_FONT = ("Courier New", 16, "bold")
PIXEL_FONT = ("Courier New", 10, "bold")
BODY_FONT = ("Segoe UI", 10)
BODY_BOLD = ("Segoe UI", 10, "bold")
SMALL_FONT = ("Segoe UI", 8)
SMALL_BOLD = ("Segoe UI", 8, "bold")


def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius=18, **kwargs):
    """Desenha retângulo arredondado no Canvas sem dependências extras."""
    r = max(1, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)


def draw_starfield(canvas: tk.Canvas, width: int, height: int, *, seed: int = 44, clouds: bool = False):
    """Desenha o fundo espacial determinístico do STAR OS."""
    canvas.delete("star_bg")
    rng = random.Random(seed)
    canvas.create_rectangle(0, 0, width, height, fill=BG, outline="", tags="star_bg")

    for i in range(10):
        pad = i * 28
        shade = 12 + i
        color = f"#{shade:02x}{(shade+5):02x}{(shade+14):02x}"
        canvas.create_oval(width * .18 + pad, height * .08 + pad, width * .82 - pad, height * .86 - pad,
                           fill=color, outline="", stipple="gray75", tags="star_bg")

    count = max(70, int((width * height) / 11500))
    for _ in range(count):
        x = rng.randint(8, max(9, width - 8))
        y = rng.randint(8, max(9, height - 8))
        size = rng.choice((1, 1, 1, 2, 2, 3))
        color = rng.choice(("#d9e3f3", "#a9b5c8", "#7a8699", "#ffffff"))
        canvas.create_rectangle(x, y, x + size, y + size, fill=color, outline="", tags="star_bg")
        if size == 3 and rng.random() < .35:
            canvas.create_line(x - 4, y + 1, x + 7, y + 1, fill="#667288", tags="star_bg")
            canvas.create_line(x + 1, y - 4, x + 1, y + 7, fill="#667288", tags="star_bg")

    if clouds:
        _draw_cloud(canvas, width * .12, height * .30, 1.35, "#202738")
        _draw_cloud(canvas, width * .70, height * .29, 1.20, "#302a37")
        _draw_cloud(canvas, width * .02, height * .55, .95, "#181f2e")
        _draw_cloud(canvas, width * .80, height * .57, 1.05, "#1b2230")
        canvas.create_polygon(0, height*.82, width*.10, height*.76, width*.23, height*.86,
                              width*.41, height*.78, width*.61, height*.87, width*.78, height*.80,
                              width, height*.84, width, height, 0, height,
                              fill="#080d18", outline="", tags="star_bg")
    canvas.tag_lower("star_bg")


def _draw_cloud(canvas: tk.Canvas, x, y, scale, color):
    tag = "star_bg"
    parts = [
        (-34, 10, 78, 38), (-12, -6, 50, 35), (22, 3, 95, 39), (58, 10, 120, 38)
    ]
    for x1, y1, x2, y2 in parts:
        canvas.create_oval(x + x1*scale, y + y1*scale, x + x2*scale, y + y2*scale,
                           fill=color, outline="", tags=tag)
    canvas.create_rectangle(x - 12*scale, y + 18*scale, x + 93*scale, y + 38*scale,
                            fill=color, outline="", tags=tag)
