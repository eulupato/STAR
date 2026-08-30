"""Ponte entre STAR e o motor local Chatterbox (Python .voice_venv)."""
from pathlib import Path
import subprocess, threading, json

ROOT=Path(__file__).resolve().parent.parent

class LocalVoiceBridge:
    def __init__(self):
        self.python=ROOT/".voice_venv"/"Scripts"/"python.exe"
        self.last_error=None
        self.enabled=True

    @property
    def configured(self):
        return self.python.exists() and (ROOT/"voice"/"reference"/"star_reference.mp3").exists()

    def speak(self,text):
        if not self.enabled:
            self.last_error="Voz local desativada."
            return False
        if not self.configured:
            self.last_error="Chatterbox não configurado: verifique .voice_venv e voice/reference/star_reference.mp3."
            return False
        try:
            p=subprocess.run(
                [str(self.python),str(ROOT/"voice_bridge.py"),str(text)],
                cwd=str(ROOT),capture_output=True,text=True,encoding="utf-8",
                errors="replace",timeout=600
            )
            # O processo pode imprimir logs do modelo; procuramos o resultado marcado.
            result=None
            for line in reversed(p.stdout.splitlines()):
                if line.startswith("STAR_VOICE_RESULT="):
                    result=json.loads(line.split("=",1)[1])
                    break
            if result is None:
                detail=(p.stderr or p.stdout or f"processo retornou {p.returncode}")[-1200:]
                self.last_error="Chatterbox não retornou confirmação de reprodução: "+detail
                return False
            self.last_error=result.get("error")
            return bool(result.get("ok"))
        except subprocess.TimeoutExpired:
            self.last_error="Tempo limite do Chatterbox excedido (10 minutos)."
            return False
        except Exception as e:
            self.last_error=f"{type(e).__name__}: {e}"
            return False

    def speak_async(self,text,callback=None):
        def run():
            ok=self.speak(text)
            if callback: callback(ok,self.last_error)
        t=threading.Thread(target=run,daemon=True)
        t.start()
        return t

    def test_audio_async(self,callback=None):
        return self.speak_async("Olá! Eu sou a STAR. Meu sistema de voz local está funcionando.",callback)
