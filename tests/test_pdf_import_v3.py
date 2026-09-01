import pytest

fitz = pytest.importorskip("fitz")

from knowledge.engine import KnowledgeEngine
from knowledge.importers.heroes import HeroEncyclopediaImporter


def test_pdf_import_pipeline_extracts_structured_character(tmp_path):
    pdf = tmp_path / "heroes.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "BATMAN\nREAL NAME: Bruce Wayne\n"
        "OCCUPATION: Detective\n"
        "FIRST APPEARANCE: Detective Comics #27\n"
        "SPECIAL POWERS/ABILITIES: investigation, martial arts\n"
        "A vigilante detective from Gotham City.",
    )
    doc.save(pdf)
    doc.close()

    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    importer = HeroEncyclopediaImporter(engine, tmp_path / "cache")
    stats = importer.import_pdf(
        pdf,
        universe="DC",
        publisher="DC Comics",
        allow_ocr=False,
    )

    assert stats.pages_seen == 1
    assert stats.entities_saved >= 1
    entity = engine.resolve_entity("Batman")
    assert entity is not None
    assert entity.attributes["real_name"] == "Bruce Wayne"
    assert entity.sources[0].source_ref == "heroes.pdf"
    assert entity.sources[0].page == 1
