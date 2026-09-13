"""STAR Watch Plasma Orbit com idioma global, People central e tela AGORA.

A camada reaproveita o renderer V0.4 e o STAR Core. Nenhum cadastro, memória ou
conhecimento é duplicado no relógio: People, Cura, idioma e clima vêm do Core.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import threading
import tkinter as tk

from clients import star_watch_app as watch_base
from clients import star_watch_visual as visual
from core.language_profiles import LOCALE_ORDER
from core.weather import weather_description

NOW_MODE = watch_base.WatchMode("now", "AGORA", "AGORA")
LANGUAGE_MODE = watch_base.WatchMode("language", "IDIOMA", "LANG")

modes = list(watch_base.WATCH_MODES)
if not any(mode.key == "now" for mode in modes):
    voice_index = next((index for index, mode in enumerate(modes) if mode.key == "voice"), 0)
    modes.insert(voice_index + 1, NOW_MODE)
if not any(mode.key == "language" for mode in modes):
    settings_index = next((index for index, mode in enumerate(modes) if mode.key == "settings"), len(modes))
    modes.insert(settings_index, LANGUAGE_MODE)
watch_base.WATCH_MODES = tuple(modes)
visual.WATCH_MODES = watch_base.WATCH_MODES


class StarWatchLanguageVisualApp(visual.StarWatchVisualApp):
    def __init__(self):
        self._swipe_start = None
        self._now_weather_line = ""
        self._now_weather_loading = False
        super().__init__()
        # Remove o PeopleStore JSON legado do simulador. O relógio passa a enxergar
        # a mesma fonte central que PC/Mobile/Core.
        self.people = self._core().people
        self.canvas.unbind("<Button-1>")
        self.canvas.bind("<ButtonPress-1>", self._swipe_press)
        self.canvas.bind("<ButtonRelease-1>", self._swipe_release)

    def render(self):
        super().render()
        self._localize_static_canvas_text()

    def _localize_static_canvas_text(self):
        manager = self._core().language
        for item in self.canvas.find_all():
            try:
                text = self.canvas.itemcget(item, "text")
            except tk.TclError:
                continue
            if not text:
                continue
            localized = manager.localize_static(text)
            if localized != text:
                self.canvas.itemconfigure(item, text=localized)

    def _swipe_press(self, event):
        self._swipe_start = (event.x, event.y)

    def _swipe_release(self, event):
        start = self._swipe_start
        self._swipe_start = None
        if start is None:
            return
        dx, dy = event.x - start[0], event.y - start[1]
        if abs(dx) >= 70 and abs(dx) > abs(dy) * 1.2:
            if dx < 0:
                self.model.active_mode = "now"
                self.message = ""
                self._refresh_now_weather_async()
            else:
                self.model.back()
                self.message = ""
            self.render()
            return
        # Toque curto mantém o comportamento original do núcleo/bezel.
        watch_base.StarWatchApp._on_click(self, event)

    def _refresh_now_weather_async(self):
        core = self._core()
        if not core.network_enabled:
            self._now_weather_line = "Clima ao vivo: offline — nenhuma rede foi acionada."
            return
        if self._now_weather_loading:
            return
        self._now_weather_loading = True
        self._now_weather_line = "Clima: atualizando..."

        def work():
            snapshot = None
            try:
                snapshot = core.weather.current()
            except Exception:
                snapshot = None
            if snapshot is None:
                line = "Clima: indisponível agora."
            else:
                line = (
                    f"{snapshot.temperature_c:.0f} °C • {weather_description(snapshot.weather_code)}\n"
                    f"{snapshot.location} • umidade {snapshot.humidity_pct}%"
                )
            self._now_weather_loading = False
            self._now_weather_line = line
            if not self.closed and self.model.active_mode == "now":
                self.root.after(0, self.render)

        threading.Thread(target=work, daemon=True, name="STAR-Watch-NowWeather").start()

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
            self.message = manager.message("language_confirmed", display=manager.display())
            self.model.back()
            self.render()
            return
        if self.model.active_mode == "now":
            self._refresh_now_weather_async()
            self.render()
            return
        super().press()

    def _add_person(self):
        from tkinter import filedialog, simpledialog
        name = simpledialog.askstring("STAR People", "Nome:", parent=self.root)
        if not name:
            return
        notes = simpledialog.askstring("STAR People", "Observações:", parent=self.root) or ""
        image = filedialog.askopenfilename(
            parent=self.root,
            title="Foto opcional",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")],
        )
        try:
            person = self.people.upsert(name, notes=notes, source="watch-local")
            if image:
                self.people.add_image(person["person_id"], Path(image))
            self.message = f"{name} foi salvo no People central da STAR."
        except (ValueError, OSError) as exc:
            self.message = str(exc)
        self.render()

    def _draw_mode_static(self, key: str):
        if key == "language":
            return self._draw_language_mode()
        if key == "now":
            return self._draw_now_mode()
        return super()._draw_mode_static(key)

    def _draw_language_mode(self):
        c = self.canvas
        manager = self._core().language
        current = manager.profile()
        order = LOCALE_ORDER
        index = order.index(current["code"])
        previous = manager.profile(order[(index - 1) % len(order)])
        following = manager.profile(order[(index + 1) % len(order)])

        c.create_text(self.CX, 82, text="S  T  A  R", fill=self.COLORS["text"], font=("Segoe UI Light", 15), tags=("hud",))
        c.create_text(self.CX, 112, text=manager.localize_static("IDIOMA"), fill=self._theme().primary, font=("Segoe UI Semibold", 11), tags=("hud",))
        c.create_text(self.CX, 212, text=current["flag"], fill=self.COLORS["text"], font=("Segoe UI Emoji", 42), tags=("hud",))
        c.create_text(self.CX, 274, text=current["name"], fill=self.COLORS["text"], width=390, font=("Segoe UI Semibold", 15), tags=("hud",))
        c.create_text(112, 332, text=f"‹  {previous['flag']}\n{previous['code']}", fill=self.COLORS["muted"], justify="center", font=("Segoe UI Emoji", 10), tags=("hud",))
        c.create_text(self.SIZE - 112, 332, text=f"{following['flag']}  ›\n{following['code']}", fill=self.COLORS["muted"], justify="center", font=("Segoe UI Emoji", 10), tags=("hud",))
        c.create_text(self.CX, 410, text=manager.localize_static("GIRE PARA TROCAR • PRESSIONE PARA CONFIRMAR"), fill=self.COLORS["muted"], font=("Segoe UI", 9), tags=("hud",))
        kind = current.get("kind", "modern")
        note = current.get("note") or "Texto, voz e respostas usam a camada local quando houver recursos instalados."
        c.create_text(self.CX, 474, text=f"{kind.upper()} • {note}", fill=self.COLORS["muted_2"], width=390, justify="center", font=("Segoe UI", 8), tags=("hud",))
        c.create_text(self.CX, 536, text=self.message or manager.display(), fill=self._theme().secondary, width=380, justify="center", font=("Segoe UI Semibold", 10), tags=("hud",))

    def _draw_now_mode(self):
        c = self.canvas
        core = self._core()
        now = datetime.now()
        cure = core.cure.stats()
        people = core.people.stats()
        manager = core.language
        network = "ONLINE" if core.network_enabled else "OFFLINE"
        if not self._now_weather_line:
            self._refresh_now_weather_async()

        c.create_text(self.CX, 82, text="S  T  A  R", fill=self.COLORS["text"], font=("Segoe UI Light", 15), tags=("hud",))
        c.create_text(self.CX, 112, text=manager.localize_static("AGORA"), fill=self._theme().primary, font=("Segoe UI Semibold", 11), tags=("hud",))
        c.create_text(self.CX, 205, text=now.strftime("%H:%M"), fill=self.COLORS["text"], font=("Segoe UI Semibold", 38), tags=("hud",))
        c.create_text(self.CX, 250, text=now.strftime("%d/%m/%Y"), fill=self.COLORS["muted"], font=("Segoe UI", 11), tags=("hud",))
        c.create_text(
            self.CX, 335,
            text=(
                f"{self._now_weather_line}\n\n"
                f"{network} • {manager.display()}\n"
                f"Cura: {'KNOWN-GOOD' if cure.get('known_good') else 'SEM BASELINE'} • People: {people.get('people', 0)}"
            ),
            fill=self.COLORS["text"], width=400, justify="center", font=("Segoe UI", 10), tags=("hud",),
        )
        c.create_text(self.CX, 485, text="← deslize para AGORA • deslize → para voltar", fill=self.COLORS["muted"], font=("Segoe UI", 9), tags=("hud",))
        c.create_text(self.CX, 535, text="Pressione para atualizar o clima quando ONLINE.", fill=self.COLORS["muted_2"], width=380, justify="center", font=("Segoe UI", 8), tags=("hud",))


if __name__ == "__main__":
    StarWatchLanguageVisualApp().run()
