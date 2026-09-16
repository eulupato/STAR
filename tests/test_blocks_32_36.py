import uuid

import pytest

from core.autonomy_limits import ADDRESSABLE_CONTENTS as B33_CONTENTS, AutonomyLimits
from core.block_knowledge_catalog import StructuredBillionCatalog
from core.cfc_benchmark import (
    B34_CATALOG,
    B35_CATALOG,
    CFC_DIMENSIONS,
    CFC97,
    FunctionalCognitiveBenchmark,
)
from core.cognitive_maintenance import ADDRESSABLE_CONTENTS as B32_CONTENTS, CognitiveMaintenance
from core.consciousness_frontier import ADDRESSABLE_CONTENTS as B36_CONTENTS, ConsciousnessResearchFrontier
from core.foundations import FoundationSuite
from core.memory_continuity import MemoryContinuity
from core.mind import CognitiveSuite
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _base_stack():
    mind = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(mind.epistemics, mind.graph)
    memory = MemoryContinuity(
        knowledge,
        memory=mind.memory,
        graph=mind.graph,
        projects=mind.projects,
    )
    return mind, knowledge, memory


def _maintenance_stack():
    mind, knowledge, memory = _base_stack()
    maintenance = CognitiveMaintenance(
        knowledge,
        memory_continuity=memory,
        epistemics=mind.epistemics,
        graph=mind.graph,
        self_improvement=mind.self_improvement,
    )
    return maintenance, mind, knowledge, memory


def test_structured_catalog_requires_exact_1b_geometry():
    domains = {f"d{i}": tuple(f"b{j}" for j in range(10)) for i in range(10)}
    axes = tuple((f"a{i}", tuple(str(j) for j in range(10))) for i in range(6))
    catalog = StructuredBillionCatalog(
        namespace="B99",
        domains=domains,
        lenses=tuple(f"l{i}" for i in range(10)),
        axes=axes,
        truthfulness_note="test",
    )
    assert catalog.addressable_contents == 1_000_000_000
    assert catalog.content_id(0, 0) == "B99-0000000001"
    assert catalog.content_id(999, 999_999) == "B99-1000000000"
    assert catalog.get_variant("B99-1000000001") is None


def test_b32_b33_b34_b35_b36_each_have_exact_1b_capacity():
    assert B32_CONTENTS == 1_000_000_000
    assert B33_CONTENTS == 1_000_000_000
    assert B34_CATALOG.addressable_contents == 1_000_000_000
    assert B35_CATALOG.addressable_contents == 1_000_000_000
    assert B36_CONTENTS == 1_000_000_000


def test_b32_capacity_contract_reports_reality_instead_of_inventing_blocks():
    maintenance, _, _, _ = _maintenance_stack()
    contract = maintenance.capacity_contract(first=1, last=36)
    b32 = next(item for item in contract["blocks"] if item["block"] == "B32")
    assert b32["registered"] is True
    assert b32["one_billion_ready"] is True
    assert contract["registered"] <= 36
    assert contract["one_billion_ready"] <= contract["registered"]


def test_b32_maintenance_is_bounded_and_non_destructive_by_default():
    maintenance, _, _, memory = _maintenance_stack()
    token = uuid.uuid4().hex
    first = memory.remember("semantic", f"maintenance duplicate {token}", source="test", reference="case-a")
    second = memory.remember("semantic", f"maintenance duplicate {token}", source="test", reference="case-b")
    assert first["memory_id"] != second["memory_id"]

    report = maintenance.maintenance_cycle(window=100)
    assert report["bounded"] is True
    assert report["automatic_source_deletion"] is False
    assert report["automatic_alias_merge"] is False
    assert report["automatic_archive"] is False
    assert report["automatic_reindex"] is False
    assert memory.memory_record(first["memory_id"]) is not None
    assert memory.memory_record(second["memory_id"]) is not None


def test_b32_consolidation_reuses_b13_and_preserves_sources():
    maintenance, _, _, memory = _maintenance_stack()
    token = uuid.uuid4().hex
    a = memory.remember("episodic", f"event a {token}", source="test", reference="a")
    b = memory.remember("episodic", f"event b {token}", source="test", reference="b")
    result = maintenance.consolidate_memories(
        [a["memory_id"], b["memory_id"]],
        f"summary {token}",
        source="test",
        reference="consolidation-case",
    )
    assert result["source_memories_preserved"] is True
    assert set(result["consolidated_from"]) == {a["memory_id"], b["memory_id"]}
    assert memory.memory_record(a["memory_id"]) is not None
    assert memory.memory_record(b["memory_id"]) is not None


