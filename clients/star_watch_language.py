"""STAR Watch Plasma Orbit com seleção e localização global de idioma.

A camada reaproveita integralmente o renderer V0.4. O idioma ativo vem do mesmo
LanguageManager usado pelo Core; não existe catálogo paralelo do Watch.
"""
from __future__ import annotations

import tkinter as tk

from clients import star_watch_app as watch_base
from clients import star_watch_visual as visual

LANGUAGE_MODE = watch_base.WatchMode("language", "IDIOMA", "LANG")
if not any(mode.key == "language" for mode in watch_base.WATCH_MODES):
    modes = list(watch_base.WATCH_MODES)
    settings_index = next(
        (index for index, mode in enumerate(modes) if mode.key == "settings"),
        len(modes),
    )
    modes.insert(settings_index, LANGUAGE_MODE)
    watch_base.WATCH_MODES = tuple(modes)
visual.WATCH_MODES = watch_base.WATCH_MODES


class StarWatchLanguageVisualApp(visual.StarWatchVisualApp):
    def render(self):
        super().render()
        self._localize_static_canvas_text()

    def _localize_static_canvas_text(self):
        """Localiza somente textos fixos conhecidos; dados dinâmicos ficam intactos."""
        manager = self._core().language
        for item in self.canvas.find_all():
            try:
                text = self.canvas.itemcget(item, "text")
            except tk.TclError:
                continue
            if not text:
                continue
            localized = manager.localization.static(text, manager.locale)
            if localized is not None and localized != text:
                self.canvas.itemconfigure(item, text=localized)

    def rotate(self, steps: int):
        if self.model.active_mode == "language":
            locale = self._core().language.cycle(steps)
            self.message = self._core().language.display(locale)
            self.render()
            return
        super().rotate(steps)

    def press(self):
        if self.model.active_mode == "language":
            manager = self._core().language
            self.message = manager.message(
                "language_confirmed",
                display=manager.display(),
            )
            self.model.back()
            self.render()
            return
        super().press()

    def _draw_mode_static(self, key: str):
        if key != "language":
            return super()._draw_mode_static(key)

        c = self.canvas
        manager = self._core().language
        current = manager.profile()
        order = ("pt-BR", "en-US", "en-GB", "es-ES", "it-IT", "fr-FR")
        index = order.index(current["code"])
        previous = manager.profile(order[(index - 1) % len(order)])
        following = manager.profile(order[(index + 1) % len(order)])

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
            text=manager.localize_static("IDIOMA"),
            fill=self._theme().primary,
            font=("Segoe UI Semibold", 11),
            tags=("hud",),
        )
        c.create_text(
            self.CX,
            212,
            text=current["flag"],
            fill=self.COLORS["text"],
            font=("Segoe UI Emoji", 42),
            tags=("hud",),
        )
        c.create_text(
            self.CX,
            274,
            text=current["name"],
            fill=self.COLORS["text"],
            font=("Segoe UI Semibold", 16),
            tags=("hud",),
        )
        c.create_text(
            112,
            332,
            text=f"‹  {previous['flag']}\n{previous['code']}",
            fill=self.COLORS["muted"],
            justify="center",
            font=("Segoe UI Emoji", 10),
            tags=("hud",),
        )
        c.create_text(
            self.SIZE - 112,
            332,
            text=f"{following['flag']}  ›\n{following['code']}",
            fill=self.COLORS["muted"],
            justify="center",
            font=("Segoe UI Emoji", 10),
            tags=("hud",),
        )
        c.create_text(
            self.CX,
            410,
            text=manager.localize_static("GIRE PARA TROCAR • PRESSIONE PARA CONFIRMAR"),
            fill=self.COLORS["muted"],
            font=("Segoe UI", 9),
            tags=("hud",),
        )
        c.create_text(
            self.CX,
            474,
            text=manager.localize_static(
                "A seleção vale para texto, voz, traduções e respostas do Core."
            ),
            fill=self.COLORS["muted_2"],
            width=350,
            justify="center",
            font=("Segoe UI", 9),
            tags=("hud",),
        )
        c.create_text(
            self.CX,
            536,
            text=self.message or manager.display(),
            fill=self._theme().secondary,
            width=360,
            justify="center",
            font=("Segoe UI Semibold", 10),
            tags=("hud",),
        )


if __name__ == "__main__":
    StarWatchLanguageVisualApp().run()
