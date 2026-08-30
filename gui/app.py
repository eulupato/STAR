import os, queue, sys, threading, tkinter as tk, json
from pathlib import Path
from tkinter import scrolledtext
from PIL import Image, ImageTk

PROJECT_ROOT=Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
from config import APP_NAME, WINDOW_HEIGHT, WINDOW_WIDTH, MENU_HEIGHT, MENU_WIDTH, VERSION
from core.avatar import AvatarManager
from core.emotion import EmotionManager
from core.islands import get_islands
from database.memory import Memory
from voice.local_voice_bridge import LocalVoiceBridge
from voice.elevenlabs_voice import ElevenLabsVoice
from voice.audio_input import AudioRecorder

class StarApp:
    def __init__(self, brain):
        self.brain=brain; self.memory=Memory(); self.avatar=AvatarManager(); self.emotion=EmotionManager()
        self.voice=LocalVoiceBridge(); self.stt=ElevenLabsVoice(); self.recorder=AudioRecorder()
        self.online_mode=False
        self.processing=False
        self.response_queue=queue.Queue()
        self.current_screen=None; self.has_messages=False; self.chat=None; self.recording=False
        self.bg='#0b1018'; self.panel='#131c29'; self.text='#edf3fb'; self.muted='#9aa8bb'; self.star='#8fd0ff'; self.user='#c9b8ff'; self.green='#76e2a0'; self.red='#ff7c87'; self.gold='#ffd36e'
        self.window=tk.Tk(); self.window.title(f'{APP_NAME} V{VERSION}'); self.window.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
        self.window.minsize(900,600); self.window.configure(bg=self.bg)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<F11>',self.toggle_maximize); self.window.bind('<Escape>',self.restore_normal_size)
        self.is_maximized=False; self.normal_size=(WINDOW_WIDTH,WINDOW_HEIGHT); self.avatar_photo=None; self.skin_photo=None
        self.selected_skin=self._load_skin_selection(); self.show_menu()

    def _load_skin_selection(self):
        p=PROJECT_ROOT/'config_skin.json'
        try: return json.loads(p.read_text(encoding='utf8')).get('skin','original.jpeg')
        except Exception: return 'original.jpeg'
    def _save_skin_selection(self):
        try: (PROJECT_ROOT/'config_skin.json').write_text(json.dumps({'skin':self.selected_skin},ensure_ascii=False,indent=2),encoding='utf8')
        except Exception: pass

    def clear_screen(self):
        for w in self.window.winfo_children(): w.destroy()

    def show_menu(self):
        self.clear_screen(); self.current_screen='menu'
        if not self.is_maximized: self.window.geometry(f'{MENU_WIDTH}x{MENU_HEIGHT}')
        f=tk.Frame(self.window,bg=self.bg); f.pack(fill='both',expand=True)
        tk.Label(f,text='⭐  STAR',fg=self.star,bg=self.bg,font=('Segoe UI',34,'bold')).pack(pady=(120,20))
        tk.Label(f,text='System for Thought, Analysis and Response',fg=self.muted,bg=self.bg,font=('Segoe UI',11)).pack(pady=(0,45))
        for text,cmd in [('INICIAR',self.show_chat),('CONFIGURAÇÕES',self.show_settings),('SAIR',self.close)]: self._button(f,text,cmd).pack(pady=7)

    def _header(self,parent):
        h=tk.Frame(parent,bg='#172231',height=56); h.pack(fill='x'); h.pack_propagate(False)
        tk.Label(h,text='⭐  STAR',fg=self.star,bg='#172231',font=('Segoe UI',20,'bold')).pack(side='left',padx=18)
        status='ONLINE' if self.online_mode else 'OFFLINE'; color=self.green if self.online_mode else self.red
        self.status_label=tk.Label(h,text=f'● V{VERSION} • {status}',fg=color,bg='#172231',font=('Segoe UI',9,'bold')); self.status_label.pack(side='right',padx=18)
        self._button(h,'⚙',self.show_settings,small=True).pack(side='right',padx=4,pady=8)
        self._button(h,'◈ ILHAS',self.show_islands,small=True).pack(side='right',padx=4,pady=8)
        self._button(h,'CHAT',self.show_chat,small=True).pack(side='right',padx=4,pady=8)
        self._button(h,'MENU',self.show_menu,small=True).pack(side='right',padx=4,pady=8)

    def _gradient(self,parent):
        c=tk.Canvas(parent,bg=self.bg,highlightthickness=0); c.place(x=0,y=0,relwidth=1,relheight=1)
        # Canvas.lower() é um método de tags do Canvas, não de widgets.
        # Usamos o comando Tk para colocar o Canvas atrás dos controles.
        c.tk.call('lower', str(c))
        def draw(event=None):
            c.delete('g'); w=max(c.winfo_width(),1); h=max(c.winfo_height(),1)
            for i in range(70):
                t=i/69; r=int(12+25*(1-t)); g=int(18+50*(1-t)); b=int(28+90*(1-t))
                y=int(i*h/70); c.create_rectangle(0,y,w,y+h/70+2,fill=f'#{r:02x}{g:02x}{b:02x}',outline='',tags='g')
        c.bind('<Configure>',draw); self.window.after(20,draw)

    def show_chat(self):
        self.clear_screen()
        self._build_chat()
        self.current_screen='chat'

    def _build_chat(self):
        root=tk.Frame(self.window,bg=self.bg); root.pack(fill='both',expand=True); self._gradient(root); self._header(root)
        self.stage=tk.Frame(root,bg=self.bg); self.stage.pack(fill='both',expand=True)
        self.center=tk.Frame(self.stage,bg=self.bg); self.center.place(relx=.5,rely=.47,anchor='center')
        self.avatar_label=tk.Label(self.center,bg=self.bg); self.avatar_label.pack()
        self._load_display_avatar()
        self.chat=None; self.has_messages=False
        self._build_input(root); self.entry.focus_set()

    def _build_input(self,root):
        bottom=tk.Frame(root,bg=self.bg,height=92); bottom.pack(fill='x',side='bottom',padx=22,pady=(0,18)); bottom.pack_propagate(False)
        box=tk.Frame(bottom,bg='#cbd9e8',padx=1,pady=1); box.place(relx=.5,rely=.5,anchor='center',relwidth=.64,height=62)
        inner=tk.Frame(box,bg='#25364b'); inner.pack(fill='both',expand=True)
        tk.Label(inner,text='+',fg='#d8e7f5',bg='#25364b',font=('Segoe UI',23)).pack(side='left',padx=(16,8))
        self.entry=tk.Entry(inner,bg='#25364b',fg=self.text,insertbackground=self.text,relief=tk.FLAT,font=('Segoe UI',12))
        self.entry.pack(side='left',fill='both',expand=True,pady=7); self.entry.insert(0,'Pergunte algo à STAR...'); self.entry.config(fg='#aebdcd')
        self.entry.bind('<FocusIn>',self._clear_placeholder); self.entry.bind('<FocusOut>',self._restore_placeholder); self.entry.bind('<Return>',self._on_enter)
        self.mic=tk.Button(inner,text='🎤',command=self.toggle_microphone,bg='#25364b',fg='#d8e7f5',relief=tk.FLAT,font=('Segoe UI',14))
        self.mic.pack(side='right',padx=4)
        self.send_button=tk.Button(inner,text='➜',command=self.send_message,bg='#395574',fg='white',relief=tk.FLAT,font=('Segoe UI',16,'bold'),width=3)
        self.send_button.pack(side='right',padx=(2,8),pady=7)

    def _clear_placeholder(self,e=None):
        if self.entry.get()=='Pergunte algo à STAR...': self.entry.delete(0,tk.END); self.entry.config(fg=self.text)
    def _restore_placeholder(self,e=None):
        if not self.entry.get().strip(): self.entry.insert(0,'Pergunte algo à STAR...'); self.entry.config(fg='#aebdcd')
    def _on_enter(self,e=None): self.send_message(); return 'break'

    def toggle_microphone(self):
        if not self.stt.configured:
            self._activate_conversation(); self._append_system('🎤 Reconhecimento de fala indisponível: configure a chave do serviço de transcrição.')
            return
        if not self.recorder.available:
            self._activate_conversation(); self._append_system('🎤 Módulo de microfone indisponível. Execute o iniciador novamente para instalar as dependências.')
            return
        if not self.recording:
            try:
                self.recorder.start(); self.recording=True
                self.mic.config(text='■',bg='#8b3340',fg='white'); self._set_status('OUVINDO',self.green)
                self._activate_conversation(); self._append_system('🎤 Estou ouvindo. Clique novamente no microfone quando terminar de falar.')
            except Exception as e:
                self._activate_conversation(); self._append_system('🎤 Não consegui abrir o microfone: '+str(e))
        else:
            self.recording=False; self.mic.config(text='🎤',bg='#25364b',fg='#d8e7f5'); self._set_status('TRANSCRIVENDO',self.gold)
            threading.Thread(target=self._finish_recording,daemon=True).start()

    def _finish_recording(self):
        path=None
        try:
            path=self.recorder.stop_to_wav()
            text=self.stt.transcribe(path)
            self.response_queue.put(('transcript',text))
        except Exception as e:
            self.response_queue.put(('voice_error',str(e)))
        finally:
            if path:
                try:path.unlink(missing_ok=True)
                except Exception:pass

    def _activate_conversation(self):
        if self.has_messages:return
        self.has_messages=True; self.center.place_forget()
        self.chat=scrolledtext.ScrolledText(self.stage,wrap=tk.WORD,bg='#0e151f',fg=self.text,insertbackground=self.text,relief=tk.FLAT,borderwidth=0,font=('Segoe UI',11),padx=28,pady=22)
        self.chat.pack(fill='both',expand=True,padx=80,pady=(25,12)); self.chat.configure(state=tk.DISABLED)
        self.chat.tag_configure('user',foreground=self.user,font=('Segoe UI',10,'bold')); self.chat.tag_configure('star',foreground=self.star,font=('Segoe UI',10,'bold')); self.chat.tag_configure('message',foreground=self.text,font=('Segoe UI',11)); self.chat.tag_configure('system',foreground=self.muted,font=('Segoe UI',10))

    def send_message(self):
        if self.processing:return
        text=self.entry.get().strip()
        if not text or text=='Pergunte algo à STAR...': return
        self.entry.delete(0,tk.END); self._activate_conversation(); self._append_user(text)
        try:self.memory.save('Você',text)
        except Exception:pass
        self.processing=True; self.entry.config(state=tk.DISABLED); self.send_button.config(state=tk.DISABLED)
        self._set_status('PROCESSANDO',self.gold); self._load_avatar('thinking',size=(250,250))
        threading.Thread(target=self._process_message,args=(text,),daemon=True).start()

    def _process_message(self,text):
        try:self.response_queue.put(('success',self.brain.process(text)))
        except Exception as e:self.response_queue.put(('error',str(e)))

    def _check_response_queue(self):
        try:
            while True:
                kind,res=self.response_queue.get_nowait()
                if kind=='transcript':
                    if self.current_screen=='chat':
                        self.entry.config(state=tk.NORMAL); self.entry.delete(0,tk.END); self.entry.insert(0,res); self.entry.config(fg=self.text)
                        self._set_status('ONLINE' if self.online_mode else 'OFFLINE',self.green if self.online_mode else self.red); self.send_message()
                elif kind=='voice_error':
                    self._activate_conversation(); self._append_system('🎤 Problema no reconhecimento de voz: '+str(res)); self._set_status('ONLINE' if self.online_mode else 'OFFLINE',self.green if self.online_mode else self.red)
                elif kind=='voice_test':
                    state,err=res
                    if self.current_screen=='chat':
                        self._activate_conversation()
                        self._append_system('🔊 Teste de voz concluído.' if state=='ok' else '🔊 A voz não pôde ser reproduzida: '+str(err))
                    self._set_status('ONLINE' if self.online_mode else 'OFFLINE',self.green if self.online_mode else self.red)
                elif kind=='speech_result':
                    ok,err=res
                    if not ok:
                        self._activate_conversation()
                        self._append_system('🔊 A resposta foi gerada, mas não consegui reproduzir a voz. Detalhe: '+str(err))
                    elif self.current_screen=='chat':
                        self._set_status('ONLINE',self.green)
                elif kind=='success':
                    res=str(res); self._append_star(res)
                    try:self.memory.save('STAR',res)
                    except Exception:pass
                    self._load_avatar('speaking',size=(250,250))
                    if self.voice.configured:
                        self.voice.speak_async(res, lambda ok,err:self.response_queue.put(('speech_result',(ok,err))))
                    else:
                        self._append_system('🔊 Voz local não configurada. Verifique .voice_venv e voice/reference/star_reference.mp3.')
                    self.processing=False
                    if self.current_screen=='chat':
                        self.entry.config(state=tk.NORMAL); self.send_button.config(state=tk.NORMAL); self._set_status('ONLINE' if self.online_mode else 'OFFLINE',self.green if self.online_mode else self.red); self.entry.focus_set()
                else:
                    self._append_system('Erro ao processar: '+str(res)); self._load_avatar('neutral',size=(250,250)); self.processing=False
                    if self.current_screen=='chat': self.entry.config(state=tk.NORMAL); self.send_button.config(state=tk.NORMAL)
        except queue.Empty:pass
        try:self.window.after(60,self._check_response_queue)
        except tk.TclError:pass

    def _append(self,name,text,tag):
        if not self.chat:return
        self.chat.configure(state=tk.NORMAL); self.chat.insert(tk.END,name+'\n',tag); self.chat.insert(tk.END,text+'\n\n','message'); self.chat.configure(state=tk.DISABLED); self.chat.see(tk.END)
    def _append_user(self,text): self._append('Você',text,'user')
    def _append_star(self,text): self._append('⭐ STAR',text,'star')
    def _append_system(self,text):
        if self.chat:
            self.chat.configure(state=tk.NORMAL); self.chat.insert(tk.END,text+'\n\n','system'); self.chat.configure(state=tk.DISABLED); self.chat.see(tk.END)

    def _load_display_avatar(self):
        skin=PROJECT_ROOT/'SKINS'/self.selected_skin
        if skin.exists():
            try:
                img=Image.open(skin).convert('RGBA'); img.thumbnail((300,330),Image.Resampling.LANCZOS)
                self.avatar_photo=ImageTk.PhotoImage(img); self.avatar_label.config(image=self.avatar_photo,text=''); return
            except Exception: pass
        self._load_avatar('neutral',size=(250,250))

    def _load_avatar(self,emotion='neutral',size=(250,250)):
        path=self.avatar.avatar_dir/f'{emotion}.png'
        if not path.exists():path=self.avatar.avatar_dir/'neutral.png'
        try:
            img=Image.open(path).convert('RGBA'); img.thumbnail(size,Image.Resampling.LANCZOS); self.avatar_photo=ImageTk.PhotoImage(img); self.avatar_label.config(image=self.avatar_photo,text='')
        except Exception:self.avatar_label.config(text='⭐\nSTAR',fg=self.star,font=('Segoe UI',28,'bold'))

    def _set_status(self,text,color):
        if hasattr(self,'status_label'): self.status_label.config(text=f'● V{VERSION} • {text}',fg=color)

    def show_settings(self):
        self.clear_screen(); self.current_screen='settings'; root=tk.Frame(self.window,bg=self.bg); root.pack(fill='both',expand=True); self._header(root)
        body=tk.Frame(root,bg=self.bg); body.pack(fill='both',expand=True,padx=80,pady=35)
        tk.Label(body,text='CONFIGURAÇÕES',fg=self.star,bg=self.bg,font=('Segoe UI',27,'bold')).pack(anchor='w')
        tk.Label(body,text='Modo de funcionamento e sistemas de voz',fg=self.muted,bg=self.bg,font=('Segoe UI',11)).pack(anchor='w',pady=(5,20))
        mode=tk.Frame(body,bg=self.panel,padx=22,pady=18); mode.pack(fill='x')
        tk.Label(mode,text='MODO DE FUNCIONAMENTO',fg=self.text,bg=self.panel,font=('Segoe UI',12,'bold')).pack(anchor='w')
        row=tk.Frame(mode,bg=self.panel); row.pack(anchor='w',pady=12)
        self.online_btn=self._button(row,'🟢 ONLINE',lambda:self._set_mode(True)); self.online_btn.pack(side='left',padx=(0,10))
        self.offline_btn=self._button(row,'🔴 OFFLINE',lambda:self._set_mode(False)); self.offline_btn.pack(side='left'); self._refresh_mode_buttons()
        tk.Label(mode,text='ONLINE habilita voz e reconhecimento de fala pelo ElevenLabs. OFFLINE mantém o Core e o conhecimento local.',fg=self.muted,bg=self.panel,wraplength=760,justify='left').pack(anchor='w')
        voicebox=tk.Frame(body,bg=self.panel,padx=22,pady=18); voicebox.pack(fill='x',pady=16)
        tk.Label(voicebox,text='🎙️ VOZ E ÁUDIO',fg=self.star,bg=self.panel,font=('Segoe UI',13,'bold')).pack(anchor='w')
        tk.Label(voicebox,text='Saída: alto-falante padrão do sistema • Entrada: microfone padrão do sistema',fg=self.text,bg=self.panel).pack(anchor='w',pady=(8,2))
        tk.Label(voicebox,text='Use o botão de microfone no chat: 1º clique inicia a gravação; 2º clique para e transcreve.',fg=self.muted,bg=self.panel).pack(anchor='w')
        self._button(voicebox,'TESTAR VOZ DA STAR',self._test_voice).pack(anchor='w',pady=(12,0))
        info=tk.Frame(body,bg=self.panel,padx=22,pady=16); info.pack(fill='x')
        rows=[('Versão',f'V{VERSION}'),('IA externa','DESATIVADA'),('Conhecimento local','ATIVO'),('Voz local Chatterbox','PRONTA' if self.voice.configured else 'NÃO CONFIGURADA'),('Reconhecimento de fala','PRONTO' if self.stt.configured else 'AGUARDANDO CHAVE')]
        for a,b in rows:
            r=tk.Frame(info,bg=self.panel); r.pack(fill='x',pady=4); tk.Label(r,text=a,fg=self.muted,bg=self.panel).pack(side='left'); tk.Label(r,text=b,fg=self.green if b in {'ATIVO','PRONTA','PRONTO'} else self.text,bg=self.panel,font=('Segoe UI',10,'bold')).pack(side='right')
        self._button(body,'VOLTAR AO CHAT',self.show_chat).pack(anchor='w',pady=10)

    def _test_voice(self):
        self._set_status('TESTANDO VOZ',self.gold)
        self.voice.test_audio_async(lambda ok,err:self.response_queue.put(('voice_test',('ok' if ok else 'erro',err))))
        # handled below by queue branch

    def _set_mode(self,online):
        self.online_mode=bool(online); self._refresh_mode_buttons()
    def _refresh_mode_buttons(self):
        if not hasattr(self,'online_btn'):return
        if self.online_mode:
            self.online_btn.config(bg='#1f5a3a'); self.offline_btn.config(bg='#5a2630')
        else:
            self.online_btn.config(bg='#24313f'); self.offline_btn.config(bg='#5a2630')

    def show_islands(self):
        self.clear_screen(); self.current_screen='islands'; root=tk.Frame(self.window,bg=self.bg); root.pack(fill='both',expand=True); self._header(root)
        body=tk.Frame(root,bg=self.bg); body.pack(fill='both',expand=True,padx=35,pady=20)
        tk.Label(body,text='HUB • STAR WORLD',fg=self.star,bg=self.bg,font=('Segoe UI',24,'bold')).pack(anchor='w',pady=(0,12))
        canvas=tk.Canvas(body,bg=self.bg,highlightthickness=0); canvas.pack(side='left',fill='both',expand=True); sb=tk.Scrollbar(body,command=canvas.yview); sb.pack(side='right',fill='y'); canvas.config(yscrollcommand=sb.set)
        inner=tk.Frame(canvas,bg=self.bg); canvas.create_window((0,0),window=inner,anchor='nw'); inner.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        for i,(k,x) in enumerate(get_islands().items()):
            card=tk.Frame(inner,bg=self.panel,padx=16,pady=14); card.grid(row=i//3,column=i%3,sticky='nsew',padx=6,pady=6)
            tk.Label(card,text=f"{x['icon']} {x['name']}",fg=self.star,bg=self.panel,font=('Segoe UI',14,'bold')).pack(anchor='w')
            tk.Label(card,text=x['description'],fg=self.text,bg=self.panel,wraplength=270,justify='left').pack(anchor='w',pady=7)
            if k.lower() in ('house','casa'):
                self._button(card,'ENTRAR NA CASA',self.show_house,small=True).pack(anchor='w',pady=5)
            else:
                state='🟢 DISPONÍVEL' if x.get('status')=='installed' else '🔒 AGUARDANDO CONHECIMENTO'
                tk.Label(card,text=state,fg=self.green if x.get('status')=='installed' else self.gold,bg=self.panel,font=('Segoe UI',8,'bold')).pack(anchor='w')

    def show_house(self):
        self.clear_screen(); self.current_screen='house'; root=tk.Frame(self.window,bg=self.bg); root.pack(fill='both',expand=True); self._header(root)
        body=tk.Frame(root,bg=self.bg); body.pack(fill='both',expand=True,padx=70,pady=45)
        tk.Label(body,text='🏠 CASA',fg=self.star,bg=self.bg,font=('Segoe UI',28,'bold')).pack(anchor='w')
        tk.Label(body,text='O espaço pessoal da STAR dentro do STAR WORLD.',fg=self.muted,bg=self.bg).pack(anchor='w',pady=(4,24))
        grid=tk.Frame(body,bg=self.bg); grid.pack(fill='x')
        for i,(title,desc,cmd) in enumerate([('🍳 COZINHA','Receitas, culinária e experimentação gastronômica.',None),('👕 CLOSET','Skins, roupas, aparência e personalização visual.',self.show_closet)]):
            c=tk.Frame(grid,bg=self.panel,padx=22,pady=20,width=360,height=180); c.grid(row=0,column=i,padx=(0,14),sticky='nsew'); c.grid_propagate(False)
            tk.Label(c,text=title,fg=self.star,bg=self.panel,font=('Segoe UI',16,'bold')).pack(anchor='w'); tk.Label(c,text=desc,fg=self.text,bg=self.panel,wraplength=290,justify='left').pack(anchor='w',pady=12)
            if cmd:self._button(c,'ABRIR CLOSET',cmd).pack(anchor='w')

    def show_closet(self):
        self.clear_screen(); self.current_screen='closet'
        root=tk.Frame(self.window,bg=self.bg); root.pack(fill='both',expand=True); self._header(root)
        body=tk.Frame(root,bg=self.bg); body.pack(fill='both',expand=True)
        top=tk.Frame(body,bg=self.bg); top.pack(fill='x',padx=45,pady=(25,0))
        tk.Label(top,text='👕 CLOSET',fg=self.star,bg=self.bg,font=('Segoe UI',27,'bold')).pack(anchor='w')
        tk.Label(top,text='Use as setas para navegar pelas aparências da STAR.',fg=self.muted,bg=self.bg).pack(anchor='w',pady=(3,8))
        self.closet_files=[p for p in sorted((PROJECT_ROOT/'SKINS').glob('*')) if p.suffix.lower() in {'.png','.jpg','.jpeg','.webp'}]
        if not self.closet_files:
            tk.Label(body,text='Nenhuma skin encontrada na pasta SKINS.',fg=self.red,bg=self.bg).pack(pady=80); return
        try: self.closet_index=[p.name for p in self.closet_files].index(self.selected_skin)
        except ValueError: self.closet_index=0
        area=tk.Frame(body,bg=self.bg); area.pack(fill='both',expand=True)
        self._button(area,'◀',lambda:self._change_closet_skin(-1),small=False).place(relx=.18,rely=.5,anchor='center')
        self._button(area,'▶',lambda:self._change_closet_skin(1),small=False).place(relx=.82,rely=.5,anchor='center')
        card=tk.Frame(area,bg='#172231',padx=18,pady=16); card.place(relx=.5,rely=.47,anchor='center',width=430,height=455)
        self.closet_image=tk.Label(card,bg='#172231'); self.closet_image.pack(expand=True,fill='both')
        self.closet_name=tk.Label(card,fg=self.text,bg='#172231',font=('Segoe UI',14,'bold')); self.closet_name.pack(pady=(8,4))
        self.closet_state=tk.Label(card,fg=self.green,bg='#172231',font=('Segoe UI',9,'bold')); self.closet_state.pack()
        self.closet_photo=None
        bottom=tk.Frame(body,bg=self.bg); bottom.pack(fill='x',padx=45,pady=(0,22))
        self.select_skin_button=self._button(bottom,'SELECIONAR ESTA SKIN',self._confirm_closet_skin)
        self.select_skin_button.pack(side='left',padx=(0,10))
        self._button(bottom,'SAIR DO CLOSET',self.show_house).pack(side='left')
        self._render_closet_skin()

    def _change_closet_skin(self,step):
        self.closet_index=(self.closet_index+step)%len(self.closet_files)
        self._render_closet_skin()

    def _render_closet_skin(self):
        p=self.closet_files[self.closet_index]
        try:
            im=Image.open(p).convert('RGBA'); im.thumbnail((360,330),Image.Resampling.LANCZOS)
            self.closet_photo=ImageTk.PhotoImage(im); self.closet_image.config(image=self.closet_photo,text='')
        except Exception as e:
            self.closet_image.config(image='',text='Não foi possível abrir esta skin',fg=self.red)
        self.closet_name.config(text=p.stem.replace('_',' ').title())
        active=p.name==self.selected_skin
        self.closet_state.config(text='✓ SKIN ATUALMENTE SELECIONADA' if active else f'{self.closet_index+1} de {len(self.closet_files)}')
        self.select_skin_button.config(text='SKIN SELECIONADA' if active else 'SELECIONAR ESTA SKIN',bg='#1f5a3a' if active else '#243247')

    def _confirm_closet_skin(self):
        self.selected_skin=self.closet_files[self.closet_index].name
        self._save_skin_selection(); self._render_closet_skin()

    def _select_skin(self,name):
        self.selected_skin=name; self._save_skin_selection(); self.show_closet()

    def _button(self,parent,text,command,small=False):
        return tk.Button(parent,text=text,command=command,bg='#243247',fg=self.text,activebackground='#38516f',activeforeground=self.text,relief=tk.FLAT,borderwidth=0,cursor='hand2',font=('Segoe UI',9 if small else 10,'bold'),padx=14,pady=7)
    def toggle_maximize(self,e=None):
        if self.is_maximized:self.restore_normal_size()
        else:self.normal_size=(self.window.winfo_width(),self.window.winfo_height()); self.window.state('zoomed'); self.is_maximized=True
    def restore_normal_size(self,e=None):
        if self.is_maximized:self.window.state('normal'); self.window.geometry(f'{max(900,self.normal_size[0])}x{max(600,self.normal_size[1])}'); self.is_maximized=False
    def close(self):
        try:
            if self.recording: self.recorder.stop_to_wav()
        except Exception:pass
        try:self.memory.close()
        finally:
            try:self.window.destroy()
            except Exception:pass
    def run(self): self.window.after(60,self._check_response_queue); self.window.mainloop()
