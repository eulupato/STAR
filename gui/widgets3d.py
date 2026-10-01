"""Renderer visual Cosmic Crystal da STAR.

Os widgets continuam embutidos no Tkinter, mas o conteúdo é rasterizado em um
framebuffer por Pillow/numpy: superfície esférica iluminada por pixel, filamentos
com profundidade, cristal facetado com z-buffer, bloom e composição do retrato.
Não abre janelas auxiliares e mantém ``start()``/``stop()`` idempotentes.
"""
from __future__ import annotations

import logging
import math
import time
import tkinter as tk

import numpy as np

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
    from PIL import Image, ImageDraw, ImageFilter, ImageTk
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
        render_started = time.perf_counter()
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
                render_ms = (time.perf_counter() - render_started) * 1000.0
                budget_ms = 1000.0 / self.fps
                self._after_id = self.after(max(1, int(budget_ms - render_ms)), self._tick)
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


_GRID_CACHE: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}


def _rgb(color: str) -> tuple[int, int, int]:
    value = str(color or "#000000").lstrip("#")
    if len(value) != 6:
        return 0, 0, 0
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return 0, 0, 0


def _mix_rgb(a, b, amount: float) -> tuple[int, int, int]:
    amount = max(0.0, min(1.0, float(amount)))
    ca, cb = np.asarray(_rgb(a), dtype=np.float32), np.asarray(_rgb(b), dtype=np.float32)
    out = ca + (cb - ca) * amount
    return tuple(int(round(v)) for v in np.clip(out, 0, 255))


def _render_size(size: int, quality: str) -> int:
    """Internal framebuffer resolution; upscale keeps the Tk UI fluid."""
    size = max(24, int(size))
    if str(quality).lower() == "low":
        return min(size, 96)
    return min(size, 176)


def _grid(size: int):
    cached = _GRID_CACHE.get(size)
    if cached is not None:
        return cached
    axis = np.linspace(-1.0, 1.0, size, dtype=np.float32)
    xx, yy = np.meshgrid(axis, axis)
    rr = np.sqrt(xx * xx + yy * yy)
    cached = (xx, yy, rr)
    _GRID_CACHE[size] = cached
    return cached


def _rgba_from_rgb_alpha(rgb: np.ndarray, alpha: np.ndarray) -> Image.Image:
    rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def _draw_filaments(layer, glow_layer, filaments, render_size, sphere_r, params, front: bool):
    draw = ImageDraw.Draw(layer, "RGBA")
    glow_draw = ImageDraw.Draw(glow_layer, "RGBA")
    cx = cy = render_size / 2
    radius = render_size * sphere_r * 0.98
    fov = render_size * 2.8
    primary = _rgb(params["primary"])
    secondary = _rgb(params["secondary"])
    glow = _rgb(params["glow"])

    for filament in filaments:
        projected = []
        for x, y, z in filament:
            px, py, _ = visual3d.project((x * radius, y * radius, z * radius), cx, cy, fov)
            projected.append((px, py, z))
        for idx in range(len(projected)):
            a = projected[idx]
            b = projected[(idx + 1) % len(projected)]
            z = (a[2] + b[2]) * 0.5
            is_front = z <= 0.0
            if is_front != front:
                continue
            frontness = max(0.0, min(1.0, (1.0 - z) * 0.5))
            color = tuple(
                int(round(secondary[i] + (glow[i] - secondary[i]) * frontness))
                for i in range(3)
            )
            if front:
                alpha = int(130 + 120 * frontness)
                width = max(1, int(round(1.0 + 2.0 * frontness)))
                glow_alpha = int(90 + 90 * frontness)
            else:
                alpha = int(30 + 70 * frontness)
                width = 1
                glow_alpha = int(28 + 45 * frontness)
                color = tuple(int((color[i] + primary[i]) * 0.5) for i in range(3))
            xy = (a[0], a[1], b[0], b[1])
            glow_draw.line(xy, fill=(*color, glow_alpha), width=width + 5)
            draw.line(xy, fill=(*color, alpha), width=width)


