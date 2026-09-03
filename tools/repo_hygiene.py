"""Validação leve de higiene do repositório STAR.

Executada no CI para impedir que dados locais, placeholders vazios inválidos,
JSON corrompido ou resíduos de versões antigas voltem à árvore ativa.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_EXACT = {
    "star.db",
    "user_settings.json",
    "AUDITORIA_STAR_CODIGO.txt",
}

FORBIDDEN_PREFIXES = (
    "knowledge/local/",
    ".venv/",
    ".voice_venv/",
    "archive/legacy/",
)

FORBIDDEN_SUFFIXES = (
    ".db-wal",
    ".db-shm",
)

FORBIDDEN_ROOT_PATTERNS = (
    re.compile(r"^HUB_E_ILHAS_V1_[0-9]+\.md$", re.I),
    re.compile(r"^test_.*\.py$", re.I),
)

ACTIVE_RUNTIME_SUFFIXES = {".py", ".bat"}
OBSOLETE_RUNTIME_VERSION = re.compile(r"\b(?:STAR\s*)?V(?:1\.[0-9]+|2\.0)\b", re.I)

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


def _is_active_runtime(normalized: str, path: Path) -> bool:
    if normalized.startswith("archive/"):
        return False
    if normalized.startswith("docs/"):
        return False
    if normalized.startswith("tests/"):
        return False
    return path.suffix.lower() in ACTIVE_RUNTIME_SUFFIXES


def validate() -> list[str]:
    failures = []
    tracked = tracked_files()

    for relative in tracked:
        normalized = relative.replace("\\", "/")
        path = ROOT / relative

        if normalized in FORBIDDEN_EXACT:
            failures.append(f"dado/resíduo local rastreado: {normalized}")
        if normalized.endswith(FORBIDDEN_SUFFIXES):
            failures.append(f"arquivo auxiliar SQLite rastreado: {normalized}")
        if any(normalized.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            failures.append(f"diretório local rastreado: {normalized}")

        if "/" not in normalized and any(
            pattern.match(normalized)
            for pattern in FORBIDDEN_ROOT_PATTERNS
        ):
            failures.append(f"arquivo legado/teste indevido na raiz: {normalized}")

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

        if _is_active_runtime(normalized, path) and path.exists():
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                failures.append(f"runtime ilegível {normalized}: {exc}")
            else:
                match = OBSOLETE_RUNTIME_VERSION.search(text)
                if match:
                    failures.append(
                        f"versão obsoleta em runtime ativo {normalized}: {match.group(0)}"
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
