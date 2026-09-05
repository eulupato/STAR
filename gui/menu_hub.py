"""Menu vivo e HUB do STAR WORLD 2D.

Mixin visual sem Core paralelo. Hover e rastreamento dos olhos alteram apenas os
elementos locais do Canvas, evitando o loop de redraw que já causou congelamento.
"""
from __future__ import annotations

import time
import tkinter as tk
from pathlib import Path

from PIL import Image

from config import VERSION
from core.islands import get_islands, status_label
from gui.theme import (
    BG,
    PANEL,
    PANEL_2,
    PANEL_3,
    BORDER,
    TEXT,
    MUTED,
    SOFT,
    GOLD,
    PINK,
    BLUE,
    BLUE_SOFT,
    GREEN,
    BODY_FONT,
    BODY_BOLD,
    SMALL_FONT,
    SMALL_BOLD,
    PIXEL_TITLE,
    PIXEL_LABEL,
    draw_starfield,
    round_rect,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class MenuHubMixin:
    MENU_EMOTIONS = {"iniciar": "happy", "configuracoes": "thinking", "sair": "sad"}
    ISLAND_POSITIONS = [
        (.22, .30), (.42, .20), (.63, .27), (.81, .39), (.69, .58),
        (.48, .62), (.27, .57), (.18, .77), (.52, .82), (.82, .76),
    ]
    ISLAND_COLORS = {
        "casa": ("#EAF6FF", BLUE),
        "laboratorio": ("#E9F6FF", BLUE),
        "biblioteca": ("#FFE69A", GOLD),
        "estudio_musica": ("#FFBBD9", PINK),
        "atelie": ("#FFD2A2", "#FFAE70"),
        "jardim": ("#A8E0B8", GREEN),
        "correio": ("#FFD878", GOLD),
        "cura": ("#D6EDFF", BLUE),
        "herois": ("#E6C7FF", "#C7A5FF"),
        "idiomas": ("#A9DEFF", BLUE),
    }
    REFERENCE_FILES = {
        "menu": "menu_face.webp",
        "kitchen": "kitchen.webp",
        "laboratory": "laboratory.webp",
        "library": "library.webp",
        "observatory": "observatory.webp",
        "cura": "cura.webp",
        "turnaround": "star_turnaround.webp",
    }

    def _reference_path(self, key):
        return PROJECT_ROOT / "assets" / "reference" / self.REFERENCE_FILES.get(key, key)

    def show_menu(self):
        self.clear_screen()
        self.current_screen = "menu"
        self.menu_action_locked = False
        canvas = tk.Canvas(self.window, bg=BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        self.menu_canvas = canvas
        canvas.bind("<Configure>", lambda _e: self._schedule_render(self._render_menu, 60))
        canvas.bind("<Motion>", self._menu_track_eyes)
        canvas.bind("<Leave>", lambda _e: self._center_menu_eyes())
        self._schedule_render(self._render_menu, 10)

    def _render_menu(self):
        c = self.menu_canvas
        if not c or not c.winfo_exists():
            return

        w = max(960, c.winfo_width())
        h = max(620, c.winfo_height())
        c.delete("all")

        path = self._reference_path("menu")
        metrics = None
        if path.exists():
            try:
                with Image.open(path) as image:
                    sw, sh = image.size

                # A arte canônica enviada ocupa a janela inteira, como no protótipo.
                scale = max(w / sw, h / sh)
                ox = (w - sw * scale) / 2
                oy = (h - sh * scale) / 2
                photo = self._photo(
                    path,
                    (w, h),
                    fit=True,
                    key=f"menucover:{w}x{h}",
                )
                if photo:
                    c.create_image(0, 0, image=photo, anchor="nw", tags="menu_background")
                    metrics = (ox, oy, scale, sw, sh)
            except Exception:
                pass

        if metrics is None:
            draw_starfield(c, w, h, seed=17)
            metrics = (0, 0, w / 1376, 1376, 768)

        self.menu_image_metrics = metrics

        c.create_text(
            28, 26, text="STAR", fill="#16315A", anchor="nw",
            font=("Courier New", 21, "bold"),
        )
        c.create_text(
            28, 58, text=f"S.T.A.R. OS · V{VERSION}", fill="#355073", anchor="nw",
            font=("Courier New", 7, "bold"),
        )

        # Botões reais sobre a imagem sem botões. O clique é do Canvas, não da arte.
        x = w * .885
        y0 = h * .61
        spacing = max(66, h * .105)
        button_w = min(250, max(205, w * .18))
        button_h = min(62, max(48, h * .072))
        for i, (action, label) in enumerate(
            (("iniciar", "INICIAR"), ("configuracoes", "CONFIGURAÇÕES"), ("sair", "SAIR"))
        ):
            y = y0 + i * spacing
            self._menu_button(
                c,
                action,
                label,
                x - button_w / 2,
                y - button_h / 2,
                button_w,
                button_h,
            )

        self._draw_menu_eyes()

        sx, sy = w - 112, h - 40
        round_rect(
            c, sx - 67, sy - 14, sx + 67, sy + 14,
            radius=14, fill="#F2F8FF", outline="#A8C7E8",
        )
        c.create_oval(sx - 50, sy - 3, sx - 44, sy + 3, fill=BLUE, outline="")
        c.create_text(
            sx - 36, sy, text=self._status_text(), fill="#16315A",
            anchor="w", font=("Courier New", 7, "bold"),
        )
        self._schedule_blink()

    def _menu_button(self, c, action, label, x, y, width, height):
        tag = f"menu_{action}"
        shape = round_rect(
            c,
            x,
            y,
            x + width,
            y + height,
            radius=7,
            fill="#EAF5FF",
            outline="#183054",
            width=3,
            tags=tag,
        )
        text_item = c.create_text(
            x + width / 2,
            y + height / 2,
            text=label,
            fill="#0B1730",
            font=("Courier New", 13, "bold"),
            tags=tag,
        )

        # Bind direto por item evita problemas de tag quando há espaços/símbolos.
        for item in (shape, text_item):
            c.tag_bind(item, "<Enter>", lambda _e, a=action: self._menu_hover(a, True))
            c.tag_bind(item, "<Leave>", lambda _e, a=action: self._menu_hover(a, False))
            c.tag_bind(item, "<Button-1>", lambda _e, a=action: self._menu_click(a))
        c.tag_raise(tag)

    def _draw_menu_eyes(self):
        c = self.menu_canvas
        self.menu_eye_items = []
        self._blink_items = []
        if not c or not self.menu_image_metrics:
            return

        ox, oy, scale, sw, sh = self.menu_image_metrics
        # Coordenadas calibradas para a arte 1376×768 enviada pelo sr. Lu.
        for ex_ratio, ey_ratio in ((556 / 1376, 284 / 768), (834 / 1376, 284 / 768)):
            x = ox + (sw * ex_ratio) * scale
            y = oy + (sh * ey_ratio) * scale
            radius = max(2, 4 * scale)
            item = c.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill="#14264A",
                outline="#D8F2FF",
                width=1,
                tags="menu_pupil",
            )
            self.menu_eye_items.append((item, x, y, radius))

    def _menu_track_eyes(self, event):
        if not self.menu_canvas or not self.menu_eye_items:
            return
        w = max(1, self.menu_canvas.winfo_width())
        h = max(1, self.menu_canvas.winfo_height())
        for item, bx, by, radius in self.menu_eye_items:
            dx = max(-5, min(5, (event.x - bx) / w * 16))
            dy = max(-4, min(4, (event.y - by) / h * 13))
            try:
                self.menu_canvas.coords(
                    item,
                    bx - radius + dx,
                    by - radius + dy,
                    bx + radius + dx,
                    by + radius + dy,
                )
            except tk.TclError:
                return

    def _center_menu_eyes(self):
        if not self.menu_canvas:
            return
        for item, bx, by, radius in self.menu_eye_items:
            try:
                self.menu_canvas.coords(
                    item,
                    bx - radius,
                    by - radius,
                    bx + radius,
                    by + radius,
                )
            except tk.TclError:
                pass

    def _schedule_blink(self):
        if self._blink_after or self.current_screen != "menu":
            return
        delay = 4200 + (int(time.time() * 1000) % 3600)
        self._blink_after = self.window.after(delay, self._blink_once)

    def _blink_once(self):
        self._blink_after = None
        c = self.menu_canvas
        if not c or self.current_screen != "menu":
            return
        for item, bx, by, radius in self.menu_eye_items:
            try:
                c.itemconfigure(item, state="hidden")
                line = c.create_line(
                    bx - radius * 2.3,
                    by,
                    bx + radius * 2.3,
                    by,
                    fill="#6B2E43",
                    width=max(2, int(radius * .8)),
                )
                self._blink_items.append(line)
            except tk.TclError:
                return
        self.window.after(115, self._end_blink)

    def _end_blink(self):
        c = self.menu_canvas
        if c:
            for line in self._blink_items:
                try:
                    c.delete(line)
                except tk.TclError:
                    pass
            for item, *_ in self.menu_eye_items:
                try:
                    c.itemconfigure(item, state="normal")
                except tk.TclError:
                    pass
        self._blink_items = []
        self._schedule_blink()

    def _menu_hover(self, action, entered):
        if self.menu_action_locked or not self.menu_canvas:
            return
        self.menu_canvas.config(cursor="hand2" if entered else "arrow")
        try:
            self.menu_canvas.itemconfigure(
                f"menu_{action}",
                outline=PINK if entered else "#183054",
            )
        except tk.TclError:
            pass

    def _menu_click(self, action):
        if self.menu_action_locked:
            return
        self.menu_action_locked = True
        emotion = self.MENU_EMOTIONS[action]
        self._show_menu_reaction(emotion)
        if action == "iniciar":
            self.window.after(520, self.show_hub)
        elif action == "configuracoes":
            self.settings_return = "menu"
            self.window.after(520, lambda: self.show_settings("general"))
        else:
            self.window.after(520, self.show_goodbye)

    def _show_menu_reaction(self, emotion):
        c = self.menu_canvas
        if not c:
            return
        w = c.winfo_width()
        h = c.winfo_height()
        photo = self._photo(
            self._avatar_path(emotion),
            (130, 130),
            fit=True,
            key=f"reaction:{emotion}",
        )
        if photo:
            round_rect(
                c,
                w * .69 - 72,
                h * .18 - 72,
                w * .69 + 72,
                h * .18 + 72,
                radius=16,
                fill="#F7FBFF",
                outline=PINK,
                width=2,
                tags="reaction",
            )
            c.create_image(w * .69, h * .18, image=photo, tags="reaction")
        labels = {"happy": "✦", "thinking": "…", "sad": "♡"}
        c.create_text(
            w * .69,
            h * .18 + 87,
            text=labels.get(emotion, "✦"),
            fill="#7A3F67",
            font=("Courier New", 18, "bold"),
            tags="reaction",
        )

    def show_goodbye(self):
        self.clear_screen()
        self.current_screen = "goodbye"
        root = tk.Frame(self.window, bg=BG)
        root.pack(fill="both", expand=True)
        draw = tk.Canvas(root, bg=BG, highlightthickness=0)
        draw.pack(fill="both", expand=True)
        draw.bind("<Configure>", lambda e: draw_starfield(draw, e.width, e.height, seed=44))
        panel = tk.Frame(
            root, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1
        )
        panel.place(relx=.5, rely=.5, anchor="center", width=460, height=310)
        avatar = self._photo(self._avatar_path("sad"), (130, 130), fit=True)
        if avatar:
            tk.Label(panel, image=avatar, bg=PANEL_2).pack(pady=(22, 8))
        tk.Label(panel, text="Até logo.", fg=TEXT, bg=PANEL_2, font=PIXEL_TITLE).pack()
        tk.Label(
            panel,
            text="A STAR continua aqui quando você voltar.",
            fg=MUTED,
            bg=PANEL_2,
            font=BODY_FONT,
        ).pack(pady=8)
        row = tk.Frame(panel, bg=PANEL_2)
        row.pack(pady=12)
        self._button(row, "VOLTAR", self.show_menu).pack(side="left", padx=6)
        self._button(row, "FECHAR", self.close, accent=True).pack(side="left", padx=6)

    def show_hub(self):
        self.clear_screen()
        self.current_screen = "hub"
        self.hovered_island = None
        c = tk.Canvas(self.window, bg=BG, highlightthickness=0)
        c.pack(fill="both", expand=True)
        self.hub_canvas = c
        c.bind("<Configure>", lambda _e: self._schedule_render(self._render_hub, 55))
        self._schedule_render(self._render_hub, 10)

    def _render_hub(self):
        c = getattr(self, "hub_canvas", None)
        if not c or not c.winfo_exists():
            return
        w = max(960, c.winfo_width())
        h = max(620, c.winfo_height())
        c.delete("all")
        self.hub_island_items = {}
        draw_starfield(c, w, h, seed=31, clouds=True)
        c.create_text(
            w / 2, 28, text="STAR WORLD", fill=TEXT, font=PIXEL_TITLE, anchor="n"
        )
        c.create_text(
            w / 2, 58, text="O MUNDO DA STAR", fill=SOFT, font=SMALL_BOLD, anchor="n"
        )

        # MENU e CHAT usam IDs reais do Canvas; não dependem de tags com espaços.
        self._canvas_button(c, 20, 20, 100, 38, "← MENU", self.show_menu)
        self._canvas_button(
            c,
            w - 118,
            h - 72,
            96,
            50,
            "◯ CHAT",
            self.show_chat,
            fill="#151426",
            fg=PINK,
        )

        c.create_text(
            w - 28,
            26,
            text=f"● {self._status_text()}",
            fill=BLUE,
            anchor="ne",
            font=SMALL_BOLD,
        )
        for idx, (key, item) in enumerate(get_islands().items()):
            rx, ry = self.ISLAND_POSITIONS[idx]
            self._draw_island(c, key, item, int(w * rx), int(h * ry))
        c.create_text(
            w / 2,
            h - 28,
            text="SELECIONE UMA ILHA PARA EXPLORAR",
            fill=MUTED,
            font=SMALL_BOLD,
        )

    def _canvas_button(self, c, x, y, width, height, text, command, fill=PANEL, fg=TEXT):
        shape = round_rect(
            c,
            x,
            y,
            x + width,
            y + height,
            radius=height / 2,
            fill=fill,
            outline=BORDER,
            width=1,
        )
        label = c.create_text(
            x + width / 2,
            y + height / 2,
            text=text,
            fill=fg,
            font=BODY_BOLD,
        )

        def enter(_event):
            c.config(cursor="hand2")

        def leave(_event):
            c.config(cursor="arrow")

        def click(_event):
            if command:
                command()

        for item in (shape, label):
            c.tag_bind(item, "<Button-1>", click)
            c.tag_bind(item, "<Enter>", enter)
            c.tag_bind(item, "<Leave>", leave)
            c.tag_raise(item)

    def _draw_island(self, c, key, item, x, y):
        body, accent = self.ISLAND_COLORS.get(key, ("#D9E7F7", BLUE))
        tag = f"island_{key}"
        c.create_oval(
            x - 56, y + 20, x + 56, y + 46,
            fill="#071025", outline="#1D2A50", width=2, tags=tag,
        )
        glow = c.create_oval(
            x - 70, y - 46, x + 70, y + 78,
            fill="", outline=accent, width=2, state="hidden", tags=tag,
        )
        c.create_polygon(
            x - 54, y + 18, x - 38, y - 2, x + 38, y - 2,
            x + 54, y + 18, x + 28, y + 36, x - 30, y + 36,
            fill="#1A263A", outline="#2F4765", tags=tag,
        )
        s = 6
        c.create_rectangle(
            x - 4*s, y - 4*s, x + 4*s, y + 3*s,
            fill=body, outline="", tags=tag,
        )
        c.create_rectangle(
            x - 2*s, y - 6*s, x + 2*s, y - 4*s,
            fill=accent, outline="", tags=tag,
        )
        c.create_rectangle(
            x - 2*s, y - s, x - s, y + 2*s,
            fill=accent, outline="", tags=tag,
        )
        c.create_rectangle(
            x + s, y - s, x + 2*s, y + 2*s,
            fill=accent, outline="", tags=tag,
        )
        name = c.create_text(
            x,
            y + 68,
            text=item["name"].upper(),
            fill=TEXT,
            font=PIXEL_LABEL,
            state="hidden",
            tags=tag,
        )
        status = c.create_text(
            x,
            y + 87,
            text=status_label(item.get("status")),
            fill=GOLD if item.get("status") != "available" else GREEN,
            font=("Courier New", 6, "bold"),
            state="hidden",
            tags=tag,
        )
        self.hub_island_items[key] = (glow, name, status)
        c.tag_bind(tag, "<Enter>", lambda _e, k=key: self._hub_hover(k, True))
        c.tag_bind(tag, "<Leave>", lambda _e, k=key: self._hub_hover(k, False))
        c.tag_bind(tag, "<Button-1>", lambda _e, k=key: self._open_island_modal(k))

    def _hub_hover(self, key, visible):
        c = getattr(self, "hub_canvas", None)
        items = self.hub_island_items.get(key)
        if not c or not items:
            return
        for item in items:
            try:
                c.itemconfigure(item, state="normal" if visible else "hidden")
            except tk.TclError:
                pass
        c.config(cursor="hand2" if visible else "arrow")

    def _open_island_modal(self, key):
        item = get_islands().get(key)
        if not item:
            return
        overlay = tk.Frame(self.window, bg="#030710")
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        card = tk.Frame(
            overlay, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1
        )
        card.place(relx=.5, rely=.5, anchor="center", width=540, height=470)
        tk.Label(
            card, text=item["icon"], bg=PANEL_2, fg=BLUE_SOFT,
            font=("Segoe UI Emoji", 35),
        ).pack(pady=(28, 4))
        tk.Label(
            card,
            text=status_label(item.get("status")),
            bg=PANEL_2,
            fg=GOLD if item.get("status") != "available" else GREEN,
            font=SMALL_BOLD,
        ).pack()
        tk.Label(
            card, text=item["name"].upper(), bg=PANEL_2, fg=TEXT, font=PIXEL_TITLE
        ).pack(pady=(8, 10))
        tk.Label(
            card,
            text=item["description"],
            bg=PANEL_2,
            fg=TEXT,
            font=BODY_FONT,
            wraplength=450,
            justify="center",
        ).pack(padx=24)
        tags = tk.Frame(card, bg=PANEL_2)
        tags.pack(pady=14)
        for value in item.get("contents", [])[:4]:
            tk.Label(
                tags,
                text=str(value).split("/")[0],
                bg=PANEL_3,
                fg=MUTED,
                font=SMALL_FONT,
                padx=8,
                pady=5,
            ).pack(side="left", padx=3)
        msg = (
            "A sala 2D já pode ser aberta; recursos avançados continuam "
            "identificados pelo estado real da Foundation."
        )
        if key == "laboratorio":
            msg = (
                "No Laboratório eu investigo; na Central de Criação eu construo. "
                "O mesmo projeto pode atravessar os dois ambientes."
            )
        if key == "cura":
            msg = (
                "Cura diagnostica e organiza correções, mas não recebe liberdade "
                "irrestrita para alterar meu sistema."
            )
        tk.Label(
            card,
            text=f"STAR · {msg}",
            bg="#151D2F",
            fg=TEXT,
            font=BODY_FONT,
            wraplength=430,
            justify="left",
            padx=14,
            pady=12,
        ).pack(fill="x", padx=24, pady=8)
        row = tk.Frame(card, bg=PANEL_2)
        row.pack(side="bottom", pady=22)
        self._button(row, "VOLTAR", overlay.destroy, subtle=True).pack(
            side="left", padx=5
        )
        action = self._island_action(key)
        self._button(
            row,
            "ENTRAR",
            lambda: (overlay.destroy(), action()),
            accent=True,
        ).pack(side="left", padx=5)

    def _island_action(self, key):
        return {
            "casa": self.show_house,
            "laboratorio": self.show_laboratory,
            "biblioteca": self.show_library,
            "estudio_musica": self.show_music_studio,
            "atelie": self.show_atelier,
            "jardim": self.show_garden,
            "correio": self.show_mail,
            "cura": self.show_cura,
            "herois": self.show_heroes,
            "idiomas": self.show_languages,
        }[key]
