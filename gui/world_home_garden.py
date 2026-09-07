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

class HomeGardenMixin:
    def show_house(self):
        self.current_screen="house"; _root, content=self._scene("CASA DA STAR","STAR WORLD",self.show_hub,subtitle="Sala · Cozinha · Quarto")
        grid=tk.Frame(content,bg=BG); grid.place(relx=.5,rely=.5,anchor="center")
        for i,(icon,title,desc,cmd) in enumerate((("📺","SALA","TV, YouTube e descanso.",self.show_living_room),("🍳","COZINHA","Receitas e preparo guiado.",self.show_kitchen),("🛏️","QUARTO","Espaço pessoal e Closet.",self.show_bedroom))):
            card=tk.Frame(grid,bg=PANEL_2,width=270,height=230,highlightbackground=BORDER,highlightthickness=1); card.grid(row=0,column=i,padx=9); card.grid_propagate(False)
            tk.Label(card,text=icon,bg=PANEL_2,fg=BLUE_SOFT,font=("Segoe UI Emoji",34)).pack(pady=(28,8)); tk.Label(card,text=title,bg=PANEL_2,fg=TEXT,font=PIXEL_LABEL).pack(); tk.Label(card,text=desc,bg=PANEL_2,fg=MUTED,font=BODY_FONT,wraplength=220).pack(pady=12); self._button(card,"ENTRAR",cmd,accent=i==0).pack()

    def show_living_room(self):
        self.current_screen="living_room"; _root,content=self._scene("SALA","CASA",self.show_house,subtitle="STAR TV · YouTube")
        left=tk.Frame(content,bg="#101727",highlightbackground=BORDER,highlightthickness=1); left.pack(side="left",fill="both",expand=True,padx=(0,10),pady=15)
        tv=tk.Canvas(left,bg="#070A10",height=320,highlightthickness=0); tv.pack(fill="x",padx=26,pady=(25,12)); tv.create_rectangle(35,30,625,280,fill="#05070C",outline=BLUE,width=3); tv.create_text(330,150,text="STAR TV",fill=BLUE,font=("Courier New",22,"bold")); tv.create_rectangle(280,282,380,300,fill="#26344C",outline="")
        tk.Label(left,text="Cole um link do YouTube. A V1.9 abre o player web oficial no navegador; nenhum dado privado é inventado.",bg="#101727",fg=MUTED,font=BODY_FONT,wraplength=620).pack(padx=26,pady=8)
        row=tk.Frame(left,bg="#101727"); row.pack(fill="x",padx=26,pady=10); entry=tk.Entry(row,bg=PANEL_3,fg=TEXT,insertbackground=TEXT,relief=tk.FLAT,font=BODY_FONT); entry.pack(side="left",fill="x",expand=True,ipady=8)
        self._button(row,"ABRIR",lambda:self._open_youtube(entry.get()),accent=True).pack(side="left",padx=6); self._button(row,"★",lambda:self._favorite_youtube(entry.get())).pack(side="left")
        right=tk.Frame(content,bg=PANEL_2,width=280); right.pack(side="right",fill="y",pady=15); right.pack_propagate(False); tk.Label(right,text="FAVORITOS",bg=PANEL_2,fg=PINK,font=PIXEL_LABEL).pack(pady=(18,8))
        for url in self.world.get("tv_favorites",[])[:10]: self._button(right,url[-28:],lambda u=url:self._open_youtube(u),subtle=True).pack(fill="x",padx=12,pady=3)

    def _valid_youtube(self, url):
        try:
            parsed=urlparse(url.strip()); host=(parsed.hostname or "").lower(); return parsed.scheme in {"http","https"} and (host=="youtu.be" or host.endswith("youtube.com"))
        except Exception: return False

    def _open_youtube(self,url):
        if not self._valid_youtube(url): return self._notice("STAR TV","Use um link válido de youtube.com ou youtu.be.")
        webbrowser.open(url.strip())

    def _favorite_youtube(self,url):
        if not self._valid_youtube(url): return self._notice("STAR TV","O favorito precisa ser um link válido do YouTube.")
        self.world.toggle_in_list("tv_favorites",url.strip()); self.show_living_room()

    def show_kitchen(self):
        self.current_screen="kitchen"; _root,content=self._scene("COZINHA","CASA",self.show_house,"kitchen",subtitle="Receitas · preparo guiado")
        panel=tk.Frame(content,bg="#09111D",highlightbackground=BORDER,highlightthickness=1); panel.pack(side="right",fill="y",padx=10,pady=8); tk.Label(panel,text="LIVRO DE RECEITAS",bg=PANEL_2,fg=GOLD,font=PIXEL_LABEL).pack(padx=16,pady=(16,8))
        for recipe in self.world.get("recipes",[]):
            self._button(panel,recipe["name"],lambda r=recipe:self._show_recipe(r),subtle=True).pack(fill="x",padx=12,pady=3)
        info=tk.Frame(content,bg="#09111D",highlightbackground=BORDER,highlightthickness=1); info.pack(side="left",fill="both",expand=True,padx=10,pady=8)
        banner=self._image_banner(info,"kitchen",(650,300))
        if banner: banner.pack(fill="x",padx=14,pady=(14,6))
        tk.Label(info,text="STAR COOKING",bg="#09111D",fg=PINK,font=PIXEL_TITLE).pack(pady=(10,8)); tk.Label(info,text="Escolha uma receita. O modo de preparo mantém checklist e etapa atual sem bloquear a interface.",bg="#09111D",fg=TEXT,font=BODY_FONT,wraplength=520,justify="center").pack()

    def _show_recipe(self,recipe):
        self.clear_screen(); self.current_screen="recipe"; root=tk.Frame(self.window,bg=BG); root.pack(fill="both",expand=True); self._button(root,"← COZINHA",self.show_kitchen,subtle=True).pack(anchor="w",padx=20,pady=20)
        body=tk.Frame(root,bg=PANEL_2,highlightbackground=BORDER,highlightthickness=1); body.pack(fill="both",expand=True,padx=100,pady=(5,60)); tk.Label(body,text=recipe["name"].upper(),bg=PANEL_2,fg=TEXT,font=PIXEL_TITLE).pack(pady=(28,8)); tk.Label(body,text=f"{recipe['category']} · {recipe['time']} · {recipe['difficulty']}",bg=PANEL_2,fg=GOLD,font=SMALL_BOLD).pack()
        cols=tk.Frame(body,bg=PANEL_2); cols.pack(fill="both",expand=True,padx=30,pady=25); left=tk.Frame(cols,bg=PANEL_3); left.pack(side="left",fill="both",expand=True,padx=(0,8)); tk.Label(left,text="INGREDIENTES",bg=PANEL_3,fg=PINK,font=PIXEL_LABEL).pack(pady=12)
        for x in recipe["ingredients"]: tk.Label(left,text=f"□ {x}",bg=PANEL_3,fg=TEXT,font=BODY_FONT,anchor="w").pack(fill="x",padx=16,pady=3)
        right=tk.Frame(cols,bg=PANEL_3); right.pack(side="right",fill="both",expand=True,padx=(8,0)); tk.Label(right,text="ETAPAS",bg=PANEL_3,fg=BLUE,font=PIXEL_LABEL).pack(pady=12)
        for i,x in enumerate(recipe["steps"],1): tk.Label(right,text=f"{i}. {x}",bg=PANEL_3,fg=TEXT,font=BODY_FONT,wraplength=420,justify="left",anchor="w").pack(fill="x",padx=16,pady=3)
        self._button(body,"COMEÇAR RECEITA",lambda:self._cooking_mode(recipe),accent=True).pack(pady=(0,22))

    def _cooking_mode(self,recipe):
        self.clear_screen(); self.current_screen="cooking"; root=tk.Frame(self.window,bg=BG); root.pack(fill="both",expand=True)
        state={"step":0,"checked":set()}; tk.Label(root,text=f"COZINHANDO · {recipe['name'].upper()}",bg=BG,fg=TEXT,font=PIXEL_TITLE).pack(pady=(48,12)); progress=tk.Label(root,bg=BG,fg=GOLD,font=SMALL_BOLD); progress.pack(); step=tk.Label(root,bg=PANEL_2,fg=TEXT,font=("Segoe UI",16,"bold"),wraplength=720,justify="center",padx=30,pady=35); step.pack(padx=100,pady=20,fill="x")
        checklist=tk.Frame(root,bg=BG); checklist.pack(); vars=[]
        for ing in recipe["ingredients"]:
            v=tk.BooleanVar(); vars.append(v); tk.Checkbutton(checklist,text=ing,variable=v,bg=BG,fg=TEXT,selectcolor=PANEL_3,activebackground=BG,activeforeground=TEXT,font=BODY_FONT).pack(anchor="w")
        def refresh(): progress.config(text=f"ETAPA {state['step']+1} / {len(recipe['steps'])}"); step.config(text=recipe["steps"][state["step"]])
        def move(delta): state["step"]=max(0,min(len(recipe["steps"])-1,state["step"]+delta)); refresh()
        row=tk.Frame(root,bg=BG); row.pack(pady=20); self._button(row,"← ANTERIOR",lambda:move(-1)).pack(side="left",padx=5); self._button(row,"PRÓXIMA →",lambda:move(1),accent=True).pack(side="left",padx=5); self._button(row,"ENCERRAR",self.show_kitchen,subtle=True).pack(side="left",padx=5); refresh()

    def show_bedroom(self):
        self.current_screen="bedroom"; _root,content=self._scene("QUARTO","CASA",self.show_house,subtitle="Espaço pessoal · Closet")
        panel=tk.Frame(content,bg=PANEL_2,highlightbackground=BORDER,highlightthickness=1); panel.place(relx=.5,rely=.5,anchor="center",width=650,height=330); tk.Label(panel,text="🛏️",bg=PANEL_2,fg=BLUE_SOFT,font=("Segoe UI Emoji",44)).pack(pady=(42,8)); tk.Label(panel,text="QUARTO DA STAR",bg=PANEL_2,fg=TEXT,font=PIXEL_TITLE).pack(); tk.Label(panel,text="Descanso, objetos pessoais e uma divisão dedicada ao Closet.",bg=PANEL_2,fg=MUTED,font=BODY_FONT).pack(pady=12); self._button(panel,"ABRIR CLOSET",self.show_closet,accent=True).pack(pady=15)

    def show_closet(self):
        self.clear_screen(); self.current_screen="closet"; root=tk.Frame(self.window,bg=BG); root.pack(fill="both",expand=True); self._button(root,"← QUARTO",self.show_bedroom,subtle=True).pack(anchor="w",padx=20,pady=20); tk.Label(root,text="CLOSET",bg=BG,fg=TEXT,font=PIXEL_TITLE).pack(); tk.Label(root,text="Skins mudam a aparência; não mudam a identidade da STAR.",bg=BG,fg=MUTED,font=BODY_FONT).pack(pady=4)
        files=[p for p in sorted((PROJECT_ROOT/"SKINS").glob("*")) if p.suffix.lower() in {".png",".jpg",".jpeg",".webp"}]; self.closet_files=files
        if not files: return tk.Label(root,text="Nenhuma skin encontrada em SKINS/.",bg=BG,fg=RED,font=BODY_BOLD).pack(pady=80)
        try:self.closet_index=[p.name for p in files].index(self.selected_skin)
        except ValueError:self.closet_index=0
        area=tk.Frame(root,bg=PANEL_2,highlightbackground=BORDER,highlightthickness=1); area.pack(pady=22,ipadx=16,ipady=10); self.closet_image=tk.Label(area,bg=PANEL_2); self.closet_image.pack(padx=20,pady=10); self.closet_name=tk.Label(area,bg=PANEL_2,fg=TEXT,font=PIXEL_LABEL); self.closet_name.pack(); self.closet_state=tk.Label(area,bg=PANEL_2,fg=GREEN,font=SMALL_BOLD); self.closet_state.pack(pady=5)
        nav=tk.Frame(root,bg=BG); nav.pack(); self._button(nav,"◀",lambda:self._change_skin(-1)).pack(side="left",padx=5); self.select_skin_button=self._button(nav,"SELECIONAR",self._select_skin,accent=True); self.select_skin_button.pack(side="left",padx=5); self._button(nav,"▶",lambda:self._change_skin(1)).pack(side="left",padx=5); self._render_skin()

    def _change_skin(self,d): self.closet_index=(self.closet_index+d)%len(self.closet_files); self._render_skin()
    def _select_skin(self): self.selected_skin=self.closet_files[self.closet_index].name; self._save_skin_selection(); self._render_skin()
    def _render_skin(self):
        p=self.closet_files[self.closet_index]; photo=self._photo(p,(340,330),fit=False,key=f"skin:{p}:{p.stat().st_mtime if p.exists() else 0}"); self.closet_photo=photo; self.closet_image.config(image=photo if photo else "",text="" if photo else "Imagem indisponível",fg=RED); self.closet_name.config(text=p.stem.replace("_"," ").title()); active=p.name==self.selected_skin; self.closet_state.config(text="✓ SKIN ATUAL" if active else f"{self.closet_index+1} de {len(self.closet_files)}"); self.select_skin_button.config(state=tk.DISABLED if active else tk.NORMAL,text="SKIN SELECIONADA" if active else "SELECIONAR")

    def show_garden(self):
        self.current_screen="garden"; _root,content=self._scene("JARDIM","STAR WORLD",self.show_hub,subtitle="Plantação · Natureza · Mar · Observatório")
        grid=tk.Frame(content,bg=BG); grid.place(relx=.5,rely=.5,anchor="center")
        options=(("🌿","PLANTAÇÃO","Plantas comestíveis e cultivo.",self.show_plantation),("🌳","NATUREZA","Fauna, flora e mundo real.",self.show_nature),("🌊","MAR","Vida aquática por profundidade.",self.show_sea),("🔭","OBSERVATÓRIO","Cosmos e classificação de realidade.",self.show_observatory))
        for i,(icon,title,desc,cmd) in enumerate(options):
            card=tk.Frame(grid,bg=PANEL_2,width=235,height=215,highlightbackground=BORDER,highlightthickness=1); card.grid(row=i//2,column=i%2,padx=8,pady=8); card.grid_propagate(False); tk.Label(card,text=icon,bg=PANEL_2,fg=GREEN,font=("Segoe UI Emoji",32)).pack(pady=(24,7)); tk.Label(card,text=title,bg=PANEL_2,fg=TEXT,font=PIXEL_LABEL).pack(); tk.Label(card,text=desc,bg=PANEL_2,fg=MUTED,font=BODY_FONT,wraplength=190).pack(pady=9); self._button(card,"EXPLORAR",cmd,accent=i==0).pack()
        tk.Label(content,text="🦦 OSHA · perto da água",bg=BG,fg=PINK,font=PIXEL_LABEL).place(relx=.78,rely=.82)

    def show_plantation(self):
        self.current_screen="plantation"; _root,content=self._scene("JARDIM / PLANTAÇÃO","JARDIM",self.show_garden,subtitle="Temperos · frutas · chás · legumes · verduras")
        body=self._scrollable(content); cultivation=self.world.get("cultivation",{})
        for plant in self.world.get("plants",[]):
            stage=cultivation.get(plant["id"],"não plantado"); card=self._card(body,f"{plant['name']} · {stage.upper()}",f"{plant['scientific']}\n{plant['category']}\nSol: {plant['sun']} · Água: {plant['water']}\nSolo: {plant['soil']}\nColheita: {plant['harvest']}\nUso: {plant['uses']}",GREEN); card.pack(fill="x",padx=40,pady=6); row=tk.Frame(card,bg=PANEL_2); row.pack(anchor="w",padx=14,pady=(0,12)); self._button(row,"PLANTAR",lambda p=plant:self._cultivate(p,"plantado"),subtle=True).pack(side="left",padx=3); self._button(row,"REGAR",lambda p=plant:self._cultivate(p,"regado"),subtle=True).pack(side="left",padx=3); self._button(row,"COLHER",lambda p=plant:self._cultivate(p,"colhido"),subtle=True).pack(side="left",padx=3)

    def _cultivate(self,plant,stage):
        data=self.world.get("cultivation",{}); data[plant["id"]]=stage; self.world.set("cultivation",data); self.show_plantation()

    def show_nature(self):
        self.current_screen="nature"; _root,content=self._scene("NATUREZA","JARDIM",self.show_garden,subtitle="Fauna · flora · ecossistemas · contemplação")
        left=tk.Frame(content,bg=PANEL_2); left.pack(side="left",fill="both",expand=True,padx=(0,7),pady=8); tk.Label(left,text="FAUNA E FLORA",bg=PANEL_2,fg=GREEN,font=PIXEL_LABEL).pack(pady=12)
        for s in self.world.get("nature_species",[]): self._button(left,f"{s['kind']} · {s['name']}",lambda x=s:self._notice(x['name'],f"{x['scientific']}\nHabitat: {x['habitat']}\nPapel: {x['role']}"),subtle=True).pack(fill="x",padx=12,pady=3)
        right=tk.Frame(content,bg=PANEL_2); right.pack(side="right",fill="both",expand=True,padx=(7,0),pady=8); tk.Label(right,text="EXPLORAR O MUNDO",bg=PANEL_2,fg=BLUE,font=PIXEL_LABEL).pack(pady=12)
        for p in self.world.get("world_places",[]): self._button(right,p["name"],lambda x=p:self._notice(x['type'],f"{x['name']}\n{x['note']}"),subtle=True).pack(fill="x",padx=12,pady=3)

    def show_sea(self):
        self.current_screen="sea"; _root,content=self._scene("MAR","JARDIM",self.show_garden,subtitle="Costa · recifes · oceano · zona crepuscular · mar profundo")
        zones=["Todos","Costa / oceano","Recifes","Oceano aberto","Zona crepuscular","Mar profundo"]
        top=tk.Frame(content,bg=BG); top.pack(fill="x",pady=8); area=tk.Frame(content,bg=BG); area.pack(fill="both",expand=True)
        def render(zone):
            for w in area.winfo_children(): w.destroy()
            for s in self.world.get("marine_species",[]):
                if zone!="Todos" and s["zone"]!=zone: continue
                card=self._card(area,f"{s['name']} · {s['zone']}",f"{s['kind']}\n{s['note']}",BLUE); card.pack(fill="x",padx=50,pady=6)
        for z in zones: self._button(top,z,lambda x=z:render(x),subtle=True).pack(side="left",padx=3)
        render("Todos")

    def show_observatory(self):
        self.current_screen="observatory"; _root,content=self._scene("OBSERVATÓRIO","JARDIM",self.show_garden,"observatory",subtitle="Cosmos · astronomia · realidade classificada")
        visual=tk.Frame(content,bg=BG); visual.pack(side="left",fill="both",expand=True,padx=(0,8),pady=8)
        banner=self._image_banner(visual,"observatory",(760,430))
        if banner: banner.pack(fill="both",expand=True)
        panel=tk.Frame(content,bg="#07101B",highlightbackground=BORDER,highlightthickness=1); panel.pack(side="right",fill="y",padx=8,pady=8); tk.Label(panel,text="CATÁLOGO CELESTE",bg=PANEL_2,fg=BLUE,font=PIXEL_LABEL).pack(padx=14,pady=14)
        for obj in self.world.get("astronomy",[]): self._button(panel,f"[{obj['class']}] {obj['name']}",lambda x=obj:self._notice(x['name'],f"Classificação: {x['class']}\nCategoria: {x['category']}\n{x['note']}"),subtle=True).pack(fill="x",padx=10,pady=3)
        note=tk.Label(content,text="REAL · HISTÓRICO · HIPOTÉTICO · SIMULADO · FICTÍCIO · DESCONHECIDO",bg="#07101B",fg=GOLD,font=SMALL_BOLD,padx=16,pady=10); note.place(relx=.5,rely=.92,anchor="center")
