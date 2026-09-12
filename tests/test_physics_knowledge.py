from core.executive import Executive
from core.physics_knowledge import PhysicsKnowledgeEngine, TOPICS


def test_physics_catalog_has_exactly_50k_variants():
    physics = PhysicsKnowledgeEngine()
    stats = physics.stats()
    assert len(TOPICS) == 50
    assert len({topic.id for topic in TOPICS}) == 50
    assert stats["canonical_topics"] == 50
    assert stats["variants_per_topic"] == 1000
    assert stats["content_variations"] == 50000
    assert stats["families"] == 10
    assert stats["styles"] == 10
    assert stats["contexts"] == 10


def test_content_id_boundaries_are_exact():
    physics = PhysicsKnowledgeEngine()
    assert physics.content_id(0, 0) == "PHYS-00001"
    assert physics.content_id(49, 999) == "PHYS-50000"
    assert physics.get_variant("PHYS-00000") is None
    assert physics.get_variant("PHYS-50001") is None


def test_first_and_last_variants_are_deterministic():
    physics = PhysicsKnowledgeEngine()
    first = physics.get_variant("PHYS-00001")
    last = physics.get_variant("PHYS-50000")
    assert first["topic_id"] == "dimensional_analysis"
    assert first["family"] == "conceito"
    assert first["style"] == "direto"
    assert first["context"] == "definicao"
    assert last["topic_id"] == "hubble_critical"
    assert last["family"] == "conexoes"
    assert last["style"] == "revisao"
    assert last["context"] == "checagem"


def test_basic_physics_formula_answer():
    physics = PhysicsKnowledgeEngine()
    answer = physics.answer("qual a fórmula da segunda lei de Newton?")
    assert answer is not None
    assert "ΣF=ma" in answer
    assert "Segunda lei de Newton" in answer


def test_extreme_advanced_general_relativity_answer():
    physics = PhysicsKnowledgeEngine()
    answer = physics.answer("explique as equações de campo de Einstein")
    assert answer is not None
    assert "G_{μν}" in answer
    assert "nível 5" in answer


def test_quantum_field_theory_is_present():
    physics = PhysicsKnowledgeEngine()
    answer = physics.answer("qual a equação de Euler Lagrange para teoria quantica de campos?")
    assert answer is not None
    assert "∂L/∂φ" in answer
    assert "Particle Data Group" in answer


def test_unknown_subject_does_not_get_forced_into_physics():
    physics = PhysicsKnowledgeEngine()
    assert physics.answer("qual é a capital do Japão?") is None


def test_executive_uses_physics_before_generic_fallback():
    physics = PhysicsKnowledgeEngine()
    executive = Executive(physics_knowledge=physics)
    answer = executive.execute({"input": "fórmula da lei de Coulomb"}, {"response_type": "local"})
    assert "Coulomb" in answer
    assert "abs(q1q2)" in answer
