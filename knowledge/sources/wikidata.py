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
from knowledge.entities import Entity, KnowledgeSource, record_field_provenance
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
    aliases: list[str] = field(default_factory=list)
    gender: str | None = None
    occupation: list[str] = field(default_factory=list)
    affiliations: list[str] = field(default_factory=list)
    creators: list[str] = field(default_factory=list)
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
    fiction_evidence = any(token in combined for token in _FICTION_TOKENS)
    # Algumas fichas Wikidata corretas não citam a editora na descrição curta.
    # Não rejeitamos automaticamente nesses casos quando o resultado é
    # explicitamente ficcional; conflitos Marvel/DC continuam rejeitados.
    if required_publishers and not publisher_evidence and not fiction_evidence:
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
    if fiction_evidence:
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
    def __init__(self, cache_dir: str | Path, *, timeout: float = 7.0):
        self.cache_dir = Path(cache_dir)
        self.search_cache = self.cache_dir / "search"
        self.entity_cache = self.cache_dir / "entities"
        self.commons_cache = self.cache_dir / "commons"
        self.image_cache = self.cache_dir / "images"
        self.image_rejections: list[dict] = []
        for path in (
            self.search_cache,
            self.entity_cache,
            self.commons_cache,
            self.image_cache,
        ):
            path.mkdir(parents=True, exist_ok=True)
        self.timeout = float(timeout)

    def _record_image_rejection(
        self,
        *,
        entity_name: str,
        reason: str,
        qid: str | None = None,
        source_url: str | None = None,
        detail: str | None = None,
    ) -> None:
        record = {
            "source": "wikimedia_commons",
            "entity": str(entity_name or ""),
            "reason": str(reason),
        }
        if qid:
            record["qid"] = str(qid)
        if source_url:
            record["source_url"] = str(source_url)
        if detail:
            record["detail"] = str(detail)[:240]
        self.image_rejections.append(record)

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

    @staticmethod
    def _claim_item_ids(entity_data: dict, property_id: str) -> list[str]:
        claims = entity_data.get("claims", {}) or {}
        result = []
        for claim in claims.get(property_id, []) or []:
            try:
                value = claim["mainsnak"]["datavalue"]["value"]
                qid = str(value["id"]).strip().upper()
            except (KeyError, TypeError):
                continue
            if re.fullmatch(r"Q\d+", qid) and qid not in result:
                result.append(qid)
        return result

    @staticmethod
    def _aliases(entity_data: dict) -> list[str]:
        aliases = entity_data.get("aliases", {}) or {}
        result = []
        for language in ("pt", "en"):
            for payload in aliases.get(language, []) or []:
                value = _clean_text((payload or {}).get("value"))
                if value and value not in result:
                    result.append(value)
                    if len(result) >= 30:
                        return result
        return result

    def _labels_for_qids(
        self,
        qids: list[str],
        *,
        online: bool,
        force: bool,
    ) -> list[str]:
        clean = []
        for qid in qids:
            value = str(qid or "").strip().upper()
            if re.fullmatch(r"Q\d+", value) and value not in clean:
                clean.append(value)
        if not clean:
            return []

        result = []
        for offset in range(0, len(clean), 50):
            chunk = clean[offset:offset + 50]
            key = "|".join(chunk)
            params = urlencode(
                {
                    "action": "wbgetentities",
                    "ids": key,
                    "props": "labels",
                    "languages": "pt|en",
                    "languagefallback": 1,
                    "format": "json",
                }
            )
            url = f"{WIKIDATA_API}?{params}"
            cache_path = self.entity_cache / (
                f"labels-{self._cache_key(key)}.json"
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
            by_id = data.get("entities", {}) or {}
            for qid in chunk:
                labels = (by_id.get(qid) or {}).get("labels", {}) or {}
                value = _clean_text(
                    (labels.get("pt") or labels.get("en") or {}).get("value")
                )
                if value and value not in result:
                    result.append(value)
        return result

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
                "iiprop": "url|mime|size|extmetadata",
                "iiurlwidth": 1024,
                "titles": "File:" + filename,
            }
        )
        url = f"{COMMONS_API}?{params}"
        cache_path = self.commons_cache / (
            f"v2-raster-1024-{self._cache_key(filename)}.json"
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
        pages = ((data.get("query") or {}).get("pages") or [])
        if not pages:
            return None
        infos = pages[0].get("imageinfo", []) or []
        return infos[0] if infos else None

    @staticmethod
    def _is_supported_raster_cache(path: Path) -> bool:
        try:
            header = path.read_bytes()[:16]
        except OSError:
            return False
        if header.startswith(b"\xff\xd8\xff"):
            return True
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return True
        if header.startswith((b"GIF87a", b"GIF89a")):
            return True
        return (
            len(header) >= 12
            and header[:4] == b"RIFF"
            and header[8:12] == b"WEBP"
        )

    def cache_commons_image(
        self,
        image_url: str | None,
        *,
        online: bool,
        entity_name: str = "",
        qid: str | None = None,
    ) -> str | None:
        if not image_url:
            self._record_image_rejection(
                entity_name=entity_name,
                qid=qid,
                reason="missing_image_url",
            )
            return None
        parsed = urlparse(image_url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (
            host == "upload.wikimedia.org"
            or host.endswith(".wikimedia.org")
        ):
            self._record_image_rejection(
                entity_name=entity_name,
                qid=qid,
                reason="unsupported_source_host",
                source_url=image_url,
            )
            return None

        suffix = Path(parsed.path).suffix.lower()
        allowed = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        if suffix not in allowed:
            suffix = ""

        cache_key = self._cache_key(image_url)
        existing = next(
            (
                self.image_cache / f"{cache_key}{candidate}"
                for candidate in allowed
                if (self.image_cache / f"{cache_key}{candidate}").exists()
                and (self.image_cache / f"{cache_key}{candidate}").stat().st_size > 0
            ),
            None,
        )
        if existing is not None:
            if self._is_supported_raster_cache(existing):
                return str(existing)
            try:
                existing.unlink()
            except OSError:
                pass
            self._record_image_rejection(
                entity_name=entity_name,
                qid=qid,
                reason="invalid_stale_image_cache",
                source_url=image_url,
                detail=str(existing),
            )
        if not online:
            self._record_image_rejection(
                entity_name=entity_name,
                qid=qid,
                reason="cache_miss_offline",
                source_url=image_url,
            )
            return None

        request = Request(
            image_url,
            headers={"User-Agent": "STAR-Knowledge/3.0"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content_type = (
                    response.headers.get("Content-Type") or ""
                ).lower().split(";", 1)[0].strip()
                type_suffix = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/webp": ".webp",
                    "image/gif": ".gif",
                }.get(content_type)
                if not type_suffix:
                    self._record_image_rejection(
                        entity_name=entity_name,
                        qid=qid,
                        reason="unsupported_image_format",
                        source_url=image_url,
                        detail=content_type or "content-type ausente",
                    )
                    return None
                suffix = suffix or type_suffix
                data = response.read(12 * 1024 * 1024 + 1)
        except HTTPError as exc:
            self._record_image_rejection(
                entity_name=entity_name,
                qid=qid,
                reason=f"http_{exc.code}",
                source_url=image_url,
            )
            return None
        except (URLError, TimeoutError, OSError) as exc:
            self._record_image_rejection(
                entity_name=entity_name,
                qid=qid,
                reason="network_error",
                source_url=image_url,
                detail=str(exc),
            )
            return None
        if not data:
            self._record_image_rejection(
                entity_name=entity_name,
                qid=qid,
                reason="empty_image",
                source_url=image_url,
            )
            return None
        if len(data) > 12 * 1024 * 1024:
            self._record_image_rejection(
                entity_name=entity_name,
                qid=qid,
                reason="image_too_large",
                source_url=image_url,
            )
            return None
        target = self.image_cache / f"{cache_key}{suffix}"
        target.write_bytes(data)
        return str(target)

    def fetch_profile(
        self,
        entity: Entity,
        *,
        online: bool = True,
        force: bool = False,
        include_image: bool = True,
        image_only: bool = False,
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
        if identity and entity.name and not image_only:
            combined = f"{_base_name(entity.name)} {identity}".strip()
            if combined and combined not in queries:
                queries.insert(0, combined)

        # A varredura visual precisa somente resolver P18. Evita até seis
        # buscas por personagem e várias chamadas de rótulos que não afetam
        # a imagem.
        search_queries = queries[:1] if image_only else queries[:3]
        search_languages = ("en", "pt") if image_only else ("pt", "en")

        candidates: dict[str, tuple[int, dict, str]] = {}
        for language in search_languages:
            for query in search_queries:
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
            if include_image:
                self._record_image_rejection(
                    entity_name=entity.name,
                    reason="wikidata_identity_unresolved",
                    detail=(
                        f"melhor_score={ranked[0][1][0]}"
                        if ranked
                        else "sem candidatos"
                    ),
                )
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

        if image_only:
            aliases = []
            gender_labels = []
            occupation = []
            affiliations = []
            creators = []
        else:
            aliases = self._aliases(entity_data)
            gender_labels = self._labels_for_qids(
                self._claim_item_ids(entity_data, "P21"),
                online=online,
                force=force,
            )
            occupation = self._labels_for_qids(
                self._claim_item_ids(entity_data, "P106"),
                online=online,
                force=force,
            )
            affiliations = self._labels_for_qids(
                self._claim_item_ids(entity_data, "P463"),
                online=online,
                force=force,
            )
            creators = self._labels_for_qids(
                self._claim_item_ids(entity_data, "P170"),
                online=online,
                force=force,
            )

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
                    usage_terms = _clean_text(
                        (ext.get("UsageTerms") or {}).get("value")
                    )
                    rights_text = normalize_search_text(
                        " ".join(
                            value
                            for value in (license_name, usage_terms)
                            if value
                        )
                    )
                    forbidden = (
                        "all rights reserved",
                        "copyrighted",
                        "non free",
                        "non-free",
                        "fair use",
                    )
                    open_markers = (
                        "cc by",
                        "cc-by",
                        "cc0",
                        "public domain",
                        "public-domain",
                        "pdm",
                        "gfdl",
                        "free art",
                    )
                    verified_open = (
                        bool(rights_text)
                        and not any(token in rights_text for token in forbidden)
                        and any(token in rights_text for token in open_markers)
                    )
                    if verified_open:
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
                            "license": license_name or usage_terms,
                            "license_url": _clean_text(
                                (ext.get("LicenseUrl") or {}).get("value")
                            ),
                            "source_url": image_source_url,
                            "rights_status": "open_license_verified",
                        }
                    else:
                        self._record_image_rejection(
                            entity_name=entity.name,
                            qid=qid,
                            reason=(
                                "missing_license_metadata"
                                if not rights_text
                                else "non_open_license"
                            ),
                            source_url=(
                                _clean_text(info.get("descriptionurl"))
                                or (
                                    "https://commons.wikimedia.org/wiki/File:"
                                    + quote(filename.replace(" ", "_"))
                                )
                            ),
                            detail=rights_text or "sem LicenseShortName/UsageTerms",
                        )
                else:
                    self._record_image_rejection(
                        entity_name=entity.name,
                        qid=qid,
                        reason="commons_metadata_unavailable",
                        source_url=(
                            "https://commons.wikimedia.org/wiki/File:"
                            + quote(filename.replace(" ", "_"))
                        ),
                    )
            else:
                self._record_image_rejection(
                    entity_name=entity.name,
                    qid=qid,
                    reason="wikidata_without_p18",
                    source_url=f"https://www.wikidata.org/wiki/{qid}",
                )

        if not any(
            (
                description,
                aliases,
                gender_labels,
                occupation,
                affiliations,
                creators,
                image_url,
            )
        ):
            return None

        return WikidataProfile(
            qid=qid,
            label=_clean_text(search_item.get("label")) or entity.name,
            description=description,
            description_language=language,
            entity_url=f"https://www.wikidata.org/wiki/{qid}",
            aliases=aliases,
            gender=gender_labels[0] if gender_labels else None,
            occupation=occupation,
            affiliations=affiliations,
            creators=creators,
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

    def merge_unique(current, incoming):
        result = list(current or [])
        seen = {normalize_search_text(item) for item in result}
        for item in incoming or []:
            key = normalize_search_text(item)
            if key and key not in seen:
                seen.add(key)
                result.append(item)
        return result

    entity.aliases = merge_unique(entity.aliases, profile.aliases)
    if profile.aliases:
        record_field_provenance(
            entity,
            "aliases",
            source_type="wikidata",
            source_ref="Wikidata",
            source_url=profile.entity_url,
        )
    if profile.gender and not entity.gender:
        entity.gender = profile.gender
        record_field_provenance(
            entity,
            "gender",
            source_type="wikidata",
            source_ref="Wikidata",
            source_url=profile.entity_url,
        )
    if profile.occupation and not entity.occupation:
        entity.occupation = list(profile.occupation)
        record_field_provenance(
            entity,
            "occupation",
            source_type="wikidata",
            source_ref="Wikidata",
            source_url=profile.entity_url,
        )
    if profile.affiliations and not entity.affiliations:
        entity.affiliations = list(profile.affiliations)
        record_field_provenance(
            entity,
            "affiliations",
            source_type="wikidata",
            source_ref="Wikidata",
            source_url=profile.entity_url,
        )
    if profile.creators and not entity.creators:
        entity.creators = list(profile.creators)
        record_field_provenance(
            entity,
            "creators",
            source_type="wikidata",
            source_ref="Wikidata",
            source_url=profile.entity_url,
        )

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
        record_field_provenance(
            entity,
            "description",
            source_type="wikidata",
            source_ref="Wikidata",
            source_url=profile.entity_url,
        )

    current_image_valid = False
    if entity.image:
        try:
            current_image_valid = Path(str(entity.image)).is_file()
        except OSError:
            current_image_valid = False

    attributions = entity.metadata.get("image_attribution", {}) or {}
    current_rights = (
        attributions.get(str(entity.image), {})
        if isinstance(attributions, dict) and entity.image
        else {}
    )
    current_open_licensed = (
        isinstance(current_rights, dict)
        and current_rights.get("rights_status") == "open_license_verified"
    )
    promote_commons = bool(
        image_path
        and (
            not current_image_valid
            or not current_open_licensed
        )
    )

    if promote_commons:
        previous_image = str(entity.image) if entity.image else None
        entity.image = image_path
        candidates = list(
            entity.metadata.get("image_candidates", []) or []
        )
        if previous_image and previous_image not in candidates:
            candidates.append(previous_image)
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
        record_field_provenance(
            entity,
            "image",
            source_type="wikimedia_commons",
            source_ref="Wikimedia Commons",
            source_url=profile.image_source_url,
        )

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
