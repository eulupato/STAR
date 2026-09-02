import json

from knowledge.engine import KnowledgeEngine
from knowledge.entities import Entity, KnowledgeSource
from knowledge.heroes_builder import HeroesKnowledgeBuilder


def test_builder_coverage_report_is_local_and_deterministic(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    image = tmp_path / "batman.jpg"
    image.write_bytes(b"image")
    engine.upsert_entity(
        Entity(
            name="Batman",
            category="character",
            universe="DC",
            image=str(image),
            description="Batman protege Gotham City.",
            metadata={"description_kind": "official_web"},
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
    assert report.with_descriptions == 1
    assert report.with_verified_descriptions == 1
    assert report.complete_cards == 1
    assert report.with_pdf_source == 1
    assert report.field_coverage["verified_description"]["count"] == 1
    assert report.field_coverage["powers"]["missing"] == 1
    assert report.field_coverage["appearances"]["missing"] == 1
    assert report.field_coverage_by_universe["DC"]["verified_description"]["percent"] == 100.0
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



def test_builder_never_leaves_character_description_blank(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    engine.upsert_entity(
        Entity(
            name="Hero Without Bio",
            category="character",
            universe="Marvel",
            publisher="Marvel Comics",
        )
    )

    report = HeroesKnowledgeBuilder(
        engine,
        tmp_path / "local",
    ).build(
        import_marvel_master=False,
        online_enrichment=False,
        wikidata_fallback=False,
    )

    entity = engine.resolve_entity(
        "Hero Without Bio",
        universe="Marvel",
    )
    assert entity is not None
    assert entity.description
    assert entity.metadata["description_kind"] == "catalog_fallback"
    assert entity.metadata["description_verified"] is False
    assert report.missing_description_count == 0
    assert report.fallback_descriptions == 1
    assert report.missing_verified_description_count == 1


def test_builder_audit_reports_field_and_image_rights_coverage(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    image = tmp_path / "hero.jpg"
    image.write_bytes(b"image")
    engine.upsert_entity(
        Entity(
            name="Hero",
            category="character",
            universe="Marvel",
            image=str(image),
            description="Verified bio.",
            powers=["Flight"],
            occupation=["Pilot"],
            metadata={
                "description_kind": "wikidata_short_description",
                "image_attribution": {
                    str(image): {
                        "author": "Example",
                        "license": "CC BY-SA 4.0",
                        "source_url": "https://commons.wikimedia.org/wiki/File:Hero.jpg",
                    }
                },
            },
        )
    )
    builder = HeroesKnowledgeBuilder(engine, tmp_path / "local")
    report = builder.audit()

    assert report.total_characters == 1
    assert report.open_licensed_images == 1
    assert report.sourced_images == 1
    assert report.field_coverage["powers"]["percent"] == 100.0
    assert report.field_coverage["abilities"]["percent"] == 0.0
    assert report.missing_by_field["abilities"] == ["Hero"]
    assert (
        tmp_path
        / "local"
        / "reports"
        / "heroes_coverage_report.json"
    ).exists()


def test_builder_audit_counts_appearances_from_attributes(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    engine.upsert_entity(
        Entity(
            name="Appearance Hero",
            category="character",
            universe="Marvel",
            attributes={"appearances": ["Hero #1", "Hero #2"]},
        )
    )

    report = HeroesKnowledgeBuilder(
        engine,
        tmp_path / "local",
    ).audit()

    assert report.field_coverage["appearances"]["count"] == 1
    assert report.field_coverage["appearances"]["missing"] == 0


def test_builder_collects_image_rejection_reasons(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    builder = HeroesKnowledgeBuilder(engine, tmp_path / "local")
    builder.web.image_rejections.append(
        {
            "source": "marvel_api_thumbnail",
            "entity": "Hero A",
            "reason": "http_403",
        }
    )
    builder.wikidata.image_rejections.extend(
        [
            {
                "source": "wikimedia_commons",
                "entity": "Hero A",
                "reason": "missing_license_metadata",
            },
            {
                "source": "wikimedia_commons",
                "entity": "Hero B",
                "reason": "missing_license_metadata",
            },
        ]
    )

    report = builder.audit()

    assert report.image_rejection_reasons["missing_license_metadata"] == 2
    assert report.image_rejection_reasons["http_403"] == 1
    assert len(report.image_rejections) == 3