def _portrait_tile(portrait: Image.Image | None, render_size: int) -> Image.Image | None:
    if portrait is None:
        return None
    image = portrait.convert("RGBA")
    width, height = image.size
    if min(width, height) <= 0:
        return None
    side = min(width, max(1, int(height * 0.50)))
    left = max(0, (width - side) // 2)
    top = max(0, min(height - side, int(height * 0.055)))
    image = image.crop((left, top, left + side, top + side))
    target = max(48, int(render_size * 0.34))
    if image.size == (target, target):
        return image
    image = image.resize((target, target), Image.Resampling.LANCZOS)

    mask = Image.new("L", (target, target), 0)
    ImageDraw.Draw(mask).ellipse((3, 3, target - 4, target - 4), fill=220)
    mask = mask.filter(ImageFilter.GaussianBlur(max(1.0, target * 0.025)))
    alpha = image.getchannel("A")
    image.putalpha(Image.fromarray(
        np.minimum(np.asarray(alpha, dtype=np.uint8), np.asarray(mask, dtype=np.uint8)),
        "L",
    ))
    return image


def render_orb_frame(
    size: int,
    t: float,
    params: dict,
    quality: str = "high",
    radius: float = 0.40,
    phase: float = 0.0,
    bg: str = _BG_DEFAULT,
    portrait: Image.Image | None = None,
) -> Image.Image:
    """Software-rendered translucent sphere with true per-pixel surface lighting."""
    rs = _render_size(size, quality)
    xx, yy, rr = _grid(rs)
    sphere_r = 0.72
    nx = xx / sphere_r
    ny = -yy / sphere_r
    radial2 = nx * nx + ny * ny
    inside = radial2 <= 1.0
    nz = np.zeros_like(xx)
    nz[inside] = np.sqrt(np.maximum(0.0, 1.0 - radial2[inside]))

    bg_rgb = np.asarray(_rgb(bg), dtype=np.float32)
    core_rgb = np.asarray(_rgb(params["secondary"]), dtype=np.float32)
    primary_rgb = np.asarray(_rgb(params["primary"]), dtype=np.float32)
    glow_rgb = np.asarray(_rgb(params["glow"]), dtype=np.float32)

    frame = Image.new("RGBA", (rs, rs), (*_rgb(bg), 255))

    halo_strength = np.exp(-np.power(rr / (sphere_r * 1.22), 3.4))
    halo_alpha = np.clip(halo_strength * 78.0, 0, 78)
    halo_rgb = np.broadcast_to(glow_rgb, (rs, rs, 3))
    frame = Image.alpha_composite(frame, _rgba_from_rgb_alpha(halo_rgb, halo_alpha))

    filaments = visual3d.orb_filaments(
        phase,
        n_circles=6 if quality == "low" else 10,
        n_pts=36 if quality == "low" else 60,
        wobble=float(params.get("wobble", 0.05)),
    )
    back = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
    back_glow = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
    _draw_filaments(back, back_glow, filaments, rs, sphere_r, params, front=False)
    back_glow = back_glow.filter(ImageFilter.GaussianBlur(max(1.2, rs * 0.012)))
    frame = Image.alpha_composite(frame, back_glow)
    frame = Image.alpha_composite(frame, back)

    light = np.asarray(
        (-0.42 + 0.08 * math.sin(t * 0.7), -0.52, 0.78),
        dtype=np.float32,
    )
    light /= np.linalg.norm(light)
    diffuse = np.clip(nx * light[0] + ny * light[1] + nz * light[2], 0.0, 1.0)
    rim = np.power(np.clip(1.0 - nz, 0.0, 1.0), 1.65)
    half_vec = light + np.asarray((0.0, 0.0, 1.0), dtype=np.float32)
    half_vec /= np.linalg.norm(half_vec)
    specular = np.power(
        np.clip(nx * half_vec[0] + ny * half_vec[1] + nz * half_vec[2], 0.0, 1.0),
        30.0,
    )
    angle = np.arctan2(ny, nx)
    swirl = 0.5 + 0.5 * np.sin(angle * 5.0 + nz * 9.0 - t * 1.15)
    inner = np.exp(-radial2 * 2.8)

    rgb = (
        core_rgb[None, None, :] * (0.34 + 0.28 * inner[..., None])
        + primary_rgb[None, None, :] * (0.18 + 0.54 * diffuse[..., None])
        + glow_rgb[None, None, :] * (
            0.11
            + 0.35 * rim[..., None]
            + 0.72 * specular[..., None]
            + 0.14 * swirl[..., None] * inner[..., None]
        )
    )
    alpha = np.zeros((rs, rs), dtype=np.float32)
    edge = np.clip((1.0 - radial2) * 3.2, 0.0, 1.0)
    alpha[inside] = (
        66
        + 62 * inner[inside]
        + 62 * diffuse[inside]
        + 42 * rim[inside]
        + 38 * edge[inside]
    )
    sphere = _rgba_from_rgb_alpha(rgb, alpha)
    frame = Image.alpha_composite(frame, sphere)

    tile = _portrait_tile(portrait, rs)
    if tile is not None and quality != "low":
        px = (rs - tile.width) // 2
        py = (rs - tile.height) // 2
        portrait_glow = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(portrait_glow, "RGBA")
        pad = max(4, int(rs * 0.018))
        gdraw.ellipse(
            (px - pad, py - pad, px + tile.width + pad, py + tile.height + pad),
            fill=(*_rgb(params["glow"]), 105),
        )
        portrait_glow = portrait_glow.filter(ImageFilter.GaussianBlur(max(2, rs * 0.018)))
        frame = Image.alpha_composite(frame, portrait_glow)
        frame.alpha_composite(tile, (px, py))

    front = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
    front_glow = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
    _draw_filaments(front, front_glow, filaments, rs, sphere_r, params, front=True)
    front_glow = front_glow.filter(ImageFilter.GaussianBlur(max(1.4, rs * 0.011)))
    frame = Image.alpha_composite(frame, front_glow)
    frame = Image.alpha_composite(frame, front)

    highlight = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(highlight, "RGBA")
    box_r = rs * sphere_r
    box = (rs / 2 - box_r, rs / 2 - box_r, rs / 2 + box_r, rs / 2 + box_r)
    hdraw.ellipse(box, outline=(*_rgb(params["glow"]), 112), width=max(1, int(rs * 0.006)))
    frame = Image.alpha_composite(frame, highlight)

    if rs != size:
        frame = frame.resize((size, size), Image.Resampling.BICUBIC)
    return frame


def _raster_triangle(
    target: np.ndarray,
    zbuffer: np.ndarray,
    pts: list[tuple[float, float]],
    depths: list[float],
    color: tuple[int, int, int],
    opacity: float,
):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    h, w = zbuffer.shape
    xmin = max(0, int(math.floor(min(xs))))
    xmax = min(w - 1, int(math.ceil(max(xs))))
    ymin = max(0, int(math.floor(min(ys))))
    ymax = min(h - 1, int(math.ceil(max(ys))))
    if xmin > xmax or ymin > ymax:
        return

    x0, y0 = pts[0]
    x1, y1 = pts[1]
    x2, y2 = pts[2]
    denom = ((y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2))
    if abs(denom) < 1e-8:
        return

    yy, xx = np.mgrid[ymin:ymax + 1, xmin:xmax + 1]
    px = xx + 0.5
    py = yy + 0.5
    b0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / denom
    b1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / denom
    b2 = 1.0 - b0 - b1
    inside = (b0 >= -1e-5) & (b1 >= -1e-5) & (b2 >= -1e-5)
    depth = b0 * depths[0] + b1 * depths[1] + b2 * depths[2]

    sub_z = zbuffer[ymin:ymax + 1, xmin:xmax + 1]
    visible = inside & (depth < sub_z)
    if not np.any(visible):
        return

    sub = target[ymin:ymax + 1, xmin:xmax + 1]
    alpha = max(0.0, min(1.0, float(opacity)))
    for channel in range(3):
        plane = sub[..., channel]
        plane[visible] = plane[visible] * (1.0 - alpha) + color[channel] * alpha
    sub_z[visible] = depth[visible]


def render_crystal_frame(
    size: int,
    t: float,
    params: dict,
    quality: str = "high",
    phase: float = 0.0,
    bg: str = _BG_DEFAULT,
) -> Image.Image:
    """Z-buffered faceted crystal with specular lighting, edges and bloom."""
    rs = _render_size(size, quality)
    bg_rgb = np.asarray(_rgb(bg), dtype=np.float32)
    target = np.empty((rs, rs, 3), dtype=np.float32)
    target[:] = bg_rgb
    zbuffer = np.full((rs, rs), np.inf, dtype=np.float32)

    xx, yy, rr = _grid(rs)
    center_glow = np.exp(-np.power(rr / 0.34, 2.1))[..., None]
    glow_rgb = np.asarray(_rgb(params.get("glow", theme.CRYSTAL_HI)), dtype=np.float32)
    target += center_glow * glow_rgb * 0.17

    crystals = visual3d.crystal_star_geometry(phase, tilt=0.34)
    cx = cy = rs / 2
    radius = rs * 0.43
    fov = rs * 3.0
    edge_records = []
    tip_records = []

    for crystal in crystals:
        idx = int(crystal["crystal_idx"])
        kind = crystal["kind"]
        tip = crystal["verts"][1]
        tip_records.append(visual3d.project((tip[0] * radius, tip[1] * radius, tip[2] * radius), cx, cy, fov)[:2])
        for face in crystal["faces"]:
            verts = face["verts"]
            projected = [
                visual3d.project((x * radius, y * radius, z * radius), cx, cy, fov)
                for x, y, z in verts
            ]
            points = [(p[0], p[1]) for p in projected]
            depths = [p[2] for p in projected]

            light = max(0.0, min(1.0, float(face["light"])))
            facing = max(0.0, min(1.0, float(face["normal_z"])))
            spec = min(1.0, light * 0.72 + facing * 0.48)
            if idx % 3 == 0:
                dark = theme.CRYSTAL_MID
            elif idx % 2:
                dark = theme.ORB_CORE
            else:
                dark = theme.CRYSTAL_BLUE
            base = _mix_rgb(dark, theme.CRYSTAL_LILAC, 0.30 + 0.45 * light)
            bright = _mix_rgb("#%02x%02x%02x" % base, theme.CRYSTAL_HI, spec ** 2.2)
            if face["face_idx"] in (1, 3):
                bright = _mix_rgb("#%02x%02x%02x" % bright, theme.CRYSTAL_PINK, 0.22)
            opacity = 0.74 if kind == "long" else 0.66
            if face["normal_z"] < -0.15:
                opacity *= 0.36
                bright = _mix_rgb("#%02x%02x%02x" % bright, bg, 0.45)

            for tri in ((0, 1, 2), (0, 2, 3)):
                _raster_triangle(
                    target,
                    zbuffer,
                    [points[i] for i in tri],
                    [depths[i] for i in tri],
                    bright,
                    opacity,
                )
            if face["normal_z"] > 0.0:
                edge_records.append((points, spec))

    image = Image.fromarray(np.clip(target, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    bloom = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bloom, "RGBA")
    core = Image.new("RGBA", (rs, rs), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(core, "RGBA")
    for points, spec in edge_records:
        closed = points + [points[0]]
        width = max(1, int(rs * (0.006 + 0.004 * spec)))
        bdraw.line(closed, fill=(*_rgb(theme.CRYSTAL_HI), int(90 + 100 * spec)), width=width + 4)
        cdraw.line(closed, fill=(*_rgb(theme.CRYSTAL_LIGHT), int(135 + 110 * spec)), width=width)

    center = (rs / 2, rs / 2)
    for idx, tip in enumerate(tip_records):
        alpha = 80 if idx % 2 else 120
        bdraw.line((center[0], center[1], tip[0], tip[1]), fill=(*_rgb(theme.CRYSTAL_PINK), alpha), width=max(1, int(rs * 0.012)))
        cdraw.line((center[0], center[1], tip[0], tip[1]), fill=(*_rgb(theme.CRYSTAL_HI), 105), width=max(1, int(rs * 0.003)))

    for part in visual3d.particle_field(t, n=8 if quality == "low" else 18, seed=7):
        x, y = part["x"] * rs, part["y"] * rs
        if math.hypot(part["x"] - 0.5, part["y"] - 0.5) < 0.20:
            continue
        r = max(0.7, part["r"] * rs / 180)
        cdraw.ellipse((x - r, y - r, x + r, y + r), fill=(*_rgb(theme.CRYSTAL_HI), int(80 + 150 * part["alpha"])))

    bloom = bloom.filter(ImageFilter.GaussianBlur(max(1.2, rs * 0.016)))
    image = Image.alpha_composite(image, bloom)
    image = Image.alpha_composite(image, core)

    if rs != size:
        image = image.resize((size, size), Image.Resampling.BICUBIC)
    return image


class _RasterVisualMixin:
    def _init_raster_surface(self):
        self._frame_item = None
        self._frame_photo = None

    def _show_frame(self, frame: Image.Image):
        if not _PIL_OK:
            return
        if frame.size != (self.size, self.size):
            frame = frame.resize((self.size, self.size), Image.Resampling.LANCZOS)
        self._frame_photo = ImageTk.PhotoImage(frame, master=self)
        if self._frame_item is None:
            self._frame_item = self.create_image(
                self.size / 2,
                self.size / 2,
                image=self._frame_photo,
            )
        else:
            self.itemconfigure(self._frame_item, image=self._frame_photo)


class StarOrb3D(_RasterVisualMixin, _Animated3D):
    """Volumetric software-rendered orb with lit surface and depth-layered filaments."""

    def __init__(self, parent, size=200, state="neutral", quality="high", fps=30, bg=None, radius=0.40):
        self.quality = "low" if str(quality).lower() == "low" else "high"
        if self.quality == "low":
            fps = min(int(fps), 20)
        super().__init__(parent, size=size, fps=fps, bg=bg, state=state)
        self.radius = float(radius)
        self.n_circles = 6 if self.quality == "low" else 10
        self.n_pts = 36 if self.quality == "low" else 60
        self._portrait = None
        self._init_raster_surface()

    def set_portrait(self, source):
        if not _PIL_OK:
            return
        if source is None:
            self._portrait = None
            return
        try:
            if isinstance(source, Image.Image):
                image = source.copy()
            else:
                with Image.open(source) as opened:
                    image = opened.convert("RGBA")
            rs = _render_size(self.size, self.quality)
            self._portrait = _portrait_tile(image.convert("RGBA"), rs)
        except (OSError, ValueError, TypeError) as exc:
            LOGGER.warning("Retrato do orb indisponível (%s): %s", source, exc)
            self._portrait = None

    def clear_portrait(self):
        self._portrait = None

    def _render(self, t: float):
        if not _PIL_OK:
            return
        frame = render_orb_frame(
            self.size,
            t,
            self._params,
            quality=self.quality,
            radius=self.radius,
            phase=self._phase,
            bg=self._bg,
            portrait=self._portrait,
        )
        self._show_frame(frame)


class CrystalStar3D(_RasterVisualMixin, _Animated3D):
    """Eight-point faceted crystal rendered with a software z-buffer and bloom."""

    def __init__(self, parent, size=120, fps=15, bg=None, quality="high", speed=0.45):
        super().__init__(parent, size=size, fps=fps, bg=bg)
        self.quality = "low" if str(quality).lower() == "low" else "high"
        if self.quality == "low":
            self.fps = min(self.fps, 20)
        self.speed = float(speed)
        if _ENGINE_OK:
            self._params = dict(self._params, speed=self.speed)
            self._to = dict(self._params)
        self._init_raster_surface()

    def set_state(self, state):
        super().set_state(state)
        if _ENGINE_OK:
            self._to = dict(self._to, speed=self.speed)

    def _render(self, t: float):
        if not _PIL_OK:
            return
        frame = render_crystal_frame(
            self.size,
            t,
            self._params,
            quality=self.quality,
            phase=self._phase,
            bg=self._bg,
        )
        self._show_frame(frame)


__all__ = [
    "StarOrb3D",
    "CrystalStar3D",
    "normalize_state",
    "render_orb_frame",
    "render_crystal_frame",
    "STATE_ALIASES",
]
