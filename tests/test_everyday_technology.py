from uuid import uuid4
import unicodedata

import pytest

from core.everyday_technology import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    EVERYDAY_TECH_BRANCHES,
    EVERYDAY_TECH_DOMAINS,
    EVERYDAY_TECH_LENSES,
    INTERPRETATION_POLICY,
    REFERENCE_SUBJECTS,
    REQUESTED_TOPICS,
    VARIANT_AXES,
    VARIANTS_PER_NODE,
    EverydayTechnologyCatalog,
    EverydayTechnologyFoundations,
)
from core.mind import CognitiveSuite
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _norm(text):
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return " ".join(value.replace("_", " ").split())


def _block(**kwargs):
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    block = EverydayTechnologyFoundations(knowledge, **kwargs)
    return block, knowledge, suite


def _canonical_fact(suite: CognitiveSuite, marker: str):
    source_id = suite.epistemics.register_source(
        f"unit://technology/{marker}",
        source_type="test",
        title=f"Fonte tecnológica {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        f"Conhecimento técnico validado {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://technology-claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência técnica rastreável {marker}",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
        reliability=1.0,
    )
    suite.epistemics.transition(record["record_id"], "VERIFIED", reason="evidência rastreável", actor="unit-test")
    return suite.epistemics.transition(record["record_id"], "CANONICAL", reason="claim técnico apto ao B11", actor="unit-test")


def test_block11_catalog_is_exactly_1b_and_on_demand():
    catalog = EverydayTechnologyCatalog()
    stats = catalog.stats()
    assert len(EVERYDAY_TECH_DOMAINS) == 13
    assert len(EVERYDAY_TECH_BRANCHES) == 50
    assert len(EVERYDAY_TECH_LENSES) == 10
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_knowledge_rows"] == 0
    assert catalog.content_id(0, 0) == "TECH-B11-0000000001"
    assert catalog.content_id(499, 1_999_999) == "TECH-B11-1000000000"
    assert catalog.get_variant("TECH-B11-1000000001") is None


def test_block11_axes_are_objects_systems_functions_uses_risks_states_contexts():
    sizes = {name: len(values) for name, values in VARIANT_AXES}
    assert list(sizes) == ["object", "system", "function", "use", "risk", "state", "context"]
    assert sizes == {"object": 10, "system": 10, "function": 10, "use": 10, "risk": 5, "state": 4, "context": 10}
    product = 1
    for size in sizes.values():
        product *= size
    assert product == 2_000_000
    item = EverydayTechnologyCatalog().get_variant("TECH-B11-1000000000")
    for axis in sizes:
        assert axis in item


def test_block11_contains_all_requested_everyday_and_technology_topics():
    corpus = _norm(" ".join(
        [branch.label for branch in EVERYDAY_TECH_BRANCHES]
        + [topic for branch in EVERYDAY_TECH_BRANCHES for topic in branch.subtopics]
        + list(REQUESTED_TOPICS)
    ))
    for topic in REQUESTED_TOPICS:
        assert _norm(topic) in corpus, topic
    for extra in ("GPS", "alergênicos", "CPU", "Git", "TLS", "data centers", "PDF"):
        assert _norm(extra) in corpus


def test_block11_registers_b11_on_same_universal_architecture_and_graph():
    block, knowledge, _suite = _block()
    namespace = knowledge.store.get_namespace("B11")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert block.knowledge is knowledge
    assert block.graph is knowledge.graph
    assert block.stats()["knowledge_graph"] == "shared knowledge_nodes/knowledge_edges"
    assert block.stats()["parallel_technology_database"] is False


def test_block11_taxonomy_materializes_in_shared_graph_and_links_science_and_context():
    block, _knowledge, suite = _block()
    result = block.materialize_taxonomy("hardware")
    assert result["knowledge_graph"] == "shared"
    assert result["parallel_technology_graph_created"] is False
    assert result["branches_materialized"] == 4
    neighbors = suite.graph.neighbors("TECH-TAX-ROOT")
    labels = {item["label"] for item in neighbors}
    assert "Ciência" in labels
    assert "Contextos Humanos Específicos" in labels
    assert "Computadores e hardware" in labels
    branch_neighbors = suite.graph.neighbors("TECH-BR-COMPUTERS", relation="has_part")
    assert any(item["node_type"] == "everyday_technology_subtopic" for item in branch_neighbors)


def test_block11_reuses_existing_multidisciplinary_technical_subjects_lazily():
    assert REFERENCE_SUBJECTS["computing_hardware"] == "computacao"
    assert REFERENCE_SUBJECTS["networks_internet"] == "ti"
    assert REFERENCE_SUBJECTS["tools_machines"] == "mecanica"
    assert REFERENCE_SUBJECTS["cities_mobility"] == "geografia"

    class FakeMultidisciplinary:
        def __init__(self):
            self.queries = []
        def answer(self, query):
            self.queries.append(query)
            return "referência técnica existente"

    fake = FakeMultidisciplinary()
    block, _knowledge, _suite = _block(multidisciplinary=fake)
    assert block._providers == {}
    result = block.reference("arquitetura de computadores", domain="hardware")
    assert result["provider"] == "core.multidisciplinary_knowledge"
    assert result["subject_hint"] == "computacao"
    assert result["canonicalized"] is False
    assert fake.queries == ["computacao arquitetura de computadores"]


def test_block11_contextualization_keeps_live_state_access_and_authorization_separate():
    block, _knowledge, _suite = _block()
    result = block.contextualize_system(
        "um notebook conectado ao Wi-Fi está apresentando lentidão",
        object_name="notebook",
        system="computacional e rede",
        function="processamento e comunicação",
        use="trabalho",
        risk="digital e perda de dados",
        state="degradado observado",
        context="doméstico",
        platform_version="Windows, versão não confirmada",
        observations=["latência percebida", "Wi-Fi conectado"],
    )
    assert result["epistemic_kind"] == "inference"
    assert result["live_state_claim"] is False
    assert result["operational_access"] is False
    assert result["operational_authorization"] is False
    assert result["unknown_state_invented"] is False
    assert result["missing_dimensions"] == []
    assert any("fonte atual" in check for check in result["context_checks"])
    assert any("culinária" in check for check in result["context_checks"])
    assert any("segurança digital" in check for check in result["context_checks"])


def test_block11_policy_prevents_knowledge_from_becoming_control_or_live_truth():
    assert INTERPRETATION_POLICY["knowledge_implies_operational_access"] is False
    assert INTERPRETATION_POLICY["technical_description_implies_authorization"] is False
    assert INTERPRETATION_POLICY["digital_security_knowledge_implies_attack_permission"] is False
    assert INTERPRETATION_POLICY["navigation_knowledge_is_live_route_data"] is False
    assert INTERPRETATION_POLICY["infrastructure_description_is_live_status"] is False
    assert INTERPRETATION_POLICY["unknown_state_may_be_invented"] is False
    assert INTERPRETATION_POLICY["live_conditions_require_current_source"] is True
    assert INTERPRETATION_POLICY["operational_action_requires_permission_capability_safety"] is True


def test_block11_canonical_knowledge_keeps_block2_gate_and_links_graph():
    block, knowledge, suite = _block()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(f"unit://tech-discovered/{marker}", source_type="test", reliability=1.0)
    discovered = suite.epistemics.discover(
        f"Claim técnico descoberto {marker}", epistemic_kind="fact", origin_type="unit_test",
        origin_ref=f"unit://tech-discovered-claim/{marker}", source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        block.promote_canonical_technology_knowledge(
            discovered["record_id"], f"Conhecimento técnico {marker}", domain="hardware", branch="computers"
        )

    canonical = _canonical_fact(suite, marker)
    item = block.promote_canonical_technology_knowledge(
        canonical["record_id"],
        f"Conhecimento técnico {marker}",
        domain="hardware",
        branch="computers",
        properties={"scope": "general"},
        contexts=["platform-dependent"],
        summary="Conhecimento técnico geral e versionável.",
    )
    assert item["namespace"] == "B11"
    assert item["properties"]["knowledge_implies_operational_access"] is False
    assert item["properties"]["live_state_requires_current_observation"] is True
    trace = knowledge.trace(item["knowledge_id"])
    assert trace["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"
    neighbors = suite.graph.neighbors(item["knowledge_id"], relation="is_a")
    assert any(n["label"] == "Computadores" for n in neighbors)


def test_block11_variant_handlers_are_explicit_and_nonintrusive():
    item = EverydayTechnologyCatalog().get_variant("TECH-B11-0000000001")
    assert item["domain"] == "built_environment"
    assert item["branch"] == "homes"
    assert item["lens"] == "concept"
    assert "Objeto=" in item["prompt"]
    assert "não concede acesso" in item["prompt"]

    block, _knowledge, _suite = _block()
    assert "BLOCO 11" in block.handle("status bloco 11")
    assert "TECH-B11-0000000001" in block.handle("TECH-B11-0000000001")
    assert "não significa acesso" in block.handle("limites bloco 11")
    assert block.handle("uma conversa cotidiana comum sem comando técnico explícito") is None
