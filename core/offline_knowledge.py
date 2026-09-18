"""Fontes e retrieval offline de conhecimento real da STAR.

Objetivos:
- registrar categorias reais de conhecimento com meta física de 1B;
- manter catálogo de fontes verificadas/razoáveis por categoria;
- consultar fatos locais antes dos matchers legados;
- usar Kiwix/ZIM localmente quando configurado, sem rede externa em runtime.
"""
from __future__ import annotations

import atexit
from dataclasses import dataclass
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

import requests


BILLION = 1_000_000_000

SOURCE_DEFINITIONS = {
    "wikidata": {
        "name": "Wikidata",
        "url": "https://www.wikidata.org/wiki/Wikidata:Database_download",
        "license": "CC0 (structured data)",
        "reliability": 0.88,
        "tier": "B",
        "role": "structured-general",
    },
    "wikipedia_kiwix": {
        "name": "Wikipedia via Kiwix ZIM",
        "url": "https://download.kiwix.org/zim/wikipedia/",
        "license": "CC BY-SA/GFDL text; see article/source terms",
        "reliability": 0.82,
        "tier": "B",
        "role": "offline-encyclopedia",
    },
    "dbpedia": {
        "name": "DBpedia Latest Core",
        "url": "https://www.dbpedia.org/resources/latest-core/",
        "license": "open DBpedia/Wikipedia-derived data; verify artifact metadata",
        "reliability": 0.84,
        "tier": "B",
        "role": "structured-encyclopedic",
    },
    "openalex": {
        "name": "OpenAlex Snapshot",
        "url": "https://help.openalex.org/access/snapshot/",
        "license": "CC0",
        "reliability": 0.90,
        "tier": "A",
        "role": "scholarly-metadata",
    },
    "crossref": {
        "name": "Crossref Public Data File",
        "url": "https://www.crossref.org/services/metadata-retrieval/public-data-file/",
        "license": "metadata broadly reusable; abstracts may have restrictions",
        "reliability": 0.92,
        "tier": "A",
        "role": "doi-metadata",
    },
    "nist_physics": {
        "name": "NIST Physical Reference Data",
        "url": "https://www.nist.gov/data",
        "license": "US government/public data; dataset-specific terms apply",
        "reliability": 0.98,
        "tier": "A",
        "role": "physical-reference",
    },
    "nist_dlmf": {
        "name": "NIST Digital Library of Mathematical Functions",
        "url": "https://dlmf.nist.gov/",
        "license": "NIST terms/citation",
        "reliability": 0.98,
        "tier": "A",
        "role": "mathematics-reference",
    },
    "nist_chemistry": {
        "name": "NIST Chemistry WebBook",
        "url": "https://webbook.nist.gov/",
        "license": "NIST Standard Reference Data terms",
        "reliability": 0.98,
        "tier": "A",
        "role": "chemistry-reference",
    },
    "pubchem": {
        "name": "PubChem",
        "url": "https://pubchem.ncbi.nlm.nih.gov/docs/downloads",
        "license": "source-specific; PubChem bulk data broadly downloadable",
        "reliability": 0.95,
        "tier": "A",
        "role": "chemical-bioactivity",
    },
    "genbank": {
        "name": "NCBI GenBank",
        "url": "https://www.ncbi.nlm.nih.gov/genbank/release/current/",
        "license": "NCBI/NLM terms; submission provenance retained",
        "reliability": 0.90,
        "tier": "A",
        "role": "sequence-data",
    },
    "pubmed": {
        "name": "PubMed Baseline",
        "url": "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/",
        "license": "NLM terms and publisher metadata conditions",
        "reliability": 0.94,
        "tier": "A",
        "role": "biomedical-literature-metadata",
    },
    "gbif": {
        "name": "GBIF",
        "url": "https://www.gbif.org/",
        "license": "per-dataset CC0/CC BY/CC BY-NC",
        "reliability": 0.88,
        "tier": "A",
        "role": "biodiversity-occurrences",
    },
    "catalogue_of_life": {
        "name": "Catalogue of Life",
        "url": "https://www.catalogueoflife.org/data/download",
        "license": "CC BY 4.0 unless otherwise indicated",
        "reliability": 0.94,
        "tier": "A",
        "role": "taxonomy",
    },
    "world_bank": {
        "name": "World Bank Indicators",
        "url": "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392",
        "license": "World Bank data terms",
        "reliability": 0.97,
        "tier": "A",
        "role": "economics-development",
    },
    "unesco_uis": {
        "name": "UNESCO Institute for Statistics",
        "url": "https://databrowser.uis.unesco.org/resources/bulk",
        "license": "UNESCO data terms",
        "reliability": 0.97,
        "tier": "A",
        "role": "education-science-culture-statistics",
    },
    "who_gho": {
        "name": "WHO Global Health Observatory",
        "url": "https://www.who.int/data/gho/info/gho-odata-api",
        "license": "WHO data terms",
        "reliability": 0.98,
        "tier": "A",
        "role": "health-statistics",
    },
    "usgs": {
        "name": "USGS Science Data Catalog",
        "url": "https://data.usgs.gov/datacatalog/",
        "license": "US government/public data; item-specific metadata",
        "reliability": 0.98,
        "tier": "A",
        "role": "earth-science",
    },
    "noaa": {
        "name": "NOAA Climate Data Online",
        "url": "https://www.ncei.noaa.gov/cdo-web/",
        "license": "US government/public data",
        "reliability": 0.98,
        "tier": "A",
        "role": "climate-weather-history",
    },
    "nasa_exoplanet": {
        "name": "NASA Exoplanet Archive",
        "url": "https://exoplanetarchive.ipac.caltech.edu/",
        "license": "NASA/IPAC data terms; citation requested",
        "reliability": 0.98,
        "tier": "A",
        "role": "astronomy-exoplanets",
    },
    "musicbrainz": {
        "name": "MusicBrainz Core",
        "url": "https://musicbrainz.org/doc/MusicBrainz_Database/Download",
        "license": "CC0 core data",
        "reliability": 0.90,
        "tier": "B",
        "role": "music-metadata",
    },
    "faostat": {
        "name": "FAOSTAT",
        "url": "https://www.fao.org/statistics/en",
        "license": "CC BY 4.0 for FAO statistical database unless otherwise stated",
        "reliability": 0.97,
        "tier": "A",
        "role": "food-agriculture-statistics",
    },
}

