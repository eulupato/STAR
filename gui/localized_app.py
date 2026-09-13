"""Camada de localização da GUI principal da STAR.

Reutiliza ``StarApp`` integralmente e altera somente superfícies textuais. A lógica
de chat, voz, memória, navegação, ilhas e closet permanece na classe estável.
"""
from __future__ import annotations

import tkinter as tk

from gui.app import StarApp


_UI_PREFIXES = ("◈ ", "🟢 ", "🔴 ", "⚡ ", "⭐ ", "🎙️ ", "🎤 ", "🔊 ")


def localize_ui_text(manager, text: str) -> str:
    """Localiza texto fixo conhecido sem tocar em valores/dados dinâmicos."""
    value = str(text or "")
    if not value:
        return value
    direct = manager.localization.static(value, manager.locale)
    if direct is not None:
        return direct
    for prefix in _UI_PREFIXES:
        if value.startswith(prefix):
            tail = value[len(prefix):]
            translated = manager.localization.static(tail, manager.locale)
            if translated is not None:
                return prefix + translated
    return value


class LocalizedStarApp(StarApp):
    """A mesma GUI V1.9, com localização aplicada como camada de apresentação."""

    def __init__(self, brain):
        self._observed_locale = None
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
        """Redesenha textos somente quando o locale realmente muda."""
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

        # O placeholder é conteúdo de Entry, não a propriedade ``text``.
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
        super().show_menu()
        self._schedule_localization()

    def show_chat(self):
        super().show_chat()
        self._schedule_localization()

    def show_settings(self):
        super().show_settings()
        self._schedule_localization()

    def show_islands(self):
        super().show_islands()
        self._schedule_localization()

    def show_house(self):
        super().show_house()
        self._schedule_localization()

    def show_closet(self):
        super().show_closet()
        self._schedule_localization()
