"""Release metadata da STAR.

STAR_MANIFEST.json é a única fonte de verdade da versão pública. Este módulo
valida o manifesto e expõe uma interface tipada para o restante do projeto.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = PROJECT_ROOT / "STAR_MANIFEST.json"


@dataclass(frozen=True)
class ReleaseInfo:
    name: str
    version: str
    codename: str
    release_status: str
    release_channel: str

    @property
    def label(self) -> str:
        return f"{self.name} V{self.version} — {self.codename}"


def load_release_info(path: Path | str | None = None) -> ReleaseInfo:
    manifest_path = Path(path) if path else DEFAULT_MANIFEST
    try:
        raw = manifest_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except OSError as exc:
        raise RuntimeError(f"Manifesto da STAR indisponível: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Manifesto da STAR inválido: {manifest_path}") from exc

    required = ("name", "version", "codename", "release_status", "release_channel")
    missing = [key for key in required if not str(data.get(key, "")).strip()]
    if missing:
        raise RuntimeError(
            "Manifesto da STAR incompleto; campos ausentes: " + ", ".join(missing)
        )

    return ReleaseInfo(
        name=str(data["name"]),
        version=str(data["version"]),
        codename=str(data["codename"]),
        release_status=str(data["release_status"]),
        release_channel=str(data["release_channel"]),
    )


RELEASE = load_release_info()
STAR_VERSION = RELEASE.version
STAR_CODENAME = RELEASE.codename
STAR_RELEASE_STATUS = RELEASE.release_status
STAR_RELEASE_CHANNEL = RELEASE.release_channel
