from core.knowledge_expansion_15m import (
    COMBINED_KNOWLEDGE_TOTAL,
    DOMAIN_ORDER,
    PLUS_CONTENTS_PER_DOMAIN,
    PLUS_TOTAL,
    KnowledgeExpansion15MEngine,
)
from main import create_star


def test_plus_exact_global_counts():
    engine = KnowledgeExpansion15MEngine()
    stats = engine.stats()
    assert stats["domains"] == 15
    assert stats["added_canonical_nodes_per_domain"] == 1000
    assert stats["added_content_variations_per_domain"] == 1_000_000
    assert PLUS_CONTENTS_PER_DOMAIN == 1_000_000
    assert PLUS_TOTAL == 15_000_000
    assert stats["added_content_variations"] == 15_000_000
    assert COMBINED_KNOWLEDGE_TOTAL == 22_150_000
    assert stats["combined_content_variations"] == 22_150_000


def test_every_domain_has_exactly_one_million_new_ids():
    engine = KnowledgeExpansion15MEngine()
    for domain in DOMAIN_ORDER:
        first = engine.content_id(domain, 0, 0)
        last = engine.content_id(domain, 999, 999)
        assert first.endswith("-0000001"), (domain, first)
        assert last.endswith("-1000000"), (domain, last)
        assert engine.get_variant(first)["domain"] == domain
        assert engine.get_variant(last)["domain"] == domain


def test_plus_ids_do_not_collide_with_legacy_ranges():
    engine = KnowledgeExpansion15MEngine()
    prefixes = engine.stats()["prefixes"]
    assert prefixes["physics"] == "PHYSX"
    assert prefixes["chemistry"] == "CHEMX"
    assert prefixes["geography"] == "GEOX"
    assert all(prefix.endswith("X") for prefix in prefixes.values())


def test_multidisciplinary_new_lenses_are_research_useful():
    engine = KnowledgeExpansion15MEngine()
    answer = engine.answer("em geografia aprofunde cartografia e projeções com incerteza")
    assert answer is not None
    low = answer.lower()
    assert "geografia" in low
    assert "cartografia" in low
    assert "incerteza" in low


def test_physics_and_chemistry_deep_topics_resolve():
    engine = KnowledgeExpansion15MEngine()
    physics = engine.answer("em física, aprofunde Hamiltonian mechanics com derivação rigorosa")
    chemistry = engine.answer("em química, aprofunde photoredox chemistry no nível de pesquisa")
    assert physics and "Física" in physics and "Hamiltonian" in physics
    assert chemistry and "Química" in chemistry and "Photoredox" in chemistry


def test_domain_policies_survive_plus_layer():
    engine = KnowledgeExpansion15MEngine()
    history = engine.answer("em história aprofunde História do Brasil com fontes primárias")
    psychology = engine.answer("em psicologia aprofunde psicometria com validação")
    decoding = engine.answer("em decodificação aprofunde UTF-8 com segurança")
    assert history and "fonte primária" in history.lower()
    assert psychology and "não como diagnóstico" in psychology.lower()
    assert decoding and "educacional/defensivo" in decoding.lower()


def test_plus_prefers_explicit_depth_requests_only():
    engine = KnowledgeExpansion15MEngine()
    assert engine.prefers("aprofunde lógica modal no nível de pesquisa")
    assert engine.prefers("mostre benchmarks e incerteza")
    assert not engine.prefers("explique lógica modal")


def test_star_exposes_plus_and_preserves_legacy_engines():
    star = create_star()
    assert star.knowledge_plus.stats()["added_content_variations"] == 15_000_000
    plus = star.process("STAR, aprofunde cartografia e projeções em geografia com incerteza")
    physics = star.process("qual a fórmula da segunda lei de Newton?")
    chemistry = star.process("qual a equação de Nernst?")
    assert "PLUS" in plus
    assert "Newton" in physics or "F=" in physics or "ma" in physics
    assert "Nernst" in chemistry or "RT" in chemistry


def test_unrelated_query_is_not_forced_into_plus():
    engine = KnowledgeExpansion15MEngine()
    assert engine.resolve("qual é a capital do Japão?") is None
