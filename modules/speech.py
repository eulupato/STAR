"""Camada de voz V1.7. Funciona com pyttsx3 quando instalado; não depende do Core."""
class SpeechEngine:
    def __init__(self):
        self.engine=None
        try:
            import pyttsx3
            self.engine=pyttsx3.init()
        except Exception: pass
    @property
    def available(self): return self.engine is not None
    def speak(self,text):
        if not self.engine: return False
        self.engine.say(str(text)); self.engine.runAndWait(); return True
