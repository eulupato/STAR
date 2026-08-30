"""Interface gráfica da STAR V1.9.

A GUI não conhece detalhes de serviços de voz: usa VoiceManager, que mantém
STT e TTS locais isolados e rápidos. Todas as atualizações de widgets Tkinter
são feitas na thread principal por meio de response_queue.
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

from config import APP_NAME, VERSION, WINDOW_HEIGHT, WINDOW_WIDTH, MENU_HEIGHT, MENU_WIDTH
from core.avatar import AvatarManager
from core.emotion import EmotionManager
from database.memory import Memory
from voice.audio_input import AudioRecorder
from voice.manager import VoiceManager


class StarApp:
    def __init__(self, brain):
        self.brain = brain
        self.memory = Memory()
        self.avatar = AvatarManager()
        self.emotion = EmotionManager()
        self.voice = VoiceManager()
        self.recorder = AudioRecorder()
        self.online_mode = False
        self.processing = False
        self.recording = False
        self._closing = False
        self.response_queue: queue.Queue = queue.Queue()
        self.current_screen = "menu"
        self.has_messages = False
        self.chat = None
        self.voice_test_label = None
        self.avatar_photo = None
        self.closet_photo = None
        self.selected_skin = self._load_skin_selection()

        self.bg = "#0b1018"; self.panel = "#131c29"; self.text = "#edf3fb"; self.muted = "#9aa8bb"
        self.star = "#8fd0ff"; self.user = "#c9b8ff"; self.green = "#76e2a0"; self.red = "#ff7c87"; self.gold = "#ffd36e"

        self.window = tk.Tk()
        self.window.title(f"{APP_NAME} V{VERSION}")
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.window.minsize(900, 600)
        self.window.configure(bg=self.bg)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<F11>", self.toggle_maximize)
        self.window.bind("<Escape>", self.restore_normal_size)
        self.is_maximized = False
        self.normal_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.show_menu()
        self.window.after(60, self._check_response_queue)

    def _load_skin_selection(self):
        try:
            return json.loads((PROJECT_ROOT / "config_skin.json").read_text(encoding="utf-8")).get("skin", "original.jpeg")
        except Exception:
            return "original.jpeg"

    def _save_skin_selection(self):
        try:
            (PROJECT_ROOT / "config_skin.json").write_text(json.dumps({"skin": self.selected_skin}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def clear_screen(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        self.chat = None
        self.has_messages = False
        self.voice_test_label = None

    def _header(self, parent):
        header = tk.Frame(parent, bg="#172231", height=56); header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text="⭐  STAR", fg=self.star, bg="#172231", font=("Segoe UI", 20, "bold")).pack(side="left", padx=18)
        online = self.online_mode; status = "ONLINE" if online else "OFFLINE"; color = self.green if online else self.red
        self.status_label = tk.Label(header, text=f"● V{VERSION} • {status}", fg=color, bg="#172231", font=("Segoe UI", 9, "bold")); self.status_label.pack(side="right", padx=18)
        for text, cmd in (("⚙", self.show_settings), ("◈ ILHAS", self.show_islands), ("CHAT", self.show_chat), ("MENU", self.show_menu)):
            self._button(header, text, cmd, small=True).pack(side="right", padx=4, pady=8)

    def _gradient(self, parent):
        canvas = tk.Canvas(parent, bg=self.bg, highlightthickness=0); canvas.place(x=0, y=0, relwidth=1, relheight=1); canvas.tk.call("lower", str(canvas))
        def draw(_event=None):
            canvas.delete("gradient"); width=max(canvas.winfo_width(),1); height=max(canvas.winfo_height(),1)
            for i in range(70):
                t=i/69; r=int(12+25*(1-t)); g=int(18+50*(1-t)); b=int(28+90*(1-t)); y=int(i*height/70)
                canvas.create_rectangle(0,y,width,y+height/70+2,fill=f"#{r:02x}{g:02x}{b:02x}",outline="",tags="gradient")
        canvas.bind("<Configure>", draw); self.window.after(20, draw)

    def show_menu(self):
        self.clear_screen(); self.current_screen="menu"
        if not self.is_maximized: self.window.geometry(f"{MENU_WIDTH}x{MENU_HEIGHT}")
        frame=tk.Frame(self.window,bg=self.bg); frame.pack(fill="both",expand=True)
        tk.Label(frame,text="⭐  STAR",fg=self.star,bg=self.bg,font=("Segoe UI",34,"bold")).pack(pady=(120,20))
        tk.Label(frame,text="System for Thought, Analysis and Response",fg=self.muted,bg=self.bg,font=("Segoe UI",11)).pack(pady=(0,45))
        for label,cmd in (("INICIAR",self.show_chat),("CONFIGURAÇÕES",self.show_settings),("SAIR",self.close)): self._button(frame,label,cmd).pack(pady=7)

    def show_chat(self):
        self.clear_screen(); self.current_screen="chat"
        root=tk.Frame(self.window,bg=self.bg); root.pack(fill="both",expand=True); self._gradient(root); self._header(root)
        self.stage=tk.Frame(root,bg=self.bg); self.stage.pack(fill="both",expand=True)
        self.center=tk.Frame(self.stage,bg=self.bg); self.center.place(relx=.5,rely=.47,anchor="center")
        self.avatar_label=tk.Label(self.center,bg=self.bg); self.avatar_label.pack(); self._load_display_avatar()
        self._build_input(root); self.entry.focus_set()

    def _build_input(self,root):
        bottom=tk.Frame(root,bg=self.bg,height=92); bottom.pack(fill="x",side="bottom",padx=22,pady=(0,18)); bottom.pack_propagate(False)
        box=tk.Frame(bottom,bg="#cbd9e8",padx=1,pady=1); box.place(relx=.5,rely=.5,anchor="center",relwidth=.64,height=62)
        inner=tk.Frame(box,bg="#25364b"); inner.pack(fill="both",expand=True)
        tk.Label(inner,text="+",fg="#d8e7f5",bg="#25364b",font=("Segoe UI",23)).pack(side="left",padx=(16,8))
        self.entry=tk.Entry(inner,bg="#25364b",fg=self.text,insertbackground=self.text,relief=tk.FLAT,font=("Segoe UI",12)); self.entry.pack(side="left",fill="both",expand=True,pady=7)
        self.entry.insert(0,"Pergunte algo à STAR..."); self.entry.config(fg="#aebdcd")
        self.entry.bind("<FocusIn>",self._clear_placeholder); self.entry.bind("<FocusOut>",self._restore_placeholder); self.entry.bind("<Return>",self._on_enter)
        self.mic=tk.Button(inner,text="🎤",command=self.toggle_microphone,bg="#25364b",fg="#d8e7f5",relief=tk.FLAT,borderwidth=0,font=("Segoe UI",14),cursor="hand2"); self.mic.pack(side="right",padx=4)
        self.send_button=tk.Button(inner,text="➜",command=self.send_message,bg="#395574",fg="white",relief=tk.FLAT,borderwidth=0,font=("Segoe UI",16,"bold"),width=3,cursor="hand2"); self.send_button.pack(side="right",padx=(2,8),pady=7)

    def _clear_placeholder(self,_event=None):
        if self.entry.get()=="Pergunte algo à STAR...": self.entry.delete(0,tk.END); self.entry.config(fg=self.text)
    def _restore_placeholder(self,_event=None):
        if not self.entry.get().strip(): self.entry.insert(0,"Pergunte algo à STAR..."); self.entry.config(fg="#aebdcd")
    def _on_enter(self,_event=None): self.send_message(); return "break"

    def toggle_microphone(self):
        if not self.voice.stt_configured:
            self._append_system("🎤 O reconhecimento local ainda não está instalado. Execute INSTALAR_VOZ.bat."); return
        if not self.recorder.available:
            self._append_system("🎤 Não consegui acessar o microfone. Verifique as configurações de áudio do Windows."); return
        if not self.recording:
            try:
                self.recorder.start(); self.recording=True; self.mic.config(text="■",bg="#8b3340",fg="white"); self._activate_conversation(); self._append_system("🎤 Estou ouvindo. Clique novamente quando terminar."); self._set_status("OUVINDO",self.green)
            except Exception as exc: self._append_system(f"🎤 Erro ao abrir microfone: {exc}")
        else:
            self.recording=False; self.mic.config(text="🎤",bg="#25364b",fg="#d8e7f5"); self._set_status("TRANSCRIVENDO",self.gold); threading.Thread(target=self._finish_recording,daemon=True).start()

    def _finish_recording(self):
        path=None
        try:
            path=self.recorder.stop_to_wav(); text=self.voice.transcribe(path); self.response_queue.put(("transcript",text))
        except Exception as exc: self.response_queue.put(("voice_error",str(exc)))
        finally:
            if path:
                try:path.unlink(missing_ok=True)
                except Exception:pass

    def _activate_conversation(self):
        if self.has_messages or not hasattr(self,"stage"): return
        self.has_messages=True
        if hasattr(self,"center"):
            try:self.center.place_forget()
            except tk.TclError:pass
        self.chat=scrolledtext.ScrolledText(self.stage,wrap=tk.WORD,bg="#0e151f",fg=self.text,insertbackground=self.text,relief=tk.FLAT,borderwidth=0,font=("Segoe UI",11),padx=28,pady=22); self.chat.pack(fill="both",expand=True,padx=80,pady=(25,12)); self.chat.configure(state=tk.DISABLED)
        for tag,fg,font in (("user",self.user,("Segoe UI",10,"bold")),("star",self.star,("Segoe UI",10,"bold")),("message",self.text,("Segoe UI",11)),("system",self.muted,("Segoe UI",10))): self.chat.tag_configure(tag,foreground=fg,font=font)

    def send_message(self):
        if self.processing or not hasattr(self,"entry"): return
        text=self.entry.get().strip()
        if not text or text=="Pergunte algo à STAR...": return
        self.entry.delete(0,tk.END); self._activate_conversation(); self._append_user(text)
        try:self.memory.save("Você",text)
        except Exception:pass
        self.processing=True; self.entry.config(state=tk.DISABLED); self.send_button.config(state=tk.DISABLED); self._set_status("PROCESSANDO",self.gold); self._load_avatar("thinking")
        threading.Thread(target=self._process_message,args=(text,),daemon=True).start()

    def _process_message(self,text):
        try:self.response_queue.put(("success",self.brain.process(text)))
        except Exception as exc:self.response_queue.put(("error",str(exc)))

    def _check_response_queue(self):
        if self._closing:return
        try:
            while True:
                kind,result=self.response_queue.get_nowait()
                if kind=="transcript":
                    if self.current_screen=="chat" and hasattr(self,"entry"):
                        self.entry.config(state=tk.NORMAL); self.entry.delete(0,tk.END); self.entry.insert(0,str(result)); self.entry.config(fg=self.text); self.send_message()
                elif kind=="voice_error":
                    self._activate_conversation(); self._append_system(f"🎤 Falha no reconhecimento: {result}"); self.processing=False
                    if self.current_screen=="chat": self.entry.config(state=tk.NORMAL); self.send_button.config(state=tk.NORMAL)
                elif kind=="voice_test":
                    ok,error=result; msg="🔊 Voz da STAR funcionando." if ok else f"🔊 Falha na voz: {error}"; self._set_voice_test_message(msg,ok)
                elif kind=="speech_result":
                    ok,error=result
                    if not ok and self.current_screen=="chat": self._append_system(f"🔊 A resposta foi gerada, mas a voz falhou: {error}")
                    if self.current_screen=="chat": self._set_status("OFFLINE" if not self.online_mode else "ONLINE",self.red if not self.online_mode else self.green)
                elif kind=="success":
                    response=str(result); self._append_star(response)
                    try:self.memory.save("STAR",response)
                    except Exception:pass
                    self._load_avatar("speaking")
                    self.voice.speak_async(response,lambda ok,error:self.response_queue.put(("speech_result",(ok,error))))
                    self.processing=False
                    if self.current_screen=="chat": self.entry.config(state=tk.NORMAL); self.send_button.config(state=tk.NORMAL); self._set_status("FALANDO",self.green); self.entry.focus_set()
                elif kind=="error":
                    self._append_system(f"Erro ao processar: {result}"); self._load_avatar("neutral"); self.processing=False
                    if self.current_screen=="chat": self.entry.config(state=tk.NORMAL); self.send_button.config(state=tk.NORMAL)
        except queue.Empty:pass
        try:self.window.after(60,self._check_response_queue)
        except tk.TclError:pass

    def _set_voice_test_message(self,message,ok):
        label=self.voice_test_label
        if label is not None:
            try:
                if label.winfo_exists(): label.config(text=message,fg=self.green if ok else self.red); return
            except tk.TclError: pass
        if self.current_screen=="chat": self._append_system(message)

    def _append(self,name,text,tag):
        if not self.chat:return
        try:
            self.chat.configure(state=tk.NORMAL); self.chat.insert(tk.END,name+"\n",tag); self.chat.insert(tk.END,text+"\n\n","message"); self.chat.configure(state=tk.DISABLED); self.chat.see(tk.END)
        except tk.TclError:self.chat=None
    def _append_user(self,text):self._append("Você",text,"user")
    def _append_star(self,text):self._append("⭐ STAR",text,"star")
    def _append_system(self,text):self._append("SISTEMA",text,"system")

    def _load_display_avatar(self):
        path=PROJECT_ROOT/"SKINS"/self.selected_skin
        if path.exists():
            try:
                image=Image.open(path).convert("RGBA"); image.thumbnail((300,330),Image.Resampling.LANCZOS); self.avatar_photo=ImageTk.PhotoImage(image); self.avatar_label.config(image=self.avatar_photo,text=""); return
            except Exception:pass
        self._load_avatar("neutral")
    def _load_avatar(self,emotion="neutral"):
        path=self.avatar.avatar_dir/f"{emotion}.png"
        if not path.exists():path=self.avatar.avatar_dir/"neutral.png"
        try:
            image=Image.open(path).convert("RGBA"); image.thumbnail((250,250),Image.Resampling.LANCZOS); self.avatar_photo=ImageTk.PhotoImage(image); self.avatar_label.config(image=self.avatar_photo,text="")
        except Exception:
            try:self.avatar_label.config(text="⭐\nSTAR",fg=self.star,font=("Segoe UI",28,"bold"))
            except tk.TclError:pass
    def _set_status(self,text,color):
        label=getattr(self,"status_label",None)
        if label:
            try:label.config(text=f"● V{VERSION} • {text}",fg=color)
            except tk.TclError:pass

    def show_settings(self):
        self.clear_screen(); self.current_screen="settings"; root=tk.Frame(self.window,bg=self.bg); root.pack(fill="both",expand=True); self._header(root)
        body=tk.Frame(root,bg=self.bg); body.pack(fill="both",expand=True,padx=80,pady=35); tk.Label(body,text="CONFIGURAÇÕES",fg=self.star,bg=self.bg,font=("Segoe UI",27,"bold")).pack(anchor="w")
        mode=tk.Frame(body,bg=self.panel,padx=22,pady=18); mode.pack(fill="x",pady=(18,12)); tk.Label(mode,text="MODO DE FUNCIONAMENTO",fg=self.text,bg=self.panel,font=("Segoe UI",12,"bold")).pack(anchor="w")
        row=tk.Frame(mode,bg=self.panel); row.pack(anchor="w",pady=12); self.online_btn=self._button(row,"🟢 ONLINE",lambda:self._set_mode(True)); self.online_btn.pack(side="left",padx=(0,10)); self.offline_btn=self._button(row,"🔴 OFFLINE",lambda:self._set_mode(False)); self.offline_btn.pack(side="left"); self._refresh_mode_buttons()
        tk.Label(mode,text="O modo online controla recursos de internet. A voz da STAR continua local nos dois modos.",fg=self.muted,bg=self.panel).pack(anchor="w")
        voicebox=tk.Frame(body,bg=self.panel,padx=22,pady=18); voicebox.pack(fill="x",pady=12); tk.Label(voicebox,text="🎙️ VOZ DA STAR",fg=self.star,bg=self.panel,font=("Segoe UI",13,"bold")).pack(anchor="w")
        tk.Label(voicebox,text="Entrada: faster-whisper tiny • Voz rápida: Piper PT-BR • Voz clonada: Chatterbox",fg=self.text,bg=self.panel).pack(anchor="w",pady=(8,2)); tk.Label(voicebox,text="Piper é usado normalmente por ser muito mais leve. Chatterbox fica como modo opcional de voz clonada.",fg=self.muted,bg=self.panel).pack(anchor="w")
        self._button(voicebox,"TESTAR VOZ DA STAR",self._test_voice).pack(anchor="w",pady=(12,4)); self.voice_test_label=tk.Label(voicebox,text="Pronto para testar.",fg=self.muted,bg=self.panel,wraplength=760,justify="left"); self.voice_test_label.pack(anchor="w")
        info=tk.Frame(body,bg=self.panel,padx=22,pady=16); info.pack(fill="x",pady=12)
        for name,value in (("Versão",f"V{VERSION}"),("Conhecimento local","ATIVO"),("Voz rápida",self.voice.tts_description),("Reconhecimento local","PRONTO" if self.voice.stt_configured else "INSTALAÇÃO PENDENTE")):
            line=tk.Frame(info,bg=self.panel); line.pack(fill="x",pady=4); tk.Label(line,text=name,fg=self.muted,bg=self.panel).pack(side="left"); tk.Label(line,text=value,fg=self.green if value in {"ATIVO","PRONTO","Piper PT-BR (rápido)"} else self.gold,bg=self.panel,font=("Segoe UI",10,"bold")).pack(side="right")
        self._button(body,"VOLTAR AO CHAT",self.show_chat).pack(anchor="w",pady=10)

    def _test_voice(self):
        self._set_voice_test_message("🔊 Gerando teste da voz rápida...",True); self._set_status("TESTANDO VOZ",self.gold); self.voice.test_audio_async(lambda ok,error:self.response_queue.put(("voice_test",(ok,error))))
    def _set_mode(self,online):self.online_mode=bool(online); self._refresh_mode_buttons(); self._set_status("ONLINE" if self.online_mode else "OFFLINE",self.green if self.online_mode else self.red)
    def _refresh_mode_buttons(self):
        if hasattr(self,"online_btn"):self.online_btn.config(bg="#1f5a3a" if self.online_mode else "#24313f")
        if hasattr(self,"offline_btn"):self.offline_btn.config(bg="#5a2630")

    def show_islands(self):
        self.clear_screen(); self.current_screen="islands"; root=tk.Frame(self.window,bg=self.bg); root.pack(fill="both",expand=True); self._header(root); body=tk.Frame(root,bg=self.bg); body.pack(fill="both",expand=True,padx=35,pady=20); tk.Label(body,text="HUB • STAR WORLD",fg=self.star,bg=self.bg,font=("Segoe UI",24,"bold")).pack(anchor="w",pady=(0,12))
        try:
            from core.islands import get_islands; data=get_islands()
        except Exception:data={}
        for i,(key,item) in enumerate(data.items()):
            card=tk.Frame(body,bg=self.panel,padx=16,pady=14); card.grid(row=i//3,column=i%3,sticky="nsew",padx=6,pady=6); tk.Label(card,text=f"{item.get('icon','🏝️')} {item.get('name',key)}",fg=self.star,bg=self.panel,font=("Segoe UI",14,"bold")).pack(anchor="w"); tk.Label(card,text=item.get('description',''),fg=self.text,bg=self.panel,wraplength=270,justify="left").pack(anchor="w",pady=7)
            if key.lower() in {"house","casa"}:self._button(card,"ENTRAR NA CASA",self.show_house,small=True).pack(anchor="w")
            else:tk.Label(card,text="🟢 DISPONÍVEL" if item.get('status')=='installed' else "🔒 AGUARDANDO CONHECIMENTO",fg=self.green if item.get('status')=='installed' else self.gold,bg=self.panel,font=("Segoe UI",8,"bold")).pack(anchor="w")

    def show_house(self):
        self.clear_screen(); self.current_screen="house"; root=tk.Frame(self.window,bg=self.bg); root.pack(fill="both",expand=True); self._header(root); body=tk.Frame(root,bg=self.bg); body.pack(fill="both",expand=True,padx=70,pady=45); tk.Label(body,text="🏠 CASA",fg=self.star,bg=self.bg,font=("Segoe UI",28,"bold")).pack(anchor="w"); tk.Label(body,text="O espaço pessoal da STAR dentro do STAR WORLD.",fg=self.muted,bg=self.bg).pack(anchor="w",pady=(4,24))
        grid=tk.Frame(body,bg=self.bg);grid.pack(fill="x")
        for i,(title,desc,cmd) in enumerate((("🍳 COZINHA","Receitas e experimentação gastronômica.",None),("👕 CLOSET","Skins e personalização visual da STAR.",self.show_closet))):
            c=tk.Frame(grid,bg=self.panel,padx=22,pady=20,width=360,height=180); c.grid(row=0,column=i,padx=(0,14)); c.grid_propagate(False); tk.Label(c,text=title,fg=self.star,bg=self.panel,font=("Segoe UI",16,"bold")).pack(anchor="w"); tk.Label(c,text=desc,fg=self.text,bg=self.panel,wraplength=290,justify="left").pack(anchor="w",pady=12)
            if cmd:self._button(c,"ABRIR CLOSET",cmd).pack(anchor="w")

    def show_closet(self):
        self.clear_screen(); self.current_screen="closet"; root=tk.Frame(self.window,bg=self.bg); root.pack(fill="both",expand=True); self._header(root); body=tk.Frame(root,bg=self.bg); body.pack(fill="both",expand=True); top=tk.Frame(body,bg=self.bg); top.pack(fill="x",padx=45,pady=(25,0)); tk.Label(top,text="👕 CLOSET",fg=self.star,bg=self.bg,font=("Segoe UI",27,"bold")).pack(anchor="w"); tk.Label(top,text="Use as setas para navegar pelas aparências da STAR.",fg=self.muted,bg=self.bg).pack(anchor="w",pady=(3,8))
        self.closet_files=[p for p in sorted((PROJECT_ROOT/"SKINS").glob("*")) if p.suffix.lower() in {".png",".jpg",".jpeg",".webp"}]
        if not self.closet_files:tk.Label(body,text="Nenhuma skin encontrada.",fg=self.red,bg=self.bg).pack(pady=80);return
        try:self.closet_index=[p.name for p in self.closet_files].index(self.selected_skin)
        except ValueError:self.closet_index=0
        area=tk.Frame(body,bg=self.bg);area.pack(fill="both",expand=True);self._button(area,"◀",lambda:self._change_closet_skin(-1)).place(relx=.18,rely=.5,anchor="center");self._button(area,"▶",lambda:self._change_closet_skin(1)).place(relx=.82,rely=.5,anchor="center")
        card=tk.Frame(area,bg="#172231",padx=18,pady=16);card.place(relx=.5,rely=.47,anchor="center",width=430,height=455);self.closet_image=tk.Label(card,bg="#172231");self.closet_image.pack(expand=True,fill="both");self.closet_name=tk.Label(card,fg=self.text,bg="#172231",font=("Segoe UI",14,"bold"));self.closet_name.pack(pady=(8,4));self.closet_state=tk.Label(card,fg=self.green,bg="#172231",font=("Segoe UI",9,"bold"));self.closet_state.pack();self.closet_photo=None
        bottom=tk.Frame(body,bg=self.bg);bottom.pack(fill="x",padx=45,pady=(0,22));self.select_skin_button=self._button(bottom,"SELECIONAR ESTA SKIN",self._confirm_closet_skin);self.select_skin_button.pack(side="left",padx=(0,10));self._button(bottom,"SAIR DO CLOSET",self.show_house).pack(side="left");self._render_closet_skin()
    def _change_closet_skin(self,step):self.closet_index=(self.closet_index+step)%len(self.closet_files);self._render_closet_skin()
    def _render_closet_skin(self):
        p=self.closet_files[self.closet_index]
        try:im=Image.open(p).convert("RGBA");im.thumbnail((360,330),Image.Resampling.LANCZOS);self.closet_photo=ImageTk.PhotoImage(im);self.closet_image.config(image=self.closet_photo,text="")
        except Exception:self.closet_image.config(image="",text="Não foi possível abrir esta skin",fg=self.red)
        self.closet_name.config(text=p.stem.replace("_"," ").title());active=p.name==self.selected_skin;self.closet_state.config(text="✓ SKIN ATUALMENTE SELECIONADA" if active else f"{self.closet_index+1} de {len(self.closet_files)}");self.select_skin_button.config(text="SKIN SELECIONADA" if active else "SELECIONAR ESTA SKIN",bg="#1f5a3a" if active else "#243247")
    def _confirm_closet_skin(self):self.selected_skin=self.closet_files[self.closet_index].name;self._save_skin_selection();self._render_closet_skin()

    def _button(self,parent,text,command,small=False):return tk.Button(parent,text=text,command=command,bg="#243247",fg=self.text,activebackground="#38516f",activeforeground=self.text,relief=tk.FLAT,borderwidth=0,cursor="hand2",font=("Segoe UI",9 if small else 10,"bold"),padx=14,pady=7)
    def toggle_maximize(self,_event=None):
        if self.is_maximized:self.restore_normal_size()
        else:self.normal_size=(self.window.winfo_width(),self.window.winfo_height());self.window.state("zoomed");self.is_maximized=True
    def restore_normal_size(self,_event=None):
        if self.is_maximized:self.window.state("normal");self.window.geometry(f"{max(900,self.normal_size[0])}x{max(600,self.normal_size[1])}");self.is_maximized=False
    def close(self):
        if self._closing:return
        self._closing=True
        try:
            if self.recording:self.recorder.stop_to_wav()
        except Exception:pass
        try:self.voice.close()
        except Exception:pass
        try:self.memory.close()
        finally:
            try:self.window.destroy()
            except Exception:pass
    def run(self):self.window.mainloop()
