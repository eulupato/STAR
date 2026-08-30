"""Camada de voz da STAR: ElevenLabs TTS + STT."""
from pathlib import Path
import tempfile, threading, os, time, traceback
import requests

ROOT=Path(__file__).resolve().parent.parent
DEFAULT_VOICE_ID="jqcCZkN6Knx8BJ5TBdYR"

class ElevenLabsVoice:
    def __init__(self, voice_id=DEFAULT_VOICE_ID):
        self.voice_id=voice_id
        self.key_path=ROOT/'key.txt'
        self.enabled=True
        self.last_error=None
        self._mixer_ready=False
        self._lock=threading.Lock()

    def _key(self):
        try: return self.key_path.read_text(encoding='utf-8').strip()
        except Exception: return ''

    @property
    def configured(self): return bool(self._key() and self.voice_id)

    def synthesize(self, text):
        key=self._key()
        if not key: raise RuntimeError('Chave do ElevenLabs não encontrada em key.txt.')
        url=f'https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}?output_format=mp3_44100_128'
        payload={"text":str(text),"model_id":"eleven_multilingual_v2",
                 "voice_settings":{"stability":0.45,"similarity_boost":0.75,
                 "style":0.35,"use_speaker_boost":True,"speed":1.0}}
        r=requests.post(url, headers={'xi-api-key':key,'Content-Type':'application/json',
                        'Accept':'audio/mpeg'}, json=payload, timeout=60)
        if not r.ok:
            raise RuntimeError(f'ElevenLabs respondeu HTTP {r.status_code}: {r.text[:300]}')
        f=tempfile.NamedTemporaryFile(delete=False,suffix='.mp3')
        f.write(r.content); f.close()
        return Path(f.name)

    def _ensure_mixer(self):
        import pygame
        if not self._mixer_ready:
            # Tenta primeiro o dispositivo padrão do sistema. Em algumas máquinas,
            # pygame pode ficar inicializado sem um dispositivo de saída válido.
            try:
                pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
                pygame.mixer.init()
            except Exception:
                pygame.mixer.quit()
                pygame.mixer.init()
            self._mixer_ready=True
        return pygame

    def speak(self, text):
        if not self.enabled:
            self.last_error='A voz está desativada pelo modo OFFLINE.'
            return False
        if not self.configured:
            self.last_error='Chave do ElevenLabs ou Voice ID não configurados.'
            return False
        path=None
        try:
            with self._lock:
                path=self.synthesize(text)
                if not path.exists() or path.stat().st_size < 100:
                    raise RuntimeError('O ElevenLabs não retornou um arquivo de áudio válido.')
                pygame=self._ensure_mixer()
                pygame.mixer.music.stop()
                try: pygame.mixer.music.unload()
                except Exception: pass
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play()
                started=time.time()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(30)
                if time.time()-started < 0.05:
                    raise RuntimeError('A reprodução terminou imediatamente. Verifique o dispositivo de saída de áudio do Windows.')
                try: pygame.mixer.music.unload()
                except Exception: pass
            self.last_error=None
            return True
        except Exception as e:
            self.last_error=f'{type(e).__name__}: {e}'
            return False
        finally:
            if path:
                for _ in range(5):
                    try:
                        path.unlink(missing_ok=True); break
                    except Exception:
                        time.sleep(.1)

    def speak_async(self,text,callback=None):
        def run():
            ok=self.speak(text)
            if callback: callback(ok,self.last_error)
        t=threading.Thread(target=run,daemon=True)
        t.start(); return t

    def transcribe(self, audio_path):
        key=self._key()
        if not key: raise RuntimeError('Chave do ElevenLabs não encontrada em key.txt.')
        url='https://api.elevenlabs.io/v1/speech-to-text'
        with open(audio_path,'rb') as f:
            files={'file':(Path(audio_path).name,f,'audio/wav')}
            data={'model_id':'scribe_v2'}
            r=requests.post(url,headers={'xi-api-key':key},files=files,data=data,timeout=90)
        if not r.ok:
            raise RuntimeError(f'Speech-to-Text respondeu HTTP {r.status_code}: {r.text[:300]}')
        payload=r.json()
        text=str(payload.get('text','')).strip()
        if not text: raise RuntimeError('Não consegui identificar fala no áudio.')
        return text

    def test_audio_async(self, callback=None):
        def run():
            ok=self.speak('Olá! Eu sou a STAR. Meu sistema de voz está funcionando.')
            if callback: callback(ok, self.last_error)
        t=threading.Thread(target=run,daemon=True); t.start(); return t
