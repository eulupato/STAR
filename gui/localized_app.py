"""Camada de localização da GUI principal da STAR.

Reutiliza ``StarApp`` integralmente e altera somente superfícies textuais, a
ponte de anexos B25 e a entrega de eventos proativos já decididos pelo scheduler.
"""
from __future__ import annotations

from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog

from gui.app import StarApp


_UI_PREFIXES = ("◈ ", "🟢 ", "🔴 ", "⚡ ", "⭐ ", "🎙️ ", "🎤 ", "🔊 ", "🖼️ ", "⏰ ")


def localize_ui_text(manager, text: str) -> str:
    value = str(text or "")
    if not value:
        return value
    for prefix in _UI_PREFIXES:
        if value.startswith(prefix):
            tail = value[len(prefix):]
            translated = manager.localization.static(tail, manager.locale)
            if translated is not None:
                return prefix + translated
    direct = manager.localization.static(value, manager.locale)
    return direct if direct is not None else value


class LocalizedStarApp(StarApp):
    """A mesma GUI V1.9, com localização, percepção e eventos temporais."""

    IMAGE_TYPES = (
        ("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp"),
        ("JPEG", "*.jpg *.jpeg"), ("PNG", "*.png"), ("WebP", "*.webp"),
        ("Todos os arquivos", "*.*"),
    )

    def __init__(self, brain):
        self._observed_locale = None
        self.pending_image_path: Path | None = None
        super().__init__(brain)
        manager = self.language
        self._observed_locale = manager.locale if manager is not None else None
        self._schedule_localization()
        self._watch_locale()
        self._watch_proactivity()

    @property
    def language(self):
        return getattr(self.brain, "language", None)

    def _loc(self, text: str) -> str:
        manager = self.language
        return localize_ui_text(manager, text) if manager is not None else str(text)

    def _schedule_localization(self) -> None:
        try: self.window.after_idle(self._localize_current_screen)
        except (AttributeError, tk.TclError): pass

    def _watch_locale(self) -> None:
        if getattr(self, "_closing", False): return
        manager = self.language; current = manager.locale if manager is not None else None
        if current != self._observed_locale:
            self._observed_locale = current; self._localize_current_screen()
        try: self.window.after(300, self._watch_locale)
        except (AttributeError, tk.TclError): pass

    def _watch_proactivity(self) -> None:
        """Entrega lembretes sem permitir que scheduler execute uma ação."""
        if getattr(self, "_closing", False):
            return
        runtime = getattr(self.brain, "proactivity", None)
        if runtime is not None:
            for event in runtime.drain(limit=8, notify_only=True):
                content = str(event.get("content") or "").strip()
                if not content:
                    continue
                if self.current_screen == "chat":
                    self._activate_conversation()
                    self._append_star("⏰ " + content)
                # A voz é uma superfície de notificação; não executa a intenção.
                try:
                    self.voice.speak_async("Lembrete. " + content.replace("Lembrete:", "", 1).strip())
                except Exception:
                    pass
        try: self.window.after(500, self._watch_proactivity)
        except (AttributeError, tk.TclError): pass

    def _localize_current_screen(self) -> None:
        manager = self.language
        if manager is None: return
        def visit(widget):
            try: keys = widget.keys()
            except (AttributeError, tk.TclError): keys = ()
            if "text" in keys:
                try:
                    current = widget.cget("text"); translated = localize_ui_text(manager, current)
                    if translated != current: widget.configure(text=translated)
                except (AttributeError, tk.TclError): pass
            try: children = widget.winfo_children()
            except (AttributeError, tk.TclError): children = ()
            for child in children: visit(child)
        visit(self.window)
        entry = getattr(self, "entry", None)
        if entry is not None:
            try:
                current = entry.get(); translated = localize_ui_text(manager, current)
                if translated != current:
                    entry.delete(0, tk.END); entry.insert(0, translated)
            except (AttributeError, tk.TclError): pass

    def clear_screen(self):
        super().clear_screen(); self._schedule_localization()

    def _button(self, parent, text, command, small=False):
        return super()._button(parent, self._loc(text), command, small=small)

    def _set_status(self, text, color):
        return super()._set_status(self._loc(text), color)

    def _append_user(self, text): self._append(self._loc("Você"), text, "user")
    def _append_system(self, text): self._append(self._loc("SISTEMA"), text, "system")

    def _build_input(self, root):
        """Transforma o antigo '+' decorativo em anexo de imagem real."""
        super()._build_input(root)
        inner = getattr(self.entry, "master", None)
        if inner is None: return
        try:
            for child in tuple(inner.winfo_children()):
                if isinstance(child, tk.Label) and child.cget("text") == "+":
                    child.destroy(); break
            self.attach_button = tk.Button(
                inner, text="+", command=self.attach_image, bg="#25364b", fg="#d8e7f5",
                activebackground="#304760", activeforeground="white", relief=tk.FLAT,
                borderwidth=0, font=("Segoe UI", 23), cursor="hand2",
            )
            self.attach_button.pack(side="left", padx=(16, 8), before=self.entry)
        except tk.TclError: return

    def attach_image(self):
        if self.processing: return
        selected = filedialog.askopenfilename(parent=self.window, title="Selecionar imagem para a STAR", filetypes=self.IMAGE_TYPES)
        if not selected: return
        path = Path(selected).expanduser()
        if not path.is_file():
            self._activate_conversation(); self._append_system("🖼️ Não consegui acessar essa imagem."); return
        self.pending_image_path = path; self._activate_conversation()
        self._append_system(f"🖼️ Imagem anexada: {path.name}. Ela será percebida localmente pelo B25 ao enviar a mensagem.")

    def send_message(self):
        if self.processing or not hasattr(self, "entry"): return
        if self.pending_image_path is None: return super().send_message()
        self.voice.cancel_speech(); text = self.entry.get().strip()
        if not text or text == "Pergunte algo à STAR...": text = "O que você observa nesta imagem?"
        path = self.pending_image_path; self.pending_image_path = None; self.entry.delete(0, tk.END)
        self._activate_conversation(); self._append_user(f"[imagem: {path.name}] {text}")
        try: self.memory.save("Você", f"[imagem anexada: {path.name}] {text}")
        except Exception: pass
        self.processing = True; self.entry.config(state=tk.DISABLED); self.send_button.config(state=tk.DISABLED)
        self._set_status("PROCESSANDO", self.gold); self._load_avatar("thinking")
        threading.Thread(target=self._process_image_message, args=(text, path), daemon=True).start()

    def _process_image_message(self, text: str, path: Path):
        try:
            runtime = getattr(self.brain, "perception_runtime", None)
            if runtime is None: raise RuntimeError("runtime perceptivo indisponível")
            runtime.ingest_image(path, source="desktop-chat-attachment")
            response = self.brain.process(text); self.response_queue.put(("success", response))
        except Exception as exc:
            self.response_queue.put(("error", f"Falha ao perceber a imagem: {exc}"))

    def show_menu(self): super().show_menu(); self._schedule_localization()
    def show_chat(self): super().show_chat(); self._schedule_localization()
    def show_settings(self): super().show_settings(); self._schedule_localization()
    def show_islands(self): super().show_islands(); self._schedule_localization()
    def show_house(self): super().show_house(); self._schedule_localization()
    def show_closet(self): super().show_closet(); self._schedule_localization()
