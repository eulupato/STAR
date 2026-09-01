"""Migração não destrutiva de packs legados para o Entity System."""
from __future__ import annotations

import json
from pathlib import Path

from core.logging_config import get_logger
from .entities import Entity, KnowledgeSource
from .store import normalize_search_text

log = get_logger("knowledge.bootstrap")


def _merge_unique(current, incoming):
    result = list(current or [])
    seen = {normalize_search_text(item) for item in result}
    for item in incoming or []:
        key = normalize_search_text(item)
        if key and key not in seen:
            seen.add(key)
            result.append(str(item))
    return result


def _find_existing(engine, names, universe=None):
    for name in names:
        if not name:
            continue
        entity = engine.store.find_exact(str(name), universe=universe)
        if entity is not None:
            return entity
    return None


def _ensure_character_seed(engine, item, universe, publisher, source):
    if isinstance(item, str):
        canonical = item
        aliases = []
        real_name = None
    else:
        canonical = str(item.get("name") or "").strip()
        aliases = [str(value) for value in item.get("aliases", []) if str(value).strip()]
        real_name = str(item.get("real_name") or "").strip() or None

    if not canonical:
        return 0

    candidates = [canonical, *aliases]
    if real_name:
        candidates.append(real_name)

    existing = _find_existing(engine, candidates, universe=universe)
    if existing is not None:
        previous_name = existing.name
        if normalize_search_text(previous_name) != normalize_search_text(canonical):
            existing.aliases = _merge_unique(existing.aliases, [previous_name])
            existing.name = canonical
        existing.aliases = _merge_unique(existing.aliases, aliases)
        if real_name:
            existing.aliases = _merge_unique(existing.aliases, [real_name])
            existing.attributes.setdefault("real_name", real_name)
        existing.publisher = existing.publisher or publisher
        existing.tags = _merge_unique(existing.tags, ["hero", "legacy-seed"])
        if not any(s.source_type == "knowledge_pack" for s in existing.sources):
            existing.sources.append(
                KnowledgeSource("knowledge_pack", str(source))
            )
        existing.metadata.setdefault("seed", True)
        engine.upsert_entity(existing)
        return 0

    entity = Entity(
        name=canonical,
        aliases=_merge_unique(aliases, [real_name] if real_name else []),
        category="character",
        universe=universe,
        publisher=publisher,
        tags=["hero", "legacy-seed"],
        sources=[KnowledgeSource("knowledge_pack", str(source))],
        metadata={"seed": True},
        attributes={"real_name": real_name} if real_name else {},
    )
    engine.upsert_entity(entity)
    return 1


def bootstrap_legacy_heroes(engine, path: str | Path) -> int:
    source = Path(path)
    if not source.exists():
        return 0
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Pack legado de heróis inválido: %s", exc)
        return 0

    created = 0
    for universe, items in data.get("super_heroes", {}).items():
        publisher = (
            "Marvel Comics"
            if universe.lower() == "marvel"
            else "DC Comics"
            if universe.lower() == "dc"
            else None
        )
        for item in items or []:
            created += _ensure_character_seed(
                engine,
                item,
                str(universe),
                publisher,
                source,
            )

    for name in data.get("heroes_historicos", []) or []:
        existing = _find_existing(engine, [name])
        if existing is None:
            engine.upsert_entity(
                Entity(
                    name=str(name),
                    category="person",
                    tags=["historical-hero", "legacy-seed"],
                    sources=[KnowledgeSource("knowledge_pack", str(source))],
                    metadata={"seed": True},
                )
            )
            created += 1

    for name in data.get("mitologia", []) or []:
        existing = _find_existing(engine, [name])
        if existing is None:
            engine.upsert_entity(
                Entity(
                    name=str(name),
                    category="mythological_character",
                    tags=["mythology", "legacy-seed"],
                    sources=[KnowledgeSource("knowledge_pack", str(source))],
                    metadata={"seed": True},
                )
            )
            created += 1

    return created
