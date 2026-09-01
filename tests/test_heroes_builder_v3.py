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
