"""Widgets Tkinter animados da STAR: orb de filamentos e estrela cristalina.

Ambos são ``tk.Canvas`` autocontidos com ``start()``/``stop()`` idempotentes,
``set_state()`` com transição suave e ``destroy()`` seguro. Se o motor 3D não
puder ser importado, os widgets degradam para um canvas vazio sem crash.
"""
from __future__ import annotations

import logging
import math
import time
import tkinter as tk

LOGGER = logging.getLogger(__name__)

try:
    from gui import theme
    from gui import visual3d
    _ENGINE_OK = True
except Exception as exc:  # pragma: no cover - fallback defensivo
    LOGGER.warning("Motor visual 3D indisponível; widgets ficarão vazios: %s", exc)
    theme = None  # type: ignore[assignment]
    visual3d = None  # type: ignore[assignment]
    _ENGINE_OK = False

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except Exception:  # pragma: no cover
    _PIL_OK = False

_BG_DEFAULT = "#05030D"
_TRANSITION_S = 0.6

# Emoções do avatar/estados de voz → estados visuais do orb.
STATE_ALIASES = {
    "neutral": "neutral", "idle": "neutral", "happy": "neutral", "calm": "neutral",
    "listening": "listening", "recording": "listening",
    "thinking": "thinking", "processing": "thinking",
    "speaking": "speaking", "talking": "speaking",
    "error": "error", "sad": "error", "alert": "error",
}


def normalize_state(state) -> str:
    return STATE_ALIASES.get(str(state or "neutral").lower(), "neutral")


def _state_params(state: str) -> dict:
    colors = dict(theme.STATE_COLORS.get(state, theme.STATE_COLORS["neutral"]))
    colors.update(theme.STATE_MOTION.get(state, theme.STATE_MOTION["neutral"]))
    return colors


class _Animated3D(tk.Canvas):
    """Base comum: loop ``after`` com cancelamento seguro e transição de estado."""

    def __init__(self, parent, size: int, fps: int, bg: str | None, state: str = "neutral"):
        bg = bg or (theme.BG_VOID if _ENGINE_OK else _BG_DEFAULT)
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, borderwidth=0)
        self.size = int(size)
        self.fps = max(1, int(fps))
        self._bg = bg
        self._after_id = None
        self._running = False
        self._phase = 0.0
        self._last = None
        self._t0 = time.monotonic()
        self.state = normalize_state(state)
        if _ENGINE_OK:
            self._params = _state_params(self.state)
            self._from = dict(self._params)
            self._to = dict(self._params)
            self._transition_start = 0.0

    # --- ciclo de vida -------------------------------------------------- #
    @property
    def running(self) -> bool:
        return self._running

    def start(self):
        if not _ENGINE_OK or self._running:
            return
        self._running = True
        self._last = time.monotonic()
        self._tick()

    def stop(self):
        self._running = False
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except (tk.TclError, ValueError):
                pass
            self._after_id = None

    def destroy(self):
        self.stop()
        try:
            super().destroy()
        except tk.TclError:
            pass

    def _alive(self) -> bool:
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    # --- estado --------------------------------------------------------- #
    def set_state(self, state):
        if not _ENGINE_OK:
            return
        state = normalize_state(state)
        if state == self.state:
            return
        self.state = state
        self._from = dict(self._params)
        self._to = _state_params(state)
        self._transition_start = time.monotonic()
        self._on_state_change()

    def _on_state_change(self):
        pass

    def _update_params(self, now: float):
        if self._to is self._params:
            return
        k = (now - self._transition_start) / _TRANSITION_S
        if k >= 1.0:
            self._params = self._to
        else:
            self._params = visual3d.lerp_state(self._from, self._to, k)

    # --- loop ----------------------------------------------------------- #
    def _tick(self):
        self._after_id = None
        if not self._running or not self._alive():
            self._running = False
            return
        now = time.monotonic()
        dt = min(0.25, now - (self._last or now))
        self._last = now
        self._update_params(now)
        self._phase += dt * float(self._params.get("speed", 0.4))
        try:
            self._render(now - self._t0)
        except tk.TclError:
            self._running = False
            return
        except Exception as exc:  # nunca derrubar a UI por um frame
            LOGGER.warning("Falha ao desenhar frame 3D (%s): %s", type(self).__name__, exc)
            self._running = False
            return
        if self._running and self._alive():
            try:
                self._after_id = self.after(max(1, int(1000 / self.fps)), self._tick)
            except tk.TclError:
                self._running = False

    def render_once(self, t: float = 0.6):
        """Desenha um frame estático (sem loop), útil para ícones."""
        if not _ENGINE_OK:
            return
        self._phase = t
        try:
            self._render(t)
        except (tk.TclError, Exception) as exc:
            LOGGER.warning("Falha ao desenhar frame estático 3D: %s", exc)

    def _render(self, t: float):  # pragma: no cover - abstrato
        raise NotImplementedError


