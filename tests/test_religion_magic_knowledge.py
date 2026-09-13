from core.religion_magic_knowledge import ReligionMagicKnowledgeEngine


def test_cultural_engine_has_exact_5m_addressable_contents():
    engine = ReligionMagicKnowledgeEngine()
    stats = engine.stats()
    assert stats["subjects"] == 125
    assert stats["religion_subjects"] == 100
    assert stats["magic_esotericism_subjects"] == 25
    assert stats["aspects_per_subject"] == 40
    assert stats["canonical_nodes"] == 5_000
    assert stats["variations_per_node"] == 1_000
    assert stats["total_addressable_contents"] == 5_000_000


def test_cultural_ids_preserve_boundaries_without_materializing_millions():
    engine = ReligionMagicKnowledgeEngine()
    assert engine.materialize(1, 1)["id"] == "RCM-0001-0001"
    assert engine.materialize(5_000, 1_000)["id"] == "RCM-5000-1000"


def test_magic_is_framed_as_cultural_history_not_physics():
    engine = ReligionMagicKnowledgeEngine()
    result = engine.answer("história da magia cerimonial")
    assert result is not None
    assert "Magia cerimonial" in result
    assert "não apresentadas como mecanismo físico estabelecido" in result
    assert engine.stats()["claims_supernatural_as_science"] is False


def test_religion_resolution_covers_global_traditions():
    engine = ReligionMagicKnowledgeEngine()
    for query, expected in (
        ("história do xintoísmo", "Xintoísmo"),
        ("rituais do candomblé", "Candomblé"),
        ("textos do judaísmo", "Judaísmo"),
        ("origens do budismo theravada", "Theravāda"),
        ("cosmologia yorùbá", "Yorùbá"),
    ):
        answer = engine.answer(query)
        assert answer is not None
        assert expected in answer


def test_sensitive_indigenous_knowledge_is_not_reconstructed():
    engine = ReligionMagicKnowledgeEngine()
    resolved = engine.resolve_subject("rituais Diné Navajo")
    assert resolved is not None
    index, _subject, _score = resolved
    canonical = (index - 1) * 40 + 14
    item = engine.materialize(canonical, 1)
    assert "Não reconstrua cerimônias fechadas" in item["access_guidance"]
    assert engine.stats()["restricted_knowledge_reconstruction"] is False


def test_generic_overviews_are_available():
    engine = ReligionMagicKnowledgeEngine()
    assert "100 tradições" in engine.answer("religiões")
    assert "25 campos" in engine.answer("magia")
