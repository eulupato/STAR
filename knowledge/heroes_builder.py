"""Orquestrador da base local da Ilha dos Heróis."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time

from core.logging_config import get_logger
from knowledge.engine import KnowledgeEngine
from knowledge.importers.heroes import HeroEncyclopediaImporter
from knowledge.sources.official import (
    OfficialWebClient,
    merge_official_profile,
    source_for_entity,
)
from knowledge.sources.marvel_catalog import MarvelOfficialCatalog

log = get_logger("heroes.builder")


@dataclass
class UniverseBuildStats:
    pdf_pages: int = 0
    pdf_saved: int = 0
    pdf_rejected: int = 0
    ocr_pages: int = 0
    official_catalog_saved: int = 0
    official_profiles: int = 0
    official_missing: int = 0


@dataclass
class HeroesBuildReport:
    generated_at: str
    marvel: UniverseBuildStats = field(default_factory=UniverseBuildStats)
    dc: UniverseBuildStats = field(default_factory=UniverseBuildStats)
    total_characters: int = 0
    with_images: int = 0
    with_pdf_source: int = 0
    with_official_source: int = 0
    missing_images: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class HeroesKnowledgeBuilder:
    def __init__(self, engine: KnowledgeEngine, local_root: str | Path):
        self.engine = engine
        self.local_root = Path(local_root)
        self.local_root.mkdir(parents=True, exist_ok=True)
        self.pdf_cache = self.local_root / "cache" / "pdf"
        self.official_cache = self.local_root / "cache" / "official"
        self.reports_dir = self.local_root / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.importer = HeroEncyclopediaImporter(engine, self.pdf_cache)
        self.web = OfficialWebClient(self.official_cache)

    @staticmethod
    def _check_pdf(path: str | Path | None, label: str) -> Path | None:
        if path is None:
            return None
        value = Path(path)
        if not value.exists() or not value.is_file():
            raise FileNotFoundError(f"{label} não encontrado: {value}")
        if value.suffix.lower() != ".pdf":
            raise ValueError(f"{label} precisa ser PDF: {value}")
        return value

    @staticmethod
    def _require_ocr_if_requested(enabled: bool):
        if enabled and shutil.which("tesseract") is None:
            raise RuntimeError(
                "OCR solicitado, mas Tesseract não está instalado ou não está no PATH."
            )

    def _import_pdf(
        self,
        path: Path | None,
        *,
        universe: str,
        publisher: str,
        allow_ocr: bool,
    ) -> UniverseBuildStats:
        stats = UniverseBuildStats()
        if path is None:
            return stats
        self._require_ocr_if_requested(allow_ocr)
        imported = self.importer.import_pdf(
            path,
            universe=universe,
            publisher=publisher,
            allow_ocr=allow_ocr,
            render_images=True,
        )
        stats.pdf_pages = imported.pages_seen
        stats.pdf_saved = imported.entities_saved
        stats.pdf_rejected = imported.entities_rejected
        stats.ocr_pages = imported.ocr_pages
        return stats

    def _enrich(
        self,
        stats_by_universe: dict[str, UniverseBuildStats],
        *,
        online: bool,
        images: bool,
        force: bool,
        limit: int = 0,
        delay_seconds: float = 0.20,
    ):
        entities = self.engine.search_entities(
            "",
            filters={"category": "character"},
            limit=5000,
        )
        if limit > 0:
            entities = entities[:limit]

        for entity in entities:
            stats = stats_by_universe.get(entity.universe or "")
            if stats is None:
                continue
            source = source_for_entity(entity, self.web)
            if source is None:
                continue

            profile = source.fetch_profile(
                entity,
                online=online,
                force=force,
            )
            if profile is None:
                stats.official_missing += 1
                continue

            image_path = None
            if images:
                image_path = self.web.cache_image(
                    profile.image_url,
                    online=online,
                )
            self.engine.upsert_entity(
                merge_official_profile(
                    entity,
                    profile,
                    image_path=image_path,
                )
            )
            stats.official_profiles += 1
            if online and delay_seconds > 0:
                time.sleep(delay_seconds)

    def _coverage(self, report: HeroesBuildReport):
        entities = self.engine.search_entities(
            "",
            filters={"category": "character"},
            limit=5000,
        )
        report.total_characters = len(entities)
        report.with_images = sum(bool(entity.image) for entity in entities)
        report.with_pdf_source = sum(
            any(source.source_type == "PDF" for source in entity.sources)
            for entity in entities
        )
        report.with_official_source = sum(
            any(
                source.source_type in {"official_web", "official_catalog"}
                for source in entity.sources
            )
            for entity in entities
        )
        report.missing_images = [
            entity.name for entity in entities if not entity.image
        ][:500]

    def build(
        self,
        *,
        marvel_pdf: str | Path | None = None,
        dc_pdf: str | Path | None = None,
        marvel_ocr: bool = True,
        dc_ocr: bool = False,
        online_enrichment: bool = False,
        cache_images: bool = True,
        force_web: bool = False,
        enrichment_limit: int = 0,
        import_marvel_catalog: bool = True,
        marvel_catalog_max_pages: int = 120,
    ) -> HeroesBuildReport:
        marvel_path = self._check_pdf(marvel_pdf, "PDF Marvel")
        dc_path = self._check_pdf(dc_pdf, "PDF DC")

        report = HeroesBuildReport(
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        report.marvel = self._import_pdf(
            marvel_path,
            universe="Marvel",
            publisher="Marvel Comics",
            allow_ocr=marvel_ocr,
        )
        report.dc = self._import_pdf(
            dc_path,
            universe="DC",
            publisher="DC Comics",
            allow_ocr=dc_ocr,
        )

        if online_enrichment and import_marvel_catalog:
            report.marvel.official_catalog_saved = MarvelOfficialCatalog(
                self.web
            ).import_into(
                self.engine,
                online=True,
                force=force_web,
                max_pages=marvel_catalog_max_pages,
            )

        if online_enrichment:
            self._enrich(
                {"Marvel": report.marvel, "DC": report.dc},
                online=True,
                images=cache_images,
                force=force_web,
                limit=enrichment_limit,
            )

        self._coverage(report)
        report_path = self.reports_dir / "heroes_build_report.json"
        report_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        log.info(
            "Heroes build: %s personagens; %s imagens; %s fontes oficiais.",
            report.total_characters,
            report.with_images,
            report.with_official_source,
        )
        return report
