#!/usr/bin/env python3
"""Instala o catálogo Marvel Database/Fandom como overlay local da Ilha dos Heróis.

O repositório não recebe o dataset massivo. Este utilitário usa os TXT coletados
pelo usuário e gera um índice TSV em knowledge/local/heroes/, que já é ignorado
pelo Git. Depois disso a STAR consegue consultar todo o inventário offline.

Uso:
    python tools/install_marvel_catalog.py
ou:
    python tools/install_marvel_catalog.py --source-dir "C:/Users/.../Downloads"
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata

CHARACTERS_FILE = "MARVEL_DATABASE_PERSONAGENS.txt"
TEAMS_FILE = "MARVEL_DATABASE_EQUIPES.txt"
EXPECTED_CHARACTERS = 104_173
EXPECTED_TEAMS = 6_851


def _ascii_key(text: str):
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold().strip()
    value = re.sub(r"^[^0-9a-z]+", "", value)
    parts = re.split(r"(\d+)", value)
    return tuple(int(part) if part.isdigit() else part for part in parts)


def _read_unique(path: Path):
    raw = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    raw = [line for line in raw if line]
    unique = set(raw)
    return sorted(unique, key=_ascii_key), len(raw) - len(unique)


def _find_source_dir(explicit: str | None):
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend(
        [
            Path.cwd(),
            Path.home() / "Downloads",
            Path.home() / "Área de Trabalho",
            Path.home() / "Desktop",
        ]
    )
    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if (resolved / CHARACTERS_FILE).is_file() and (resolved / TEAMS_FILE).is_file():
            return resolved
    return None


def _atomic_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8", newline="\n")
    temp.replace(path)


def build_catalog(source_dir: Path, output_dir: Path):
    characters_path = source_dir / CHARACTERS_FILE
    teams_path = source_dir / TEAMS_FILE

    characters, character_dupes = _read_unique(characters_path)
    teams, team_dupes = _read_unique(teams_path)

    typed = [("PERSONAGEM", name) for name in characters]
    typed.extend(("EQUIPE", name) for name in teams)
    typed.sort(key=lambda item: (_ascii_key(item[1]), item[0]))

    lines = ["tipo\tentrada"]
    lines.extend(f"{kind}\t{name}" for kind, name in typed)
    catalog_text = "\n".join(lines) + "\n"
    digest = hashlib.sha256(catalog_text.encode("utf-8")).hexdigest()

    catalog_path = output_dir / "catalog.tsv"
    meta_path = output_dir / "catalog.meta.json"
    _atomic_write(catalog_path, catalog_text)

    overlap = len(set(characters).intersection(teams))
    meta = {
        "schema": "star.heroes.catalog.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "name": "Marvel Database / Fandom",
            "official_marvel": False,
            "characters_category": "https://marvel.fandom.com/wiki/Category:Characters",
            "teams_category": "https://marvel.fandom.com/wiki/Category:Teams",
            "input_files": [CHARACTERS_FILE, TEAMS_FILE],
        },
        "characters": len(characters),
        "teams": len(teams),
        "total": len(typed),
        "duplicates_removed": {
            "characters": character_dupes,
            "teams": team_dupes,
        },
        "cross_category_same_title": overlap,
        "variants_preserved": True,
        "sha256": digest,
    }
    _atomic_write(
        meta_path,
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
    )
    return catalog_path, meta_path, meta


def main():
    parser = argparse.ArgumentParser(
        description="Instala o catálogo local Marvel Database para a Ilha dos Heróis."
    )
    parser.add_argument(
        "--source-dir",
        help="Pasta contendo MARVEL_DATABASE_PERSONAGENS.txt e MARVEL_DATABASE_EQUIPES.txt.",
    )
    parser.add_argument(
        "--project-root",
        help="Raiz da STAR. Por padrão é detectada a partir deste script.",
    )
    args = parser.parse_args()

    project_root = (
        Path(args.project_root).expanduser().resolve()
        if args.project_root
        else Path(__file__).resolve().parents[1]
    )
    source_dir = _find_source_dir(args.source_dir)
    if source_dir is None:
        raise SystemExit(
            "Não encontrei os dois arquivos de origem. "
            "Use --source-dir apontando para a pasta que contém "
            f"{CHARACTERS_FILE} e {TEAMS_FILE}."
        )

    output_dir = project_root / "knowledge" / "local" / "heroes"
    catalog_path, meta_path, meta = build_catalog(source_dir, output_dir)

    print("=" * 72)
    print("⭐ STAR — CATÁLOGO MARVEL LOCAL INSTALADO")
    print("=" * 72)
    print(f"Origem:      {source_dir}")
    print(f"Personagens: {meta['characters']}")
    print(f"Equipes:     {meta['teams']}")
    print(f"Total:       {meta['total']}")
    print(f"Catálogo:    {catalog_path}")
    print(f"Metadados:   {meta_path}")
    print(f"SHA-256:     {meta['sha256']}")

    if meta["characters"] != EXPECTED_CHARACTERS or meta["teams"] != EXPECTED_TEAMS:
        print()
        print(
            "⚠️ A contagem difere do snapshot auditado em 06/09/2026 "
            f"({EXPECTED_CHARACTERS} personagens / {EXPECTED_TEAMS} equipes). "
            "O catálogo foi instalado com as contagens reais dos arquivos fornecidos."
        )

    print()
    print("✅ O dataset fica local e não será enviado ao GitHub.")
    print("✅ Reinicie a STAR e abra HUB → HERÓIS para usar o catálogo offline.")


if __name__ == "__main__":
    main()
