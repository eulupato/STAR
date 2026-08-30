"""Ponte STAR -> Chatterbox em ambiente separado, reprodução no Python principal."""
from pathlib import Path
import subprocess, threading, json
ROOT=Path(__file__).resolve().parent.parent

class LocalVoiceBridge:
    def __init__(self):
        self.python=ROOT/".voice_venv"/"Scripts"/"python.exe"; self.last_error=None; self.enabled=True
    @property
    def configured(self):
        return self.python.exists() and (ROOT/"voice"/"reference"/"star_reference.mp3").exists()

    def _generate(self,text):
        p=subprocess.run([str(self.python),str(ROOT/"voice_bridge.py"),str(text)],cwd=str(ROOT),
          capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=600)
        result=None
        for line in reversed(p.stdout.splitlines()):
            if line.startswith("STAR_VOICE_RESULT="):
                result=json.loads(line.split("=",1)[1]); break
        if not result:
            raise RuntimeError((p.stderr or p.stdout or f"processo retornou {p.returncode}")[-1500:])
        if not result.get("ok"): raise RuntimeError(result.get("error") or "falha desconhecida")
        path=Path(result["path"])
        if not path.exists(): raise RuntimeError(f"áudio gerado não encontrado: {path}")
        return path

    def speak(self,text):
        if not self.enabled: self.last_error="Voz local desativada."; return False
        if not self.configured: self.last_error="Chatterbox não configurado: verifique .voice_venv e voice/reference/star_reference.mp3."; return False
        try:
            path=self._generate(text)
            # Reproduz no ambiente principal, onde sounddevice/soundfile já estão instalados.
            import sounddevice as sd
            import soundfile as sf
            data, rate=sf.read(str(path),dtype="float32")
            sd.play(data,rate); sd.wait()
            self.last_error=None; return True
        except subprocess.TimeoutExpired:
            self.last_error="Tempo limite do Chatterbox excedido (10 minutos)."; return False
        except Exception as e:
            self.last_error=f"{type(e).__name__}: {e}"; return False

    def speak_async(self,text,callback=None):
        def run():
            ok=self.speak(text)
            if callback: callback(ok,self.last_error)
        t=threading.Thread(target=run,daemon=True); t.start(); return t

    def test_audio_async(self,callback=None):
        return self.speak_async("Olá! Eu sou a STAR. Meu sistema de voz local está funcionando.",callback)
