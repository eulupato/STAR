from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from core.epistemics import (
    EPISTEMIC_ADDRESSABLE_CONTENTS,
    EPISTEMIC_KINDS,
    LIFECYCLE_STATES,
    EpistemicContentCatalog,
    EpistemicFoundation,
)
from core.mind import CognitiveSuite


def _fact(epistemics: EpistemicFoundation, marker: str, *, confidence=0.8, stale_after=None):
    source_id = epistemics.register_source(
        f"unit://source/{marker}",
        source_type="test",
        title=f"Fonte {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = epistemics.discover(
        f"Conhecimento rastreável de teste {marker} com conteúdo suficientemente distinto.",
        epistemic_kind="fact",
        origin_type="test_source",
        origin_ref=f"unit://source/{marker}",
        source_id=source_id,
        confidence=confidence,
        stale_after=stale_after,
    )
    return record, source_id


def test_block2_catalog_is_exactly_1b_and_on_demand():
    catalog = EpistemicContentCatalog()
    stats = catalog.stats()

    assert EPISTEMIC_ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["canonical_nodes"] == 1_000
    assert stats["variants_per_node"] == 1_000_000
    assert stats["addressable_contents"] == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_knowledge_rows"] == 0

    first = catalog.content_id(0, 0)
    last = catalog.content_id(999, 999_999)
    assert first == "EPI-0000000001"
    assert last == "EPI-1000000000"
    assert catalog.get_variant(first)["id"] == first
    assert catalog.get_variant(last)["id"] == last
    assert catalog.get_variant("EPI-1000000001") is None


def test_block2_has_required_epistemic_kinds_and_lifecycle_states():
    assert {"fact", "hypothesis", "inference", "opinion", "fiction", "simulation", "unknown"}.issubset(EPISTEMIC_KINDS)
    assert LIFECYCLE_STATES == (
        "DISCOVERED",
        "QUARANTINED",
        "VERIFIED",
        "CANONICAL",
        "SUPERSEDED",
        "RETRACTED",
    )


def test_trace_preserves_origin_source_learning_time_confidence_and_history():
    epistemics = EpistemicFoundation()
    marker = uuid4().hex
    record, source_id = _fact(epistemics, marker)

    trace = epistemics.trace(record["record_id"])
    assert trace["record"]["lifecycle_state"] == "DISCOVERED"
    assert trace["record"]["epistemic_kind"] == "fact"
    assert trace["origin_source"]["source_id"] == source_id
    assert trace["origin_source"]["reliability"] == 1.0
    assert trace["epistemic_summary"]["where_from"] == f"unit://source/{marker}"
    assert trace["epistemic_summary"]["when_learned"]
    assert trace["revisions"][0]["event_type"] == "discovered"
    assert trace["could_be_wrong"] is True


def test_evidence_recalculates_confidence_and_verification_requires_evidence():
    epistemics = EpistemicFoundation()
    marker = uuid4().hex
    record, source_id = _fact(epistemics, marker, confidence=0.5)

    with pytest.raises(ValueError, match="VERIFIED exige"):
        epistemics.transition(record["record_id"], "VERIFIED", reason="sem evidência")

    evidence = epistemics.add_evidence(
        record["record_id"],
        "Medição primária confirmou a afirmação.",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
    )
    assert evidence["reliability"] == 1.0

    trace = epistemics.trace(record["record_id"])
    assert trace["record"]["confidence"] > 0.5
    assert trace["record"]["uncertainty"] < 1.0

    verified = epistemics.transition(record["record_id"], "VERIFIED", reason="evidência suficiente")
    assert verified["lifecycle_state"] == "VERIFIED"
    assert verified["last_verified_at"]


def test_canonical_is_gated_by_fact_evidence_confidence_temporality_and_conflicts():
    epistemics = EpistemicFoundation()
    marker = uuid4().hex
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    record, source_id = _fact(epistemics, marker, confidence=0.8, stale_after=future)
    epistemics.add_evidence(
        record["record_id"],
        "Fonte primária forte.",
        evidence_type="primary_source",
        source_id=source_id,
        strength=1.0,
    )
    epistemics.transition(record["record_id"], "VERIFIED", reason="validado")
    readiness = epistemics.canonical_readiness(record["record_id"])
    assert readiness["ready"] is True

    canonical = epistemics.transition(record["record_id"], "CANONICAL", reason="critérios atendidos")
    assert canonical["lifecycle_state"] == "CANONICAL"