# Toda categoria usa a enciclopédia offline como camada ampla e fontes
# especializadas como camada de maior autoridade.
CATEGORY_SOURCES = {
    "geography": ("wikidata", "wikipedia_kiwix", "dbpedia", "usgs"),
    "history": ("wikidata", "wikipedia_kiwix", "dbpedia"),
    "physics": ("nist_physics", "wikipedia_kiwix", "openalex", "crossref"),
    "chemistry": ("pubchem", "nist_chemistry", "wikipedia_kiwix", "openalex", "crossref"),
    "biology": ("genbank", "catalogue_of_life", "gbif", "wikipedia_kiwix", "openalex"),
    "mathematics": ("nist_dlmf", "wikipedia_kiwix", "openalex", "crossref"),
    "astronomy": ("nasa_exoplanet", "wikipedia_kiwix", "openalex", "crossref"),
    "earth_science": ("usgs", "noaa", "wikipedia_kiwix", "openalex"),
    "environment": ("noaa", "usgs", "wikipedia_kiwix", "openalex"),
    "medicine": ("who_gho", "pubmed", "wikipedia_kiwix", "openalex"),
    "neuroscience": ("pubmed", "wikipedia_kiwix", "openalex", "crossref"),
    "psychology": ("wikipedia_kiwix", "openalex", "crossref"),
    "sociology": ("wikipedia_kiwix", "openalex", "crossref", "unesco_uis"),
    "philosophy": ("wikipedia_kiwix", "openalex", "crossref"),
    "economics": ("world_bank", "wikipedia_kiwix", "openalex", "crossref"),
    "law": ("wikidata", "wikipedia_kiwix", "openalex", "crossref"),
    "civics": ("wikidata", "wikipedia_kiwix", "unesco_uis"),
    "computer_science": ("wikipedia_kiwix", "openalex", "crossref"),
    "software_engineering": ("wikipedia_kiwix", "openalex", "crossref"),
    "engineering": ("wikipedia_kiwix", "openalex", "crossref", "nist_physics"),
    "mechanics": ("nist_physics", "wikipedia_kiwix", "openalex"),
    "electronics": ("nist_physics", "wikipedia_kiwix", "openalex"),
    "robotics": ("wikipedia_kiwix", "openalex", "crossref"),
    "materials": ("nist_physics", "wikipedia_kiwix", "openalex", "crossref"),
    "energy": ("nist_physics", "wikipedia_kiwix", "openalex"),
    "fauna": ("catalogue_of_life", "gbif", "genbank", "wikipedia_kiwix"),
    "flora": ("catalogue_of_life", "gbif", "genbank", "wikipedia_kiwix"),
    "linguistics": ("wikidata", "wikipedia_kiwix", "openalex", "crossref"),
    "literature": ("wikidata", "wikipedia_kiwix", "dbpedia"),
    "arts": ("wikidata", "wikipedia_kiwix", "dbpedia"),
    "music": ("musicbrainz", "wikidata", "wikipedia_kiwix"),
    "culture": ("unesco_uis", "wikidata", "wikipedia_kiwix", "dbpedia"),
    "agriculture": ("faostat", "wikipedia_kiwix", "openalex"),
    "food_nutrition": ("faostat", "who_gho", "wikipedia_kiwix", "openalex"),
}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "svg", "noscript"}:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "svg", "noscript"} and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            value = " ".join(str(data or "").split())
            if value:
                self.parts.append(value)

    def text(self) -> str:
        return " ".join(self.parts)


