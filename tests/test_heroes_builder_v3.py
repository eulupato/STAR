import json

from knowledge.engine import KnowledgeEngine
from knowledge.entities import Entity, KnowledgeSource
from knowledge.heroes_builder import HeroesKnowledgeBuilder


def test_builder_coverage_report_is_local_and_deterministic(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    engine.upsert_entity(
        Entity(
            name="Batman",
            category="character",
            universe="DC",
            image=str(tmp_path / "batman.jpg"),
            sources=[
                KnowledgeSource("PDF", "dc.pdf", page=1),
                KnowledgeSource(
                    "official_web",
                    "DC Comics",
                    url="https://www.dc.com/characters/batman",
                ),
            ],
        )
    )
    builder = HeroesKnowledgeBuilder(engine, tmp_path / "local")
    report = builder.build(
        marvel_pdf=None,
        dc_pdf=None,
        online_enrichment=False,
        import_marvel_master=False,
    )

    assert report.total_characters == 1
    assert report.with_images == 1
    assert report.with_pdf_source == 1
    assert report.with_official_source == 1
    saved = json.loads(
        (tmp_path / "local" / "reports" / "heroes_build_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert saved["total_characters"] == 1


def test_builder_purges_only_untrusted_marvel_pdf_entities(tmp_path):
    pack = tmp_path / "pack"
    pack.mkdir()
    record = {
        "id": "marvel-api:10",
        "source_id": 10,
        "name": "Black Panther",
        "original_name": "Black Panther",
        "aliases": [],
        "universe": "Marvel",
        "publisher": "Marvel Comics",
        "official_api_uri": "https://gateway.marvel.com/v1/public/characters/10",
        "image_ref": None,
    }
    (pack / "marvel_characters.jsonl").write_text(
        json.dumps(record) + "\n",
        encoding="utf-8",
    )
    (pack / "marvel_image_manifest.json").write_text(
        json.dumps({"schema_version": 1, "images": {}}),
        encoding="utf-8",
    )
    (pack / "marvel_sources.json").write_text(
        json.dumps({"schema_version": 1, "coverage": {"snapshot_records": 1}}),
        encoding="utf-8",
    )

    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    engine.upsert_entity(
        Entity(
            name="FACTFILE aia",
            category="character",
            universe="Marvel",
            sources=[KnowledgeSource("PDF", "bad.pdf", page=4)],
        )
    )
    engine.upsert_entity(
        Entity(
            name="Spider-Man",
            category="character",
            universe="Marvel",
            sources=[KnowledgeSource("knowledge_pack", "heroes.json")],
        )
    )

    report = HeroesKnowledgeBuilder(
        engine,
        tmp_path / "local",
        marvel_pack_root=pack,
    ).build(import_marvel_master=True)

    assert report.marvel.purged_untrusted_pdf == 1
    assert engine.resolve_entity("FACTFILE aia", universe="Marvel") is None
    assert engine.resolve_entity("Spider-Man", universe="Marvel") is not None
    assert engine.resolve_entity("Black Panther", universe="Marvel") is not None
