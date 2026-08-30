"""Baixa os modelos locais de voz da STAR uma única vez."""
from __future__ import annotations

from pathlib import Path
from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parent.parent
PIPER_DIR = ROOT / "voice" / "models" / "piper"
REPO = "rhasspy/piper-voices"
MODEL = "pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx"
CONFIG = MODEL + ".json"


def main() -> None:
    PIPER_DIR.mkdir(parents=True, exist_ok=True)
    print("🎙️ Preparando Piper PT-BR...")
    for filename in (MODEL, CONFIG):
        target = PIPER_DIR / Path(filename).name
        if target.exists() and target.stat().st_size > 1000:
            print(f"✅ Já existe: {target.name}")
            continue
        path = hf_hub_download(
            repo_id=REPO,
            filename=filename,
            local_dir=str(PIPER_DIR),
            local_dir_use_symlinks=False,
        )
        downloaded = Path(path)
        print(f"✅ Baixado: {downloaded.name}")

    print("🎙️ Piper PT-BR pronto.")


if __name__ == "__main__":
    main()
