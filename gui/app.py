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

from config import APP_NAME, WINDOW_HEIGHT, WINDOW_WIDTH, MENU_HEIGHT, MENU_WIDTH, VERSION
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
        self.response_queue = queue.Queue()
        self.current_screen = "menu"
        self.has_messages = False
        self.chat = None
        self._closing = False
        self._speech_lock = threading.Lock()

        self.bg = "#0b1018"
        self.panel = "#131c29"
        self.text = "#edf3fb"
        self.muted = "#9aa8bb"
        self.star = "#8fd0ff"
        self.user = "#c9b8ff"
        self.green = "#76e2a0"
        self.red = "#ff7c87"
        self.gold = "#ffd36e"

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
        self.avatar_photo = None
        self.closet_photo = None
        self.selected_skin = self._load_skin_selection()

        self.show_menu()
        self.window.after(60, self._check_response_queue)

    def _load_skin_selection(self):
        path = PROJECT_ROOT / "config_skin.json"
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("skin", "original.jpeg")
        except Exception:
            return "original.jpeg"

    def _save_skin_selection(self):
        try:
            (PROJECT_ROOT / "config_skin.json").write_text(
                json.dumps({"skin": self.selected_skin}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def clear_screen(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        self.chat = None
        self.has_messages = False
        # Não mantemos referências a widgets de telas destruídas.
        if hasattr(self, "voice_test_label"):
            self.voice_test_label = None

    def show_menu(self):
        self.clear_screen()
        self.current_screen = "menu"
        if not self.is_maximized:
            self.window.geometry(f"{MENU_WIDTH}x{MENU_HEIGHT}")
        frame = tk.Frame(self.window, bg=self.bg)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="⭐  STAR", fg=self.star, bg=self.bg, font=("Segoe UI", 34, "bold")).pack(pady=(120, 20))
        tk.Label(frame, text="System for Thought, Analysis and Response", fg=self.muted, bg=self.bg, font=("Segoe UI", 11)).pack(pady=(0, 45))
        for label, command in (("INICIAR", self.show_chat), ("CONFIGURAÇÕES", self.show_settings), ("SAIR", self.close)):
            self._button(frame, label, command).pack(pady=7)

    def _header(self, parent):
        header = tk.Frame(parent, bg="#172231", height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="⭐  STAR", fg=self.star, bg="#172231", font=("Segoe UI", 20, "bold")).pack(side="left", padx=18)
        status = "ONLINE" if self.online_mode else "OFFLINE"
        color = self.green if self.online_mode else self.red
        self.status_label = tk.Label(header, text=f"● V{VERSION} • {status}", fg=color, bg="#172231", font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side="right", padx=18)
        self._button(header, "⚙", self.show_settings, small=True).pack(side="right", padx=4, pady=8)
        self._button(header, "◈ ILHAS", self.show_islands, small=True).pack(side="right", padx=4, pady=8)
        self._button(header, "CHAT", self.show_chat, small=True).pack(side="right", padx=4, pady=8)
        self._button(header, "MENU", self.show_menu, small=True).pack(side="right", padx=4, pady=8)

    def _gradient(self, parent):
        canvas = tk.Canvas(parent, bg=self.bg, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.tk.call("lower", str(canvas))
        def draw(_event=None):
            canvas.delete("gradient")
            width = max(canvas.winfo_width(), 1)
            height = max(canvas.winfo_height(), 1)
            for i in range(70):
                t = i / 69
                r = int(12 + 25 * (1 - t)); g = int(18 + 50 * (1 - t)); b = int(28 + 90 * (1 - t))
                y = int(i * height / 70)
                canvas.create_rectangle(0, y, width, y + height / 70 + 2, fill=f"#{r:02x}{g:02x}{b:02x}", outline="", tags="gradient")
        canvas.bind("<Configure>", draw)
        self.window.after(20, draw)

    def show_chat(self):
        self.clear_screen()
        self.current_screen = "chat"
        root = tk.Frame(self.window, bg=self.bg)
        root.pack(fill="both", expand=True)
        self._gradient(root)
        self._header(root)
        self.stage = tk.Frame(root, bg=self.bg)
        self.stage.pack(fill="both", expand=True)
        self.center = tk.Frame(self.stage, bg=self.bg)
        self.center.place(relx=0.5, rely=0.47, anchor="center")
        self.avatar_label = tk.Label(self.center, bg=self.bg)
        self.avatar_label.pack()
        self._load_display_avatar()
        self._build_input(root)
        self.entry.focus_set()

    def _build_input(self, root):
        bottom = tk.Frame(root, bg=self.bg, height=92)
        bottom.pack(fill="x", side="bottom", padx=22, pady=(0, 18))
        bottom.pack_propagate(False)
        box = tk.Frame(bottom, bg="#cbd9e8", padx=1, pady=1)
        box.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.64, height=62)
        inner = tk.Frame(box, bg="#25364b")
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text="+", fg="#d8e7f5", bg="#25364b", font=("Segoe UI", 23)).pack(side="left", padx=(16, 8))
        self.entry = tk.Entry(inner, bg="#25364b", fg=self.text, insertbackground=self.text, relief=tk.FLAT, font=("Segoe UI", 12))
        self.entry.pack(side="left", fill="both", expand=True, pady=7)
        self.entry.insert(0, "Pergunte algo à STAR...")
        self.entry.config(fg="#aebdcd")
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)
        self.entry.bind("<Return>", self._on_enter)
        self.mic = tk.Button(inner, text="🎤", command=self.toggle_microphone, bg="#25364b", fg="#d8e7f5", relief=tk.FLAT, borderwidth=0, font=("Segoe UI", 14), cursor="hand2")
        self.mic.pack(side="right", padx=4)
        self.send_button = tk.Button(inner, text="➜", command=self.send_message, bg="#395574", fg="white", relief=tk.FLAT, borderwidth=0, font=("Segoe UI", 16, "bold"), width=3, cursor="hand2")
        self.send_button.pack(side="right", padx=(2, 8), pady=7)

    def _clear_placeholder(self, _event=None):
        if self.entry.get() == "Pergunte algo à STAR...":
            self.entry.delete(0, tk.END); self.entry.config(fg=self.text)

    def _restore_placeholder(self, _event=None):
        if not self.entry.get().strip():
            self.entry.insert(0, "Pergunte algo à STAR..."); self.entry.config(fg="#aebdcd")

    def _on_enter(self, _event=None):
        self.send_message(); return "break"

    def toggle_microphone(self):
        if not self.voice.stt_configured:
            self._activate_conversation(); self._append_system("🎤 Reconhecimento local ainda não instalado. Execute INSTALAR_VOZ.bat."); return
        if not self.recorder.available:
            self._activate_conversation(); self._append_system("🎤 Não consegui acessar o microfone. Verifique as dependências de áudio."); return
        if not self.recording:
            try:
                self.recorder.start(); self.recording = True
                self.mic.config(text="■", bg="#8b3340", fg="white")
                self._activate_conversation(); self._append_system("🎤 Estou ouvindo. Clique novamente quando terminar.")
                self._set_status("OUVINDO", self.green)
            except Exception as exc:
                self._activate_conversation(); self._append_system(f"🎤 Não consegui abrir o microfone: {exc}")
            return
        self.recording = False
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
                try: path.unlink(missing_ok=True)
                except Exception: pass

    def _activate_conversation(self):
        if self.has_messages or not hasattr(self, "stage"):
            return
        self.has_messages = True
        if hasattr(self, "center"):
            try: self.center.place_forget()
            except tk.TclError: pass
        self.chat = scrolledtext.ScrolledText(self.stage, wrap=tk.WORD, bg="#0e151f", fg=self.text, insertbackground=self.text, relief=tk.FLAT, borderwidth=0, font=("Segoe UI", 11), padx=28, pady=22)
        self.chat.pack(fill="both", expand=True, padx=80, pady=(25, 12))
        self.chat.configure(state=tk.DISABLED)
        self.chat.tag_configure("user", foreground=self.user, font=("Segoe UI", 10, "bold"))
        self.chat.tag_configure("star", foreground=self.star, font=("Segoe UI", 10, "bold"))
        self.chat.tag_configure("message", foreground=self.text, font=("Segoe UI", 11))
        self.chat.tag_configure("system", foreground=self.muted, font=("Segoe UI", 10))

    def send_message(self):
        if self.processing or not hasattr(self, "entry"):
            return
        text = self.entry.get().strip()
        if not text or text == "Pergunte algo à STAR...":
            return
        self.entry.delete(0, tk.END); self._activate_conversation(); self._append_user(text)
        try: self.memory.save("Você", text)
        except Exception: pass
        self.processing = True; self.entry.config(state=tk.DISABLED); self.send_button.config(state=tk.DISABLED)
        self._set_status("PROCESSANDO", self.gold); self._load_avatar("thinking")
        threading.Thread(target=self._process_message, args=(text,), daemon=True).start()

    def _process_message(self, text):
        try: self.response_queue.put(("success", self.brain.process(text)))
        except Exception as exc: self.response_queue.put(("error", str(exc)))

    def _voice_callback(self, ok, error):
        if not self._closing:
            self.response_queue.put(("speech_result", (ok, error)))

    def _check_response_queue(self):
        if self._closing:
            return
        try:
            while True:
                kind, result = self.response_queue.get_nowait()
                if kind == "transcript":
                    if self.current_screen == "chat" and hasattr(self, "entry"):
                        self.entry.config(state=tk.NORMAL); self.entry.delete(0, tk.END); self.entry.insert(0, str(result)); self.entry.config(fg=self.text)
                        self.send_button.config(state=tk.NORMAL)
                        self.send_message()
                elif kind == "voice_error":
                    self._activate_conversation(); self._append_system(f"🎤 Falha no reconhecimento: {result}")
                    self.processing = False
                    if self.current_screen == "chat": self.entry.config(state=tk.NORMAL); self.send_button.config(state=tk.NORMAL)
                elif kind == "voice_test":
                    ok, error = result
                    message = "🔊 Voz da STAR funcionando." if ok else f"🔊 Falha na voz: {error}"
                    self._set_voice_test_message(message, ok)
                elif kind == "speech_result":
                    ok, error = result
                    if self.current_screen == "chat": self._set_status("OFFLINE", self.red) if ok else self._set_status("VOZ ERRO", self.red)
                    if not ok: self._append_system(f"🔊 A resposta foi gerada, mas a voz falhou: {error}")
                elif kind == "success":
                    response = str(result); self._append_star(response)
                    try: self.memory.save("STAR", response)
                    except Exception: pass
                    self._load_avatar("speaking")
                    # O TTS é rápido e local; não bloqueia a UI.
                    self.voice.speak_async(response, self._voice_callback)
                    self.processing = False
                    if self.current_screen == "chat":
                        self.entry.config(state=tk.NORMAL); self.send_button.config(state=tk.NORMAL); self._set_status("FALANDO", self.green); self.entry.focus_set()
                elif kind == "error":
                    self._append_system(f"Erro ao processar: {result}"); self._load_avatar("neutral"); self.processing = False
                    if self.current_screen == "chat": self.entry.config(state=tk.NORMAL); self.send_button.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        if not self._closing:
            try: self.window.after(60, self._check_response_queue)
            except tk.TclError: pass

    def _set_voice_test_message(self, message, ok):
        label = getattr(self, "voice_test_label", None)
        if label is not None:
            try:
                if int(label.winfo_exists()) == 1:
                    label.config(text=message, fg=self.green if ok else self.red)
                    return
            except (tk.TclError, AttributeError):
                pass
        if self.current_screen == "chat": self._append_system(message)

    def _append(self, name, text, tag):
        if not self.chat: return
        try:
            self.chat.configure(state=tk.NORMAL); self.chat.insert(tk.END, name + "\n", tag); self.chat.insert(tk.END, text + "\n\n", "message"); self.chat.configure(state=tk.DISABLED); self.chat.see(tk.END)
        except tk.TclError:
            self.chat = None

    def _append_user(self, text): self._append("Você", text, "user")
    def _append_star(self, text): self._append("⭐ STAR", text, "star")
    def _append_system(self, text): self._append("SISTEMA", text, "system")

    def _load_display_avatar(self):
        skin = PROJECT_ROOT / "SKINS" / self.selected_skin
        if skin.exists():
            try:
                image = Image.open(skin).convert("RGBA"); image.thumbnail((300, 330), Image.Resampling.LANCZOS); self.avatar_photo = ImageTk.PhotoImage(image); self.avatar_label.config(image=self.avatar_photo, text=""); return
            except Exception: pass
        self._load_avatar("neutral")

    def _load_avatar(self, emotion="neutral"):
        path = self.avatar.avatar_dir / f"{emotion}.png"
        if not path.exists(): path = self.avatar.avatar_dir / "neutral.png"
        try:
            image = Image.open(path).convert("RGBA"); image.thumbnail((250, 250), Image.Resampling.LANCZOS); self.avatar_photo = ImageTk.PhotoImage(image); self.avatar_label.config(image=self.avatar_photo, text="")
        except Exception:
            if hasattr(self, "avatar_label"):
                try: self.avatar_label.config(text="⭐\nSTAR", fg=self.star, font=("Segoe UI", 28, "bold"))
                except tk.TclError: pass

    def _set_status(self, text, color):
        if hasattr(self, "status_label"):
            try: self.status_label.config(text=f"● V{VERSION} • {text}", fg=color)
            except tk.TclError: pass

    def show_settings(self):
        self.clear_screen(); self.current_screen = "settings"
        root = tk.Frame(self.window, bg=self.bg); root.pack(fill="both", expand=True); self._header(root)
        body = tk.Frame(root, bg=self.bg); body.pack(fill="both", expand=True, padx=80, pady=35)
        tk.Label(body, text="CONFIGURAÇÕES", fg=self.star, bg=self.bg, font=("Segoe UI", 27, "bold")).pack(anchor="w")
        mode = tk.Frame(body, bg=self.panel, padx=22, pady=18); mode.pack(fill="x", pady=(18, 12))
        tk.Label(mode, text="MODO DE FUNCIONAMENTO", fg=self.text, bg=self.panel, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        row = tk.Frame(mode, bg=self.panel); row.pack(anchor="w", pady=12)
        self.online_btn = self._button(row, "🟢 ONLINE", lambda: self._set_mode(True)); self.online_btn.pack(side="left", padx=(0, 10))
        self.offline_btn = self._button(row, "🔴 OFFLINE", lambda: self._set_mode(False)); self.offline_btn.pack(side="left")
        self._refresh_mode_buttons()
        tk.Label(mode, text="Recursos online podem ser ativados separadamente. A voz padrão da STAR é local.", fg=self.muted, bg=self.panel, wraplength=760, justify="left").pack(anchor="w")
        voicebox = tk.Frame(body, bg=self.panel, padx=22, pady=18); voicebox.pack(fill="x", pady=12)
        tk.Label(voicebox, text="🎙️ VOZ DA STAR", fg=self.star, bg=self.panel, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(voicebox, text="Entrada: faster-whisper tiny • Voz rápida: Piper PT-BR • Voz clonada: Chatterbox", fg=self.text, bg=self.panel).pack(anchor="w", pady=(8, 2))
        tk.Label(voicebox, text="Piper é o caminho de fala normal por ser leve. Chatterbox fica reservado para o modo de voz clonada, que é mais pesado em CPU.", fg=self.muted, bg=self.panel, wraplength=760, justify="left").pack(anchor="w")
        self._button(voicebox, "TESTAR VOZ DA STAR", self._test_voice).pack(anchor="w", pady=(12, 4))
        self.voice_test_label = tk.Label(voicebox, text="Pronto para testar.", fg=self.muted, bg=self.panel, wraplength=760, justify="left"); self.voice_test_label.pack(anchor="w")
        info = tk.Frame(body, bg=self.panel, padx=22, pady=16); info.pack(fill="x", pady=12)
        for name, value in (("Versão", f"V{VERSION}"),("Conhecimento local", "ATIVO"),("Voz rápida", "PRONTO" if self.voice.configured else "INSTALAÇÃO PENDENTE"),("Reconhecimento local", "PRONTO" if self.voice.stt_configured else "INSTALAÇÃO PENDENTE")):
            line = tk.Frame(info, bg=self.panel); line.pack(fill="x", pady=4)
            tk.Label(line, text=name, fg=self.muted, bg=self.panel).pack(side="left")
            tk.Label(line, text=value, fg=self.green if value in {"ATIVO", "PRONTO"} else self.gold, bg=self.panel, font=("Segoe UI", 10, "bold")).pack(side="right")
        self._button(body, "VOLTAR AO CHAT", self.show_chat).pack(anchor="w", pady=10)

    def _test_voice(self):
        self._set_voice_test_message("🔊 Gerando teste da voz rápida...", True)
        self._set_status("TESTANDO VOZ", self.gold)
        self.voice.test_audio_async(lambda ok, error: self.response_queue.put(("voice_test", (ok, error))))

    # As funções visuais abaixo permanecem da versão anterior.
    def show_islands(self):
        self.clear_screen(); self.current_screen = "islands"
        root = tk.Frame(self.window, bg=self.bg); root.pack(fill="both", expand=True); self._header(root)
        tk.Label(root, text="STAR WORLD", fg=self.star, bg=self.bg, font=("Segoe UI", 27, "bold")).pack(pady=25)
        islands = self._get_islands_safe()
        for island in islands:
            self._button(root, str(island), lambda x=island: self._append_island(x)).pack(pady=5)
        self._button(root, "VOLTAR", self.show_chat).pack(pady=20)

    def _get_islands_safe(self):
        try:
            from core.islands import get_islands
            return get_islands()
        except Exception:
            return []

    def _append_island(self, island):
        self.show_chat(); self._activate_conversation(); self._append_system(f"🏝️ {island}")

    def _set_mode(self, online):
        self.online_mode = bool(online); self._refresh_mode_buttons(); self._set_status("ONLINE" if self.online_mode else "OFFLINE", self.green if self.online_mode else self.red)

    def _refresh_mode_buttons(self):
        if hasattr(self, "online_btn"):
            self.online_btn.config(relief=tk.SUNKEN if self.online_mode else tk.RAISED)
        if hasattr(self, "offline_btn"):
            self.offline_btn.config(relief=tk.SUNKEN if not self.online_mode else tk.RAISED)

    def _button(self, parent, text, command, small=False):
        return tk.Button(parent, text=text, command=command, bg="#26374d", fg=self.text, activebackground="#395574", activeforeground="white", relief=tk.FLAT, borderwidth=0, padx=14 if small else 22, pady=7 if small else 10, font=("Segoe UI", 9 if small else 10, "bold"), cursor="hand2")

    def toggle_maximize(self, _event=None):
        try:
            if self.is_maximized:
                self.window.state("normal"); self.window.geometry(f"{self.normal_size[0]}x{self.normal_size[1]}")
            else:
                self.normal_size = (self.window.winfo_width(), self.window.winfo_height()); self.window.state("zoomed")
            self.is_maximized = not self.is_maximized
        except tk.TclError: pass

    def restore_normal_size(self, _event=None):
        if self.is_maximized:
            self.toggle_maximize()

    def run(self):
        self.window.mainloop()

    def close(self):
        if self._closing: return
        self._closing = True
        try: self.recorder.stop_to_wav()
        except Exception: pass
        try: self.voice.close()
        except Exception: pass
        try: self.window.destroy()
        except tk.TclError: pass
