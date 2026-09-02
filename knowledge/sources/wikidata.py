"""Enriquecimento suplementar de personagens via Wikidata/Wikimedia Commons.

A fonte é opcional e nunca substitui dados oficiais/PDF já validados. O objetivo
é preencher lacunas de descrições curtas e referências visuais quando as fontes
primárias não oferecem esses campos. Dados estruturados do Wikidata são
registrados com proveniência; imagens do Commons ficam apenas no cache local e
mantêm metadados de atribuição/licença.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from pathlib import Path
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from core.logging_config import get_logger
from knowledge.entities import Entity, KnowledgeSource
from knowledge.store import normalize_search_text

log = get_logger("knowledge.wikidata")

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

_FICTION_TOKENS = (
    "fictional character",
    "fictional superhero",
    "fictional supervillain",
    "comic book character",
    "personagem ficticio",
    "personagem de ficcao",
    "super heroi ficticio",
    "superhero ficticio",
    "supervilao ficticio",
)


@dataclass
class WikidataProfile:
    qid: str
    label: str
    description: str
    description_language: str
    entity_url: str
    image_url: str | None = None
    image_source_url: str | None = None
    image_attribution: dict = field(default_factory=dict)


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", unescape(str(value)))
    return re.sub(r"\s+", " ", text).strip()


def _base_name(value: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", str(value or "")).strip()


def _identity_hint(entity: Entity) -> str:
    attributes = entity.attributes or {}
    real_name = _clean_text(attributes.get("real_name"))
    if real_name:
        return real_name
    name = str(entity.name or "")
    if name.endswith(")") and "(" in name:
        return name.rsplit("(", 1)[1][:-1].strip()
    return ""


def _publisher_tokens(entity: Entity) -> tuple[tuple[str, ...], tuple[str, ...]]:
    universe = normalize_search_text(entity.universe or "")
    publisher = normalize_search_text(entity.publisher or "")
    if universe == "marvel" or "marvel comics" in publisher:
        return (("marvel", "marvel comics"), ("dc comics",))
    if universe == "dc" or "dc comics" in publisher:
        return (("dc comics", "dc universe"), ("marvel", "marvel comics"))
    return ((), ())


def score_candidate(entity: Entity, candidate: dict) -> int:
    """Pontua candidatos de busca; sem evidência de editora, o perfil é rejeitado."""
    label = _clean_text(candidate.get("label"))
    description = _clean_text(candidate.get("description"))
    aliases = [
        _clean_text(item)
        for item in candidate.get("aliases", []) or []
        if _clean_text(item)
    ]
    if not label:
        return -100

    expected_values = [entity.name, entity.original_name, *entity.aliases]
    expected = {normalize_search_text(item) for item in expected_values if item}
    label_key = normalize_search_text(label)
    base_key = normalize_search_text(_base_name(entity.name))
    combined = normalize_search_text(" ".join([label, description, *aliases]))

    required_publishers, rejected_publishers = _publisher_tokens(entity)
    if rejected_publishers and any(token in combined for token in rejected_publishers):
        return -100
    publisher_evidence = any(token in combined for token in required_publishers)
    if required_publishers and not publisher_evidence:
        return -100

    score = 0
    if label_key in expected:
        score += 7
    if base_key and normalize_search_text(_base_name(label)) == base_key:
        score += 4
    if any(
        key
        and (
            f" {key} " in f" {label_key} "
            or f" {label_key} " in f" {key} "
        )
        for key in expected
    ):
        score += 2

    identity = normalize_search_text(_identity_hint(entity))
    if identity:
        if f" {identity} " in f" {combined} ":
            score += 5
        elif identity not in normalize_search_text(entity.name):
            score -= 2

    if publisher_evidence:
        score += 7
    if any(token in combined for token in _FICTION_TOKENS):
        score += 2
    if description:
        score += 1
    return score


def format_short_description(entity: Entity, description: str) -> str:
    """Transforma a descrição curta do Wikidata em uma frase ligada à entidade."""
    value = _clean_text(description).strip(" .")
    if not value:
        return ""
    if normalize_search_text(entity.name) in normalize_search_text(value):
        text = value
    else:
        text = f"{entity.name} — {value}"
    return text[:1].upper() + text[1:] + "."


class WikidataClient:
    def __init__(self, cache_dir: str | Path, *, timeout: float = 12.0):
        self.cache_dir = Path(cache_dir)
        self.search_cache = self.cache_dir / "search"
        self.entity_cache = self.cache_dir / "entities"
        self.commons_cache = self.cache_dir / "commons"
        self.image_cache = self.cache_dir / "images"
        for path in (
            self.search_cache,
            self.entity_cache,
            self.commons_cache,
            self.image_cache,
        ):
            path.mkdir(parents=True, exist_ok=True)
        self.timeout = float(timeout)

    @staticmethod
    def _cache_key(value: str) -> str:
        return sha256(value.encode("utf-8")).hexdigest()

    def _json_request(
        self,
        url: str,
        cache_path: Path,
        *,
        online: bool,
        force: bool = False,
    ) -> dict | None:
        if cache_path.exists() and not force:
            try:
                return json.loads(cache_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        if not online:
            return None
        request = Request(
            url,
            headers={
                "User-Agent": "STAR-Knowledge/3.0 (local personal knowledge index)",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
        ) as exc:
            log.debug("Wikidata indisponível %s: %s", url, exc)
            return None
        try:
            cache_path.write_text(
                json.dumps(data, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            log.debug("Falha ao salvar cache Wikidata %s: %s", cache_path, exc)
        return data

    def _search(
        self,
        query: str,
        language: str,
        *,
        online: bool,
        force: bool,
    ) -> list[dict]:
        params = urlencode(
            {
                "action": "wbsearchentities",
                "search": query,
                "language": language,
                "uselang": language,
                "format": "json",
                "limit": 10,
                "type": "item",
            }
        )
        url = f"{WIKIDATA_API}?{params}"
        cache_path = self.search_cache / (
            f"{self._cache_key(language + '|' + query)}.json"
        )
        data = (
            self._json_request(
                url,
                cache_path,
                online=online,
                force=force,
            )
            or {}
        )
        results = data.get("search", [])
        return [item for item in results if isinstance(item, dict)]

    def _entity_data(
        self,
        qid: str,
        *,
        online: bool,
        force: bool,
    ) -> dict | None:
        qid = str(qid or "").strip().upper()
        if not re.fullmatch(r"Q\d+", qid):
            return None
        url = WIKIDATA_ENTITY.format(qid=qid)
        cache_path = self.entity_cache / f"{qid}.json"
        data = (
            self._json_request(
                url,
                cache_path,
                online=online,
                force=force,
            )
            or {}
        )
        return (data.get("entities") or {}).get(qid)

    @staticmethod
    def _description(
        entity_data: dict,
        preferred: tuple[str, ...],
    ) -> tuple[str, str]:
        descriptions = entity_data.get("descriptions", {}) or {}
        for language in preferred:
            value = _clean_text(
                (descriptions.get(language) or {}).get("value")
            )
            if value:
                return value, language
        for language, payload in descriptions.items():
            value = _clean_text((payload or {}).get("value"))
            if value:
                return value, str(language)
        return "", ""

    @staticmethod
    def _p18_filename(entity_data: dict) -> str | None:
        claims = entity_data.get("claims", {}) or {}
        for claim in claims.get("P18", []) or []:
            try:
                value = claim["mainsnak"]["datavalue"]["value"]
            except (KeyError, TypeError):
                continue
            filename = _clean_text(value)
            if filename:
                return filename
        return None

    def _commons_info(
        self,
        filename: str,
        *,
        online: bool,
        force: bool,
    ) -> dict | None:
        params = urlencode(
            {
                "action": "query",
                "format": "json",
                "formatversion": 2,
                "prop": "imageinfo",
                "iiprop": "url|extmetadata",
                "titles": "File:" + filename,
            }
        )
        url = f"{COMMONS_API}?{params}"
        cache_path = self.commons_cache / f"{self._cache_key(filename)}.json"
        data = (
            self._json_request(
                url,
                cache_path,
                online=online,
                force=force,
            )
            or {}
        )
        pages = ((data.get("query") or {}).get("pages") or [])
        if not pages:
            return None
        infos = pages[0].get("imageinfo", []) or []
        return infos[0] if infos else None

    def cache_commons_image(
        self,
        image_url: str | None,
        *,
        online: bool,
    ) -> str | None:
        if not image_url:
            return None
        parsed = urlparse(image_url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (
            host == "upload.wikimedia.org"
            or host.endswith(".wikimedia.org")
        ):
            return None

        suffix = Path(parsed.path).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            suffix = ".jpg"
        target = self.image_cache / (
            f"{self._cache_key(image_url)}{suffix}"
        )
        if target.exists() and target.stat().st_size > 0:
            return str(target)
        if not online:
            return None

        request = Request(
            image_url,
            headers={"User-Agent": "STAR-Knowledge/3.0"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content_type = (
                    response.headers.get("Content-Type") or ""
                ).lower()
                if not content_type.startswith("image/"):
                    return None
                data = response.read(12 * 1024 * 1024 + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            log.debug("Imagem Commons indisponível %s: %s", image_url, exc)
            return None
        if not data or len(data) > 12 * 1024 * 1024:
            return None
        target.write_bytes(data)
        return str(target)

    def fetch_profile(
        self,
        entity: Entity,
        *,
        online: bool = True,
        force: bool = False,
        include_image: bool = True,
    ) -> WikidataProfile | None:
        queries = []
        for value in (
            entity.name,
            entity.original_name,
            _base_name(entity.name),
        ):
            value = _clean_text(value)
            if value and value not in queries:
                queries.append(value)
        identity = _identity_hint(entity)
        if identity and entity.name:
            combined = f"{_base_name(entity.name)} {identity}".strip()
            if combined and combined not in queries:
                queries.insert(0, combined)

        candidates: dict[str, tuple[int, dict, str]] = {}
        for language in ("pt", "en"):
            for query in queries[:3]:
                for item in self._search(
                    query,
                    language,
                    online=online,
                    force=force,
                ):
                    qid = str(item.get("id") or "").strip()
                    score = score_candidate(entity, item)
                    current = candidates.get(qid)
                    if qid and (
                        current is None or score > current[0]
                    ):
                        candidates[qid] = (
                            score,
                            item,
                            language,
                        )
            strong = [
                value
                for value in candidates.values()
                if value[0] >= 12
            ]
            if strong:
                break

        ranked = sorted(
            candidates.items(),
            key=lambda pair: pair[1][0],
            reverse=True,
        )
        if not ranked or ranked[0][1][0] < 12:
            return None

        qid, (_score, search_item, search_language) = ranked[0]
        entity_data = (
            self._entity_data(
                qid,
                online=online,
                force=force,
            )
            or {}
        )
        description, language = self._description(
            entity_data,
            ("pt", "en"),
        )
        if not description:
            description = _clean_text(search_item.get("description"))
            language = search_language if description else ""
        description = format_short_description(
            entity,
            description,
        )
        if not description:
            return None

        image_url = None
        image_source_url = None
        attribution = {}
        if include_image:
            filename = self._p18_filename(entity_data)
            if filename:
                info = self._commons_info(
                    filename,
                    online=online,
                    force=force,
                )
                if info:
                    ext = info.get("extmetadata", {}) or {}
                    license_name = _clean_text(
                        (ext.get("LicenseShortName") or {}).get("value")
                    )
                    if license_name:
                        image_url = (
                            _clean_text(
                                info.get("thumburl")
                                or info.get("url")
                            )
                            or None
                        )
                        image_source_url = (
                            _clean_text(info.get("descriptionurl"))
                            or (
                                "https://commons.wikimedia.org/wiki/File:"
                                + quote(filename.replace(" ", "_"))
                            )
                        )
                        attribution = {
                            "file": filename,
                            "author": _clean_text(
                                (ext.get("Artist") or {}).get("value")
                            ),
                            "credit": _clean_text(
                                (ext.get("Credit") or {}).get("value")
                            ),
                            "license": license_name,
                            "license_url": _clean_text(
                                (ext.get("LicenseUrl") or {}).get("value")
                            ),
                            "source_url": image_source_url,
                        }

        return WikidataProfile(
            qid=qid,
            label=_clean_text(search_item.get("label")) or entity.name,
            description=description,
            description_language=language,
            entity_url=f"https://www.wikidata.org/wiki/{qid}",
            image_url=image_url,
            image_source_url=image_source_url,
            image_attribution=attribution,
        )


def merge_wikidata_profile(
    entity: Entity,
    profile: WikidataProfile,
    *,
    image_path: str | None = None,
) -> Entity:
    """Preenche somente lacunas; fonte suplementar nunca sobrescreve fonte primária."""
    entity.metadata["wikidata_id"] = profile.qid
    description_kind = (
        entity.metadata or {}
    ).get("description_kind")
    if profile.description and (
        not entity.description
        or description_kind == "catalog_fallback"
    ):
        entity.description = profile.description
        entity.metadata[
            "description_kind"
        ] = "wikidata_short_description"
        entity.metadata[
            "description_language"
        ] = profile.description_language
        entity.metadata["description_verified"] = True

    current_image_valid = False
    if entity.image:
        try:
            current_image_valid = Path(str(entity.image)).is_file()
        except OSError:
            current_image_valid = False

    if image_path and not current_image_valid:
        entity.image = image_path
        candidates = list(
            entity.metadata.get("image_candidates", []) or []
        )
        if image_path not in candidates:
            candidates.append(image_path)
        entity.metadata["image_candidates"] = candidates
        entity.metadata["image_kind"] = (
            "wikimedia_commons_cache"
        )
        if profile.image_attribution:
            entity.metadata.setdefault(
                "image_attribution",
                {},
            )[image_path] = profile.image_attribution

    if not any(
        source.url == profile.entity_url
        for source in entity.sources
    ):
        entity.sources.append(
            KnowledgeSource(
                source_type="wikidata",
                source_ref="Wikidata",
                url=profile.entity_url,
                retrieved_at=datetime.now(
                    timezone.utc
                ).isoformat(),
                field_name="description",
            )
        )
    if (
        image_path
        and profile.image_source_url
        and not any(
            source.url == profile.image_source_url
            for source in entity.sources
        )
    ):
        entity.sources.append(
            KnowledgeSource(
                source_type="wikimedia_commons",
                source_ref="Wikimedia Commons",
                url=profile.image_source_url,
                retrieved_at=datetime.now(
                    timezone.utc
                ).isoformat(),
                field_name="image",
            )
        )
    return entity
