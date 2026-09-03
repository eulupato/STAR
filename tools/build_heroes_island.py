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
            "Sincroniza o catálogo mestre, prioriza fontes oficiais e usa "
            "Wikidata/Commons somente para lacunas verificáveis."
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
        help="Habilita enriquecimento web; fontes oficiais são consultadas primeiro.",
    )
    p.add_argument(
        "--audit-only",
        action="store_true",
        help="Gera apenas o relatório de cobertura atual, sem alterar entidades ou acessar a rede.",
    )
    p.add_argument(
        "--scan-images",
        action="store_true",
        help=(
            "Varre personagem por personagem procurando referência visual "
            "segura: Commons licenciado, perfil oficial e manifesto Marvel."
        ),
    )
    p.add_argument(
        "--restart-image-scan",
        action="store_true",
        help="Ignora checkpoint anterior e refaz a varredura visual.",
    )
    p.add_argument(
        "--image-scan-limit",
        type=int,
        default=0,
        help="Limita personagens na varredura visual; 0 = catálogo inteiro.",
    )
    p.add_argument(
        "--improve-existing-images",
        action="store_true",
        help="Também consulta Commons para personagens que já possuem imagem válida.",
    )
    p.add_argument(
        "--scan-live-official",
        action="store_true",
        help="Habilita fallback live Marvel/DC; desligado por padrão por causa de HTTP 403.",
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
    p.add_argument(
        "--wikidata-fallback",
        action="store_true",
        help=(
            "Preenche lacunas de descrição, campos estruturados e imagem com "
            "Wikidata/Wikimedia Commons, sem sobrescrever fontes primárias."
        ),
    )
    p.add_argument(
        "--wikidata-limit",
        type=int,
        default=0,
        help="Limita o enriquecimento suplementar; 0 = todos os candidatos.",
    )
    p.add_argument(
        "--no-wikidata-images",
        action="store_true",
        help="Usa Wikidata somente para descrições, sem cachear imagens do Commons.",
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
    if args.audit_only:
        report = builder.audit()
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    if args.scan_images:
        # Garante que o snapshot versionado atual esteja presente antes da busca.
        if not args.skip_marvel_master:
            builder.marvel_master.import_into(
                engine,
                progress=builder._progress,
            )
        try:
            report = builder.scan_visual_references(
                online=True,
                resume=not args.restart_image_scan,
                force=args.restart_image_scan or args.force_web,
                limit=max(0, args.image_scan_limit),
                improve_existing=args.improve_existing_images,
                live_official_fallback=args.scan_live_official,
            )
        except KeyboardInterrupt:
            print(
                "\n[STAR] Varredura interrompida pelo usuário. "
                "O checkpoint anterior foi preservado.",
                flush=True,
            )
            raise SystemExit(130)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

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
        wikidata_fallback=args.wikidata_fallback,
        wikidata_limit=max(0, args.wikidata_limit),
        wikidata_images=not args.no_wikidata_images,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
