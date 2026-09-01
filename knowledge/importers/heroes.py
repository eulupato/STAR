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
    "real_name": r"(?:REAL NAME|Real name)\s*[:\-]?\s*([^\n|]{2,100})",
    "occupation": r"(?:OCCUPATION|Occupation)\s*[:\-]?\s*([^\n|]{2,140})",
    "base": r"(?:BASE OF OPERATIONS|BASE|Base)\s*[:\-]?\s*([^\n|]{2,140})",
    "first_appearance": r"(?:FIRST APPEARANCE|First appearance)\s*[:\-]?\s*([^\n]{2,180})",
    "species": r"(?:SPECIES|Species)\s*[:\-]?\s*([^\n|]{2,100})",
    "gender": r"(?:GENDER|Gender)\s*[:\-]?\s*([^\n|]{2,60})",
    "status": r"(?:STATUS|Status)\s*[:\-]?\s*([^\n|]{2,80})",
    "origin": r"(?:ORIGIN|Origin)\s*[:\-]?\s*([^\n|]{2,160})",
    "place_of_origin": r"(?:PLACE OF ORIGIN|Place of Origin)\s*[:\-]?\s*([^\n|]{2,160})",
    "known_relatives": r"(?:KNOWN RELATIVES|Known relatives)\s*[:\-]?\s*([^\n]{2,240})",
    "group_affiliation": r"(?:GROUP AFFILIATION|AFFILIATIONS|TEAM|Teams)\s*[:\-]?\s*([^\n]{2,240})",
    "special": r"(?:SPECIAL POWERS/ABILITIES|SPECIAL POWERS|POWERS/ABILITIES|POWERS|Special powers/abilities)\s*[:\-]?\s*([^\n]{2,300})",
}

GENERIC_HEADINGS = {
    "CONTENTS", "FOREWORD", "INTRODUCTION", "CONTRIBUTORS", "INDEX",
    "ACKNOWLEDGMENTS", "ACKNOWLEDGEMENTS", "AMAZING VEHICLES",
    "AMAZING WEAPONS", "ALIEN RACES", "GREAT TEAM-UPS",
    "ROMANTIC MOMENTS", "GREAT BATTLES", "STRANGE TIMES AND PLACES",
    "CHARACTER FACTS", "FACTFILE", "BIOGRAPHY", "HISTORY", "PERSONALITY",
}


