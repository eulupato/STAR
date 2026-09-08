"""Official plasma visual renderer for the STAR Watch PC preview.

This module keeps the existing functional STAR Watch client as the single source of
interaction logic and only replaces the home visual layer. The PC remains the
brain; STAR World is not loaded here.
"""
from __future__ import annotations

import math
import time
import tkinter as tk

from PIL import Image, ImageDraw, ImageFilter, ImageTk

from star_watch_pc import StarWatchPC, WATCH_SCREENS, mix_color


class PlasmaStarWatchPC(StarWatchPC):
    """Minimal home surface inspired by the approved STAR plasma reference."""

    HOME_CORE_X = StarWatchPC.WIDTH / 2
    HOME_CORE_Y = 220
    HOME_CORE_RADIUS = 92

    def __init__(self):
        # These attributes must exist before StarWatchPC.__init__ because the base
        # constructor calls render()/animate(), which are overridden here.
        self._plasma_photo = None
        self._plasma_last_frame = 0.0
        self._voice_from_home = False
        super().__init__()

    # ------------------------------------------------------------------
    # Minimal plasma home
    # ------------------------------------------------------------------
    def _plasma_colors(self):
        palette = self._state_palette()
        return [tuple(int(v) for v in self._hex_rgb(color)) for color in palette]

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

    def _state_strength(self):
        return {
            "idle": 0.72,
            "listening": 1.00,
            "thinking": 0.96,
            "speaking": 1.00,
            "error": 0.88,
        }.get(self.state, 0.82)

    def _plasma_perimeter(self, strand: int, phase: float):
        """Return a soft, breathing rounded-square perimeter.

        The base geometry follows the current watch shape but offsets every point
        along the outward normal with multiple low-frequency sine waves. Drawing
        several phase-shifted strands creates the fluid/plasma look without
        storing a heavy video asset.
        """
        points = self._perimeter_points(margin=13, radius=34, straight=28, curve=18)
        cx = self.WIDTH / 2
        cy = self.HEIGHT / 2
        result = []
        amp = 2.2 + strand * 0.55
        for index, (x, y) in enumerate(points):
            dx = x - cx
            dy = y - cy
            length = max(1.0, math.hypot(dx, dy))
            nx, ny = dx / length, dy / length
            wave = (
                math.sin(index * 0.23 + phase * 2.0 + strand * 0.9)
                + 0.55 * math.sin(index * 0.51 - phase * 1.35 + strand)
                + 0.22 * math.sin(index * 0.91 + phase * 0.7)
            )
            offset = amp * wave
            result.append((x + nx * offset, y + ny * offset))
        if result:
            result.append(result[0])
        return result

    def _draw_plasma_border(self, image, phase):
        palette = self._plasma_colors()
        strength = self._state_strength()

        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        crisp = Image.new("RGBA", image.size, (0, 0, 0, 0))
        crisp_draw = ImageDraw.Draw(crisp)

        strand_count = 7
        for strand in range(strand_count):
            points = self._plasma_perimeter(strand, phase)
            color_a = palette[strand % len(palette)]
            color_b = palette[(strand + 1) % len(palette)]
            color = self._blend_rgb(color_a, color_b, (math.sin(phase + strand) + 1) / 2)
            glow_alpha = int((48 + strand * 8) * strength)
            crisp_alpha = int((104 + strand * 13) * strength)
            glow_draw.line(points, fill=(*color, glow_alpha), width=8 + strand // 2, joint="curve")
            crisp_draw.line(points, fill=(*color, crisp_alpha), width=1 + (strand % 2), joint="curve")

        image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))
        image.alpha_composite(crisp)

    def _draw_orbit(self, image, center, size, color, angle, phase, width=2, alpha=120):
        layer_size = int(size * 2.6)
        layer = Image.new("RGBA", (layer_size, layer_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        pad = int(layer_size * 0.18)
        box = (
            pad,
            layer_size // 2 - int(size * 0.29),
            layer_size - pad,
            layer_size // 2 + int(size * 0.29),
        )
        start = int((phase * 95 + angle * 2.7) % 360)
        draw.arc(box, start=start, end=start + 250, fill=(*color, alpha), width=width)
        draw.arc(
            box,
            start=start + 275,
            end=start + 338,
            fill=(*color, max(40, alpha // 2)),
            width=max(1, width - 1),
        )
        rotated = layer.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
        x = int(center[0] - layer_size / 2)
        y = int(center[1] - layer_size / 2)
        image.alpha_composite(rotated, (x, y))

    def _draw_plasma_core(self, image, phase):
        cx, cy = self.HOME_CORE_X, self.HOME_CORE_Y
        radius = self.HOME_CORE_RADIUS
        palette = self._plasma_colors()
        strength = self._state_strength()

        aura = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ad = ImageDraw.Draw(aura)
        for ring in range(11, 0, -1):
            extra = ring * 4
            color = palette[ring % len(palette)]
            alpha = int((10 + ring * 2.3) * strength)
            ad.ellipse(
                (cx - radius - extra, cy - radius - extra, cx + radius + extra, cy + radius + extra),
                outline=(*color, alpha),
                width=5,
            )
        image.alpha_composite(aura.filter(ImageFilter.GaussianBlur(11)))

        # Soft translucent inner body, intentionally asymmetric like the approved
        # plasma reference rather than a flat neon circle.
        core = Image.new("RGBA", image.size, (0, 0, 0, 0))
        cd = ImageDraw.Draw(core)
        base = self._blend_rgb(palette[1], palette[2], 0.45)
        cd.ellipse(
            (cx - radius + 5, cy - radius + 5, cx + radius - 5, cy + radius - 5),
            fill=(*base, int(58 * strength)),
        )

        wobble = math.sin(phase * 1.6)
        blob_specs = [
            (-28 + wobble * 7, -18, 60, 70, palette[-1], 88),
            (30, -28 - wobble * 5, 62, 58, palette[0], 60),
            (4 - wobble * 8, 36, 78, 55, palette[2], 78),
        ]
        for ox, oy, rx, ry, color, alpha in blob_specs:
            cd.ellipse(
                (cx + ox - rx, cy + oy - ry, cx + ox + rx, cy + oy + ry),
                fill=(*color, int(alpha * strength)),
            )
        core = core.filter(ImageFilter.GaussianBlur(18))

        mask = Image.new("L", image.size, 0)
        md = ImageDraw.Draw(mask)
        md.ellipse(
            (cx - radius + 7, cy - radius + 7, cx + radius - 7, cy + radius - 7),
            fill=225,
        )
        core.putalpha(Image.composite(core.getchannel("A"), Image.new("L", image.size, 0), mask))
        image.alpha_composite(core)

        # Fine luminous layers around the orb.
        ring_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring_layer)
        breath = (math.sin(phase * 1.2) + 1.0) * 0.5
        for offset, width, alpha in ((0, 3, 238), (5, 2, 120), (11, 1, 70)):
            color = self._blend_rgb(palette[0], palette[-1], 0.38 + 0.18 * breath)
            rd.ellipse(
                (cx - radius - offset, cy - radius - offset, cx + radius + offset, cy + radius + offset),
                outline=(*color, int(alpha * strength)),
                width=width,
            )
        image.alpha_composite(ring_layer.filter(ImageFilter.GaussianBlur(0.7)))

        # Orbit trails provide the same floating/rotating feel as the plasma GIF.
        self._draw_orbit(
            image,
            (cx, cy),
            radius,
            palette[0],
            -18,
            phase,
            width=2,
            alpha=int(155 * strength),
        )
        self._draw_orbit(
            image,
            (cx, cy),
            radius + 6,
            palette[2],
            17,
            -phase * 0.83,
            width=2,
            alpha=int(135 * strength),
        )
        self._draw_orbit(
            image,
            (cx, cy),
            radius - 3,
            palette[-1],
            38,
            phase * 0.62,
            width=1,
            alpha=int(112 * strength),
        )

        # Triangle ↔ star reveal keeps the approved STAR identity animation.
        morph = 0.0
        if self.logo_animation_started is not None:
            elapsed = time.monotonic() - self.logo_animation_started
            if elapsed >= 0.72:
                self.logo_animation_started = None
            else:
                morph = math.sin(math.pi * (elapsed / 0.72))

        icon = Image.new("RGBA", image.size, (0, 0, 0, 0))
        idraw = ImageDraw.Draw(icon)
        tri_r = radius * 0.46
        triangle = [
            (cx - tri_r, cy - tri_r * 0.52),
            (cx + tri_r, cy - tri_r * 0.52),
            (cx, cy + tri_r * 0.74),
            (cx - tri_r, cy - tri_r * 0.52),
        ]
        tri_color = self._blend_rgb(palette[0], (255, 255, 255), 0.55)
        idraw.line(
            triangle,
            fill=(*tri_color, max(14, int(245 * (1.0 - morph)))),
            width=3,
            joint="curve",
        )

        if morph > 0.01:
            outer = radius * 0.42
            inner = outer * 0.38
            star = []
            for i in range(11):
                idx = i % 10
                angle = -math.pi / 2 + idx * math.pi / 5
                r = outer if idx % 2 == 0 else inner
                star.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
            star_color = self._blend_rgb(palette[-1], (255, 255, 255), 0.62)
            idraw.line(
                star,
                fill=(*star_color, int(245 * morph)),
                width=3,
                joint="curve",
            )

        glow_icon = icon.filter(ImageFilter.GaussianBlur(8))
        image.alpha_composite(glow_icon)
        image.alpha_composite(icon)

    def _home_state_label(self):
        return {
            "idle": "PRONTA",
            "listening": "OUVINDO",
            "thinking": "PENSANDO",
            "speaking": "RESPONDENDO",
            "error": "ATENÇÃO",
        }.get(self.state, self.status or "PRONTA")

    def _draw_plasma_home(self):
        phase = self.energy_phase * math.tau
        background = self._hex_rgb(self.theme.get("background", "#05070D"))
        # Darken the configured background to match the approved reference.
        background = self._blend_rgb(background, (0, 0, 0), 0.55)
        image = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (*background, 255))

        self._draw_plasma_border(image, phase)
        self._draw_plasma_core(image, phase)

        photo = ImageTk.PhotoImage(image.convert("RGB"))
        self._plasma_photo = photo
        self.canvas.delete("plasma_home")
        self.canvas.create_image(0, 0, anchor="nw", image=photo, tags=("plasma_home",))

        label = self._home_state_label()
        color = self.theme["danger"] if self.state == "error" else mix_color(
            self.theme["primary"], self.theme["text"], 0.42
        )
        self.canvas.create_text(
            self.WIDTH / 2,
            367,
            text="  ".join(label),
            fill=color,
            font=("Segoe UI Light", 11),
            tags=("plasma_home",),
        )
        # Tiny status dash, matching the approved minimal concept.
        dash_color = self.theme["accent"] if self.state in {"thinking", "speaking"} else self.theme["secondary"]
        self.canvas.create_line(
            self.WIDTH / 2 - 18,
            394,
            self.WIDTH / 2 + 18,
            394,
            fill=dash_color,
            width=3,
            capstyle=tk.ROUND,
            tags=("plasma_home",),
        )
        self._plasma_last_frame = time.monotonic()

    def _draw_home(self):
        self._draw_plasma_home()

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
        if self.animations_enabled:
            speed = {
                "idle": 0.0045,
                "listening": 0.015,
                "thinking": 0.020,
                "speaking": 0.017,
                "error": 0.007,
            }.get(self.state, 0.006)
            self.energy_phase = (self.energy_phase + speed) % 1.0

        if self.screen == "home":
            if self.animations_enabled or (time.monotonic() - self._plasma_last_frame) > 0.5:
                self._draw_plasma_home()
        else:
            self._draw_energy_frame()
            if self.screen == "talk":
                self._draw_logo(self.WIDTH / 2, 132, 36)
        self.root.after(self.FRAME_MS if self.animations_enabled else 250, self._animate)

    # ------------------------------------------------------------------
    # Interaction stays functional while Home remains visually minimal.
    # ------------------------------------------------------------------
    def _hit_logo(self, x, y):
        if self.screen == "home":
            radius = self.HOME_CORE_RADIUS + 28
            return (
                (x - self.HOME_CORE_X) ** 2 + (y - self.HOME_CORE_Y) ** 2
            ) <= radius ** 2
        return super()._hit_logo(x, y)

    def _hit_nav(self, x, y):
        if self.screen == "home":
            return None
        return super()._hit_nav(x, y)

    def _on_release(self, event):
        # Base behavior is retained, except the removed HOME quick-action rectangle.
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
                    self._voice_from_home = False
                    self.set_state("idle", "PRONTA")
                self.root.after(0, finish)
            else:
                message = error or "A resposta textual funcionou, mas a voz não pôde ser reproduzida."
                self.root.after(0, lambda: self._voice_output_error(message))

        self._voice().speak_async(response, callback=spoken)


def main():
    print("=" * 60)
    print("⌚ STAR WATCH — PLASMA HOME / FUNCTIONAL BETA")
    print("=" * 60)
    print("Core: STAR local do PC")
    print("Home: minimal plasma core")
    print("STAR World: não carregado pela interface do Watch")
    print("Ações privilegiadas: bloqueadas no cliente")
    PlasmaStarWatchPC().run()


if __name__ == "__main__":
    main()