class StarOrb3D(_Animated3D):
    """Orb de filamentos de luz violeta com profundidade e glow em camadas."""

    CHUNKS = 4

    def __init__(self, parent, size=200, state="neutral", quality="high", fps=30, bg=None, radius=0.36):
        self.quality = "low" if str(quality).lower() == "low" else "high"
        if self.quality == "low":
            fps = min(int(fps), 20)
        super().__init__(parent, size=size, fps=fps, bg=bg, state=state)
        self.n_circles = 5 if self.quality == "low" else 9
        self.n_pts = 32 if self.quality == "low" else 48
        self.radius = float(radius)
        self._items: list[tuple[int, int, int]] = []
        self._halo_item = None
        self._halo_photo = None
        self._halo_state = None
        if _ENGINE_OK:
            self._build_halo()

    def _build_halo(self):
        if self.quality == "low" or not _PIL_OK:
            return
        try:
            target = getattr(self, "_to", self._params)
            glow = target.get("glow", theme.ORB_GLOW)
            core = target.get("secondary", theme.ORB_CORE)
            s = self.size
            mask = Image.radial_gradient("L").resize((s, s))  # 0 no centro → 255 na borda
            mask = mask.point(lambda v: int(max(0, 255 - v * 1.55) * 0.55))
            base = Image.new("RGB", (s, s), self._bg)
            tint = Image.new("RGB", (s, s), theme.mix(core, glow, 0.35))
            halo = Image.composite(tint, base, mask)
            self._halo_photo = ImageTk.PhotoImage(halo, master=self)
            if self._halo_item is None:
                self._halo_item = self.create_image(s / 2, s / 2, image=self._halo_photo)
                self.tag_lower(self._halo_item)
            else:
                self.itemconfigure(self._halo_item, image=self._halo_photo)
            self._halo_state = self.state
        except Exception as exc:
            LOGGER.warning("Halo do orb indisponível: %s", exc)
            self._halo_photo = None

    def _on_state_change(self):
        # Halo é regerado apenas na troca de estado (barato, uma vez).
        self._build_halo()

    def _ensure_items(self, count: int):
        while len(self._items) < count:
            self._items.append((
                self.create_line(0, 0, 0, 0, fill=self._bg, width=1, capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True),
                self.create_line(0, 0, 0, 0, fill=self._bg, width=1, capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True),
                self.create_line(0, 0, 0, 0, fill=self._bg, width=1, capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True),
            ))

    def _render(self, t: float):
        p = self._params
        s = self.size
        cx = cy = s / 2
        pulse = 1.0 + float(p.get("pulse", 0.03)) * math.sin(t * 3.2)
        R = s * self.radius * pulse
        fov = s * 3.0
        filaments = visual3d.orb_filaments(self._phase, self.n_circles, self.n_pts, wobble=float(p.get("wobble", 0.05)))
        # Divide cada filamento em trechos para iluminar a frente e escurecer o fundo.
        chunks = []
        n = self.n_pts
        step = max(2, n // self.CHUNKS)
        for fil in filaments:
            for c in range(0, n, step):
                seg = [fil[(c + k) % n] for k in range(step + 1)]
                chunks.append(seg)
        chunks.sort(key=lambda seg: sum(pt[2] for pt in seg) / len(seg), reverse=True)
        self._ensure_items(len(chunks))

        primary, secondary, glow = p["primary"], p["secondary"], p["glow"]
        width_scale = max(0.6, min(1.6, s / 260))
        for (outer, mid, core), seg in zip(self._items, chunks):
            coords = []
            zsum = 0.0
            for x, y, z in seg:
                px, py, _ = visual3d.project((x * R, y * R, z * R), cx, cy, fov)
                coords.extend((px, py))
                zsum += z
            depth = 0.5 * (1 - zsum / len(seg))  # 0 = fundo, 1 = frente
            depth = max(0.0, min(1.0, depth))
            self.coords(outer, *coords)
            self.coords(mid, *coords)
            self.coords(core, *coords)
            self.itemconfigure(outer, fill=theme.mix(self._bg, secondary, 0.25 + 0.45 * depth), width=(1.6 + 3.2 * depth) * width_scale)
            self.itemconfigure(mid, fill=theme.mix(secondary, primary, 0.3 + 0.7 * depth), width=(0.8 + 1.4 * depth) * width_scale)
            self.itemconfigure(core, fill=theme.mix(primary, glow, depth ** 1.5), width=max(1.0, (0.4 + 0.7 * depth) * width_scale))
        for extra in self._items[len(chunks):]:
            for item in extra:
                self.coords(item, 0, 0, 0, 0)


class CrystalStar3D(_Animated3D):
    """Estrela cristalina de 8 pontas girando lentamente em Y, com facetas sombreadas."""

    POOL = 40

    def __init__(self, parent, size=120, fps=15, bg=None, quality="high", speed=0.45):
        super().__init__(parent, size=size, fps=fps, bg=bg)
        self.quality = "low" if str(quality).lower() == "low" else "high"
        self.speed = float(speed)
        self._polys: list[int] = []
        self._particles: list[tuple[int, dict]] = []
        if _ENGINE_OK:
            self._params = dict(self._params, speed=self.speed)
            self._to = self._params
            self._build_static()

    def set_state(self, state):
        super().set_state(state)
        if _ENGINE_OK:
            self._to = dict(self._to, speed=self.speed)

    def _build_static(self):
        s = self.size
        n = 0 if s < 48 else (10 if self.quality == "low" else 22)
        for part in visual3d.particle_field(0.0, n=n, seed=7):
            # Somente no anel externo (fora das pontas mais densas).
            dx, dy = part["x"] - 0.5, part["y"] - 0.5
            if math.hypot(dx, dy) < 0.18:
                continue
            x, y = part["x"] * s, part["y"] * s
            r = part["r"] * max(0.6, s / 160)
            item = self.create_oval(x - r, y - r, x + r, y + r, fill=self._bg, outline="")
            self._particles.append((item, part))
        for _ in range(self.POOL):
            self._polys.append(self.create_polygon(0, 0, 0, 0, 0, 0, fill=self._bg, outline="", state="hidden"))

    def _face_color(self, crystal_idx: int, face: dict) -> str:
        light = face["light"]
        dark = theme.CRYSTAL_BLUE if crystal_idx % 2 == 0 else theme.ORB_CORE
        base = theme.mix(dark, theme.CRYSTAL_LILAC, 0.35 + 0.65 * light)
        if face["face_idx"] in (1, 3):
            base = theme.mix(base, theme.CRYSTAL_PINK if crystal_idx % 3 else theme.CRYSTAL_MID, 0.28)
        if light > 0.8:
            base = theme.mix(base, theme.CRYSTAL_HI, (light - 0.8) * 3.0)
        return base

    def _render(self, t: float):
        s = self.size
        cx = cy = s / 2
        R = s * 0.46
        fov = s * 4.0
        crystals = visual3d.crystal_star_geometry(self._phase)
        edge = theme.mix(self._bg, theme.PANEL_EDGE, 0.8)
        i = 0
        for crystal in crystals:
            for face in crystal["faces"]:
                if face["normal_z"] <= 0.0 or i >= len(self._polys):
                    continue
                coords = []
                for x, y, z in face["verts"]:
                    px, py, _ = visual3d.project((x * R, y * R, z * R), cx, cy, fov)
                    coords.extend((px, py))
                poly = self._polys[i]
                self.coords(poly, *coords)
                self.itemconfigure(poly, fill=self._face_color(crystal["crystal_idx"], face),
                                   outline=edge if s >= 48 else "", state="normal")
                i += 1
        for poly in self._polys[i:]:
            self.itemconfigure(poly, state="hidden")
        for item, part in self._particles:
            freq = 0.5 + part["r"] * 0.4
            a = 0.3 + 0.7 * 0.5 * (1 + math.sin(t * freq + part["x"] * 13.0))
            self.itemconfigure(item, fill=theme.mix(self._bg, theme.CRYSTAL_HI, a))


__all__ = ["StarOrb3D", "CrystalStar3D", "normalize_state", "STATE_ALIASES"]
