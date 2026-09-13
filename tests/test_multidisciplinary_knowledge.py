from core.multidisciplinary_knowledge import MultidisciplinaryKnowledgeEngine
from core.multidisciplinary_taxonomy import SUBJECT_ORDER, SUBJECTS
from core.thematic_voice import (
    THEMATIC_VOICE_VARIATIONS,
    parse_thematic_voice,
    thematic_voice_id,
    thematic_voice_stats,
    thematic_voice_variant,
)
from main import create_star


def test_exact_multidisciplinary_counts():
    engine = MultidisciplinaryKnowledgeEngine()
    stats = engine.stats()
    assert stats["subjects"] == 13
    assert stats["canonical_nodes_per_subject"] == 500
    assert stats["canonical_nodes"] == 6500
    assert stats["variants_per_node"] == 1000
    assert stats["contents_per_subject"] == 500000
    assert stats["total_content_variations"] == 6500000


def test_each_subject_has_25_macroareas_and_500k():
    engine = MultidisciplinaryKnowledgeEngine()
    for subject in SUBJECT_ORDER:
        assert len(SUBJECTS[subject]["areas"]) == 25
        assert engine.content_id(subject, 0, 0).endswith("-000001")
        assert engine.content_id(subject, 499, 999).endswith("-500000")


def test_addressable_variants_cover_every_subject_boundary():
    engine = MultidisciplinaryKnowledgeEngine()
    for subject in SUBJECT_ORDER:
        prefix = SUBJECTS[subject]["prefix"]
        first = engine.get_variant(f"{prefix}-000001")
        last = engine.get_variant(f"{prefix}-500000")
        assert first and first["subject"] == subject
        assert last and last["subject"] == subject
        assert first["id"].endswith("000001")
        assert last["id"].endswith("500000")


def test_representative_subject_routing():
    engine = MultidisciplinaryKnowledgeEngine()
    cases = {
        "explique SIG e análise espacial em geografia": "geography",
        "curiosidade sobre Roma e mundo romano na história": "history",
        "explique teoria dos grafos em matemática": "mathematics",
        "como funciona genética molecular em biologia": "biology",
        "calcule flexão de vigas em mecânica": "mechanics",
        "gestão de requisitos em engenharia": "engineering",
        "complexidade computacional em computação": "computing",
        "redes corporativas em TI": "it",
        "explique lógica modal": "logic",
        "psicometria em psicologia": "psychology_sociology",
        "explique UTF-8 e decodificação": "decoding",
        "reprodutibilidade na ciência": "science",
        "epistemologia na filosofia": "philosophy",
    }
    for query, subject in cases.items():
        resolved = engine.resolve(query)
        assert resolved is not None, query
        assert resolved["subject"] == subject, (query, resolved)


def test_history_curiosity_uses_evidence_policy_and_hidden_angle():
    engine = MultidisciplinaryKnowledgeEngine()
    answer = engine.answer("curiosidade pouco ensinada sobre Roma e mundo romano na história")
    assert answer is not None
    assert "fonte primária" in answer.lower()
    assert "grafites" in answer.lower()
    assert "hipóteses" in answer.lower() or "disputas" in answer.lower()


def test_decoding_is_defensive_not_bypass_catalog():
    engine = MultidisciplinaryKnowledgeEngine()
    answer = engine.answer("explique criptografia simétrica e assimétrica em decodificação")
    assert answer is not None
    low = answer.lower()
    assert "defensiva" in low
    assert "quebra de credenciais" in low


def test_psychology_has_non_diagnostic_boundary():
    engine = MultidisciplinaryKnowledgeEngine()
    answer = engine.answer("explique psicologia cognitiva")
    assert answer is not None
    assert "não produzem diagnóstico" in answer.lower()


def test_thematic_voice_catalog_is_exactly_one_million():
    stats = thematic_voice_stats()
    assert THEMATIC_VOICE_VARIATIONS == 1_000_000
    assert stats["variations"] == 1_000_000
    assert thematic_voice_id(0) == "VOICE-STUDY-0000001"
    assert thematic_voice_id(999_999) == "VOICE-STUDY-1000000"


def test_thematic_voice_variants_are_addressable_and_distinct():
    samples = [thematic_voice_variant(i) for i in (0, 1, 9, 10, 999, 123456, 999999)]
    assert len({x["id"] for x in samples}) == len(samples)
    assert len({x["phrase"] for x in samples}) == len(samples)
    assert all(x["topic"] for x in samples)


def test_thematic_voice_parser_accepts_natural_study_commands():
    match = parse_thematic_voice("STAR, me ensine lógica modal do zero")
    assert match is not None
    assert "logica modal" in match.query.lower()
    match2 = parse_thematic_voice("Ei STAR, aprofunde genética molecular no nível de pesquisa")
    assert match2 is not None
    assert "genetica molecular" in match2.query.lower()


def test_star_core_exposes_and_uses_multidisciplinary_engine():
    star = create_star()
    assert hasattr(star, "multidisciplinary")
    assert star.multidisciplinary.stats()["total_content_variations"] == 6_500_000
    answer = star.process("STAR, me ensine lógica modal do zero")
    assert "Lógica modal" in answer


def test_existing_specific_science_engines_stay_available():
    star = create_star()
    physics = star.process("qual a fórmula da segunda lei de Newton?")
    chemistry = star.process("qual a equação de Nernst?")
    assert "Newton" in physics or "F=" in physics or "ma" in physics
    assert "Nernst" in chemistry or "RT" in chemistry


def test_unrelated_question_is_not_forced_into_multidisciplinary_catalog():
    engine = MultidisciplinaryKnowledgeEngine()
    assert engine.resolve("qual é a capital do Japão?") is None