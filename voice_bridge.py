import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from voice.chatterbox_voice import ChatterboxVoice

if __name__=="__main__":
    text=" ".join(sys.argv[1:]).strip() or "Olá!"
    v=ChatterboxVoice()
    try:
        path=v.synthesize(text)
        result={"ok":True,"path":str(path),"error":None}
    except Exception as e:
        result={"ok":False,"path":None,"error":f"{type(e).__name__}: {e}"}
    print("STAR_VOICE_RESULT="+json.dumps(result,ensure_ascii=False),flush=True)