def test_temporal_validity_detects_stale_and_expired_knowledge():
    epistemics = EpistemicFoundation()
    marker = uuid4().hex
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    record, _ = _fact(epistemics, marker, stale_after=past)
    temporal = epistemics.temporal_status(record["record_id"])
    assert temporal["state"] == "stale"
    assert temporal["is_outdated"] is True

    marker2 = uuid4().hex
    record2, _ = _fact(epistemics, marker2)
    epistemics.revise(record2["record_id"], {"valid_until": past}, reason="validade histórica")
    assert epistemics.temporal_status(record2["record_id"])["state"] == "expired"


def test_contradictions_quarantine_verified_or_canonical_records():
    epistemics = EpistemicFoundation()
    a, source_a = _fact(epistemics, uuid4().hex)
    b, source_b = _fact(epistemics, uuid4().hex)

    for record, source in ((a, source_a), (b, source_b)):
        epistemics.add_evidence(
            record["record_id"],
            "Evidência suficiente para verificação.",
            evidence_type="primary_source",
            source_id=source,
            strength=1.0,
        )
        epistemics.transition(record["record_id"], "VERIFIED", reason="verificado")

    epistemics.contradict(a["record_id"], b["record_id"], reason="resultados incompatíveis")
    assert epistemics.trace(a["record_id"])["record"]["lifecycle_state"] == "QUARANTINED"
    assert epistemics.trace(b["record_id"])["record"]["lifecycle_state"] == "QUARANTINED"
    assert epistemics.trace(a["record_id"])["contradictions"]


def test_revision_supersession_and_retraction_are_historicized():
    epistemics = EpistemicFoundation()
    old, old_source = _fact(epistemics, uuid4().hex)
    new, new_source = _fact(epistemics, uuid4().hex)

    for record, source in ((old, old_source), (new, new_source)):
        epistemics.add_evidence(
            record["record_id"],
            "Evidência primária.",
            evidence_type="primary_source",
            source_id=source,
            strength=1.0,
        )
        epistemics.transition(record["record_id"], "VERIFIED", reason="verificado")

    epistemics.revise(new["record_id"], {"confidence": 0.9}, reason="nova calibração")
    superseded = epistemics.supersede(old["record_id"], new["record_id"], reason="versão mais atual")
    assert superseded["lifecycle_state"] == "SUPERSEDED"
    assert any(r["relation"] == "superseded_by" for r in epistemics.trace(old["record_id"])["relations"])

    retracted = epistemics.retract(old["record_id"], reason="retirada definitiva")
    assert retracted["lifecycle_state"] == "RETRACTED"
    events = [r["event_type"] for r in epistemics.trace(old["record_id"])["revisions"]]
    assert "state_transition" in events


def test_daily_growth_automatically_creates_epistemic_trace_without_changing_legacy_counts():
    suite = CognitiveSuite()
    marker = uuid4().hex
    content = f"Informação validada e suficientemente longa para rastreabilidade epistêmica {marker}."
    record = {
        "content": content,
        "source": f"unit:{marker}",
        "source_type": "test",
        "confidence": 0.9,
    }
    result = suite.growth.ingest("reasoning", [record], target_count=1)
    assert result["accepted"] == 1

    record_id = suite.epistemics.stable_record_id(content)
    trace = suite.epistemics.trace(record_id)
    assert trace["record"]["lifecycle_state"] == "DISCOVERED"
    assert trace["record"]["origin_type"] == "knowledge_ingestion"
    assert trace["origin_source"]["locator"] == f"unit:{marker}"


def test_block2_handlers_are_explicit_and_do_not_capture_normal_chat():
    suite = CognitiveSuite()
    status = suite.handle("status bloco 2")
    assert "1000000000" in status
    assert "FUNDAÇÃO EPISTÊMICA" in status

    item = suite.handle("EPI-0000000001")
    assert "EPI-0000000001" in item
    assert suite.epistemics.handle("uma conversa normal") is None
