from core.curriculum_knowledge import (
    CONCEPTS,
    TOTAL_NEW_ADDRESSABLE,
    VARIATIONS_PER_ITEM,
    CurriculumKnowledgeEngine,
)


def _concept(label: str):
    wanted = label.casefold()
    return next(item for item in CONCEPTS if item.label.casefold() == wanted)


def test_curriculum_has_56_real_themes_and_one_million_per_item():
    engine = CurriculumKnowledgeEngine()
    stats = engine.stats()
    assert stats["themes"] == 56
    assert stats["variations_per_theme"] == 1_000_000
    assert stats["variations_per_concept"] == 1_000_000
    assert stats["raw_topic_mentions"] > stats["unique_concepts"]
    assert stats["deduplicated_mentions"] > 0
    assert stats["unique_concepts"] > 400
    assert stats["total_new_addressable_contents"] == (
        stats["themes"] + stats["unique_concepts"]
    ) * 1_000_000
    assert stats["total_new_addressable_contents"] == TOTAL_NEW_ADDRESSABLE


def test_curriculum_ids_cover_full_million_without_materializing_it():
    engine = CurriculumKnowledgeEngine()
    first_theme = engine.materialize_theme(1, 1)
    last_theme = engine.materialize_theme(56, VARIATIONS_PER_ITEM)
    first_concept = engine.materialize_concept(1, 1)
    last_concept = engine.materialize_concept(len(CONCEPTS), VARIATIONS_PER_ITEM)
    assert first_theme["id"] == "CURRT-001-0000001"
    assert last_theme["id"] == "CURRT-056-1000000"
    assert first_concept["id"].endswith("-0000001")
    assert last_concept["id"].endswith("-1000000")


def test_repeated_topics_are_one_canonical_concept_with_many_memberships():
    vision = _concept("visão computacional")
    assert set((27, 41, 44)).issubset(set(vision.theme_ids))
    fusion = _concept("fusão nuclear")
    assert set((17, 37, 55)).issubset(set(fusion.theme_ids))
    sensors = _concept("sensores")
    assert set((24, 27, 28, 47)).issubset(set(sensors.theme_ids))


def test_aliases_do_not_create_duplicate_wormhole_or_fea_concepts():
    engine = CurriculumKnowledgeEngine()
    wormhole = _concept("buracos de minhoca")
    resolved = engine.resolve("wormholes")
    assert resolved is not None
    assert resolved.kind == "concept"
    assert resolved.item_id == wormhole.index

    fea = _concept("análise por elementos finitos")
    resolved_fea = engine.resolve("FEA")
    assert resolved_fea is not None
    assert resolved_fea.item_id == fea.index


def test_programming_c_and_cpp_remain_distinct_concepts():
    c_lang = _concept("C")
    cpp = _concept("C++")
    assert c_lang.index != cpp.index
    assert c_lang.key != cpp.key


def test_frontier_topics_keep_evidence_status_instead_of_becoming_facts():
    engine = CurriculumKnowledgeEngine()
    wormhole = _concept("buracos de minhoca")
    warp = _concept("métricas de warp")
    teleport = _concept("teletransporte quântico")
    fusion = _concept("fusão nuclear")
    assert wormhole.evidence_class == "theoretical"
    assert warp.evidence_class == "theoretical"
    assert teleport.evidence_class == "established-quantum-state-protocol"
    assert fusion.evidence_class == "experimental-engineering"

    answer = engine.materialize_concept(wormhole.index, 1)["answer"]
    assert "física teórica" in answer


def test_meta_priority_and_invention_views_do_not_create_duplicate_bases():
    stats = CurriculumKnowledgeEngine().stats()
    assert stats["priority_view_items"] == 17
    assert stats["learning_core_items"] == 25
    assert stats["invention_cycle_steps"] == 14


def test_new_specific_topics_resolve_without_replacing_broad_domains():
    engine = CurriculumKnowledgeEngine()
    for query in (
        "MBSE",
        "TEVV de IA",
        "equação TOV",
        "amplificação lock-in",
        "cônicas remendadas",
        "beamforming",
    ):
        resolved = engine.resolve(query)
        assert resolved is not None, query
        assert resolved.kind == "concept"