class _ContentLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        values = dict(attrs)
        href = str(values.get("href") or "")
        if href.startswith("/content/"):
            self.links.append(href)


class KiwixOfflineEncyclopedia:
    """Busca Wikipedia/afins em ZIM local, isolada em 127.0.0.1."""

    def __init__(self, zim_dir: str | Path | None = None):
        self.zim_dir = Path(
            zim_dir or os.getenv("STAR_KIWIX_DIR") or Path("runtime") / "knowledge" / "zim"
        ).expanduser().resolve()
        configured = str(os.getenv("STAR_KIWIX_SERVE") or "").strip()
        self.executable = shutil.which(configured) if configured else shutil.which("kiwix-serve")
        self.port = int(os.getenv("STAR_KIWIX_PORT", "8767"))
        self._process: subprocess.Popen | None = None
        self._base = f"http://127.0.0.1:{self.port}"
        atexit.register(self.stop)

    @property
    def zim_files(self) -> list[Path]:
        if not self.zim_dir.is_dir():
            return []
        return sorted(self.zim_dir.glob("*.zim"))

    @property
    def available(self) -> bool:
        return bool(self.executable and self.zim_files)

    def _healthy(self) -> bool:
        try:
            response = requests.get(self._base + "/catalog/v2/entries?count=1", timeout=0.6)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def start(self) -> bool:
        if self._healthy():
            return True
        if not self.available:
            return False
        command = [
            str(self.executable),
            "-i", "127.0.0.1",
            "-p", str(self.port),
            "-b",
            str(self.zim_dir),
        ]
        try:
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except OSError:
            self._process = None
            return False
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if self._healthy():
                return True
            if self._process.poll() is not None:
                break
            time.sleep(0.1)
        self.stop()
        return False

    def stop(self):
        process = self._process
        self._process = None
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()

    def search(self, query: str, *, limit: int = 3) -> list[dict]:
        query = " ".join(str(query or "").split())
        if not query or not self.start():
            return []
        try:
            response = requests.get(
                self._base + "/search",
                params={
                    "books.filter.lang": "por",
                    "pattern": query,
                    "pageLength": max(1, min(int(limit), 10)),
                    "format": "html",
                },
                timeout=4,
            )
            response.raise_for_status()
        except requests.RequestException:
            return []
        parser = _ContentLinkParser()
        parser.feed(response.text)
        results = []
        seen = set()
        for href in parser.links:
            if href in seen:
                continue
            seen.add(href)
            try:
                article = requests.get(self._base + href, timeout=4)
                article.raise_for_status()
            except requests.RequestException:
                continue
            extractor = _TextExtractor()
            extractor.feed(article.text)
            text_value = extractor.text()
            if len(text_value) < 80:
                continue
            results.append({
                "content": text_value[:4000],
                "source": "kiwix-local:" + href,
                "source_type": "offline_encyclopedia",
                "confidence": 0.82,
                "local_only": True,
            })
            if len(results) >= limit:
                break
        return results

    def stats(self) -> dict:
        return {
            "available": self.available,
            "kiwix_serve": self.executable,
            "zim_dir": str(self.zim_dir),
            "zim_files": len(self.zim_files),
            "runtime_network": "loopback-only",
        }


