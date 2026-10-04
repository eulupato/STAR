"""Interface gráfica da STAR V2.0."""
from __future__ import annotations

import json
import logging
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

from PIL import Image, ImageTk, UnidentifiedImageError

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import APP_NAME, VERSION, WINDOW_HEIGHT, WINDOW_WIDTH, MENU_HEIGHT, MENU_WIDTH, STT_MODEL, VOICE_CHAT_MODE
from core.avatar import AvatarManager
from core.emotion import EmotionManager
from database.memory import Memory
from voice.audio_devices import audio_device_info
from voice.audio_input import AudioRecorder, VoiceActivityDetector, VoiceTurnAssembler
from voice.manager import VoiceManager
from gui import theme

import config as _config

VISUAL_3D_ENABLED = bool(getattr(_config, "VISUAL_3D_ENABLED", True))
VISUAL_3D_FPS = int(getattr(_config, "VISUAL_3D_FPS", 30))
VISUAL_3D_QUALITY = str(getattr(_config, "VISUAL_3D_QUALITY", "high"))

try:
    from gui.widgets3d import CrystalStar3D, StarOrb3D
except Exception as _exc:  # pragma: no cover - fallback visual seguro
    LOGGER.warning("Widgets 3D indisponíveis; usando interface estática: %s", _exc)
    CrystalStar3D = StarOrb3D = None


