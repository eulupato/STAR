"""CLI para importar enciclopédias de personagens para a STAR V3."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import KNOWLEDGE_DB
from knowledge.engine import KnowledgeEngine
from knowledge.importers import HeroEncyclopediaImporter


def build_parser():
    parser = argparse.ArgumentParser(description="Importa uma enciclopédia para a STAR.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--universe", required=True)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--ocr", action="store_true", help="Usa Tesseract em páginas sem texto.")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    return parser


def main():
    args = build_parser().parse_args()
    engine = KnowledgeEngine(ROOT / KNOWLEDGE_DB)
    importer = HeroEncyclopediaImporter(
        engine,
        ROOT / "knowledge" / "local" / "cache" / "pdf",
    )
    stats = importer.import_pdf(
        args.pdf,
        universe=args.universe,
        publisher=args.publisher,
        allow_ocr=args.ocr,
        start_page=args.start,
        end_page=args.end,
    )
    print(
        f"Importação concluída: {stats.pages_seen} páginas; "
        f"{stats.entities_saved} entidades; OCR em {stats.ocr_pages} páginas."
    )


if __name__ == "__main__":
    main()
