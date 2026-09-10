"""STAR Watch Functional Beta — visual preview and local PC client.

This client is intentionally a thin endpoint over the existing STAR Core. It does
not duplicate identity, memory, knowledge or reasoning and it never loads STAR
WORLD. The same DeviceRuntime profile used by the Android watch drives the theme.
"""
from __future__ import annotations

import math
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import VOICE_CHAT_MODE
from core.device_runtime import DeviceRuntime
from main import create_star
from voice.audio_input import AudioRecorder
from voice.manager import VoiceManager

WATCH_SCREENS = ("home", "talk", "health", "gps", "vision", "settings")
SCREEN_LABELS = {
    "home": "HOME",
    "talk": "VOZ",
    "health": "SAÚDE",
    "gps": "GPS",
    "vision": "VISÃO",
    "settings": "CONFIG",
}

DEFAULT_THEME = {
    "background": "#05070D",
    "surface": "#0C1220",
    "primary": "#7AD7FF",
    "secondary": "#B58CFF",
    "accent": "#F28BD8",
    "text": "#FFFFFF",
    "muted": "#8E9AAF",
    "gold": "#F6D35F",
    "danger": "#FF6B8A",
    "energy_blue": "#4F7BFF",
    "energy_cyan": "#6FE7FF",
    "energy_violet": "#9B72FF",
    "energy_pink": "#FF79C8",
}


def _hex_to_rgb(value: str):
    value = str(value or "").lstrip("#")
    if len(value) != 6:
        return 255, 255, 255
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return 255, 255, 255


def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(
        *[max(0, min(255, int(round(v)))) for v in rgb]
    )


def mix_color(a: str, b: str, amount: float) -> str:
    amount = max(0.0, min(1.0, float(amount)))
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    return _rgb_to_hex((
        ar + (br - ar) * amount,
        ag + (bg - ag) * amount,
        ab + (bb - ab) * amount,
    ))


def watch_runtime_profile():
    runtime = DeviceRuntime(ROOT / "STAR_MANIFEST.json")
    return runtime.profile_for(
        {
            "name": "STAR Watch PC Preview",
            "metadata": {
                "platform": "windows",
                "form_factor": "watch",
                "os_version": sys.platform,
                "app_version": "0.3.0-beta",
                "screen_width": 440,
                "screen_height": 520,
            },
        }
    )


