"""Catálogo mestre Marvel versionado para a Ilha dos Heróis.

A identidade dos personagens vem de um snapshot estruturado no repositório.
Nenhum OCR cria personagens. Imagens são somente referências remotas no pack e
são baixadas para cache local quando o usuário solicita.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Callable

from core.logging_config import get_logger
from knowledge.entities import Entity, KnowledgeSource
from knowledge.store import normalize_search_text

log = get_logger("knowledge.marvel_catalog")

DEFAULT_PACK_ROOT = Path(__file__).resolve().parents[1] / "packs" / "heroes"
MASTER_FILE = "marvel_characters.jsonl"
IMAGE_MANIFEST_FILE = "marvel_image_manifest.json"
SOURCES_FILE = "marvel_sources.json"

_BANNED_NAMES = {
    "factfile",
    "essential storylines",
    "first appearance",
    "character facts",
    "contents",
    "index",
    "members",
    "original members",
    "key members",
}


@dataclass(frozen=True)
class MarvelMasterRecord:
    id: str
    source_id: int
    name: str
    original_name: str
    aliases: tuple[str, ...] = ()
    universe: str = "Marvel"
    publisher: str = "Marvel Comics"
    official_api_uri: str | None = None
    official_legacy_url: str | None = None
    image_ref: str | None = None


def _merge_values(current, incoming) -> list[str]:
    result = list(current or [])
    seen = {normalize_search_text(item) for item in result}
    for item in incoming or []:
        value = str(item or "").strip()
        key = normalize_search_text(value)
        if value and key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _valid_name(value: str) -> bool:
    name = str(value or "").strip()
    normalized = normalize_search_text(name)
    if not name or len(name) > 140 or normalized in _BANNED_NAMES:
        return False
    if len(name.split()) > 18:
        return False
    return any(ch.isalpha() for ch in name)


def _parenthetical_identity(value: str) -> str | None:
    """Retorna apenas o rótulo entre parênteses; a validação é por real_name exato."""
    name = str(value or "").strip()
    if not name.endswith(")") or "(" not in name:
        return None
    identity = name.rsplit("(", 1)[1][:-1].strip()
    return identity or None


class MarvelMasterCatalog:
    def __init__(self, pack_root: str | Path | None = None):
        self.pack_root = Path(pack_root) if pack_root else DEFAULT_PACK_ROOT
        self.master_path = self.pack_root / MASTER_FILE
        self.image_manifest_path = self.pack_root / IMAGE_MANIFEST_FILE
        self.sources_path = self.pack_root / SOURCES_FILE

    def source_metadata(self) -> dict:
        try:
            return json.loads(self.sources_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Metadados do catálogo Marvel inválidos: {exc}") from exc

    def load_records(self) -> list[MarvelMasterRecord]:
        if not self.master_path.exists():
            raise FileNotFoundError(f"Catálogo mestre Marvel ausente: {self.master_path}")

        records = []
        seen_ids = set()
        for line_number, raw in enumerate(
            self.master_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not raw.strip():
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"JSONL Marvel inválido na linha {line_number}: {exc}"
                ) from exc

            record_id = str(data.get("id") or "").strip()
            name = str(data.get("name") or "").strip()
            source_id = data.get("source_id")
            if (
                not record_id
                or record_id in seen_ids
                or not isinstance(source_id, int)
                or not _valid_name(name)
            ):
                raise RuntimeError(
                    f"Registro Marvel inválido na linha {line_number}: {record_id or name}"
                )
            seen_ids.add(record_id)
            records.append(
                MarvelMasterRecord(
                    id=record_id,
                    source_id=source_id,
                    name=name,
                    original_name=str(data.get("original_name") or name).strip(),
                    aliases=tuple(
                        str(item).strip()
                        for item in data.get("aliases", [])
                        if str(item).strip()
                    ),
                    universe=str(data.get("universe") or "Marvel"),
                    publisher=str(data.get("publisher") or "Marvel Comics"),
                    official_api_uri=data.get("official_api_uri"),
                    official_legacy_url=data.get("official_legacy_url"),
                    image_ref=data.get("image_ref"),
                )
            )
        return records

    def image_manifest(self) -> dict[str, list[str]]:
        try:
            data = json.loads(self.image_manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Manifesto visual Marvel inválido: {exc}") from exc
        images = data.get("images", {})
        if not isinstance(images, dict):
            raise RuntimeError("Manifesto visual Marvel precisa conter um mapa 'images'.")
        return {
            str(key): [str(url) for url in urls if str(url).startswith("https://")]
            for key, urls in images.items()
            if isinstance(urls, list)
        }

    @property
    def image_reference_count(self) -> int:
        return sum(bool(urls) for urls in self.image_manifest().values())

    def import_into(
        self,
        engine,
        *,
        progress: Callable[[str, int, int], None] | None = None,
    ) -> int:
        records = self.load_records()
        retrieved = datetime.now(timezone.utc).isoformat()

        current = engine.search_entities(
            "",
            filters={"category": "character", "universe": "Marvel"},
            limit=10000,
        )
        by_real_name = {}
        for item in current:
            real_name = normalize_search_text(
                (item.attributes or {}).get("real_name") or ""
            )
            if real_name:
                by_real_name.setdefault(real_name, item)

        for index, record in enumerate(records, start=1):
            existing = engine.store.find_exact(record.name, universe="Marvel")
            if existing is None and record.original_name != record.name:
                existing = engine.store.find_exact(
                    record.original_name,
                    universe="Marvel",
                )

            # Seeds antigos podem usar apenas o codinome, mas já guardar a
            # identidade real. Só convergimos por igualdade EXATA do real_name;
            # compartilhar "Spider-Man" nunca une Peter e Miles.
            identity = _parenthetical_identity(record.name)
            identity_key = normalize_search_text(identity or "")
            if existing is None and identity_key:
                existing = by_real_name.get(identity_key)

            if existing is None:
                entity = Entity(
                    id=record.id,
                    name=record.name,
                    original_name=record.original_name,
                    aliases=list(record.aliases),
                    category="character",
                    universe="Marvel",
                    publisher="Marvel Comics",
                )
            else:
                entity = existing
                entity.aliases = _merge_values(entity.aliases, record.aliases)
                if record.name != entity.name:
                    entity.aliases = _merge_values(
                        entity.aliases,
                        [record.name],
                    )
                if record.original_name != entity.name:
                    entity.aliases = _merge_values(
                        entity.aliases,
                        [record.original_name],
                    )

            entity.tags = _merge_values(entity.tags, ["marvel", "master-catalog"])
            entity.attributes["marvel_source_id"] = record.source_id
            entity.metadata["master_catalog_id"] = record.id
            entity.metadata["master_catalog"] = True
            if record.image_ref:
                entity.metadata["image_ref"] = record.image_ref
            if record.official_legacy_url:
                entity.metadata["official_legacy_url"] = record.official_legacy_url

            if not any(
                source.source_type == "marvel_master"
                and source.url == record.official_api_uri
                for source in entity.sources
            ):
                entity.sources.append(
                    KnowledgeSource(
                        source_type="marvel_master",
                        source_ref="Marvel API snapshot",
                        url=record.official_api_uri,
                        retrieved_at=retrieved,
                    )
                )

            engine.upsert_entity(entity)
            real_name = normalize_search_text(
                (entity.attributes or {}).get("real_name") or ""
            )
            if real_name:
                by_real_name.setdefault(real_name, entity)

            if progress and (index == 1 or index == len(records) or index % 50 == 0):
                progress("CATÁLOGO MARVEL", index, len(records))

        return len(records)

    def cache_images(
        self,
        engine,
        web_client,
        *,
        online: bool = True,
        limit: int = 0,
        progress: Callable[[str, int, int], None] | None = None,
    ) -> int:
        records = [record for record in self.load_records() if record.image_ref]
        if limit > 0:
            records = records[: int(limit)]
        manifest = self.image_manifest()
        cached = 0

        for index, record in enumerate(records, start=1):
            entity = engine.store.find_exact(record.name, universe="Marvel")
            if entity is None and record.original_name != record.name:
                entity = engine.store.find_exact(
                    record.original_name,
                    universe="Marvel",
                )

            if entity is not None:
                urls = manifest.get(record.image_ref or "", [])
                local_paths = []
                for url in urls:
                    image_path = web_client.cache_image(url, online=online)
                    if image_path:
                        local_paths.append(image_path)

                if local_paths:
                    entity.metadata["image_candidates"] = _merge_values(
                        entity.metadata.get("image_candidates", []),
                        local_paths,
                    )
                    entity.metadata["image_kind"] = "marvel_master_cache"
                    entity.image = local_paths[0]
                    for url in urls:
                        if not any(source.url == url for source in entity.sources):
                            entity.sources.append(
                                KnowledgeSource(
                                    source_type="image_manifest",
                                    source_ref="Marvel API thumbnail",
                                    url=url,
                                )
                            )
                    engine.upsert_entity(entity)
                    cached += 1

            if progress and (index == 1 or index == len(records) or index % 25 == 0):
                progress("IMAGENS MARVEL", index, len(records))

        return cached
