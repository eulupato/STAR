"""Camada de localização da GUI principal da STAR.

Reutiliza ``StarApp`` integralmente e adiciona superfícies localizadas sem duplicar
lógica de Core. O painel AGORA usa dados locais imediatamente e nunca bloqueia a UI
esperando rede.
"""
from __future__ import annotations

from datetime import datetime
import threading
import tkinter as tk

from gui.app import StarApp
from core.weather import weather_description


_UI_PREFIXES = ("◈ ", "🟢 ", "🔴 ", "⚡ ", "⭐ ", "🎙️ ", "🎤 ", "🔊 ")


def localize_ui_text(manager, text: str) -> str:
    """Localiza texto fixo conhecido sem tocar em valores/dados dinâmicos."""
    value = str(text or "")
    if not value:
        return value
    for prefix in _UI_PREFIXES:
        if value.startswith(prefix):
            tail = value[len(prefix):]
            translated = manager.localize_static(tail)
            if translated != tail:
                return prefix + translated
    direct = manager.localize_static(value)
    return direct


class LocalizedStarApp(StarApp):
    """A mesma GUI V1.9, com localização aplicada como camada de apresentação."""

    def __init__(self, brain):
        self._observed_locale = None
        self._now_popup = None
        self._now_weather_label = None
        super().__init__(brain)
        manager = self.language
        self._observed_locale = manager.locale if manager is not None else None
        self._schedule_localization()
        self._watch_locale()

    @property
    def language(self):
        return getattr(self.brain, "language", None)

    def _loc(self, text: str) -> str:
        manager = self.language
        return localize_ui_text(manager, text) if manager is not None else str(text)

    def _schedule_localization(self) -> None:
        try:
            self.window.after_idle(self._localize_current_screen)
        except (AttributeError, tk.TclError):
            pass

    def _watch_locale(self) -> None:
        if getattr(self, "_closing", False):
            return
        manager = self.language
        current = manager.locale if manager is not None else None
        if current != self._observed_locale:
            self._observed_locale = current
            self._localize_current_screen()
        try:
            self.window.after(300, self._watch_locale)
        except (AttributeError, tk.TclError):
            pass

    def _localize_current_screen(self) -> None:
        manager = self.language
        if manager is None:
            return

        def visit(widget):
            try:
                keys = widget.keys()
            except (AttributeError, tk.TclError):
                keys = ()
            if "text" in keys:
                try:
                    current = widget.cget("text")
                    translated = localize_ui_text(manager, current)
                    if translated != current:
                        widget.configure(text=translated)
                except (AttributeError, tk.TclError):
                    pass
            try:
                children = widget.winfo_children()
            except (AttributeError, tk.TclError):
                children = ()
            for child in children:
                visit(child)

        visit(self.window)
        entry = getattr(self, "entry", None)
        if entry is not None:
            try:
                current = entry.get()
                translated = localize_ui_text(manager, current)
                if translated != current:
                    entry.delete(0, tk.END)
                    entry.insert(0, translated)
            except (AttributeError, tk.TclError):
                pass

    def _header(self, parent):
        super()._header(parent)
        # A Foundation não expõe o frame do header; ele é o último Frame criado
        # por _header. Acrescentamos AGORA sem reconstruir a navegação estável.
        try:
            frames = [child for child in parent.winfo_children() if isinstance(child, tk.Frame)]
            header = frames[-1]
            self._button(header, "AGORA", self.show_now_popup, small=True).pack(side="right", padx=4, pady=8)
        except (IndexError, tk.TclError):
            pass

    def show_now_popup(self):
        popup = self._now_popup
        if popup is not None:
            try:
                if popup.winfo_exists():
                    popup.lift(); popup.focus_force(); return
            except tk.TclError:
                pass

        popup = tk.Toplevel(self.window)
        self._now_popup = popup
        popup.title(f"STAR • {self._loc('AGORA')}")
        popup.geometry("430x470")
        popup.resizable(False, False)
        popup.configure(bg=self.bg)
        popup.transient(self.window)

        body = tk.Frame(popup, bg=self.bg, padx=28, pady=24)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=f"⭐  STAR • {self._loc('AGORA')}", fg=self.star, bg=self.bg, font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(body, text=datetime.now().strftime("%H:%M  •  %d/%m/%Y"), fg=self.text, bg=self.bg, font=("Segoe UI Semibold", 18)).pack(anchor="w", pady=(16, 18))

        core = self.brain
        manager = core.language
        cure = core.cure.stats()
        people = core.people.stats()
        try:
            mdrives = core.mdrives.stats()
        except Exception:
            mdrives = {"mdrives": 0}
        local_lines = (
            f"🌐 {'ONLINE' if core.network_enabled else 'OFFLINE'}\n"
            f"🌍 {manager.display()}\n"
            f"🩹 Cura: {'known-good ativo' if cure.get('known_good') else 'sem baseline'}\n"
            f"👥 People: {people.get('people', 0)} perfil(is)\n"
            f"💾 M.drives: {mdrives.get('mdrives', mdrives.get('drives', 0))}"
        )
        tk.Label(body, text=local_lines, fg=self.text, bg=self.panel, justify="left", anchor="w", padx=18, pady=14, font=("Segoe UI", 10)).pack(fill="x")

        self._now_weather_label = tk.Label(
            body,
            text="☁ Clima ao vivo: atualizando..." if core.network_enabled else "☁ Clima ao vivo: OFFLINE — nenhuma rede foi acionada.",
            fg=self.muted, bg=self.bg, justify="left", anchor="w", wraplength=370, font=("Segoe UI", 10),
        )
        self._now_weather_label.pack(fill="x", pady=(18, 12))
        tk.Label(
            body,
            text="Tudo acima, exceto clima ao vivo, funciona localmente. A busca web e o clima só acessam rede quando o modo ONLINE foi autorizado.",
            fg=self.muted, bg=self.bg, justify="left", wraplength=370, font=("Segoe UI", 9),
        ).pack(fill="x", pady=(4, 12))
        self._button(body, "FECHAR", popup.destroy, small=True).pack(anchor="e", pady=(12, 0))
        self._schedule_localization()

        if core.network_enabled:
            def weather_work():
                snapshot = None
                try:
                    snapshot = core.weather.current()
                except Exception:
                    snapshot = None
                if snapshot is None:
                    text = "☁ Clima: indisponível agora."
                else:
                    text = (
                        f"☁ {snapshot.location}\n"
                        f"{snapshot.temperature_c:.0f} °C • {weather_description(snapshot.weather_code)} • "
                        f"umidade {snapshot.humidity_pct}% • vento {snapshot.wind_kmh:.0f} km/h"
                    )
                try:
                    popup.after(0, lambda: self._update_now_weather(text))
                except tk.TclError:
                    pass
            threading.Thread(target=weather_work, daemon=True, name="STAR-PC-NowWeather").start()

    def _update_now_weather(self, text: str):
        label = self._now_weather_label
        try:
            if label is not None and label.winfo_exists():
                label.configure(text=text)
        except tk.TclError:
            pass

    def clear_screen(self):
        super().clear_screen()
        self._schedule_localization()

    def _button(self, parent, text, command, small=False):
        return super()._button(parent, self._loc(text), command, small=small)

    def _set_status(self, text, color):
        return super()._set_status(self._loc(text), color)

    def _append_user(self, text):
        self._append(self._loc("Você"), text, "user")

    def _append_system(self, text):
        self._append(self._loc("SISTEMA"), text, "system")

    def show_menu(self):
        super().show_menu(); self._schedule_localization()

    def show_chat(self):
        super().show_chat(); self._schedule_localization()

    def show_settings(self):
        super().show_settings(); self._schedule_localization()

    def show_islands(self):
        super().show_islands(); self._schedule_localization()

    def show_house(self):
        super().show_house(); self._schedule_localization()

    def show_closet(self):
        super().show_closet(); self._schedule_localization()