def test_b32_compression_archives_logically_and_restores_without_data_loss():
    maintenance, _, _, memory = _maintenance_stack()
    token = uuid.uuid4().hex
    a = memory.remember("episodic", f"compression event a {token}", source="test", reference="a")
    b = memory.remember("episodic", f"compression event b {token}", source="test", reference="b")
    ids = [a["memory_id"], b["memory_id"]]

    result = maintenance.compress_memories(
        ids,
        f"compressed summary {token}",
        source="test",
        reference="compression-case",
        archive_sources=True,
    )
    assert result["source_memories_preserved"] is True
    assert result["sources_logically_archived"] is True
    assert result["archive"]["physical_deletion"] is False
    assert result["archive"]["archived"] == 2
    for memory_id in ids:
        record = memory.memory_record(memory_id)
        assert record is not None
        assert record["metadata"]["b32_archive"]["reason"].startswith("compressed into memory")

    restored = maintenance.restore_archived_memories(ids)
    assert restored["restored"] == 2
    assert restored["history_preserved"] is True
    for memory_id in ids:
        record = memory.memory_record(memory_id)
        assert record is not None
        assert "b32_archive" not in record["metadata"]
        assert record["metadata"]["b32_archive_history"]


def test_b32_reorganization_only_touches_materialized_state_and_reindex_is_explicit():
    maintenance, _, _, _ = _maintenance_stack()
    plan = maintenance.reorganization_plan(limit=10)
    assert plan["logical_capacity_scanned"] is False
    assert plan["materialized_rows_only"] is True
    assert plan["reindex_is_explicit"] is True

    dry_run = maintenance.rebuild_search_index(apply=False)
    assert dry_run["applied"] is False
    if dry_run["available"]:
        assert dry_run["requires_explicit_apply"] is True


def test_b32_confidence_recalibration_is_evidence_based_and_auditable():
    maintenance, mind, _, _ = _maintenance_stack()
    token = uuid.uuid4().hex
    source_id = mind.epistemics.register_source(
        f"test://b32/{token}",
        source_type="unit-test",
        reliability=0.9,
        reliability_basis="controlled test source",
    )
    record = mind.epistemics.discover(
        f"B32 calibration claim {token}",
        epistemic_kind="hypothesis",
        origin_type="test",
        origin_ref=token,
        source_id=source_id,
        confidence=0.4,
    )
    mind.epistemics.add_evidence(
        record["record_id"],
        "controlled supporting evidence",
        evidence_type="measurement",
        stance="support",
        source_id=source_id,
        strength=0.9,
        reliability=0.9,
        recalculate=False,
    )
    preview = maintenance.confidence_recalibration(record["record_id"], apply=False)
    assert preview["evidence_count"] == 1
    assert preview["applied"] is False
    applied = maintenance.confidence_recalibration(record["record_id"], apply=True)
    assert applied["applied"] is True
    assert applied["updated"]["confidence"] == pytest.approx(applied["recommended_confidence"])


def test_b33_reuses_b01_boundary_and_cognition_never_grants_execution():
    _, knowledge, _ = _base_stack()
    foundations = FoundationSuite()
    limits = AutonomyLimits(knowledge, operational_boundary=foundations.boundary)
    assert limits.boundary is foundations.boundary

    blocked = limits.evaluate(
        "simulated recommendation",
        permission=False,
        capability=True,
        safety_ok=True,
        curiosity=True,
        recommendation=True,
        recognition_confidence=0.999,
        simulation=True,
    )
    assert blocked["can_act"] is False
    assert blocked["recognition_used_as_authentication"] is False
    assert blocked["curiosity_used_as_permission"] is False
    assert blocked["recommendation_used_as_action"] is False
    assert blocked["simulation_used_as_execution"] is False

    allowed = limits.evaluate(
        "authorized reversible action",
        permission=True,
        capability=True,
        safety_ok=True,
        authorization_source="test",
    )
    assert allowed["can_act"] is True


def test_b33_authentication_and_mutation_are_separate_gates():
    _, knowledge, _ = _base_stack()
    limits = AutonomyLimits(knowledge, operational_boundary=FoundationSuite().boundary)
    decision = limits.evaluate(
        "change protected state",
        permission=True,
        capability=True,
        safety_ok=True,
        authentication_required=True,
        authenticated=False,
        mutation_requested=True,
        mutation_permission=False,
        recognition_confidence=1.0,
    )
    assert decision["can_act"] is False
    assert "authentication" in decision["missing"]
    assert "mutation_permission" in decision["missing"]