class OfflineKnowledgeService:
    """Retrieval factual local + enciclopédia ZIM antes dos matchers legados."""

    def __init__(self, store, *, real_materializer=None, seed_path: str | Path | None = None):
        self.store = store
        self.real_materializer = real_materializer
        self.kiwix = KiwixOfflineEncyclopedia()
        root = Path(__file__).resolve().parents[1]
        self.seed_path = Path(seed_path or root / "knowledge" / "offline_core_facts.jsonl")
        self.ensure_categories()
        self.seed_builtin_once()

    def ensure_categories(self):
        if self.real_materializer is not None and hasattr(self.real_materializer, "ensure_namespaces"):
            self.real_materializer.ensure_namespaces(CATEGORY_SOURCES)

    def seed_builtin_once(self) -> dict:
        marker = self.store.memory_by_key("offline-core-facts-v1", kind="system")
        if marker:
            return {"seeded": False, "reason": "already_seeded"}
        if not self.seed_path.is_file():
            return {"seeded": False, "reason": "seed_missing"}
        grouped = {}
        with self.seed_path.open("r", encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                theme = str(item.pop("theme")).strip()
                grouped.setdefault(theme, []).append(item)
        accepted = 0
        for theme, records in grouped.items():
            result = self.store.ingest_facts(theme, records, target_count=BILLION)
            accepted += int(result["accepted"])
        self.store.remember(
            "system",
            f"offline core seed v1: {accepted} facts",
            key="offline-core-facts-v1",
            metadata={"source": str(self.seed_path), "accepted": accepted},
            importance=0.2,
        )
        return {"seeded": True, "accepted": accepted}

    def search(self, query: str, *, limit: int = 5) -> list[dict]:
        facts = self.store.search_facts(query, limit=limit)
        strong = [x for x in facts if float(x.get("confidence", 0)) >= 0.72 and float(x.get("query_overlap", 0)) >= 0.45]
        if strong:
            return strong[:limit]
        return self.kiwix.search(query, limit=min(limit, 3))

    def answer(self, query: str) -> str | None:
        hits = self.search(query, limit=4)
        if not hits:
            return None
        first = hits[0]
        if first.get("source_type") == "offline_encyclopedia":
            text_value = str(first.get("content") or "")
            # Evita despejar uma página inteira. O NaturalInteraction pode
            # reescrever a resposta depois sem inventar fatos novos.
            sentences = re.split(r"(?<=[.!?])\s+", text_value)
            summary = " ".join(sentences[:4]).strip()
            return summary[:1800] if summary else None

        high = [x for x in hits if float(x.get("query_overlap", 0)) >= 0.60]
        chosen = high[:3] or hits[:1]
        contents = []
        seen = set()
        for item in chosen:
            value = " ".join(str(item.get("content") or "").split())
            if value and value not in seen:
                contents.append(value)
                seen.add(value)
        return " ".join(contents) if contents else None

    def source_catalog(self) -> dict:
        return {
            "target_per_category": BILLION,
            "categories": {
                category: {
                    "target_count": BILLION,
                    "sources": [
                        {"id": source_id, **SOURCE_DEFINITIONS[source_id]}
                        for source_id in source_ids
                    ],
                }
                for category, source_ids in CATEGORY_SOURCES.items()
            },
        }

    def stats(self) -> dict:
        status = self.real_materializer.status() if self.real_materializer is not None else {}
        return {
            "categories": len(CATEGORY_SOURCES),
            "category_keys": list(CATEGORY_SOURCES),
            "target_per_category": BILLION,
            "real_materialization": status,
            "kiwix": self.kiwix.stats(),
            "offline_fact_retrieval": True,
            "source_catalog": True,
            "logical_variations_count_as_real": False,
        }
