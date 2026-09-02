"""Fontes oficiais DC/Marvel para enriquecimento opcional.

Nada deste módulo é necessário para a STAR funcionar offline. A rede é usada
somente quando o usuário executa explicitamente o enriquecimento.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from core.logging_config import get_logger
from knowledge.entities import Entity, KnowledgeSource, Relationship
from knowledge.store import normalize_search_text

log = get_logger("knowledge.official")


ALLOWED_PAGE_HOSTS = {
    "dc.com",
    "www.dc.com",
    "marvel.com",
    "www.marvel.com",
}

ALLOWED_IMAGE_HOST_SUFFIXES = (
    "dc.com",
    "marvel.com",
    "marvelcdn.com",
    "annihil.us",
)


def _slugify(value: str) -> str:
    text = normalize_search_text(value).replace(" ", "-")
    return re.sub(r"-+", "-", text).strip("-")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", unescape(str(value))).strip(" \t\r\n:-")
    return text or None


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[,;]|\s+•\s+", value)
    result = []
    seen = set()
    for item in parts:
        cleaned = _clean(item)
        if not cleaned:
            continue
        key = normalize_search_text(cleaned)
        if key and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


class _ProfileParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.links: list[dict] = []
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []
        self._heading_level: str | None = None
        self._heading_text: list[str] = []
        self.current_section: str = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        tag = tag.lower()
        if tag == "meta":
            key = attrs.get("property") or attrs.get("name")
            content = attrs.get("content")
            if key and content:
                self.meta[key.lower()] = content
        elif tag == "a":
            self._anchor_href = attrs.get("href")
            self._anchor_text = []
        elif tag in {"h1", "h2", "h3", "h4"}:
            self._heading_level = tag
            self._heading_text = []

    def handle_data(self, data):
        text = _clean(data)
        if not text:
            return
        self.text_parts.append(text)
        if self._anchor_href is not None:
            self._anchor_text.append(text)
        if self._heading_level is not None:
            self._heading_text.append(text)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "a" and self._anchor_href is not None:
            self.links.append(
                {
                    "href": self._anchor_href,
                    "text": _clean(" ".join(self._anchor_text)) or "",
                    "section": self.current_section,
                }
            )
            self._anchor_href = None
            self._anchor_text = []
        elif self._heading_level == tag:
            heading = _clean(" ".join(self._heading_text))
            if heading:
                self.current_section = heading
            self._heading_level = None
            self._heading_text = []

    @property
    def text(self) -> str:
        return "\n".join(self.text_parts)


@dataclass
class OfficialProfile:
    name: str
    universe: str
    publisher: str
    source_url: str
    description: str | None = None
    aliases: list[str] = field(default_factory=list)
    powers: list[str] = field(default_factory=list)
    occupation: list[str] = field(default_factory=list)
    affiliations: list[str] = field(default_factory=list)
    origin_place: str | None = None
    first_appearance: str | None = None
    gender: str | None = None
    image_url: str | None = None
    relationships: list[Relationship] = field(default_factory=list)
    attributes: dict = field(default_factory=dict)


class OfficialWebClient:
    def __init__(
        self,
        cache_dir: str | Path,
        *,
        timeout: float = 12.0,
        cache_ttl_hours: int = 168,
    ):
        self.cache_dir = Path(cache_dir)
        self.html_cache = self.cache_dir / "html"
        self.image_cache = self.cache_dir / "images"
        self.html_cache.mkdir(parents=True, exist_ok=True)
        self.image_cache.mkdir(parents=True, exist_ok=True)
        self.timeout = float(timeout)
        self.cache_ttl_seconds = max(0, int(cache_ttl_hours)) * 3600

    @staticmethod
    def _validate_page_url(url: str) -> str:
        parsed = urlparse(str(url))
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in ALLOWED_PAGE_HOSTS:
            raise ValueError(f"Fonte web não autorizada: {url}")
        return url

    @staticmethod
    def _cache_key(url: str) -> str:
        return sha256(url.encode("utf-8")).hexdigest()

    def fetch_html(self, url: str, *, online: bool = True, force: bool = False) -> str | None:
        url = self._validate_page_url(url)
        cache_path = self.html_cache / f"{self._cache_key(url)}.html"
        if cache_path.exists() and not force:
            age = time.time() - cache_path.stat().st_mtime
            if not online or age <= self.cache_ttl_seconds:
                return cache_path.read_text(encoding="utf-8", errors="replace")
        if not online:
            return None

        request = Request(
            url,
            headers={
                "User-Agent": "STAR-Knowledge/3.0 (+local personal knowledge index)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                html = response.read().decode(charset, errors="replace")
        except HTTPError as exc:
            log.info("Fonte oficial recusou %s: HTTP %s", url, exc.code)
            return None
        except (URLError, TimeoutError, OSError) as exc:
            log.warning("Fonte oficial indisponível %s: %s", url, exc)
            return None

        cache_path.write_text(html, encoding="utf-8")
        return html

    def cache_image(self, url: str | None, *, online: bool = True) -> str | None:
        if not url:
            return None
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not any(
            host == suffix or host.endswith("." + suffix)
            for suffix in ALLOWED_IMAGE_HOST_SUFFIXES
        ):
            return None

        suffix = Path(parsed.path).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            suffix = ".jpg"
        path = self.image_cache / f"{self._cache_key(url)}{suffix}"
        if path.exists() and path.stat().st_size > 0:
            return str(path)
        if not online:
            return None

        request = Request(
            url,
            headers={"User-Agent": "STAR-Knowledge/3.0"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content_type = (response.headers.get("Content-Type") or "").lower()
                if not content_type.startswith("image/"):
                    return None
                data = response.read(12 * 1024 * 1024 + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            log.warning("Imagem oficial indisponível %s: %s", url, exc)
            return None

        if not data or len(data) > 12 * 1024 * 1024:
            return None
        path.write_bytes(data)
        return str(path)


class OfficialCharacterSource:
    universe = ""
    publisher = ""

    def __init__(self, client: OfficialWebClient):
        self.client = client

    def candidate_urls(self, entity: Entity) -> list[str]:
        raise NotImplementedError

    def parse(self, html: str, url: str) -> OfficialProfile | None:
        raise NotImplementedError

    def fetch_profile(
        self,
        entity: Entity,
        *,
        online: bool = True,
        force: bool = False,
    ) -> OfficialProfile | None:
        for url in self.candidate_urls(entity):
            html = self.client.fetch_html(url, online=online, force=force)
            if not html:
                continue
            profile = self.parse(html, url)
            if profile and self.profile_matches_entity(entity, profile):
                return profile
            if profile:
                log.warning(
                    "Perfil oficial rejeitado por identidade: entidade=%s perfil=%s url=%s",
                    entity.name,
                    profile.name,
                    url,
                )
        return None

    @staticmethod
    def profile_matches_entity(entity: Entity, profile: OfficialProfile) -> bool:
        def norm(value):
            return normalize_search_text(value or "")

        expected = {
            norm(entity.name),
            norm(entity.original_name),
            *(norm(value) for value in entity.aliases),
        }
        expected.discard("")

        actual = {
            norm(profile.name),
            *(norm(value) for value in profile.aliases),
        }
        actual.discard("")

        profile_base = norm(re.sub(r"\([^)]*\)", " ", profile.name or ""))
        if profile_base:
            actual.add(profile_base)

        name_match = bool(expected & actual)
        if not name_match:
            for left in expected:
                for right in actual:
                    left_tokens = set(left.split())
                    right_tokens = set(right.split())
                    same_tokens = (
                        len(left_tokens) >= 2
                        and left_tokens == right_tokens
                    )
                    contained = (
                        len(left) >= 4
                        and (
                            f" {left} " in f" {right} "
                            or f" {right} " in f" {left} "
                        )
                    )
                    if same_tokens or contained:
                        name_match = True
                        break
                if name_match:
                    break

        if not name_match:
            return False

        real_name = norm(
            entity.attributes.get("real_name")
            if entity.attributes
            else None
        )
        if real_name:
            identity_haystack = " ".join(sorted(actual))
            if f" {real_name} " not in f" {identity_haystack} ":
                return False

        return True

    @staticmethod
    def _meta_description(parser: _ProfileParser) -> str | None:
        return _clean(
            parser.meta.get("og:description")
            or parser.meta.get("description")
            or parser.meta.get("twitter:description")
        )

    @staticmethod
    def _meta_image(parser: _ProfileParser) -> str | None:
        return _clean(
            parser.meta.get("og:image")
            or parser.meta.get("twitter:image")
            or parser.meta.get("twitter:image:src")
        )


class DCOfficialSource(OfficialCharacterSource):
    universe = "DC"
    publisher = "DC Comics"
    base = "https://www.dc.com/characters/"

    def candidate_urls(self, entity: Entity) -> list[str]:
        names = [entity.name, entity.original_name, *entity.aliases]
        urls = []
        for name in names:
            if not name:
                continue
            url = self.base + _slugify(name)
            if url not in urls:
                urls.append(url)
        return urls

    FIELD_LABELS = {
        "powers": "powers",
        "first appearance": "first_appearance",
        "alias alter ego": "alter_ego",
        "aka": "aka",
        "base of operations": "base",
        "occupation": "occupation",
    }

    @classmethod
    def _labeled_fields(cls, text: str) -> dict[str, str]:
        """Extrai pares rótulo/valor sem depender do layout HTML exato."""
        lines = []
        for raw in str(text or "").splitlines():
            value = _clean(raw)
            if value:
                lines.append(value)

        fields: dict[str, str] = {}
        index = 0
        while index < len(lines):
            normalized = normalize_search_text(lines[index].rstrip(":"))
            key = cls.FIELD_LABELS.get(normalized)
            if key is None:
                index += 1
                continue

            values = []
            cursor = index + 1
            while cursor < len(lines):
                next_normalized = normalize_search_text(lines[cursor].rstrip(":"))
                if next_normalized in cls.FIELD_LABELS:
                    break
                if next_normalized == "related characters":
                    break
                values.append(lines[cursor])
                cursor += 1

            value = _clean(" ".join(values))
            if value:
                fields[key] = value
            index = max(cursor, index + 1)

        return fields

    def parse(self, html: str, url: str) -> OfficialProfile | None:
        parser = _ProfileParser()
        parser.feed(html)
        text = parser.text

        title = (
            parser.meta.get("og:title")
            or parser.meta.get("twitter:title")
            or ""
        )
        title = re.sub(r"\s*\|.*$", "", title).strip()
        if not title:
            match = re.search(r"\n([^\n]{2,80})\nOFFICIAL CHARACTER PROFILE", text, re.I)
            title = match.group(1).strip() if match else ""
        if not title:
            return None

        fields = self._labeled_fields(text)
        powers = _split_csv(fields.get("powers"))
        first = fields.get("first_appearance")
        alter = fields.get("alter_ego")
        aka = fields.get("aka")
        base = fields.get("base")
        occupation = fields.get("occupation")

        aliases = []
        for value in (alter, aka):
            aliases.extend(_split_csv(value))

        related = []
        seen = set()
        for link in parser.links:
            href = link.get("href") or ""
            name = _clean(link.get("text"))
            section = normalize_search_text(link.get("section") or "")
            if (
                name
                and "/characters/" in href
                and "related characters" in section
                and normalize_search_text(name) != normalize_search_text(title)
            ):
                key = normalize_search_text(name)
                if key not in seen:
                    seen.add(key)
                    related.append(
                        Relationship(
                            "related",
                            name,
                            metadata={"source": "dc.com"},
                        )
                    )

        return OfficialProfile(
            name=title,
            universe=self.universe,
            publisher=self.publisher,
            source_url=url,
            description=self._meta_description(parser),
            aliases=aliases,
            powers=powers,
            occupation=_split_csv(occupation),
            origin_place=base,
            first_appearance=first,
            image_url=self._meta_image(parser),
            relationships=related,
        )


class MarvelOfficialSource(OfficialCharacterSource):
    universe = "Marvel"
    publisher = "Marvel Comics"
    base = "https://www.marvel.com/characters/"

    def candidate_urls(self, entity: Entity) -> list[str]:
        urls = []
        discovered = (entity.metadata or {}).get("official_profile_url")
        if discovered:
            try:
                validated = self.client._validate_page_url(str(discovered))
                if urlparse(validated).path.startswith("/characters/"):
                    urls.append(validated)
            except ValueError:
                pass

        names = [entity.name, entity.original_name, *entity.aliases]
        real_name = _clean(entity.attributes.get("real_name")) if entity.attributes else None
        candidates = []
        for name in names:
            if not name:
                continue
            if real_name and normalize_search_text(real_name) not in normalize_search_text(name):
                candidates.append(_slugify(f"{name} {real_name}"))
            candidates.append(_slugify(name))

        for slug in candidates:
            if not slug:
                continue
            for suffix in ("", "/in-comics"):
                url = self.base + slug + suffix
                if url not in urls:
                    urls.append(url)
        return urls

    @staticmethod
    def _section(text: str, label: str, next_labels: tuple[str, ...]) -> str | None:
        match = re.search(rf"(?:^|\n){re.escape(label)}\s*(?:\n|$)", text, re.I)
        if not match:
            return None
        tail = text[match.end():]
        stop = len(tail)
        for next_label in next_labels:
            nxt = re.search(rf"(?:^|\n){re.escape(next_label)}\s*(?:\n|$)", tail, re.I)
            if nxt:
                stop = min(stop, nxt.start())
        return _clean(tail[:stop])

    def parse(self, html: str, url: str) -> OfficialProfile | None:
        parser = _ProfileParser()
        parser.feed(html)
        text = parser.text

        title = parser.meta.get("og:title") or parser.meta.get("twitter:title") or ""
        title = re.sub(r"\s*\|.*$", "", title).strip()
        if not title:
            h = re.search(r"^([^\n]{2,100})$", text, re.MULTILINE)
            title = h.group(1).strip() if h else ""
        if not title:
            return None

        aliases = _split_csv(
            self._section(
                text,
                "Other Aliases",
                ("Education", "Place of Origin", "Identity", "Known Relatives", "Powers", "Group Affiliation"),
            )
        )
        powers = _split_csv(
            self._section(
                text,
                "Powers",
                ("Group Affiliation", "Connections", "Essential Reading"),
            )
        )
        affiliations = _split_csv(
            self._section(
                text,
                "Group Affiliation",
                ("Connections", "Essential Reading", "Latest"),
            )
        )
        origin_place = self._section(
            text,
            "Place of Origin",
            ("Identity", "Known Relatives", "Powers", "Group Affiliation"),
        )
        gender = self._section(
            text,
            "GENDER",
            ("EYES", "HAIR", "Universe", "Other Aliases"),
        )

        related = []
        seen = set()
        for link in parser.links:
            href = link.get("href") or ""
            name = _clean(link.get("text"))
            if name and "/characters/" in href:
                key = normalize_search_text(name)
                if key and key != normalize_search_text(title) and key not in seen:
                    seen.add(key)
                    related.append(
                        Relationship(
                            "related",
                            name,
                            metadata={"source": "marvel.com"},
                        )
                    )

        return OfficialProfile(
            name=title,
            universe=self.universe,
            publisher=self.publisher,
            source_url=url,
            description=self._meta_description(parser),
            aliases=aliases,
            powers=powers,
            affiliations=affiliations,
            origin_place=origin_place,
            gender=gender,
            image_url=self._meta_image(parser),
            relationships=related[:100],
        )


def source_for_entity(entity: Entity, client: OfficialWebClient) -> OfficialCharacterSource | None:
    universe = normalize_search_text(entity.universe or "")
    publisher = normalize_search_text(entity.publisher or "")
    if "dc" == universe or "dc comics" in publisher:
        return DCOfficialSource(client)
    if "marvel" == universe or "marvel comics" in publisher:
        return MarvelOfficialSource(client)
    return None


def merge_official_profile(
    entity: Entity,
    profile: OfficialProfile,
    *,
    image_path: str | None = None,
) -> Entity:
    def merge_list(current, incoming):
        result = list(current or [])
        seen = {normalize_search_text(item) for item in result}
        for item in incoming or []:
            key = normalize_search_text(item)
            if key and key not in seen:
                seen.add(key)
                result.append(item)
        return result

    entity.aliases = merge_list(entity.aliases, profile.aliases)
    entity.powers = merge_list(entity.powers, profile.powers)
    entity.occupation = merge_list(entity.occupation, profile.occupation)
    entity.affiliations = merge_list(entity.affiliations, profile.affiliations)

    # A fonte oficial é autoritativa quando fornece o campo. O conteúdo do PDF
    # continua preservado como apoio/proveniência em vez de ser descartado.
    if profile.description:
        if entity.description and entity.description != profile.description:
            entity.metadata.setdefault("supplemental_pdf_description", entity.description)
        entity.description = profile.description
    if profile.origin_place:
        entity.origin_place = profile.origin_place
    if profile.first_appearance:
        entity.first_appearance = profile.first_appearance
    if profile.gender:
        entity.gender = profile.gender
    if image_path:
        candidates = list(entity.metadata.get("image_candidates", []) or [])
        if entity.image and str(entity.image) not in {str(item) for item in candidates if item}:
            candidates.insert(0, str(entity.image))
        normalized_paths = {str(item) for item in candidates if item}
        if str(image_path) not in normalized_paths:
            candidates.append(str(image_path))
        entity.metadata["image_candidates"] = candidates
        entity.image = image_path
        entity.metadata["image_kind"] = "official_web_cache"

    existing_relations = {
        (normalize_search_text(item.predicate), normalize_search_text(item.target_name))
        for item in entity.relationships
    }
    for relation in profile.relationships:
        key = (normalize_search_text(relation.predicate), normalize_search_text(relation.target_name))
        if key not in existing_relations:
            existing_relations.add(key)
            entity.relationships.append(relation)

    if not any(source.url == profile.source_url for source in entity.sources):
        entity.sources.append(
            KnowledgeSource(
                source_type="official_web",
                source_ref=profile.publisher,
                url=profile.source_url,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
            )
        )

    entity.tags = merge_list(
        entity.tags,
        ["official-source", profile.universe.lower()],
    )
    return entity
