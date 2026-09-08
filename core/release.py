"""Metadados oficiais de release da STAR.

STAR_MANIFEST.json é a fonte única de verdade para nome, versão e canal público.
Este módulo expõe esses valores ao runtime sem duplicá-los em vários arquivos.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "STAR_MANIFEST.json"


class ReleaseManifestError(RuntimeError):
    """Manifesto de release ausente, inválido ou incompleto."""


@lru_cache(maxsize=1)
def load_release_manifest() -> dict:
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseManifestError(f"Manifesto de release não encontrado: {MANIFEST_PATH}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseManifestError(f"Não foi possível carregar o manifesto de release: {exc}") from exc

    if not isinstance(data, dict):
        raise ReleaseManifestError("STAR_MANIFEST.json deve conter um objeto JSON.")

    required = ("name", "version", "release_status", "release_channel")
    missing = [key for key in required if not str(data.get(key) or "").strip()]
    if missing:
        raise ReleaseManifestError(
            "STAR_MANIFEST.json está incompleto; campos ausentes: " + ", ".join(missing)
        )
    return data


_RELEASE = load_release_manifest()
APP_NAME = str(_RELEASE["name"])
VERSION = str(_RELEASE["version"])
RELEASE_STATUS = str(_RELEASE["release_status"])
RELEASE_CHANNEL = str(_RELEASE["release_channel"])
