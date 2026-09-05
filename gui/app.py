"""Interface oficial 2D da STAR V1.9.

A classe ativa combina o shell estável (chat/voz/memória), o Menu/HUB vivo e os
ambientes funcionais do STAR WORLD. Não existe Core, identidade ou memória
cognitiva paralela.
"""
from __future__ import annotations

import tkinter as tk
from PIL import Image, ImageOps, ImageTk

from gui.shell import StarApp as StarShell
from gui.menu_hub import MenuHubMixin
from gui.world_scene import WorldSceneMixin
from gui.world_home_garden import HomeGardenMixin
from gui.world_workspaces import WorkspaceMixin
from gui.world_systems import WorldSystemsMixin
from gui.world_state import WorldState
from gui.theme import (
    BG, PANEL, PANEL_3, BORDER, TEXT, MUTED, BLUE, GREEN, RED,
    BODY_FONT, BODY_BOLD, SMALL_BOLD, PIXEL_TITLE,
)


class StarApp(MenuHubMixin, WorldSceneMixin, HomeGardenMixin, WorkspaceMixin, WorldSystemsMixin, StarShell):
    """STAR V1.9 + STAR WORLD 2D funcional, preservando o mesmo StarCore."""

    REFERENCE_FILES = {
        "menu": "menusembotao.jpeg", "kitchen": "kitchen.webp", "laboratory": "laboratory.webp",
        "library": "library.webp", "observatory": "observatory.webp", "cura": "cura.webp", "turnaround": "star_turnaround.webp",
    }
    REFERENCE_FALLBACKS = {
        "menu": ("menu_face.webp", "star_menu_face.jpg"),
        "kitchen": ("kitchen_reference.jpg",),
    }

    SETTINGS_SECTIONS = (
        ("general", "⚙", "GERAL"), ("appearance", "◉", "APARÊNCIA"),
        ("voice", "🎙", "VOZ"), ("audio", "◖", "ÁUDIO"),
        ("models", "▣", "MODELOS"), ("memory", "♧", "MEMÓRIA"),
        ("knowledge", "▤", "CONHECIMENTO"), ("privacy", "◇", "PRIVACIDADE"),
        ("permissions", "⌕", "PERMISSÕES"), ("devices", "⌁", "DISPOSITIVOS"),
        ("world", "◎", "STAR WORLD"), ("about", "ⓘ", "SOBRE A STAR"),
    )

    def __init__(self, brain):
        self.world = WorldState(self._project_root())
        self._blink_after = None
        self._blink_items = []
        self.menu_image_metrics = None
        self.settings_return = "menu"
        self.atelier_color = "#F18ACB"
        super().__init__(brain)

    def _reference_path(self, key):
        folder = self._project_root() / "assets" / "reference"
        canonical = folder / self.REFERENCE_FILES.get(key, key)
        if canonical.exists():
            return canonical
        fallbacks = self.REFERENCE_FALLBACKS.get(key, ())
        if isinstance(fallbacks, str):
            fallbacks = (fallbacks,)
        for fallback in fallbacks:
            legacy = folder / fallback
            if legacy.exists():
                return legacy
        return canonical

    @staticmethod
    def _project_root():
        from pathlib import Path
        return Path(__file__).resolve().parent.parent

    def clear_screen(self):
        if getattr(self, "_blink_after", None):
            try:
                self.window.after_cancel(self._blink_after)
            except Exception:
                pass
            self._blink_after = None
        self._blink_items = []
        super().clear_screen()

    def _photo(self, path, size, *, fit=True, key=None):
        """Cache de imagens com nearest-neighbour para preservar pixel art."""
        from pathlib import Path
        path = Path(path); width=max(1,int(size[0])); height=max(1,int(size[1]))
        cache_key = key or f"{path}:{width}x{height}:{fit}:pixel"
        if cache_key in self.photo_cache:
            return self.photo_cache[cache_key]
        if not path.exists() or path.stat().st_size == 0:
            return None
        try:
            with Image.open(path) as source:
                image = source.convert("RGBA")
            if fit:
                image = ImageOps.fit(image, (width, height), Image.Resampling.NEAREST)
            else:
                image.thumbnail((width, height), Image.Resampling.NEAREST)
            photo = ImageTk.PhotoImage(image)
            self.photo_cache[cache_key] = photo
            return photo
        except Exception:
            return None

    def show_settings(self, section="general"):
        previous = getattr(self, "current_screen", "menu")
        if previous != "settings":
            self.settings_return = "chat" if previous == "chat" else "menu"
        self.clear_screen(); self.current_screen="settings"
        root=tk.Frame(self.window,bg=BG); root.pack(fill="both",expand=True)
        back=self.show_chat if self.settings_return=="chat" else self.show_menu
        self._button(root,"← VOLTAR",back,subtle=True).place(x=20,y=20)
        side=tk.Frame(root,bg=PANEL,highlightbackground=BORDER,highlightthickness=1)
        side.place(relx=.08,rely=.12,relwidth=.22,relheight=.78)
        tk.Label(side,text="STAR\nCONFIGURAÇÕES",bg=PANEL,fg=TEXT,font=SMALL_BOLD,justify="left").pack(anchor="w",padx=16,pady=16)
        for key,icon,label in self.SETTINGS_SECTIONS:
            tk.Button(side,text=f"{icon}  {label}",command=lambda k=key:self.show_settings(k),
                      bg=PANEL_3 if key==section else PANEL,fg=TEXT,activebackground=PANEL_3,
                      activeforeground=TEXT,relief=tk.FLAT,anchor="w",font=SMALL_BOLD,
                      padx=14,pady=7,cursor="hand2").pack(fill="x",padx=10,pady=1)
        panel=tk.Frame(root,bg=PANEL,highlightbackground=BORDER,highlightthickness=1)
        panel.place(relx=.32,rely=.12,relwidth=.60,relheight=.78)
        self._render_settings(panel,section)

    def _render_settings(self,panel,section):
        title=dict((k,l) for k,_i,l in self.SETTINGS_SECTIONS).get(section,section)
        tk.Label(panel,text=title,bg=PANEL,fg=TEXT,font=PIXEL_TITLE).pack(anchor="w",padx=28,pady=(28,10))
        if section=="general":
            tk.Label(panel,text="Modo de operação",bg=PANEL,fg=MUTED,font=SMALL_BOLD).pack(anchor="w",padx=28,pady=8)
            row=tk.Frame(panel,bg=PANEL); row.pack(anchor="w",padx=28)
            for mode in ("local","lan","online"):
                self._button(row,mode.upper(),lambda m=mode:self._set_operation_mode(m),accent=self.operation_mode==mode).pack(side="left",padx=4)
            self._settings_text(panel,"LOCAL é o estado nativo da STAR. LAN conecta endpoints locais. ONLINE acrescenta recursos externos opcionais.")
        elif section=="appearance":
            self._settings_text(panel,f"Skin atual: {self.selected_skin}")
            self._button(panel,"ABRIR CLOSET",self.show_closet,accent=True).pack(anchor="w",padx=28,pady=12)
        elif section=="voice":
            self._settings_text(panel,self.voice.tts_description)
            row=tk.Frame(panel,bg=PANEL); row.pack(anchor="w",padx=28,pady=8)
            self._button(row,"FAST",lambda:self._set_voice_mode("fast"),accent=self.voice.mode=="fast").pack(side="left",padx=3)
            self._button(row,"OFFICIAL",lambda:self._set_voice_mode("official"),accent=self.voice.mode=="official").pack(side="left",padx=3)
            self._button(panel,"TESTAR VOZ OFICIAL",self._test_voice).pack(anchor="w",padx=28,pady=10)
            self.voice_test_label=tk.Label(panel,text="Pronto.",bg=PANEL,fg=MUTED,font=BODY_FONT); self.voice_test_label.pack(anchor="w",padx=28)
        elif section=="audio":
            self._settings_text(panel,f"Microfone: {'PRONTO' if self.recorder.available else 'INDISPONÍVEL'}\nSTT: {'PRONTO' if self.voice.stt_configured else 'INSTALAÇÃO PENDENTE'}")
        elif section=="models":
            self._settings_text(panel,"Modelos são ferramentas da STAR, não sua identidade. Model Router avançado pertence à V2.3.")
        elif section=="memory":
            self._settings_text(panel,f"Memória persistente inicializada. Conversas carregadas: {len(self.chat_history)}. O estado visual do mundo fica separado em runtime/.")
        elif section=="knowledge":
            try: stats=self.brain.packs.stats()
            except Exception: stats={"packs":0,"entries":0}
            self._settings_text(panel,f"Knowledge Packs: {stats.get('packs',0)}\nEntradas: {stats.get('entries',0)}\nPDF/RAG massivo continua na V3 KNOWLEDGE.")
        elif section=="privacy":
            self._settings_text(panel,"Local-first: bancos, referências de voz, estados pessoais e runtime ficam locais por padrão.")
        elif section=="permissions":
            self._settings_text(panel,"Permission Manager completo ainda é futuro. Ações remotas críticas permanecem bloqueadas na Foundation.")
        elif section=="devices":
            self._settings_text(panel,"PC CORE: principal\nSTAR Mobile iOS: EXPERIMENTAL\nSTAR Watch Android: EXPERIMENTAL\nGateway LAN: OPT-IN\nEndpoints não possuem MIND separado.")
        elif section=="world":
            self._settings_text(panel,"STAR WORLD 2D: Casa, Laboratório/Central, Biblioteca, Estúdio, Ateliê, Jardim, Correios, Cura, Heróis e Idiomas.")
            self._button(panel,"ABRIR HUB",self.show_hub,accent=True).pack(anchor="w",padx=28,pady=10)
        elif section=="about":
            from config import VERSION
            self._settings_text(panel,f"S.T.A.R. — System for Thought, Analysis and Response\nV{VERSION} FINAL — FOUNDATION\nPróxima geração: V2.0 MIND\nInternet amplia a STAR; não constitui a STAR.")

    def _settings_text(self,panel,text):
        tk.Label(panel,text=text,bg=PANEL,fg=TEXT,font=BODY_FONT,wraplength=690,justify="left").pack(anchor="w",padx=28,pady=12)

    def _set_operation_mode(self,mode):
        self.operation_mode=mode; self.online_mode=mode=="online"
        try: self.brain.network_enabled=self.online_mode
        except Exception: pass
        self._save_operation_mode(); self.show_settings("general")

    def _set_voice_mode(self,mode):
        self.voice.set_voice_mode(mode); self._save_voice_mode(); self.show_settings("voice")

    def _test_voice(self):
        self.voice.test_official_audio_async(lambda ok,error:self.response_queue.put(("voice_test",(ok,error))))

    def _set_voice_test_message(self,message,ok):
        if self.voice_test_label:
            try: self.voice_test_label.config(text=message,fg=GREEN if ok else RED)
            except tk.TclError: pass
