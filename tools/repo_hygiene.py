"""Validação leve de higiene do repositório STAR.

Executada no CI para impedir que dados locais, placeholders vazios inválidos
ou JSON corrompido sejam versionados por acidente.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_EXACT = {
    "star.db",
    "user_settings.json",
}

FORBIDDEN_PREFIXES = (
    "knowledge/local/",
    ".venv/",
    ".voice_venv/",
)

FORBIDDEN_SUFFIXES = (
    ".db-wal",
    ".db-shm",
)

ALLOWED_EMPTY_NAMES = {
    "__init__.py",
}


def tracked_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"Não foi possível consultar arquivos rastreados: {exc}") from exc

    return [
        item.decode("utf-8", errors="strict")
        for item in result.stdout.split(b"\0")
        if item
    ]


def validate() -> list[str]:
    failures = []
    tracked = tracked_files()

    for relative in tracked:
        normalized = relative.replace("\\", "/")
        path = ROOT / relative

        if normalized in FORBIDDEN_EXACT:
            failures.append(f"dado local rastreado: {normalized}")
        if normalized.endswith(FORBIDDEN_SUFFIXES):
            failures.append(f"arquivo auxiliar SQLite rastreado: {normalized}")
        if any(normalized.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            failures.append(f"diretório local rastreado: {normalized}")

        if (
            path.exists()
            and path.is_file()
            and path.stat().st_size == 0
            and path.name not in ALLOWED_EMPTY_NAMES
        ):
            failures.append(f"arquivo vazio inválido: {normalized}")

        if path.suffix.lower() == ".json" and path.exists():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                failures.append(f"JSON inválido {normalized}: {exc}")

    root_tests = [
        item
        for item in tracked
        if "/" not in item.replace("\\", "/")
        and Path(item).name.startswith("test_")
        and Path(item).suffix == ".py"
    ]
    for item in root_tests:
        failures.append(
            f"teste Python fora de tests/: {item}"
        )

    return failures


def main() -> None:
    failures = validate()
    if failures:
        print("❌ Higiene do repositório falhou:")
        for item in failures:
            print(" -", item)
        raise SystemExit(1)

    print("✅ Higiene do repositório STAR OK.")


if __name__ == "__main__":
    main()
