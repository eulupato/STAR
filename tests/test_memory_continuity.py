from uuid import uuid4
import unicodedata

import pytest

from core.memory_continuity import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    MEMORY_BRANCHES,
    MEMORY_KINDS,
    MEMORY_LENSES,
    MEMORY_POLICY,
    VARIANT_AXES,
    VARIANTS_PER_NODE,
    MemoryCatalog,
    MemoryContinuity,
    WorkingMemoryBuffer,
)
from core.mind import CognitiveSuite
from core.self_model import SelfModel
from core.star_identity import StarIdentity
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _norm(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return " ".join(text.replace("_", " ").split())


def _block():
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    self_model = SelfModel(
        knowledge,
        identity=StarIdentity(),
        state=StarState(),
        mind=suite,
    )
    block = MemoryContinuity(
        knowledge,
        memory=suite.memory,
        graph=suite.graph,
        projects=suite.projects,
        self_model=self_model,
    )
    return block, knowledge, suite, self_model


def _canonical_fact(suite: CognitiveSuite, marker: str):
    source_id = suite.epistemics.register_source(
        f"unit://memory/{marker}",
        source_type="test",
        title=f"Fonte B13 {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        f"Conhecimento canônico sobre memória {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://memory-claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência B13 {marker}",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
        reliability=1.0,
    )
    suite.epistemics.transition(record["record_id"], "VERIFIED", reason="evidência suficiente", actor="unit-test")
    return suite.epistemics.transition(record["record_id"], "CANONICAL", reason="claim apto ao B13", actor="unit-test")


def test_block13_catalog_is_exactly_1b_and_on_demand():
    catalog = MemoryCatalog()
    stats = catalog.stats()
    assert len(MEMORY_KINDS) == 10
    assert len(MEMORY_BRANCHES) == 50
    assert len(MEMORY_LENSES) == 10
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_memory_rows"] == 0
    assert catalog.content_id(0, 0) == "MEM-B13-0000000001"
    assert catalog.content_id(499, 1_999_999) == "MEM-B13-1000000000"
    assert catalog.get_variant("MEM-B13-1000000001") is None


def test_block13_axes_multiply_to_2m_per_node():
    sizes = {name: len(values) for name, values in VARIANT_AXES}
    assert sizes == {
        "retention_scope": 10,
        "retrieval_mode": 10,
        "relation_mode": 10,
        "temporal_scope": 10,
        "source_quality": 5,
        "context_scope": 4,
        "consolidation_stage": 10,
    }
    product = 1
    for value in sizes.values():
        product *= value
    assert product == 2_000_000


def test_block13_covers_requested_memory_types_and_dimensions():
    requested_types = {
        "working", "episodic", "semantic", "conversation", "project",
        "people", "object", "social", "autobiographical", "temporal",
    }
    assert set(MEMORY_KINDS) == requested_types
    requested_dimensions = {
        "event", "entity", "date_time", "relation", "location",
        "importance", "context", "experience", "source", "meaning",
    }
    assert {key for key, _label, _instruction in MEMORY_LENSES} == requested_dimensions
    assert all(sum(1 for branch in MEMORY_BRANCHES if branch.kind == kind) == 5 for kind in MEMORY_KINDS)


def test_working_memory_is_bounded_transient_and_not_persisted_by_default():
    buffer = WorkingMemoryBuffer(max_items=8)
    for index in range(12):
        buffer.add(f"item {index}", key=f"k{index}", source="unit-test", importance=index / 12)
    assert len(buffer.list()) == 8
    assert buffer.get("k0") is None
    assert buffer.get("k11")["persistent"] is False

    block, _knowledge, suite, _self_model = _block()
    before = suite.memory.store.memory_counts()["total"]
    result = block.remember("working", "resultado temporário", source="unit-test", key=uuid4().hex)
    after = suite.memory.store.memory_counts()["total"]
    assert result["persistent"] is False
    assert after == before


def test_persistent_episodic_memory_keeps_event_entities_time_location_importance_context_source_and_meaning():
    block, _knowledge, _suite, _self_model = _block()
    marker = uuid4().hex
    result = block.remember(
        "episodic",
        f"evento de integração {marker}",
        source="unit-test",
        reference=f"event:{marker}",
        occurred_at="2026-09-14T19:00:00-03:00",
        entities=["STAR", "Projeto STAR"],
        location="ambiente de teste",
        importance=0.91,
        context={"project": "STAR", "phase": "B13"},
        experience=True,
        meaning="continuidade validada",
    )
    record = result["record"]
    metadata = record["metadata"]
    assert record["kind"] == "episodic"
    assert record["importance"] == pytest.approx(0.91)
    assert metadata["entities"] == ["STAR", "Projeto STAR"]
    assert metadata["occurred_at"] == "2026-09-14T19:00:00-03:00"
    assert metadata["location"] == "ambiente de teste"
    assert metadata["context"]["project"] == "STAR"
    assert metadata["source"] == "unit-test"
    assert metadata["meaning"] == "continuidade validada"
    assert metadata["experience"] is True
    assert metadata["fabricated"] is False


def test_cognitive_memory_accepts_social_and_autobiographical_without_parallel_store():
    block, _knowledge, suite, _self_model = _block()
    assert "social" in suite.memory.KINDS
    assert "autobiographical" in suite.memory.KINDS
    social = block.remember("social", f"contexto social {uuid4().hex}", source="unit-test")
    autobiographical = block.remember(
        "autobiographical",
        f"evento da STAR {uuid4().hex}",
        source="git",
        reference="commit:test",
    )
    assert social["record"]["kind"] == "social"
    assert autobiographical["record"]["kind"] == "autobiographical"
    assert block.stats()["persistent_store"] == "cognitive_memory"
    assert block.stats()["parallel_database"] is False


def test_autobiographical_memory_and_experience_require_auditable_reference():
    block, _knowledge, _suite, _self_model = _block()
    with pytest.raises(ValueError, match="referência auditável"):
        block.remember("autobiographical", "evento sem referência", source="unit-test")
    with pytest.raises(ValueError, match="referência auditável"):
        block.remember("episodic", "experiência sem referência", source="unit-test", experience=True)


def test_b12_self_history_can_feed_autobiographical_memory_without_fabrication():
    block, _knowledge, _suite, self_model = _block()
    event = self_model.history.record_experience(
        "integração B13 observada",
        source="unit-test-session",
        reference="conversation:test-b13",
    )
    result = block.remember_self_event(event)
    metadata = result["record"]["metadata"]
    assert result["kind"] == "autobiographical"
    assert metadata["imported_from_b12_self_history"] is True
    assert metadata["fabricated"] is False
    assert metadata["reference"] == "conversation:test-b13"


def test_memory_relations_use_shared_knowledge_graph():
    block, knowledge, suite, _self_model = _block()
    marker = uuid4().hex
    first = block.remember("episodic", f"primeiro {marker}", source="unit-test")
    second = block.remember("temporal", f"segundo {marker}", source="unit-test")
    relation = block.relate_memories(first["memory_id"], second["memory_id"], "precedes")
    assert block.graph is knowledge.graph is suite.graph
    assert relation["relation"] == "precedes"
    neighbors = suite.graph.neighbors(first["memory_node_id"])
    assert any(item["relation"] == "precedes" for item in neighbors)
    assert block.stats()["parallel_graph"] is False


def test_consolidation_creates_derived_semantic_memory_and_preserves_sources():
    block, _knowledge, suite, _self_model = _block()
    marker = uuid4().hex
    first = block.remember("episodic", f"observação A {marker}", source="unit-test")
    second = block.remember("conversation", f"observação B {marker}", source="unit-test")
    consolidated = block.consolidate(
        [first["memory_id"], second["memory_id"]],
        f"síntese consolidada {marker}",
        source="unit-test-consolidator",
        reference=f"consolidation:{marker}",
        meaning="síntese derivada",
    )
    assert consolidated["record"]["kind"] == "semantic"
    assert consolidated["source_memories_preserved"] is True
    assert consolidated["consolidated_from"] == [first["memory_id"], second["memory_id"]]
    neighbors = suite.graph.neighbors(consolidated["memory_node_id"])
    derived = [item for item in neighbors if item["relation"] == "derived_from"]
    assert len(derived) >= 2
    assert block.memory_record(first["memory_id"]) is not None
    assert block.memory_record(second["memory_id"]) is not None


def test_recall_combines_persistent_and_working_memory_without_loading_entire_store():
    block, _knowledge, _suite, _self_model = _block()
    marker = uuid4().hex
    block.remember("semantic", f"semântica {marker}", source="unit-test", importance=0.8)
    block.remember("working", f"working {marker}", source="unit-test", importance=0.9)
    recalled = block.recall(marker, limit=10)
    assert any(item["storage"] == "persistent" for item in recalled)
    assert any(item["storage"] == "working" for item in recalled)
    assert len(recalled) <= 10


def test_people_memory_marks_sensitive_inference_as_disabled():
    block, _knowledge, _suite, _self_model = _block()
    result = block.remember(
        "people",
        f"preferência declarada {uuid4().hex}",
        source="declared-by-person",
        context={"scope": "interaction"},
    )
    assert result["record"]["metadata"]["sensitive_attribute_inference"] is False


def test_block13_taxonomy_reuses_shared_graph_and_links_b12_and_cognitive_memory():
    block, _knowledge, suite, _self_model = _block()
    result = block.materialize_taxonomy("autobiographical")
    assert result["branches_materialized"] == 5
    assert result["knowledge_graph"] == "shared"
    assert result["parallel_memory_graph_created"] is False
    labels = {item["label"] for item in suite.graph.neighbors("MEMORY-TAX-ROOT")}
    assert "SELF MODEL / Self History" in labels
    assert "CognitiveMemory" in labels
    assert "Memória autobiográfica da STAR" in labels


def test_block13_canonical_memory_knowledge_keeps_b2_b3_gate():
    block, knowledge, suite, _self_model = _block()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(f"unit://memory-discovered/{marker}", source_type="test", reliability=1.0)
    discovered = suite.epistemics.discover(
        f"claim memória descoberto {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://memory-discovered-claim/{marker}",
        source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        block.promote_canonical_memory_knowledge(
            discovered["record_id"], f"Memória {marker}", memory_kind="semantic", branch="concepts"
        )

    canonical = _canonical_fact(suite, marker)
    item = block.promote_canonical_memory_knowledge(
        canonical["record_id"],
        f"Conceito de memória {marker}",
        memory_kind="semantic",
        branch="concepts",
        summary="Conhecimento canônico sobre arquitetura de memória.",
    )
    assert item["namespace"] == "B13"
    assert item["properties"]["memory_is_fact"] is False
    trace = knowledge.trace(item["knowledge_id"])
    assert trace["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"


def test_continuity_snapshot_reports_real_counts_and_does_not_claim_operational_authority():
    block, _knowledge, _suite, self_model = _block()
    self_model.history.record("release", "marco B13", source="git", reference="commit:test-b13")
    block.remember("project", f"projeto {uuid4().hex}", source="unit-test")
    snapshot = block.continuity_snapshot()
    assert snapshot["persistent_memory"]["total"] >= 1
    assert snapshot["b12_self_history_events"] == 1
    assert snapshot["identity_continuity_source"] == "B12 Self Model / official identity"
    assert snapshot["memory_is_fact"] is False
    assert snapshot["autobiographical_memory_fabricated"] is False
    assert snapshot["operational_authorization"] is False


def test_block13_policy_catalog_prompt_and_handlers_are_explicit_and_nonintrusive():
    assert MEMORY_POLICY["working_memory_persistent_by_default"] is False
    assert MEMORY_POLICY["memory_equals_fact"] is False
    assert MEMORY_POLICY["consolidation_overwrites_sources"] is False
    assert MEMORY_POLICY["autobiographical_experience_may_be_fabricated"] is False
    assert MEMORY_POLICY["memory_grants_operational_authorization"] is False

    item = MemoryCatalog().get_variant("MEM-B13-0000000001")
    assert item["memory_kind"] == "working"
    assert item["branch"] == "active_items"
    assert item["lens"] == "event"
    assert "não é persistida" in item["prompt"]

    block, _knowledge, _suite, _self_model = _block()
    assert "BLOCO 13" in block.handle("status bloco 13")
    assert "MEM-B13-0000000001" in block.handle("MEM-B13-0000000001")
    assert "Continuidade B13" in block.handle("continuidade da star")
    assert block.handle("uma conversa normal sem comando de memória") is None