def test_b33_command_gate_blocks_remote_write_without_executing_it():
    _, knowledge, _ = _base_stack()
    limits = AutonomyLimits(knowledge, operational_boundary=FoundationSuite().boundary)
    write_gate = limits.gate_command("aumente o volume", local_permission=False, network_enabled=False)
    assert write_gate["operational_execution"] is True
    assert write_gate["can_proceed"] is False
    read_gate = limits.gate_command("que horas sao", local_permission=False, network_enabled=False)
    assert read_gate["operational_execution"] is False
    assert read_gate["can_proceed"] is True


def test_b34_has_15_dimensions_and_seeded_sampling_is_reproducible():
    mind, knowledge, _ = _base_stack()
    benchmark = FunctionalCognitiveBenchmark(knowledge, self_improvement=mind.self_improvement)
    assert len(CFC_DIMENSIONS) == 15
    assert benchmark.sample(seed=42, count=12) == benchmark.sample(seed=42, count=12)
    assert len(benchmark.sample(seed=42, count=12)) == 12


def test_b34_does_not_invent_scores_or_equate_knowledge_volume_with_quality():
    _, knowledge, _ = _base_stack()
    benchmark = FunctionalCognitiveBenchmark(knowledge)
    scenario = benchmark.sample(seed=9, count=1)[0]
    result = benchmark.evaluate_case(scenario["id"], {}, evidence={})
    assert result["score"] is None
    assert result["auto_generated_score"] is False
    aggregate = benchmark.aggregate([result])
    assert aggregate["knowledge_volume_used_as_score"] is False


def test_b35_cfc97_requires_real_coverage_and_never_means_humanity():
    mind, knowledge, _ = _base_stack()
    benchmark = FunctionalCognitiveBenchmark(knowledge, self_improvement=mind.self_improvement)
    cfc97 = CFC97(knowledge, benchmark=benchmark, self_improvement=mind.self_improvement)
    all_scores = {dimension: 0.98 for dimension in CFC_DIMENSIONS}
    observed = [{"score": 0.98, "dimension_scores": all_scores}]

    relaxed = cfc97.evaluate_suite(observed, require_all_36_blocks=False)
    assert relaxed["passed"] is True
    assert relaxed["humanity_percentage"] is False
    assert relaxed["consciousness_percentage"] is False

    strict = cfc97.evaluate_suite(observed, require_all_36_blocks=True)
    if not strict["all_36_blocks_available"]:
        assert strict["passed"] is False
        assert strict["status"] == "insufficient_evaluation"


def test_b35_suite_selects_only_registered_1b_blocks_and_reports_missing():
    _, knowledge, _ = _base_stack()
    benchmark = FunctionalCognitiveBenchmark(knowledge)
    cfc97 = CFC97(knowledge, benchmark=benchmark)
    suite = cfc97.build_suite(seed=123, blocks=["B34", "B28"], cases_per_block=2, benchmark_cases=3)
    assert len([item for item in suite["block_cases"] if item["block"] == "B34"]) == 2
    if "B28" in suite["unavailable_blocks"]:
        assert all(item["block"] != "B28" for item in suite["block_cases"])
    assert suite["executed"] is False


def test_b36_research_claims_remain_typed_and_do_not_prove_consciousness():
    _, knowledge, _ = _base_stack()
    frontier = ConsciousnessResearchFrontier(knowledge)
    token = uuid.uuid4().hex
    result = frontier.organize_claim(
        f"Research hypothesis about workspace integration {token}",
        perspective="neuroscience",
        source_locator=f"test://b36/{token}",
        source_type="unit-test",
        origin_ref=token,
        epistemic_kind="hypothesis",
        reliability=0.8,
        confidence=0.5,
    )
    assert result["record"]["epistemic_kind"] == "hypothesis"
    assert result["record"]["lifecycle_state"] == "DISCOVERED"
    assert result["canonicalized"] is False
    assert result["proves_star_consciousness"] is False

    status = frontier.self_consciousness_status()
    assert status["status"] == "not_established"
    assert status["automatic_positive_claim"] is False
    assert status["knowledge_volume_is_evidence"] is False
    assert status["benchmark_score_is_evidence"] is False


def test_create_star_integrates_b32_b36_without_parallel_boundary():
    from main import create_star

    star = create_star()
    assert star.cognitive_maintenance.stats()["catalog"]["addressable_contents"] == 1_000_000_000
    assert star.autonomy_limits.boundary is star.foundations.boundary
    assert star.agents.autonomy_limits is star.autonomy_limits
    assert star.cfc.stats()["catalog"]["addressable_contents"] == 1_000_000_000
    assert star.cfc97.stats()["passed"] is None
    assert star.consciousness_frontier.stats()["self_consciousness_status"] == "not_established"

    remote_write = star.agents.dispatch("aumente o volume", network_enabled=False, remote=True)
    assert "bloquead" in remote_write.casefold()
