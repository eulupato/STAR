from uuid import uuid4
import unicodedata

import pytest

from core.mind import CognitiveSuite
from core.society_culture import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    INTERPRETATION_POLICY,
    REFERENCE_SUBJECTS,
    REQUESTED_TOPICS,
    SOCIETY_CULTURE_BRANCHES,
    SOCIETY_CULTURE_DOMAINS,
    SOCIETY_CULTURE_LENSES,
    VARIANT_AXES,
    VARIANTS_PER_NODE,
    SocietyCultureCatalog,
    SocietyCultureFoundations,
)
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _norm(text):
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return " ".join(value.replace("_", " ").split())


def _block():
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    block = SocietyCultureFoundations(knowledge)
    return block, knowledge, suite


def _canonical_fact(suite: CognitiveSuite, marker: str):
    source_id = suite.epistemics.register_source(
        f"unit://society/{marker}",
        source_type="test",
        title=f"Fonte sociocultural {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        f"Conhecimento sociocultural geral validado {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://society-claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência sociocultural rastreável {marker}",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
        reliability=1.0,
    )
    suite.epistemics.transition(record["record_id"], "VERIFIED", reason="evidência rastreável", actor="unit-test")
    return suite.epistemics.transition(record["record_id"], "CANONICAL", reason="claim geral apto ao B09", actor="unit-test")


def test_block9_catalog_is_exactly_1b_and_on_demand():
    catalog = SocietyCultureCatalog()
    stats = catalog.stats()
    assert len(SOCIETY_CULTURE_DOMAINS) == 13
    assert len(SOCIETY_CULTURE_BRANCHES) == 50
    assert len(SOCIETY_CULTURE_LENSES) == 20
    assert CANONICAL_NODES == 1_000
    assert VARIANTS_PER_NODE == 1_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_knowledge_rows"] == 0
    assert catalog.content_id(0, 0) == "SOC-B09-0000000001"
    assert catalog.content_id(999, 999_999) == "SOC-B09-1000000000"
    assert catalog.get_variant("SOC-B09-1000000001") is None


def test_block9_variant_space_covers_society_era_region_system_relation_perspective():
    sizes = {name: len(values) for name, values in VARIANT_AXES}
    assert list(sizes) == ["society", "era", "region", "system", "relation", "perspective"]
    assert all(size == 10 for size in sizes.values())
    product = 1
    for size in sizes.values():
        product *= size
    assert product == 1_000_000
    item = SocietyCultureCatalog().get_variant("SOC-B09-1000000000")
    for dimension in sizes:
        assert dimension in item


def test_block9_contains_all_requested_social_and_cultural_topics():
    corpus = _norm(" ".join(
        [branch.label for branch in SOCIETY_CULTURE_BRANCHES]
        + [topic for branch in SOCIETY_CULTURE_BRANCHES for topic in branch.subtopics]
        + list(REQUESTED_TOPICS)
    ))
    for topic in REQUESTED_TOPICS:
        assert _norm(topic) in corpus, topic
    assert "etnografia" in corpus
    assert "pluralismo juridico" in corpus
    assert "secularizacao" in corpus
    assert "industrias culturais" in corpus


def test_block9_reuses_existing_multidisciplinary_subjects_without_duplication():
    assert REFERENCE_SUBJECTS["geography_regions"] == "geography"
    assert REFERENCE_SUBJECTS["history_temporality"] == "history"
    assert REFERENCE_SUBJECTS["sociology_society"] == "psychology_sociology"
    assert REFERENCE_SUBJECTS["ethics_philosophy"] == "philosophy"
    block, _knowledge, _suite = _block()
    assert block.stats()["multidisciplinary_knowledge"] == "reused, not duplicated"


def test_block9_registers_b09_on_same_universal_architecture():
    block, knowledge, _suite = _block()
    namespace = knowledge.store.get_namespace("B09")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert block.knowledge is knowledge
    assert block.graph is knowledge.graph
    assert block.stats()["knowledge_graph"] == "shared knowledge_nodes/knowledge_edges"


def test_block9_taxonomy_uses_shared_graph_and_links_blocks7_and8():
    block, _knowledge, suite = _block()
    result = block.materialize_taxonomy("família")
    assert result["knowledge_graph"] == "shared"
    assert result["parallel_social_graph_created"] is False
    assert result["branches_materialized"] == 3
    root_neighbors = suite.graph.neighbors("SOC-TAX-ROOT")
    labels = {item["label"] for item in root_neighbors}
    assert "Mente Humana e Psicologia" in labels
    assert "Linguagem e Comunicação" in labels
    assert "Relações, família e amizade" in labels
    branch_neighbors = suite.graph.neighbors("SOC-BR-FAMILY_KINSHIP", relation="has_part")
    assert any(item["node_type"] == "society_culture_subtopic" for item in branch_neighbors)


def test_block9_contextualization_rejects_essentialism_and_anachronism():
    block, _knowledge, _suite = _block()
    result = block.contextualize_social_statement(
        "essa sociedade valoriza propriedade coletiva",
        society="comunidade histórica específica",
        era="século XIX",
        region="região documentada",
        system="propriedade e recursos",
        perspective="histórica e comparativa",
        sources=["arquivo A", "estudo B"],
    )
    assert result["epistemic_kind"] == "inference"
    assert result["certainty"] == "context_dependent"
    assert result["universal_claim"] is False
    assert result["group_membership_determines_individual_trait"] is False
    assert result["political_endorsement"] is False
    assert result["alternative_interpretations_required"] is True
    assert result["missing_context"] == []
    assert any("anacronismo" in item for item in result["context_checks"])


def test_block9_policy_preserves_context_pluralism_and_religion_law_distinctions():
    assert INTERPRETATION_POLICY["culture_is_fixed_or_homogeneous"] is False
    assert INTERPRETATION_POLICY["group_membership_determines_individual_trait"] is False
    assert INTERPRETATION_POLICY["present_values_are_universal_historical_standard"] is False
    assert INTERPRETATION_POLICY["political_description_implies_endorsement"] is False
    assert INTERPRETATION_POLICY["religious_belief_is_empirical_fact_by_default"] is False
    assert INTERPRETATION_POLICY["mythology_is_ranked_against_religion"] is False
    assert INTERPRETATION_POLICY["law_is_timeless_or_jurisdiction_free"] is False
    assert INTERPRETATION_POLICY["contested_claims_require_multiple_perspectives"] is True


def test_block9_canonical_knowledge_keeps_block2_gate_and_context_policy():
    block, knowledge, suite = _block()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(
        f"unit://soc-discovered/{marker}", source_type="test", reliability=1.0
    )
    discovered = suite.epistemics.discover(
        f"Claim social descoberto {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://soc-discovered-claim/{marker}",
        source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        block.promote_canonical_social_knowledge(
            discovered["record_id"],
            f"Conhecimento social {marker}",
            domain="sociologia",
            branch="social_structure",
        )

    canonical = _canonical_fact(suite, marker)
    item = block.promote_canonical_social_knowledge(
        canonical["record_id"],
        f"Conhecimento social {marker}",
        domain="sociologia",
        branch="social_structure",
        properties={"scope": "general"},
        contexts=["historical", "regional"],
        summary="Conhecimento sociocultural geral e contextual.",
    )
    assert item["namespace"] == "B09"
    assert item["properties"]["culture_fixed_or_homogeneous"] is False
    assert item["properties"]["group_trait_determinism"] is False
    assert item["properties"]["political_endorsement"] is False
    assert item["properties"]["jurisdiction_and_time_context_required_for_law"] is True
    trace = knowledge.trace(item["knowledge_id"])
    assert trace["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"
    assert trace["canonical_claim"]["evidence"]


def test_block9_variant_and_handlers_are_explicit_and_nonintrusive():
    item = SocietyCultureCatalog().get_variant("SOC-B09-0000000001")
    assert item["domain"] == "anthropology_culture"
    assert item["branch"] == "cultural_anthropology"
    assert item["lens"] == "concept"
    assert "Sociedade=" in item["prompt"]
    assert "essências fixas" in item["prompt"]

    block, _knowledge, _suite = _block()
    assert "BLOCO 9" in block.handle("status bloco 9")
    assert "SOC-B09-0000000001" in block.handle("SOC-B09-0000000001")
    assert "não trata culturas" in block.handle("generalização cultural")
    assert block.handle("uma conversa cotidiana sem comando sociocultural") is None
