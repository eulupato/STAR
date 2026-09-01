import json

from knowledge.bootstrap import bootstrap_legacy_heroes
from knowledge.engine import KnowledgeEngine
from knowledge.entities import Entity, KnowledgeSource


def test_bootstrap_preserves_rich_existing_entity(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    engine.upsert_entity(
        Entity(
            name="Batman",
            category="character",
            universe="DC",
            publisher="DC Comics",
            description="Descrição rica",
            powers=["detective skill"],
            sources=[KnowledgeSource("PDF", "dc.pdf", page=42)],
        )
    )
    seed = tmp_path / "heroes.json"
    seed.write_text(
        json.dumps(
            {
                "super_heroes": {
                    "DC": [{"name": "Batman", "aliases": [], "real_name": "Bruce Wayne"}]
                }
            }
        ),
        encoding="utf-8",
    )

    created = bootstrap_legacy_heroes(engine, seed)
    batman = engine.resolve_entity("Batman", universe="DC")
    assert created == 0
    assert batman.description == "Descrição rica"
    assert "detective skill" in batman.powers
    assert "Bruce Wayne" in batman.aliases
    assert any(source.source_type == "PDF" for source in batman.sources)


def test_bootstrap_migrates_portuguese_alias_to_canonical_name(tmp_path):
    engine = KnowledgeEngine(tmp_path / "knowledge.db")
    engine.upsert_entity(
        Entity(
            name="Homem-Aranha",
            category="character",
            universe="Marvel",
            publisher="Marvel Comics",
        )
    )
    seed = tmp_path / "heroes.json"
    seed.write_text(
        json.dumps(
            {
                "super_heroes": {
                    "Marvel": [
                        {
                            "name": "Spider-Man",
                            "aliases": ["Homem-Aranha"],
                            "real_name": "Peter Parker",
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    bootstrap_legacy_heroes(engine, seed)
    entity = engine.resolve_entity("Spider-Man", universe="Marvel")
    assert entity is not None
    assert entity.name == "Spider-Man"
    assert "Homem-Aranha" in entity.aliases
    assert engine.store.count("character") == 1
