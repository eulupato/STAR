from uuid import uuid4

import pytest

from core.mind import CognitiveSuite
from core.scientific_foundations import (
    REQUESTED_SCIENTIFIC_CONTENT,
    SCIENTIFIC_ADDRESSABLE_CONTENTS,
    SCIENTIFIC_BRANCHES,
    SCIENTIFIC_CANONICAL_NODES,
    SCIENTIFIC_DOMAINS,
    SCIENTIFIC_LENSES,
    SCIENTIFIC_VARIANTS_PER_NODE,
    ScientificCatalog,
    ScientificFoundations,
)
from core.star_core import StarCore
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _science():
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    science = ScientificFoundations(knowledge, reasoner=suite.science)
    return science, knowledge, suite


def _canonical_fact(suite: CognitiveSuite, marker: str, text: str | None = None):
    source_id = suite.epistemics.register_source(
        f"unit://science/{marker}",
        source_type="test",
        title=f"Fonte científica {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        text or f"Conhecimento científico canônico validado {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://science-claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência científica independente {marker}",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
        reliability=1.0,
    )
    suite.epistemics.transition(
        record["record_id"],
        "VERIFIED",
        reason="evidência científica rastreável suficiente para teste",
        actor="unit-test",
    )
    return suite.epistemics.transition(
        record["record_id"],
        "CANONICAL",
        reason="claim científico apto a conhecimento canônico",
        actor="unit-test",
    )


def test_block5_catalog_is_exactly_1b_and_has_requested_domains():
    catalog = ScientificCatalog()
    stats = catalog.stats()

    assert len(SCIENTIFIC_DOMAINS) == 13
    assert set(SCIENTIFIC_DOMAINS) == {
        "logic", "mathematics", "statistics", "scientific_method", "physics",
        "chemistry", "biology", "geology", "astronomy", "climatology",
        "ecology", "fauna", "flora",
    }
    assert len(SCIENTIFIC_BRANCHES) == 50
    assert len(SCIENTIFIC_LENSES) == 20
    assert SCIENTIFIC_CANONICAL_NODES == 1_000
    assert SCIENTIFIC_VARIANTS_PER_NODE == 1_000_000
    assert SCIENTIFIC_ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["addressable_contents"] == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_knowledge_rows"] == 0

    assert catalog.content_id(0, 0) == "SCI-B05-0000000001"
    assert catalog.content_id(999, 999_999) == "SCI-B05-1000000000"
    assert catalog.get_variant("SCI-B05-1000000001") is None


def test_block5_contains_every_requested_scientific_content_kind():
    required = {
        "concept", "law", "theory", "formula", "equation", "experiment",
        "property", "unit", "constant", "relation", "discovery", "method",
        "evidence", "exception", "application", "problem", "solution", "subdiscipline",
    }
    assert required == set(REQUESTED_SCIENTIFIC_CONTENT)
    variant = ScientificCatalog().get_variant("SCI-B05-0000000001")
    assert variant["domain"] == "logic"
    assert variant["branch"] == "formal_logic"
    assert variant["lens"] == "concept"
    assert variant["subbranches"]
    assert "evidência" in variant["prompt"]


def test_block5_registers_b05_on_same_universal_architecture():
    science, knowledge, _suite = _science()
    namespace = knowledge.store.get_namespace("B05")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert science.knowledge is knowledge
    assert science.graph is knowledge.graph
    assert science.stats()["knowledge_graph"] == "shared knowledge_nodes/knowledge_edges"


def test_scientific_taxonomy_materializes_into_shared_knowledge_graph():
    science, _knowledge, suite = _science()
    result = science.materialize_taxonomy("physics")
    assert result["knowledge_graph"] == "shared"
    assert result["branches_materialized"] == 6

    root_neighbors = suite.graph.neighbors("SCI-TAX-ROOT", relation="has_part")
    assert any(item["label"] == "Física" for item in root_neighbors)

    domain_neighbors = suite.graph.neighbors("SCI-DOM-PHYSICS", relation="has_part")
    labels = {item["label"] for item in domain_neighbors}
    assert "Mecânica clássica" in labels
    assert "Eletromagnetismo" in labels

    branch_neighbors = suite.graph.neighbors("SCI-BR-CLASSICAL_MECHANICS", relation="has_part")
    assert any(item["node_type"] == "science_subbranch" for item in branch_neighbors)


def test_scientific_canonical_knowledge_uses_block2_gate_block3_and_graph():
    science, knowledge, suite = _science()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(
        f"unit://science-discovered/{marker}",
        source_type="test",
        reliability=1.0,
    )
    discovered = suite.epistemics.discover(
        f"Claim científico ainda descoberto {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://science-discovered-claim/{marker}",
        source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        science.promote_canonical_scientific(
            discovered["record_id"],
            f"Lei científica {marker}",
            domain="physics",
            branch="classical_mechanics",
        )

    canonical = _canonical_fact(suite, marker)
    item = science.promote_canonical_scientific(
        canonical["record_id"],
        f"Lei científica {marker}",
        domain="physics",
        branch="classical_mechanics",
        aliases=[f"lei-{marker}"],
        properties={"kind": "law", "units_checked": True},
        subtopics=["laws", "mechanics"],
        contexts=["science"],
        rules=["declarar domínio de validade"],
        exceptions=["regimes fora das hipóteses do modelo"],
        summary="Conhecimento científico materializado com proveniência epistêmica.",
    )
    assert item["namespace"] == "B05"
    assert item["canonical_claim_id"] == canonical["record_id"]
    facets = {(f["facet_type"], f["value"]) for f in item["facets"]}
    assert ("category", "science") in facets
    assert ("category", "physics") in facets
    assert ("category", "classical_mechanics") in facets

    traced = knowledge.trace(item["knowledge_id"])
    assert traced["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"
    assert traced["canonical_claim"]["evidence"]

    neighbors = suite.graph.neighbors(item["knowledge_id"], relation="is_a")
    assert any(x["target_id"] == "SCI-BR-CLASSICAL_MECHANICS" or x["source_id"] == "SCI-BR-CLASSICAL_MECHANICS" for x in neighbors)


def test_block5_reuses_existing_physics_and_chemistry_engines_lazily():
    science, _knowledge, _suite = _science()
    assert science.stats()["providers_loaded"] == []

    physics = science.reference("segunda lei de newton", domain="physics")
    assert physics is not None
    assert physics["provider"] == "core.physics_knowledge_150k"
    assert physics["topic_id"] == "newton_second"
    assert physics["source"]

    chemistry = science.reference("constante de avogadro", domain="chemistry")
    assert chemistry is not None
    assert chemistry["provider"] == "core.chemistry_knowledge_500k"
    assert chemistry["topic_id"] == "avogadro_constant"
    assert chemistry["source"]

    loaded = set(science.stats()["providers_loaded"])
    assert {"physics", "chemistry"} <= loaded


def test_block5_reuses_multidisciplinary_and_curriculum_science_providers():
    science, _knowledge, _suite = _science()
    logic = science.reference("lógica proposicional", domain="logic")
    assert logic is not None
    assert logic["provider"] == "core.multidisciplinary_knowledge"

    astronomy = science.reference("buracos negros", domain="astronomy")
    assert astronomy is not None
    assert astronomy["provider"] == "core.curriculum_knowledge"


def test_scientific_hypothesis_evaluation_reuses_mind_reasoner_and_keeps_epistemic_boundary():
    science, _knowledge, suite = _science()
    assert science.reasoner is suite.science
    result = science.evaluate_hypothesis(
        "A variável X aumenta Y",
        observations=[
            {"stance": "support"},
            {"stance": "refute"},
            {"stance": "support"},
        ],
    )
    assert result["block"] == "B05"
    assert result["evidence_summary"]["support"] == 2
    assert result["evidence_summary"]["refute"] == 1
    assert "não se torna fato" in result["epistemic_note"]
    assert result["falsification"]
    assert result["replication"]


def test_block5_taxonomy_snapshot_preserves_deep_subdisciplines_without_database_materialization():
    science, _knowledge, _suite = _science()
    snapshot = science.taxonomy_snapshot("flora")
    assert len(snapshot["branches"]) == 4
    all_subbranches = {x for branch in snapshot["branches"] for x in branch["subbranches"]}
    assert "fotossíntese" in all_subbranches
    assert "filogenia vegetal" in all_subbranches
    assert "etnobotânica" in all_subbranches
    assert "ecology" in snapshot["cross_domain_bridges"]["flora"]


def test_block5_handlers_and_star_core_integration_are_explicit_and_non_intrusive():
    science, _knowledge, _suite = _science()
    assert "BLOCO 5" in science.handle("status bloco 5")
    assert "SCI-B05-0000000001" in science.handle("SCI-B05-0000000001")
    assert "Taxonomia científica" in science.handle("taxonomia científica física")
    assert science.handle("uma conversa cotidiana sem comando científico") is None

    class Router:
        def route(self, request):
            return {"response_type": "local"}

    class Executive:
        def execute(self, request, route):
            return "fallback"

    class State:
        def get_state(self):
            return {}

    core = StarCore(Router(), Executive(), State())
    assert core.mind.scientific_foundations is core.scientific_foundations
    assert core.scientific_foundations.knowledge is core.knowledge
    assert core.scientific_foundations.reasoner is core.mind.science
    response = core._process_portuguese("status bloco 5")
    assert "BLOCO 5" in response
    assert core.last_intent == "scientific_foundations"
