import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from voice.chatterbox_voice import ChatterboxVoice
v=ChatterboxVoice()
print("Referencia:", ROOT/"voice"/"reference"/"star_reference.mp3")
print("Carregando Chatterbox e gerando teste...")
ok=v.speak("Olá! Eu sou a STAR. Meu novo sistema de voz local está funcionando.")
print("SUCESSO!" if ok else "ERRO: "+str(v.last_error))
