"""Optimized plasma visual renderer for the STAR Watch PC preview.

This module is visual-only: interaction, identity, memory, STT/TTS and the STAR
Core stay in ``star_watch_pc.py`` / the existing project.  The HOME surface is
kept minimal and persistent while a voice interaction started there is active.

Performance rule: expensive Pillow blur/compositing is pre-rendered once in a
small background cache.  The Tk main loop only swaps cached frames and draws the
small STAR symbol/status overlays, so the UI remains responsive.
"""
from __future__ import annotations

import math
import threading
import time
import tkinter as tk

from PIL import Image, ImageDraw, ImageFilter, ImageTk

from star_watch_pc import StarWatchPC, WATCH_SCREENS, mix_color


class PlasmaStarWatchPC(StarWatchPC):
    """Minimal, persistent and lightweight plasma HOME for STAR Watch."""

    HOME_CORE_X = StarWatchPC.WIDTH / 2
    HOME_CORE_Y = 220
    HOME_CORE_RADIUS = 92

    # 60 Hz lightweight UI tick. The heavier plasma raster changes at a lower,
    # state-dependent cadence using already cached frames.
    FRAME_TICK_MS = 16
    PLASMA_CACHE_FRAMES = 24
    PLASMA_RENDER_SCALE = 0.50
    LOGO_MORPH_SECONDS = 0.78

    def __init__(self):
        # Base __init__ calls our render/_animate, so all fields used there must
        # already exist.
        self._plasma_photos = []
        self._plasma_cache_ready = False
        self._plasma_cache_building = False
        self._plasma_frame_index = 0
        self._plasma_last_advance = 0.0
        self._plasma_item = None
        self._status_item = None
        self._dash_item = None
        self._fallback_photo = None
        self._voice_from_home = False
        self._cache_worker = None
        super().__init__()
        self._build_plasma_cache_async()

    # ------------------------------------------------------------------
    # Color helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _hex_rgb(value: str):
        value = str(value or "#FFFFFF").lstrip("#")
        if len(value) != 6:
            return 255, 255, 255
        try:
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return 255, 255, 255

    @staticmethod
    def _blend_rgb(a, b, amount):
        amount = max(0.0, min(1.0, float(amount)))
        return tuple(int(round(x + (y - x) * amount)) for x, y in zip(a, b))

    def _visual_palette(self):
        return [
            self._hex_rgb(self.theme["energy_cyan"]),
            self._hex_rgb(self.theme["energy_blue"]),
            self._hex_rgb(self.theme["energy_violet"]),
            self._hex_rgb(self.theme["energy_pink"]),
        ]

    def _frame_interval_ms(self):
        return {
            "idle": 70,
            "listening": 45,
            "thinking": 36,
            "speaking": 40,
            "error": 85,
        }.get(self.state, 55)

    # ------------------------------------------------------------------
    # Cached plasma renderer
    # ------------------------------------------------------------------
    def _build_plasma_cache_async(self):
        if self._plasma_cache_ready or self._plasma_cache_building or self.closed:
            return
        self._plasma_cache_building = True

        def worker():
            frames = []
            try:
                for index in range(self.PLASMA_CACHE_FRAMES):
                    if self.closed:
                        return
                    phase = math.tau * index / self.PLASMA_CACHE_FRAMES
                    frames.append(self._render_plasma_frame(phase))
            finally:
                if not self.closed:
                    self.root.after(0, lambda: self._install_plasma_cache(frames))

        self._cache_worker = threading.Thread(
            target=worker,
            daemon=True,
            name="STAR-Watch-PlasmaCache",
        )
        self._cache_worker.start()

    def _install_plasma_cache(self, frames):
        if self.closed:
            return
        try:
            self._plasma_photos = [ImageTk.PhotoImage(frame) for frame in frames]
            self._plasma_cache_ready = bool(self._plasma_photos)
            self._plasma_frame_index = 0
            self._plasma_last_advance = time.monotonic()
        finally:
            self._plasma_cache_building = False
        if self.screen == "home":
            self._draw_plasma_home(force=True)

    def _scaled_perimeter(self, scale, strand, phase):
        points = self._perimeter_points(margin=13, radius=34, straight=28, curve=18)
        cx = self.WIDTH / 2
        cy = self.HEIGHT / 2
        result = []
        amp = 2.0 + strand * 0.48
        for index, (x, y) in enumerate(points):
            dx = x - cx
            dy = y - cy
            length = max(1.0, math.hypot(dx, dy))
            nx, ny = dx / length, dy / length
            wave = (
                math.sin(index * 0.23 + phase * 1.55 + strand * 0.82)
                + 0.50 * math.sin(index * 0.49 - phase * 1.10 + strand)
                + 0.20 * math.sin(index * 0.87 + phase * 0.63)
            )
            offset = amp * wave
            result.append(((x + nx * offset) * scale, (y + ny * offset) * scale))
        if result:
            result.append(result[0])
        return result

    def _render_plasma_frame(self, phase):
        """Render one background/core frame off the Tk thread.

        Rendering at half resolution cuts blur/compositing cost dramatically;
        the final upscale is visually appropriate for soft plasma.
        """
        scale = self.PLASMA_RENDER_SCALE
        width = max(1, int(self.WIDTH * scale))
        height = max(1, int(self.HEIGHT * scale))
        palette = self._visual_palette()

        bg = self._hex_rgb(self.theme.get("background", "#05070D"))
        bg = self._blend_rgb(bg, (0, 0, 0), 0.58)
        image = Image.new("RGBA", (width, height), (*bg, 255))

        # Living plasma frame: a few layered fluid filaments, blurred once.
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        crisp = Image.new("RGBA", image.size, (0, 0, 0, 0))
        cd = ImageDraw.Draw(crisp)
        for strand in range(6):
            points = self._scaled_perimeter(scale, strand, phase)
            a = palette[strand % len(palette)]
            b = palette[(strand + 1) % len(palette)]
            color = self._blend_rgb(a, b, (math.sin(phase + strand * 0.8) + 1.0) * 0.5)
            gd.line(
                points,
                fill=(*color, 45 + strand * 8),
                width=max(2, int((7 + strand) * scale)),
                joint="curve",
            )
            cd.line(
                points,
                fill=(*color, 105 + strand * 15),
                width=max(1, int((1 + strand % 2) * scale)),
                joint="curve",
            )
        image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(max(2, int(7 * scale)))))
        image.alpha_composite(crisp)

        # Soft fluid core without the STAR symbol; symbol is drawn cheaply by Tk.
        cx = self.HOME_CORE_X * scale
        cy = self.HOME_CORE_Y * scale
        radius = self.HOME_CORE_RADIUS * scale

        aura = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ad = ImageDraw.Draw(aura)
        for ring in range(8, 0, -1):
            extra = ring * 3 * scale
            color = palette[ring % len(palette)]
            ad.ellipse(
                (cx - radius - extra, cy - radius - extra, cx + radius + extra, cy + radius + extra),
                outline=(*color, 11 + ring * 3),
                width=max(1, int(4 * scale)),
            )
        image.alpha_composite(aura.filter(ImageFilter.GaussianBlur(max(2, int(9 * scale)))))

        core = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(core)
        base = self._blend_rgb(palette[1], palette[2], 0.48)
        draw.ellipse(
            (cx - radius + 3, cy - radius + 3, cx + radius - 3, cy + radius - 3),
            fill=(*base, 62),
        )
        wobble = math.sin(phase * 1.2)
        blobs = [
            (-0.28 + wobble * 0.07, -0.17, 0.62, 0.72, palette[3], 92),
            (0.31, -0.26 - wobble * 0.05, 0.60, 0.57, palette[0], 66),
            (0.02 - wobble * 0.08, 0.36, 0.78, 0.54, palette[2], 82),
        ]
        for ox, oy, rx, ry, color, alpha in blobs:
            x = cx + ox * radius
            y = cy + oy * radius
            draw.ellipse(
                (x - rx * radius, y - ry * radius, x + rx * radius, y + ry * radius),
                fill=(*color, alpha),
            )
        core = core.filter(ImageFilter.GaussianBlur(max(3, int(15 * scale))))

        mask = Image.new("L", image.size, 0)
        md = ImageDraw.Draw(mask)
        md.ellipse((cx - radius + 4, cy - radius + 4, cx + radius - 4, cy + radius - 4), fill=225)
        core.putalpha(Image.composite(core.getchannel("A"), Image.new("L", image.size, 0), mask))
        image.alpha_composite(core)

        # Bright glass rim + three light orbital trails.
        ring = Image.new("RGBA", image.size, (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring)
        rim = self._blend_rgb(palette[0], (255, 255, 255), 0.64)
        rd.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=(*rim, 238),
            width=max(1, int(3 * scale)),
        )
        image.alpha_composite(ring.filter(ImageFilter.GaussianBlur(max(0.5, 0.7 * scale))))

        for orbit_index, (angle, color, alpha) in enumerate((
            (-17, palette[0], 155),
            (18, palette[2], 135),
            (39, palette[3], 112),
        )):
            layer_side = int(radius * 3.0)
            layer = Image.new("RGBA", (layer_side, layer_side), (0, 0, 0, 0))
            od = ImageDraw.Draw(layer)
            pad = int(layer_side * 0.15)
            mid = layer_side / 2
            squash = radius * (0.27 + orbit_index * 0.02)
            box = (pad, mid - squash, layer_side - pad, mid + squash)
            start = int((phase / math.tau * 360 + orbit_index * 103) % 360)
            od.arc(box, start=start, end=start + 245, fill=(*color, alpha), width=max(1, int(2 * scale)))
            rotated = layer.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
            image.alpha_composite(rotated, (int(cx - layer_side / 2), int(cy - layer_side / 2)))

        if scale != 1.0:
            image = image.resize((self.WIDTH, self.HEIGHT), Image.Resampling.LANCZOS)
        return image.convert("RGB")

    def _fallback_frame(self):
        if self._fallback_photo is not None:
            return self._fallback_photo
        bg = self._hex_rgb(self.theme.get("background", "#05070D"))
        bg = self._blend_rgb(bg, (0, 0, 0), 0.58)
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), bg)
        draw = ImageDraw.Draw(image)
        cyan = self._hex_rgb(self.theme["energy_cyan"])
        violet = self._hex_rgb(self.theme["energy_violet"])
        pink = self._hex_rgb(self.theme["energy_pink"])
        draw.rounded_rectangle((12, 12, self.WIDTH - 12, self.HEIGHT - 12), radius=34, outline=violet, width=2)
        r = self.HOME_CORE_RADIUS
        cx, cy = self.HOME_CORE_X, self.HOME_CORE_Y
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(13, 12, 35), outline=cyan, width=3)
        draw.ellipse((cx - r + 7, cy - r + 7, cx + r - 7, cy + r - 7), outline=pink, width=2)
        self._fallback_photo = ImageTk.PhotoImage(image)
        return self._fallback_photo

    # ------------------------------------------------------------------
    # Lightweight Tk overlays
    # ------------------------------------------------------------------
    def _symbol_mix(self):
        # Thinking/responding deliberately hold the star so the morph is obvious
        # even on slower machines. A tap also performs a visible 780 ms reveal.
        if self.state in {"thinking", "speaking"}:
            return 1.0
        if self.logo_animation_started is None:
            return 0.0

        elapsed = time.monotonic() - self.logo_animation_started
        if elapsed >= self.LOGO_MORPH_SECONDS:
            self.logo_animation_started = None
            return 0.0
        if elapsed < 0.18:
            return elapsed / 0.18
        if elapsed < 0.50:
            return 1.0
        return max(0.0, 1.0 - (elapsed - 0.50) / (self.LOGO_MORPH_SECONDS - 0.50))

    def _draw_symbol_overlay(self):
        self.canvas.delete("plasma_icon")
        cx = self.HOME_CORE_X
        cy = self.HOME_CORE_Y
        radius = self.HOME_CORE_RADIUS
        morph = self._symbol_mix()
        bg = self.theme["background"]

        tri_color = mix_color(bg, self.theme["energy_cyan"], 1.0 - morph)
        star_color = mix_color(bg, self.theme["energy_pink"], morph)

        tri_r = radius * 0.45
        self.canvas.create_line(
            cx - tri_r, cy - tri_r * 0.52,
            cx + tri_r, cy - tri_r * 0.52,
            cx, cy + tri_r * 0.74,
            cx - tri_r, cy - tri_r * 0.52,
            fill=tri_color,
            width=max(1, int(4 - morph * 2)),
            smooth=True,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            tags=("plasma_icon",),
        )

        if morph > 0.01:
            outer = radius * 0.42
            inner = outer * 0.38
            points = []
            for index in range(11):
                i = index % 10
                angle = -math.pi / 2 + i * math.pi / 5
                r = outer if i % 2 == 0 else inner
                points.extend((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
            self.canvas.create_line(
                *points,
                fill=star_color,
                width=max(2, int(2 + morph * 2)),
                smooth=False,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
                tags=("plasma_icon",),
            )

    def _home_state_label(self):
        return {
            "idle": "PRONTA",
            "listening": "OUVINDO",
            "thinking": "PENSANDO",
            "speaking": "RESPONDENDO",
            "error": "ATENÇÃO",
        }.get(self.state, self.status or "PRONTA")

    def _draw_plasma_home(self, force=False):
        if self.screen != "home" or self.closed:
            return

        if self._plasma_cache_ready and self._plasma_photos:
            photo = self._plasma_photos[self._plasma_frame_index % len(self._plasma_photos)]
        else:
            photo = self._fallback_frame()

        if self._plasma_item is None:
            self._plasma_item = self.canvas.create_image(
                0, 0, anchor="nw", image=photo, tags=("plasma_home",)
            )
        else:
            self.canvas.itemconfigure(self._plasma_item, image=photo)

        label = "  ".join(self._home_state_label())
        color = self.theme["danger"] if self.state == "error" else mix_color(
            self.theme["primary"], self.theme["text"], 0.42
        )
        if self._status_item is None:
            self._status_item = self.canvas.create_text(
                self.WIDTH / 2,
                367,
                text=label,
                fill=color,
                font=("Segoe UI Light", 11),
                tags=("plasma_home",),
            )
        else:
            self.canvas.itemconfigure(self._status_item, text=label, fill=color)

        dash_color = self.theme["accent"] if self.state in {"thinking", "speaking"} else self.theme["secondary"]
        if self._dash_item is None:
            self._dash_item = self.canvas.create_line(
                self.WIDTH / 2 - 18,
                394,
                self.WIDTH / 2 + 18,
                394,
                fill=dash_color,
                width=3,
                capstyle=tk.ROUND,
                tags=("plasma_home",),
            )
        else:
            self.canvas.itemconfigure(self._dash_item, fill=dash_color)

        self._draw_symbol_overlay()
        self.canvas.tag_raise("plasma_icon")
        if self._status_item is not None:
            self.canvas.tag_raise(self._status_item)
        if self._dash_item is not None:
            self.canvas.tag_raise(self._dash_item)

    def _draw_home(self):
        self._draw_plasma_home(force=True)

    # ------------------------------------------------------------------
    # Rendering / animation
    # ------------------------------------------------------------------
    def _reset_home_items(self):
        self._plasma_item = None
        self._status_item = None
        self._dash_item = None

    def render(self):
        if self.closed:
            return
        self.canvas.delete("content")
        self.canvas.delete("logo")
        self.entry.place_forget()
        self.send_button.place_forget()

        if self.screen == "home":
            self.canvas.delete("energy")
            self._draw_home()
            return

        self.canvas.delete("plasma_home")
        self.canvas.delete("plasma_icon")
        self._reset_home_items()
        if self.screen == "talk":
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

        now = time.monotonic()
        if self.screen == "home":
            if self.animations_enabled and self._plasma_cache_ready and self._plasma_photos:
                interval = self._frame_interval_ms() / 1000.0
                if now - self._plasma_last_advance >= interval:
                    self._plasma_frame_index = (self._plasma_frame_index + 1) % len(self._plasma_photos)
                    self._plasma_last_advance = now
                    self._draw_plasma_home()
                else:
                    # The symbol morph runs at the light 60 Hz tick even when the
                    # raster plasma frame does not need to change.
                    self._draw_symbol_overlay()
            else:
                self._draw_symbol_overlay()
        else:
            if self.animations_enabled:
                self.energy_phase = (self.energy_phase + 0.0035) % 1.0
            self._draw_energy_frame()
            if self.screen == "talk":
                self._draw_logo(self.WIDTH / 2, 132, 36)

        self.root.after(self.FRAME_TICK_MS if self.animations_enabled else 120, self._animate)

    # ------------------------------------------------------------------
    # HOME interaction: minimal screen stays persistent during voice flow
    # ------------------------------------------------------------------
    def _hit_logo(self, x, y):
        if self.screen == "home":
            radius = self.HOME_CORE_RADIUS + 28
            return ((x - self.HOME_CORE_X) ** 2 + (y - self.HOME_CORE_Y) ** 2) <= radius ** 2
        return super()._hit_logo(x, y)

    def _hit_nav(self, x, y):
        if self.screen == "home":
            return None
        return super()._hit_nav(x, y)

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
            self._draw_symbol_overlay()
            self.toggle_voice()
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

    def start_voice(self):
        if not self.recorder.available:
            self.set_state("error", "MICROFONE INDISPONÍVEL")
            self.last_response = "sounddevice não está disponível neste ambiente."
            return
        try:
            self._voice().cancel_speech()
            self.recorder.start()
            self.recording = True
            self._voice_from_home = self.screen == "home"
            if not self._voice_from_home:
                self.open_screen("talk")
            self.set_state("listening", "OUVINDO")
        except Exception as exc:
            self.recording = False
            self.last_response = f"Não consegui abrir o microfone: {type(exc).__name__}: {exc}"
            self.set_state("error", "ERRO DE MICROFONE")

    def _complete_interaction(self, user_text, response):
        self.processing = False
        self.last_user_text = user_text
        self.last_response = response

        if self._voice_from_home:
            # Never jump back to the legacy/talk screen when the interaction was
            # started on the plasma HOME.
            self.screen_index = WATCH_SCREENS.index("home")
            self.screen = "home"

        self.set_state("speaking" if self.voice_output_enabled else "idle", "RESPONDENDO")

        if not self._voice_from_home:
            self.open_screen("talk")

        if not self.voice_output_enabled:
            self._voice_from_home = False
            self.set_state("idle", "PRONTA")
            return

        def spoken(ok, error):
            if self.closed:
                return
            if ok:
                def finish():
                    keep_home = self._voice_from_home
                    self._voice_from_home = False
                    if keep_home:
                        self.screen_index = WATCH_SCREENS.index("home")
                        self.screen = "home"
                    self.set_state("idle", "PRONTA")
                self.root.after(0, finish)
            else:
                message = error or "A resposta textual funcionou, mas a voz não pôde ser reproduzida."
                self.root.after(0, lambda: self._voice_output_error(message))

        self._voice().speak_async(response, callback=spoken)

    def _interaction_error(self, message):
        self.processing = False
        self.last_response = message
        if self._voice_from_home:
            self.screen_index = WATCH_SCREENS.index("home")
            self.screen = "home"
            self.set_state("error", "FALHA NA INTERAÇÃO")
            return
        super()._interaction_error(message)

    def _voice_output_error(self, message):
        self.last_response = self.last_response + "\n\nVoz: " + str(message)
        if self._voice_from_home:
            self.screen_index = WATCH_SCREENS.index("home")
            self.screen = "home"
        self.set_state("error", "VOZ INDISPONÍVEL")


def main():
    print("=" * 60)
    print("⌚ STAR WATCH — MINIMAL PLASMA CORE / FUNCTIONAL BETA")
    print("=" * 60)
    print("Core: STAR local do PC")
    print("Home: persistent minimal plasma core")
    print("Renderer: cached plasma + lightweight 60 Hz symbol/status overlay")
    print("STAR World: não carregado pela interface do Watch")
    print("Ações privilegiadas: bloqueadas no cliente")
    PlasmaStarWatchPC().run()


if __name__ == "__main__":
    main()
