import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from voice.chatterbox_voice import ChatterboxVoice

if __name__=="__main__":
    text=" ".join(sys.argv[1:]).strip() or "Olá!"
    v=ChatterboxVoice()
    try:
        ok=v.speak(text)
        result={"ok":bool(ok),"error":v.last_error}
    except Exception as e:
        result={"ok":False,"error":f"{type(e).__name__}: {e}"}
    print("STAR_VOICE_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)
