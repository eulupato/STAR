"""Parte modular dos ambientes funcionais do STAR WORLD 2D."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog
from urllib.parse import urlparse

from PIL import Image, ImageTk
from gui.theme import (BG, PANEL, PANEL_2, PANEL_3, BORDER, TEXT, MUTED, SOFT, GOLD, PINK, BLUE, BLUE_SOFT, GREEN, RED, WHITE, BODY_FONT, BODY_BOLD, SMALL_FONT, SMALL_BOLD, PIXEL_TITLE, PIXEL_LABEL, draw_starfield, round_rect)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class WorldSceneMixin:
    def _title(self, parent, title, subtitle=None):
        tk.Label(parent, text=title, fg=TEXT, bg=parent.cget("bg"), font=PIXEL_TITLE).pack(anchor="w")
        if subtitle: tk.Label(parent, text=subtitle, fg=MUTED, bg=parent.cget("bg"), font=BODY_FONT).pack(anchor="w", pady=(4, 0))

    def _card(self, parent, title, body="", accent=PINK):
        frame = tk.Frame(parent, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(frame, text=title, fg=accent, bg=PANEL_2, font=SMALL_BOLD).pack(anchor="w", padx=14, pady=(12, 4))
        if body: tk.Label(frame, text=body, fg=TEXT, bg=PANEL_2, font=BODY_FONT, wraplength=560, justify="left").pack(anchor="w", padx=14, pady=(0, 12))
        return frame

    def _scrollable(self, parent):
        outer = tk.Frame(parent, bg=BG); outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0); bar = tk.Scrollbar(outer, command=canvas.yview)
        body = tk.Frame(canvas, bg=BG); win = canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=bar.set); canvas.pack(side="left", fill="both", expand=True); bar.pack(side="right", fill="y")
        body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
        return body

    def _scene(self, title, back_text, back_command, reference=None, subtitle=None):
        self.clear_screen(); root = tk.Frame(self.window, bg=BG); root.pack(fill="both", expand=True)
        canvas = tk.Canvas(root, bg=BG, highlightthickness=0); canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        def render_bg():
            if not canvas.winfo_exists(): return
            w, h = max(960, canvas.winfo_width()), max(620, canvas.winfo_height()); canvas.delete("scene_bg")
            if reference:
                photo = self._photo(self._reference_path(reference), (w, h), fit=True, key=f"scene:{reference}:{w}x{h}")
                if photo: canvas.create_image(w/2, h/2, image=photo, tags="scene_bg")
                else: draw_starfield(canvas, w, h, seed=73, clouds=True)
            else: draw_starfield(canvas, w, h, seed=73, clouds=True)
            canvas.tag_lower("scene_bg")
        canvas.bind("<Configure>", lambda _e: self._schedule_render(render_bg, 60)); self._schedule_render(render_bg, 10)
        top = tk.Frame(root, bg="#080B12"); top.pack(fill="x", padx=20, pady=18)
        self._button(top, f"←  {back_text}", back_command, subtle=True).pack(side="left")
        box = tk.Frame(top, bg="#080B12"); box.pack(side="left", padx=24)
        tk.Label(box, text=title, fg=TEXT, bg="#080B12", font=PIXEL_TITLE).pack(anchor="w")
        if subtitle: tk.Label(box, text=subtitle, fg=MUTED, bg="#080B12", font=SMALL_FONT).pack(anchor="w")
        tk.Label(top, text=f"● {self._status_text()}", fg=BLUE, bg=PANEL, font=SMALL_BOLD, padx=11, pady=6).pack(side="right")
        content = tk.Frame(root, bg=BG); content.pack(fill="both", expand=True, padx=34, pady=(8, 28))
        return root, content

    def _image_banner(self, parent, reference, size=(720, 250)):
        """Mostra a arte canônica dentro da cena sem depender de transparência do Tk."""
        photo = self._photo(self._reference_path(reference), size, fit=True, key=f"banner:{reference}:{size[0]}x{size[1]}")
        if not photo:
            return None
        label = tk.Label(parent, image=photo, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        label.image = photo
        return label

    def _notice(self,title,text):
        overlay=tk.Frame(self.window,bg="#02050A");overlay.place(relx=0,rely=0,relwidth=1,relheight=1);card=tk.Frame(overlay,bg=PANEL_2,highlightbackground=BORDER,highlightthickness=1);card.place(relx=.5,rely=.5,anchor="center",width=500,height=280);tk.Label(card,text=title.upper(),bg=PANEL_2,fg=PINK,font=PIXEL_LABEL).pack(pady=(35,14));tk.Label(card,text=text,bg=PANEL_2,fg=TEXT,font=BODY_FONT,wraplength=420,justify="center").pack(padx=20);self._button(card,"OK",overlay.destroy,accent=True).pack(pady=24)
