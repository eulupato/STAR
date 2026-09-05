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

class WorldSystemsMixin:
    def show_cura(self):
        self.current_screen="cura"; _root,content=self._scene("CURA","STAR WORLD",self.show_hub,"cura",subtitle="Diagnóstico · proposta · validação · teste")
        try: disk=shutil.disk_usage(PROJECT_ROOT); disk_text=f"{disk.free/1024**3:.1f} GB livres"
        except Exception: disk_text="DESCONHECIDO"
        try: packs=self.brain.packs.stats()
        except Exception: packs={"packs":0,"entries":0}
        diagnostics=[("CORE","ATIVO"),("MEMÓRIA","INICIALIZADA"),("STT","PRONTO" if self.voice.stt_configured else "NÃO INSTALADO"),("TTS",self.voice.mode.upper()),("KNOWLEDGE",f"{packs.get('packs',0)} packs / {packs.get('entries',0)} entradas"),("DISCO",disk_text),("SISTEMA",platform.system()),("DEVICE GATEWAY","OPT-IN" if not os.getenv("STAR_DEVICE_GATEWAY") else "SOLICITADO")]
        panel=tk.Frame(content,bg="#07101B",highlightbackground=BORDER,highlightthickness=1); panel.pack(fill="both",expand=True,padx=80,pady=12)
        banner=self._image_banner(panel,"cura",(820,240))
        if banner: banner.pack(fill="x",padx=18,pady=(18,4))
        tk.Label(panel,text="STAR STATUS · TELEMETRIA DISPONÍVEL",bg=PANEL_2,fg=BLUE,font=PIXEL_LABEL).pack(pady=14)
        for name,value in diagnostics:
            row=tk.Frame(panel,bg=PANEL_3); row.pack(fill="x",padx=18,pady=3); tk.Label(row,text=name,bg=PANEL_3,fg=MUTED,font=SMALL_BOLD).pack(side="left",padx=10,pady=8); tk.Label(row,text=value,bg=PANEL_3,fg=GREEN if value in {"ATIVO","INICIALIZADA","PRONTO"} else TEXT,font=BODY_BOLD).pack(side="right",padx=10)
        tk.Label(panel,text="CURA V1.9 não altera o sistema automaticamente. Fluxo: diagnóstico → identificação → proposta → validação → aplicação autorizada → teste.",bg=PANEL_2,fg=GOLD,font=BODY_FONT,wraplength=760,justify="center").pack(padx=20,pady=18)

    def show_mail(self):
        self.current_screen="mail"; _root,content=self._scene("CORREIOS","STAR WORLD",self.show_hub,subtitle="Encomendas · objetos · inventário")
        left=tk.Frame(content,bg=PANEL_2); left.pack(side="left",fill="both",expand=True,padx=(0,7),pady=8); tk.Label(left,text="ENCOMENDAS",bg=PANEL_2,fg=GOLD,font=PIXEL_LABEL).pack(pady=14)
        for item in self.world.get("mail",[]):
            row=tk.Frame(left,bg=PANEL_3); row.pack(fill="x",padx=12,pady=4); tk.Label(row,text=f"{'●' if item['status']=='unread' else '○'} {item['title']}",bg=PANEL_3,fg=TEXT,font=BODY_FONT).pack(side="left",padx=8,pady=8); self._button(row,"ABRIR",lambda x=item:self._open_package(x),subtle=True).pack(side="right",padx=5)
        right=tk.Frame(content,bg=PANEL_2); right.pack(side="right",fill="both",expand=True,padx=(7,0),pady=8); tk.Label(right,text="INVENTÁRIO",bg=PANEL_2,fg=PINK,font=PIXEL_LABEL).pack(pady=14)
        for item in self.world.get("inventory",[]): tk.Label(right,text=f"◆ {item.get('name')}",bg=PANEL_3,fg=TEXT,font=BODY_FONT,padx=10,pady=8).pack(fill="x",padx=12,pady=3)

    def _open_package(self,item):
        mail=self.world.get("mail",[])
        for x in mail:
            if x.get("id")==item.get("id"): x["status"]="read"
        inv=self.world.get("inventory",[])
        if not any(x.get("source")==item.get("id") for x in inv): inv.append({"name":item.get("item"),"source":item.get("id"),"description":item.get("description")})
        self.world.set("mail",mail); self.world.set("inventory",inv); self.show_mail(); self.window.after(60, lambda: self._notice(item.get("title"), item.get("description")))

    def show_heroes(self):
        self.current_screen="heroes"; _root,content=self._scene("HERÓIS","STAR WORLD",self.show_hub,subtitle="Catálogo especializado · Knowledge Packs")
        hero_dir=PROJECT_ROOT/"knowledge"/"packs"/"heroes"; installed=hero_dir.exists() and any(hero_dir.rglob("*.json*"))
        panel=tk.Frame(content,bg=PANEL_2,highlightbackground=BORDER,highlightthickness=1); panel.place(relx=.5,rely=.5,anchor="center",width=650,height=320); tk.Label(panel,text="🦸",bg=PANEL_2,fg=PINK,font=("Segoe UI Emoji",44)).pack(pady=(42,10)); tk.Label(panel,text="KNOWLEDGE PACK DETECTADO" if installed else "AGUARDANDO KNOWLEDGE PACK",bg=PANEL_2,fg=GREEN if installed else GOLD,font=PIXEL_LABEL).pack(); tk.Label(panel,text="A interface não inventa biografias para preencher lacunas. Quando o catálogo estruturado estiver disponível, esta ilha passa a exibir os dados reais do pack.",bg=PANEL_2,fg=TEXT,font=BODY_FONT,wraplength=540,justify="center").pack(pady=20)

    def show_languages(self):
        self.current_screen="languages"; _root,content=self._scene("IDIOMAS","STAR WORLD",self.show_hub,subtitle="Cartões · vocabulário · estudo local")
        body=self._scrollable(content)
        for lang in self.world.get("languages",[]):
            card=self._card(body,f"{lang['name']} · {lang['status']}","Cartões iniciais desta interface 2D.",BLUE); card.pack(fill="x",padx=60,pady=6); row=tk.Frame(card,bg=PANEL_2); row.pack(fill="x",padx=14,pady=(0,12))
            for front,back in lang.get("cards",[])[:5]: self._button(row,front,lambda a=front,b=back:self._notice(a,b),subtle=True).pack(side="left",padx=3)