class StarApp:
    def __init__(self, brain, profile="pc"):
        self.brain = brain
        self.profile = "mobile" if str(profile).lower() == "mobile" else "pc"
        surface_memory = getattr(brain, "surface_memory", None)
        self.memory = surface_memory if surface_memory is not None else Memory()
        self.avatar = AvatarManager()
        self.emotion = EmotionManager()
        surface_voice = getattr(brain, "surface_voice", None)
        self.voice = surface_voice if surface_voice is not None else VoiceManager()
        self.voice.set_voice_mode(self._load_voice_mode())
        self.recorder = AudioRecorder()
        self.vad = VoiceActivityDetector()
        self.turn_assembler = VoiceTurnAssembler(
            lambda text: self.response_queue.put(("vad_utterance", text))
        )
        self.hands_free = False
        self._pending_voice_transcript = None
        self.online_mode = False
        self.processing = False
        self.recording = False
        self._closing = False
        self.response_queue: queue.Queue = queue.Queue()
        self.current_screen = "menu"
        self.has_messages = False
        self.chat = None
        self.voice_test_label = None
        self.voice_test_buttons = []
        self.voice_test_stop_button = None
        self.avatar_photo = None
        self.closet_photo = None
        self.selected_skin = self._load_skin_selection()

        self.bg = theme.BG_VOID; self.panel = theme.PANEL; self.text = theme.TEXT; self.muted = theme.MUTED
        self.star = theme.ORB_GLOW; self.user = theme.CRYSTAL_MID; self.green = theme.ACCENT_OK; self.red = theme.ACCENT_ERR; self.gold = theme.ACCENT_WARN
        self._visuals = []

        self.window = tk.Tk()
        title_suffix = " Mobile" if self.profile == "mobile" else ""
        self.window.title(f"{APP_NAME}{title_suffix} V{VERSION}")
        if self.profile == "mobile":
            self.window.geometry("430x820")
            self.window.minsize(390, 680)
        else:
            self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
            self.window.minsize(900, 600)
        self.window.configure(bg=self.bg)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<F11>", self.toggle_maximize)
        self.window.bind("<Escape>", self.restore_normal_size)
        self.is_maximized = False
        self.normal_size = (430, 820) if self.profile == "mobile" else (WINDOW_WIDTH, WINDOW_HEIGHT)
        if self.profile == "mobile":
            self.show_chat()
        else:
            self.show_menu()
        self.window.after(60, self._check_response_queue)
        # Pré-carrega somente o STT. O Chatterbox oficial leva minutos em CPU e
        # não deve atrasar nem sobrecarregar a abertura da interface.
        self.voice.warmup_stt_async()

    @property
    def _user_settings_path(self):
        return PROJECT_ROOT / "user_settings.json"

    def _read_user_settings(self):
        path = self._user_settings_path
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            LOGGER.warning("Não foi possível ler %s: %s", path, exc)
            return {}
        if not isinstance(data, dict):
            LOGGER.warning("Configuração ignorada porque %s não contém um objeto JSON.", path)
            return {}
        return data

    def _write_user_settings(self, **values):
        path = self._user_settings_path
        temp = path.with_name(path.name + ".tmp")
        data = self._read_user_settings()
        data.update(values)
        try:
            temp.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temp.replace(path)
        except (OSError, TypeError) as exc:
            LOGGER.error("Falha ao salvar configurações em %s: %s", path, exc)
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass

    def _load_voice_mode(self):
        mode = str(self._read_user_settings().get("voice_mode", VOICE_CHAT_MODE)).lower()
        return mode if mode in {"official", "fast"} else VOICE_CHAT_MODE

    def _load_skin_selection(self):
        local = self._read_user_settings().get("skin")
        if local:
            return str(local)
        path = PROJECT_ROOT / "config_skin.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return str(data.get("skin", "original.jpeg")) if isinstance(data, dict) else "original.jpeg"
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            LOGGER.warning("Falha ao ler skin padrão de %s: %s", path, exc)
            return "original.jpeg"

    def _save_skin_selection(self):
        self._write_user_settings(skin=self.selected_skin)

    def _save_voice_mode(self):
        self._write_user_settings(voice_mode=self.voice.mode)

    def clear_screen(self):
        # Mãos-livres só existe enquanto a superfície de chat está visível.
        # Navegar para outra tela encerra o stream para manter consentimento
        # observável e evitar um microfone ativo sem indicador na interface.
        if getattr(self, "hands_free", False):
            try:
                self.vad.stop()
            except Exception as exc:
                LOGGER.warning("Falha ao encerrar VAD ao trocar de tela: %s", exc)
            self.turn_assembler.cancel()
            self.hands_free = False
        self._stop_visuals()
        for widget in self.window.winfo_children():
            widget.destroy()
        self.chat = None
        self.has_messages = False
        self.voice_test_label = None
        self.voice_test_buttons = []
        self.voice_test_stop_button = None

    def _header(self, parent):
        header = tk.Frame(parent, bg=theme.PANEL, height=56); header.pack(fill="x"); header.pack_propagate(False)
        self._header_frame = header
        is_mobile = self.profile == "mobile"
        mini = self._make_visual(CrystalStar3D, header, size=26 if is_mobile else 30, bg=theme.PANEL, quality="low")
        if mini is not None:
            mini.pack(side="left", padx=((10, 4) if is_mobile else (18, 6))); mini.render_once()
        title_size = 15 if is_mobile else 20
        tk.Label(header, text="STAR", fg=self.star, bg=theme.PANEL, font=("Segoe UI", title_size, "bold")).pack(side="left", padx=(0 if mini is not None else (10 if is_mobile else 18), 10 if is_mobile else 18))
        status = "ONLINE" if self.online_mode else "OFFLINE"; color = self.green if self.online_mode else self.red
        status_text = f"● {status}" if is_mobile else f"● V{VERSION} • {status}"
        self.status_label = tk.Label(header, text=status_text, fg=color, bg=theme.PANEL, font=("Segoe UI", 8 if is_mobile else 9, "bold")); self.status_label.pack(side="right", padx=10 if is_mobile else 18)
        controls = (("⚙", self.show_settings), ("CHAT", self.show_chat)) if is_mobile else (("⚙", self.show_settings), ("◈ ILHAS", self.show_islands), ("CHAT", self.show_chat), ("MENU", self.show_menu))
        for text, cmd in controls:
            self._button(header, text, cmd, small=True).pack(side="right", padx=2 if is_mobile else 4, pady=8)

    def _gradient(self, parent, exclude=0, rely=.47):
        """Fundo cósmico: vazio violeta profundo + campo de partículas estáticas.

        O brilho radial violeta vem do halo do próprio orb (mesma cor de fundo),
        evitando "caixas" visíveis, já que o Tk não tem transparência entre widgets.
        ``exclude`` é o meio-lado do quadrado central (orb) sem partículas.
        """
        canvas = tk.Canvas(parent, bg=self.bg, highlightthickness=0); canvas.place(x=0,y=0,relwidth=1,relheight=1); canvas.tk.call("lower", str(canvas))
        try:
            from gui.visual3d import particle_field
            particles = particle_field(0.0, n=80, seed=42)
        except Exception as exc:
            LOGGER.warning("Partículas do fundo indisponíveis: %s", exc); particles = []
        def draw(_event=None):
            try:
                if not canvas.winfo_exists():return
            except tk.TclError:return
            canvas.delete("gradient"); width=max(canvas.winfo_width(),1); height=max(canvas.winfo_height(),1)
            cx=width/2; cy=height*rely
            for part in particles:
                x=part["x"]*width; y=part["y"]*height
                if exclude and abs(x-cx)<exclude+6 and abs(y-cy)<exclude+6:continue
                r=part["r"]*.8; glow=part["alpha"]*.75
                canvas.create_oval(x-r,y-r,x+r,y+r,fill=theme.mix(theme.BG_VOID,theme.CRYSTAL_HI if part["r"]>1.6 else theme.ORB_GLOW,glow),outline="",tags="gradient")
        canvas.bind("<Configure>",draw); self.window.after(20,draw)
        return canvas

    def _make_visual(self, cls, parent, **kwargs):
        """Cria um widget 3D registrado para cleanup; None se desativado/indisponível."""
        if cls is None or not VISUAL_3D_ENABLED:return None
        try:
            widget=cls(parent,**kwargs)
        except Exception as exc:
            LOGGER.warning("Falha ao criar widget 3D %s: %s", getattr(cls,"__name__",cls), exc);return None
        visuals=getattr(self,"_visuals",None)
        if visuals is None:visuals=self._visuals=[]
        visuals.append(widget)
        return widget

    def _stop_visuals(self):
        """Para e destrói todos os widgets 3D ativos (idempotente)."""
        visuals=getattr(self,"_visuals",None) or []
        for widget in visuals:
            try:
                widget.stop()
                if widget.winfo_exists():widget.destroy()
            except (tk.TclError, AttributeError) as exc:
                LOGGER.debug("Widget 3D já encerrado: %s", exc)
        self._visuals=[]
        self._orb=None; self._mini_orb=None

    def _orb_state(self, emotion):
        """Mapeia emoção do avatar → estado visual do orb (nunca propaga erro)."""
        try:
            for orb in (getattr(self,"_orb",None),getattr(self,"_mini_orb",None)):
                if orb is not None and orb.winfo_exists():orb.set_state(emotion)
        except Exception as exc:
            LOGGER.debug("Falha ao atualizar estado do orb: %s", exc)

    def show_menu(self):
        self.clear_screen(); self.current_screen="menu"
        if not self.is_maximized:self.window.geometry(f"{MENU_WIDTH}x{MENU_HEIGHT}")
        frame=tk.Frame(self.window,bg=self.bg); frame.pack(fill="both",expand=True)
        self._gradient(frame)
        crystal=self._make_visual(CrystalStar3D,frame,size=170,fps=max(15,min(VISUAL_3D_FPS,30)),bg=theme.BG_VOID,quality=VISUAL_3D_QUALITY)
        if crystal is not None:crystal.pack(pady=(70,8));crystal.start()
        tk.Label(frame,text="STAR",fg=self.text,bg=self.bg,font=("Segoe UI",46,"bold")).pack(pady=((0,14) if crystal is not None else (120,20))); tk.Label(frame,text="System for Thought, Analysis and Response",fg=self.muted,bg=self.bg,font=("Segoe UI",11)).pack(pady=(0,45))
        for label,cmd in (("INICIAR",self.show_chat),("CONFIGURAÇÕES",self.show_settings),("SAIR",self.close)):self._button(frame,label,cmd).pack(pady=7)

    def show_chat(self):
        self.clear_screen(); self.current_screen="chat"
        root=tk.Frame(self.window,bg=self.bg); root.pack(fill="both",expand=True); self._gradient(root); self._header(root)
        self.stage=tk.Frame(root,bg=self.bg); self.stage.pack(fill="both",expand=True)
        orb_size=self._orb_size()
        self._gradient(self.stage, exclude=orb_size/2)
        center_bg=self.bg
        self.center=tk.Frame(self.stage,bg=center_bg); self.center.place(relx=.5,rely=.47,anchor="center")
        self._orb=self._make_visual(StarOrb3D,self.center,size=orb_size,bg=self.bg,quality=VISUAL_3D_QUALITY,fps=VISUAL_3D_FPS,radius=.4)
        self.avatar_label=tk.Label(self.center,bg=center_bg,borderwidth=0,highlightthickness=0)
        if self._orb is not None:
            self._orb.pack();self._orb.start()
        else:
            self.avatar_label.pack()
        self._load_display_avatar(); self._build_input(root); self.entry.focus_set()

    def _orb_size(self):
        try:height=int(self.window.winfo_height())
        except tk.TclError:height=0
        if height<200:height=(820 if self.profile == "mobile" else WINDOW_HEIGHT)
        if self.profile == "mobile":
            return max(200,min(300,height-56-110-80))
        return max(260,min(460,height-56-110-40))

    def _build_input(self,root):
        side_pad = 10 if self.profile == "mobile" else 22
        box_width = .95 if self.profile == "mobile" else .64
        bottom=tk.Frame(root,bg=self.bg,height=92); bottom.pack(fill="x",side="bottom",padx=side_pad,pady=(0,12 if self.profile == "mobile" else 18)); bottom.pack_propagate(False)
        box=tk.Frame(bottom,bg=theme.CRYSTAL_LILAC,padx=1,pady=1); box.place(relx=.5,rely=.5,anchor="center",relwidth=box_width,height=62); inner=tk.Frame(box,bg=theme.INPUT_BG); inner.pack(fill="both",expand=True)
        tk.Label(inner,text="+",fg=theme.CRYSTAL_HI,bg=theme.INPUT_BG,font=("Segoe UI",23)).pack(side="left",padx=(16,8)); self.entry=tk.Entry(inner,bg=theme.INPUT_BG,fg=self.text,insertbackground=self.text,relief=tk.FLAT,font=("Segoe UI",12)); self.entry.pack(side="left",fill="both",expand=True,pady=7); self.entry.insert(0,"Pergunte algo à STAR..."); self.entry.config(fg=theme.MUTED)
        self.entry.bind("<FocusIn>",self._clear_placeholder); self.entry.bind("<FocusOut>",self._restore_placeholder); self.entry.bind("<Return>",self._on_enter)
        self.mic=tk.Button(inner,text="🎤",command=self.toggle_microphone,bg=theme.INPUT_BG,fg=theme.CRYSTAL_HI,activebackground=theme.PANEL_HOVER,relief=tk.FLAT,borderwidth=0,font=("Segoe UI",14),cursor="hand2"); self.mic.pack(side="right",padx=4)
        self.hands_free_button=tk.Button(inner,text="◉",command=self.toggle_hands_free,bg=theme.INPUT_BG,fg=theme.MUTED,activebackground=theme.PANEL_HOVER,relief=tk.FLAT,borderwidth=0,font=("Segoe UI",13,"bold"),cursor="hand2"); self.hands_free_button.pack(side="right",padx=4)
        self.send_button=tk.Button(inner,text="➜",command=self.send_message,bg=theme.ORB_MID,fg=theme.TEXT,activebackground=theme.ORB_GLOW,relief=tk.FLAT,borderwidth=0,font=("Segoe UI",16,"bold"),width=3,cursor="hand2"); self.send_button.pack(side="right",padx=(2,8),pady=7)

    def _clear_placeholder(self,_event=None):
        if self.entry.get()=="Pergunte algo à STAR...":self.entry.delete(0,tk.END);self.entry.config(fg=self.text)
    def _restore_placeholder(self,_event=None):
        if not self.entry.get().strip():self.entry.insert(0,"Pergunte algo à STAR...");self.entry.config(fg=theme.MUTED)
    def _on_enter(self,_event=None):self.send_message();return "break"

    def toggle_microphone(self):
        if self.hands_free:
            self._activate_conversation()
            self._append_system("🎙️ O modo mãos-livres está ativo. Desative o botão ◉ para usar a gravação manual.")
            return
        self.voice.cancel_speech(reason="manual_microphone")
        if not self.voice.stt_configured:self._activate_conversation();self._append_system("🎤 Reconhecimento local ainda não está instalado. Execute INSTALAR_VOZ.bat.");return
        if not self.recorder.available:self._activate_conversation();self._append_system("🎤 Não consegui acessar o microfone. Verifique as configurações de áudio do Windows.");return
        if not self.recording:
            try:self.recorder.start();self.recording=True;self.mic.config(text="■",bg=theme.RECORDING,fg="white");self._activate_conversation();self._append_system("🎤 Estou ouvindo. Clique novamente quando terminar.");self._set_status("OUVINDO",self.green)
            except Exception as exc:self._append_system(f"🎤 Erro ao abrir microfone: {exc}")
        else:
            self.recording=False;self.mic.config(text="🎤",bg=theme.INPUT_BG,fg=theme.CRYSTAL_HI);self._set_status("TRANSCRIVENDO",self.gold);threading.Thread(target=self._finish_recording,daemon=True).start()

    def toggle_hands_free(self):
        """Ativa escuta contínua somente após uma ação explícita do usuário."""
        if self.hands_free:
            try:
                self.vad.stop()
            finally:
                self.hands_free = False
                if hasattr(self, "hands_free_button"):
                    self.hands_free_button.config(text="◉", bg=theme.INPUT_BG, fg=theme.MUTED)
                if self.current_screen == "chat":
                    self._set_status("OFFLINE" if not self.online_mode else "ONLINE", self.red if not self.online_mode else self.green)
                    self._activate_conversation()
                    self._append_system("🎙️ Modo mãos-livres desativado.")
            return

        if self.recording:
            self._activate_conversation()
            self._append_system("🎙️ Finalize a gravação manual antes de ativar o modo mãos-livres.")
            return
        if not self.voice.stt_configured:
            self._activate_conversation()
            self._append_system("🎙️ O STT local ainda não está instalado. Execute INSTALAR_VOZ.bat.")
            return
        if not self.vad.available:
            self._activate_conversation()
            self._append_system("🎙️ VAD local indisponível. Verifique sounddevice/soundfile e o microfone.")
            return

        try:
            self.vad.start(
                on_start=self._vad_on_start,
                on_end=self._vad_on_end,
                on_error=self._vad_on_error,
                guard_provider=lambda: self.voice.is_speaking,
            )
            self.hands_free = True
            if hasattr(self, "hands_free_button"):
                self.hands_free_button.config(text="●", bg=theme.TOGGLE_ON, fg="white")
            self._activate_conversation()
            self._append_system(
                "🎙️ Mãos-livres ativo. A detecção é local; somente trechos de fala viram WAV temporário e são apagados após a transcrição. Fale por cima da STAR para interrompê-la."
            )
            self._set_status("MÃOS-LIVRES", self.green)
        except Exception as exc:
            self.hands_free = False
            self._activate_conversation()
            self._append_system(f"🎙️ Não consegui iniciar mãos-livres: {exc}")

    def _vad_on_start(self):
        self.turn_assembler.speech_started()
        interrupted = self.voice.barge_in()
        self.response_queue.put(("vad_start", interrupted))

    def _vad_on_end(self, path, duration_ms):
        threading.Thread(
            target=self._transcribe_vad_segment,
            args=(path, duration_ms),
            daemon=True,
            name="STAR-VAD-STT",
        ).start()

    def _vad_on_error(self, message):
        self.response_queue.put(("vad_error", str(message)))

    def _transcribe_vad_segment(self, path, duration_ms):
        try:
            text = self.voice.transcribe(path)
            self.response_queue.put(("vad_transcript", (text, float(duration_ms))))
        except Exception as exc:
            self.response_queue.put(("vad_error", f"{type(exc).__name__}: {exc}"))
        finally:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError as exc:
                LOGGER.warning("Falha ao remover WAV temporário %s: %s", path, exc)

    def _flush_pending_voice_transcript(self):
        if self.processing or not self._pending_voice_transcript or self.current_screen != "chat":
            return
        text = self._pending_voice_transcript
        self._pending_voice_transcript = None
        self.voice.cancel_speech(reason="new_voice_turn")
        self.entry.config(state=tk.NORMAL)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)
        self.entry.config(fg=self.text)
        self.send_message()

    def _finish_recording(self):
        path=None
        try:
            path=self.recorder.stop_to_wav()
            if getattr(self.brain, "is_remote_endpoint", False):
                transcript,answer=self.brain.process_audio(path)
                self.response_queue.put(("remote_voice_response",(transcript,answer)))
            else:
                text=self.voice.transcribe(path)
                self.response_queue.put(("transcript",text))
        except Exception as exc:self.response_queue.put(("voice_error",str(exc)))
        finally:
            if path:
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    LOGGER.warning("Falha ao remover gravação temporária %s: %s", path, exc)

    def _activate_conversation(self):
        if self.has_messages or not hasattr(self,"stage"):return
        self.has_messages=True
        if hasattr(self,"center"):
            try:self.center.place_forget()
            except tk.TclError:pass
        self._dock_orb()
        chat_pad = 12 if self.profile == "mobile" else 80
        self.chat=scrolledtext.ScrolledText(self.stage,wrap=tk.WORD,bg=theme.BG_DEEP,fg=self.text,insertbackground=self.text,relief=tk.FLAT,borderwidth=0,font=("Segoe UI",11),padx=18 if self.profile == "mobile" else 28,pady=18 if self.profile == "mobile" else 22);self.chat.pack(fill="both",expand=True,padx=chat_pad,pady=(14 if self.profile == "mobile" else 25,12));self.chat.configure(state=tk.DISABLED)
        for tag,fg,font in (("user",self.user,("Segoe UI",10,"bold")),("star",self.star,("Segoe UI",10,"bold")),("message",self.text,("Segoe UI",11)),("system",self.muted,("Segoe UI",10))):self.chat.tag_configure(tag,foreground=fg,font=font)

    def _dock_orb(self):
        """Quando o palco central some, para o orb grande e mostra um mini-orb no header."""
        orb=getattr(self,"_orb",None)
        if orb is not None:
            try:orb.stop()
            except tk.TclError:pass
        header=getattr(self,"_header_frame",None)
        if header is None or getattr(self,"_mini_orb",None) is not None:return
        try:
            if not header.winfo_exists():return
        except tk.TclError:return
        state=getattr(orb,"state","neutral") if orb is not None else "neutral"
        self._mini_orb=self._make_visual(StarOrb3D,header,size=48,state=state,quality="low",fps=min(VISUAL_3D_FPS,20),bg=theme.PANEL)
        if self._mini_orb is not None:self._mini_orb.pack(side="left",padx=(0,8));self._mini_orb.start()

    def send_message(self):
        if self.processing or not hasattr(self,"entry"):return
        self.voice.cancel_speech()
        text=self.entry.get().strip()
        if not text or text=="Pergunte algo à STAR...":return
        self.entry.delete(0,tk.END);self._activate_conversation();self._append_user(text)
        try:
            self.memory.save("Você", text)
        except Exception as exc:
            LOGGER.warning("Falha ao persistir mensagem do usuário: %s", exc)
        self.processing=True;self.entry.config(state=tk.DISABLED);self.send_button.config(state=tk.DISABLED);self._set_status("PROCESSANDO",self.gold);self._load_avatar("thinking");threading.Thread(target=self._process_message,args=(text,),daemon=True).start()

    def _process_message(self,text):
        try:self.response_queue.put(("success",self.brain.process(text)))
        except Exception as exc:self.response_queue.put(("error",str(exc)))

    def _check_response_queue(self):
        if self._closing:return
        try:
            while True:
                kind,result=self.response_queue.get_nowait()
                if kind=="vad_start":
                    self._load_avatar("listening")
                    self._set_status("OUVINDO", self.green)
                    if result and self.current_screen=="chat":
                        self._activate_conversation();self._append_system("🎙️ Interrompi minha fala para ouvir você.")
                elif kind=="vad_transcript":
                    text,duration_ms=result
                    if self.current_screen=="chat":
                        self._set_status("INTERPRETANDO FALA", self.gold)
                    self.turn_assembler.feed(str(text))
                elif kind=="vad_utterance":
                    text=str(result).strip()
                    if text and self.current_screen=="chat":
                        if self.processing:
                            self._pending_voice_transcript=text
                            self._append_system("🎙️ Entendi seu próximo turno. Vou responder assim que concluir o processamento atual.")
                        else:
                            self.entry.config(state=tk.NORMAL);self.entry.delete(0,tk.END);self.entry.insert(0,text);self.entry.config(fg=self.text);self.send_message()
                elif kind=="vad_error":
                    if self.current_screen=="chat":
                        self._activate_conversation();self._append_system(f"🎙️ Falha no modo mãos-livres: {result}")
                    self._set_status("ATENÇÃO", self.red)
                elif kind=="transcript":
                    if self.current_screen=="chat":
                        self.entry.config(state=tk.NORMAL);self.entry.delete(0,tk.END);self.entry.insert(0,str(result));self.entry.config(fg=self.text);self.send_message()
                elif kind=="remote_voice_response":
                    transcript,response=result
                    self._activate_conversation();self._append_user(str(transcript));self._append_star(str(response))
                    self._load_avatar("speaking")
                    self.voice.speak_async(str(response),lambda ok,error:self.response_queue.put(("speech_result",(ok,error))))
                    self.processing=False
                    if self.current_screen=="chat":
                        self.entry.config(state=tk.NORMAL);self.send_button.config(state=tk.NORMAL);self._set_status("FALANDO",self.green);self.entry.focus_set()
                elif kind=="voice_error":
                    self._activate_conversation();self._append_system(f"🎤 Falha no reconhecimento: {result}");self.processing=False
                    if self.current_screen=="chat":self.entry.config(state=tk.NORMAL);self.send_button.config(state=tk.NORMAL)
                elif kind=="voice_test":
                    if isinstance(result, tuple) and len(result) == 3:
                        backend,ok,error=result
                    else:
                        backend="current";ok,error=result
                    self._set_voice_test_busy(False)
                    if error == "Fala cancelada.":
                        self._set_voice_test_message("⏹ Teste de voz interrompido.",None)
                    elif ok:
                        self._set_voice_test_message(f"🔊 Voz funcionando: {self.voice.last_tts_engine}.",True)
                    else:
                        self._set_voice_test_message(f"🔊 Falha em {backend}: {error or 'erro desconhecido'}",False)
                    self._set_status("ONLINE" if self.online_mode else "OFFLINE",self.green if self.online_mode else self.red)
                elif kind=="speech_result":
                    ok,error=result
                    if not ok and self.current_screen=="chat":self._append_system(f"🔊 A resposta foi gerada, mas a voz falhou: {error}")
                    self._load_avatar("neutral")
                    if self.current_screen=="chat":
                        if self.hands_free:self._set_status("MÃOS-LIVRES",self.green)
                        else:self._set_status("OFFLINE" if not self.online_mode else "ONLINE",self.red if not self.online_mode else self.green)
                elif kind=="success":
                    response=str(result);self._append_star(response)
                    try:
                        self.memory.save("STAR", response)
                    except Exception as exc:
                        LOGGER.warning("Falha ao persistir resposta da STAR: %s", exc)
                    self._load_avatar("speaking");self.voice.speak_async(response,lambda ok,error:self.response_queue.put(("speech_result",(ok,error))));self.processing=False
                    if self.current_screen=="chat":self.entry.config(state=tk.NORMAL);self.send_button.config(state=tk.NORMAL);self._set_status("FALANDO",self.green);self.entry.focus_set()
                    if self._pending_voice_transcript:self.window.after(10,self._flush_pending_voice_transcript)
                elif kind=="error":
                    self._append_system(f"Erro ao processar: {result}");self._load_avatar("neutral");self.processing=False
                    if self.current_screen=="chat":self.entry.config(state=tk.NORMAL);self.send_button.config(state=tk.NORMAL)
        except queue.Empty:pass
        if not self._closing:
            try:self.window.after(60,self._check_response_queue)
            except tk.TclError:pass

    def _set_voice_test_message(self,message,ok):
        label=self.voice_test_label
        color=self.green if ok is True else self.red if ok is False else self.gold
        if label is not None:
            try:
                if label.winfo_exists():label.config(text=message,fg=color);return
            except tk.TclError:pass
        if self.current_screen=="chat":self._append_system(message)

    def _set_voice_test_busy(self,busy):
        state=tk.DISABLED if busy else tk.NORMAL
        for button in getattr(self,"voice_test_buttons",[]):
            try:
                if button.winfo_exists():button.config(state=state)
            except tk.TclError:pass
        stop=getattr(self,"voice_test_stop_button",None)
        if stop is not None:
            try:
                if stop.winfo_exists():stop.config(state=tk.NORMAL if busy else tk.DISABLED)
            except tk.TclError:pass

    def _voice_output_description(self):
        if self.profile == "mobile":
            return "saída remota pelo Core do PC"
        try:
            info=audio_device_info("output")
            name=info.get("name") or "dispositivo de áudio"
            if "primário" in name.casefold() or "primary" in name.casefold():
                return f"{name} (acompanha o padrão do Windows)"
            return f"{name} (índice {info.get('index')})"
        except Exception as exc:
            LOGGER.warning("Não foi possível resolver a saída de áudio: %s",exc)
            return "saída do sistema não resolvida"

    def _append(self,name,text,tag):
        if not self.chat:return
        try:self.chat.configure(state=tk.NORMAL);self.chat.insert(tk.END,name+"\n",tag);self.chat.insert(tk.END,text+"\n\n","message");self.chat.configure(state=tk.DISABLED);self.chat.see(tk.END)
        except tk.TclError:self.chat=None
    def _append_user(self,text):self._append("Você",text,"user")
    def _append_star(self,text):self._append("⭐ STAR",text,"star")
    def _append_system(self,text):self._append("SISTEMA",text,"system")

    def _load_display_avatar(self):
        skin=PROJECT_ROOT/"SKINS"/self.selected_skin
        orb=getattr(self,"_orb",None)
        if skin.exists() and orb is not None and hasattr(orb,"set_portrait"):
            orb.set_portrait(skin)
            return
        if skin.exists():
            try:
                with Image.open(skin) as source:
                    image = source.convert("RGBA")
                image.thumbnail((300,330),Image.Resampling.LANCZOS)
                self.avatar_photo=ImageTk.PhotoImage(image)
                self.avatar_label.config(image=self.avatar_photo,text="")
                return
            except (OSError, ValueError, UnidentifiedImageError) as exc:
                LOGGER.warning("Skin inválida ou ilegível %s: %s", skin, exc)
        self._load_avatar("neutral")
    def _load_avatar(self,emotion="neutral"):
        path=self.avatar.avatar_dir/f"{emotion}.png"
        if not path.exists() or path.stat().st_size == 0:path=self.avatar.avatar_dir/"neutral.png"
        orb=getattr(self,"_orb",None)
        if orb is not None and hasattr(orb,"set_portrait"):
            if path.exists():orb.set_portrait(path)
            self._orb_state(emotion)
            return
        try:
            with Image.open(path) as source:
                image = source.convert("RGBA")
            image.thumbnail((250,250),Image.Resampling.LANCZOS)
            self.avatar_photo=ImageTk.PhotoImage(image)
            self.avatar_label.config(image=self.avatar_photo,text="")
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            LOGGER.warning("Avatar inválido ou ilegível %s: %s", path, exc)
            try:
                self.avatar_label.config(text="⭐\nSTAR",fg=self.star,font=("Segoe UI",28,"bold"))
            except tk.TclError:
                pass
        self._orb_state(emotion)
    def _set_status(self,text,color):
        label=getattr(self,"status_label",None)
        if label:
            try:
                status_text = f"● {text}" if self.profile == "mobile" else f"● V{VERSION} • {text}"
                label.config(text=status_text,fg=color)
            except tk.TclError:pass

    def show_settings(self):
        self.clear_screen();self.current_screen="settings";root=tk.Frame(self.window,bg=self.bg);root.pack(fill="both",expand=True);self._header(root);settings_pad = 20 if self.profile == "mobile" else 80;body=tk.Frame(root,bg=self.bg);body.pack(fill="both",expand=True,padx=settings_pad,pady=24 if self.profile == "mobile" else 35);tk.Label(body,text="CONFIGURAÇÕES",fg=self.star,bg=self.bg,font=("Segoe UI",22 if self.profile == "mobile" else 27,"bold")).pack(anchor="w")
        mode=tk.Frame(body,bg=self.panel,padx=22,pady=18);mode.pack(fill="x",pady=(18,12));tk.Label(mode,text="MODO DE FUNCIONAMENTO",fg=self.text,bg=self.panel,font=("Segoe UI",12,"bold")).pack(anchor="w");row=tk.Frame(mode,bg=self.panel);row.pack(anchor="w",pady=12);self.online_btn=self._button(row,"🟢 ONLINE",lambda:self._set_mode(True));self.online_btn.pack(side="left",padx=(0,10));self.offline_btn=self._button(row,"🔴 OFFLINE",lambda:self._set_mode(False));self.offline_btn.pack(side="left");self._refresh_mode_buttons();tk.Label(mode,text="O modo online controla recursos de internet. A voz da STAR é local nos dois modos.",fg=self.muted,bg=self.panel).pack(anchor="w")
        voicebox=tk.Frame(body,bg=self.panel,padx=22,pady=18);voicebox.pack(fill="x",pady=12)
        tk.Label(voicebox,text="🎙️ VOZ DA STAR",fg=self.star,bg=self.panel,font=("Segoe UI",13,"bold")).pack(anchor="w")
        tk.Label(voicebox,text=f"Entrada: faster-whisper {STT_MODEL} PT-BR • Conversa: {self.voice.tts_description}",fg=self.text,bg=self.panel).pack(anchor="w",pady=(8,3))
        tk.Label(voicebox,text=f"Saída: {self._voice_output_description()}",fg=self.muted,bg=self.panel,wraplength=760,justify="left").pack(anchor="w",pady=(0,7))
        voice_row=tk.Frame(voicebox,bg=self.panel);voice_row.pack(anchor="w",pady=(2,8))
        self._button(voice_row,"⚡ USAR RÁPIDA",lambda:self._set_voice_mode("fast"),small=True).pack(side="left",padx=(0,8))
        self._button(voice_row,"⭐ USAR OFICIAL",lambda:self._set_voice_mode("official"),small=True).pack(side="left")
        tk.Label(voicebox,text="Seleção e teste são separados. A voz oficial Chatterbox pode levar vários minutos no primeiro carregamento em CPU.",fg=self.muted,bg=self.panel,wraplength=760,justify="left").pack(anchor="w")
        test_row=tk.Frame(voicebox,bg=self.panel);test_row.pack(anchor="w",pady=(12,4))
        self.voice_test_buttons=[]
        if hasattr(self.voice,"test_backend_async"):
            sapi_name=getattr(getattr(self.voice,"fallback",None),"voice_name",None) or "Windows SAPI"
            for text,backend in (("▶ PIPER PT-BR","piper"),(f"▶ {sapi_name[:22]}","sapi"),("▶ OFICIAL STAR","official")):
                button=self._button(test_row,text,lambda b=backend:self._test_voice_backend(b),small=True)
                button.pack(side="left",padx=(0,8));self.voice_test_buttons.append(button)
        else:
            button=self._button(test_row,"▶ TESTAR SAÍDA REMOTA",self._test_voice,small=True)
            button.pack(side="left",padx=(0,8));self.voice_test_buttons.append(button)
        self.voice_test_stop_button=self._button(test_row,"■ PARAR TESTE",self._stop_voice_test,small=True)
        self.voice_test_stop_button.pack(side="left");self.voice_test_stop_button.config(state=tk.DISABLED)
        self.voice_test_label=tk.Label(voicebox,text="Escolha uma voz acima para testar.",fg=self.muted,bg=self.panel,wraplength=760,justify="left");self.voice_test_label.pack(anchor="w")
        info=tk.Frame(body,bg=self.panel,padx=22,pady=16);info.pack(fill="x",pady=12)
        for name,value in (("Versão",f"V{VERSION}"),("Conhecimento local","ATIVO"),("Modo de voz",self.voice.mode.upper()),("Reconhecimento local","PRONTO" if self.voice.stt_configured else "INSTALAÇÃO PENDENTE")):
            line=tk.Frame(info,bg=self.panel);line.pack(fill="x",pady=4);tk.Label(line,text=name,fg=self.muted,bg=self.panel).pack(side="left");tk.Label(line,text=value,fg=self.green if value in {"ATIVO","PRONTO","Piper PT-BR (rápido)"} else self.gold,bg=self.panel,font=("Segoe UI",10,"bold")).pack(side="right")
        self._button(body,"VOLTAR AO CHAT",self.show_chat).pack(anchor="w",pady=10)

    def _test_voice(self):
        self._set_voice_test_busy(True)
        self._set_voice_test_message("🔊 Testando a saída de voz selecionada...",None)
        self._set_status("TESTANDO VOZ",self.gold)
        self.voice.test_audio_async(
            lambda ok,error:self.response_queue.put(("voice_test",("current",ok,error)))
        )

    def _test_voice_backend(self,backend):
        names={"piper":"Piper PT-BR","sapi":"Windows SAPI","official":"voz oficial STAR"}
        label=names.get(backend,backend)
        self._set_voice_test_busy(True)
        if backend=="official":
            message="⭐ Carregando a voz oficial STAR. Em CPU, o primeiro teste pode levar vários minutos; use PARAR TESTE para cancelar."
        else:
            message=f"🔊 Testando {label}..."
        self._set_voice_test_message(message,None)
        self._set_status("TESTANDO VOZ",self.gold)
        try:
            tester=getattr(self.voice,"test_backend_async")
            tester(
                backend,
                lambda ok,error,b=backend:self.response_queue.put(("voice_test",(b,ok,error))),
            )
        except Exception as exc:
            self._set_voice_test_busy(False)
            self._set_voice_test_message(f"🔊 Não foi possível iniciar {label}: {exc}",False)

    def _test_official_voice(self):
        if hasattr(self.voice,"test_backend_async"):
            self._test_voice_backend("official")
            return
        self._set_voice_test_busy(True)
        self._set_voice_test_message("⭐ Preparando a voz oficial...",None)
        self.voice.test_official_audio_async(
            lambda ok,error:self.response_queue.put(("voice_test",("official",ok,error)))
        )

    def _stop_voice_test(self):
        try:
            self.voice.cancel_speech(reason="voice_test_stop")
        except Exception as exc:
            LOGGER.warning("Falha ao interromper teste de voz: %s",exc)
        self._set_voice_test_busy(False)
        self._set_voice_test_message("⏹ Teste de voz interrompido.",None)
        self._set_status("ONLINE" if self.online_mode else "OFFLINE",self.green if self.online_mode else self.red)
    def _set_voice_mode(self,mode):
        self.voice.set_voice_mode(mode);self._save_voice_mode();self.show_settings()
    def _set_mode(self,online):
        self.online_mode=bool(online)
        try:self.brain.network_enabled = self.online_mode
        except Exception as exc:LOGGER.warning("Falha ao alterar modo de rede da superfície: %s", exc)
        self._refresh_mode_buttons();self._set_status("ONLINE" if self.online_mode else "OFFLINE",self.green if self.online_mode else self.red)
    def _refresh_mode_buttons(self):
        if hasattr(self,"online_btn"):self.online_btn.config(bg=theme.TOGGLE_ON if self.online_mode else theme.PANEL_EDGE)
        if hasattr(self,"offline_btn"):self.offline_btn.config(bg=theme.TOGGLE_OFF_ALERT if not self.online_mode else theme.PANEL_EDGE)

    def show_islands(self):
        self.clear_screen();self.current_screen="islands";root=tk.Frame(self.window,bg=self.bg);root.pack(fill="both",expand=True);self._header(root);body=tk.Frame(root,bg=self.bg);body.pack(fill="both",expand=True,padx=35,pady=20);tk.Label(body,text="HUB • STAR WORLD",fg=self.star,bg=self.bg,font=("Segoe UI",24,"bold")).pack(anchor="w",pady=(0,12))
        try:
            from core.islands import get_islands
            data = get_islands()
        except Exception as exc:
            LOGGER.error("Falha ao carregar ilhas da STAR: %s", exc)
            data = {}
        cards=tk.Frame(body,bg=self.bg);cards.pack(fill="both",expand=True)
        for column in range(3):cards.grid_columnconfigure(column,weight=1)
        for i,(key,item) in enumerate(data.items()):
            card=tk.Frame(cards,bg=self.panel,padx=16,pady=14);card.grid(row=i//3,column=i%3,sticky="nsew",padx=6,pady=6);tk.Label(card,text=f"{item.get('icon','🏝️')} {item.get('name',key)}",fg=self.star,bg=self.panel,font=("Segoe UI",14,"bold")).pack(anchor="w");tk.Label(card,text=item.get('description',''),fg=self.text,bg=self.panel,wraplength=270,justify="left").pack(anchor="w",pady=7)
            if key.lower() in {"house","casa"}:self._button(card,"ENTRAR NA CASA",self.show_house,small=True).pack(anchor="w")
            else:tk.Label(card,text="🟢 DISPONÍVEL" if item.get('status')=='installed' else "🔒 AGUARDANDO CONHECIMENTO",fg=self.green if item.get('status')=='installed' else self.gold,bg=self.panel,font=("Segoe UI",8,"bold")).pack(anchor="w")

    def show_house(self):
        self.clear_screen();self.current_screen="house";root=tk.Frame(self.window,bg=self.bg);root.pack(fill="both",expand=True);self._header(root);body=tk.Frame(root,bg=self.bg);body.pack(fill="both",expand=True,padx=70,pady=45);tk.Label(body,text="🏠 CASA",fg=self.star,bg=self.bg,font=("Segoe UI",28,"bold")).pack(anchor="w");tk.Label(body,text="O espaço pessoal da STAR dentro do STAR WORLD.",fg=self.muted,bg=self.bg).pack(anchor="w",pady=(4,24));grid=tk.Frame(body,bg=self.bg);grid.pack(fill="x")
        for i,(title,desc,cmd) in enumerate((("🍳 COZINHA","Receitas e experimentação gastronômica.",None),("👕 CLOSET","Skins e personalização visual da STAR.",self.show_closet))):
            c=tk.Frame(grid,bg=self.panel,padx=22,pady=20,width=360,height=180);c.grid(row=0,column=i,padx=(0,14));c.grid_propagate(False);tk.Label(c,text=title,fg=self.star,bg=self.panel,font=("Segoe UI",16,"bold")).pack(anchor="w");tk.Label(c,text=desc,fg=self.text,bg=self.panel,wraplength=290,justify="left").pack(anchor="w",pady=12)
            if cmd:self._button(c,"ABRIR CLOSET",cmd).pack(anchor="w")

    def show_closet(self):
        self.clear_screen();self.current_screen="closet";root=tk.Frame(self.window,bg=self.bg);root.pack(fill="both",expand=True);self._header(root);body=tk.Frame(root,bg=self.bg);body.pack(fill="both",expand=True);top=tk.Frame(body,bg=self.bg);top.pack(fill="x",padx=45,pady=(25,0));tk.Label(top,text="👕 CLOSET",fg=self.star,bg=self.bg,font=("Segoe UI",27,"bold")).pack(anchor="w");tk.Label(top,text="Use as setas para navegar pelas aparências da STAR.",fg=self.muted,bg=self.bg).pack(anchor="w",pady=(3,8));self.closet_files=[p for p in sorted((PROJECT_ROOT/"SKINS").glob("*")) if p.suffix.lower() in {".png",".jpg",".jpeg",".webp"}]
        if not self.closet_files:tk.Label(body,text="Nenhuma skin encontrada.",fg=self.red,bg=self.bg).pack(pady=80);return
        try:self.closet_index=[p.name for p in self.closet_files].index(self.selected_skin)
        except ValueError:self.closet_index=0
        area=tk.Frame(body,bg=self.bg);area.pack(fill="both",expand=True);self._button(area,"◀",lambda:self._change_closet_skin(-1)).place(relx=.18,rely=.5,anchor="center");self._button(area,"▶",lambda:self._change_closet_skin(1)).place(relx=.82,rely=.5,anchor="center");card=tk.Frame(area,bg=theme.PANEL,padx=18,pady=16);card.place(relx=.5,rely=.47,anchor="center",width=430,height=455);self.closet_image=tk.Label(card,bg=theme.PANEL);self.closet_image.pack(expand=True,fill="both");self.closet_name=tk.Label(card,fg=self.text,bg=theme.PANEL,font=("Segoe UI",14,"bold"));self.closet_name.pack(pady=(8,4));self.closet_state=tk.Label(card,fg=self.green,bg=theme.PANEL,font=("Segoe UI",9,"bold"));self.closet_state.pack();self.closet_photo=None;bottom=tk.Frame(body,bg=self.bg);bottom.pack(fill="x",padx=45,pady=(0,22));self.select_skin_button=self._button(bottom,"SELECIONAR ESTA SKIN",self._confirm_closet_skin);self.select_skin_button.pack(side="left",padx=(0,10));self._button(bottom,"SAIR DO CLOSET",self.show_house).pack(side="left");self._render_closet_skin()
    def _change_closet_skin(self,step):self.closet_index=(self.closet_index+step)%len(self.closet_files);self._render_closet_skin()
    def _render_closet_skin(self):
        p=self.closet_files[self.closet_index]
        try:
            with Image.open(p) as source:
                im = source.convert("RGBA")
            im.thumbnail((360,330),Image.Resampling.LANCZOS)
            self.closet_photo=ImageTk.PhotoImage(im)
            self.closet_image.config(image=self.closet_photo,text="")
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            LOGGER.warning("Skin do closet inválida ou ilegível %s: %s", p, exc)
            self.closet_image.config(image="",text="Não foi possível abrir esta skin",fg=self.red)
        self.closet_name.config(text=p.stem.replace("_"," ").title());active=p.name==self.selected_skin;self.closet_state.config(text="✓ SKIN ATUALMENTE SELECIONADA" if active else f"{self.closet_index+1} de {len(self.closet_files)}");self.select_skin_button.config(text="SKIN SELECIONADA" if active else "SELECIONAR ESTA SKIN",bg=theme.TOGGLE_ON if active else theme.PANEL_EDGE)
    def _confirm_closet_skin(self):self.selected_skin=self.closet_files[self.closet_index].name;self._save_skin_selection();self._render_closet_skin()
    def _button(self,parent,text,command,small=False):return tk.Button(parent,text=text,command=command,bg=theme.PANEL_EDGE,fg=self.text,activebackground=theme.ORB_MID,activeforeground=self.text,relief=tk.FLAT,borderwidth=0,cursor="hand2",font=("Segoe UI",9 if small else 10,"bold"),padx=14,pady=7)
    def toggle_maximize(self,_event=None):
        if self.is_maximized:self.restore_normal_size()
        else:self.normal_size=(self.window.winfo_width(),self.window.winfo_height());self.window.state("zoomed");self.is_maximized=True
    def restore_normal_size(self,_event=None):
        if self.is_maximized:
            self.window.state("normal")
            min_w, min_h = ((390, 680) if self.profile == "mobile" else (900, 600))
            self.window.geometry(f"{max(min_w,self.normal_size[0])}x{max(min_h,self.normal_size[1])}")
            self.is_maximized=False
    @staticmethod
    def _cleanup(label, callback):
        try:
            callback()
        except Exception as exc:
            LOGGER.warning("Falha de cleanup em %s: %s", label, exc)

    def close(self):
        if self._closing:
            return
        self._closing = True
        self._cleanup("visuals", self._stop_visuals)
        self._cleanup("vad", self.vad.stop)
        self._cleanup("turn_assembler", self.turn_assembler.cancel)
        if self.recording:
            self._cleanup("recorder", self.recorder.stop_to_wav)
        self._cleanup("voice", self.voice.close)
        self._cleanup("memory", self.memory.close)
        close_surface = getattr(self.brain, "close_surface", None)
        if callable(close_surface):
            self._cleanup("surface", close_surface)
        try:
            self.window.destroy()
        except tk.TclError:
            pass

    def run(self):
        self.window.mainloop()
