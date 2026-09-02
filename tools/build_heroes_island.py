"""Constrói/sincroniza a base local da Ilha dos Heróis."""
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
        description=(
            "Sincroniza o catálogo mestre Marvel versionado, aceita PDFs como "
            "complemento e pode enriquecer DC por fonte oficial."
        )
    )
    p.add_argument(
        "--marvel-pdf",
        type=Path,
        help="PDF Marvel opcional; complementa apenas identidades já catalogadas.",
    )
    p.add_argument("--dc-pdf", type=Path)
    p.add_argument(
        "--online",
        action="store_true",
        help="Enriquecimento web opcional; Marvel live fica desligado por padrão.",
    )
    p.add_argument("--no-marvel-ocr", action="store_true")
    p.add_argument("--dc-ocr", action="store_true")
    p.add_argument("--no-images", action="store_true")
    p.add_argument("--force-web", action="store_true")
    p.add_argument("--enrichment-limit", type=int, default=0)
    p.add_argument(
        "--skip-marvel-master",
        action="store_true",
        help="Não sincroniza o catálogo mestre Marvel versionado.",
    )
    p.add_argument(
        "--cache-marvel-images",
        action="store_true",
        help="Baixa as referências visuais Marvel para o cache local.",
    )
    p.add_argument(
        "--marvel-image-limit",
        type=int,
        default=0,
        help="Limita downloads visuais; 0 = todas as referências.",
    )
    p.add_argument(
        "--live-marvel-enrichment",
        action="store_true",
        help="Tenta perfis live da Marvel explicitamente; pode sofrer HTTP 403.",
    )
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
        import_marvel_master=not args.skip_marvel_master,
        cache_marvel_images=args.cache_marvel_images,
        marvel_image_limit=max(0, args.marvel_image_limit),
        live_marvel_enrichment=args.live_marvel_enrichment,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
