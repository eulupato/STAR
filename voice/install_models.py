"""Baixa os modelos locais de voz da STAR uma única vez."""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parent.parent
PIPER_DIR = ROOT / "voice" / "models" / "piper"
PIPER_REPO = "rhasspy/piper-voices"
PIPER_MODEL = "pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx"
PIPER_CONFIG = PIPER_MODEL + ".json"

SILERO_DIR = ROOT / "voice" / "models" / "vad"
SILERO_VERSION = "v6.2.1"
SILERO_MODEL = "silero_vad.onnx"
SILERO_URL = (
    "https://github.com/snakers4/silero-vad/raw/"
    f"{SILERO_VERSION}/src/silero_vad/data/{SILERO_MODEL}"
)
SILERO_SHA256 = "1a153a22f4509e292a94e67d6f9b85e8deb25b4988682b7e174c65279d8788e3"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_silero_vad_model(*, force: bool = False) -> Path:
    """Baixa e valida o Silero VAD pinado; nunca é chamado pelo runtime."""
    SILERO_DIR.mkdir(parents=True, exist_ok=True)
    target = SILERO_DIR / SILERO_MODEL

    if target.is_file() and not force:
        if _sha256(target) == SILERO_SHA256:
            print(f"✅ Silero VAD {SILERO_VERSION} já existe e foi validado.")
            return target
        print("⚠️ Silero VAD local possui hash diferente; será baixado novamente.")

    request = Request(SILERO_URL, headers={"User-Agent": "STAR-Voice-Installer/0.1"})
    temp_path: Path | None = None
    try:
        with urlopen(request, timeout=60) as response, tempfile.NamedTemporaryFile(
            prefix="star_silero_", suffix=".onnx", delete=False, dir=SILERO_DIR
        ) as temp:
            temp_path = Path(temp.name)
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                temp.write(block)

        actual = _sha256(temp_path)
        if actual != SILERO_SHA256:
            raise RuntimeError(
                "Falha de integridade no Silero VAD: "
                f"SHA-256 esperado {SILERO_SHA256}, obtido {actual}."
            )
        temp_path.replace(target)
        print(f"✅ Silero VAD {SILERO_VERSION} instalado: {target}")
        return target
    finally:
        if temp_path is not None and temp_path.exists() and temp_path != target:
            temp_path.unlink(missing_ok=True)


def _prepare_piper() -> None:
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
            local_dir_use_symlinks=False,
        )
        print(f"✅ Baixado: {Path(path).name}")
    print("🎙️ Piper PT-BR pronto.")


def main() -> None:
    _prepare_piper()
    print("🎙️ Preparando Silero VAD local...")
    download_silero_vad_model()
    print("🎙️ Modelos locais de voz preparados.")


if __name__ == "__main__":
    main()
