"""STAR Watch App V0.4 — app-first simulator.

A nova direção do projeto começa pelo relógio. Este módulo simula no PC a
experiência principal do STAR Watch sem duplicar identidade, memória ou raciocínio.
O STAR Core continua sendo reutilizado para respostas, voz e comandos já existentes.

Hardware ainda ausente (GPS, saúde, laser, câmera do relógio) é representado por
providers explícitos. O simulador nunca apresenta dado simulado como medição real.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "runtime" / "star_watch"
PEOPLE_FILE = RUNTIME_DIR / "people.json"
WATCH_APP_VERSION = "0.4.0"


@dataclass(frozen=True)
class WatchMode:
    key: str
    label: str
    short: str
    available: bool = True


WATCH_MODES = (
    WatchMode("voice", "VOZ", "VOZ"),
    WatchMode("search", "BUSCA", "BUSCA"),
    WatchMode("health", "SAÚDE", "SAÚDE"),
    WatchMode("gps", "GPS", "GPS"),
    WatchMode("vision", "VISÃO", "VISÃO"),
    WatchMode("people", "PEOPLE", "PEOPLE"),
    WatchMode("measure", "MEDIR", "MEDIR"),
    WatchMode("media", "MÍDIA", "MÍDIA"),
    WatchMode("weather", "CLIMA", "CLIMA"),
    WatchMode("settings", "CONFIG", "CONFIG"),
)


class StarWatchModel:
    """Estado independente de GUI para tornar o STAR Ring testável."""

    def __init__(self):
        self.selected_index = 0
        self.active_mode = "home"
        self.state = "idle"
        self.status = "PRONTA"
        self.simulation_enabled = True
        self.voice_output_enabled = True
        self.last_result = ""

    @property
    def selected_mode(self) -> WatchMode:
        return WATCH_MODES[self.selected_index]

    def rotate(self, steps: int) -> WatchMode:
        if not steps:
            return self.selected_mode
        self.selected_index = (self.selected_index + int(steps)) % len(WATCH_MODES)
        return self.selected_mode

    def press(self) -> str:
        if self.active_mode == "home":
            self.active_mode = self.selected_mode.key
        else:
            self.active_mode = "home"
        return self.active_mode

    def back(self) -> str:
        self.active_mode = "home"
        return self.active_mode

    def set_state(self, state: str, status: str) -> None:
        self.state = state
        self.status = status


class PeopleStore:
    """Cadastro pessoal local. Não faz reconhecimento facial nem envia dados."""

    def __init__(self, path: Path = PEOPLE_FILE):
        self.path = Path(path)

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def list(self) -> list[dict]:
        return list(self._load())

    def add(self, name: str, notes: str = "", image_path: str = "") -> dict:
        name = str(name or "").strip()
        if not name:
            raise ValueError("Nome é obrigatório.")
        rows = self._load()
        item = {
            "name": name,
            "notes": str(notes or "").strip(),
            "image_path": str(image_path or "").strip(),
        }
        rows.append(item)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return item


class SimulatorProviders:
    """Providers explícitos para funções dependentes de hardware real."""

    def __init__(self, model: StarWatchModel):
        self.model = model
        self._distance = 3.42

    def health(self) -> dict:
        if not self.model.simulation_enabled:
            return {"available": False, "message": "Sensor de saúde não conectado."}
        return {
            "available": True,
            "simulated": True,
            "heart_rate": 72,
            "spo2": 98,
            "message": "SIMULAÇÃO — aguardando sensores reais do relógio.",
        }

    def gps(self) -> dict:
        if not self.model.simulation_enabled:
            return {"available": False, "message": "GPS não conectado."}
        return {
            "available": True,
            "simulated": True,
            "speed_kmh": 0.0,
            "accuracy_m": 8.0,
            "message": "SIMULAÇÃO — posição real não está sendo lida no PC.",
        }

    def measure(self) -> dict:
        if not self.model.simulation_enabled:
            return {"available": False, "message": "Módulo laser não conectado."}
        # pequena variação visual para testar a UX sem fingir uma medição real
        self._distance += 0.01
        if self._distance > 3.49:
            self._distance = 3.42
        return {
            "available": True,
            "simulated": True,
            "distance_m": round(self._distance, 2),
            "message": "SIMULAÇÃO — futuro LaserDistanceProvider.",
        }

    def weather(self) -> dict:
        return {
            "available": False,
            "message": "Clima ainda sem provedor configurado. A interface já está pronta.",
        }


class StarWatchApp:
    SIZE = 560
    CX = 280
    CY = 280
    FACE_RADIUS = 236
    RING_RADIUS = 250

    COLORS = {
        "bg": "#03050A",
        "surface": "#0B1220",
        "text": "#FFFFFF",
        "muted": "#8B96A8",
        "cyan": "#72E8FF",
        "blue": "#4F7BFF",
        "violet": "#A276FF",
        "pink": "#FF79C8",
        "gold": "#F5D76E",
        "danger": "#FF6688",
    }

    def __init__(self):
        import tkinter as tk

        self.tk = tk
        self.model = StarWatchModel()
        self.providers = SimulatorProviders(self.model)
        self.people = PeopleStore()
        self.star = None
        self.voice_manager = None
        self.recorder = None
        self.recording = False
        self.closed = False
        self.phase = 0.0
        self.input_widget = None
        self.action_button = None
        self.message = "Gire o STAR Ring para escolher um modo."

        self.root = tk.Tk()
        self.root.title(f"STAR Watch App V{WATCH_APP_VERSION} — Simulator")
        self.root.geometry(f"{self.SIZE}x{self.SIZE}")
        self.root.resizable(False, False)
        self.root.configure(bg=self.COLORS["bg"])

        self.canvas = tk.Canvas(
            self.root,
            width=self.SIZE,
            height=self.SIZE,
            bg=self.COLORS["bg"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-1>", self._on_click)
        self.root.bind("<Left>", lambda _e: self.rotate(-1))
        self.root.bind("<Right>", lambda _e: self.rotate(1))
        self.root.bind("<Return>", lambda _e: self.press())
        self.root.bind("<space>", lambda _e: self.toggle_voice())
        self.root.bind("<BackSpace>", lambda _e: self.back())
        self.root.bind("<Escape>", lambda _e: self.back() if self.model.active_mode != "home" else self.close())
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.render()
        self._animate()

    def _core(self):
        if self.star is None:
            from main import create_star
            self.star = create_star()
        return self.star

    def _voice(self):
        if self.voice_manager is None:
            from voice.manager import VoiceManager
            self.voice_manager = VoiceManager()
        return self.voice_manager

    def _clear_controls(self):
        for widget in (self.input_widget, self.action_button):
            if widget is not None:
                try:
                    widget.destroy()
                except Exception:
                    pass
        self.input_widget = None
        self.action_button = None

    def run(self):
        self.root.mainloop()

    def rotate(self, steps: int):
        if self.model.active_mode != "home":
            # Em uma tela interna o giro continua trocando modos rapidamente.
            self.model.back()
        mode = self.model.rotate(steps)
        self.message = mode.label
        self.render()

    def press(self):
        if self.model.active_mode == "home":
            self.model.press()
            self.message = ""
            self.render()
            return
        if self.model.active_mode == "voice":
            self.toggle_voice()
            return
        if self.model.active_mode == "measure":
            data = self.providers.measure()
            self.message = self._provider_message(data, f"{data.get('distance_m', '--')} m")
            self.render()
            return
        if self.model.active_mode == "media":
            self._process_core("pause a musica")
            return
        self.back()

    def back(self):
        self.model.back()
        self.message = "Gire para escolher. Pressione para abrir."
        self.render()

    def _on_mousewheel(self, event):
        delta = getattr(event, "delta", 0)
        if delta:
            self.rotate(-1 if delta > 0 else 1)

    def _on_click(self, event):
        dx = event.x - self.CX
        dy = event.y - self.CY
        distance = math.hypot(dx, dy)
        if distance <= 112:
            self.press()
        elif 195 <= distance <= 268:
            # Clique na metade esquerda/direita simula giro físico do bezel.
            self.rotate(-1 if dx < 0 else 1)

    def _provider_message(self, data: dict, value: str = "") -> str:
        prefix = "SIMULADO • " if data.get("simulated") else ""
        if value:
            return f"{prefix}{value}\n{data.get('message', '')}".strip()
        return f"{prefix}{data.get('message', '')}".strip()

    def _process_core(self, text: str):
        text = str(text or "").strip()
        if not text:
            return
        self.model.set_state("thinking", "PENSANDO")
        self.message = text
        self.render()

        def work():
            try:
                answer = self._core().process(text, allow_actions=False)
            except Exception as exc:
                answer = f"Erro: {type(exc).__name__}: {exc}"
                state = "error"
            else:
                state = "speaking"
            self.root.after(0, lambda: self._finish_core(answer, state))

        threading.Thread(target=work, daemon=True, name="STAR-Watch-Core").start()

    def _finish_core(self, answer: str, state: str):
        self.model.set_state(state, "RESPONDENDO" if state == "speaking" else "ATENÇÃO")
        self.message = str(answer)
        self.render()
        if state == "speaking" and self.model.voice_output_enabled:
            try:
                self._voice().speak_async(str(answer), callback=lambda *_: self.root.after(0, self._idle))
                return
            except Exception:
                pass
        self.root.after(1400, self._idle)

    def _idle(self):
        if self.closed:
            return
        self.model.set_state("idle", "PRONTA")
        self.render()

    def toggle_voice(self):
        if self.model.active_mode not in {"home", "voice"}:
            self.model.active_mode = "voice"
        if self.recording:
            self._stop_voice()
        else:
            self._start_voice()

    def _start_voice(self):
        try:
            from voice.audio_input import AudioRecorder
            self.recorder = AudioRecorder()
            if not self.recorder.available:
                raise RuntimeError("sounddevice não está disponível.")
            self.recorder.start()
            self.recording = True
            self.model.set_state("listening", "OUVINDO")
            self.message = "Fale normalmente. Pressione o núcleo novamente para enviar."
        except Exception as exc:
            self.recording = False
            self.recorder = None
            self.model.set_state("error", "ATENÇÃO")
            self.message = f"Microfone indisponível: {exc}"
        self.render()

    def _stop_voice(self):
        recorder = self.recorder
        self.recorder = None
        self.recording = False
        if recorder is None:
            return
        self.model.set_state("thinking", "TRANSCRIBINDO")
        self.message = "Processando áudio local..."
        self.render()

        def work():
            path = None
            try:
                path = recorder.stop_to_wav()
                transcript = self._voice().transcribe(path)
                answer = self._core().process(transcript, allow_actions=False)
                error = None
            except Exception as exc:
                transcript = ""
                answer = ""
                error = f"{type(exc).__name__}: {exc}"
            finally:
                if path is not None:
                    try:
                        Path(path).unlink(missing_ok=True)
                    except OSError:
                        pass
            self.root.after(0, lambda: self._finish_voice(transcript, answer, error))

        threading.Thread(target=work, daemon=True, name="STAR-Watch-Voice").start()

    def _finish_voice(self, transcript: str, answer: str, error: str | None):
        if error:
            self.model.set_state("error", "ATENÇÃO")
            self.message = error
            self.render()
            self.root.after(1800, self._idle)
            return
        self.model.set_state("speaking", "RESPONDENDO")
        self.message = f"Você: {transcript}\n\nSTAR: {answer}"
        self.render()
        if self.model.voice_output_enabled:
            self._voice().speak_async(answer, callback=lambda *_: self.root.after(0, self._idle))
        else:
            self.root.after(1600, self._idle)

    def _submit_search(self):
        if self.input_widget is None:
            return
        query = self.input_widget.get().strip()
        if query:
            self._process_core(f"pesquise {query}")

    def _add_person(self):
        from tkinter import filedialog, simpledialog
        name = simpledialog.askstring("STAR People", "Nome:", parent=self.root)
        if not name:
            return
        notes = simpledialog.askstring("STAR People", "Observações:", parent=self.root) or ""
        image = filedialog.askopenfilename(
            parent=self.root,
            title="Foto opcional",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")],
        )
        try:
            self.people.add(name, notes, image)
            self.message = f"{name} foi salvo localmente."
        except ValueError as exc:
            self.message = str(exc)
        self.render()

    def _select_vision_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Mostrar imagem à STAR",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")],
        )
        if path:
            self.message = f"Imagem selecionada:\n{Path(path).name}\n\nAnálise visual ainda não está ativa."
            self.render()

    def _toggle_simulation(self):
        self.model.simulation_enabled = not self.model.simulation_enabled
        self.message = "Simulação ATIVA" if self.model.simulation_enabled else "Simulação DESATIVADA"
        self.render()

    def _toggle_voice_output(self):
        self.model.voice_output_enabled = not self.model.voice_output_enabled
        self.message = "Resposta falada ATIVA" if self.model.voice_output_enabled else "Resposta falada DESATIVADA"
        self.render()

    def render(self):
        self._clear_controls()
        c = self.canvas
        c.delete("all")
        c.create_rectangle(0, 0, self.SIZE, self.SIZE, fill=self.COLORS["bg"], outline="")
        self._draw_ring()
        c.create_oval(
            self.CX - self.FACE_RADIUS,
            self.CY - self.FACE_RADIUS,
            self.CX + self.FACE_RADIUS,
            self.CY + self.FACE_RADIUS,
            fill="#050810",
            outline="#16233A",
            width=2,
        )
        if self.model.active_mode == "home":
            self._draw_home()
        else:
            self._draw_mode(self.model.active_mode)

    def _draw_ring(self):
        c = self.canvas
        palette = [self.COLORS["cyan"], self.COLORS["blue"], self.COLORS["violet"], self.COLORS["pink"]]
        for i in range(60):
            angle = math.radians(i * 6 - 90)
            inner = self.RING_RADIUS - (16 if i % 5 == 0 else 10)
            outer = self.RING_RADIUS
            x1 = self.CX + math.cos(angle) * inner
            y1 = self.CY + math.sin(angle) * inner
            x2 = self.CX + math.cos(angle) * outer
            y2 = self.CY + math.sin(angle) * outer
            color = palette[(i + int(self.phase * 8)) % len(palette)] if i % 5 == 0 else "#253044"
            c.create_line(x1, y1, x2, y2, fill=color, width=3 if i % 5 == 0 else 1)

    def _draw_home(self):
        c = self.canvas
        mode = self.model.selected_mode
        # núcleo plasma leve
        pulse = (math.sin(time.monotonic() * 2.4) + 1.0) * 0.5
        r = 78 + pulse * 8
        colors = [self.COLORS["violet"], self.COLORS["blue"], self.COLORS["cyan"]]
        for idx, color in enumerate(colors):
            rr = r + idx * 13
            c.create_oval(self.CX - rr, self.CY - rr, self.CX + rr, self.CY + rr, outline=color, width=max(1, 5 - idx))
        tri = [self.CX - 38, self.CY - 30, self.CX + 38, self.CY - 30, self.CX, self.CY + 40]
        c.create_polygon(tri, fill="", outline=self.COLORS["cyan"], width=3)
        c.create_text(self.CX, 76, text=f"STAR WATCH • V{WATCH_APP_VERSION}", fill=self.COLORS["muted"], font=("Segoe UI", 9))
        c.create_text(self.CX, 160, text=mode.label, fill=self.COLORS["text"], font=("Segoe UI Semibold", 19))
        c.create_text(self.CX, 378, text=self.model.status, fill=self._state_color(), font=("Segoe UI Semibold", 10))
        c.create_text(self.CX, 418, text=self.message, fill=self.COLORS["muted"], width=310, justify="center", font=("Segoe UI", 9))
        prev_mode = WATCH_MODES[(self.model.selected_index - 1) % len(WATCH_MODES)].short
        next_mode = WATCH_MODES[(self.model.selected_index + 1) % len(WATCH_MODES)].short
        c.create_text(90, self.CY, text=f"‹ {prev_mode}", fill="#596579", font=("Segoe UI", 8))
        c.create_text(470, self.CY, text=f"{next_mode} ›", fill="#596579", font=("Segoe UI", 8))

    def _state_color(self):
        return {
            "idle": self.COLORS["cyan"],
            "listening": self.COLORS["cyan"],
            "thinking": self.COLORS["violet"],
            "speaking": self.COLORS["pink"],
            "error": self.COLORS["danger"],
        }.get(self.model.state, self.COLORS["text"])

    def _draw_mode(self, key: str):
        c = self.canvas
        mode = next((m for m in WATCH_MODES if m.key == key), None)
        title = mode.label if mode else key.upper()
        c.create_text(self.CX, 72, text=title, fill=self.COLORS["text"], font=("Segoe UI Semibold", 20))
        c.create_text(self.CX, 102, text="STAR", fill=self.COLORS["cyan"], font=("Segoe UI", 9))

        if key == "voice":
            text = "OUVINDO" if self.recording else "Pressione o núcleo para falar"
            sub = self.message or "Espaço também inicia/encerra a captura."
            self._draw_center_value(text, sub)
        elif key == "search":
            self._draw_center_value("BUSCA STAR", "Digite um tema/produto. O Core atual abre a pesquisa disponível; comparação multi-loja será o próximo provider.")
            self._create_search_controls()
        elif key == "health":
            data = self.providers.health()
            value = f"{data.get('heart_rate', '--')} BPM   •   SpO₂ {data.get('spo2', '--')}%" if data.get("available") else "SEM SENSOR"
            self._draw_center_value(value, data.get("message", ""))
        elif key == "gps":
            data = self.providers.gps()
            value = f"{data.get('speed_kmh', '--')} km/h" if data.get("available") else "GPS OFF"
            self._draw_center_value(value, data.get("message", ""))
        elif key == "vision":
            self._draw_center_value("STAR SCAN", self.message or "Selecione uma imagem. Transporte existe; análise visual ainda não.")
            self._create_action_button("SELECIONAR IMAGEM", self._select_vision_image)
        elif key == "people":
            rows = self.people.list()
            names = ", ".join(item.get("name", "") for item in rows[-4:]) or "Nenhuma pessoa cadastrada"
            self._draw_center_value(f"{len(rows)} PERFIS", names)
            self._create_action_button("ADICIONAR PESSOA", self._add_person)
        elif key == "measure":
            data = self.providers.measure()
            value = f"{data.get('distance_m', '--')} m" if data.get("available") else "LASER OFF"
            self._draw_center_value(value, data.get("message", "") + "\nPressione para medir novamente.")
        elif key == "media":
            self._draw_center_value("MÍDIA", self.message or "Pressione para play/pause. Comandos de faixa e volume usam a Foundation atual.")
        elif key == "weather":
            data = self.providers.weather()
            self._draw_center_value("CLIMA", data.get("message", ""))
        elif key == "settings":
            self._draw_center_value(
                "CONFIG",
                f"Simulação: {'ON' if self.model.simulation_enabled else 'OFF'}\nResposta falada: {'ON' if self.model.voice_output_enabled else 'OFF'}",
            )
            self._create_settings_buttons()
        c.create_text(self.CX, 462, text="BACKSPACE = voltar   •   roda/setas = girar", fill="#667286", font=("Segoe UI", 8))

    def _draw_center_value(self, value: str, subtitle: str):
        self.canvas.create_text(self.CX, 245, text=value, fill=self.COLORS["cyan"], width=320, justify="center", font=("Segoe UI Semibold", 18))
        self.canvas.create_text(self.CX, 320, text=subtitle, fill=self.COLORS["muted"], width=330, justify="center", font=("Segoe UI", 9))

    def _create_search_controls(self):
        tk = self.tk
        self.input_widget = tk.Entry(
            self.root,
            bg=self.COLORS["surface"],
            fg=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            relief="flat",
            justify="center",
            font=("Segoe UI", 10),
        )
        self.input_widget.place(x=150, y=370, width=260, height=34)
        self.input_widget.bind("<Return>", lambda _e: self._submit_search())
        self._create_action_button("PESQUISAR", self._submit_search, y=414)
        self.input_widget.focus_set()

    def _create_action_button(self, text: str, command, y: int = 382):
        tk = self.tk
        self.action_button = tk.Button(
            self.root,
            text=text,
            command=command,
            bg="#14243B",
            fg=self.COLORS["cyan"],
            activebackground="#1D3554",
            activeforeground=self.COLORS["text"],
            relief="flat",
            bd=0,
            font=("Segoe UI Semibold", 9),
        )
        self.action_button.place(x=185, y=y, width=190, height=34)

    def _create_settings_buttons(self):
        tk = self.tk
        first = tk.Button(self.root, text="SIMULAÇÃO", command=self._toggle_simulation, relief="flat", bd=0, bg="#14243B", fg=self.COLORS["cyan"])
        second = tk.Button(self.root, text="VOZ", command=self._toggle_voice_output, relief="flat", bd=0, bg="#14243B", fg=self.COLORS["pink"])
        first.place(x=170, y=382, width=105, height=34)
        second.place(x=285, y=382, width=105, height=34)
        self.input_widget = first
        self.action_button = second

    def _animate(self):
        if self.closed:
            return
        self.phase = (self.phase + 0.015) % 1.0
        # redesenha apenas o canvas; controles são recriados somente em telas que usam widgets
        if self.model.active_mode == "home":
            self.render()
        self.root.after(50, self._animate)

    def close(self):
        self.closed = True
        if self.recorder is not None:
            try:
                self.recorder.stop()
            except Exception:
                pass
        if self.voice_manager is not None:
            try:
                self.voice_manager.close()
            except Exception:
                pass
        self.root.destroy()


def main():
    StarWatchApp().run()


if __name__ == "__main__":
    main()
