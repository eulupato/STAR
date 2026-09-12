"""STAR Watch Plasma Orbit com seleção lateral de idioma.

A camada reaproveita integralmente o renderer V0.4 e adiciona somente o modo IDIOMA.
Girar o STAR Ring dentro da tela percorre bandeiras/perfis; pressionar confirma e volta.
"""
from __future__ import annotations

from clients import star_watch_app as watch_base
from clients import star_watch_visual as visual

LANGUAGE_MODE = watch_base.WatchMode("language", "IDIOMA", "LANG")
if not any(mode.key == "language" for mode in watch_base.WATCH_MODES):
    watch_base.WATCH_MODES = watch_base.WATCH_MODES + (LANGUAGE_MODE,)
visual.WATCH_MODES = watch_base.WATCH_MODES


class StarWatchLanguageVisualApp(visual.StarWatchVisualApp):
    def rotate(self, steps: int):
        if self.model.active_mode == "language":
            locale = self._core().language.cycle(steps)
            self.message = self._core().language.display(locale)
            self.render()
            return
        super().rotate(steps)

    def press(self):
        if self.model.active_mode == "language":
            self.message = f"Idioma confirmado: {self._core().language.display()}"
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
            text="IDIOMA",
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
            text="GIRE PARA TROCAR • PRESSIONE PARA CONFIRMAR",
            fill=self.COLORS["muted"],
            font=("Segoe UI", 9),
            tags=("hud",),
        )
        c.create_text(
            self.CX,
            474,
            text="A seleção vale para texto, voz, traduções e respostas do Core.",
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
