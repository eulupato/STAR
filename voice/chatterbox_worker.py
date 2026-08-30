"""Worker persistente do Chatterbox para a STAR.

Executa no .voice_venv, mantém o modelo carregado e gera WAVs sob demanda.
Não reproduz áudio: a reprodução acontece no processo principal da STAR.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "voice" / "reference" / "star_reference.mp3"
OUT = ROOT / "voice" / "output"


def emit(payload: dict) -> None:
    print("STAR_CHATTERBOX_RESULT=" + json.dumps(payload, ensure_ascii=False), flush=True)


def main() -> int:
    try:
        import torch
        import torchaudio as ta
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    except Exception as exc:
        emit({"ok": False, "error": f"Falha ao importar Chatterbox: {type(exc).__name__}: {exc}"})
        return 1

    if not REF.exists():
        emit({"ok": False, "error": f"Áudio de referência não encontrado: {REF}"})
        return 1

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    try:
        print(f"STAR_CHATTERBOX_READY device={device}", flush=True)
        model = ChatterboxMultilingualTTS.from_pretrained(device=device)
        print("STAR_CHATTERBOX_MODEL_READY", flush=True)
    except Exception as exc:
        emit({"ok": False, "error": f"Falha ao carregar Chatterbox: {type(exc).__name__}: {exc}"})
        return 1

    OUT.mkdir(parents=True, exist_ok=True)

    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            request = json.loads(raw)
            if request.get("command") == "shutdown":
                emit({"ok": True, "shutdown": True})
                return 0

            text = str(request.get("text", "")).strip()
            if not text:
                emit({"ok": False, "error": "Texto vazio."})
                continue

            output_name = request.get("output") or f"star_{int(time.time() * 1000)}.wav"
            output_path = OUT / Path(output_name).name

            wav = model.generate(
                text,
                language_id="pt",
                audio_prompt_path=str(REF),
                exaggeration=float(request.get("exaggeration", 0.5)),
                cfg_weight=float(request.get("cfg_weight", 0.4)),
                temperature=float(request.get("temperature", 0.8)),
            )
            ta.save(str(output_path), wav, model.sr)
            emit({"ok": True, "path": str(output_path), "sample_rate": int(model.sr)})
        except Exception as exc:
            emit({"ok": False, "error": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc(limit=3)})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
