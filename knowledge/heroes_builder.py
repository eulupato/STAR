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
from knowledge.sources.marvel_catalog import MarvelMasterCatalog
from knowledge.sources.wikidata import WikidataClient, merge_wikidata_profile

log = get_logger("heroes.builder")


@dataclass
class UniverseBuildStats:
    pdf_pages: int = 0
    pdf_saved: int = 0
    pdf_rejected: int = 0
    ocr_pages: int = 0
    master_catalog_saved: int = 0
    master_image_refs: int = 0
    master_images_cached: int = 0
    purged_untrusted_pdf: int = 0
    official_catalog_saved: int = 0
    official_profiles: int = 0
    official_missing: int = 0
    supplemental_profiles: int = 0
    supplemental_descriptions: int = 0
    supplemental_images: int = 0
    supplemental_missing: int = 0


@dataclass
class HeroesBuildReport:
    generated_at: str
    marvel: UniverseBuildStats = field(default_factory=UniverseBuildStats)
    dc: UniverseBuildStats = field(default_factory=UniverseBuildStats)
    total_characters: int = 0
    with_images: int = 0
    with_descriptions: int = 0
    with_verified_descriptions: int = 0
    fallback_descriptions: int = 0
    complete_cards: int = 0
    missing_image_count: int = 0
    missing_description_count: int = 0
    missing_verified_description_count: int = 0
    with_pdf_source: int = 0
    with_official_source: int = 0
    with_supplemental_source: int = 0
    sourced_images: int = 0
    open_licensed_images: int = 0
    official_reference_images: int = 0
    images_without_rights_metadata: int = 0
    image_rejection_reasons: dict[str, int] = field(default_factory=dict)
    image_rejections: list[dict] = field(default_factory=list)
    rich_cards: int = 0
    field_coverage: dict[str, dict] = field(default_factory=dict)
    field_coverage_by_universe: dict[str, dict[str, dict]] = field(default_factory=dict)
    missing_by_field: dict[str, list[str]] = field(default_factory=dict)
    missing_images: list[str] = field(default_factory=list)
    missing_descriptions: list[str] = field(default_factory=list)
    missing_verified_descriptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class HeroesKnowledgeBuilder:
    def __init__(
        self,
        engine: KnowledgeEngine,
        local_root: str | Path,
        *,
        marvel_pack_root: str | Path | None = None,
    ):
        self.engine = engine
        self.local_root = Path(local_root)
        self.local_root.mkdir(parents=True, exist_ok=True)
        self.pdf_cache = self.local_root / "cache" / "pdf"
        self.official_cache = self.local_root / "cache" / "official"
        self.wikidata_cache = self.local_root / "cache" / "wikidata"
        self.reports_dir = self.local_root / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.importer = HeroEncyclopediaImporter(engine, self.pdf_cache)
        self.web = OfficialWebClient(self.official_cache)
        self.wikidata = WikidataClient(self.wikidata_cache)
        self.marvel_master = MarvelMasterCatalog(marvel_pack_root)

    @staticmethod
    def _progress(stage: str, current: int, total: int):
        total = max(1, int(total))
        current = min(max(0, int(current)), total)
        percent = current * 100 / total
        print(
            f"[STAR] {stage}: {current} / {total} ({percent:5.1f}%)",
            flush=True,
        )

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

    @staticmethod
    def _has_local_image(entity) -> bool:
        value = getattr(entity, "image", None)
        if not value:
            return False
        try:
            return Path(str(value)).is_file()
        except OSError:
            return False

    @staticmethod
    def _description_is_verified(entity) -> bool:
        if not getattr(entity, "description", None):
            return False
        kind = (getattr(entity, "metadata", {}) or {}).get("description_kind")
        return kind != "catalog_fallback"

    @staticmethod
    def _field_present(entity, field_name: str) -> bool:
        if field_name == "verified_description":
            return HeroesKnowledgeBuilder._description_is_verified(entity)
        if field_name == "real_name":
            return bool((entity.attributes or {}).get("real_name"))
        if field_name == "appearances":
            return bool((entity.attributes or {}).get("appearances"))
        value = getattr(entity, field_name, None)
        if isinstance(value, (list, tuple, set, dict)):
            return bool(value)
        return bool(str(value).strip()) if value is not None else False

    @staticmethod
    def _image_rights_kind(entity) -> str:
        if not HeroesKnowledgeBuilder._has_local_image(entity):
            return "missing"
        metadata = getattr(entity, "metadata", {}) or {}
        attributions = metadata.get("image_attribution", {}) or {}
        image = str(getattr(entity, "image", "") or "")
        record = attributions.get(image) if isinstance(attributions, dict) else None
        if not isinstance(record, dict) and isinstance(attributions, dict):
            record = next(
                (item for item in attributions.values() if isinstance(item, dict)),
                None,
            )
        if not isinstance(record, dict):
            return "unknown"
        rights_status = str(record.get("rights_status") or "").strip()
        license_name = str(record.get("license") or "").strip().lower()
        if rights_status == "open_license_verified":
            return "open_licensed"
        if rights_status == "official_source_local_reference":
            return "official_reference"
        if license_name and license_name not in {
            "no open license recorded",
            "licença registrada na fonte",
        }:
            return "open_licensed"
        return "unknown"

    def _import_pdf(
        self,
        path: Path | None,
        *,
        universe: str,
        publisher: str,
        allow_ocr: bool,
        existing_only: bool = False,
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
            existing_only=existing_only,
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
        include_marvel: bool = False,
    ):
        entities = self.engine.search_entities(
            "",
            filters={"category": "character"},
            limit=10000,
        )
        if limit > 0:
            entities = entities[:limit]

        for entity in entities:
            if entity.universe == "Marvel" and not include_marvel:
                continue
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
            if images and not self._has_local_image(entity):
                image_path = self.web.cache_image(
                    profile.image_url,
                    online=online,
                    context=entity.name,
                    source_ref="official_web",
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

    def _supplement_missing(
        self,
        stats_by_universe: dict[str, UniverseBuildStats],
        *,
        online: bool,
        images: bool,
        force: bool,
        limit: int = 0,
        delay_seconds: float = 0.12,
    ):
        entities = self.engine.search_entities(
            "",
            filters={"category": "character"},
            limit=10000,
        )
        candidates = [
            entity
            for entity in entities
            if entity.universe in stats_by_universe
            and (
                not self._description_is_verified(entity)
                or self._image_rights_kind(entity) != "open_licensed"
                or not entity.occupation
                or not entity.affiliations
                or not entity.creators
                or not entity.gender
            )
        ]
        if limit > 0:
            candidates = candidates[:limit]

        total = len(candidates)
        for index, entity in enumerate(candidates, start=1):
            stats = stats_by_universe[entity.universe]
            needed_description = not self._description_is_verified(entity)
            needed_image = (
                images
                and self._image_rights_kind(entity) != "open_licensed"
            )
            before_description = entity.description
            before_image = entity.image

            profile = self.wikidata.fetch_profile(
                entity,
                online=online,
                force=force,
                include_image=needed_image,
            )
            if profile is None:
                stats.supplemental_missing += 1
            else:
                image_path = None
                if needed_image and profile.image_url:
                    image_path = self.wikidata.cache_commons_image(
                        profile.image_url,
                        online=online,
                        entity_name=entity.name,
                        qid=profile.qid,
                    )
                merged = merge_wikidata_profile(
                    entity,
                    profile,
                    image_path=image_path,
                )
                self.engine.upsert_entity(merged)
                stats.supplemental_profiles += 1
                if (
                    needed_description
                    and merged.description != before_description
                ):
                    stats.supplemental_descriptions += 1
                if (
                    needed_image
                    and merged.image != before_image
                    and self._has_local_image(merged)
                ):
                    stats.supplemental_images += 1

            if total and (
                index == 1
                or index == total
                or index % 25 == 0
            ):
                self._progress(
                    "ENRIQUECIMENTO SUPLEMENTAR",
                    index,
                    total,
                )
            if online and delay_seconds > 0:
                time.sleep(delay_seconds)

    @staticmethod
    def _fallback_description(entity) -> str:
        publisher = (
            entity.publisher
            or entity.universe
            or "catálogo de heróis"
        )
        universe = entity.universe or "universo registrado"
        details = []
        attributes = entity.attributes or {}
        real_name = str(
            attributes.get("real_name") or ""
        ).strip()
        if real_name:
            details.append(
                f"identidade registrada: {real_name}"
            )
        if entity.species:
            details.append(
                f"tipo/espécie: {entity.species}"
            )
        if entity.team:
            details.append(
                "equipes: " + ", ".join(entity.team[:3])
            )
        if entity.powers:
            details.append(
                "poderes registrados: "
                + ", ".join(entity.powers[:4])
            )

        text = (
            f"{entity.name} integra o catálogo de personagens e entidades da "
            f"{publisher} no universo {universe}."
        )
        if details:
            text += " " + "; ".join(details) + "."
        text += (
            " A biografia detalhada ainda não foi encontrada "
            "em uma fonte estruturada verificada."
        )
        return text

    def _ensure_descriptions(self) -> int:
        entities = self.engine.search_entities(
            "",
            filters={"category": "character"},
            limit=10000,
        )
        updated = 0
        for entity in entities:
            if entity.description:
                continue
            entity.description = self._fallback_description(entity)
            entity.metadata["description_kind"] = "catalog_fallback"
            entity.metadata["description_verified"] = False
            self.engine.upsert_entity(entity)
            updated += 1
        return updated

    def _collect_image_rejections(
        self,
        report: HeroesBuildReport,
    ) -> None:
        records = [
            *getattr(self.web, "image_rejections", []),
            *getattr(self.wikidata, "image_rejections", []),
        ]
        report.image_rejections = records[:1000]
        counts: dict[str, int] = {}
        for record in records:
            reason = str((record or {}).get("reason") or "unknown")
            counts[reason] = counts.get(reason, 0) + 1
        report.image_rejection_reasons = dict(
            sorted(
                counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        )

    def _coverage(self, report: HeroesBuildReport):
        entities = self.engine.search_entities(
            "",
            filters={"category": "character"},
            limit=10000,
        )
        report.total_characters = len(entities)
        report.with_images = sum(
            self._has_local_image(entity)
            for entity in entities
        )
        report.with_descriptions = sum(
            bool(entity.description)
            for entity in entities
        )
        report.with_verified_descriptions = sum(
            self._description_is_verified(entity)
            for entity in entities
        )
        report.fallback_descriptions = sum(
            (entity.metadata or {}).get("description_kind")
            == "catalog_fallback"
            for entity in entities
        )
        report.complete_cards = sum(
            self._has_local_image(entity)
            and self._description_is_verified(entity)
            for entity in entities
        )
        report.rich_cards = sum(
            self._has_local_image(entity)
            and self._description_is_verified(entity)
            and any(
                (
                    entity.powers,
                    entity.abilities,
                    entity.equipment,
                    entity.occupation,
                    entity.affiliations,
                    entity.team,
                )
            )
            for entity in entities
        )
        report.with_pdf_source = sum(
            any(
                source.source_type == "PDF"
                for source in entity.sources
            )
            for entity in entities
        )
        report.with_official_source = sum(
            any(
                source.source_type in {
                    "official_web",
                    "official_catalog",
                    "marvel_master",
                }
                for source in entity.sources
            )
            for entity in entities
        )
        report.with_supplemental_source = sum(
            any(
                source.source_type in {
                    "wikidata",
                    "wikimedia_commons",
                }
                for source in entity.sources
            )
            for entity in entities
        )

        rights = [self._image_rights_kind(entity) for entity in entities]
        report.sourced_images = sum(
            value in {"official_reference", "open_licensed"}
            for value in rights
        )
        report.open_licensed_images = rights.count("open_licensed")
        report.official_reference_images = rights.count("official_reference")
        report.images_without_rights_metadata = rights.count("unknown")

        tracked_fields = (
            "verified_description",
            "real_name",
            "powers",
            "abilities",
            "equipment",
            "occupation",
            "affiliations",
            "team",
            "origin_place",
            "first_appearance",
            "appearances",
            "relationships",
            "creators",
            "species",
            "gender",
        )
        by_universe: dict[str, list] = {}
        for entity in entities:
            key = str(entity.universe or "Unknown")
            by_universe.setdefault(key, []).append(entity)

        report.field_coverage = {}
        report.field_coverage_by_universe = {}
        report.missing_by_field = {}
        total = max(1, len(entities))

        for field_name in tracked_fields:
            count = sum(
                self._field_present(entity, field_name)
                for entity in entities
            )
            missing = [
                entity.name
                for entity in entities
                if not self._field_present(entity, field_name)
            ]
            report.field_coverage[field_name] = {
                "count": count,
                "total": len(entities),
                "percent": round(count * 100 / total, 2) if entities else 0.0,
                "missing": len(missing),
            }
            report.missing_by_field[field_name] = missing[:500]

        for universe, universe_entities in sorted(by_universe.items()):
            universe_total = len(universe_entities)
            report.field_coverage_by_universe[universe] = {}
            for field_name in tracked_fields:
                count = sum(
                    self._field_present(entity, field_name)
                    for entity in universe_entities
                )
                report.field_coverage_by_universe[universe][field_name] = {
                    "count": count,
                    "total": universe_total,
                    "percent": (
                        round(count * 100 / universe_total, 2)
                        if universe_total
                        else 0.0
                    ),
                }

        missing_images = [
            entity.name
            for entity in entities
            if not self._has_local_image(entity)
        ]
        missing_descriptions = [
            entity.name
            for entity in entities
            if not entity.description
        ]
        missing_verified = [
            entity.name
            for entity in entities
            if not self._description_is_verified(entity)
        ]

        report.missing_image_count = len(missing_images)
        report.missing_description_count = len(missing_descriptions)
        report.missing_verified_description_count = len(missing_verified)
        report.missing_images = missing_images[:500]
        report.missing_descriptions = missing_descriptions[:500]
        report.missing_verified_descriptions = missing_verified[:500]

        if report.missing_image_count:
            report.warnings.append(
                f"{report.missing_image_count} registros "
                "ainda sem imagem local válida."
            )
        if report.images_without_rights_metadata:
            report.warnings.append(
                f"{report.images_without_rights_metadata} imagens locais "
                "ainda não possuem metadados de direitos/proveniência suficientes."
            )
        if report.missing_verified_description_count:
            report.warnings.append(
                f"{report.missing_verified_description_count} "
                "registros usam descrição básica do catálogo."
            )

    def audit(self) -> HeroesBuildReport:
        """Gera cobertura do catálogo atual sem alterar entidades nem acessar a rede."""
        report = HeroesBuildReport(
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        self._coverage(report)
        self._collect_image_rejections(report)
        report_path = self.reports_dir / "heroes_coverage_report.json"
        report_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return report

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
        import_marvel_master: bool = True,
        cache_marvel_images: bool = False,
        marvel_image_limit: int = 0,
        live_marvel_enrichment: bool = False,
        wikidata_fallback: bool = False,
        wikidata_limit: int = 0,
        wikidata_images: bool = True,
    ) -> HeroesBuildReport:
        marvel_path = self._check_pdf(marvel_pdf, "PDF Marvel")
        dc_path = self._check_pdf(dc_pdf, "PDF DC")

        report = HeroesBuildReport(
            generated_at=datetime.now(timezone.utc).isoformat()
        )

        if import_marvel_master:
            report.marvel.purged_untrusted_pdf = (
                self.engine.store.delete_source_only_characters(
                    universe="Marvel",
                    source_type="PDF",
                    trusted_source_types=(
                        "marvel_master",
                        "official_web",
                        "official_catalog",
                        "wikidata",
                        "knowledge_pack",
                    ),
                )
            )
            report.marvel.master_catalog_saved = self.marvel_master.import_into(
                self.engine,
                progress=self._progress,
            )
            report.marvel.master_image_refs = self.marvel_master.image_reference_count

        marvel_pdf_stats = self._import_pdf(
            marvel_path,
            universe="Marvel",
            publisher="Marvel Comics",
            allow_ocr=marvel_ocr,
            existing_only=True,
        )
        report.marvel.pdf_pages = marvel_pdf_stats.pdf_pages
        report.marvel.pdf_saved = marvel_pdf_stats.pdf_saved
        report.marvel.pdf_rejected = marvel_pdf_stats.pdf_rejected
        report.marvel.ocr_pages = marvel_pdf_stats.ocr_pages

        report.dc = self._import_pdf(
            dc_path,
            universe="DC",
            publisher="DC Comics",
            allow_ocr=dc_ocr,
            existing_only=False,
        )

        if cache_marvel_images and import_marvel_master:
            report.marvel.master_images_cached = self.marvel_master.cache_images(
                self.engine,
                self.web,
                online=True,
                limit=max(0, int(marvel_image_limit)),
                progress=self._progress,
            )

        if online_enrichment:
            self._enrich(
                {"Marvel": report.marvel, "DC": report.dc},
                online=True,
                images=cache_images,
                force=force_web,
                limit=enrichment_limit,
                include_marvel=live_marvel_enrichment,
            )

        if wikidata_fallback:
            self._supplement_missing(
                {"Marvel": report.marvel, "DC": report.dc},
                online=True,
                images=cache_images and wikidata_images,
                force=force_web,
                limit=max(0, int(wikidata_limit)),
            )

        self._ensure_descriptions()
        self._coverage(report)
        self._collect_image_rejections(report)
        report_path = self.reports_dir / "heroes_build_report.json"
        report_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        log.info(
            "Heroes build: %s personagens; %s imagens; "
            "%s descrições verificadas; %s fichas completas.",
            report.total_characters,
            report.with_images,
            report.with_verified_descriptions,
            report.complete_cards,
        )
        return report