class StarWatchPC:
    WIDTH = 440
    HEIGHT = 520
    FRAME_MS = 50

    def __init__(self):
        self.runtime = watch_runtime_profile()
        self.theme = dict(DEFAULT_THEME)
        self.theme.update(self.runtime.get("theme") or {})
        self.profile = dict(self.runtime.get("profile") or {})

        self.star = create_star()
        self.voice_manager = None
        self.recorder = AudioRecorder()
        self.voice_output_enabled = True
        self.animations_enabled = True
        self.recording = False
        self.processing = False
        self.closed = False

        self.screen_index = 0
        self.screen = WATCH_SCREENS[self.screen_index]
        self.state = "idle"
        self.status = "PRONTA"
        self.last_user_text = ""
        self.last_response = "Toque no núcleo da STAR ou abra VOZ para conversar."
        self.logo_animation_started = None
        self.energy_phase = 0.0
        self.drag_start = None
        self.drag_started_at = None
        self.settings_rows = []

        self.root = tk.Tk()
        self.root.title("STAR Watch — Functional Beta")
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=self.theme["background"])

        self.canvas = tk.Canvas(
            self.root,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg=self.theme["background"],
            highlightthickness=0,
            bd=0,
        )
        self.canvas.place(x=0, y=0, width=self.WIDTH, height=self.HEIGHT)

        self.entry = tk.Entry(
            self.root,
            bd=0,
            relief="flat",
            bg=self.theme["surface"],
            fg=self.theme["text"],
            insertbackground=self.theme["text"],
            font=("Segoe UI", 11),
        )
        self.send_button = tk.Button(
            self.root,
            text="ENVIAR",
            command=self.send_text,
            bd=0,
            relief="flat",
            bg=self.theme["primary"],
            fg="#06111A",
            activebackground=self.theme["secondary"],
            activeforeground="#06111A",
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.root.bind("<Left>", lambda _e: self.navigate(-1))
        self.root.bind("<Right>", lambda _e: self.navigate(1))
        self.root.bind("<space>", lambda _e: self.toggle_voice())
        self.root.bind("<Escape>", lambda _e: self.close())
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.render()
        self._animate()
        self._tick_clock()

    def run(self):
        self.root.mainloop()

    def _voice(self):
        if self.voice_manager is None:
            manager = VoiceManager()
            try:
                manager.set_voice_mode(VOICE_CHAT_MODE)
            except Exception:
                pass
            self.voice_manager = manager
        return self.voice_manager

    def _tick_clock(self):
        if self.closed:
            return
        if self.screen == "home":
            self.render()
        self.root.after(1000, self._tick_clock)

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=24,
            **kwargs,
        )

    def _perimeter_points(self, margin=11, radius=31, straight=12, curve=8):
        w, h = self.WIDTH, self.HEIGHT
        left, top, right, bottom = margin, margin, w - margin, h - margin
        points = []

        for i in range(straight + 1):
            t = i / straight
            points.append((left + radius + (right - left - 2 * radius) * t, top))
        for i in range(1, curve + 1):
            angle = -math.pi / 2 + (math.pi / 2) * (i / curve)
            points.append((right - radius + radius * math.cos(angle),
                           top + radius + radius * math.sin(angle)))
        for i in range(1, straight + 1):
            t = i / straight
            points.append((right, top + radius + (bottom - top - 2 * radius) * t))
        for i in range(1, curve + 1):
            angle = (math.pi / 2) * (i / curve)
            points.append((right - radius + radius * math.cos(angle),
                           bottom - radius + radius * math.sin(angle)))
        for i in range(1, straight + 1):
            t = i / straight
            points.append((right - radius - (right - left - 2 * radius) * t, bottom))
        for i in range(1, curve + 1):
            angle = math.pi / 2 + (math.pi / 2) * (i / curve)
            points.append((left + radius + radius * math.cos(angle),
                           bottom - radius + radius * math.sin(angle)))
        for i in range(1, straight + 1):
            t = i / straight
            points.append((left, bottom - radius - (bottom - top - 2 * radius) * t))
        for i in range(1, curve + 1):
            angle = math.pi + (math.pi / 2) * (i / curve)
            points.append((left + radius + radius * math.cos(angle),
                           top + radius + radius * math.sin(angle)))
        return points

    def _state_palette(self):
        if self.state == "listening":
            return [
                self.theme["energy_cyan"],
                self.theme["energy_blue"],
                self.theme["energy_cyan"],
                self.theme["energy_violet"],
            ]
        if self.state == "thinking":
            return [
                self.theme["energy_violet"],
                self.theme["energy_pink"],
                self.theme["energy_blue"],
                self.theme["energy_violet"],
            ]
        if self.state == "speaking":
            return [
                self.theme["energy_cyan"],
                self.theme["energy_blue"],
                self.theme["energy_violet"],
                self.theme["energy_pink"],
            ]
        if self.state == "error":
            return [
                self.theme["danger"],
                self.theme["energy_pink"],
                self.theme["gold"],
                self.theme["danger"],
            ]
        return [
            mix_color(self.theme["energy_blue"], self.theme["background"], 0.42),
            mix_color(self.theme["energy_violet"], self.theme["background"], 0.45),
            mix_color(self.theme["energy_pink"], self.theme["background"], 0.62),
            mix_color(self.theme["energy_cyan"], self.theme["background"], 0.58),
        ]

    def _draw_energy_frame(self):
        self.canvas.delete("energy")
        points = self._perimeter_points()
        palette = self._state_palette()
        count = len(points)
        if count < 2:
            return

        for i in range(count):
            p1 = points[i]
            p2 = points[(i + 1) % count]
            phase = ((i / count) + self.energy_phase) % 1.0
            scaled = phase * len(palette)
            idx = int(scaled) % len(palette)
            nxt = (idx + 1) % len(palette)
            color = mix_color(palette[idx], palette[nxt], scaled - int(scaled))
            self.canvas.create_line(
                p1[0], p1[1], p2[0], p2[1],
                fill=mix_color(color, self.theme["background"], 0.60),
                width=9,
                capstyle=tk.ROUND,
                tags=("energy",),
            )
            self.canvas.create_line(
                p1[0], p1[1], p2[0], p2[1],
                fill=color,
                width=3,
                capstyle=tk.ROUND,
                tags=("energy",),
            )

    def _draw_logo(self, cx, cy, radius=43, tag="logo"):
        self.canvas.delete(tag)
        pulse = 0.0
        if self.animations_enabled:
            pulse = (math.sin(time.monotonic() * 2.2) + 1.0) * 0.5
        halo = mix_color(
            self.theme["secondary"],
            self.theme["background"],
            0.74 - pulse * 0.08,
        )
        self.canvas.create_oval(
            cx - radius - 10,
            cy - radius - 10,
            cx + radius + 10,
            cy + radius + 10,
            outline=halo,
            width=7,
            tags=(tag,),
        )
        self.canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            outline=self.theme["primary"],
            width=2,
            tags=(tag,),
        )

        p = 0.0
        if self.logo_animation_started is not None:
            elapsed = time.monotonic() - self.logo_animation_started
            if elapsed >= 0.72:
                self.logo_animation_started = None
            else:
                p = math.sin(math.pi * (elapsed / 0.72))

        triangle_color = mix_color(
            self.theme["primary"], self.theme["background"], p * 0.88
        )
        star_color = mix_color(
            self.theme["accent"], self.theme["background"], (1.0 - p) * 0.96
        )

        tri = [
            cx - radius * 0.48, cy - radius * 0.34,
            cx + radius * 0.48, cy - radius * 0.34,
            cx, cy + radius * 0.52,
        ]
        self.canvas.create_polygon(
            tri,
            fill="",
            outline=triangle_color,
            width=3,
            tags=(tag,),
        )

        outer = radius * 0.52
        inner = outer * 0.42
        star = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            r = outer if i % 2 == 0 else inner
            star.extend((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        self.canvas.create_polygon(
            star,
            fill="",
            outline=star_color,
            width=max(1, int(3 * p)),
            tags=(tag,),
        )

    def _draw_header(self, title, subtitle=None):
        self.canvas.create_text(
            30, 30,
            anchor="nw",
            text=title,
            fill=self.theme["text"],
            font=("Segoe UI Semibold", 12),
            tags=("content",),
        )
        self.canvas.create_text(
            self.WIDTH - 30, 31,
            anchor="ne",
            text="● CORE LOCAL",
            fill=self.theme["primary"] if self.state != "error" else self.theme["danger"],
            font=("Segoe UI", 8),
            tags=("content",),
        )
        if subtitle:
            self.canvas.create_text(
                30, 51,
                anchor="nw",
                text=subtitle,
                fill=self.theme["muted"],
                font=("Segoe UI", 8),
                tags=("content",),
            )

    def _draw_nav(self):
        y = self.HEIGHT - 34
        cell = (self.WIDTH - 34) / len(WATCH_SCREENS)
        self.canvas.create_line(
            24, y - 18, self.WIDTH - 24, y - 18,
            fill=mix_color(self.theme["muted"], self.theme["background"], 0.75),
            width=1,
            tags=("content",),
        )
        for index, name in enumerate(WATCH_SCREENS):
            x = 17 + cell * index + cell / 2
            active = name == self.screen
            self.canvas.create_text(
                x, y,
                text=SCREEN_LABELS[name],
                fill=self.theme["primary"] if active else self.theme["muted"],
                font=("Segoe UI Semibold" if active else "Segoe UI", 7),
                tags=("content", f"nav:{index}"),
            )
            if active:
                self.canvas.create_oval(
                    x - 2, y + 10, x + 2, y + 14,
                    fill=self.theme["accent"],
                    outline="",
                    tags=("content",),
                )

    def _draw_home(self):
        now = datetime.now()
        self._draw_header("STAR WATCH", "Functional Beta • PC Preview")
        self.canvas.create_text(
            self.WIDTH / 2, 92,
            text=now.strftime("%H:%M"),
            fill=self.theme["text"],
            font=("Segoe UI Light", 32),
            tags=("content",),
        )
        self.canvas.create_text(
            self.WIDTH / 2, 126,
            text=now.strftime("%d/%m/%Y"),
            fill=self.theme["muted"],
            font=("Segoe UI", 9),
            tags=("content",),
        )
        self._draw_logo(self.WIDTH / 2, 232, 48)
        self.canvas.create_text(
            self.WIDTH / 2, 306,
            text=self.status,
            fill=self.theme["primary"],
            font=("Segoe UI Semibold", 10),
            tags=("content",),
        )
        self.canvas.create_text(
            self.WIDTH / 2, 339,
            width=330,
            justify="center",
            text="Toque no núcleo para falar. Arraste para os lados para trocar de função.",
            fill=self.theme["muted"],
            font=("Segoe UI", 9),
            tags=("content",),
        )
        self._rounded_rect(
            73, 380, self.WIDTH - 73, 426, 18,
            fill=self.theme["surface"],
            outline=mix_color(self.theme["primary"], self.theme["background"], 0.55),
            width=1,
            tags=("content", "quick:talk"),
        )
        self.canvas.create_text(
            self.WIDTH / 2, 403,
            text="FALAR COM A STAR",
            fill=self.theme["text"],
            font=("Segoe UI Semibold", 9),
            tags=("content", "quick:talk"),
        )

    def _draw_talk(self):
        self._draw_header("CONVERSA", self.status)
        self._draw_logo(self.WIDTH / 2, 132, 36)
        state_text = {
            "idle": "TOQUE PARA FALAR",
            "listening": "ESTOU OUVINDO",
            "thinking": "PENSANDO NO PC",
            "speaking": "RESPONDENDO",
            "error": "ATENÇÃO",
        }.get(self.state, self.status)
        self.canvas.create_text(
            self.WIDTH / 2, 191,
            text=state_text,
            fill=self.theme["primary"] if self.state != "error" else self.theme["danger"],
            font=("Segoe UI Semibold", 9),
            tags=("content",),
        )

        if self.last_user_text:
            self.canvas.create_text(
                40, 229,
                anchor="nw",
                width=360,
                text="VOCÊ\n" + self.last_user_text,
                fill=self.theme["muted"],
                font=("Segoe UI", 9),
                tags=("content",),
            )
        self.canvas.create_text(
            40, 294 if self.last_user_text else 239,
            anchor="nw",
            width=360,
            text="STAR\n" + self.last_response,
            fill=self.theme["text"],
            font=("Segoe UI", 10),
            tags=("content",),
        )
        self.entry.place(x=38, y=407, width=280, height=36)
        self.send_button.place(x=326, y=407, width=76, height=36)

    def _draw_health(self):
        self._draw_header("SAÚDE", "Endpoint de sensores • sem dados simulados")
        self.canvas.create_text(
            self.WIDTH / 2, 105,
            text="HEALTH LINK",
            fill=self.theme["secondary"],
            font=("Segoe UI Light", 24),
            tags=("content",),
        )
        rows = [
            ("BATIMENTOS", "AGUARDANDO SMARTWATCH"),
            ("MOVIMENTO", "AGUARDANDO SMARTWATCH"),
            ("SONO", "AGUARDANDO SMARTWATCH"),
        ]
        y = 166
        for label, value in rows:
            self._rounded_rect(
                48, y, self.WIDTH - 48, y + 62, 18,
                fill=self.theme["surface"],
                outline=mix_color(self.theme["secondary"], self.theme["background"], 0.66),
                width=1,
                tags=("content",),
            )
            self.canvas.create_text(
                66, y + 17,
                anchor="nw",
                text=label,
                fill=self.theme["text"],
                font=("Segoe UI Semibold", 9),
                tags=("content",),
            )
            self.canvas.create_text(
                66, y + 38,
                anchor="nw",
                text=value,
                fill=self.theme["muted"],
                font=("Segoe UI", 8),
                tags=("content",),
            )
            y += 76
        self.canvas.create_text(
            self.WIDTH / 2, 406,
            width=330,
            text="A análise de saúde ficará condicionada aos sensores e permissões reais do relógio.",
            fill=self.theme["muted"],
            font=("Segoe UI", 8),
            justify="center",
            tags=("content",),
        )

    def _draw_gps(self):
        self._draw_header("GPS", "Preview visual • localização real ainda não conectada")
        self._rounded_rect(
            45, 86, self.WIDTH - 45, 382, 24,
            fill="#080D17",
            outline=mix_color(self.theme["accent"], self.theme["background"], 0.65),
            width=1,
            tags=("content",),
        )
        for x in range(78, self.WIDTH - 45, 48):
            self.canvas.create_line(
                x, 104, x - 28, 365,
                fill="#111B2B",
                width=1,
                tags=("content",),
            )
        for y in range(118, 370, 45):
            self.canvas.create_line(
                58, y, self.WIDTH - 58, y + 22,
                fill="#111B2B",
                width=1,
                tags=("content",),
            )
        route = [84, 325, 128, 290, 161, 303, 205, 249, 244, 259, 295, 188, 354, 143]
        self.canvas.create_line(
            *route,
            fill=mix_color(self.theme["accent"], self.theme["background"], 0.28),
            width=5,
            smooth=True,
            tags=("content",),
        )
        self.canvas.create_text(
            self.WIDTH / 2, 221,
            text="DEMO VISUAL",
            fill=self.theme["muted"],
            font=("Segoe UI Semibold", 9),
            tags=("content",),
        )
        self.canvas.create_text(
            self.WIDTH / 2, 408,
            width=320,
            text="No relógio real, a rota só aparece após permissão de localização e dados GPS verdadeiros.",
            fill=self.theme["muted"],
            font=("Segoe UI", 8),
            justify="center",
            tags=("content",),
        )

    def _draw_vision(self):
        self._draw_header("STAR VISION", "Câmera como extensão sensorial")
        self.canvas.create_oval(
            123, 115, self.WIDTH - 123, 257,
            outline=self.theme["primary"],
            width=2,
            tags=("content",),
        )
        self.canvas.create_oval(
            185, 162, 255, 232,
            outline=self.theme["secondary"],
            width=4,
            tags=("content",),
        )
        self.canvas.create_oval(
            210, 187, 230, 207,
            fill=self.theme["accent"],
            outline="",
            tags=("content",),
        )
        self.canvas.create_text(
            self.WIDTH / 2, 296,
            text="TRANSPORTE DE CÂMERA: PREPARADO",
            fill=self.theme["primary"],
            font=("Segoe UI Semibold", 9),
            tags=("content",),
        )
        self.canvas.create_text(
            self.WIDTH / 2, 335,
            width=330,
            justify="center",
            text=(
                "O cliente Android já consegue enviar imagens ao PC. "
                "A STAR ainda não possui Vision Engine nesta versão, então nenhuma análise visual é simulada."
            ),
            fill=self.theme["muted"],
            font=("Segoe UI", 9),
            tags=("content",),
        )

    def _draw_settings(self):
        self._draw_header("CONFIGURAÇÕES", "Perfil watch • fonte central no PC")
        rows = [
            ("RESPOSTA FALADA", "ATIVA" if self.voice_output_enabled else "DESATIVADA", "toggle:voice"),
            ("ANIMAÇÕES", "ATIVAS" if self.animations_enabled else "DESATIVADAS", "toggle:animations"),
            ("SEGURANÇA", "AÇÕES REMOTAS BLOQUEADAS", None),
            ("AUTENTICAÇÃO", "PAREAMENTO POR TOKEN NO RELÓGIO", None),
            ("IDENTIDADE", f"{self.star.get_name()} • CRIADOR {self.star.get_creator()}", None),
        ]
        self.settings_rows = []
        y = 92
        for label, value, action in rows:
            self._rounded_rect(
                45, y, self.WIDTH - 45, y + 55, 16,
                fill=self.theme["surface"],
                outline=mix_color(self.theme["primary"], self.theme["background"], 0.72),
                width=1,
                tags=("content", action or "static"),
            )
            self.canvas.create_text(
                62, y + 12,
                anchor="nw",
                text=label,
                fill=self.theme["text"],
                font=("Segoe UI Semibold", 8),
                tags=("content", action or "static"),
            )
            self.canvas.create_text(
                self.WIDTH - 62, y + 34,
                anchor="ne",
                text=value,
                fill=self.theme["primary"] if action else self.theme["muted"],
                font=("Segoe UI", 7),
                tags=("content", action or "static"),
            )
            if action:
                self.settings_rows.append((45, y, self.WIDTH - 45, y + 55, action))
            y += 66

        self.canvas.create_text(
            self.WIDTH / 2, 435,
            width=330,
            justify="center",
            text="Biometria facial/voz e Permission Manager completo ainda não estão implementados.",
            fill=self.theme["muted"],
            font=("Segoe UI", 8),
            tags=("content",),
        )

    def render(self):
        if self.closed:
            return
        self.canvas.delete("content")
        self.canvas.delete("logo")
        self.entry.place_forget()
        self.send_button.place_forget()

        if self.screen == "home":
            self._draw_home()
        elif self.screen == "talk":
            self._draw_talk()
        elif self.screen == "health":
            self._draw_health()
        elif self.screen == "gps":
            self._draw_gps()
        elif self.screen == "vision":
            self._draw_vision()
        else:
            self._draw_settings()
        self._draw_nav()

    def _animate(self):
        if self.closed:
            return
        if self.animations_enabled:
            speed = {
                "idle": 0.0025,
                "listening": 0.010,
                "thinking": 0.016,
                "speaking": 0.012,
                "error": 0.004,
            }.get(self.state, 0.004)
            self.energy_phase = (self.energy_phase + speed) % 1.0
        self._draw_energy_frame()
        if self.screen in {"home", "talk"}:
            if self.screen == "home":
                self._draw_logo(self.WIDTH / 2, 232, 48)
            else:
                self._draw_logo(self.WIDTH / 2, 132, 36)
        self.root.after(self.FRAME_MS, self._animate)

    def set_state(self, state: str, status: str | None = None):
        self.state = state
        if status:
            self.status = status
        self.render()

    def navigate(self, direction: int):
        if self.recording or self.processing:
            return
        self.screen_index = (self.screen_index + int(direction)) % len(WATCH_SCREENS)
        self.screen = WATCH_SCREENS[self.screen_index]
        self.render()

    def open_screen(self, name: str):
        if name not in WATCH_SCREENS or self.recording or self.processing:
            return
        self.screen_index = WATCH_SCREENS.index(name)
        self.screen = name
        self.render()

    def _hit_logo(self, x, y):
        cy = 232 if self.screen == "home" else 132
        radius = 65 if self.screen == "home" else 52
        return self.screen in {"home", "talk"} and ((x - self.WIDTH / 2) ** 2 + (y - cy) ** 2) <= radius ** 2

    def _hit_nav(self, x, y):
        if y < self.HEIGHT - 66:
            return None
        cell = (self.WIDTH - 34) / len(WATCH_SCREENS)
        index = int((x - 17) / cell)
        if 0 <= index < len(WATCH_SCREENS):
            return index
        return None

    def _on_press(self, event):
        self.drag_start = (event.x, event.y)
        self.drag_started_at = time.monotonic()

    def _on_release(self, event):
        if self.drag_start is None:
            return
        sx, sy = self.drag_start
        elapsed = time.monotonic() - (self.drag_started_at or time.monotonic())
        dx, dy = event.x - sx, event.y - sy
        self.drag_start = None
        self.drag_started_at = None

        if abs(dx) > 55 and abs(dx) > abs(dy):
            self.navigate(-1 if dx > 0 else 1)
            return
        if elapsed > 0.75 and abs(dx) < 20 and abs(dy) < 20:
            self.open_screen("settings")
            return

        nav = self._hit_nav(event.x, event.y)
        if nav is not None:
            self.open_screen(WATCH_SCREENS[nav])
            return

        if self._hit_logo(event.x, event.y):
            self.logo_animation_started = time.monotonic()
            self.toggle_voice()
            return

        if self.screen == "home" and 73 <= event.x <= self.WIDTH - 73 and 380 <= event.y <= 426:
            self.open_screen("talk")
            return

        if self.screen == "settings":
            for x1, y1, x2, y2, action in self.settings_rows:
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    if action == "toggle:voice":
                        self.voice_output_enabled = not self.voice_output_enabled
                    elif action == "toggle:animations":
                        self.animations_enabled = not self.animations_enabled
                    self.render()
                    return

    def _on_double_click(self, _event):
        if not self.recording and not self.processing:
            self.open_screen("home")

    def _on_mousewheel(self, event):
        self.navigate(-1 if event.delta > 0 else 1)

    def toggle_voice(self):
        if self.processing:
            return
        if self.recording:
            self.stop_voice()
        else:
            self.start_voice()

    def start_voice(self):
        if not self.recorder.available:
            self.set_state("error", "MICROFONE INDISPONÍVEL")
            self.last_response = "sounddevice não está disponível neste ambiente."
            self.open_screen("talk")
            return
        try:
            self._voice().cancel_speech()
            self.recorder.start()
            self.recording = True
            self.open_screen("talk")
            self.set_state("listening", "OUVINDO")
        except Exception as exc:
            self.recording = False
            self.last_response = f"Não consegui abrir o microfone: {type(exc).__name__}: {exc}"
            self.set_state("error", "ERRO DE MICROFONE")

    def stop_voice(self):
        if not self.recording:
            return
        try:
            path = self.recorder.stop_to_wav()
        except Exception as exc:
            self.recording = False
            self.last_response = f"Falha ao encerrar a gravação: {type(exc).__name__}: {exc}"
            self.set_state("error", "ERRO DE ÁUDIO")
            return

        self.recording = False
        if path is None:
            self.set_state("idle", "PRONTA")
            return
        self.processing = True
        self.set_state("thinking", "TRANSCRIBINDO")

        def worker():
            try:
                transcript = self._voice().transcribe(path)
                response = str(self.star.process(transcript, allow_actions=False))
                self.root.after(0, lambda: self._complete_interaction(transcript, response))
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                self.root.after(0, lambda: self._interaction_error(message))
            finally:
                try:
                    Path(path).unlink(missing_ok=True)
                except OSError:
                    pass

        threading.Thread(target=worker, daemon=True, name="STAR-Watch-STT").start()

    def send_text(self):
        if self.processing:
            return
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.processing = True
        self.last_user_text = text
        self.set_state("thinking", "PENSANDO")

        def worker():
            try:
                response = str(self.star.process(text, allow_actions=False))
                self.root.after(0, lambda: self._complete_interaction(text, response))
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                self.root.after(0, lambda: self._interaction_error(message))

        threading.Thread(target=worker, daemon=True, name="STAR-Watch-Text").start()

    def _complete_interaction(self, user_text, response):
        self.processing = False
        self.last_user_text = user_text
        self.last_response = response
        self.set_state("speaking" if self.voice_output_enabled else "idle", "RESPONDENDO")
        self.open_screen("talk")

        if not self.voice_output_enabled:
            self.set_state("idle", "PRONTA")
            return

        def spoken(ok, error):
            if self.closed:
                return
            if ok:
                self.root.after(0, lambda: self.set_state("idle", "PRONTA"))
            else:
                message = error or "A resposta textual funcionou, mas a voz não pôde ser reproduzida."
                self.root.after(0, lambda: self._voice_output_error(message))

        self._voice().speak_async(response, callback=spoken)

    def _voice_output_error(self, message):
        self.last_response = self.last_response + "\n\nVoz: " + str(message)
        self.set_state("error", "VOZ INDISPONÍVEL")

    def _interaction_error(self, message):
        self.processing = False
        self.last_response = message
        self.set_state("error", "FALHA NA INTERAÇÃO")
        self.open_screen("talk")

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            if self.recording:
                self.recorder.stop()
        except Exception:
            pass
        try:
            if self.voice_manager is not None:
                self.voice_manager.close()
        except Exception:
            pass
        self.root.destroy()


def main():
    print("=" * 60)
    print("⌚ STAR WATCH — FUNCTIONAL BETA / PC PREVIEW")
    print("=" * 60)
    print("Core: STAR local do PC")
    print("STAR World: não carregado pela interface do Watch")
    print("Ações privilegiadas: bloqueadas no cliente")
    StarWatchPC().run()


if __name__ == "__main__":
    main()
