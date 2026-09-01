"""Constrói a base local completa da Ilha dos Heróis."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import KNOWLEDGE_DB
from knowledge.bootstrap import bootstrap_legacy_heroes
from knowledge.engine import KnowledgeEngine
from knowledge.heroes_builder import HeroesKnowledgeBuilder


def parser():
    p = argparse.ArgumentParser(
        description="Importa os PDFs Marvel/DC e opcionalmente enriquece pelos sites oficiais."
    )
    p.add_argument("--marvel-pdf", type=Path)
    p.add_argument("--dc-pdf", type=Path)
    p.add_argument("--online", action="store_true", help="Consulta dc.com e marvel.com.")
    p.add_argument("--no-marvel-ocr", action="store_true")
    p.add_argument("--dc-ocr", action="store_true")
    p.add_argument("--no-images", action="store_true")
    p.add_argument("--force-web", action="store_true")
    p.add_argument("--enrichment-limit", type=int, default=0)
    return p


def main():
    args = parser().parse_args()
    engine = KnowledgeEngine(ROOT / KNOWLEDGE_DB)
    bootstrap_legacy_heroes(
        engine,
        ROOT / "knowledge" / "packs" / "heroes" / "heroes.json",
    )
    builder = HeroesKnowledgeBuilder(
        engine,
        ROOT / "knowledge" / "local",
    )
    report = builder.build(
        marvel_pdf=args.marvel_pdf,
        dc_pdf=args.dc_pdf,
        marvel_ocr=not args.no_marvel_ocr,
        dc_ocr=args.dc_ocr,
        online_enrichment=args.online,
        cache_images=not args.no_images,
        force_web=args.force_web,
        enrichment_limit=max(0, args.enrichment_limit),
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
