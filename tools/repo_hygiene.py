"""Auditoria de higiene do repositório STAR.

Fonte única para invariantes estruturais simples que devem valer no PC e na CI.
Não altera arquivos; somente reporta problemas e encerra com código diferente de
zero quando encontra uma violação.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_EMPTY_PYTHON = {
    "core/__init__.py",
    "core/models/__init__.py",
    "core/models/local/__init__.py",
    "core/nuclei/__init__.py",
    "database/__init__.py",
    "gui/__init__.py",
    "modules/__init__.py",
    "tests/__init__.py",
}

PRIVATE_VOICE_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
MOJIBAKE_MARKERS = ("├", "┬", "�")
FORBIDDEN_TRACKED_PREFIXES = ("archive/legacy/", "runtime/")
FORBIDDEN_TRACKED_NAMES = {
    "star.db",
    ".env",
    "key.txt",
    "AUDITORIA_STAR_CODIGO.txt",
    "HUB_E_ILHAS_V1_4.md",
    "HUB_E_ILHAS_V1_5.md",
}


def _tracked_files(root: Path = ROOT) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        names = result.stdout.decode("utf-8").split("\0")
        return [root / name for name in names if name]
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        ignored_roots = {".git", ".venv", "venv", "__pycache__", "runtime"}
        return [
            path
            for path in root.rglob("*")
            if path.is_file()
            and not any(part in ignored_roots for part in path.relative_to(root).parts)
        ]


def _relative(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def collect_issues(root: Path = ROOT) -> list[str]:
    files = _tracked_files(root)
    issues: list[str] = []

    for path in files:
        rel = _relative(path, root)

        if rel in FORBIDDEN_TRACKED_NAMES:
            issues.append(f"arquivo local/legado versionado: {rel}")
        if any(rel.startswith(prefix) for prefix in FORBIDDEN_TRACKED_PREFIXES):
            issues.append(f"diretório local/legado versionado: {rel}")
        if any(marker in rel for marker in MOJIBAKE_MARKERS):
            issues.append(f"nome de caminho corrompido/mojibake: {rel}")

        lower_name = path.name.casefold()
        if (
            path.suffix.casefold() in {".py", ".bat", ".md", ".txt"}
            and ("_backup" in lower_name or lower_name.endswith(".bak"))
        ):
            issues.append(f"backup versionado no fluxo ativo: {rel}")

        if rel.startswith("voice/reference/") and path.suffix.casefold() in PRIVATE_VOICE_EXTENSIONS:
            issues.append(f"referência de voz privada versionada: {rel}")

        if path.suffix.casefold() == ".py" and path.stat().st_size == 0 and rel not in ALLOWED_EMPTY_PYTHON:
            issues.append(f"módulo Python vazio sem função real: {rel}")

    root_tests = sorted(root.glob("test_*.py"))
    issues.extend(f"teste fora de tests/: {_relative(path, root)}" for path in root_tests)

    assets = root / "assets"
    if assets.exists():
        for path in assets.rglob("*"):
            if path.is_file() and path.stat().st_size == 0:
                issues.append(f"asset vazio: {_relative(path, root)}")

    icon = root / "assets" / "icons" / "star.ico"
    if not icon.is_file() or icon.stat().st_size == 0:
        issues.append("assets/icons/star.ico ausente ou vazio")
    duplicate_icon = root / "assets" / "icons" / "star.ico.ico"
    if duplicate_icon.exists():
        issues.append("ícone duplicado assets/icons/star.ico.ico")

    # Todo JSON versionado precisa continuar parseável. Isso evita listas manuais
    # divergentes entre workflows quando novos manifests forem adicionados.
    for path in files:
        if path.suffix.casefold() != ".json":
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            issues.append(f"JSON inválido: {_relative(path, root)} ({exc})")

    manifest = root / "STAR_MANIFEST.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for key in ("name", "version", "release_status", "release_channel"):
            if not str(data.get(key, "")).strip():
                issues.append(f"STAR_MANIFEST.json sem campo obrigatório: {key}")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        # Já reportado acima quando versionado; mantém mensagem explícita caso
        # o arquivo esteja ausente.
        if not manifest.exists():
            issues.append("STAR_MANIFEST.json ausente")

    return sorted(set(issues))


def duplicate_content_groups(root: Path = ROOT) -> list[list[str]]:
    """Retorna duplicações não vazias para auditoria manual, sem falhar a CI."""
    groups: dict[str, list[str]] = {}
    for path in _tracked_files(root):
        try:
            if path.stat().st_size == 0:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
        groups.setdefault(digest, []).append(_relative(path, root))
    return sorted(
        (sorted(paths) for paths in groups.values() if len(paths) > 1),
        key=lambda items: (-len(items), items),
    )


def main() -> int:
    issues = collect_issues()
    if issues:
        print("Repository hygiene FAILED")
        for item in issues:
            print(f"- {item}")
        return 1

    duplicates = duplicate_content_groups()
    print("Repository hygiene OK")
    if duplicates:
        print(f"Duplicações exatas não vazias para revisão: {len(duplicates)}")
        for group in duplicates[:10]:
            print("  - " + " | ".join(group))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
