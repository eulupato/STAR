from core.chemistry_knowledge_500k import (
    CONTEXTS,
    FAMILIES,
    STYLES,
    TOTAL_DOMAINS,
    TOTAL_TOPICS,
    TOTAL_VARIANTS,
    TOPICS,
    TOPICS_PER_DOMAIN,
    ChemistryKnowledgeEngine,
)
from core.executive import Executive


def test_chemistry_catalog_exact_size():
    engine = ChemistryKnowledgeEngine()
    stats = engine.stats()
    assert TOTAL_TOPICS == 500
    assert TOTAL_VARIANTS == 500000
    assert stats["canonical_topics"] == 500
    assert stats["content_variations"] == 500000
    assert stats["variants_per_topic"] == 1000


def test_chemistry_domains_are_exactly_20_by_25():
    stats = ChemistryKnowledgeEngine().stats()
    assert TOTAL_DOMAINS == 20
    assert TOPICS_PER_DOMAIN == 25
    assert stats["domains"] == 20
    assert len(stats["domain_counts"]) == 20
    assert set(stats["domain_counts"].values()) == {25}


def test_chemistry_variation_axes_are_10x10x10():
    assert len(FAMILIES) == 10
    assert len(STYLES) == 10
    assert len(CONTEXTS) == 10
    assert len(FAMILIES) * len(STYLES) * len(CONTEXTS) == 1000


def test_chemistry_ids_first_last_and_invalid():
    engine = ChemistryKnowledgeEngine()
    assert engine.content_id(0, 0) == "CHEM-000001"
    assert engine.content_id(499, 999) == "CHEM-500000"
    assert engine.get_variant("CHEM-000001")["topic_id"] == "matter_classification"
    assert engine.get_variant("CHEM-500000")["topic_id"] == "multiscale_chemistry"
    assert engine.get_variant("CHEM-000000") is None
    assert engine.get_variant("CHEM-500001") is None
    assert engine.get_variant("PHYS-000001") is None


def test_each_canonical_topic_owns_exactly_1000_ids():
    engine = ChemistryKnowledgeEngine()
    first_topic_last = engine.get_variant("CHEM-001000")
    second_topic_first = engine.get_variant("CHEM-001001")
    assert first_topic_last["topic_id"] == TOPICS[0].id
    assert second_topic_first["topic_id"] == TOPICS[1].id


def test_molarity_formula_match():
    engine = ChemistryKnowledgeEngine()
    topic = engine.match("qual é a fórmula da molaridade?")
    assert topic is not None
    assert topic.id == "molarity"
    answer = engine.answer("qual é a fórmula da molaridade?")
    assert "c=n/V" in answer


def test_nernst_specific_match():
    engine = ChemistryKnowledgeEngine()
    topic = engine.match("explique a equação de Nernst")
    assert topic is not None
    assert topic.id == "nernst_equation"
    assert "RT/nF" in engine.answer("qual a equação de Nernst?")


def test_beer_lambert_specific_match():
    engine = ChemistryKnowledgeEngine()
    topic = engine.match("lei de Beer Lambert")
    assert topic is not None
    assert topic.id == "beer_lambert"
    assert "A=εbc" in engine.answer("qual a formula de Beer Lambert")


def test_sn2_match():
    engine = ChemistryKnowledgeEngine()
    topic = engine.match("explique SN2")
    assert topic is not None
    assert topic.id == "sn2"
    assert "concertado" in engine.answer("explique SN2")


def test_hartree_fock_advanced_match():
    engine = ChemistryKnowledgeEngine()
    topic = engine.match("o que é Hartree-Fock?")
    assert topic is not None
    assert topic.id == "hartree_fock"
    assert topic.level == 5


def test_photocatalysis_match():
    engine = ChemistryKnowledgeEngine()
    topic = engine.match("como funciona fotocatálise?")
    assert topic is not None
    assert topic.id == "photocatalysis"


def test_radiolysis_water_match():
    engine = ChemistryKnowledgeEngine()
    topic = engine.match("explique radiólise da água")
    assert topic is not None
    assert topic.id == "radiolysis_water"
    assert topic.level == 4


def test_unrelated_question_is_not_claimed():
    engine = ChemistryKnowledgeEngine()
    assert engine.match("qual é a capital do Japão?") is None
    assert engine.answer("qual é a capital do Japão?") is None


def test_variant_is_deterministic():
    engine = ChemistryKnowledgeEngine()
    a = engine.get_variant("CHEM-123456")
    b = engine.get_variant("CHEM-123456")
    assert a == b
    assert a["id"] == "CHEM-123456"


def test_executive_uses_chemistry_before_generic_fallback():
    chemistry = ChemistryKnowledgeEngine()
    executive = Executive(chemistry_knowledge=chemistry)
    answer = executive.execute({"input": "qual a equação de Nernst?"}, route=None)
    assert "Nernst" in answer
    assert "RT/nF" in answer
