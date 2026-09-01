"""Importador estruturado para enciclopédias de personagens."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re

from core.logging_config import get_logger
from knowledge.entities import Entity, KnowledgeSource, Relationship
from knowledge.store import normalize_search_text

from .pdf import PdfDocumentReader, PdfPage

log = get_logger("knowledge.heroes_import")


FACT_PATTERNS = {
    "real_name": r"(?:REAL NAME|REAL NAME\s*:|Real name)\s*[:\-]?\s*([^\n|]{2,80})",
    "occupation": r"(?:OCCUPATION|Occupation)\s*[:\-]?\s*([^\n|]{2,100})",
    "base": r"(?:BASE|Base)\s*[:\-]?\s*([^\n|]{2,100})",
    "first_appearance": r"(?:FIRST APPEARANCE|First appearance)\s*[:\-]?\s*([^\n]{2,140})",
    "species": r"(?:SPECIES|Species)\s*[:\-]?\s*([^\n|]{2,80})",
    "status": r"(?:STATUS|Status)\s*[:\-]?\s*([^\n|]{2,80})",
    "known_relatives": r"(?:KNOWN RELATIVES|Known relatives)\s*[:\-]?\s*([^\n]{2,180})",
    "special": r"(?:SPECIAL POWERS/ABILITIES|SPECIAL POWERS|POWERS/ABILITIES|Special powers/abilities)\s*[:\-]?\s*([^\n]{2,240})",
}

GENERIC_HEADINGS = {
    "CONTENTS", "FOREWORD", "INTRODUCTION", "CONTRIBUTORS", "INDEX",
    "ACKNOWLEDGMENTS", "ACKNOWLEDGEMENTS", "AMAZING VEHICLES",
    "AMAZING WEAPONS", "ALIEN RACES", "GREAT TEAM-UPS",
    "ROMANTIC MOMENTS", "GREAT BATTLES", "STRANGE TIMES AND PLACES",
}


@dataclass
class ImportStats:
    pages_seen: int = 0
    pages_with_text: int = 0
    entities_detected: int = 0
    entities_saved: int = 0
    ocr_pages: int = 0


class HeroEncyclopediaImporter:
    def __init__(self, engine, cache_dir: str | Path):
        self.engine = engine
        self.reader = PdfDocumentReader(cache_dir)

    @staticmethod
    def _split_values(value: str | None) -> list[str]:
        if not value:
            return []
        parts = re.split(r"[,;/]|\band\b|\be\b", value, flags=re.IGNORECASE)
        return [item.strip(" .") for item in parts if item.strip(" .")]

    @staticmethod
    def _clean_heading(value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip(" :.-\t")
        return value

    @classmethod
    def _heading_candidates(cls, text: str) -> list[str]:
        candidates = []
        for raw in text.splitlines()[:18]:
            line = cls._clean_heading(raw)
            if not line or len(line) < 2 or len(line) > 60:
                continue
            normalized = normalize_search_text(line)
            if normalized.upper() in GENERIC_HEADINGS:
                continue
            if re.search(r"\b(?:FACTFILE|FIRST APPEARANCE|REAL NAME|OCCUPATION|BASE)\b", line, re.I):
                continue
            letters = [ch for ch in line if ch.isalpha()]
            if len(letters) < 2:
                continue
            uppercase_ratio = sum(ch.isupper() for ch in letters) / len(letters)
            titleish = uppercase_ratio >= 0.72 or line.istitle()
            if titleish:
                candidates.append(line)
        return candidates[:4]

    @staticmethod
    def _extract_fact(text: str, key: str) -> str | None:
        pattern = FACT_PATTERNS[key]
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        value = re.sub(r"\s+", " ", match.group(1)).strip(" .:-")
        return value or None

    @staticmethod
    def _summary(text: str, heading: str) -> str | None:
        cleaned = re.sub(r"\s+", " ", text)
        cleaned = re.sub(re.escape(heading), " ", cleaned, count=1, flags=re.I)
        cleaned = re.sub(
            r"(FACTFILE|FIRST APPEARANCE|REAL NAME|OCCUPATION|BASE|HEIGHT|WEIGHT|EYES|HAIR).*",
            "",
            cleaned,
            flags=re.I,
        ).strip()
        if len(cleaned) < 40:
            return None
        return cleaned[:700].rstrip()

    @classmethod
    def parse_page(
        cls,
        page: PdfPage,
        *,
        universe: str,
        publisher: str,
        source_file: str,
    ) -> list[Entity]:
        if len(page.text.strip()) < 40:
            return []

        headings = cls._heading_candidates(page.text)
        if not headings:
            return []

        # A maioria das páginas possui uma entrada dominante; múltiplos headings
        # são mantidos quando o OCR/texto deixa isso claro.
        entities = []
        for heading in headings:
            normalized = normalize_search_text(heading)
            if normalized in {normalize_search_text(item) for item in GENERIC_HEADINGS}:
                continue

            real_name = cls._extract_fact(page.text, "real_name")
            occupation = cls._extract_fact(page.text, "occupation")
            first_appearance = cls._extract_fact(page.text, "first_appearance")
            species = cls._extract_fact(page.text, "species")
            status = cls._extract_fact(page.text, "status")
            relatives = cls._extract_fact(page.text, "known_relatives")
            special = cls._extract_fact(page.text, "special")

            aliases = []
            if real_name and normalize_search_text(real_name) != normalized:
                aliases.append(real_name)

            relations = []
            for relative in cls._split_values(relatives):
                relations.append(Relationship("relative", relative))

            entity = Entity(
                name=heading.title() if heading.isupper() else heading,
                original_name=heading,
                aliases=aliases,
                category="character",
                universe=universe,
                publisher=publisher,
                species=species,
                occupation=cls._split_values(occupation),
                status=status,
                first_appearance=first_appearance,
                description=cls._summary(page.text, heading),
                powers=cls._split_values(special),
                relationships=relations,
                image=page.image_path,
                tags=["encyclopedia", universe.lower(), "pdf-import"],
                sources=[
                    KnowledgeSource(
                        source_type="PDF",
                        source_ref=source_file,
                        page=page.number,
                        retrieved_at=datetime.now(timezone.utc).isoformat(),
                    )
                ],
                metadata={
                    "source_page": page.number,
                    "ocr": page.used_ocr,
                    "image_kind": "page_reference" if page.image_path else None,
                },
                attributes={
                    "real_name": real_name,
                    "base": cls._extract_fact(page.text, "base"),
                },
            )
            entities.append(entity)

        # Evita multiplicar a mesma entrada por headings repetidos na página.
        unique = {}
        for entity in entities:
            unique[normalize_search_text(entity.name)] = entity
        return list(unique.values())

    def import_pdf(
        self,
        pdf_path: str | Path,
        *,
        universe: str,
        publisher: str,
        allow_ocr: bool = False,
        start_page: int = 1,
        end_page: int | None = None,
        render_images: bool = True,
    ) -> ImportStats:
        source = Path(pdf_path)
        stats = ImportStats()

        for page in self.reader.iter_pages(
            source,
            start_page=start_page,
            end_page=end_page,
            allow_ocr=allow_ocr,
            render_images=render_images,
        ):
            stats.pages_seen += 1
            if page.text.strip():
                stats.pages_with_text += 1
            if page.used_ocr:
                stats.ocr_pages += 1

            entities = self.parse_page(
                page,
                universe=universe,
                publisher=publisher,
                source_file=source.name,
            )
            stats.entities_detected += len(entities)
            for entity in entities:
                self.engine.upsert_entity(entity)
                stats.entities_saved += 1

        log.info(
            "Importação %s: %s páginas, %s entidades salvas.",
            source.name,
            stats.pages_seen,
            stats.entities_saved,
        )
        return stats
