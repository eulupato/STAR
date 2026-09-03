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


def test_visual_scan_prefers_commons_and_writes_checkpoint(tmp_path, monkeypatch):
    from knowledge.entities import Entity
    from knowledge.sources.wikidata import WikidataProfile
    import knowledge.heroes_builder as heroes_builder_module

    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    engine.upsert_entity(
        Entity(
            name="Visual Hero",
            category="character",
            universe="Marvel",
            publisher="Marvel Comics",
        )
    )
    builder = HeroesKnowledgeBuilder(engine, tmp_path / "local")

    profile = WikidataProfile(
        qid="Q123",
        label="Visual Hero",
        description="Visual Hero — fictional superhero.",
        description_language="en",
        entity_url="https://www.wikidata.org/wiki/Q123",
        image_url="https://upload.wikimedia.org/visual-hero.jpg",
        image_source_url=(
            "https://commons.wikimedia.org/wiki/File:Visual_Hero.jpg"
        ),
        image_attribution={
            "author": "Example Artist",
            "license": "CC BY-SA 4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "source_url": (
                "https://commons.wikimedia.org/wiki/File:Visual_Hero.jpg"
            ),
            "rights_status": "open_license_verified",
        },
    )

    monkeypatch.setattr(
        builder.wikidata,
        "fetch_profile",
        lambda *args, **kwargs: profile,
    )

    def fake_cache(*args, **kwargs):
        image = tmp_path / "commons.jpg"
        image.write_bytes(b"image")
        return str(image)

    monkeypatch.setattr(builder.wikidata, "cache_commons_image", fake_cache)

    def official_must_not_run(*args, **kwargs):
        raise AssertionError("fonte oficial não deve substituir Commons licenciado")

    monkeypatch.setattr(
        heroes_builder_module,
        "source_for_entity",
        official_must_not_run,
    )

    report = builder.scan_visual_references(
        online=False,
        resume=False,
        limit=1,
        delay_seconds=0,
    )

    assert report["totals"]["accepted_open_license"] == 1
    assert builder._visual_scan_state_path().exists()
    state = json.loads(
        builder._visual_scan_state_path().read_text(encoding="utf-8")
    )
    record = next(iter(state["characters"].values()))
    assert record["status"] == "accepted_open_license"
    assert record["accepted"]["license"] == "CC BY-SA 4.0"


def test_visual_scan_resume_skips_completed_character(tmp_path, monkeypatch):
    from knowledge.entities import Entity

    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    image = tmp_path / "official.jpg"
    image.write_bytes(b"image")
    entity = Entity(
        name="Resume Hero",
        category="character",
        universe="Marvel",
        publisher="Marvel Comics",
        image=str(image),
        metadata={
            "image_attribution": {
                str(image): {
                    "author": "Marvel",
                    "license": "No open license recorded",
                    "source_url": "https://www.marvel.com/characters/resume-hero",
                    "rights_status": "official_source_local_reference",
                }
            }
        },
    )
    engine.upsert_entity(entity)
    builder = HeroesKnowledgeBuilder(engine, tmp_path / "local")
    key = str(engine.resolve_entity("Resume Hero", universe="Marvel").id)
    builder._save_visual_scan_state(
        {
            "schema_version": 2,
            "characters": {
                key: {
                    "name": "Resume Hero",
                    "universe": "Marvel",
                    "status": "accepted_official_reference",
                    "accepted": {},
                    "rejections": [],
                }
            },
        }
    )

    monkeypatch.setattr(
        builder.wikidata,
        "fetch_profile",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("checkpoint deveria evitar nova busca")
        ),
    )

    report = builder.scan_visual_references(
        online=False,
        resume=True,
        delay_seconds=0,
    )

    assert report["totals"]["skipped_resume"] == 1
    assert report["totals"]["accepted_official_reference"] == 1


