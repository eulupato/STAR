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

class WorkspaceMixin:
    def show_laboratory(self): self._project_workspace("LABORATÓRIO","laboratory",self.show_hub,"investigation")

    def show_creation_center(self): self._project_workspace("CENTRAL DE CRIAÇÃO",None,self.show_laboratory,"build")

    def _project_workspace(self,title,reference,back,phase):
        self.current_screen="laboratory" if phase=="investigation" else "creation_center"; _root,content=self._scene(title,"STAR WORLD" if phase=="investigation" else "LABORATÓRIO",back,reference,subtitle="INVESTIGAR" if phase=="investigation" else "CONSTRUIR")
        left=tk.Frame(content,bg=PANEL_2,width=330,highlightbackground=BORDER,highlightthickness=1); left.pack(side="left",fill="y",padx=(0,8),pady=8); left.pack_propagate(False); tk.Label(left,text="PROJETOS COMPARTILHADOS",bg=PANEL_2,fg=PINK if phase=="build" else BLUE,font=PIXEL_LABEL).pack(pady=14)
        projects=self.world.get("shared_projects",[])
        editor=tk.Frame(content,bg=PANEL_2,highlightbackground=BORDER,highlightthickness=1); editor.pack(side="right",fill="both",expand=True,padx=(8,0),pady=8)
        if reference:
            banner=self._image_banner(editor,reference,(650,180))
            if banner: banner.pack(fill="x",padx=18,pady=(16,2))
        title_e=self._labeled_entry(editor,"Nome do projeto"); objective=self._labeled_entry(editor,"Objetivo"); hypothesis=self._labeled_entry(editor,"Hipótese / plano"); notes=self._labeled_entry(editor,"Observações / versão")
        selected={"index":None}
        def select(i):
            p=self.world.get("shared_projects",[])[i]; selected["index"]=i
            for e,k in ((title_e,"name"),(objective,"objective"),(hypothesis,"hypothesis"),(notes,"notes")): e.delete(0,tk.END); e.insert(0,p.get(k,""))
        for i,p in enumerate(projects): self._button(left,p.get("name","Projeto"),lambda n=i:select(n),subtle=True).pack(fill="x",padx=10,pady=3)
        def save():
            item={"id":str(int(time.time()*1000)),"name":title_e.get().strip() or "Projeto sem título","objective":objective.get().strip(),"hypothesis":hypothesis.get().strip(),"notes":notes.get().strip(),"phase":phase,"status":"EM DESENVOLVIMENTO"}
            if selected["index"] is None:self.world.append("shared_projects",item)
            else:
                old=self.world.get("shared_projects",[])[selected["index"]]; item["id"]=old.get("id",item["id"]); self.world.replace_list_item("shared_projects",selected["index"],item)
            self._project_workspace(title,reference,back,phase)
        row=tk.Frame(editor,bg=PANEL_2); row.pack(anchor="w",padx=18,pady=16); self._button(row,"SALVAR PROJETO",save,accent=True).pack(side="left",padx=4)
        if phase=="investigation": self._button(row,"IR PARA CENTRAL DE CRIAÇÃO",self.show_creation_center).pack(side="left",padx=4)
        else:self._button(row,"VOLTAR À INVESTIGAÇÃO",self.show_laboratory).pack(side="left",padx=4)
        tk.Label(editor,text="Este workspace registra ideias, hipóteses, observações e versões. Não fornece procedimentos perigosos nem substitui validação técnica real.",bg=PANEL_2,fg=MUTED,font=SMALL_FONT,wraplength=600,justify="left").pack(anchor="w",padx=18,pady=8)

    def _labeled_entry(self,parent,label):
        tk.Label(parent,text=label.upper(),bg=PANEL_2,fg=MUTED,font=SMALL_BOLD).pack(anchor="w",padx=18,pady=(14,4)); e=tk.Entry(parent,bg=PANEL_3,fg=TEXT,insertbackground=TEXT,relief=tk.FLAT,font=BODY_FONT); e.pack(fill="x",padx=18,ipady=7); return e

    def show_library(self):
        self.current_screen="library"; _root,content=self._scene("BIBLIOTECA","STAR WORLD",self.show_hub,"library",subtitle="PDFs locais · leitura · progresso · Knowledge Packs")
        panel=tk.Frame(content,bg="#09111D",highlightbackground=BORDER,highlightthickness=1); panel.pack(fill="both",expand=True,padx=60,pady=10)
        banner=self._image_banner(panel,"library",(880,250))
        if banner: banner.pack(fill="x",padx=16,pady=(16,4))
        top=tk.Frame(panel,bg=PANEL_2); top.pack(fill="x",padx=16,pady=14); self._button(top,"IMPORTAR PDF",self._import_pdf,accent=True).pack(side="left"); tk.Label(top,text="LER COM A STAR: leitura TTS de PDF ainda não faz parte da Foundation.",bg=PANEL_2,fg=GOLD,font=SMALL_FONT).pack(side="right")
        for i,item in enumerate(self.world.get("library",[])):
            row=tk.Frame(panel,bg=PANEL_3); row.pack(fill="x",padx=16,pady=4); tk.Label(row,text=item.get("title","PDF"),bg=PANEL_3,fg=TEXT,font=BODY_BOLD).pack(side="left",padx=10,pady=8); tk.Label(row,text=f"Progresso: {item.get('progress',0)}%",bg=PANEL_3,fg=MUTED,font=SMALL_FONT).pack(side="left",padx=8); self._button(row,"ABRIR",lambda x=item:self._open_local_file(x.get("path","")),subtle=True).pack(side="right",padx=4); self._button(row,"+10%",lambda n=i:self._library_progress(n),subtle=True).pack(side="right",padx=4)
        try: stats=self.brain.packs.stats()
        except Exception: stats={"packs":0,"entries":0}
        tk.Label(panel,text=f"Knowledge Packs ativos: {stats.get('packs',0)} · entradas: {stats.get('entries',0)}",bg=PANEL_2,fg=BLUE,font=SMALL_BOLD).pack(anchor="w",padx=18,pady=12)

    def _import_pdf(self):
        p=filedialog.askopenfilename(title="Adicionar PDF à Biblioteca",filetypes=[("PDF","*.pdf")])
        if not p:return
        self.world.append("library",{"title":Path(p).name,"path":p,"progress":0,"notes":""}); self.show_library()

    def _library_progress(self,index):
        items=self.world.get("library",[]); items[index]["progress"]=min(100,int(items[index].get("progress",0))+10); self.world.set("library",items); self.show_library()

    def _open_local_file(self, path):
        p=Path(path)
        if not p.exists():return
        try:
            if os.name=="nt": os.startfile(str(p))
            elif sys.platform=="darwin": subprocess.Popen(["open",str(p)])
            else: subprocess.Popen(["xdg-open",str(p)])
        except Exception: pass

    def show_music_studio(self):
        self.current_screen="studio"; _root,content=self._scene("ESTÚDIO DE MÚSICA","STAR WORLD",self.show_hub,subtitle="Projetos · letras · BPM · tonalidade · áudio local")
        left=tk.Frame(content,bg=PANEL_2,width=320,highlightbackground=BORDER,highlightthickness=1); left.pack(side="left",fill="y",padx=(0,8),pady=8); left.pack_propagate(False); tk.Label(left,text="PROJETOS",bg=PANEL_2,fg=PINK,font=PIXEL_LABEL).pack(pady=14)
        for p in self.world.get("music_projects",[]): tk.Label(left,text=f"♪ {p.get('title','Sem título')} · {p.get('bpm','?')} BPM",bg=PANEL_3,fg=TEXT,font=BODY_FONT,padx=8,pady=8).pack(fill="x",padx=10,pady=3)
        editor=tk.Frame(content,bg=PANEL_2,highlightbackground=BORDER,highlightthickness=1); editor.pack(side="right",fill="both",expand=True,padx=(8,0),pady=8); title=self._labeled_entry(editor,"Título"); bpm=self._labeled_entry(editor,"BPM"); key=self._labeled_entry(editor,"Tonalidade"); tk.Label(editor,text="LETRA / NOTAS",bg=PANEL_2,fg=MUTED,font=SMALL_BOLD).pack(anchor="w",padx=18,pady=(14,4)); lyrics=tk.Text(editor,bg=PANEL_3,fg=TEXT,insertbackground=TEXT,height=10,relief=tk.FLAT,font=BODY_FONT); lyrics.pack(fill="both",expand=True,padx=18)
        def save(): self.world.append("music_projects",{"id":str(time.time()),"title":title.get().strip() or "Projeto musical","bpm":bpm.get().strip(),"key":key.get().strip(),"lyrics":lyrics.get("1.0",tk.END).strip()}); self.show_music_studio()
        self._button(editor,"SALVAR PROJETO",save,accent=True).pack(anchor="w",padx=18,pady=14); tk.Label(editor,text="DAW profissional e processamento avançado de áudio continuam EM DESENVOLVIMENTO.",bg=PANEL_2,fg=GOLD,font=SMALL_FONT).pack(anchor="w",padx=18,pady=(0,12))

    def show_atelier(self):
        self.current_screen="atelier"; _root,content=self._scene("ATELIÊ","STAR WORLD",self.show_hub,subtitle="Pixel art · paleta · ideias visuais")
        canvas=tk.Canvas(content,bg="#0B0F18",width=540,height=540,highlightbackground=BORDER,highlightthickness=1); canvas.pack(side="left",padx=20,pady=8); data=self.world.get("pixel_art",{"size":16,"points":{}}); size=int(data.get("size",16)); cell=30; ox=25; oy=25
        def redraw():
            canvas.delete("all"); points=self.world.get("pixel_art",{}).get("points",{})
            for y in range(size):
                for x in range(size):
                    color=points.get(f"{x},{y}","#111827"); canvas.create_rectangle(ox+x*cell,oy+y*cell,ox+(x+1)*cell,oy+(y+1)*cell,fill=color,outline="#26334A")
        def paint(event):
            x=(event.x-ox)//cell; y=(event.y-oy)//cell
            if 0<=x<size and 0<=y<size:
                art=self.world.get("pixel_art",{"size":size,"points":{}}); art.setdefault("points",{})[f"{x},{y}"]=self.atelier_color; self.world.set("pixel_art",art); redraw()
        canvas.bind("<Button-1>",paint); redraw()
        tools=tk.Frame(content,bg=PANEL_2,width=290); tools.pack(side="right",fill="y",padx=10,pady=8); tools.pack_propagate(False); tk.Label(tools,text="PALETA",bg=PANEL_2,fg=PINK,font=PIXEL_LABEL).pack(pady=16)
        for color,name in ((PINK,"ROSA"),(BLUE,"AZUL"),(GOLD,"AMARELO"),(WHITE,"BRANCO"),("#111827","BORRACHA")): self._button(tools,name,lambda c=color:setattr(self,"atelier_color",c),subtle=True).pack(fill="x",padx=16,pady=3)
        self._button(tools,"LIMPAR",lambda:(self.world.set("pixel_art",{"size":16,"points":{}}),redraw())).pack(fill="x",padx=16,pady=(20,3)); tk.Label(tools,text="Canvas simples e funcional. Ferramentas profissionais de design permanecem fora desta fase.",bg=PANEL_2,fg=MUTED,font=SMALL_FONT,wraplength=245,justify="left").pack(padx=16,pady=18)
