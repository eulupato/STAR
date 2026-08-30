import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from voice.chatterbox_voice import ChatterboxVoice
if __name__=="__main__":
    text=sys.argv[1] if len(sys.argv)>1 else "Olá!"
    v=ChatterboxVoice()
    ok=v.speak(text)
    print(json.dumps({"ok":ok,"error":v.last_error},ensure_ascii=False))
