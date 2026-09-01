"""Enriquece personagens existentes usando apenas sites oficiais DC/Marvel."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import KNOWLEDGE_DB
from knowledge.engine import KnowledgeEngine
from knowledge.sources.official import (
    OfficialWebClient,
    merge_official_profile,
    source_for_entity,
)


def parser():
    p = argparse.ArgumentParser()
    p.add_argument("--universe", choices=["Marvel", "DC"])
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--offline-cache-only", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--no-images", action="store_true")
    return p


def main():
    args = parser().parse_args()
    engine = KnowledgeEngine(ROOT / KNOWLEDGE_DB)
    client = OfficialWebClient(ROOT / "knowledge" / "local" / "cache" / "official")
    filters = {"category": "character"}
    if args.universe:
        filters["universe"] = args.universe

    entities = engine.search_entities("", filters=filters, limit=5000)
    if args.limit > 0:
        entities = entities[: args.limit]

    found = updated = missing = 0
    for index, entity in enumerate(entities, start=1):
        source = source_for_entity(entity, client)
        if source is None:
            continue

        profile = source.fetch_profile(
            entity,
            online=not args.offline_cache_only,
            force=args.force,
        )
        if profile is None:
            missing += 1
            print(f"[{index}/{len(entities)}] sem perfil oficial: {entity.name}")
            continue

        found += 1
        image_path = None
        if not args.no_images and not entity.image:
            image_path = client.cache_image(
                profile.image_url,
                online=not args.offline_cache_only,
            )

        engine.upsert_entity(
            merge_official_profile(entity, profile, image_path=image_path)
        )
        updated += 1
        print(f"[{index}/{len(entities)}] atualizado: {entity.name}")

    print(
        f"Concluído. perfis={found}; atualizados={updated}; "
        f"sem_correspondência={missing}; total={len(entities)}"
    )


if __name__ == "__main__":
    main()
