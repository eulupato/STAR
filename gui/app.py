"""Interface 2D da STAR reconstruída a partir do protótipo visual do STAR OS.

A GUI continua local-first e preserva o Core Python, memória, voz e Knowledge
Packs existentes. O visual foi refeito sem dependência do Base44.
"""
from __future__ import annotations

import json
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageOps, ImageTk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import APP_NAME, VERSION, WINDOW_HEIGHT, WINDOW_WIDTH, VOICE_CHAT_MODE
from core.avatar import AvatarManager
from core.emotion import EmotionManager
from database.memory import Memory
from gui.theme import (
    BG, BG_ALT, PANEL, PANEL_2, PANEL_3, BORDER, TEXT, MUTED, SOFT,
    BLUE, BLUE_SOFT, PINK, GOLD, GREEN, RED, WHITE,
    BODY_FONT, BODY_BOLD, SMALL_FONT, SMALL_BOLD,
    draw_starfield, round_rect,
)
from voice.audio_input import AudioRecorder
from voice.manager import VoiceManager


class StarApp:
    """Janela principal da STAR.

    A navegação oficial desta UI é Menu -> HUB/STAR WORLD. O chat é acessível
    pelo HUB e, dentro dele, o botão de ilha retorna ao HUB sem perder a conversa.
    """

    SETTINGS_SECTIONS = (
        ("general", "⚙", "GERAL"),
        ("appearance", "◉", "APARÊNCIA"),
        ("voice", "🎙", "VOZ"),
        ("audio", "◖", "ÁUDIO"),
        ("models", "▣", "MODELOS"),
        ("memory", "♧", "MEMÓRIA"),
        ("knowledge", "▤", "CONHECIMENTO"),
        ("privacy", "◇", "PRIVACIDADE"),
        ("permissions", "⌕", "PERMISSÕES"),
        ("world", "◎", "STAR WORLD"),
        ("about", "ⓘ", "SOBRE A STAR"),
    )

    MENU_EMOTIONS = {
        "iniciar": "happy",
        "configuracoes": "thinking",
        "sair": "sad",
    }

    ISLAND_POSITIONS = [
        (.38, .28), (.55, .17), (.71, .28),
        (.30, .53), (.55, .55), (.78, .53),
        (.42, .75), (.66, .75), (.84, .73),
        (.18, .72), (.90, .36),
    ]

    ISLAND_COLORS = {
        "casa": ("#eef8ff", "#8fd0ff"),
        "laboratorio": ("#edf7ff", "#8fd0ff"),
        "biblioteca": ("#ffe891", "#ffd36e"),
        "estudio_musica": ("#ffb7d8", "#f39bc2"),
        "jardim": ("#a6deb1", "#75d99c"),
        "correio": ("#ffdc85", "#ffd36e"),
        "cura": ("#d8edff", "#8fd0ff"),
        "herois": ("#f3d1ff", "#cbb5ff"),
        "idiomas": ("#a7ddff", "#5aa6ff"),
        "atelie": ("#ffd5a8", "#ffb87a"),
    }

    def __init__(self, brain):
        self.brain = brain
        self.memory = Memory()
        self.avatar = AvatarManager()
        self.emotion = EmotionManager()
        self.voice = VoiceManager()
        self.voice.set_voice_mode(self._load_voice_mode())
        self.recorder = AudioRecorder()

        self.operation_mode = self._load_operation_mode()
        self.online_mode = self.operation_mode == "online"
        self.processing = False
        self.recording = False
        self._closing = False
        self.response_queue: queue.Queue = queue.Queue()
        self.current_screen = "menu"
        self.selected_skin = self._load_skin_selection()
        self.chat_history = self._load_chat_history()

        self.photo_cache: dict[str, ImageTk.PhotoImage] = {}
        self.menu_emotion = "neutral"
        self.hovered_island = None
        self.is_maximized = False
        self.normal_size = (WINDOW_WIDTH, WINDOW_HEIGHT)

        self.entry = None
        self.send_button = None
        self.mic_button = None
        self.status_label = None
        self.voice_test_label = None
        self.chat_scroll_canvas = None
        self.chat_messages_frame = None
        self.menu_canvas = None
        self.menu_eye_items = []
        self.menu_hero_box = None

        self.window = tk.Tk()
        self.window.title(f"{APP_NAME} V{VERSION}")
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.window.minsize(960, 620)
        self.window.configure(bg=BG)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<F11>", self.toggle_maximize)
        self.window.bind("<Escape>", self.restore_normal_size)

        self.show_menu()
        self.window.after(60, self._check_response_queue)
        self.voice.warmup_stt_async()

    @property
    def _user_settings_path(self):
        return PROJECT_ROOT / "user_settings.json"

    def _read_user_settings(self):
        try:
            return json.loads(self._user_settings_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_user_settings(self, **values):
        try:
            data = self._read_user_settings()
            data.update(values)
            self._user_settings_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def _load_voice_mode(self):
        mode = str(self._read_user_settings().get("voice_mode", VOICE_CHAT_MODE)).lower()
        return mode if mode in {"official", "fast"} else VOICE_CHAT_MODE

    def _load_operation_mode(self):
        mode = str(self._read_user_settings().get("operation_mode", "local")).lower()
        return mode if mode in {"local", "lan", "online"} else "local"

    def _load_skin_selection(self):
        local = self._read_user_settings().get("skin")
        if local:
            return str(local)
        try:
            data = json.loads((PROJECT_ROOT / "config_skin.json").read_text(encoding="utf-8"))
            return data.get("skin", "original.jpeg")
        except Exception:
            return "original.jpeg"

    def _save_skin_selection(self):
        self._write_user_settings(skin=self.selected_skin)

    def _save_voice_mode(self):
        self._write_user_settings(voice_mode=self.voice.mode)

    def _save_operation_mode(self):
        self._write_user_settings(operation_mode=self.operation_mode)

    def _load_chat_history(self):
        try:
            rows = self.memory.load()
            result = []
            for row in rows[-80:]:
                sender = str(getattr(row, "sender", ""))
                content = str(getattr(row, "content", ""))
                if content:
                    result.append((sender, content))
            return result
        except Exception:
            return []

    def clear_screen(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        self.entry = None
        self.send_button = None
        self.mic_button = None
        self.status_label = None
        self.voice_test_label = None
        self.chat_scroll_canvas = None
        self.chat_messages_frame = None
        self.menu_canvas = None
        self.menu_eye_items = []
        self.menu_hero_box = None

    def _photo(self, path: Path, size: tuple[int, int], *, fit=True, key=None):
        path = Path(path)
        cache_key = key or f"{path}:{size}:{fit}"
        if cache_key in self.photo_cache:
            return self.photo_cache[cache_key]
        if not path.exists() or path.stat().st_size == 0:
            return None
        try:
            image = Image.open(path).convert("RGBA")
            if fit:
                image = ImageOps.fit(image, size, Image.Resampling.LANCZOS, centering=(.5, .42))
            else:
                image.thumbnail(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.photo_cache[cache_key] = photo
            return photo
        except Exception:
            return None

    def _avatar_path(self, emotion="neutral"):
        path = PROJECT_ROOT / "assets" / "avatar" / f"{emotion}.png"
        if path.exists() and path.stat().st_size > 0:
            return path
        return PROJECT_ROOT / "assets" / "avatar" / "neutral.png"

    def _reference_path(self, name):
        return PROJECT_ROOT / "assets" / "reference" / name

    def _button(self, parent, text, command, *, accent=False, subtle=False, width=None):
        bg = BLUE if accent else (BG_ALT if subtle else PANEL_3)
        active = "#70b4ff" if accent else "#293650"
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=WHITE if accent else TEXT,
            activebackground=active,
            activeforeground=WHITE,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            font=BODY_BOLD,
            padx=16,
            pady=8,
            width=width,
        )

    def _pill(self, parent, text, *, fg=BLUE, bg=PANEL, font=SMALL_BOLD):
        return tk.Label(parent, text=text, fg=fg, bg=bg, font=font, padx=12, pady=5)

    def _status_text(self):
        if self.processing:
            return "THINKING"
        if self.recording:
            return "LISTENING"
        return self.operation_mode.upper()

    def show_menu(self):
        self.clear_screen()
        self.current_screen = "menu"
        self.menu_emotion = "neutral"
        canvas = tk.Canvas(self.window, bg=BG, highlightthickness=0, cursor="arrow")
        canvas.pack(fill="both", expand=True)
        self.menu_canvas = canvas
        canvas.bind("<Configure>", self._render_menu)
        canvas.bind("<Motion>", self._menu_track_eyes)
        self.window.after(20, self._render_menu)

    def _render_menu(self, _event=None):
        canvas = self.menu_canvas
        if canvas is None or not canvas.winfo_exists():
            return
        w = max(canvas.winfo_width(), 960)
        h = max(canvas.winfo_height(), 620)
        canvas.delete("all")
        draw_starfield(canvas, w, h, seed=16)

        canvas.create_text(32, 30, text="STAR", fill=TEXT, anchor="nw", font=("Courier New", 22, "bold"))
        canvas.create_text(32, 62, text=f"S.T.A.R. OS · V{VERSION}", fill=SOFT, anchor="nw", font=("Courier New", 7, "bold"))

        box_w = min(390, int(w * .31))
        box_h = min(330, int(h * .50))
        x1 = max(54, int(w * .06))
        y1 = h - box_h + 34
        self.menu_hero_box = (x1, y1, box_w, box_h)
        round_rect(canvas, x1 - 2, y1 - 2, x1 + box_w + 2, y1 + box_h + 2,
                   radius=26, fill="#132033", outline="#29405f", width=1, tags="menu_fg")

        if self.menu_emotion == "neutral":
            hero = self._photo(self._reference_path("star_menu_face.jpg"), (box_w, box_h), fit=True,
                               key=f"menu-neutral-{box_w}-{box_h}")
        else:
            hero = self._photo(self._avatar_path(self.menu_emotion), (box_w, box_h), fit=True,
                               key=f"menu-{self.menu_emotion}-{box_w}-{box_h}")
        if hero:
            canvas.create_image(x1, y1, image=hero, anchor="nw", tags="menu_fg")
        else:
            canvas.create_text(x1 + box_w/2, y1 + box_h/2, text="STAR", fill=BLUE_SOFT,
                               font=("Courier New", 28, "bold"), tags="menu_fg")

        self.menu_eye_items = []
        eye_y = y1 + box_h * .46
        for ex in (x1 + box_w * .39, x1 + box_w * .62):
            item = canvas.create_oval(ex - 3, eye_y - 3, ex + 3, eye_y + 3,
                                      fill="#13223c", outline="#bfdcff", width=1, tags="menu_eyes")
            self.menu_eye_items.append(item)

        menu_x = w * .86
        start_y = h * .50
        options = [
            ("iniciar", "◆  INICIAR"),
            ("configuracoes", "◆  CONFIGURAÇÕES"),
            ("sair", "◆  SAIR"),
        ]
        for idx, (action, label) in enumerate(options):
            y = start_y + idx * 75
            tag = f"menu_{action}"
            color = TEXT if self.menu_emotion == self.MENU_EMOTIONS[action] else "#9296a6"
            canvas.create_text(menu_x, y, text=label, fill=color, anchor="center",
                               font=("Courier New", 12, "bold"), tags=(tag, "menu_option"))
            canvas.tag_bind(tag, "<Enter>", lambda e, a=action: self._menu_hover(a))
            canvas.tag_bind(tag, "<Leave>", lambda e: self._menu_leave())
            canvas.tag_bind(tag, "<Button-1>", lambda e, a=action: self._menu_click(a))

        status = self._status_text()
        sx, sy = w - 112, h - 48
        round_rect(canvas, sx - 74, sy - 13, sx + 74, sy + 13, radius=13,
                   fill="#0c1422", outline=BORDER, width=1, tags="menu_fg")
        canvas.create_oval(sx - 57, sy - 3, sx - 51, sy + 3, fill=BLUE, outline="", tags="menu_fg")
        canvas.create_text(sx - 43, sy, text=status, anchor="w", fill=BLUE,
                           font=("Courier New", 7, "bold"), tags="menu_fg")

    def _menu_hover(self, action):
        self.menu_emotion = self.MENU_EMOTIONS.get(action, "neutral")
        try:
            self.emotion.set_emotion(self.menu_emotion)
        except Exception:
            pass
        self._render_menu()

    def _menu_leave(self):
        self.menu_emotion = "neutral"
        try:
            self.emotion.reset()
        except Exception:
            pass
        self._render_menu()

    def _menu_click(self, action):
        self.menu_emotion = self.MENU_EMOTIONS.get(action, "neutral")
        self._render_menu()
        if action == "iniciar":
            self.window.after(220, self.show_hub)
        elif action == "configuracoes":
            self.window.after(220, lambda: self.show_settings("general"))
        elif action == "sair":
            self.window.after(260, self.close)

    def _menu_track_eyes(self, event):
        canvas = self.menu_canvas
        if not canvas or not self.menu_hero_box or len(self.menu_eye_items) != 2:
            return
        x1, y1, bw, bh = self.menu_hero_box
        cx, cy = x1 + bw * .5, y1 + bh * .45
        dx = max(-4.0, min(4.0, (event.x - cx) / max(1, self.window.winfo_width()) * 15))
        dy = max(-3.0, min(3.0, (event.y - cy) / max(1, self.window.winfo_height()) * 11))
        bases = ((x1 + bw * .39, y1 + bh * .46), (x1 + bw * .62, y1 + bh * .46))
        for item, (bx, by) in zip(self.menu_eye_items, bases):
            try:
                canvas.coords(item, bx - 3 + dx, by - 3 + dy, bx + 3 + dx, by + 3 + dy)
            except tk.TclError:
                return

    def show_hub(self):
        self.clear_screen()
        self.current_screen = "hub"
        self.hovered_island = None
        canvas = tk.Canvas(self.window, bg=BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        self.hub_canvas = canvas
        canvas.bind("<Configure>", self._render_hub)
        self.window.after(20, self._render_hub)

    show_islands = show_hub

    def _render_hub(self, _event=None):
        canvas = getattr(self, "hub_canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return
        w = max(canvas.winfo_width(), 960)
        h = max(canvas.winfo_height(), 620)
        canvas.delete("all")
        draw_starfield(canvas, w, h, seed=31, clouds=True)

        canvas.create_text(w/2, 28, text="STAR WORLD", fill=TEXT, font=("Courier New", 18, "bold"), anchor="n")
        canvas.create_text(w/2, 58, text="O MUNDO DA STAR", fill=SOFT, font=("Courier New", 7, "bold"), anchor="n")

        self._canvas_pill(canvas, 20, 20, 96, 38, "←  Menu", self.show_menu)
        self._canvas_pill(canvas, w - 194, 20, 90, 38, "👱  STAR", self.show_chat)
        self._canvas_pill(canvas, w - 94, 20, 76, 38, f"● {self._status_text()}", None, fg=BLUE)

        try:
            from core.islands import get_islands
            data = get_islands()
        except Exception:
            data = {}

        for idx, (key, item) in enumerate(data.items()):
            if idx >= len(self.ISLAND_POSITIONS):
                break
            rx, ry = self.ISLAND_POSITIONS[idx]
            x, y = int(w * rx), int(h * ry)
            hovered = key == self.hovered_island
            self._draw_island(canvas, key, item, x, y, hovered)

        hx, hy = w/2, h - 38
        round_rect(canvas, hx - 128, hy - 17, hx + 128, hy + 17, radius=17,
                   fill="#171b27", outline="#3a3f4d", width=1, tags="hub_ui")
        canvas.create_text(hx, hy, text="◎  SELECIONE UMA ILHA PARA EXPLORAR", fill="#8d8f99",
                           font=("Courier New", 7, "bold"), tags="hub_ui")
        self._canvas_pill(canvas, w - 118, h - 72, 96, 52, "◯  CHAT", self.show_chat, fg=TEXT, fill="#111625")

    def _canvas_pill(self, canvas, x, y, width, height, text, command, *, fg=TEXT, fill="#101827"):
        tag = f"pill_{id(command)}_{x}_{y}"
        round_rect(canvas, x, y, x + width, y + height, radius=height/2,
                   fill=fill, outline=BORDER, width=1, tags=(tag, "hub_ui"))
        canvas.create_text(x + width/2, y + height/2, text=text, fill=fg,
                           font=BODY_BOLD, tags=(tag, "hub_ui"))
        if command:
            canvas.tag_bind(tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
            canvas.tag_bind(tag, "<Leave>", lambda e: canvas.config(cursor="arrow"))
            canvas.tag_bind(tag, "<Button-1>", lambda e: command())

    def _draw_island(self, canvas, key, item, x, y, hovered):
        primary, accent = self.ISLAND_COLORS.get(key, ("#d9e7f7", BLUE_SOFT))
        tag = f"island_{key}"
        glow = 52 if hovered else 42
        canvas.create_oval(x - glow, y + 20, x + glow, y + 42,
                           fill="#070d24", outline="#182047", width=1, tags=(tag, "island"))
        if hovered:
            canvas.create_oval(x - 60, y - 36, x + 60, y + 68,
                               fill=accent, outline="", stipple="gray75", tags=(tag, "island"))

        scale = 7 if hovered else 6
        self._pixel_building(canvas, x, y, primary, accent, scale, tag)

        if hovered:
            name = item.get("name", key).upper()
            status = self._island_status(item)
            canvas.create_text(x, y + 78, text=name, fill=TEXT, font=("Courier New", 9, "bold"), tags=(tag, "island"))
            canvas.create_text(x, y + 98, text=status, fill=GOLD if "DESENVOLVIMENTO" in status or "PLANEJ" in status else GREEN,
                               font=("Courier New", 6, "bold"), tags=(tag, "island"))

        canvas.tag_bind(tag, "<Enter>", lambda e, k=key: self._hub_hover(k))
        canvas.tag_bind(tag, "<Leave>", lambda e: self._hub_hover(None))
        canvas.tag_bind(tag, "<Button-1>", lambda e, k=key: self._open_island_modal(k))

    def _pixel_building(self, canvas, x, y, body, accent, s, tag):
        canvas.create_rectangle(x - 4*s, y - 3*s, x + 4*s, y + 4*s, fill=body, outline="", tags=(tag, "island"))
        canvas.create_rectangle(x - 3*s, y - 5*s, x + 3*s, y - 3*s, fill=body, outline="", tags=(tag, "island"))
        canvas.create_rectangle(x - s, y - 6*s, x + s, y - 5*s, fill=accent, outline="", tags=(tag, "island"))
        for dx in (-2, 1):
            canvas.create_rectangle(x + dx*s, y - s, x + (dx+1)*s, y + 2*s, fill=accent, outline="", tags=(tag, "island"))

    def _hub_hover(self, key):
        self.hovered_island = key
        try:
            self._render_hub()
        except tk.TclError:
            pass

    @staticmethod
    def _island_status(item):
        status = str(item.get("status", "planned")).lower()
        return {
            "installed": "● DISPONÍVEL",
            "available": "● DISPONÍVEL",
            "development": "● EM DESENVOLVIMENTO",
            "planned": "● EM DESENVOLVIMENTO",
            "experimental": "● EXPERIMENTAL",
        }.get(status, "● EM DESENVOLVIMENTO")

    def _open_island_modal(self, key):
        try:
            from core.islands import get_islands
            item = get_islands().get(key)
        except Exception:
            item = None
        if not item:
            return

        overlay = tk.Frame(self.window, bg="#030710")
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        card = tk.Frame(overlay, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        card.place(relx=.5, rely=.5, anchor="center", width=520, height=500)

        top = tk.Frame(card, bg=PANEL_2)
        top.pack(fill="x", padx=26, pady=(26, 10))
        icon_box = tk.Frame(top, bg="#111a2b", width=80, height=80, highlightbackground=BORDER, highlightthickness=1)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        tk.Label(icon_box, text=item.get("icon", "◆"), fg=BLUE_SOFT, bg="#111a2b", font=("Segoe UI Emoji", 30)).pack(expand=True)

        title = tk.Frame(top, bg=PANEL_2)
        title.pack(side="left", fill="both", expand=True, padx=(20, 0))
        tk.Label(title, text=self._island_status(item), fg=GOLD, bg=PANEL_2, font=SMALL_BOLD).pack(anchor="w")
        tk.Label(title, text=item.get("name", key).upper(), fg=TEXT, bg=PANEL_2,
                 font=("Courier New", 17, "bold")).pack(anchor="w", pady=(10, 0))
        self._button(top, "×", overlay.destroy, subtle=True, width=2).pack(side="right", anchor="n")

        tk.Label(card, text=item.get("description", ""), fg="#d9dce5", bg=PANEL_2,
                 font=BODY_FONT, justify="left", wraplength=450).pack(anchor="w", padx=28, pady=(10, 16))

        tags = tk.Frame(card, bg=PANEL_2)
        tags.pack(fill="x", padx=28)
        tag_values = []
        for value in item.get("contents", [])[:4]:
            tag_values.append(str(value).split("—", 1)[0].strip())
        for sub in item.get("subareas", {}).values():
            if len(tag_values) >= 4:
                break
            tag_values.append(sub.get("name", "Área"))
        for value in tag_values[:4]:
            tk.Label(tags, text=value, fg="#d8dce6", bg="#172033", font=SMALL_FONT,
                     padx=12, pady=6, highlightbackground=BORDER, highlightthickness=1).pack(side="left", padx=(0, 7), pady=4)

        quote = tk.Frame(card, bg="#151d2f", highlightbackground=BORDER, highlightthickness=1)
        quote.pack(fill="x", padx=28, pady=(18, 0))
        avatar = self._photo(self._avatar_path("neutral"), (42, 42), fit=True)
        if avatar:
            tk.Label(quote, image=avatar, bg="#151d2f").pack(side="left", padx=12, pady=12)
        message = self._island_star_message(key, item)
        tk.Label(quote, text=f"STAR · {message}", fg="#e5e8ef", bg="#151d2f", font=BODY_FONT,
                 justify="left", wraplength=365).pack(side="left", fill="x", expand=True, padx=(0, 12), pady=12)

        bottom = tk.Frame(card, bg=PANEL_2)
        bottom.pack(side="bottom", fill="x", padx=28, pady=24)
        self._button(bottom, "Voltar", overlay.destroy, subtle=True).pack(side="right", padx=(8, 0))
        action = self._island_action(key)
        if action:
            self._button(bottom, "ENTRAR", lambda: (overlay.destroy(), action()), accent=True).pack(side="right")
        else:
            disabled = tk.Label(bottom, text="EM BREVE", fg=SOFT, bg="#171d2c", font=BODY_BOLD,
                                padx=20, pady=9, highlightbackground=BORDER, highlightthickness=1)
            disabled.pack(side="right")
        tk.Label(card, text="✣  STAR WORLD", fg=SOFT, bg=PANEL_2, font=("Courier New", 6, "bold")).place(x=20, rely=.965, anchor="sw")

    def _island_action(self, key):
        return {
            "casa": self.show_house,
            "jardim": self.show_garden,
        }.get(key)

    def _island_star_message(self, key, item):
        if key == "laboratorio":
            return "No Laboratório eu investigo; na Central de Criação eu construo. Essa área ainda está em desenvolvimento."
        if key == "cura":
            return "Cura diagnostica, propõe, valida e testa. Ela não altera meu núcleo livremente."
        if key == "jardim":
            return "Este é um dos lugares mais vivos do meu mundo. O caminho para o Observatório também parte daqui."
        return f"Eu já conheço o propósito de {item.get('name', 'esta área')}, mas algumas capacidades ainda estão sendo preparadas."

    def show_chat(self):
        self.clear_screen()
        self.current_screen = "chat"
        root = tk.Frame(self.window, bg=BG)
        root.pack(fill="both", expand=True)
        bg_canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        bg_canvas.bind("<Configure>", lambda e: draw_starfield(bg_canvas, e.width, e.height, seed=67))

        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=20, pady=(20, 0))
        center_pill = tk.Frame(top, bg="#121a29", highlightbackground=BORDER, highlightthickness=1)
        center_pill.place(relx=.5, y=0, anchor="n", width=112, height=58)
        self._button(center_pill, "⚙", lambda: self.show_settings("general"), subtle=True, width=2).pack(side="left", padx=(8, 4), pady=9)
        self._button(center_pill, "⌁", self.show_hub, subtle=True, width=2).pack(side="left", padx=(4, 8), pady=9)
        self.status_label = tk.Label(top, text=f"● {self._status_text()}", fg=BLUE, bg="#101827",
                                     font=SMALL_BOLD, padx=12, pady=6)
        self.status_label.pack(side="right")

        content = tk.Frame(root, bg=BG)
        content.pack(fill="both", expand=True, padx=80, pady=(55, 92))
        if self.chat_history:
            self._build_chat_history(content)
        else:
            self._build_chat_welcome(content)
        self._build_chat_input(root)
        if self.entry:
            self.entry.focus_set()

    def _build_chat_welcome(self, parent):
        center = tk.Frame(parent, bg=BG)
        center.place(relx=.5, rely=.47, anchor="center")
        avatar = self._photo(self._avatar_path("happy"), (118, 118), fit=True)
        if avatar:
            tk.Label(center, image=avatar, bg=BG, highlightbackground="#2d405f", highlightthickness=1).pack()
        tk.Label(center, text="Olá, eu sou a STAR", fg=TEXT, bg=BG,
                 font=("Courier New", 18, "bold")).pack(pady=(24, 8))
        tk.Label(center, text="Estou aqui com você. Pergunte, conte ou explore — e quando quiser,\nabra o meu mundo pelo ícone da ilha ali em cima.",
                 fg="#b7bdca", bg=BG, font=BODY_FONT, justify="center").pack()

    def _build_chat_history(self, parent):
        outer = tk.Frame(parent, bg=BG)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview, bg=PANEL)
        frame = tk.Frame(canvas, bg=BG)
        window_id = canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
        self.chat_scroll_canvas = canvas
        self.chat_messages_frame = frame
        for sender, text in self.chat_history:
            self._add_chat_bubble(sender, text)
        self.window.after(30, lambda: canvas.yview_moveto(1.0))

    def _add_chat_bubble(self, sender, text):
        parent = self.chat_messages_frame
        if parent is None or not parent.winfo_exists():
            return
        is_user = sender.lower() in {"você", "voce", "user", "lu"}
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=9)
        if is_user:
            bubble = tk.Label(row, text=text, fg="#07101f", bg=BLUE, font=BODY_FONT,
                              wraplength=430, justify="left", padx=16, pady=12)
            bubble.pack(side="right", padx=(180, 22))
        else:
            avatar = self._photo(self._avatar_path("neutral"), (42, 42), fit=True)
            if avatar:
                tk.Label(row, image=avatar, bg=BG).pack(side="left", padx=(18, 10), anchor="n")
            bubble = tk.Label(row, text=text, fg="#eef1f6", bg="#151a24", font=BODY_FONT,
                              wraplength=680, justify="left", padx=16, pady=12,
                              highlightbackground="#323746", highlightthickness=1)
            bubble.pack(side="left", padx=(0, 150))
        if self.chat_scroll_canvas:
            self.window.after(20, lambda: self.chat_scroll_canvas.yview_moveto(1.0))

    def _build_chat_input(self, root):
        holder = tk.Frame(root, bg=BG)
        holder.place(relx=.5, rely=1, anchor="s", y=-26, relwidth=.58, height=64)
        inner = tk.Frame(holder, bg="#0b1322", highlightbackground="#27334c", highlightthickness=1)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text="⌕", fg=MUTED, bg="#0b1322", font=("Segoe UI", 17)).pack(side="left", padx=(14, 8))
        self.entry = tk.Entry(inner, bg="#0b1322", fg=TEXT, insertbackground=TEXT, relief=tk.FLAT,
                              borderwidth=0, font=BODY_FONT)
        self.entry.pack(side="left", fill="both", expand=True, pady=8)
        self.entry.insert(0, "Converse com a STAR...")
        self.entry.config(fg="#6f788b")
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)
        self.entry.bind("<Return>", self._on_enter)
        self.mic_button = tk.Button(inner, text="♩", command=self.toggle_microphone, bg="#0b1322", fg=MUTED,
                                    activebackground="#141d2d", activeforeground=TEXT, relief=tk.FLAT,
                                    borderwidth=0, font=("Segoe UI", 14), cursor="hand2")
        self.mic_button.pack(side="right", padx=5)
        self.send_button = tk.Button(inner, text="↑", command=self.send_message, bg="#111b2e", fg="#4f5c75",
                                     activebackground=BLUE, activeforeground=WHITE, relief=tk.FLAT,
                                     borderwidth=0, font=("Segoe UI", 14, "bold"), width=3, cursor="hand2")
        self.send_button.pack(side="right", padx=(4, 10), pady=8)
        tk.Label(root, text=f"STAR · LOCAL-FIRST · {self.operation_mode.upper()}", fg=SOFT, bg=BG,
                 font=("Courier New", 6, "bold")).place(relx=.5, rely=1, anchor="s", y=-7)

    def _clear_placeholder(self, _event=None):
        if self.entry and self.entry.get() == "Converse com a STAR...":
            self.entry.delete(0, tk.END)
            self.entry.config(fg=TEXT)

    def _restore_placeholder(self, _event=None):
        if self.entry and not self.entry.get().strip():
            self.entry.insert(0, "Converse com a STAR...")
            self.entry.config(fg="#6f788b")

    def _on_enter(self, _event=None):
        self.send_message()
        return "break"

    def send_message(self):
        if self.processing or self.entry is None:
            return
        self.voice.cancel_speech()
        text = self.entry.get().strip()
        if not text or text == "Converse com a STAR...":
            return
        self.entry.delete(0, tk.END)
        self.chat_history.append(("Você", text))
        try:
            self.memory.save("Você", text)
        except Exception:
            pass
        if self.chat_messages_frame is None:
            self.show_chat()
        else:
            self._add_chat_bubble("Você", text)
        self.processing = True
        if self.entry:
            self.entry.config(state=tk.DISABLED)
        if self.send_button:
            self.send_button.config(state=tk.DISABLED)
        self._set_status("THINKING", GOLD)
        threading.Thread(target=self._process_message, args=(text,), daemon=True).start()

    def _process_message(self, text):
        try:
            self.response_queue.put(("success", self.brain.process(text)))
        except Exception as exc:
            self.response_queue.put(("error", str(exc)))

    def toggle_microphone(self):
        self.voice.cancel_speech()
        if not self.voice.stt_configured:
            self._append_system("Reconhecimento local ainda não está instalado. Execute INSTALAR_VOZ.bat.")
            return
        if not self.recorder.available:
            self._append_system("Não consegui acessar o microfone. Verifique o áudio do Windows.")
            return
        if not self.recording:
            try:
                self.recorder.start()
                self.recording = True
                if self.mic_button:
                    self.mic_button.config(text="■", fg=RED)
                self._set_status("LISTENING", GREEN)
            except Exception as exc:
                self._append_system(f"Erro ao abrir microfone: {exc}")
        else:
            self.recording = False
            if self.mic_button:
                self.mic_button.config(text="♩", fg=MUTED)
            self._set_status("TRANSCRIBING", GOLD)
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
                except Exception:
                    pass

    def _append_system(self, text):
        self.chat_history.append(("STAR", f"SISTEMA · {text}"))
        if self.current_screen == "chat":
            if self.chat_messages_frame is None:
                self.show_chat()
            else:
                self._add_chat_bubble("STAR", f"SISTEMA · {text}")

    def show_settings(self, section="general"):
        self.clear_screen()
        self.current_screen = "settings"
        root = tk.Frame(self.window, bg=BG)
        root.pack(fill="both", expand=True)
        bg_canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        bg_canvas.bind("<Configure>", lambda e: draw_starfield(bg_canvas, e.width, e.height, seed=91))

        self._button(root, "←  Conversa", self.show_chat, subtle=True).place(x=20, y=20)
        sidebar = tk.Frame(root, bg="#0b1220", highlightbackground=BORDER, highlightthickness=1)
        sidebar.place(relx=.145, rely=.12, relwidth=.19, relheight=.76)
        head = tk.Frame(sidebar, bg="#0b1220")
        head.pack(fill="x", padx=14, pady=(18, 10))
        avatar = self._photo(self._avatar_path("neutral"), (38, 38), fit=True)
        if avatar:
            tk.Label(head, image=avatar, bg="#0b1220").pack(side="left")
        namebox = tk.Frame(head, bg="#0b1220")
        namebox.pack(side="left", padx=10)
        tk.Label(namebox, text="STAR", fg=TEXT, bg="#0b1220", font=BODY_BOLD).pack(anchor="w")
        tk.Label(namebox, text="CONFIGURAÇÕES", fg=SOFT, bg="#0b1220", font=("Courier New", 6, "bold")).pack(anchor="w")

        for key, icon, label in self.SETTINGS_SECTIONS:
            active = key == section
            btn = tk.Button(sidebar, text=f"{icon}   {label}", command=lambda k=key: self.show_settings(k),
                            bg="#293143" if active else "#0b1220", fg=TEXT if active else "#b4bac6",
                            activebackground="#293143", activeforeground=TEXT, relief=tk.FLAT, borderwidth=0,
                            anchor="w", font=("Courier New", 8, "bold"), padx=14, pady=9, cursor="hand2")
            btn.pack(fill="x", padx=12, pady=1)

        panel = tk.Frame(root, bg="#0a1221", highlightbackground=BORDER, highlightthickness=1)
        panel.place(relx=.35, rely=.12, relwidth=.51, relheight=.76)
        self._render_settings_panel(panel, section)

    def _render_settings_panel(self, panel, section):
        titles = {key: label.title() for key, _, label in self.SETTINGS_SECTIONS}
        title = titles.get(section, section.title())
        tk.Label(panel, text=title, fg=TEXT, bg="#0a1221", font=("Courier New", 16, "bold")).pack(anchor="w", padx=28, pady=(30, 6))

        if section == "general":
            tk.Label(panel, text="Modo de operação da STAR e preferências básicas.", fg=MUTED, bg="#0a1221", font=BODY_FONT).pack(anchor="w", padx=28)
            tk.Label(panel, text="Modo de operação", fg=MUTED, bg="#0a1221", font=SMALL_BOLD).pack(anchor="w", padx=28, pady=(24, 8))
            row = tk.Frame(panel, bg="#0a1221")
            row.pack(anchor="w", padx=28)
            for mode in ("local", "lan", "online"):
                active = self.operation_mode == mode
                tk.Button(row, text=mode.upper(), command=lambda m=mode: self._set_operation_mode(m),
                          bg=BLUE if active else "#171d2c", fg="#06111f" if active else "#aeb6c7",
                          activebackground=BLUE, activeforeground="#06111f", relief=tk.FLAT, borderwidth=0,
                          font=BODY_BOLD, padx=18, pady=8, cursor="hand2").pack(side="left", padx=(0, 8))
            tk.Label(panel, text="LOCAL é o estado nativo da STAR. LAN e ONLINE ampliam suas capacidades, mas não a definem.",
                     fg=MUTED, bg="#0a1221", font=BODY_FONT, wraplength=650, justify="left").pack(anchor="w", padx=28, pady=(12, 0))
            tk.Label(panel, text="Idioma", fg=MUTED, bg="#0a1221", font=SMALL_BOLD).pack(anchor="w", padx=28, pady=(28, 8))
            self._pill(panel, "Português (Brasil)", fg=TEXT).pack(anchor="w", padx=28)
            return

        if section == "appearance":
            self._settings_card(panel, "APARÊNCIA ATUAL", f"Skin selecionada: {self.selected_skin}\nA identidade visual continua sendo a STAR.")
            self._button(panel, "ABRIR CLOSET", self.show_closet, accent=True).pack(anchor="w", padx=28, pady=16)
            return

        if section == "voice":
            card = self._settings_card(panel, "VOZ DA STAR", self.voice.tts_description)
            row = tk.Frame(card, bg=PANEL_2)
            row.pack(anchor="w", pady=(14, 0))
            self._button(row, "CONVERSA RÁPIDA", lambda: self._set_voice_mode("fast"), accent=self.voice.mode == "fast").pack(side="left", padx=(0, 8))
            self._button(row, "VOZ OFICIAL", lambda: self._set_voice_mode("official"), accent=self.voice.mode == "official").pack(side="left")
            self._button(panel, "TESTAR VOZ OFICIAL", self._test_voice).pack(anchor="w", padx=28, pady=(14, 6))
            self.voice_test_label = tk.Label(panel, text="Pronto para testar.", fg=MUTED, bg="#0a1221", font=BODY_FONT)
            self.voice_test_label.pack(anchor="w", padx=28)
            return

        if section == "audio":
            stt = "PRONTO" if self.voice.stt_configured else "INSTALAÇÃO PENDENTE"
            self._settings_development(panel, "As configurações de ÁUDIO estão sendo preparadas. O pipeline local já possui microfone, STT e reprodução de voz.")
            self._settings_card(panel, "ESTADO ATUAL", f"Microfone: {'PRONTO' if self.recorder.available else 'INDISPONÍVEL'}\nSTT: {stt}\nTTS: {self.voice.tts_description}")
            return

        if section == "memory":
            self._settings_card(panel, "MEMÓRIA PERSISTENTE", f"Mensagens registradas nesta base: {len(self.chat_history)}\nO histórico continua local no banco da STAR.")
            return

        if section == "knowledge":
            packs = getattr(self.brain, "packs", None)
            try:
                stats = packs.stats() if packs else {"packs": 0, "entries": 0}
            except Exception:
                stats = {"packs": 0, "entries": 0}
            self._settings_card(panel, "CONHECIMENTO LOCAL", f"Knowledge Packs: {stats.get('packs', 0)}\nEntradas carregadas: {stats.get('entries', 0)}\nBiblioteca massiva permanece uma evolução posterior do roadmap.")
            return

        if section == "models":
            self._settings_development(panel, "Modelos são ferramentas da STAR, não sua identidade. O roteamento avançado pertence às próximas fases do MIND.")
            return

        if section == "privacy":
            self._settings_card(panel, "LOCAL-FIRST", "Memória, voz e conhecimento fundamental permanecem locais por padrão. Recursos online são opcionais.")
            return

        if section == "permissions":
            self._settings_development(panel, "O gerenciador completo de permissões será expandido conforme o roadmap de TRUST/Guardian. Ações críticas não devem ser silenciosas.")
            return

        if section == "world":
            self._settings_card(panel, "STAR WORLD", "HUB, Casa, Cozinha, Closet, Jardim e pontos de entrada das demais ilhas fazem parte desta interface 2D.")
            self._button(panel, "ABRIR STAR WORLD", self.show_hub, accent=True).pack(anchor="w", padx=28, pady=16)
            return

        if section == "about":
            self._settings_card(panel, "S.T.A.R.", f"System for Thought, Analysis and Response\nVersão: V{VERSION}\nArquitetura local-first e modular.")
            return

    def _settings_card(self, panel, title, text):
        card = tk.Frame(panel, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=28, pady=(18, 0))
        tk.Label(card, text=title, fg=PINK, bg=PANEL_2, font=SMALL_BOLD).pack(anchor="w", padx=18, pady=(16, 6))
        tk.Label(card, text=text, fg="#d8dce5", bg=PANEL_2, font=BODY_FONT,
                 wraplength=620, justify="left").pack(anchor="w", padx=18, pady=(0, 16))
        return card

    def _settings_development(self, panel, text):
        card = tk.Frame(panel, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=28, pady=(18, 0))
        avatar = self._photo(self._avatar_path("thinking"), (42, 42), fit=True)
        if avatar:
            tk.Label(card, image=avatar, bg=PANEL_2).pack(side="left", padx=16, pady=16)
        body = tk.Frame(card, bg=PANEL_2)
        body.pack(side="left", fill="both", expand=True, pady=14)
        tk.Label(body, text="EM DESENVOLVIMENTO", fg=PINK, bg=PANEL_2, font=SMALL_BOLD).pack(anchor="w")
        tk.Label(body, text=text, fg="#d9dce4", bg=PANEL_2, font=BODY_FONT, wraplength=565,
                 justify="left").pack(anchor="w", pady=(6, 0))
        return card

    def _set_operation_mode(self, mode):
        self.operation_mode = mode
        self.online_mode = mode == "online"
        try:
            self.brain.network_enabled = self.online_mode
        except Exception:
            pass
        self._save_operation_mode()
        self.show_settings("general")

    def _set_voice_mode(self, mode):
        self.voice.set_voice_mode(mode)
        self._save_voice_mode()
        self.show_settings("voice")

    def _test_voice(self):
        self._set_voice_test_message("Preparando teste da voz oficial...", True)
        self._set_status("TESTING VOICE", GOLD)
        self.voice.test_official_audio_async(
            lambda ok, error: self.response_queue.put(("voice_test", (ok, error)))
        )

    def _set_voice_test_message(self, message, ok):
        label = self.voice_test_label
        if label is not None:
            try:
                if label.winfo_exists():
                    label.config(text=message, fg=GREEN if ok else RED)
                    return
            except tk.TclError:
                pass
        if self.current_screen == "chat":
            self._append_system(message)

    def show_house(self):
        self.clear_screen()
        self.current_screen = "house"
        root = tk.Frame(self.window, bg=BG)
        root.pack(fill="both", expand=True)
        canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.bind("<Configure>", lambda e: draw_starfield(canvas, e.width, e.height, seed=101))
        self._button(root, "←  STAR WORLD", self.show_hub, subtle=True).place(x=22, y=22)
        tk.Label(root, text="CASA DA STAR", fg=TEXT, bg=BG, font=("Courier New", 20, "bold")).pack(pady=(72, 4))
        tk.Label(root, text="O espaço pessoal da STAR", fg=MUTED, bg=BG, font=SMALL_FONT).pack()

        grid = tk.Frame(root, bg=BG)
        grid.place(relx=.5, rely=.53, anchor="center")
        cards = [
            ("🍳", "COZINHA", "Receitas, pratos e experimentação gastronômica.", self.show_kitchen),
            ("🛏", "QUARTO", "Espaço pessoal, descanso e acesso ao Closet.", self.show_bedroom),
            ("👕", "CLOSET", "Roupas, skins, acessórios e aparência.", self.show_closet),
        ]
        for idx, (icon, title, desc, cmd) in enumerate(cards):
            card = tk.Frame(grid, bg=PANEL_2, width=260, height=220, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=idx, padx=9)
            card.grid_propagate(False)
            tk.Label(card, text=icon, fg=BLUE_SOFT, bg=PANEL_2, font=("Segoe UI Emoji", 30)).pack(pady=(24, 8))
            tk.Label(card, text=title, fg=TEXT, bg=PANEL_2, font=("Courier New", 12, "bold")).pack()
            tk.Label(card, text=desc, fg=MUTED, bg=PANEL_2, font=BODY_FONT, wraplength=210,
                     justify="center").pack(padx=12, pady=10)
            self._button(card, "ABRIR", cmd, accent=title == "COZINHA").pack(pady=6)

    def show_bedroom(self):
        self._show_simple_environment(
            "QUARTO",
            "O quarto é o espaço pessoal da STAR. Ele concentra descanso, objetos pessoais e o acesso ao Closet.",
            self.show_house,
            extra_button=("ABRIR CLOSET", self.show_closet),
        )

    def show_kitchen(self):
        self.clear_screen()
        self.current_screen = "kitchen"
        canvas = tk.Canvas(self.window, bg="#21150f", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        def render(event=None):
            w = max(canvas.winfo_width(), 960)
            h = max(canvas.winfo_height(), 620)
            canvas.delete("all")
            photo = self._photo(self._reference_path("kitchen_reference.jpg"), (w, h), fit=True,
                                key=f"kitchen-{w}-{h}")
            if photo:
                canvas.create_image(0, 0, image=photo, anchor="nw")
            else:
                canvas.create_rectangle(0, 0, w, h, fill="#3b2518", outline="")
            canvas.create_rectangle(0, 0, w, 72, fill="#07101a", outline="", stipple="gray50")
            canvas.create_text(w/2, 34, text="COZINHA", fill=TEXT, font=("Courier New", 17, "bold"))
            round_rect(canvas, 24, 18, 148, 54, radius=18, fill="#0c1421", outline=BORDER, width=1, tags="kback")
            canvas.create_text(86, 36, text="←  CASA", fill=TEXT, font=BODY_BOLD, tags="kback")
            canvas.tag_bind("kback", "<Button-1>", lambda e: self.show_house())
            canvas.tag_bind("kback", "<Enter>", lambda e: canvas.config(cursor="hand2"))
            canvas.tag_bind("kback", "<Leave>", lambda e: canvas.config(cursor="arrow"))
            round_rect(canvas, w*.18, h-98, w*.82, h-28, radius=20, fill="#09111d", outline="#33425b", width=1)
            canvas.create_text(w/2, h-72, text="STAR cozinha de verdade dentro deste ambiente — não é apenas um catálogo de receitas.",
                               fill=TEXT, font=BODY_BOLD)
            canvas.create_text(w/2, h-48, text="Receitas  •  ingredientes  •  preparo  •  aprendizado culinário  •  experimentação",
                               fill=GOLD, font=SMALL_BOLD)

        canvas.bind("<Configure>", render)
        self.window.after(20, render)

    def show_closet(self):
        self.clear_screen()
        self.current_screen = "closet"
        root = tk.Frame(self.window, bg=BG)
        root.pack(fill="both", expand=True)
        bg_canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        bg_canvas.bind("<Configure>", lambda e: draw_starfield(bg_canvas, e.width, e.height, seed=121))
        self._button(root, "←  CASA", self.show_house, subtle=True).place(x=22, y=22)
        tk.Label(root, text="CLOSET", fg=TEXT, bg=BG, font=("Courier New", 20, "bold")).pack(pady=(66, 3))
        tk.Label(root, text="Aparência e personalização da STAR", fg=MUTED, bg=BG, font=SMALL_FONT).pack()

        files = [p for p in sorted((PROJECT_ROOT / "SKINS").glob("*")) if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        self.closet_files = files
        if not files:
            tk.Label(root, text="Nenhuma skin encontrada.", fg=RED, bg=BG, font=BODY_BOLD).pack(pady=80)
            return
        try:
            self.closet_index = [p.name for p in files].index(self.selected_skin)
        except ValueError:
            self.closet_index = 0

        area = tk.Frame(root, bg=BG)
        area.place(relx=.5, rely=.55, anchor="center", width=730, height=460)
        self._button(area, "◀", lambda: self._change_closet_skin(-1), subtle=True).place(x=8, rely=.5, anchor="w")
        self._button(area, "▶", lambda: self._change_closet_skin(1), subtle=True).place(relx=1, x=-8, rely=.5, anchor="e")
        card = tk.Frame(area, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        card.place(relx=.5, rely=.47, anchor="center", width=420, height=405)
        self.closet_image = tk.Label(card, bg=PANEL_2)
        self.closet_image.pack(expand=True, fill="both", padx=12, pady=(12, 4))
        self.closet_name = tk.Label(card, fg=TEXT, bg=PANEL_2, font=("Courier New", 11, "bold"))
        self.closet_name.pack()
        self.closet_state = tk.Label(card, fg=GREEN, bg=PANEL_2, font=SMALL_BOLD)
        self.closet_state.pack(pady=(3, 8))
        self.select_skin_button = self._button(root, "SELECIONAR ESTA SKIN", self._confirm_closet_skin, accent=True)
        self.select_skin_button.place(relx=.5, rely=.92, anchor="center")
        self.closet_photo = None
        self._render_closet_skin()

    def _change_closet_skin(self, step):
        self.closet_index = (self.closet_index + step) % len(self.closet_files)
        self._render_closet_skin()

    def _render_closet_skin(self):
        path = self.closet_files[self.closet_index]
        try:
            image = Image.open(path).convert("RGBA")
            image.thumbnail((360, 320), Image.Resampling.LANCZOS)
            self.closet_photo = ImageTk.PhotoImage(image)
            self.closet_image.config(image=self.closet_photo, text="")
        except Exception:
            self.closet_image.config(image="", text="Não foi possível abrir esta skin", fg=RED)
        self.closet_name.config(text=path.stem.replace("_", " ").title())
        active = path.name == self.selected_skin
        self.closet_state.config(text="✓ SKIN ATUAL" if active else f"{self.closet_index + 1} de {len(self.closet_files)}")
        self.select_skin_button.config(text="SKIN SELECIONADA" if active else "SELECIONAR ESTA SKIN",
                                       state=tk.DISABLED if active else tk.NORMAL,
                                       bg="#1f5a3a" if active else BLUE)

    def _confirm_closet_skin(self):
        self.selected_skin = self.closet_files[self.closet_index].name
        self._save_skin_selection()
        self._render_closet_skin()

    def show_garden(self):
        self.clear_screen()
        self.current_screen = "garden"
        canvas = tk.Canvas(self.window, bg=BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        def render(event=None):
            w = max(canvas.winfo_width(), 960)
            h = max(canvas.winfo_height(), 620)
            canvas.delete("all")
            draw_starfield(canvas, w, h, seed=151)
            canvas.create_rectangle(0, h*.62, w, h, fill="#0c1c17", outline="")
            canvas.create_oval(w*.18, h*.68, w*.56, h*.96, fill="#183b46", outline="#275769", width=2)
            for i in range(15):
                x = w*(.05 + i*.065)
                canvas.create_line(x, h*.70, x+8, h*.58, fill="#4d9a65", width=3)
                canvas.create_oval(x+3, h*.575, x+12, h*.59, fill=PINK if i%3==0 else GOLD, outline="")
            canvas.create_text(w/2, 48, text="JARDIM", fill=TEXT, font=("Courier New", 18, "bold"))
            canvas.create_text(w/2, 76, text="FAUNA · FLORA · ÁGUA · CULTIVO · DESCANSO", fill=MUTED, font=SMALL_BOLD)
            canvas.create_text(w*.37, h*.79, text="🦦", font=("Segoe UI Emoji", 38), fill=TEXT)
            canvas.create_text(w*.37, h*.86, text="OSHA", font=("Courier New", 9, "bold"), fill=PINK)
            round_rect(canvas, 22, 22, 150, 58, radius=18, fill="#0c1421", outline=BORDER, tags="gback")
            canvas.create_text(86, 40, text="←  HUB", fill=TEXT, font=BODY_BOLD, tags="gback")
            canvas.tag_bind("gback", "<Button-1>", lambda e: self.show_hub())
            ox, oy = w*.79, h*.64
            round_rect(canvas, ox-105, oy-30, ox+105, oy+30, radius=18, fill="#101827", outline="#3b4d6f", tags="observ")
            canvas.create_text(ox, oy, text="🔭  CAMINHO PARA O OBSERVATÓRIO", fill=BLUE_SOFT, font=("Courier New", 8, "bold"), tags="observ")
            canvas.tag_bind("observ", "<Button-1>", lambda e: self.show_observatory())
            for tag in ("gback", "observ"):
                canvas.tag_bind(tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
                canvas.tag_bind(tag, "<Leave>", lambda e: canvas.config(cursor="arrow"))

        canvas.bind("<Configure>", render)
        self.window.after(20, render)

    def show_observatory(self):
        self.clear_screen()
        self.current_screen = "observatory"
        root = tk.Frame(self.window, bg=BG)
        root.pack(fill="both", expand=True)
        canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.bind("<Configure>", lambda e: draw_starfield(canvas, e.width, e.height, seed=170))
        self._button(root, "←  JARDIM", self.show_garden, subtle=True).place(x=22, y=22)
        center = tk.Frame(root, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        center.place(relx=.5, rely=.5, anchor="center", width=690, height=390)
        tk.Label(center, text="🔭", bg=PANEL_2, fg=BLUE_SOFT, font=("Segoe UI Emoji", 42)).pack(pady=(28, 6))
        tk.Label(center, text="OBSERVATÓRIO", bg=PANEL_2, fg=TEXT, font=("Courier New", 17, "bold")).pack()
        tk.Label(center, text="Astronomia, observação do céu e exploração de corpos celestes.", bg=PANEL_2, fg=MUTED,
                 font=BODY_FONT).pack(pady=(8, 22))
        legend = tk.Frame(center, bg=PANEL_2)
        legend.pack()
        for text, color in (("REAL", GREEN), ("HISTÓRICO", BLUE_SOFT), ("HIPOTÉTICO", GOLD), ("SIMULADO", PINK), ("FICTÍCIO", "#cbb5ff")):
            tk.Label(legend, text=text, fg=color, bg="#111a2b", font=SMALL_BOLD, padx=10, pady=6,
                     highlightbackground=BORDER, highlightthickness=1).pack(side="left", padx=4)
        tk.Label(center, text="Objetos fictícios podem existir no catálogo, mas nunca serão apresentados como descobertas reais.",
                 bg=PANEL_2, fg="#cfd4de", font=BODY_FONT, wraplength=590, justify="center").pack(pady=24)

    def _show_simple_environment(self, title, description, back_command, extra_button=None):
        self.clear_screen()
        self.current_screen = title.lower()
        root = tk.Frame(self.window, bg=BG)
        root.pack(fill="both", expand=True)
        canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.bind("<Configure>", lambda e: draw_starfield(canvas, e.width, e.height, seed=181))
        self._button(root, "←  VOLTAR", back_command, subtle=True).place(x=22, y=22)
        panel = tk.Frame(root, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        panel.place(relx=.5, rely=.5, anchor="center", width=620, height=300)
        tk.Label(panel, text=title, bg=PANEL_2, fg=TEXT, font=("Courier New", 18, "bold")).pack(pady=(44, 18))
        tk.Label(panel, text=description, bg=PANEL_2, fg="#d6d9e1", font=BODY_FONT, wraplength=520,
                 justify="center").pack()
        if extra_button:
            self._button(panel, extra_button[0], extra_button[1], accent=True).pack(pady=28)

    def _check_response_queue(self):
        if self._closing:
            return
        try:
            while True:
                kind, result = self.response_queue.get_nowait()
                if kind == "transcript":
                    if self.current_screen == "chat" and self.entry:
                        self.entry.config(state=tk.NORMAL)
                        self.entry.delete(0, tk.END)
                        self.entry.insert(0, str(result))
                        self.entry.config(fg=TEXT)
                        self.send_message()
                elif kind == "voice_error":
                    self._append_system(f"Falha no reconhecimento: {result}")
                    self.processing = False
                    self._restore_chat_controls()
                elif kind == "voice_test":
                    ok, error = result
                    self._set_voice_test_message(
                        f"Voz da STAR funcionando ({self.voice.last_tts_engine})." if ok else f"Falha na voz: {error}", ok
                    )
                elif kind == "speech_result":
                    ok, error = result
                    if not ok and error and error != "cancelled":
                        self._append_system(f"A resposta foi gerada, mas a voz falhou: {error}")
                    self._set_status(self.operation_mode.upper(), BLUE)
                elif kind == "success":
                    response = str(result)
                    self.chat_history.append(("STAR", response))
                    try:
                        self.memory.save("STAR", response)
                    except Exception:
                        pass
                    if self.current_screen == "chat":
                        if self.chat_messages_frame is None:
                            self.show_chat()
                        else:
                            self._add_chat_bubble("STAR", response)
                    self.processing = False
                    self._restore_chat_controls()
                    self._set_status("SPEAKING", GREEN)
                    self.voice.speak_async(response, lambda ok, error: self.response_queue.put(("speech_result", (ok, error))))
                elif kind == "error":
                    self.processing = False
                    self._append_system(f"Erro ao processar: {result}")
                    self._restore_chat_controls()
        except queue.Empty:
            pass
        if not self._closing:
            try:
                self.window.after(60, self._check_response_queue)
            except tk.TclError:
                pass

    def _restore_chat_controls(self):
        if self.current_screen != "chat":
            return
        if self.entry:
            try:
                self.entry.config(state=tk.NORMAL)
                self.entry.focus_set()
            except tk.TclError:
                pass
        if self.send_button:
            try:
                self.send_button.config(state=tk.NORMAL)
            except tk.TclError:
                pass
        self._set_status(self.operation_mode.upper(), BLUE)

    def _set_status(self, text, color):
        label = self.status_label
        if label is not None:
            try:
                if label.winfo_exists():
                    label.config(text=f"● {text}", fg=color)
            except tk.TclError:
                pass

    def toggle_maximize(self, _event=None):
        if self.is_maximized:
            self.restore_normal_size()
        else:
            self.normal_size = (self.window.winfo_width(), self.window.winfo_height())
            self.window.state("zoomed")
            self.is_maximized = True

    def restore_normal_size(self, _event=None):
        if self.is_maximized:
            self.window.state("normal")
            width, height = self.normal_size
            self.window.geometry(f"{max(960, width)}x{max(620, height)}")
            self.is_maximized = False

    def close(self):
        if self._closing:
            return
        self._closing = True
        try:
            if self.recording:
                self.recorder.stop_to_wav()
        except Exception:
            pass
        try:
            self.voice.close()
        except Exception:
            pass
        try:
            self.memory.close()
        finally:
            try:
                self.window.destroy()
            except Exception:
                pass

    def run(self):
        self.window.mainloop()