def test_theme_report_assigns_every_concept_to_at_least_one_area():
    engine = CurriculumKnowledgeEngine()
    reports = engine.theme_report()
    assert len(reports) == 56
    assert all(row["unique_concepts"] > 0 for row in reports)
    assert all(concept.primary_owner for concept in engine.concepts)
    assert all(concept.theme_ids for concept in engine.concepts)
    assert all(concept.sources for concept in engine.concepts)


def test_main_wires_curriculum_without_breaking_legacy_routes(tmp_path, monkeypatch):
    # A criação do Core é suficiente; não abre GUI nem inicia gateway.
    monkeypatch.setenv("STAR_RUNTIME_DIR", str(tmp_path))
    from main import create_star

    star = create_star()
    assert hasattr(star, "curriculum")
    assert star.curriculum.stats()["themes"] == 56

    broad = str(star.process("energia"))
    assert "CURRÍCULO" not in broad

    specific = str(star.process("explique MBSE"))
    assert "MBSE" in specific
    assert "Modo=" not in specific


def test_curriculum_foundations_cover_all_56_themes_with_real_content():
    from core.curriculum_foundations import render_theme_foundation

    engine = CurriculumKnowledgeEngine()
    stats = engine.stats()
    assert stats["factual_foundations"] == 56
    assert stats["verified_fact_records"] >= 50
    assert stats["country_capitals"] >= 70
    assert stats["factual_sources"] >= 20

    for theme_id in range(1, 57):
        answer = render_theme_foundation(theme_id)
        assert len(answer) > 120
        assert "•" in answer


def test_basic_general_knowledge_is_answered_locally():
    engine = CurriculumKnowledgeEngine()
    cases = {
        "qual é a capital da França?": ("Paris",),
        "quantos ossos o corpo humano tem?": ("206",),
        "para que serve o coração?": ("sangue", "pulmões"),
        "qual é a função do pulmão?": ("oxigênio", "dióxido de carbono"),
        "quem é Michael Jackson?": ("cantor", "Thriller", "1958"),
        "em que época os dinossauros existiram?": ("245", "66", "Mesozoica"),
        "quantos planetas tem o Sistema Solar?": ("oito",),
        "o que é DNA?": ("informação genética",),
        "qual é a fórmula da água?": ("H₂O",),
        "o que são placas tectônicas?": ("litosfera", "movem"),
        "qual é o maior oceano?": ("Pacífico",),
        "qual é a velocidade da luz?": ("299 792 458",),
        "qual é a capital da Suécia?": ("Estocolmo",),
    }
    for question, expected in cases.items():
        answer = engine.answer(question)
        assert answer is not None, question
        for fragment in expected:
            assert fragment.casefold() in answer.casefold(), (question, answer)


def test_foundational_answer_can_expose_real_source_when_requested():
    engine = CurriculumKnowledgeEngine()
    answer = engine.answer("qual é a capital da França? cite a fonte")
    assert "Paris" in answer
    assert "European Union" in answer
    assert "https://" in answer


def test_all_canonical_concepts_have_real_basic_content_not_metadata_only():
    engine = CurriculumKnowledgeEngine()
    stats = engine.stats()
    assert stats["concept_foundations"] == stats["unique_concepts"]
    assert stats["unique_concepts"] == len(CONCEPTS)

    for concept in CONCEPTS:
        answer = engine.materialize_concept(concept.index, 1)["answer"]
        assert len(answer) > 180, concept.label
        assert concept.label.casefold() in answer.casefold()
        assert "Modo=" not in answer
        assert "profundidade=" not in answer
        assert "Ponto-chave relacionado:" in answer


def test_concept_source_request_uses_real_foundation_urls():
    engine = CurriculumKnowledgeEngine()
    answer = engine.answer("explique neurônios e cite fontes")
    assert answer is not None
    assert "neurônios" in answer.casefold()
    assert "NCBI" in answer or "OpenStax" in answer
    assert "https://" in answer
