"""Interface gráfica atual da STAR WORLD.

A GUI permanece desacoplada da lógica cognitiva: navegação, mídia e views
delegam conhecimento e conversação aos serviços do Core.
"""
from __future__ import annotations

import json
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

from PIL import Image, ImageTk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    APP_NAME,
    MENU_HEIGHT,
    MENU_WIDTH,
    VERSION,
    VOICE_CHAT_MODE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from core.avatar import AvatarManager
from core.emotion import EmotionManager
from core.logging_config import get_logger
from database.memory import Memory
from gui.heroes_view import HeroesIslandView
from gui.navigation import NavigationManager, ROUTES
from modules.media_controller import MediaController
from voice.audio_input import AudioRecorder
from voice.manager import VoiceManager

log = get_logger("gui")


class StarApp:
    def __init__(self, brain):
        self.brain = brain
        self.memory = Memory()
        self.avatar = AvatarManager()
        self.emotion = EmotionManager()
        self.voice = VoiceManager()
        self.voice.set_voice_mode(self._load_voice_mode())
        self.recorder = AudioRecorder()
        self.media = MediaController()
        self.tv_frame = None
        self.tv_status_label = None

        self.online_mode = False
        self.processing = False
        self.recording = False
        self._closing = False
        self._exit_overlay = None
        self.response_queue: queue.Queue = queue.Queue()
        self._subscribe_world_events()

        self.nav = NavigationManager()
        self.current_screen = "menu"
        self.session_messages: list[tuple[str, str]] = []

        self.chat = None
        self.chat_panel = None
        self.entry = None
        self.mic = None
        self.send_button = None
        self.status_label = None
        self.voice_test_label = None
        self.avatar_label = None
        self.avatar_photo = None
        self.closet_photo = None
        self.gallery_photo = None
        self.selected_skin = self._load_skin_selection()

        self.bg = "#0b1018"
        self.panel = "#131c29"
        self.panel_2 = "#172231"
        self.text = "#edf3fb"
        self.muted = "#9aa8bb"
        self.star = "#8fd0ff"
        self.user = "#c9b8ff"
        self.green = "#76e2a0"
        self.red = "#ff7c87"
        self.gold = "#ffd36e"
        self.pink = "#ff9dcc"

        self.window = tk.Tk()
        self.window.title(f"{APP_NAME} V{VERSION}")
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.window.minsize(900, 600)
        self.window.configure(bg=self.bg)
        self.window.protocol("WM_DELETE_WINDOW", self.request_exit)
        self.window.bind("<F11>", self.toggle_maximize)
        self.window.bind("<Escape>", self._escape_action)
        self.window.bind("<Control-l>", lambda _e: self.toggle_chat_panel())
        self.window.bind("<Control-k>", lambda _e: self.toggle_chat_panel())
        self.window.bind("<Configure>", self._schedule_media_sync, add="+")

        self.is_maximized = False
        self.normal_size = (WINDOW_WIDTH, WINDOW_HEIGHT)

        self.show_menu()
        self.window.after(60, self._check_response_queue)
        self.voice.warmup_stt_async()

    def _subscribe_world_events(self):
        mind = getattr(self.brain, "mind", None)
        if mind is None:
            return
        try:
            mind.events.subscribe(
                "MEDIA_REQUESTED",
                lambda event: self.response_queue.put(
                    ("media_command", dict(event.payload))
                ),
            )
        except Exception as exc:
            log.warning("Falha ao assinar eventos de mídia: %s", exc)

    def _handle_media_command(self, payload):
        action = str((payload or {}).get("action", ""))

        if action == "open_youtube":
            if not self.online_mode:
                return
            if self.nav.current != "living_room":
                self.navigate("living_room")
            self.window.after(80, self._open_youtube_tv)
            return

        if action == "fullscreen":
            self._tv_fullscreen()
        elif action == "restore":
            self._tv_restore()
        elif action == "close":
            self._tv_close()
        elif action == "pause":
            self.media.pause()
            self._refresh_media_status()
        elif action == "play":
            self.media.play()
            self._refresh_media_status()
        elif action == "volume":
            self.media.volume(int((payload or {}).get("value", 100)))
            self._refresh_media_status()

    @property
    def _user_settings_path(self):
        return PROJECT_ROOT / "user_settings.json"

    def _read_user_settings(self):
        try:
            return json.loads(self._user_settings_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("Configurações do usuário inválidas: %s", exc)
            return {}

    def _write_user_settings(self, **values):
        try:
            data = self._read_user_settings()
            data.update(values)
            self._user_settings_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except (OSError, TypeError) as exc:
            log.warning("Não foi possível salvar user_settings.json: %s", exc)

    def _load_voice_mode(self):
        mode = str(
            self._read_user_settings().get("voice_mode", VOICE_CHAT_MODE)
        ).lower()
        return mode if mode in {"official", "fast"} else VOICE_CHAT_MODE

    def _load_skin_selection(self):
        local = self._read_user_settings().get("skin")
        if local:
            return str(local)
        try:
            return json.loads(
                (PROJECT_ROOT / "config_skin.json").read_text(encoding="utf-8")
            ).get("skin", "original.jpeg")
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("config_skin.json inválido; usando skin padrão: %s", exc)
            return "original.jpeg"

    def _save_skin_selection(self):
        self._write_user_settings(skin=self.selected_skin)

    def _save_voice_mode(self):
        self._write_user_settings(voice_mode=self.voice.mode)

    # ------------------------------------------------------------------
    # Navegação
    # ------------------------------------------------------------------

    def clear_screen(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        self.chat = None
        self.chat_panel = None
        self.entry = None
        self.mic = None
        self.send_button = None
        self.status_label = None
        self.voice_test_label = None
        self.avatar_label = None
        self.tv_frame = None
        self.tv_status_label = None
        self._exit_overlay = None

    def _render_current(self):
        route = self.nav.current
        renderers = {
            "menu": self.show_menu,
            "hub": self.show_hub,
            "house": self.show_house,
            "living_room": self.show_living_room,
            "kitchen": self.show_kitchen,
            "bedroom": self.show_bedroom,
            "closet": self.show_closet,
            "gallery": self.show_gallery,
            "heroes": self.show_heroes,
            "settings": self._render_settings,
            "chat": self._render_expanded_chat,
        }
        renderers.get(route, self.show_hub)()

    def navigate(self, route):
        if self.nav.current == "living_room" and route != "living_room":
            self._close_media_if_open()
        self.nav.go(route)
        self._render_current()

    def go_back(self):
        if self.nav.current == "living_room":
            self._close_media_if_open()
        self.nav.back()
        self._render_current()

    def open_settings(self):
        if self.nav.current == "living_room":
            self._close_media_if_open()
        if self.nav.current != "settings":
            self.nav.open_overlay("settings")
        self._render_settings()

    def close_settings(self):
        self.nav.close_overlay("hub")
        self._render_current()

    def _escape_action(self, _event=None):
        if self._exit_overlay is not None:
            self._cancel_exit()
            return "break"
        if self.chat_panel is not None and self.nav.current != "chat":
            self._close_chat_panel()
            return "break"
        if self.is_maximized:
            self.restore_normal_size()
            return "break"
        if self.nav.current not in {"menu", "hub"}:
            self.go_back()
        return "break"

    # ------------------------------------------------------------------
    # Elementos visuais globais
    # ------------------------------------------------------------------

    def _gradient(self, parent):
        canvas = tk.Canvas(parent, bg=self.bg, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.tk.call("lower", str(canvas))

        def draw(_event=None):
            canvas.delete("gradient")
            width = max(canvas.winfo_width(), 1)
            height = max(canvas.winfo_height(), 1)
            for i in range(72):
                t = i / 71
                r = int(10 + 17 * (1 - t))
                g = int(14 + 36 * (1 - t))
                b = int(24 + 66 * (1 - t))
                y = int(i * height / 72)
                canvas.create_rectangle(
                    0,
                    y,
                    width,
                    y + height / 72 + 2,
                    fill=f"#{r:02x}{g:02x}{b:02x}",
                    outline="",
                    tags="gradient",
                )

        canvas.bind("<Configure>", draw)
        self.window.after(20, draw)

    def _header(self, parent, title=None, *, back=True):
        header = tk.Frame(parent, bg=self.panel_2, height=58)
        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=self.panel_2)
        left.pack(side="left", fill="y")
        if back and self.nav.current not in {"hub", "menu"}:
            self._button(left, "←", self.go_back, small=True).pack(
                side="left", padx=(10, 4), pady=9
            )
        tk.Label(
            left,
            text=f"⭐  {title or ROUTES[self.nav.current].label}",
            fg=self.star,
            bg=self.panel_2,
            font=("Segoe UI", 17, "bold"),
        ).pack(side="left", padx=10)

        right = tk.Frame(header, bg=self.panel_2)
        right.pack(side="right", fill="y", padx=10)

        status = "ONLINE" if self.online_mode else "OFFLINE"
        color = self.green if self.online_mode else self.red
        self.status_label = tk.Label(
            right,
            text=f"● V{VERSION} • {status}",
            fg=color,
            bg=self.panel_2,
            font=("Segoe UI", 8, "bold"),
        )
        self.status_label.pack(side="right", padx=(12, 4))

        self._button(right, "⚙", self.open_settings, small=True).pack(
            side="right", padx=3, pady=9
        )
        self._button(right, "💬", self.toggle_chat_panel, small=True).pack(
            side="right", padx=3, pady=9
        )
        if self.nav.current != "hub":
            self._button(right, "🏝 HUB", lambda: self.navigate("hub"), small=True).pack(
                side="right", padx=3, pady=9
            )

    def _button(self, parent, text, command, small=False, accent=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg="#315575" if accent else "#243247",
            fg=self.text,
            activebackground="#42698d",
            activeforeground=self.text,
            relief=tk.FLAT,
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 9 if small else 10, "bold"),
            padx=14,
            pady=7,
        )

    def _scene_title(self, parent, title, subtitle):
        box = tk.Frame(parent, bg=self.bg)
        box.pack(fill="x", padx=42, pady=(28, 8))
        tk.Label(
            box,
            text=title,
            fg=self.star,
            bg=self.bg,
            font=("Segoe UI", 28, "bold"),
        ).pack(anchor="w")
        tk.Label(
            box,
            text=subtitle,
            fg=self.muted,
            bg=self.bg,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

    def _world_card(self, parent, title, desc, command=None, status=None):
        card = tk.Frame(parent, bg=self.panel, padx=18, pady=16)
        tk.Label(
            card,
            text=title,
            fg=self.star,
            bg=self.panel,
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")
        tk.Label(
            card,
            text=desc,
            fg=self.text,
            bg=self.panel,
            wraplength=270,
            justify="left",
        ).pack(anchor="w", pady=(7, 10))
        if status:
            status_key = str(status).lower()
            status_map = {
                "available": ("🟢 DISPONÍVEL", self.green),
                "partial": ("🟡 PARCIAL", self.gold),
                "experimental": ("🟠 EXPERIMENTAL", self.gold),
                "planned": ("🔵 PLANEJADA", self.muted),
                "unavailable": ("⚫ INDISPONÍVEL", self.red),
            }
            label, color = status_map.get(
                status_key,
                (str(status).upper(), self.muted),
            )
            tk.Label(
                card,
                text=label,
                fg=color,
                bg=self.panel,
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w", pady=(0, 8))
        if command:
            self._button(card, "ENTRAR", command, small=True, accent=True).pack(anchor="w")
        return card

    def _place_star(self, parent, relx=0.5, rely=0.58, size=(250, 300)):
        holder = tk.Frame(parent, bg=self.bg)
        holder.place(relx=relx, rely=rely, anchor="center")
        label = tk.Label(holder, bg=self.bg, cursor="hand2")
        label.pack()
        self.avatar_label = label
        self._load_display_avatar(max_size=size)
        label.bind("<Button-1>", lambda _e: self.toggle_chat_panel())
        tk.Label(
            holder,
            text="clique na STAR para conversar",
            fg=self.muted,
            bg=self.bg,
            font=("Segoe UI", 8),
        ).pack(pady=(5, 0))

    # ------------------------------------------------------------------
    # Menu e HUB
    # ------------------------------------------------------------------

    def show_menu(self):
        self.clear_screen()
        self.nav.current = "menu"
        self.current_screen = "menu"
        if not self.is_maximized:
            self.window.geometry(f"{MENU_WIDTH}x{MENU_HEIGHT}")

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)

        center = tk.Frame(root, bg=self.bg)
        center.place(relx=0.5, rely=0.47, anchor="center")

        tk.Label(
            center,
            text="⭐",
            fg=self.gold,
            bg=self.bg,
            font=("Segoe UI Emoji", 48),
        ).pack(pady=(0, 4))
        tk.Label(
            center,
            text="STAR",
            fg=self.star,
            bg=self.bg,
            font=("Segoe UI", 37, "bold"),
        ).pack()
        tk.Label(
            center,
            text="System for Thought, Analysis and Response",
            fg=self.muted,
            bg=self.bg,
            font=("Segoe UI", 11),
        ).pack(pady=(4, 35))

        for label, cmd in (
            ("INICIAR", lambda: self.navigate("hub")),
            ("CONFIGURAÇÕES", self.open_settings),
            ("SAIR", self.request_exit),
        ):
            self._button(center, label, cmd, accent=(label == "INICIAR")).pack(
                fill="x", pady=6
            )

    def show_hub(self):
        self.clear_screen()
        self.nav.current = "hub"
        self.current_screen = "hub"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root, "STAR HUB", back=False)
        self._scene_title(
            root,
            "🏝️ STAR ISLANDS",
            "Escolha uma ilha. A Casa é o primeiro ambiente totalmente navegável.",
        )

        body = tk.Frame(root, bg=self.bg)
        body.pack(fill="both", expand=True, padx=36, pady=(8, 28))

        try:
            from core.islands import get_islands

            data = get_islands()
        except Exception as exc:
            log.error("Não foi possível carregar catálogo de ilhas: %s", exc)
            data = {}

        preferred = ["casa", "herois"]
        order = preferred + [key for key in data if key not in preferred]
        for idx, key in enumerate(order):
            if key not in data:
                continue
            item = data[key]
            status = item.get("status", "planned")
            enterable = status in {"available", "partial", "experimental"}
            card = self._world_card(
                body,
                f"{item.get('icon', '🏝️')} {item.get('name', key)}",
                item.get("description", ""),
                (lambda k=key: self._open_island(k))
                if enterable and key in {"casa", "herois"}
                else None,
                status,
            )
            card.grid(
                row=idx // 4,
                column=idx % 4,
                sticky="nsew",
                padx=6,
                pady=6,
            )
        for col in range(4):
            body.grid_columnconfigure(col, weight=1)

    def show_islands(self):
        self.navigate("hub")

    def _open_island(self, key):
        if key == "casa":
            self.navigate("house")
        elif key == "herois":
            self.navigate("heroes")

    def show_heroes(self):
        self.clear_screen()
        self.nav.current = "heroes"
        self.current_screen = "heroes"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root, "ILHA DOS HERÓIS")
        self._scene_title(
            root,
            "🦸 ILHA DOS HERÓIS",
            "Busca local ativa; acervo em consolidação por PDFs e fontes oficiais.",
        )

        knowledge = getattr(self.brain, "knowledge", None)
        if knowledge is None:
            tk.Label(
                root,
                text="Knowledge Engine indisponível.",
                fg=self.red,
                bg=self.bg,
                font=("Segoe UI", 12, "bold"),
            ).pack(pady=80)
            return

        palette = {
            "bg": self.bg,
            "panel": self.panel,
            "text": self.text,
            "muted": self.muted,
            "star": self.star,
        }
        view = HeroesIslandView(
            root,
            knowledge=knowledge,
            palette=palette,
            on_selected=self._hero_selected,
        )
        view.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def _hero_selected(self, entity):
        mind = getattr(self.brain, "mind", None)
        if mind is not None:
            mind.context.track_entity(
                entity.name,
                entity_id=entity.id,
                category=entity.category,
            )
            try:
                mind.events.publish(
                    "HERO_SELECTED",
                    {"entity_id": entity.id, "name": entity.name},
                    "world",
                )
            except Exception as exc:
                log.warning("Falha ao publicar HERO_SELECTED: %s", exc)

    # ------------------------------------------------------------------
    # Casa e cômodos
    # ------------------------------------------------------------------

    def show_house(self):
        self.clear_screen()
        self.nav.current = "house"
        self.current_screen = "house"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root, "CASA DA STAR")
        self._scene_title(
            root,
            "🏠 STAR HOUSE",
            "Ilha residencial navegável; os cômodos exibem seus próprios níveis de maturidade.",
        )

        stage = tk.Frame(root, bg=self.bg)
        stage.pack(fill="both", expand=True, padx=42, pady=20)

        house = tk.Frame(stage, bg=self.panel_2, padx=28, pady=24)
        house.place(relx=0.5, rely=0.47, anchor="center", relwidth=0.78, relheight=0.65)

        tk.Label(
            house,
            text="Escolha um cômodo",
            fg=self.text,
            bg=self.panel_2,
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(8, 20))

        rooms = tk.Frame(house, bg=self.panel_2)
        rooms.pack(expand=True)

        for col, (title, subtitle, route) in enumerate(
            (
                ("📺 SALA", "entretenimento e conversa", "living_room"),
                ("🍳 COZINHA", "receitas e preparo", "kitchen"),
                ("🛏️ QUARTO", "espaço pessoal", "bedroom"),
            )
        ):
            card = tk.Frame(rooms, bg=self.panel, width=210, height=160)
            card.grid(row=0, column=col, padx=12)
            card.grid_propagate(False)
            tk.Label(
                card,
                text=title,
                fg=self.star,
                bg=self.panel,
                font=("Segoe UI", 14, "bold"),
            ).pack(pady=(24, 7))
            tk.Label(
                card,
                text=subtitle,
                fg=self.muted,
                bg=self.panel,
            ).pack()
            self._button(
                card,
                "IR →",
                lambda r=route: self.navigate(r),
                small=True,
                accent=True,
            ).pack(pady=18)

        self._place_star(stage, relx=0.84, rely=0.78, size=(170, 210))

    def show_living_room(self):
        self.clear_screen()
        self.nav.current = "living_room"
        self.current_screen = "living_room"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root, "CASA • SALA")
        self._scene_title(
            root,
            "📺 SALA",
            "Entretenimento, mídia e um lugar tranquilo para conversar com a STAR.",
        )

        stage = tk.Frame(root, bg=self.bg)
        stage.pack(fill="both", expand=True, padx=42, pady=16)

        tv = tk.Frame(stage, bg="#070a0e", width=430, height=245)
        tv.place(relx=0.27, rely=0.43, anchor="center")
        tv.pack_propagate(False)
        self.tv_frame = tv

        tk.Label(
            tv,
            text="STAR TV",
            fg=self.star,
            bg="#070a0e",
            font=("Segoe UI", 22, "bold"),
        ).pack(pady=(24, 5))

        self.tv_status_label = tk.Label(
            tv,
            text="Mídia pronta • WebView sob demanda",
            fg=self.muted,
            bg="#070a0e",
            font=("Segoe UI", 9),
        )
        self.tv_status_label.pack(pady=(0, 10))

        controls = tk.Frame(tv, bg="#070a0e")
        controls.pack(pady=(4, 0))
        self._button(
            controls,
            "YOUTUBE",
            self._open_youtube_tv,
            small=True,
            accent=True,
        ).pack(side="left", padx=3)
        self._button(
            controls,
            "⛶",
            self._tv_fullscreen,
            small=True,
        ).pack(side="left", padx=3)
        self._button(
            controls,
            "RESTAURAR",
            self._tv_restore,
            small=True,
        ).pack(side="left", padx=3)
        self._button(
            controls,
            "FECHAR",
            self._tv_close,
            small=True,
        ).pack(side="left", padx=3)

        sofa = tk.Frame(stage, bg=self.panel, width=420, height=115)
        sofa.place(relx=0.29, rely=0.78, anchor="center")
        sofa.pack_propagate(False)
        tk.Label(
            sofa,
            text="☕ MODO CONVERSA",
            fg=self.pink,
            bg=self.panel,
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(20, 5))
        self._button(
            sofa,
            "CONVERSAR COM A STAR",
            self.toggle_chat_panel,
            small=True,
        ).pack()

        self._place_star(stage, relx=0.73, rely=0.55, size=(230, 285))

    def _tv_rect(self):
        frame = self.tv_frame
        if frame is None:
            return None
        try:
            if not frame.winfo_exists():
                return None
            self.window.update_idletasks()
            return (
                frame.winfo_rootx(),
                frame.winfo_rooty(),
                max(320, frame.winfo_width()),
                max(180, frame.winfo_height()),
            )
        except tk.TclError:
            return None

    def _set_tv_status(self, text, ok=True):
        label = self.tv_status_label
        if label is not None:
            try:
                if label.winfo_exists():
                    label.config(
                        text=str(text),
                        fg=self.green if ok else self.red,
                    )
            except tk.TclError:
                self.tv_status_label = None

    def _open_youtube_tv(self):
        if not self.online_mode:
            self._set_tv_status("Ative o modo ONLINE para usar o YouTube.", False)
            return

        rect = self._tv_rect()
        if not rect:
            self._set_tv_status("A área da TV ainda não está pronta.", False)
            return

        if self.media.open_youtube(rect=rect):
            self._set_tv_status("YouTube carregado na STAR TV.")
            self.window.after(600, self._refresh_media_status)
        else:
            state = self.media.state()
            error = state.get("last_error") or "backend WebView indisponível"
            self._set_tv_status(f"TV indisponível: {error}", False)

    def _schedule_media_sync(self, _event=None):
        if self._media_sync_job is not None:
            try:
                self.window.after_cancel(self._media_sync_job)
            except tk.TclError as exc:
                log.debug("Operação Tk ignorada após destruição de widget: %s", exc)
        self._media_sync_job = self.window.after(90, self._sync_media_to_tv)

    def _sync_media_to_tv(self):
        self._media_sync_job = None
        try:
            state = self.media.state()
        except Exception as exc:
            log.warning("Falha ao ler estado da mídia: %s", exc)
            return
        if not state.get("opened") or state.get("fullscreen"):
            return
        if self.nav.current != "living_room":
            return
        rect = self._tv_rect()
        if rect:
            self.media.sync_rect(rect)

    def _refresh_media_status(self):
        state = self.media.state()
        if not state.get("opened"):
            error = state.get("last_error")
            if error:
                self._set_tv_status(f"TV indisponível: {error}", False)
            return
        self._set_tv_status(
            "YouTube • tela cheia"
            if state.get("fullscreen")
            else "YouTube • exibindo na STAR TV"
        )

    def _tv_fullscreen(self):
        if self.media.fullscreen():
            self._set_tv_status("YouTube • tela cheia")
        else:
            self._refresh_media_status()

    def _tv_restore(self):
        if self.media.restore():
            self.window.after(80, self._sync_media_to_tv)
            self._set_tv_status("YouTube • exibindo na STAR TV")
        else:
            self._refresh_media_status()

    def _tv_close(self):
        self.media.close()
        self._set_tv_status("Mídia pronta • WebView sob demanda")

    def _close_media_if_open(self):
        try:
            if self.media.state().get("opened"):
                self.media.close()
        except Exception as exc:
            log.warning("Falha ao fechar mídia: %s", exc)
        if self._media_sync_job is not None:
            try:
                self.window.after_cancel(self._media_sync_job)
            except tk.TclError as exc:
                log.debug("Operação Tk ignorada após destruição de widget: %s", exc)
            self._media_sync_job = None
        self.tv_frame = None
        self.tv_status_label = None

    def show_kitchen(self):
        self.clear_screen()
        self.nav.current = "kitchen"
        self.current_screen = "kitchen"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root, "CASA • COZINHA")
        self._scene_title(
            root,
            "🍳 COZINHA",
            "Receitas, preparo e experimentação gastronômica.",
        )

        stage = tk.Frame(root, bg=self.bg)
        stage.pack(fill="both", expand=True, padx=42, pady=16)

        bench = tk.Frame(stage, bg=self.panel, width=560, height=190)
        bench.place(relx=0.36, rely=0.64, anchor="center")
        bench.pack_propagate(False)
        tk.Label(
            bench,
            text="BANCADA",
            fg=self.muted,
            bg=self.panel,
            font=("Segoe UI", 10, "bold"),
        ).pack(pady=(25, 8))
        tk.Label(
            bench,
            text="🥕   🥛   🥚   🍞   🧂",
            fg=self.text,
            bg=self.panel,
            font=("Segoe UI Emoji", 25),
        ).pack()

        book = tk.Frame(stage, bg="#6e4b3c", width=210, height=150)
        book.place(relx=0.22, rely=0.32, anchor="center")
        book.pack_propagate(False)
        tk.Label(
            book,
            text="📖\nLIVRO DE RECEITAS",
            fg="#fff3da",
            bg="#6e4b3c",
            font=("Segoe UI", 13, "bold"),
        ).pack(expand=True)
        self._button(
            book,
            "ABRIR",
            self._open_recipe_book,
            small=True,
        ).pack(pady=(0, 12))

        self._place_star(stage, relx=0.76, rely=0.52, size=(230, 285))

    def _open_recipe_book(self):
        popup = tk.Toplevel(self.window)
        popup.title("STAR • Livro de Receitas")
        popup.geometry("620x480")
        popup.configure(bg=self.bg)
        popup.transient(self.window)

        tk.Label(
            popup,
            text="📖 LIVRO DE RECEITAS",
            fg=self.star,
            bg=self.bg,
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w", padx=24, pady=(24, 6))
        tk.Label(
            popup,
            text="A cozinha já possui a interface do livro. O acervo local de receitas será conectado aqui.",
            fg=self.muted,
            bg=self.bg,
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=24, pady=(0, 16))

        recipes_dir = PROJECT_ROOT / "knowledge" / "recipes"
        files = []
        if recipes_dir.exists():
            files = sorted(
                p for p in recipes_dir.rglob("*")
                if p.is_file() and p.suffix.lower() in {".txt", ".md", ".json"}
            )
        box = tk.Frame(popup, bg=self.panel, padx=18, pady=16)
        box.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        if not files:
            tk.Label(
                box,
                text="Nenhuma receita local cadastrada ainda.",
                fg=self.gold,
                bg=self.panel,
            ).pack(anchor="w")
        else:
            for path in files[:30]:
                tk.Label(
                    box,
                    text=f"• {path.stem.replace('_', ' ').title()}",
                    fg=self.text,
                    bg=self.panel,
                ).pack(anchor="w", pady=2)

    def show_bedroom(self):
        self.clear_screen()
        self.nav.current = "bedroom"
        self.current_screen = "bedroom"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root, "CASA • QUARTO")
        self._scene_title(
            root,
            "🛏️ QUARTO",
            "O espaço pessoal da STAR, com acesso ao Closet.",
        )

        stage = tk.Frame(root, bg=self.bg)
        stage.pack(fill="both", expand=True, padx=42, pady=16)

        bed = tk.Frame(stage, bg=self.panel, width=420, height=150)
        bed.place(relx=0.28, rely=0.69, anchor="center")
        bed.pack_propagate(False)
        tk.Label(
            bed,
            text="🛏️  ESPAÇO PESSOAL",
            fg=self.text,
            bg=self.panel,
            font=("Segoe UI", 13, "bold"),
        ).pack(expand=True)

        closet = tk.Frame(stage, bg="#1c2937", width=230, height=235)
        closet.place(relx=0.23, rely=0.33, anchor="center")
        closet.pack_propagate(False)
        tk.Label(
            closet,
            text="👕\nCLOSET",
            fg=self.star,
            bg="#1c2937",
            font=("Segoe UI", 16, "bold"),
        ).pack(expand=True)
        self._button(
            closet,
            "ENTRAR",
            lambda: self.navigate("closet"),
            small=True,
            accent=True,
        ).pack(pady=(0, 18))

        self._place_star(stage, relx=0.78, rely=0.54, size=(230, 285))

    # ------------------------------------------------------------------
    # Closet e álbum
    # ------------------------------------------------------------------

    def show_closet(self):
        self.clear_screen()
        self.nav.current = "closet"
        self.current_screen = "closet"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root, "CASA • QUARTO • CLOSET")
        self._scene_title(
            root,
            "👕 CLOSET",
            "Skins e aparências da STAR. O sistema existente foi preservado.",
        )

        body = tk.Frame(root, bg=self.bg)
        body.pack(fill="both", expand=True)

        self.closet_files = [
            p
            for p in sorted((PROJECT_ROOT / "SKINS").glob("*"))
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ]
        if not self.closet_files:
            tk.Label(
                body,
                text="Nenhuma skin encontrada.",
                fg=self.red,
                bg=self.bg,
            ).pack(pady=80)
            return

        try:
            self.closet_index = [p.name for p in self.closet_files].index(
                self.selected_skin
            )
        except ValueError:
            self.closet_index = 0

        area = tk.Frame(body, bg=self.bg)
        area.pack(fill="both", expand=True)
        self._button(area, "◀", lambda: self._change_closet_skin(-1)).place(
            relx=0.16, rely=0.5, anchor="center"
        )
        self._button(area, "▶", lambda: self._change_closet_skin(1)).place(
            relx=0.84, rely=0.5, anchor="center"
        )

        card = tk.Frame(area, bg=self.panel_2, padx=18, pady=16)
        card.place(relx=0.5, rely=0.46, anchor="center", width=430, height=450)
        self.closet_image = tk.Label(card, bg=self.panel_2)
        self.closet_image.pack(expand=True, fill="both")
        self.closet_name = tk.Label(
            card,
            fg=self.text,
            bg=self.panel_2,
            font=("Segoe UI", 14, "bold"),
        )
        self.closet_name.pack(pady=(8, 4))
        self.closet_state = tk.Label(
            card,
            fg=self.green,
            bg=self.panel_2,
            font=("Segoe UI", 9, "bold"),
        )
        self.closet_state.pack()

        self.closet_photo = None
        bottom = tk.Frame(body, bg=self.bg)
        bottom.pack(fill="x", padx=45, pady=(0, 22))
        self.select_skin_button = self._button(
            bottom,
            "SELECIONAR ESTA SKIN",
            self._confirm_closet_skin,
            accent=True,
        )
        self.select_skin_button.pack(side="left", padx=(0, 10))
        self._button(
            bottom,
            "📸 ABRIR ÁLBUM",
            lambda: self.navigate("gallery"),
        ).pack(side="left")

        self._render_closet_skin()

    def _change_closet_skin(self, step):
        self.closet_index = (self.closet_index + step) % len(self.closet_files)
        self._render_closet_skin()

    def _render_closet_skin(self):
        path = self.closet_files[self.closet_index]
        try:
            image = Image.open(path).convert("RGBA")
            image.thumbnail((360, 330), Image.Resampling.LANCZOS)
            self.closet_photo = ImageTk.PhotoImage(image)
            self.closet_image.config(image=self.closet_photo, text="")
        except (OSError, ValueError, tk.TclError) as exc:
            log.warning("Não foi possível abrir skin %s: %s", path, exc)
            self.closet_image.config(
                image="",
                text="Não foi possível abrir esta skin",
                fg=self.red,
            )
        self.closet_name.config(text=path.stem.replace("_", " ").title())
        active = path.name == self.selected_skin
        self.closet_state.config(
            text=(
                "✓ SKIN ATUALMENTE SELECIONADA"
                if active
                else f"{self.closet_index + 1} de {len(self.closet_files)}"
            )
        )
        self.select_skin_button.config(
            text="SKIN SELECIONADA" if active else "SELECIONAR ESTA SKIN",
            bg="#1f5a3a" if active else "#315575",
        )

    def _confirm_closet_skin(self):
        self.selected_skin = self.closet_files[self.closet_index].name
        self._save_skin_selection()
        self._render_closet_skin()

    def show_gallery(self):
        self.clear_screen()
        self.nav.current = "gallery"
        self.current_screen = "gallery"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root, "CASA • ÁLBUM")
        self._scene_title(
            root,
            "📸 ÁLBUM DA STAR",
            "Galeria local. Imagens privadas permanecem no computador do usuário.",
        )

        body = tk.Frame(root, bg=self.bg)
        body.pack(fill="both", expand=True, padx=42, pady=14)

        configured = self._read_user_settings().get("photo_library")
        candidates = []
        if configured:
            folder = Path(str(configured)).expanduser()
            if folder.exists():
                candidates.append(folder)
        candidates.append(PROJECT_ROOT / "assets" / "images")

        images = []
        for folder in candidates:
            if not folder.exists():
                continue
            images.extend(
                p
                for p in folder.rglob("*")
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
            )
        images = sorted(dict.fromkeys(images))

        if not images:
            empty = tk.Frame(body, bg=self.panel, padx=24, pady=22)
            empty.pack(fill="x")
            tk.Label(
                empty,
                text="Nenhuma imagem encontrada no álbum local.",
                fg=self.gold,
                bg=self.panel,
                font=("Segoe UI", 12, "bold"),
            ).pack(anchor="w")
            tk.Label(
                empty,
                text=(
                    "Por padrão a STAR procura em assets/images. "
                    "Também é possível definir 'photo_library' em user_settings.json."
                ),
                fg=self.muted,
                bg=self.panel,
                wraplength=760,
                justify="left",
            ).pack(anchor="w", pady=(6, 0))
            return

        canvas = tk.Canvas(body, bg=self.bg, highlightthickness=0)
        scroll = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
        grid = tk.Frame(canvas, bg=self.bg)
        grid.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=grid, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.gallery_photos = []
        for idx, path in enumerate(images[:100]):
            card = tk.Frame(grid, bg=self.panel, padx=8, pady=8)
            card.grid(row=idx // 5, column=idx % 5, padx=5, pady=5, sticky="nsew")
            try:
                image = Image.open(path).convert("RGB")
                image.thumbnail((150, 110), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.gallery_photos.append(photo)
                tk.Label(card, image=photo, bg=self.panel).pack()
            except (OSError, ValueError, tk.TclError) as exc:
                log.debug("Thumbnail indisponível para %s: %s", path, exc)
                tk.Label(
                    card,
                    text="📷",
                    fg=self.star,
                    bg=self.panel,
                    font=("Segoe UI Emoji", 26),
                ).pack()
            tk.Label(
                card,
                text=path.stem[:24],
                fg=self.text,
                bg=self.panel,
                font=("Segoe UI", 8),
            ).pack(pady=(5, 0))

    # ------------------------------------------------------------------
    # Chat global contextual
    # ------------------------------------------------------------------

    def toggle_chat_panel(self):
        if self.nav.current == "menu":
            return
        if self.nav.current == "chat":
            self.nav.close_overlay("hub")
            self._render_current()
            return
        if self.chat_panel is not None:
            self._close_chat_panel()
            return
        self._build_chat_panel()

    def _build_chat_panel(self):
        if self.chat_panel is not None:
            return

        panel = tk.Frame(
            self.window,
            bg="#101923",
            highlightbackground="#38516f",
            highlightthickness=1,
        )
        panel.place(relx=1.0, rely=0.0, anchor="ne", relwidth=0.36, relheight=1.0)
        panel.lift()
        self.chat_panel = panel

        top = tk.Frame(panel, bg=self.panel_2, height=58)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(
            top,
            text="💬 STAR",
            fg=self.star,
            bg=self.panel_2,
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left", padx=14)
        self._button(top, "⛶", self.open_expanded_chat, small=True).pack(
            side="right", padx=(3, 6), pady=9
        )
        self._button(top, "×", self._close_chat_panel, small=True).pack(
            side="right", padx=3, pady=9
        )

        context = self.nav.context or "STAR"
        self.chat_context_label = tk.Label(
            panel,
            text=f"📍 {context}",
            fg=self.muted,
            bg="#101923",
            font=("Segoe UI", 8, "bold"),
        )
        self.chat_context_label.pack(anchor="w", padx=14, pady=(10, 3))

        self.chat = scrolledtext.ScrolledText(
            panel,
            wrap=tk.WORD,
            bg="#0e151f",
            fg=self.text,
            insertbackground=self.text,
            relief=tk.FLAT,
            borderwidth=0,
            font=("Segoe UI", 10),
            padx=14,
            pady=12,
        )
        self.chat.pack(fill="both", expand=True, padx=10, pady=(4, 8))
        self._configure_chat_tags()
        self._restore_session_messages()

        self._build_chat_input(panel, compact=True)
        self.entry.focus_set()

    def _close_chat_panel(self):
        if self.chat_panel is not None:
            try:
                self.chat_panel.destroy()
            except tk.TclError as exc:
                log.debug("Operação Tk ignorada após destruição de widget: %s", exc)
        self.chat_panel = None
        self.chat = None
        self.entry = None
        self.mic = None
        self.send_button = None

    def open_expanded_chat(self):
        if self.nav.current != "chat":
            self.nav.open_overlay("chat")
        self._render_expanded_chat()

    def _render_expanded_chat(self):
        self.clear_screen()
        self.nav.current = "chat"
        self.current_screen = "chat"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root, "CONVERSA COM A STAR")

        context = self.nav.return_route
        context_text = ROUTES.get(context, ROUTES["hub"]).context if context else "STAR World"

        tk.Label(
            root,
            text=f"📍 Contexto: {context_text}",
            fg=self.muted,
            bg=self.bg,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=70, pady=(18, 5))

        self.chat = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            bg="#0e151f",
            fg=self.text,
            insertbackground=self.text,
            relief=tk.FLAT,
            borderwidth=0,
            font=("Segoe UI", 11),
            padx=28,
            pady=22,
        )
        self.chat.pack(fill="both", expand=True, padx=70, pady=(5, 10))
        self._configure_chat_tags()
        self._restore_session_messages()
        self._build_chat_input(root, compact=False)
        self.entry.focus_set()

    def show_chat(self):
        self.open_expanded_chat()

    def _build_chat_input(self, parent, compact=False):
        bottom = tk.Frame(parent, bg=self.bg if not compact else "#101923", height=80)
        bottom.pack(fill="x", side="bottom", padx=10 if compact else 22, pady=(0, 14))
        bottom.pack_propagate(False)

        box = tk.Frame(bottom, bg="#cbd9e8", padx=1, pady=1)
        box.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.96 if compact else 0.72, height=58)
        inner = tk.Frame(box, bg="#25364b")
        inner.pack(fill="both", expand=True)

        self.entry = tk.Entry(
            inner,
            bg="#25364b",
            fg="#aebdcd",
            insertbackground=self.text,
            relief=tk.FLAT,
            font=("Segoe UI", 10 if compact else 12),
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(12, 4), pady=7)
        self.entry.insert(0, "Fale com a STAR...")
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)
        self.entry.bind("<Return>", self._on_enter)

        self.mic = tk.Button(
            inner,
            text="🎤",
            command=self.toggle_microphone,
            bg="#25364b",
            fg="#d8e7f5",
            relief=tk.FLAT,
            borderwidth=0,
            font=("Segoe UI", 12),
            cursor="hand2",
        )
        self.mic.pack(side="right", padx=3)
        self.send_button = tk.Button(
            inner,
            text="➜",
            command=self.send_message,
            bg="#395574",
            fg="white",
            relief=tk.FLAT,
            borderwidth=0,
            font=("Segoe UI", 14, "bold"),
            width=3,
            cursor="hand2",
        )
        self.send_button.pack(side="right", padx=(2, 7), pady=7)

    def _configure_chat_tags(self):
        if not self.chat:
            return
        for tag, fg, font in (
            ("user", self.user, ("Segoe UI", 9, "bold")),
            ("star", self.star, ("Segoe UI", 9, "bold")),
            ("message", self.text, ("Segoe UI", 10)),
            ("system", self.muted, ("Segoe UI", 9)),
        ):
            self.chat.tag_configure(tag, foreground=fg, font=font)
        self.chat.configure(state=tk.DISABLED)

    def _restore_session_messages(self):
        if not self.chat:
            return
        for sender, text in self.session_messages:
            if sender == "Você":
                self._append("Você", text, "user", remember=False)
            elif sender == "STAR":
                self._append("⭐ STAR", text, "star", remember=False)
            else:
                self._append("SISTEMA", text, "system", remember=False)

    def _clear_placeholder(self, _event=None):
        if self.entry and self.entry.get() in {
            "Fale com a STAR...",
            "Pergunte algo à STAR...",
        }:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.text)

    def _restore_placeholder(self, _event=None):
        if self.entry and not self.entry.get().strip():
            self.entry.insert(0, "Fale com a STAR...")
            self.entry.config(fg="#aebdcd")

    def _on_enter(self, _event=None):
        self.send_message()
        return "break"

    def _context_for_brain(self):
        if self.nav.current == "chat" and self.nav.return_route:
            return ROUTES.get(self.nav.return_route, ROUTES["hub"]).context
        return self.nav.context

    def send_message(self):
        if self.processing or not self.entry:
            return
        self.voice.cancel_speech()
        text = self.entry.get().strip()
        if not text or text in {"Fale com a STAR...", "Pergunte algo à STAR..."}:
            return

        self.entry.delete(0, tk.END)
        self._append_user(text)
        try:
            self.memory.save("Você", text)
        except Exception as exc:
            log.warning("Falha ao persistir mensagem do usuário: %s", exc)

        context = self._context_for_brain()
        self.processing = True
        self.entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self._set_status("PROCESSANDO", self.gold)
        self._load_avatar("thinking")
        threading.Thread(
            target=self._process_message,
            args=(text, context),
            daemon=True,
        ).start()

    def _process_message(self, text, context):
        try:
            self.brain.ui_context = context
            self.response_queue.put(("success", self.brain.process(text)))
        except Exception as exc:
            self.response_queue.put(("error", str(exc)))

    def _append(self, name, text, tag, remember=True):
        if remember:
            sender = "STAR" if tag == "star" else "Você" if tag == "user" else "SISTEMA"
            self.session_messages.append((sender, str(text)))
        if not self.chat:
            return
        try:
            self.chat.configure(state=tk.NORMAL)
            self.chat.insert(tk.END, name + "\n", tag)
            self.chat.insert(tk.END, str(text) + "\n\n", "message")
            self.chat.configure(state=tk.DISABLED)
            self.chat.see(tk.END)
        except tk.TclError:
            self.chat = None

    def _append_user(self, text):
        self._append("Você", text, "user")

    def _append_star(self, text):
        self._append("⭐ STAR", text, "star")

    def _append_system(self, text):
        self._append("SISTEMA", text, "system")

    # ------------------------------------------------------------------
    # Voz e processamento
    # ------------------------------------------------------------------

    def toggle_microphone(self):
        self.voice.cancel_speech()
        if not self.voice.stt_configured:
            self._append_system(
                "🎤 Reconhecimento local ainda não está instalado. Execute INSTALAR_VOZ.bat."
            )
            return
        if not self.recorder.available:
            self._append_system(
                "🎤 Não consegui acessar o microfone. Verifique as configurações de áudio do Windows."
            )
            return

        if not self.recording:
            try:
                self.recorder.start()
                self.recording = True
                if self.mic:
                    self.mic.config(text="■", bg="#8b3340", fg="white")
                self._append_system("🎤 Estou ouvindo. Clique novamente quando terminar.")
                self._set_status("OUVINDO", self.green)
            except Exception as exc:
                self._append_system(f"🎤 Erro ao abrir microfone: {exc}")
        else:
            self.recording = False
            if self.mic:
                self.mic.config(text="🎤", bg="#25364b", fg="#d8e7f5")
            self._set_status("TRANSCRIVENDO", self.gold)
            threading.Thread(target=self._finish_recording, daemon=True).start()

    def _finish_recording(self):
        path = None
        try:
            path = self.recorder.stop_to_wav()
            text = self.voice.transcribe(path)
            self.response_queue.put(("transcript", text))
        except Exception as exc:
            self.response_queue.put(("voice_error", str(exc)))
        finally:
            if path:
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    log.debug("Não foi possível remover áudio temporário: %s", exc)

    def _chat_controls_available(self):
        return self.entry is not None and self.send_button is not None

    def _check_response_queue(self):
        if self._closing:
            return
        try:
            while True:
                kind, result = self.response_queue.get_nowait()

                if kind == "media_command":
                    self._handle_media_command(result)

                elif kind == "transcript":
                    if not self._chat_controls_available():
                        self._build_chat_panel()
                    if self.entry:
                        self.entry.config(state=tk.NORMAL)
                        self.entry.delete(0, tk.END)
                        self.entry.insert(0, str(result))
                        self.entry.config(fg=self.text)
                        self.send_message()

                elif kind == "voice_error":
                    if not self.chat and self.nav.current != "menu":
                        self._build_chat_panel()
                    self._append_system(f"🎤 Falha no reconhecimento: {result}")
                    self.processing = False
                    if self._chat_controls_available():
                        self.entry.config(state=tk.NORMAL)
                        self.send_button.config(state=tk.NORMAL)

                elif kind == "voice_test":
                    ok, error = result
                    self._set_voice_test_message(
                        (
                            f"🔊 Voz da STAR funcionando ({self.voice.last_tts_engine})."
                            if ok
                            else f"🔊 Falha na voz: {error}"
                        ),
                        ok,
                    )

                elif kind == "speech_result":
                    ok, error = result
                    if not ok and self.chat:
                        self._append_system(
                            f"🔊 A resposta foi gerada, mas a voz falhou: {error}"
                        )
                    self._load_avatar("neutral")
                    self._set_status(
                        "ONLINE" if self.online_mode else "OFFLINE",
                        self.green if self.online_mode else self.red,
                    )

                elif kind == "success":
                    response = str(result)
                    if not self.chat and self.nav.current != "menu":
                        self._build_chat_panel()
                    self._append_star(response)
                    try:
                        self.memory.save("STAR", response)
                    except Exception as exc:
                        log.warning("Falha ao persistir resposta da STAR: %s", exc)
                    self._load_avatar("speaking")
                    self.voice.speak_async(
                        response,
                        lambda ok, error: self.response_queue.put(
                            ("speech_result", (ok, error))
                        ),
                    )
                    self.processing = False
                    if self._chat_controls_available():
                        self.entry.config(state=tk.NORMAL)
                        self.send_button.config(state=tk.NORMAL)
                        self.entry.focus_set()
                    self._set_status("FALANDO", self.green)

                elif kind == "error":
                    if not self.chat and self.nav.current != "menu":
                        self._build_chat_panel()
                    self._append_system(f"Erro ao processar: {result}")
                    self._load_avatar("neutral")
                    self.processing = False
                    if self._chat_controls_available():
                        self.entry.config(state=tk.NORMAL)
                        self.send_button.config(state=tk.NORMAL)

        except queue.Empty:
            queue_drained = True  # fim esperado do lote atual

        if not self._closing:
            try:
                self.window.after(60, self._check_response_queue)
            except tk.TclError as exc:
                log.debug("Operação Tk ignorada após destruição de widget: %s", exc)

    # ------------------------------------------------------------------
    # Avatar
    # ------------------------------------------------------------------

    def _load_display_avatar(self, max_size=(300, 330)):
        if self.avatar_label is None:
            return
        skin = PROJECT_ROOT / "SKINS" / self.selected_skin
        if skin.exists():
            try:
                image = Image.open(skin).convert("RGBA")
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                self.avatar_photo = ImageTk.PhotoImage(image)
                self.avatar_label.config(image=self.avatar_photo, text="")
                return
            except (OSError, ValueError, tk.TclError) as exc:
                log.warning("Skin atual não pôde ser usada no avatar: %s", exc)
        self._load_avatar("neutral", max_size=max_size)

    def _load_avatar(self, emotion="neutral", max_size=(250, 250)):
        if self.avatar_label is None:
            return
        path = self.avatar.avatar_dir / f"{emotion}.png"
        if not path.exists() or path.stat().st_size == 0:
            path = self.avatar.avatar_dir / "neutral.png"
        try:
            image = Image.open(path).convert("RGBA")
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            self.avatar_photo = ImageTk.PhotoImage(image)
            self.avatar_label.config(image=self.avatar_photo, text="")
        except Exception:
            try:
                self.avatar_label.config(
                    text="⭐\nSTAR",
                    fg=self.star,
                    font=("Segoe UI", 26, "bold"),
                )
            except tk.TclError as exc:
                log.debug("Operação Tk ignorada após destruição de widget: %s", exc)

    # ------------------------------------------------------------------
    # Configurações
    # ------------------------------------------------------------------

    def _render_settings(self):
        self.clear_screen()
        self.nav.current = "settings"
        self.current_screen = "settings"

        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)

        header = tk.Frame(root, bg=self.panel_2, height=58)
        header.pack(fill="x")
        header.pack_propagate(False)
        self._button(header, "←", self.close_settings, small=True).pack(
            side="left", padx=(10, 4), pady=9
        )
        tk.Label(
            header,
            text="⚙ CONFIGURAÇÕES",
            fg=self.star,
            bg=self.panel_2,
            font=("Segoe UI", 17, "bold"),
        ).pack(side="left", padx=10)

        body = tk.Frame(root, bg=self.bg)
        body.pack(fill="both", expand=True, padx=80, pady=35)

        mode = tk.Frame(body, bg=self.panel, padx=22, pady=18)
        mode.pack(fill="x", pady=(0, 12))
        tk.Label(
            mode,
            text="MODO DE FUNCIONAMENTO",
            fg=self.text,
            bg=self.panel,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        row = tk.Frame(mode, bg=self.panel)
        row.pack(anchor="w", pady=12)
        self.online_btn = self._button(
            row, "🟢 ONLINE", lambda: self._set_mode(True)
        )
        self.online_btn.pack(side="left", padx=(0, 10))
        self.offline_btn = self._button(
            row, "🔴 OFFLINE", lambda: self._set_mode(False)
        )
        self.offline_btn.pack(side="left")
        self._refresh_mode_buttons()

        voicebox = tk.Frame(body, bg=self.panel, padx=22, pady=18)
        voicebox.pack(fill="x", pady=12)
        tk.Label(
            voicebox,
            text="🎙️ VOZ DA STAR",
            fg=self.star,
            bg=self.panel,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")
        tk.Label(
            voicebox,
            text=f"Entrada: faster-whisper tiny • Conversa: {self.voice.tts_description}",
            fg=self.text,
            bg=self.panel,
        ).pack(anchor="w", pady=(8, 6))

        voice_row = tk.Frame(voicebox, bg=self.panel)
        voice_row.pack(anchor="w", pady=(2, 8))
        self._button(
            voice_row,
            "⚡ CONVERSA RÁPIDA",
            lambda: self._set_voice_mode("fast"),
            small=True,
        ).pack(side="left", padx=(0, 8))
        self._button(
            voice_row,
            "⭐ VOZ OFICIAL",
            lambda: self._set_voice_mode("official"),
            small=True,
        ).pack(side="left")

        self._button(
            voicebox,
            "TESTAR VOZ OFICIAL",
            self._test_voice,
        ).pack(anchor="w", pady=(12, 4))
        self.voice_test_label = tk.Label(
            voicebox,
            text="Pronto para testar.",
            fg=self.muted,
            bg=self.panel,
            wraplength=760,
            justify="left",
        )
        self.voice_test_label.pack(anchor="w")

        info = tk.Frame(body, bg=self.panel, padx=22, pady=16)
        info.pack(fill="x", pady=12)
        for name, value in (
            ("Versão", f"V{VERSION}"),
            ("Conhecimento local", "ATIVO"),
            ("Modo de voz", self.voice.mode.upper()),
            ("Navegação contextual", "ATIVA"),
            ("Chat global", "ATIVO"),
        ):
            line = tk.Frame(info, bg=self.panel)
            line.pack(fill="x", pady=4)
            tk.Label(line, text=name, fg=self.muted, bg=self.panel).pack(side="left")
            tk.Label(
                line,
                text=value,
                fg=self.green if "ATIV" in value else self.gold,
                bg=self.panel,
                font=("Segoe UI", 10, "bold"),
            ).pack(side="right")

    def show_settings(self):
        self.open_settings()

    def _test_voice(self):
        self._set_voice_test_message(
            "🔊 Preparando teste da voz oficial...",
            True,
        )
        self._set_status("TESTANDO VOZ", self.gold)
        self.voice.test_official_audio_async(
            lambda ok, error: self.response_queue.put(
                ("voice_test", (ok, error))
            )
        )

    def _set_voice_test_message(self, message, ok):
        label = self.voice_test_label
        if label is not None:
            try:
                if label.winfo_exists():
                    label.config(
                        text=message,
                        fg=self.green if ok else self.red,
                    )
                    return
            except tk.TclError as exc:
                log.debug("Operação Tk ignorada após destruição de widget: %s", exc)
        if self.chat:
            self._append_system(message)

    def _set_voice_mode(self, mode):
        self.voice.set_voice_mode(mode)
        self._save_voice_mode()
        self._render_settings()

    def _set_mode(self, online):
        self.online_mode = bool(online)
        self.brain.network_enabled = self.online_mode
        self._refresh_mode_buttons()
        self._set_status(
            "ONLINE" if self.online_mode else "OFFLINE",
            self.green if self.online_mode else self.red,
        )

    def _refresh_mode_buttons(self):
        if hasattr(self, "online_btn"):
            self.online_btn.config(
                bg="#1f5a3a" if self.online_mode else "#24313f"
            )
        if hasattr(self, "offline_btn"):
            self.offline_btn.config(
                bg="#5a2630" if not self.online_mode else "#24313f"
            )

    def _set_status(self, text, color):
        label = self.status_label
        if label:
            try:
                label.config(text=f"● V{VERSION} • {text}", fg=color)
            except tk.TclError as exc:
                log.debug("Operação Tk ignorada após destruição de widget: %s", exc)

    # ------------------------------------------------------------------
    # Saída e janela
    # ------------------------------------------------------------------

    def request_exit(self):
        if self._closing or self._exit_overlay is not None:
            return

        overlay = tk.Frame(
            self.window,
            bg="#080c12",
            highlightbackground="#31475f",
            highlightthickness=2,
        )
        overlay.place(relx=0.5, rely=0.5, anchor="center", width=430, height=330)
        overlay.lift()
        self._exit_overlay = overlay

        sad_path = self.avatar.avatar_dir / "sad.png"
        photo = None
        if sad_path.exists() and sad_path.stat().st_size > 0:
            try:
                image = Image.open(sad_path).convert("RGBA")
                image.thumbnail((125, 125), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.exit_photo = photo
            except (OSError, ValueError, tk.TclError) as exc:
                log.warning("Avatar de saída indisponível: %s", exc)
                photo = None

        if photo:
            tk.Label(overlay, image=photo, bg="#080c12").pack(pady=(20, 5))
        else:
            tk.Label(
                overlay,
                text="⭐",
                fg=self.gold,
                bg="#080c12",
                font=("Segoe UI Emoji", 42),
            ).pack(pady=(25, 5))

        tk.Label(
            overlay,
            text="Você já vai?",
            fg=self.text,
            bg="#080c12",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(5, 18))

        row = tk.Frame(overlay, bg="#080c12")
        row.pack()
        self._button(row, "SIM", self._confirm_exit).pack(side="left", padx=6)
        self._button(row, "NÃO", self._cancel_exit, accent=True).pack(
            side="left", padx=6
        )

    def _cancel_exit(self):
        if self._exit_overlay is not None:
            try:
                self._exit_overlay.destroy()
            except tk.TclError as exc:
                log.debug("Operação Tk ignorada após destruição de widget: %s", exc)
        self._exit_overlay = None
        try:
            self.emotion.set_emotion("happy")
        except Exception as exc:
            log.debug("Não foi possível atualizar emoção após cancelar saída: %s", exc)

    def _confirm_exit(self):
        if self._exit_overlay is not None:
            for child in self._exit_overlay.winfo_children():
                try:
                    child.destroy()
                except tk.TclError as exc:
                    log.debug("Widget de saída já destruído: %s", exc)
            tk.Label(
                self._exit_overlay,
                text="⭐\n\nOk...",
                fg=self.muted,
                bg="#080c12",
                font=("Segoe UI", 16, "bold"),
            ).pack(expand=True)
            self.window.after(450, self.close)
        else:
            self.close()

    def toggle_maximize(self, _event=None):
        if self.is_maximized:
            self.restore_normal_size()
        else:
            self.normal_size = (
                self.window.winfo_width(),
                self.window.winfo_height(),
            )
            self.window.state("zoomed")
            self.is_maximized = True

    def restore_normal_size(self, _event=None):
        if self.is_maximized:
            self.window.state("normal")
            self.window.geometry(
                f"{max(900, self.normal_size[0])}x{max(600, self.normal_size[1])}"
            )
            self.is_maximized = False

    def close(self):
        if self._closing:
            return
        self._closing = True
        try:
            self.media.close()
        except Exception as exc:
            log.warning("Falha ao encerrar mídia: %s", exc)
        try:
            if self.recording:
                self.recorder.stop_to_wav()
        except Exception as exc:
            log.warning("Falha ao finalizar gravação durante saída: %s", exc)
        try:
            self.voice.close()
        except Exception as exc:
            log.warning("Falha ao encerrar voz: %s", exc)
        try:
            self.memory.close()
        finally:
            try:
                self.window.destroy()
            except tk.TclError as exc:
                log.debug("Janela já estava destruída no encerramento: %s", exc)

    def run(self):
        self.window.mainloop()
