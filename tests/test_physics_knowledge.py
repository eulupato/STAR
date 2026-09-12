from core.executive import Executive
from core.physics_knowledge_150k import (
    ADDED_TOPICS,
    ADDED_VARIANTS,
    BASE_TOPICS,
    PhysicsKnowledgeEngine,
    TOPICS,
)


def test_physics_catalog_has_exactly_150k_variants():
    physics = PhysicsKnowledgeEngine()
    stats = physics.stats()
    assert len(BASE_TOPICS) == 50
    assert ADDED_TOPICS == 100
    assert ADDED_VARIANTS == 100000
    assert len(TOPICS) == 150
    assert len({topic.id for topic in TOPICS}) == 150
    assert stats["canonical_topics"] == 150
    assert stats["base_topics"] == 50
    assert stats["added_topics"] == 100
    assert stats["variants_per_topic"] == 1000
    assert stats["base_content_variations"] == 50000
    assert stats["added_content_variations"] == 100000
    assert stats["content_variations"] == 150000
    assert stats["families"] == 10
    assert stats["styles"] == 10
    assert stats["contexts"] == 10


def test_content_id_boundaries_preserve_old_ids_and_add_new_range():
    physics = PhysicsKnowledgeEngine()
    assert physics.content_id(0, 0) == "PHYS-00001"
    assert physics.content_id(49, 999) == "PHYS-50000"
    assert physics.content_id(50, 0) == "PHYS-50001"
    assert physics.content_id(149, 999) == "PHYS-150000"
    assert physics.get_variant("PHYS-00000") is None
    assert physics.get_variant("PHYS-150001") is None


def test_legacy_50k_boundary_stays_deterministic():
    physics = PhysicsKnowledgeEngine()
    first = physics.get_variant("PHYS-00001")
    legacy_last = physics.get_variant("PHYS-50000")
    assert first["topic_id"] == "dimensional_analysis"
    assert first["family"] == "conceito"
    assert first["style"] == "direto"
    assert first["context"] == "definicao"
    assert legacy_last["topic_id"] == "hubble_critical"
    assert legacy_last["family"] == "conexoes"
    assert legacy_last["style"] == "revisao"
    assert legacy_last["context"] == "checagem"


def test_new_100k_range_is_deterministic():
    physics = PhysicsKnowledgeEngine()
    first_new = physics.get_variant("PHYS-50001")
    last = physics.get_variant("PHYS-150000")
    assert first_new["topic_id"] == "kinematic_vectors"
    assert first_new["title"] == "Vetores cinemáticos"
    assert first_new["family"] == "conceito"
    assert last["topic_id"] == "chirp_mass"
    assert last["title"] == "Massa chirp em binárias"
    assert last["family"] == "conexoes"
    assert last["style"] == "revisao"
    assert last["context"] == "checagem"


def test_basic_physics_formula_answer():
    physics = PhysicsKnowledgeEngine()
    answer = physics.answer("qual a fórmula da segunda lei de Newton?")
    assert answer is not None
    assert "ΣF=ma" in answer
    assert "Segunda lei de Newton" in answer


def test_advanced_fluid_dynamics_is_present():
    physics = PhysicsKnowledgeEngine()
    answer = physics.answer("explique as equações de Navier Stokes")
    assert answer is not None
    assert "Navier-Stokes" in answer
    assert "∇p" in answer
    assert "nível 5" in answer


def test_quantum_relativistic_and_qft_topics_are_present():
    physics = PhysicsKnowledgeEngine()
    dirac = physics.answer("qual a equação de Dirac?")
    qed = physics.answer("explique a lagrangiana da QED")
    assert dirac is not None and "γ^μ" in dirac
    assert qed is not None and "F_{μν}" in qed
    assert "Particle Data Group" in qed


def test_gravitational_wave_topic_uses_ligo_reference():
    physics = PhysicsKnowledgeEngine()
    answer = physics.answer("explique ondas gravitacionais")
    assert answer is not None
    assert "Ondas gravitacionais" in answer
    assert "LIGO Scientific Collaboration" in answer


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


def test_executive_uses_expanded_physics_before_generic_fallback():
    physics = PhysicsKnowledgeEngine()
    executive = Executive(physics_knowledge=physics)
    answer = executive.execute({"input": "explique o critério de Lawson na fusão"}, {"response_type": "local"})
    assert "Lawson" in answer
    assert "IAEA" in answer