@dataclass
class ImportStats:
    pages_seen: int = 0
    pages_with_text: int = 0
    entities_detected: int = 0
    entities_saved: int = 0
    entities_rejected: int = 0
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
        result = []
        seen = set()
        for item in parts:
            cleaned = item.strip(" .")
            key = normalize_search_text(cleaned)
            if cleaned and key and key not in seen:
                seen.add(key)
                result.append(cleaned)
        return result

    @staticmethod
    def _clean_heading(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" :.-\t")

    @classmethod
    def _heading_entries(cls, text: str) -> list[tuple[int, str]]:
        entries = []
        lines = text.splitlines()
        generic = {normalize_search_text(item) for item in GENERIC_HEADINGS}

        for index, raw in enumerate(lines):
            line = cls._clean_heading(raw)
            if not line or len(line) < 2 or len(line) > 70:
                continue
            normalized = normalize_search_text(line)
            if normalized in generic:
                continue
            if re.search(
                r"\b(?:FIRST APPEARANCE|REAL NAME|OCCUPATION|BASE|POWERS|ABILITIES|HEIGHT|WEIGHT|EYES|HAIR)\b",
                line,
                re.I,
            ):
                continue

            letters = [ch for ch in line if ch.isalpha()]
            if len(letters) < 2:
                continue
            uppercase_ratio = sum(ch.isupper() for ch in letters) / len(letters)
            titleish = uppercase_ratio >= 0.72 or line.istitle()
            if not titleish:
                continue

            # Headings muito longos/fraseados tendem a ser subtítulos editoriais.
            if len(line.split()) > 8:
                continue
            entries.append((index, line))

        return entries

    @classmethod
    def _heading_candidates(cls, text: str) -> list[str]:
        return [name for _index, name in cls._heading_entries(text)]

    @staticmethod
    def _extract_fact(text: str, key: str) -> str | None:
        match = re.search(FACT_PATTERNS[key], text, re.IGNORECASE)
        if not match:
            return None
        value = re.sub(r"\s+", " ", match.group(1)).strip(" .:-")
        return value or None

    @staticmethod
    def _summary(text: str, heading: str) -> str | None:
        cleaned = re.sub(re.escape(heading), " ", text, count=1, flags=re.I)
        cleaned = re.sub(
            r"(?is)(FACTFILE|CHARACTER FACTS|FIRST APPEARANCE|REAL NAME|OCCUPATION|BASE|HEIGHT|WEIGHT|EYES|HAIR|POWERS).*",
            "",
            cleaned,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) < 45:
            return None
        return cleaned[:900].rstrip()

    @classmethod
    def _build_entity(
        cls,
        segment: str,
        heading: str,
        page: PdfPage,
        *,
        universe: str,
        publisher: str,
        source_file: str,
    ) -> tuple[Entity | None, float]:
        normalized = normalize_search_text(heading)
        if normalized in {normalize_search_text(item) for item in GENERIC_HEADINGS}:
            return None, 0.0

        facts = {key: cls._extract_fact(segment, key) for key in FACT_PATTERNS}
        summary = cls._summary(segment, heading)
        signal_count = sum(bool(value) for value in facts.values())
        confidence = 0.28 + min(signal_count, 5) * 0.11 + (0.17 if summary else 0.0)

        # Sem qualquer ficha, exigimos um resumo substancial para evitar que
        # títulos editoriais virem personagens.
        if signal_count == 0 and (not summary or len(summary) < 100):
            return None, confidence
        if confidence < 0.45:
            return None, confidence

        real_name = facts["real_name"]
        aliases = []
        if real_name and normalize_search_text(real_name) != normalized:
            aliases.append(real_name)

        relatives = cls._split_values(facts["known_relatives"])
        relations = [Relationship("relative", value) for value in relatives]

        teams = cls._split_values(facts["group_affiliation"])
        relations.extend(Relationship("team", value) for value in teams)

        origin_place = facts["place_of_origin"] or facts["base"]
        entity = Entity(
            name=heading.title() if heading.isupper() else heading,
            original_name=heading,
            aliases=aliases,
            category="character",
            universe=universe,
            publisher=publisher,
            team=teams,
            species=facts["species"],
            gender=facts["gender"],
            origin=facts["origin"],
            origin_place=origin_place,
            occupation=cls._split_values(facts["occupation"]),
            status=facts["status"],
            first_appearance=facts["first_appearance"],
            description=summary,
            powers=cls._split_values(facts["special"]),
            relationships=relations,
            image=page.portrait_path,
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
                "import_confidence": round(min(confidence, 1.0), 3),
                "image_kind": "pdf_embedded_candidate" if page.portrait_path else None,
                "page_reference": page.image_path,
                "image_candidates": list(page.image_candidates),
            },
            attributes={
                "real_name": real_name,
                "base": facts["base"],
            },
        )
        return entity, confidence

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

        lines = page.text.splitlines()
        entries = cls._heading_entries(page.text)
        if not entries:
            return []

        entities = []
        for position, (line_index, heading) in enumerate(entries):
            next_index = (
                entries[position + 1][0]
                if position + 1 < len(entries)
                else len(lines)
            )
            segment = "\n".join(lines[line_index:next_index]).strip()
            entity, _confidence = cls._build_entity(
                segment,
                heading,
                page,
                universe=universe,
                publisher=publisher,
                source_file=source_file,
            )
            if entity is not None:
                entities.append(entity)

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

            candidates = self._heading_entries(page.text)
            entities = self.parse_page(
                page,
                universe=universe,
                publisher=publisher,
                source_file=source.name,
            )
            stats.entities_detected += len(candidates)
            stats.entities_rejected += max(0, len(candidates) - len(entities))
            for entity in entities:
                self.engine.upsert_entity(entity)
                stats.entities_saved += 1

        log.info(
            "Importação %s: %s páginas, %s entidades salvas, %s candidatos rejeitados.",
            source.name,
            stats.pages_seen,
            stats.entities_saved,
            stats.entities_rejected,
        )
        return stats
