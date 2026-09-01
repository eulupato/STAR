"""Migração leve de packs legados para o Entity System."""
from __future__ import annotations

import json
from pathlib import Path

from core.logging_config import get_logger
from .entities import Entity, KnowledgeSource

log = get_logger("knowledge.bootstrap")


def bootstrap_legacy_heroes(engine, path: str | Path) -> int:
    source = Path(path)
    if not source.exists():
        return 0
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Pack legado de heróis inválido: %s", exc)
        return 0

    entities = []
    super_heroes = data.get("super_heroes", {})
    for universe, names in super_heroes.items():
        publisher = "Marvel Comics" if universe.lower() == "marvel" else "DC Comics" if universe.lower() == "dc" else None
        for name in names or []:
            entities.append(
                Entity(
                    name=str(name),
                    category="character",
                    universe=str(universe),
                    publisher=publisher,
                    tags=["hero", "legacy-seed"],
                    sources=[
                        KnowledgeSource(
                            source_type="knowledge_pack",
                            source_ref=str(source),
                        )
                    ],
                    metadata={"seed": True},
                )
            )

    for name in data.get("heroes_historicos", []) or []:
        entities.append(
            Entity(
                name=str(name),
                category="person",
                tags=["historical-hero", "legacy-seed"],
                sources=[KnowledgeSource("knowledge_pack", str(source))],
                metadata={"seed": True},
            )
        )

    for name in data.get("mitologia", []) or []:
        entities.append(
            Entity(
                name=str(name),
                category="mythological_character",
                tags=["mythology", "legacy-seed"],
                sources=[KnowledgeSource("knowledge_pack", str(source))],
                metadata={"seed": True},
            )
        )

    return engine.store.upsert_many(entities)
