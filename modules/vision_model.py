"""Modelo local do STAR Vision usando MediaPipe Tasks.

O modelo oficial é baixado somente quando o usuário inicia o STAR Vision pela
primeira vez. Depois disso o tracking funciona sem internet.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import os
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "runtime" / "vision" / "models"
HAND_MODEL = MODEL_DIR / "hand_landmarker.task"
HAND_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
# Snapshot oficial validado pelo workflow STAR Vision com MediaPipe 0.10.35.
# O hash fixo impede que um arquivo diferente seja aceito silenciosamente.
HAND_MODEL_SHA256 = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
MIN_MODEL_BYTES = 1_000_000


def model_ready() -> bool:
    try:
        return HAND_MODEL.is_file() and HAND_MODEL.stat().st_size >= MIN_MODEL_BYTES
    except OSError:
        return False


def model_sha256(path: Path = HAND_MODEL) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate(path: Path) -> None:
    size = path.stat().st_size
    if size < MIN_MODEL_BYTES:
        raise RuntimeError(f"Modelo HandLandmarker incompleto: {size} bytes.")
    actual = model_sha256(path)
    if actual.lower() != HAND_MODEL_SHA256.lower():
        raise RuntimeError("Hash SHA-256 do modelo HandLandmarker não confere.")


def ensure_hand_model(*, download: bool = True) -> Path:
    """Retorna o modelo local, baixando o snapshot oficial se necessário."""
    if model_ready():
        _validate(HAND_MODEL)
        return HAND_MODEL
    if not download:
        raise FileNotFoundError(
            f"Modelo de mãos ausente em {HAND_MODEL}. Execute o STAR Vision uma vez para preparar o modelo local."
        )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="hand_landmarker-", suffix=".task", dir=MODEL_DIR)
    os.close(fd)
    temp = Path(temp_name)
    try:
        request = urllib.request.Request(
            HAND_MODEL_URL,
            headers={"User-Agent": "STAR-Vision/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=45) as response, temp.open("wb") as target:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)
        _validate(temp)
        temp.replace(HAND_MODEL)
        return HAND_MODEL
    except Exception:
        temp.unlink(missing_ok=True)
        raise
