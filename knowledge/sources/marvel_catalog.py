"""Descoberta em lote do catálogo oficial Marvel.

O catálogo é importado somente quando o usuário executa explicitamente o
builder com acesso online. A STAR continua totalmente funcional offline depois
que o cache/banco local foi criado.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import re
from urllib.parse import parse_qs, urljoin, urlparse

from core.logging_config import get_logger
from knowledge.entities import Entity, KnowledgeSource
from knowledge.store import normalize_search_text
from knowledge.sources.official import OfficialWebClient

log = get_logger("knowledge.marvel_catalog")

MARVEL_CATALOG_URL = "https://www.marvel.com/characters?target=Agent_X"
MARVEL_LEGACY_INDEX_URL = "https://www.marvel.com/comics/characters?l=sem&o=603409"


class _CatalogParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        self._href = dict(attrs).get("href")
        self._text = []

    def handle_data(self, data):
        if self._href is not None:
            value = re.sub(r"\s+", " ", str(data or "")).strip()
            if value:
                self._text.append(value)

    def handle_endtag(self, tag):
        if tag.lower() != "a" or self._href is None:
            return
        text = re.sub(r"\s+", " ", " ".join(self._text)).strip()
        self.links.append((self._href, text))
        self._href = None
        self._text = []


@dataclass(frozen=True)
class MarvelCatalogEntry:
    name: str
    profile_url: str
    real_name: str | None = None
    aliases: tuple[str, ...] = ()

    @property
    def identity_key(self) -> str:
        return normalize_search_text(
            " | ".join(filter(None, [self.name, self.real_name, self.profile_url]))
        )


def _clean_label(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" \t\r\n-")


def _split_identity(label: str) -> tuple[str, str | None, list[str]]:
    """Preserva variantes oficiais sem fundir identidades diferentes."""
    label = _clean_label(label)
    match = re.match(r"^(.*?)\s*\(([^()]{2,100})\)\s*$", label)
    if not match:
        return label, None, []

    base = _clean_label(match.group(1))
    identity = _clean_label(match.group(2))
    if not base or not identity:
        return label, None, []

    display = f"{base} ({identity})"
    aliases = [base, identity]
    return display, identity, aliases


def _is_profile_path(path: str) -> bool:
    normalized = path.rstrip("/")
    if normalized.startswith("/characters/") and normalized != "/characters":
        return True
    if re.match(r"^/comics/characters/\d+/[^/]+$", normalized, re.I):
        return True
    return False


def _is_catalog_page(url: str) -> bool:
    parsed = urlparse(url)
    if (parsed.hostname or "").lower() not in {"marvel.com", "www.marvel.com"}:
        return False
    path = parsed.path.rstrip("/")
    if path != "/characters":
        return False
    query = parse_qs(parsed.query)
    paging_keys = {"page", "p", "offset", "start", "target"}
    return bool(paging_keys & set(query))


def parse_catalog_html(html: str, source_url: str) -> tuple[list[MarvelCatalogEntry], list[str]]:
    parser = _CatalogParser()
    parser.feed(html)

    entries: list[MarvelCatalogEntry] = []
    pages: list[str] = []
    seen_entries = set()
    seen_pages = set()

    for href, text in parser.links:
        absolute = urljoin(source_url, href)
        parsed = urlparse(absolute)
        if (parsed.hostname or "").lower() not in {"marvel.com", "www.marvel.com"}:
            continue

        if _is_catalog_page(absolute):
            if absolute not in seen_pages:
                seen_pages.add(absolute)
                pages.append(absolute)
            continue

        if not _is_profile_path(parsed.path):
            continue

        label = _clean_label(text)
        if not label:
            slug = parsed.path.rstrip("/").split("/")[-1]
            label = slug.replace("-", " ").title()
        if not label:
            continue

        name, real_name, aliases = _split_identity(label)
        key = normalize_search_text(absolute)
        if not key or key in seen_entries:
            continue
        seen_entries.add(key)
        entries.append(
            MarvelCatalogEntry(
                name=name,
                profile_url=absolute,
                real_name=real_name,
                aliases=tuple(aliases),
            )
        )

    return entries, pages


class MarvelOfficialCatalog:
    """Importa todos os links de personagens que a Marvel expõe no índice."""

    def __init__(self, client: OfficialWebClient):
        self.client = client

    def discover(
        self,
        *,
        online: bool = True,
        force: bool = False,
        max_pages: int = 120,
    ) -> list[MarvelCatalogEntry]:
        queue = [MARVEL_LEGACY_INDEX_URL, MARVEL_CATALOG_URL]
        visited = set()
        collected: dict[str, MarvelCatalogEntry] = {}

        while queue and len(visited) < max(1, int(max_pages)):
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            html = self.client.fetch_html(url, online=online, force=force)
            if not html:
                continue

            entries, pages = parse_catalog_html(html, url)
            for entry in entries:
                collected.setdefault(entry.identity_key, entry)

            for page in pages:
                if page not in visited and page not in queue:
                    queue.append(page)

        log.info(
            "Catálogo Marvel oficial: %s entradas descobertas em %s páginas.",
            len(collected),
            len(visited),
        )
        return sorted(collected.values(), key=lambda item: item.name.lower())

    def import_into(
        self,
        engine,
        *,
        online: bool = True,
        force: bool = False,
        max_pages: int = 120,
    ) -> int:
        entries = self.discover(
            online=online,
            force=force,
            max_pages=max_pages,
        )
        retrieved = datetime.now(timezone.utc).isoformat()
        saved = 0

        for entry in entries:
            existing = engine.resolve_entity(entry.name, universe="Marvel")
            if existing is None and entry.aliases:
                for alias in entry.aliases:
                    existing = engine.resolve_entity(alias, universe="Marvel")
                    if existing is not None:
                        break

            if existing is None:
                entity = Entity(
                    name=entry.name,
                    category="character",
                    aliases=list(entry.aliases),
                    universe="Marvel",
                    publisher="Marvel Comics",
                    tags=["marvel", "official-catalog"],
                    attributes={
                        "real_name": entry.real_name,
                    },
                    metadata={
                        "official_profile_url": entry.profile_url,
                        "catalog_seed": True,
                    },
                    sources=[
                        KnowledgeSource(
                            source_type="official_catalog",
                            source_ref="Marvel Characters",
                            url=entry.profile_url,
                            retrieved_at=retrieved,
                        )
                    ],
                )
            else:
                entity = existing
                entity.aliases = _merge_values(entity.aliases, entry.aliases)
                if entry.real_name and not entity.attributes.get("real_name"):
                    entity.attributes["real_name"] = entry.real_name
                entity.metadata["official_profile_url"] = entry.profile_url
                entity.metadata["catalog_seed"] = entity.metadata.get(
                    "catalog_seed", False
                )
                entity.tags = _merge_values(
                    entity.tags,
                    ["marvel", "official-catalog"],
                )
                if not any(source.url == entry.profile_url for source in entity.sources):
                    entity.sources.append(
                        KnowledgeSource(
                            source_type="official_catalog",
                            source_ref="Marvel Characters",
                            url=entry.profile_url,
                            retrieved_at=retrieved,
                        )
                    )

            engine.upsert_entity(entity)
            saved += 1

        return saved


def _merge_values(current, incoming) -> list[str]:
    result = list(current or [])
    seen = {normalize_search_text(item) for item in result}
    for item in incoming or []:
        value = _clean_label(item)
        key = normalize_search_text(value)
        if value and key and key not in seen:
            seen.add(key)
            result.append(value)
    return result
