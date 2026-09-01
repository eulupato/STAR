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
