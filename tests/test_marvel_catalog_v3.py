import json
from pathlib import Path

from knowledge.engine import KnowledgeEngine
from knowledge.sources.marvel_catalog import MarvelMasterCatalog


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge" / "packs" / "heroes"


def _write_pack(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "id": "marvel-api:1",
            "source_id": 1,
            "name": "Spider-Man (Peter Parker)",
            "original_name": "Spider-Man",
            "aliases": ["Spider-Man"],
            "universe": "Marvel",
            "publisher": "Marvel Comics",
            "official_api_uri": "https://gateway.marvel.com/v1/public/characters/1",
            "image_ref": "marvel-api:1",
        },
        {
            "id": "marvel-api:2",
            "source_id": 2,
            "name": "Spider-Man (Miles Morales)",
            "original_name": "Spider-Man (Miles Morales)",
            "aliases": [],
            "universe": "Marvel",
            "publisher": "Marvel Comics",
            "official_api_uri": "https://gateway.marvel.com/v1/public/characters/2",
            "image_ref": "marvel-api:2",
        },
    ]
    (root / "marvel_characters.jsonl").write_text(
        "\n".join(json.dumps(item) for item in records) + "\n",
        encoding="utf-8",
    )
    (root / "marvel_image_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "images": {
                    "marvel-api:1": ["https://i.annihil.us/peter.jpg"],
                    "marvel-api:2": ["https://i.annihil.us/miles.jpg"],
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "marvel_sources.json").write_text(
        json.dumps({"schema_version": 1, "coverage": {"snapshot_records": 2}}),
        encoding="utf-8",
    )


def test_versioned_master_pack_is_structured_and_declares_coverage():
    catalog = MarvelMasterCatalog(PACK)
    records = catalog.load_records()
    meta = catalog.source_metadata()

    assert len(records) == meta["coverage"]["snapshot_records"]
    assert len(records) >= 1500
    assert meta["coverage"]["status"] == "partial_verified_snapshot"
    assert meta["coverage"]["official_site_reported_results"] > len(records)
    assert all("factfile" not in record.name.lower() for record in records)


def test_master_catalog_import_is_offline_and_preserves_variants(tmp_path):
    pack = tmp_path / "pack"
    _write_pack(pack)
    engine = KnowledgeEngine(tmp_path / "knowledge.db")

    saved = MarvelMasterCatalog(pack).import_into(engine)

    assert saved == 2
    peter = engine.resolve_entity("Spider-Man (Peter Parker)", universe="Marvel")
    miles = engine.resolve_entity("Spider-Man (Miles Morales)", universe="Marvel")
    assert peter is not None and miles is not None
    assert peter.id != miles.id
    assert any(source.source_type == "marvel_master" for source in peter.sources)


def test_image_manifest_contains_urls_not_binary_assets():
    catalog = MarvelMasterCatalog(PACK)
    manifest = catalog.image_manifest()

    assert manifest
    assert all(
        url.startswith("https://")
        for urls in manifest.values()
        for url in urls
    )
    assert not list(PACK.glob("*.jpg"))
    assert not list(PACK.glob("*.png"))


def test_master_catalog_reuses_seed_by_exact_real_name(tmp_path):
    pack = tmp_path / "pack"
    _write_pack(pack)
    engine = KnowledgeEngine(tmp_path / "knowledge.db")

    from knowledge.entities import Entity

    engine.upsert_entity(
        Entity(
            name="Spider-Man",
            category="character",
            universe="Marvel",
            publisher="Marvel Comics",
            attributes={"real_name": "Peter Parker"},
        )
    )

    MarvelMasterCatalog(pack).import_into(engine)

    peter = engine.resolve_entity("Spider-Man (Peter Parker)", universe="Marvel")
    miles = engine.resolve_entity("Spider-Man (Miles Morales)", universe="Marvel")
    original_seed = engine.resolve_entity("Spider-Man", universe="Marvel")

    assert peter is not None
    assert miles is not None
    assert original_seed is not None
    assert peter.id == original_seed.id
    assert peter.id != miles.id
