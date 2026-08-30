"""Ponte entre STAR (Python principal) e Chatterbox (Python 3.11)."""
from pathlib import Path
import subprocess, threading, json
ROOT=Path(__file__).resolve().parent.parent
class LocalVoiceBridge:
    def __init__(self):
        self.python=ROOT/".voice_venv"/"Scripts"/"python.exe"; self.last_error=None; self.enabled=True
    @property
    def configured(self): return self.python.exists() and (ROOT/"voice"/"reference"/"star_reference.mp3").exists()
    def speak(self,text):
        if not self.configured:
            self.last_error="Chatterbox não instalado. Execute INSTALAR_CHATTERBOX.bat primeiro."; return False
        try:
            p=subprocess.run([str(self.python),str(ROOT/"voice_bridge.py"),str(text)],cwd=str(ROOT),capture_output=True,text=True,timeout=600)
            lines=[x for x in p.stdout.splitlines() if x.strip()]
            data=json.loads(lines[-1]) if lines else {"ok":False,"error":p.stderr[-500:]}
            self.last_error=data.get("error"); return bool(data.get("ok"))
        except Exception as e:
            self.last_error=f"{type(e).__name__}: {e}"; return False
    def speak_async(self,text,callback=None):
        def run():
            ok=self.speak(text)
            if callback: callback(ok,self.last_error)
        t=threading.Thread(target=run,daemon=True); t.start(); return t
