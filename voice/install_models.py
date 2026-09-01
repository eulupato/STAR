"""Prepara explicitamente os modelos locais de voz da STAR.

Este script é a única etapa que pode baixar Piper/Whisper. O runtime usa apenas
arquivos já presentes em ``voice/models`` e nunca baixa modelo por conta própria.
"""
from __future__ import annotations

from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download

from config import PIPER_MODEL, STT_MODEL

ROOT = Path(__file__).resolve().parent.parent
PIPER_DIR = ROOT / "voice" / "models" / "piper"
WHISPER_DIR = ROOT / "voice" / "models" / "whisper" / STT_MODEL
PIPER_REPO = "rhasspy/piper-voices"
PIPER_CONFIG = PIPER_MODEL + ".json"
WHISPER_REPO = f"Systran/faster-whisper-{STT_MODEL}"


def install_piper() -> None:
    PIPER_DIR.mkdir(parents=True, exist_ok=True)
    print("🎙️ Preparando Piper PT-BR...")
    for filename in (PIPER_MODEL, PIPER_CONFIG):
        target = PIPER_DIR / Path(filename).name
        if target.exists() and target.stat().st_size > 1000:
            print(f"✅ Já existe: {target.name}")
            continue
        path = hf_hub_download(
            repo_id=PIPER_REPO,
            filename=filename,
            local_dir=str(PIPER_DIR),
        )
        print(f"✅ Baixado: {Path(path).name}")


def install_whisper() -> None:
    required = (WHISPER_DIR / "model.bin", WHISPER_DIR / "config.json")
    if all(path.exists() and path.stat().st_size > 0 for path in required):
        print(f"✅ Whisper {STT_MODEL} já existe localmente.")
        return

    WHISPER_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🎤 Preparando Whisper {STT_MODEL} local...")
    snapshot_download(
        repo_id=WHISPER_REPO,
        local_dir=str(WHISPER_DIR),
    )
    missing = [path.name for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "Download do Whisper incompleto; faltando: " + ", ".join(missing)
        )
    print(f"✅ Whisper {STT_MODEL} pronto em {WHISPER_DIR}.")


def main() -> None:
    install_piper()
    install_whisper()
    print("🎙️ Modelos locais de voz preparados.")


if __name__ == "__main__":
    main()
