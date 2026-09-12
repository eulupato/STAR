"""Constrói o índice SQLite offline de idiomas da STAR.

Aceita:
1) JSONL normalizado: term, source_locale, target_locale, translation, source;
2) TSV normalizado com as mesmas cinco colunas;
3) JSONL do Wiktextract/Kaikki com --format kaikki e --source-locale.

O script não baixa dados sozinho: isso evita downloads silenciosos de gigabytes.
Depois da construção, consultas da STAR usam somente o SQLite local.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.offline_dictionary import DEFAULT_DB, DICTIONARY_SOURCES, normalize_term

LANG_TO_LOCALE = {
    "pt": "pt-BR", "por": "pt-BR", "pt-br": "pt-BR",
    "en": "en-US", "eng": "en-US", "en-us": "en-US", "en-gb": "en-GB",
    "es": "es-ES", "spa": "es-ES",
    "it": "it-IT", "ita": "it-IT",
    "fr": "fr-FR", "fra": "fr-FR", "fre": "fr-FR",
}


def connect(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS translations (
            source_locale TEXT NOT NULL,
            target_locale TEXT NOT NULL,
            term TEXT NOT NULL,
            term_norm TEXT NOT NULL,
            translation TEXT NOT NULL,
            source TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (source_locale, target_locale, term_norm, translation, source)
        );
        CREATE INDEX IF NOT EXISTS idx_translation_lookup
        ON translations(source_locale, target_locale, term_norm, priority DESC);
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """
    )
    return db


def insert(db, source_locale, target_locale, term, translation, source, priority=0):
    term = str(term or "").strip()
    translation = str(translation or "").strip()
    if not term or not translation or source_locale == target_locale:
        return 0
    norm = normalize_term(term)
    if not norm:
        return 0
    db.execute(
        "INSERT OR IGNORE INTO translations(source_locale,target_locale,term,term_norm,translation,source,priority) VALUES(?,?,?,?,?,?,?)",
        (source_locale, target_locale, term, norm, translation, source, int(priority)),
    )
    return 1


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def import_normalized(db, path: Path, fmt: str):
    count = 0
    with open_text(path) as fh:
        if fmt == "tsv":
            for line in fh:
                if not line.strip() or line.startswith("#"):
                    continue
                p = line.rstrip("\n").split("\t")
                if len(p) < 5:
                    continue
                count += insert(db, p[1], p[2], p[0], p[3], p[4], 10)
        else:
            for line in fh:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                count += insert(
                    db,
                    row.get("source_locale"), row.get("target_locale"),
                    row.get("term"), row.get("translation"), row.get("source", path.name),
                    row.get("priority", 10),
                )
    return count


def import_kaikki(db, path: Path, source_locale: str):
    count = 0
    with open_text(path) as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            word = row.get("word")
            if not word:
                continue
            translations = []
            translations.extend(row.get("translations") or [])
            for sense in row.get("senses") or []:
                translations.extend(sense.get("translations") or [])
            for item in translations:
                code = str(item.get("code") or item.get("lang_code") or "").lower()
                target = LANG_TO_LOCALE.get(code)
                target_word = item.get("word") or item.get("roman")
                if target and target_word:
                    count += insert(db, source_locale, target, word, target_word, "Kaikki/Wiktionary", 20)
                    count += insert(db, target, source_locale, target_word, word, "Kaikki/Wiktionary", 15)
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--format", choices=("jsonl", "tsv", "kaikki"), default="jsonl")
    parser.add_argument("--source-locale", choices=("pt-BR", "en-US", "en-GB", "es-ES", "it-IT", "fr-FR"))
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    if args.format == "kaikki" and not args.source_locale:
        parser.error("--source-locale é obrigatório com --format kaikki")

    if any(len(v) < 5 for v in DICTIONARY_SOURCES.values()):
        raise SystemExit("Cada família linguística precisa manter pelo menos 5 fontes configuradas.")

    db = connect(args.db)
    total = 0
    try:
        for path in args.inputs:
            if args.format == "kaikki":
                added = import_kaikki(db, path, args.source_locale)
            else:
                added = import_normalized(db, path, args.format)
            total += added
            print(f"{path}: {added} relações importadas")
        db.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('schema','1')")
        db.commit()
    finally:
        db.close()
    print(f"STAR offline dictionary: {total} relações processadas -> {args.db}")


if __name__ == "__main__":
    main()