def test_visual_scan_uses_marvel_manifest_before_live_official(tmp_path, monkeypatch):
    import knowledge.heroes_builder as heroes_builder_module

    pack = tmp_path / "pack"
    pack.mkdir()
    record = {
        "id": "marvel-api:99",
        "source_id": 99,
        "name": "Manifest Hero",
        "original_name": "Manifest Hero",
        "aliases": [],
        "universe": "Marvel",
        "publisher": "Marvel Comics",
        "official_api_uri": "https://gateway.marvel.com/v1/public/characters/99",
        "image_ref": "marvel-api:99",
    }
    (pack / "marvel_characters.jsonl").write_text(
        json.dumps(record) + "\n",
        encoding="utf-8",
    )
    (pack / "marvel_image_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "images": {
                    "marvel-api:99": [
                        "https://i.annihil.us/manifest-hero.jpg"
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (pack / "marvel_sources.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "coverage": {"snapshot_records": 1},
            }
        ),
        encoding="utf-8",
    )

    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    builder = HeroesKnowledgeBuilder(
        engine,
        tmp_path / "local",
        marvel_pack_root=pack,
    )
    builder.marvel_master.import_into(engine)

    def fake_cache(url, *, online=True, context="", source_ref=""):
        image = tmp_path / "manifest.jpg"
        image.write_bytes(b"image")
        return str(image)

    monkeypatch.setattr(builder.web, "cache_image", fake_cache)
    monkeypatch.setattr(
        builder.wikidata,
        "fetch_profile",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        heroes_builder_module,
        "source_for_entity",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("perfil live não deve ser chamado quando o manifesto resolveu")
        ),
    )

    report = builder.scan_visual_references(
        online=False,
        resume=False,
        delay_seconds=0,
    )

    assert report["totals"]["accepted_official_reference"] == 1
    hero = engine.resolve_entity("Manifest Hero", universe="Marvel")
    assert hero is not None
    assert hero.image
    attribution = hero.metadata["image_attribution"][hero.image]
    assert attribution["rights_status"] == "official_source_local_reference"


def test_network_clients_use_fail_fast_default_timeouts(tmp_path):
    from knowledge.sources.official import OfficialWebClient
    from knowledge.sources.wikidata import WikidataClient

    assert OfficialWebClient(tmp_path / "official").timeout <= 5.0
    assert WikidataClient(tmp_path / "wikidata").timeout <= 7.0


def test_visual_scan_discards_old_checkpoint_schema(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    builder = HeroesKnowledgeBuilder(engine, tmp_path / "local")
    builder._visual_scan_state_path().write_text(
        json.dumps(
            {
                "schema_version": 1,
                "characters": {
                    "old": {
                        "status": "accepted_official_reference",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    state = builder._load_visual_scan_state()

    assert state["schema_version"] == 2
    assert state["characters"] == {}


def test_visual_scan_does_not_call_live_official_by_default(tmp_path, monkeypatch):
    import knowledge.heroes_builder as heroes_builder_module

    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    engine.upsert_entity(
        Entity(
            name="No Image Hero",
            category="character",
            universe="Marvel",
            publisher="Marvel Comics",
        )
    )
    builder = HeroesKnowledgeBuilder(engine, tmp_path / "local")
    monkeypatch.setattr(
        builder.wikidata,
        "fetch_profile",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        heroes_builder_module,
        "source_for_entity",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("live official must be opt-in in image scan")
        ),
    )

    report = builder.scan_visual_references(
        online=False,
        resume=False,
        delay_seconds=0,
    )

    assert report["totals"]["unresolved"] == 1


def test_visual_scan_skips_wikidata_when_manifest_image_exists(tmp_path, monkeypatch):
    pack = tmp_path / "pack_skip_wikidata"
    pack.mkdir()
    record = {
        "id": "marvel-api:199",
        "source_id": 199,
        "name": "Fast Hero",
        "original_name": "Fast Hero",
        "aliases": [],
        "universe": "Marvel",
        "publisher": "Marvel Comics",
        "official_api_uri": "https://gateway.marvel.com/v1/public/characters/199",
        "image_ref": "marvel-api:199",
    }
    (pack / "marvel_characters.jsonl").write_text(
        json.dumps(record) + "\n",
        encoding="utf-8",
    )
    (pack / "marvel_image_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "images": {
                    "marvel-api:199": [
                        "https://i.annihil.us/fast-hero.jpg"
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (pack / "marvel_sources.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "coverage": {"snapshot_records": 1},
            }
        ),
        encoding="utf-8",
    )

    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    builder = HeroesKnowledgeBuilder(
        engine,
        tmp_path / "local",
        marvel_pack_root=pack,
    )
    builder.marvel_master.import_into(engine)

    def fake_cache(url, *, online=True, context="", source_ref=""):
        image = tmp_path / "fast.jpg"
        image.write_bytes(b"image")
        return str(image)

    monkeypatch.setattr(builder.web, "cache_image", fake_cache)
    monkeypatch.setattr(
        builder.wikidata,
        "fetch_profile",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Wikidata should not run after manifest success")
        ),
    )

    report = builder.scan_visual_references(
        online=False,
        resume=False,
        delay_seconds=0,
    )

    assert report["totals"]["accepted_official_reference"] == 1
