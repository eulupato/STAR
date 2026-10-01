"""STAR Watch visual system — Plasma Orbit UI.

Camada visual da STAR Watch App. Ela reutiliza integralmente o modelo, providers,
voz, Core e ações de ``clients.star_watch_app`` e substitui somente a apresentação
do simulador no PC.

O objetivo é manter a interface circular, responsiva e coerente com os estados
PRONTA / OUVINDO / PENSANDO / RESPONDENDO / ATENÇÃO, sem acoplar o Core à GUI.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from clients.star_watch_app import (  # noqa: E402
    StarWatchApp,
    WATCH_APP_VERSION,
    WATCH_MODES,
)

try:  # Motor 3D procedural (stdlib pura); fallback 2D se indisponível.
    from gui.visual3d import (  # noqa: E402
        crystal_star_geometry,
        orb_filaments,
        particle_field,
        project,
    )

    VISUAL_3D_AVAILABLE = True
except Exception:  # pragma: no cover - depende do ambiente
    crystal_star_geometry = orb_filaments = particle_field = project = None
    VISUAL_3D_AVAILABLE = False

# Paleta "Cosmic Crystal" das facetas da estrela.
CRYSTAL_BLUE = "#3B4FA8"
CRYSTAL_HI = "#E9D8FF"
CRYSTAL_EDGE = "#1A1440"

VISUAL_SYSTEM_VERSION = "1.0.0"
VISUAL_STYLE = "plasma-orbit"
TARGET_FRAME_MS = 33  # ~30 FPS no simulador, redesenhando só a camada dinâmica.


@dataclass(frozen=True)
class StateTheme:
    primary: str
    secondary: str
    tertiary: str
    icon: str
    orbit_speed: float
    pulse_speed: float
    label: str


STATE_THEMES = {
    "idle": StateTheme(
        primary="#9B7BD4",
        secondary="#3A2467",
        tertiary="#C49EE0",
        icon="triangle",
        orbit_speed=0.55,
        pulse_speed=1.30,
        label="PRONTA",
    ),
    "listening": StateTheme(
        primary="#8FA8FF",
        secondary="#3B4FA8",
        tertiary="#B79CFF",
        icon="triangle",
        orbit_speed=1.00,
        pulse_speed=2.00,
        label="OUVINDO",
    ),
    "thinking": StateTheme(
        primary="#C49EE0",
        secondary="#5B3A99",
        tertiary="#8FA8FF",
        icon="star",
        orbit_speed=1.45,
        pulse_speed=2.35,
        label="PENSANDO",
    ),
    "speaking": StateTheme(
        primary="#F0A6E0",
        secondary="#7E58B3",
        tertiary="#A9C4FF",
        icon="star",
        orbit_speed=1.10,
        pulse_speed=1.75,
        label="RESPONDENDO",
    ),
    "error": StateTheme(
        primary="#FF7C87",
        secondary="#7A2B5A",
        tertiary="#9B7BD4",
        icon="triangle",
        orbit_speed=1.65,
        pulse_speed=2.70,
        label="ATENÇÃO",
    ),
}


class StarWatchVisualApp(StarWatchApp):
    """Apresentação circular premium da mesma STAR Watch App funcional."""

    SIZE = 640
    CX = 320
    CY = 320
    FACE_RADIUS = 278
    RING_RADIUS = 294

    COLORS = {
        # Tokens "Cosmic Crystal"
        "bg": "#05030D",
        "void": "#0E0923",
        "dim": "#160F2E",
        "primary": "#7E58B3",
        "secondary": "#3A2467",
        "glow": "#C49EE0",
        "accent": "#A192C6",
        "highlight": "#E6DCEA",
        "ok": "#76E2A0",
        "warn": "#FFD36E",
        "err": "#FF7C87",
        "muted": "#A99CC9",
        "muted_2": "#6B5F8A",
        # Chaves legadas (mantidas para compatibilidade com subclasses)
        "surface": "#0E0923",
        "surface_2": "#160F2E",
        "text": "#F3EEFA",
        "cyan": "#A192C6",
        "blue": "#5B6FD0",
        "violet": "#7E58B3",
        "pink": "#E6A6E0",
        "gold": "#FFD36E",
        "danger": "#FF7C87",
    }

    def __init__(self):
        self._last_clock = ""
        self._last_dynamic_state = None
        self._dynamic_center = (self.CX, self.CY - 8)
        self._dynamic_radius = 96
        super().__init__()
        self.root.title(
            f"STAR Watch App V{WATCH_APP_VERSION} • Plasma Orbit Visual {VISUAL_SYSTEM_VERSION}"
        )

    def _theme(self) -> StateTheme:
        return STATE_THEMES.get(self.model.state, STATE_THEMES["idle"])

    @staticmethod
    def _hex_to_rgb(color: str) -> tuple[int, int, int]:
        value = color.lstrip("#")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

    @classmethod
    def _blend(cls, a: str, b: str, amount: float) -> str:
        amount = max(0.0, min(1.0, float(amount)))
        ar, ag, ab = cls._hex_to_rgb(a)
        br, bg, bb = cls._hex_to_rgb(b)
        rgb = (
            round(ar + (br - ar) * amount),
            round(ag + (bg - ag) * amount),
            round(ab + (bb - ab) * amount),
        )
        return "#{:02X}{:02X}{:02X}".format(*rgb)

    def render(self):
        """Reconstrói apenas a cena estática; animação atualiza a tag ``dynamic``."""
        self._clear_controls()
        c = self.canvas
        c.delete("all")
        c.configure(bg=self.COLORS["bg"])

        c.create_rectangle(
            0,
            0,
            self.SIZE,
            self.SIZE,
            fill=self.COLORS["bg"],
            outline="",
            tags=("base",),
        )
        self._draw_watch_shell()

        if self.model.active_mode == "home":
            self._draw_home_static()
            self._dynamic_center = (self.CX, self.CY - 12)
            self._dynamic_radius = 94
        else:
            self._draw_mode_static(self.model.active_mode)
            self._dynamic_center = (self.CX, 232)
            self._dynamic_radius = 62

        self._draw_dynamic_layer()
        self._draw_clock(force=True)
        c.tag_raise("hud")

    def _draw_watch_shell(self):
        c = self.canvas
        c.create_oval(
            self.CX - self.RING_RADIUS - 8,
            self.CY - self.RING_RADIUS - 8,
            self.CX + self.RING_RADIUS + 8,
            self.CY + self.RING_RADIUS + 8,
            outline="#0C0820",
            width=8,
            tags=("chrome",),
        )
        c.create_oval(
            self.CX - self.RING_RADIUS,
            self.CY - self.RING_RADIUS,
            self.CX + self.RING_RADIUS,
            self.CY + self.RING_RADIUS,
            outline="#3A2E5C",
            width=2,
            tags=("chrome",),
        )
        c.create_oval(
            self.CX - self.FACE_RADIUS,
            self.CY - self.FACE_RADIUS,
            self.CX + self.FACE_RADIUS,
            self.CY + self.FACE_RADIUS,
            fill="#07041A",
            outline="#1E1540",
            width=2,
            tags=("chrome",),
        )

        c.create_arc(
            35,
            35,
            self.SIZE - 35,
            self.SIZE - 35,
            start=150,
            extent=62,
            style="arc",
            outline=self.COLORS["cyan"],
            width=4,
            tags=("chrome",),
        )
        c.create_arc(
            35,
            35,
            self.SIZE - 35,
            self.SIZE - 35,
            start=-30,
            extent=62,
            style="arc",
            outline=self.COLORS["violet"],
            width=4,
            tags=("chrome",),
        )

        for index in range(24):
            angle = math.radians(index * 15 - 90)
            major = index % 3 == 0
            inner = self.RING_RADIUS - (15 if major else 9)
            outer = self.RING_RADIUS - 3
            x1 = self.CX + math.cos(angle) * inner
            y1 = self.CY + math.sin(angle) * inner
            x2 = self.CX + math.cos(angle) * outer
            y2 = self.CY + math.sin(angle) * outer
            c.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="#4A3A78" if major else "#251B48",
                width=2 if major else 1,
                tags=("chrome",),
            )

        selected_angle = math.radians(
            -90 + (360 / len(WATCH_MODES)) * self.model.selected_index
        )
        marker_r = self.RING_RADIUS - 9
        mx = self.CX + math.cos(selected_angle) * marker_r
        my = self.CY + math.sin(selected_angle) * marker_r
        c.create_oval(
            mx - 4,
            my - 4,
            mx + 4,
            my + 4,
            fill=self._theme().primary,
            outline="",
            tags=("hud",),
        )

    def _draw_home_static(self):
        c = self.canvas
        mode = self.model.selected_mode

        c.create_text(
            self.CX,
            88,
            text="S  T  A  R",
            fill=self.COLORS["text"],
            font=("Segoe UI Light", 18),
            tags=("hud",),
        )
        c.create_line(
            self.CX - 18,
            113,
            self.CX + 18,
            113,
            fill=self.COLORS["violet"],
            width=3,
            tags=("hud",),
        )
        c.create_text(
            self.CX,
            145,
            text=mode.label,
            fill=self.COLORS["muted"],
            font=("Segoe UI Semibold", 10),
            tags=("hud",),
        )

        prev_mode = WATCH_MODES[
            (self.model.selected_index - 1) % len(WATCH_MODES)
        ].short
        next_mode = WATCH_MODES[
            (self.model.selected_index + 1) % len(WATCH_MODES)
        ].short
        c.create_text(
            92,
            self.CY,
            text=f"‹  {prev_mode}",
            fill=self.COLORS["muted_2"],
            font=("Segoe UI", 8),
            tags=("hud",),
        )
        c.create_text(
            self.SIZE - 92,
            self.CY,
            text=f"{next_mode}  ›",
            fill=self.COLORS["muted_2"],
            font=("Segoe UI", 8),
            tags=("hud",),
        )

        c.create_text(
            self.CX,
            438,
            text=self.model.status,
            fill=self._state_color(),
            font=("Segoe UI Semibold", 11),
            tags=("hud",),
        )
        c.create_line(
            self.CX - 17,
            460,
            self.CX + 17,
            460,
            fill=self._theme().secondary,
            width=3,
            tags=("hud",),
        )

        start_x = self.CX - 28
        nearby = (
            (self.model.selected_index - 1) % len(WATCH_MODES),
            self.model.selected_index,
            (self.model.selected_index + 1) % len(WATCH_MODES),
        )
        for i, _mode_index in enumerate(nearby):
            active = i == 1
            radius = 4 if active else 3
            color = self._theme().primary if active else "#2E2450"
            x = start_x + i * 28
            c.create_oval(
                x - radius,
                486 - radius,
                x + radius,
                486 + radius,
                fill=color,
                outline="",
                tags=("hud",),
            )

        c.create_text(
            self.CX,
            535,
            text=self.message,
            fill=self.COLORS["muted"],
            width=360,
            justify="center",
            font=("Segoe UI", 9),
            tags=("hud",),
        )
        c.create_text(
            self.CX,
            586,
            text="GIRE  •  PRESSIONE  •  FALE",
            fill="#6B5F8A",
            font=("Segoe UI", 8),
            tags=("hud",),
        )

    def _draw_mode_static(self, key: str):
        c = self.canvas
        mode = next((item for item in WATCH_MODES if item.key == key), None)
        title = mode.label if mode else key.upper()

        c.create_text(
            self.CX,
            82,
            text="S  T  A  R",
            fill=self.COLORS["text"],
            font=("Segoe UI Light", 15),
            tags=("hud",),
        )
        c.create_text(
            self.CX,
            112,
            text=title,
            fill=self._theme().primary,
            font=("Segoe UI Semibold", 11),
            tags=("hud",),
        )

        if key == "voice":
            value = "OUVINDO" if self.recording else "TOQUE PARA FALAR"
            subtitle = self.message or "Pressione o núcleo para iniciar a conversa."
            self._draw_mode_value(value, subtitle)
        elif key == "search":
            self._draw_mode_value(
                "BUSCA STAR",
                "Pesquise pelo Core atual. O comparador multi-loja permanece como evolução do provider.",
            )
            self._create_search_controls()
        elif key == "health":
            data = self.providers.health()
            value = (
                f"{data.get('heart_rate', '--')} BPM  •  SpO₂ {data.get('spo2', '--')}%"
                if data.get("available")
                else "SEM SENSOR"
            )
            self._draw_mode_value(value, data.get("message", ""))
        elif key == "gps":
            data = self.providers.gps()
            value = (
                f"{data.get('speed_kmh', '--')} km/h"
                if data.get("available")
                else "GPS OFF"
            )
            self._draw_mode_value(value, data.get("message", ""))
        elif key == "vision":
            self._draw_mode_value(
                "STAR SCAN",
                self.message
                or "Selecione uma imagem para enviar ao STAR Core e analisar pelo B25.",
            )
            self._create_action_button("SELECIONAR IMAGEM", self._select_vision_image)
        elif key == "people":
            rows = self.people.list()
            names = ", ".join(
                item.get("name", "") for item in rows[-4:] if item.get("name")
            ) or "Nenhuma pessoa cadastrada"
            self._draw_mode_value(f"{len(rows)} PERFIS", names)
            self._create_action_button("ADICIONAR PESSOA", self._add_person)
        elif key == "measure":
            data = self.providers.measure()
            value = (
                f"{data.get('distance_m', '--')} m"
                if data.get("available")
                else "SENSOR OFF"
            )
            self._draw_mode_value(
                value,
                data.get("message", "") + "\nPressione para medir novamente.",
            )
        elif key == "media":
            self._draw_mode_value(
                "MÍDIA",
                self.message
                or "Pressione para play/pause. Faixa e volume reutilizam os comandos atuais.",
            )
        elif key == "weather":
            data = self.providers.weather()
            self._draw_mode_value("CLIMA", data.get("message", ""))
        elif key == "settings":
            self._draw_mode_value(
                "CONFIG",
                "Simulação: "
                + ("ON" if self.model.simulation_enabled else "OFF")
                + "\nResposta falada: "
                + ("ON" if self.model.voice_output_enabled else "OFF"),
            )
            self._create_settings_buttons()

        c.create_text(
            self.CX,
            574,
            text="BACKSPACE  •  VOLTAR     RODA/SETAS  •  GIRAR",
            fill="#6B5F8A",
            font=("Segoe UI", 8),
            tags=("hud",),
        )

    def _draw_mode_value(self, value: str, subtitle: str):
        self.canvas.create_text(
            self.CX,
            345,
            text=value,
            fill=self.COLORS["text"],
            width=390,
            justify="center",
            font=("Segoe UI Semibold", 17),
            tags=("hud",),
        )
        self.canvas.create_line(
            self.CX - 16,
            373,
            self.CX + 16,
            373,
            fill=self._theme().primary,
            width=3,
            tags=("hud",),
        )
        self.canvas.create_text(
            self.CX,
            410,
            text=subtitle,
            fill=self.COLORS["muted"],
            width=390,
            justify="center",
            font=("Segoe UI", 9),
            tags=("hud",),
        )

    def _advance_clock3d(self, speed: float) -> float:
        """Relógio contínuo para o motor 3D (sem saltos quando ``phase`` dá a volta)."""
        now = time.monotonic()
        last = getattr(self, "_t3d_last", None)
        dt = 0.0 if last is None else max(0.0, min(0.25, now - last))
        self._t3d_last = now
        self._t3d = getattr(self, "_t3d", 0.0) + dt * (0.45 + 0.55 * speed)
        return self._t3d

    def _draw_dynamic_layer(self):
        c = self.canvas
        c.delete("dynamic")

        cx, cy = self._dynamic_center
        radius = self._dynamic_radius
        theme = self._theme()
        now = time.monotonic()
        pulse = 0.5 + 0.5 * math.sin(now * theme.pulse_speed)
        phase = self.phase * math.tau
        use_3d = VISUAL_3D_AVAILABLE
        t3d = self._advance_clock3d(theme.orbit_speed)

        for idx, color in enumerate(
            (
                self._blend(self.COLORS["bg"], theme.secondary, 0.22),
                self._blend(self.COLORS["bg"], theme.primary, 0.26),
                self._blend(self.COLORS["bg"], theme.tertiary, 0.16),
            )
        ):
            rr = radius + 24 - idx * 8 + pulse * (5 - idx)
            c.create_oval(
                cx - rr,
                cy - rr,
                cx + rr,
                cy + rr,
                outline=color,
                width=6 - idx,
                tags=("dynamic",),
            )

        # Núcleo nebuloso (fundo do orb).
        points = []
        count = 48
        blob_radius = radius * (0.70 if use_3d else 0.62)
        for i in range(count):
            angle = math.tau * i / count
            wobble = (
                1.0
                + 0.075 * math.sin(angle * 3 + phase * 1.2)
                + 0.045 * math.sin(angle * 5 - phase * 0.7)
            )
            rr = blob_radius * wobble
            points.extend((cx + math.cos(angle) * rr, cy + math.sin(angle) * rr))
        c.create_polygon(
            points,
            fill=self._blend(self.COLORS["void"], theme.secondary, 0.42),
            outline="" if use_3d else self._blend(theme.primary, "#FFFFFF", 0.24),
            width=2,
            smooth=True,
            tags=("dynamic",),
        )

        drawn_3d = False
        if use_3d:
            try:
                self._draw_orbit_3d(cx, cy, radius * 0.86, t3d, theme)
                drawn_3d = True
            except Exception:
                drawn_3d = False
        if not drawn_3d:
            orbit_specs = (
                (1.02, 0.58, 0.0, theme.primary),
                (1.20, 0.42, 1.9, theme.secondary),
                (0.94, 0.70, 3.7, theme.tertiary),
            )
            speed_phase = phase * theme.orbit_speed
            for scale, squash, offset, color in orbit_specs:
                self._draw_orbit(
                    cx, cy, radius * scale, squash, speed_phase + offset, color
                )

        if theme.icon == "star":
            star_r = radius * (0.62 if use_3d else 0.30)
            self._draw_star(cx, cy, star_r, theme.primary)
        else:
            self._draw_triangle(cx, cy, radius * 0.28, theme.primary)

        if self.model.state == "listening":
            self._draw_listening_waves(cx, cy, radius, theme.primary)
        elif self.model.state == "error":
            c.create_arc(
                cx - radius - 20,
                cy - radius - 20,
                cx + radius + 20,
                cy + radius + 20,
                start=210 + (self.phase * 180),
                extent=95,
                style="arc",
                outline=theme.primary,
                width=4,
                tags=("dynamic",),
            )

        c.tag_raise("dynamic")
        c.tag_raise("hud")

    def _depth_color(self, base: str, near: float) -> str:
        """``near`` 0 = fundo (escuro/opaco) … 1 = frente (claro/brilhante)."""
        if near < 0.5:
            return self._blend(self.COLORS["void"], base, 0.30 + near * 1.2)
        return self._blend(base, self.COLORS["highlight"], (near - 0.5) * 1.1)

    def _draw_orbit_3d(self, cx: float, cy: float, radius: float, t: float, theme):
        """Orb de filamentos 3D: great circles projetados em perspectiva.

        Profundidade (convenção do motor: z maior = mais longe) controla largura
        (1px fundo → 2px frente) e cor (escuro atrás → brilhante na frente).
        Segmentos consecutivos de mesma faixa de profundidade são agrupados numa
        única linha para manter o custo por frame baixo.
        """
        canvas = self.canvas
        palette = (theme.primary, theme.secondary, theme.tertiary)
        filaments = orb_filaments(t, n_circles=7, n_pts=36)
        for f_idx, filament in enumerate(filaments):
            base = palette[f_idx % len(palette)]
            if base == theme.secondary:
                base = self._blend(base, self.COLORS["glow"], 0.45)
            proj = [
                project((x * radius, y * radius, z * radius), cx, cy, fov=300)
                for x, y, z in filament
            ]
            n = len(proj)
            run: list[float] = []
            run_bucket = None
            for k in range(n + 1):
                p0 = proj[k % n]
                p1 = proj[(k + 1) % n]
                near = max(0.0, min(1.0, 0.5 - (p0[2] + p1[2]) / (4.0 * radius)))
                bucket = 0 if near < 0.38 else (1 if near < 0.68 else 2)
                if k == n or (run_bucket is not None and bucket != run_bucket):
                    if len(run) >= 4:
                        mid = (0.2, 0.53, 0.88)[run_bucket]
                        canvas.create_line(
                            *run,
                            fill=self._depth_color(base, mid),
                            width=(1, 1.5, 2)[run_bucket],
                            capstyle="round",
                            tags=("dynamic",),
                        )
                    run = [p0[0], p0[1]] if k < n else []
                if k == n:
                    break
                if not run:
                    run = [p0[0], p0[1]]
                run.extend((p1[0], p1[1]))
                run_bucket = bucket

            # Faísca viajando pelo filamento (maior/mais clara quando na frente).
            spark = proj[int((self.phase * 1.3 + f_idx / 7.0) * n) % n]
            near = max(0.0, min(1.0, 0.5 - spark[2] / (2.0 * radius)))
            sr = 1.2 + 2.0 * near
            canvas.create_oval(
                spark[0] - sr,
                spark[1] - sr,
                spark[0] + sr,
                spark[1] + sr,
                fill=self._depth_color(base, near),
                outline="",
                tags=("dynamic",),
            )

    def _draw_orbit(
        self,
        cx: float,
        cy: float,
        radius: float,
        squash: float,
        angle: float,
        color: str,
    ):
        points = []
        steps = 72
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        for i in range(steps + 1):
            t = math.tau * i / steps
            x = radius * math.cos(t)
            y = radius * squash * math.sin(t)
            rx = x * cos_a - y * sin_a
            ry = x * sin_a + y * cos_a
            points.extend((cx + rx, cy + ry))
        self.canvas.create_line(
            *points,
            fill=color,
            width=2,
            smooth=True,
            splinesteps=12,
            tags=("dynamic",),
        )

        t = self.phase * math.tau * 1.3 + angle
        x = radius * math.cos(t)
        y = radius * squash * math.sin(t)
        px = cx + x * cos_a - y * sin_a
        py = cy + x * sin_a + y * cos_a
        self.canvas.create_oval(
            px - 3,
            py - 3,
            px + 3,
            py + 3,
            fill=color,
            outline="",
            tags=("dynamic",),
        )

    def _draw_triangle(self, cx: float, cy: float, radius: float, color: str):
        points = []
        for deg in (150, 30, 270):
            angle = math.radians(deg)
            points.extend((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
        points.extend(points[:2])
        self.canvas.create_line(
            *points,
            fill=color,
            width=4,
            joinstyle="round",
            tags=("dynamic",),
        )

    def _draw_star(self, cx: float, cy: float, radius: float, color: str):
        if VISUAL_3D_AVAILABLE:
            try:
                self._draw_crystal_star(cx, cy, radius, color)
                return
            except Exception:
                pass
        points = []
        inner = radius * 0.46
        for index in range(10):
            r = radius if index % 2 == 0 else inner
            angle = math.radians(-90 + index * 36)
            points.extend((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        self.canvas.create_polygon(
            points,
            fill="",
            outline=color,
            width=4,
            tags=("dynamic",),
        )

    def _draw_crystal_star(self, cx: float, cy: float, radius: float, color: str):
        """Estrela cristalina de 8 pontas (bipirâmides) girando lentamente em Y."""
        canvas = self.canvas
        t = getattr(self, "_t3d", 0.0) * 0.55
        crystals = crystal_star_geometry(t)
        for crystal in crystals:  # já ordenados do mais distante ao mais próximo
            for face in crystal["faces"]:
                pts = []
                for x, y, z in face["verts"]:
                    px, py, _ = project(
                        (x * radius, y * radius, z * radius), cx, cy, fov=300
                    )
                    pts.extend((px, py))
                lit = max(0.0, face["normal_z"]) * 0.55 + face["light"] * 0.45
                fill = self._blend(CRYSTAL_BLUE, CRYSTAL_HI, 0.15 + 0.80 * lit)
                fill = self._blend(fill, color, 0.18)
                canvas.create_polygon(
                    pts,
                    fill=fill,
                    outline=self._blend(CRYSTAL_EDGE, fill, 0.35),
                    width=1,
                    tags=("dynamic",),
                )

        # Partículas cintilantes ao redor da estrela.
        span = radius * 2.4
        for p in particle_field(time.monotonic(), n=12, seed=7):
            px = cx + (p["x"] - 0.5) * span
            py = cy + (p["y"] - 0.5) * span
            col = self._blend(self.COLORS["void"], CRYSTAL_HI, p["alpha"])
            r = p["r"] * 0.9
            if p["alpha"] > 0.85:
                arm = r * 2.6
                canvas.create_line(px - arm, py, px + arm, py, fill=col, tags=("dynamic",))
                canvas.create_line(px, py - arm, px, py + arm, fill=col, tags=("dynamic",))
            canvas.create_oval(
                px - r, py - r, px + r, py + r, fill=col, outline="", tags=("dynamic",)
            )

    def _draw_listening_waves(
        self, cx: float, cy: float, radius: float, color: str
    ):
        for offset in (16, 28):
            self.canvas.create_arc(
                cx - radius - offset,
                cy - radius * 0.55,
                cx - radius + offset,
                cy + radius * 0.55,
                start=-65,
                extent=130,
                style="arc",
                outline=color,
                width=2,
                tags=("dynamic",),
            )
            self.canvas.create_arc(
                cx + radius - offset,
                cy - radius * 0.55,
                cx + radius + offset,
                cy + radius * 0.55,
                start=115,
                extent=130,
                style="arc",
                outline=color,
                width=2,
                tags=("dynamic",),
            )

    def _draw_clock(self, force: bool = False):
        now = time.strftime("%H:%M")
        if not force and now == self._last_clock:
            return
        self._last_clock = now
        self.canvas.delete("clock")
        y = 505 if self.model.active_mode == "home" else 535
        self.canvas.create_text(
            self.CX,
            y,
            text=now,
            fill="#C9BEE3",
            font=("Segoe UI Light", 12),
            tags=("clock", "hud"),
        )

    def _create_search_controls(self):
        tk = self.tk
        self.input_widget = tk.Entry(
            self.root,
            bg="#0E0923",
            fg=self.COLORS["text"],
            insertbackground=self.COLORS["cyan"],
            highlightbackground="#3A2E5C",
            highlightcolor=self.COLORS["violet"],
            highlightthickness=1,
            relief="flat",
            justify="center",
            font=("Segoe UI", 10),
        )
        self.input_widget.place(x=170, y=467, width=300, height=36)
        self.input_widget.bind("<Return>", lambda _e: self._submit_search())
        self._create_action_button("PESQUISAR", self._submit_search, y=510)
        self.input_widget.focus_set()

    def _create_action_button(self, text: str, command, y: int = 482):
        tk = self.tk
        self.action_button = tk.Button(
            self.root,
            text=text,
            command=command,
            bg="#160F2E",
            fg=self._theme().primary,
            activebackground="#24184A",
            activeforeground=self.COLORS["text"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )
        self.action_button.place(x=210, y=y, width=220, height=38)

    def _create_settings_buttons(self):
        tk = self.tk
        first = tk.Button(
            self.root,
            text="SIMULAÇÃO",
            command=self._toggle_simulation,
            relief="flat",
            bd=0,
            bg="#160F2E",
            fg=self.COLORS["cyan"],
            activebackground="#24184A",
            activeforeground=self.COLORS["text"],
        )
        second = tk.Button(
            self.root,
            text="VOZ",
            command=self._toggle_voice_output,
            relief="flat",
            bd=0,
            bg="#160F2E",
            fg=self.COLORS["pink"],
            activebackground="#24184A",
            activeforeground=self.COLORS["text"],
        )
        first.place(x=195, y=482, width=116, height=38)
        second.place(x=329, y=482, width=116, height=38)
        self.input_widget = first
        self.action_button = second

    def _on_click(self, event):
        dx = event.x - self.CX
        dy = event.y - self.CY
        distance = math.hypot(dx, dy)
        if distance <= 132:
            self.press()
        elif 245 <= distance <= 315:
            self.rotate(-1 if dx < 0 else 1)

    def _animate(self):
        if self.closed:
            return
        theme = self._theme()
        self.phase = (
            self.phase + (0.0065 + 0.0045 * theme.orbit_speed)
        ) % 1.0
        self._draw_dynamic_layer()
        self._draw_clock()
        self.root.after(TARGET_FRAME_MS, self._animate)


def main():
    StarWatchVisualApp().run()


if __name__ == "__main__":
    main()
