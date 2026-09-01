from knowledge.engine import KnowledgeEngine
from knowledge.entities import Entity, KnowledgeSource, Relationship


def make_engine(tmp_path):
    return KnowledgeEngine(tmp_path / "knowledge.db")


def test_entity_alias_search_filters_and_sources(tmp_path):
    engine = make_engine(tmp_path)
    entity = Entity(
        name="Homem-Aranha",
        original_name="Spider-Man",
        aliases=["Spider-Man", "Peter Parker"],
        category="character",
        universe="Marvel",
        publisher="Marvel Comics",
        species="Humano",
        team=["Vingadores"],
        powers=["sentido aranha", "agilidade"],
        sources=[KnowledgeSource("PDF", "marvel.pdf", page=12)],
    )
    engine.upsert_entity(entity)

    assert engine.resolve_entity("spider man").name == "Homem-Aranha"
    assert engine.resolve_entity("Peter Parker").name == "Homem-Aranha"
    assert engine.search_entities("aranha")[0].name == "Homem-Aranha"
    assert engine.search_entities("agilidade")[0].name == "Homem-Aranha"
    assert engine.search_entities("", {"universe": "Marvel"})[0].sources[0].page == 12


def test_knowledge_graph_relationship_query(tmp_path):
    engine = make_engine(tmp_path)
    batman = Entity(
        name="Batman",
        aliases=["Bruce Wayne"],
        category="character",
        universe="DC",
        publisher="DC Comics",
        origin_place="Gotham City",
        relationships=[
            Relationship("ally", "Robin"),
            Relationship("team", "Liga da Justiça"),
        ],
    )
    engine.upsert_entity(batman)

    answer = engine.answer("quais aliados do Batman?")
    assert "Robin" in answer
    origin = engine.answer("onde Batman vem?")
    assert "Gotham City" in origin


def test_universal_search_deduplicates_entities(tmp_path):
    engine = make_engine(tmp_path)
    engine.upsert_entity(
        Entity(
            name="Wolverine",
            aliases=["Logan"],
            category="character",
            universe="Marvel",
            powers=["fator de cura"],
        )
    )
    results = engine.universal_search("Wolverine")
    names = [item.title for item in results]
    assert names.count("Wolverine") == 1


def test_context_resolves_entity_pronouns(tmp_path):
    from core.mind.context import ContextEngine
    from core.mind.working_memory import WorkingMemory

    context = ContextEngine()
    memory = WorkingMemory()
    context.track_entity("Batman", category="character")
    assert context.resolve_reference_text("quais aliados dele?") == "quais aliados de Batman?"
    assert context.resolve_reference_text("onde ele vem?") == "onde Batman vem?"


def test_multivalue_filters_for_team_power_and_affiliation(tmp_path):
    engine = make_engine(tmp_path)
    engine.upsert_entity(
        Entity(
            name="Jean Grey",
            category="character",
            universe="Marvel",
            team=["X-Men"],
            affiliations=["X-Men"],
            species="Mutante",
            powers=["telepatia", "telecinese"],
            tags=["mutante"],
        )
    )
    assert engine.search_entities("", {"team": "X-Men"})[0].name == "Jean Grey"
    assert engine.search_entities("", {"power": "telepatia"})[0].name == "Jean Grey"
    assert engine.search_entities("", {"affiliation": "X-Men"})[0].name == "Jean Grey"


def test_knowledge_store_releases_database_file(tmp_path):
    import os

    db = tmp_path / "knowledge.db"
    engine = KnowledgeEngine(db)
    engine.upsert_entity(
        Entity(name="Lock Test", category="concept")
    )
    assert engine.store.count() == 1

    moved = tmp_path / "knowledge-moved.db"
    os.replace(db, moved)
    assert moved.exists()


def test_multivalue_filter_does_not_match_description_only(tmp_path):
    engine = make_engine(tmp_path)
    engine.upsert_entity(
        Entity(
            name="Jean Grey",
            category="character",
            universe="Marvel",
            powers=["telepatia"],
        )
    )
    engine.upsert_entity(
        Entity(
            name="Professor Example",
            category="character",
            universe="Marvel",
            description="Estuda telepatia, mas não possui esse poder.",
            powers=["inteligência"],
        )
    )

    matches = engine.search_entities("", {"power": "telepatia"})
    assert [entity.name for entity in matches] == ["Jean Grey"]


def test_structured_team_and_affiliation_answers(tmp_path):
    engine = make_engine(tmp_path)
    engine.upsert_entity(
        Entity(
            name="Jean Grey",
            category="character",
            universe="Marvel",
            team=["X-Men"],
            affiliations=["X-Men", "Quiet Council"],
            powers=["telepatia"],
        )
    )

    assert "X-Men" in engine.answer("quais equipes da Jean Grey?")
    affiliation = engine.answer("quais afiliações da Jean Grey?")
    assert "X-Men" in affiliation
    assert "Quiet Council" in affiliation


def test_group_query_uses_structured_team_and_trait_filters(tmp_path):
    engine = make_engine(tmp_path)
    engine.upsert_entity(
        Entity(
            name="Jean Grey",
            category="character",
            universe="Marvel",
            team=["X-Men"],
            powers=["telepatia"],
        )
    )
    engine.upsert_entity(
        Entity(
            name="Example",
            category="character",
            universe="Marvel",
            team=["X-Men"],
            description="Pesquisa telepatia sem possuir esse poder.",
            powers=["inteligência"],
        )
    )

    answer = engine.answer("quais personagens dos X-Men possuem telepatia?")
    assert "Jean Grey" in answer
    assert "Example" not in answer


def test_resolve_entity_universe_is_case_insensitive(tmp_path):
    engine = make_engine(tmp_path)
    engine.upsert_entity(
        Entity(
            name="Batman",
            category="character",
            universe="DC",
        )
    )
    assert engine.resolve_entity("Batman", universe="dc").name == "Batman"


def test_relationship_filter_uses_structured_index(tmp_path):
    engine = make_engine(tmp_path)
    engine.upsert_entity(
        Entity(
            name="Batman",
            category="character",
            universe="DC",
            relationships=[Relationship("ally", "Robin")],
        )
    )
    engine.upsert_entity(
        Entity(
            name="Example",
            category="character",
            universe="DC",
            description="Leu histórias sobre Robin.",
        )
    )

    matches = engine.search_entities("", {"relationship": "Robin"})
    assert [entity.name for entity in matches] == ["Batman"]


def test_multivalue_index_migrates_existing_entities(tmp_path):
    db = tmp_path / "knowledge.db"
    engine = KnowledgeEngine(db)
    engine.upsert_entity(
        Entity(
            name="Storm",
            category="character",
            universe="Marvel",
            team=["X-Men"],
            powers=["controle climático"],
            relationships=[Relationship("ally", "Wolverine")],
        )
    )

    with engine.store._connect() as connection:
        connection.execute("DELETE FROM entity_values")
        connection.execute(
            "DELETE FROM knowledge_meta WHERE key = ?",
            ("entity_values_schema",),
        )

    migrated = KnowledgeEngine(db)
    assert migrated.search_entities("", {"team": "X-Men"})[0].name == "Storm"
    assert migrated.search_entities("", {"power": "controle climático"})[0].name == "Storm"
    assert migrated.search_entities("", {"relationship": "Wolverine"})[0].name == "Storm"
