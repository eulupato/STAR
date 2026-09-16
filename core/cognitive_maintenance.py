"""BLOCO 32 — manutenção cognitiva integrada da STAR.

Mantém os stores e o Knowledge Graph existentes; não cria outra memória, outro
grafo ou outro banco. Operações potencialmente destrutivas são opt-in, bounded
e auditáveis. A manutenção trabalha por janelas/candidatos: nunca carrega 1B de
conteúdos simultaneamente.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import re
import unicodedata
from typing import Any

from sqlalchemy import text

from core.block_knowledge_catalog import StructuredBillionCatalog
from database.database import engine


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    raw = unicodedata.normalize("NFKD", _clean(value))
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch)).casefold()
    return " ".join(re.findall(r"[a-z0-9]+", raw))


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return default


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


DOMAINS = {
    "consolidation": ("episodic", "semantic", "conversation", "project", "people", "social", "temporal", "autobiographical", "cross_memory", "canonicalization"),
    "deduplication": ("exact", "normalized", "alias", "claim", "evidence", "memory", "node", "edge", "source", "cross_namespace"),
    "compression": ("summary", "reference", "cluster", "history", "event", "source_preserving", "lossless", "bounded", "cold_data", "retrieval_view"),
    "reorganization": ("taxonomy", "facet", "index", "namespace", "relation", "temporal", "context", "source", "priority", "partition"),
    "aliases": ("resolve", "collision", "canonical", "locale", "entity", "person", "concept", "legacy", "ambiguous", "provenance"),
    "confidence": ("recalibrate", "support", "refute", "coverage", "source_reliability", "staleness", "uncertainty", "conflict", "revision", "audit"),
    "contradictions": ("detect", "link", "compare", "scope", "temporal", "context", "source", "unresolved", "resolved", "history"),
    "graph": ("dangling_edge", "orphan_node", "duplicate_node", "weight", "relation", "connectivity", "taxonomy_path", "cross_link", "integrity", "repair"),
    "retention": ("working", "hot", "warm", "cold", "archive", "forget_candidate", "importance", "recency", "relevance", "reversible"),
    "cache_archive": ("cache_hit", "cache_miss", "invalidate", "ttl", "lru", "archive_plan", "archive_snapshot", "restore", "storage_budget", "maintenance_report"),
}
LENSES = ("identity", "evidence", "temporal", "context", "relation", "risk", "cost", "quality", "traceability", "reversibility")
AXES = (
    ("scope", ("single", "small", "medium", "large", "namespace", "memory", "graph", "epistemic", "cross_block", "global")),
    ("priority", ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9")),
    ("confidence", ("unknown", "very_low", "low", "mid_low", "medium", "mid_high", "high", "very_high", "conflicted", "audited")),
    ("age", ("instant", "session", "day", "week", "month", "quarter", "year", "historical", "archival", "unknown")),
    ("action", ("inspect", "plan", "link", "consolidate", "reindex", "recalibrate", "archive", "repair", "defer", "report")),
    ("safety", ("read_only", "reversible", "source_preserving", "authorized", "dry_run", "bounded", "audited", "rollback_ready", "manual_review", "blocked")),
)
CATALOG = StructuredBillionCatalog(
    namespace="B32",
    domains=DOMAINS,
    lenses=LENSES,
    axes=AXES,
    truthfulness_note="1B representa combinações de manutenção endereçáveis; não 1B rotinas materializadas nem alterações automáticas.",
)
ADDRESSABLE_CONTENTS = CATALOG.addressable_contents


class CognitiveMaintenance:
    """Manutenção bounded sobre B02/B03/B13/Knowledge Graph/cache existentes."""

    NAMESPACE = "B32"
    MAX_WINDOW = 5_000
    MAX_RESULTS = 500

    def __init__(
        self,
        knowledge,
        *,
        memory_continuity,
        epistemics,
        graph,
        self_improvement=None,
    ):
        self.knowledge = knowledge
        self.memory_continuity = memory_continuity
        self.epistemics = epistemics
        self.graph = graph
        self.self_improvement = self_improvement
        self.catalog = CATALOG
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 32 — MANUTENÇÃO COGNITIVA",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/cognitive_maintenance.py",
            metadata={
                "materialization": "on-demand",
                "bounded_windows": True,
                "destructive_by_default": False,
                "source_preserving_consolidation": True,
                "logical_archive": True,
                "archive_reversible": True,
                "shared_database": "star.db",
                "shared_graph": True,
                "parallel_memory": False,
            },
        )

    @staticmethod
    def _bounded(value: int, maximum: int) -> int:
        return max(1, min(int(value), maximum))

    def capacity_contract(self, *, first: int = 1, last: int = 36) -> dict:
        namespaces = {item["namespace"]: item for item in self.knowledge.store.list_namespaces()}
        blocks = []
        for number in range(int(first), int(last) + 1):
            namespace = f"B{number:02d}"
            item = namespaces.get(namespace)
            capacity = int(item["logical_capacity"]) if item else None
            blocks.append({
                "block": namespace,
                "registered": item is not None,
                "logical_capacity": capacity,
                "one_billion_ready": capacity == 1_000_000_000,
                "source": item.get("source") if item else None,
            })
        return {
            "blocks": blocks,
            "registered": sum(1 for item in blocks if item["registered"]),
            "one_billion_ready": sum(1 for item in blocks if item["one_billion_ready"]),
            "missing": [item["block"] for item in blocks if not item["registered"]],
            "invalid_capacity": [item["block"] for item in blocks if item["registered"] and not item["one_billion_ready"]],
            "rule": "capacidade lógica não equivale a fatos materializados; cada bloco é recuperado sob demanda",
        }

    def duplicate_memory_candidates(self, *, window: int = 2_000, limit: int = 100) -> list[dict]:
        window = self._bounded(window, self.MAX_WINDOW)
        limit = self._bounded(limit, self.MAX_RESULTS)
        with engine.connect() as conn:
            rows = conn.execute(text("""
                WITH recent AS (
                    SELECT id,kind,content,importance,created_at
                    FROM cognitive_memory ORDER BY id DESC LIMIT :window
                )
                SELECT kind, lower(trim(content)) AS normalized_content,
                       COUNT(*) AS copies, MIN(id) AS first_id, MAX(id) AS last_id,
                       MAX(importance) AS max_importance
                FROM recent
                GROUP BY kind, lower(trim(content))
                HAVING COUNT(*) > 1
                ORDER BY copies DESC, last_id DESC LIMIT :limit
            """), {"window": window, "limit": limit}).mappings().all()
        return [dict(row) for row in rows]

    def alias_collisions(self, *, limit: int = 100) -> list[dict]:
        limit = self._bounded(limit, self.MAX_RESULTS)
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT normalized_alias, COUNT(DISTINCT knowledge_id) AS targets,
                       GROUP_CONCAT(DISTINCT knowledge_id) AS knowledge_ids
                FROM universal_aliases
                GROUP BY normalized_alias
                HAVING COUNT(DISTINCT knowledge_id) > 1
                ORDER BY targets DESC, normalized_alias LIMIT :limit
            """), {"limit": limit}).mappings().all()
        return [dict(row) for row in rows]

    def resolve_alias(self, alias: str, *, namespace: str | None = None, limit: int = 20) -> dict:
        alias = _clean(alias)
        if not alias:
            raise ValueError("alias vazio")
        results = self.knowledge.store.search(alias, namespace=namespace, limit=self._bounded(limit, 100))
        exact = []
        normalized = _norm(alias)
        for item in results:
            labels = {_norm(item.get("canonical_label"))}
            labels.update(_norm(row.get("alias")) for row in item.get("aliases", ()))
            if normalized in labels:
                exact.append(item)
        candidates = exact or results
        return {
            "alias": alias,
            "namespace": namespace,
            "status": "resolved" if len(candidates) == 1 else ("ambiguous" if candidates else "unknown"),
            "candidate_ids": [item["knowledge_id"] for item in candidates[:limit]],
            "candidates": candidates[:limit],
            "automatic_merge": False,
        }

    def contradictions(self, *, limit: int = 100) -> list[dict]:
        limit = self._bounded(limit, self.MAX_RESULTS)
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT r.source_record_id,r.target_record_id,r.relation,r.weight,
                       s.content AS source_content,t.content AS target_content
                FROM epistemic_relations r
                LEFT JOIN epistemic_records s ON s.record_id=r.source_record_id
                LEFT JOIN epistemic_records t ON t.record_id=r.target_record_id
                WHERE lower(r.relation)='contradicts'
                ORDER BY r.weight DESC, r.relation_id DESC LIMIT :limit
            """), {"limit": limit}).mappings().all()
        return [dict(row) for row in rows]

    def confidence_recalibration(self, record_id: str, *, apply: bool = False) -> dict:
        current = self.epistemics.store.get_epistemic_record(record_id)
        if current is None:
            raise KeyError(record_id)
        evidence = self.epistemics.store.epistemic_evidence(record_id, limit=500)
        support = refute = neutral = 0.0
        for item in evidence:
            weight = _clamp(item.get("strength"), 0.5) * _clamp(item.get("reliability"), 0.5)
            stance = str(item.get("stance") or "neutral").casefold()
            if stance == "support":
                support += weight
            elif stance in {"refute", "contradict"}:
                refute += weight
            else:
                neutral += weight
        decisive = support + refute
        coverage = min(1.0, decisive / 3.0)
        evidence_probability = 0.5 if decisive == 0 else support / decisive
        old = _clamp(current.get("confidence"), 0.5)
        recommended = max(0.0, min(1.0, old * (1.0 - coverage) + evidence_probability * coverage))
        uncertainty = max(0.0, min(1.0, 1.0 - coverage * abs((support - refute) / decisive))) if decisive else 1.0
        result = {
            "record_id": record_id,
            "old_confidence": old,
            "recommended_confidence": recommended,
            "recommended_uncertainty": uncertainty,
            "support_weight": support,
            "refute_weight": refute,
            "neutral_weight": neutral,
            "evidence_count": len(evidence),
            "applied": False,
        }
        if apply and evidence:
            updated = self.epistemics.store.update_epistemic_record(
                record_id,
                {"confidence": recommended, "uncertainty": uncertainty},
                event_type="confidence_recalibrated",
                reason="B32 evidence-weighted recalibration",
                actor="B32-cognitive-maintenance",
            )
            result["applied"] = True
            result["updated"] = updated
        return result

    def graph_integrity(self, *, limit: int = 100, repair: bool = False) -> dict:
        limit = self._bounded(limit, self.MAX_RESULTS)
        with engine.connect() as conn:
            dangling = conn.execute(text("""
                SELECT e.id,e.source_id,e.target_id,e.relation
                FROM knowledge_edges e
                LEFT JOIN knowledge_nodes s ON s.node_id=e.source_id
                LEFT JOIN knowledge_nodes t ON t.node_id=e.target_id
                WHERE s.node_id IS NULL OR t.node_id IS NULL
                ORDER BY e.id LIMIT :limit
            """), {"limit": limit}).mappings().all()
        rows = [dict(row) for row in dangling]
        removed = 0
        if repair and rows:
            ids = [int(row["id"]) for row in rows]
            holders = ",".join(f":id{i}" for i in range(len(ids)))
            params = {f"id{i}": value for i, value in enumerate(ids)}
            with engine.begin() as conn:
                removed = int(conn.execute(text(f"DELETE FROM knowledge_edges WHERE id IN ({holders})"), params).rowcount or 0)
        return {
            "dangling_edges": rows,
            "dangling_count": len(rows),
            "repaired": removed,
            "bounded": True,
            "repair_policy": "only edges whose source or target node is absent",
        }

    def consolidation_plan(self, *, window: int = 2_000, limit: int = 50) -> dict:
        duplicates = self.duplicate_memory_candidates(window=window, limit=limit)
        return {
            "duplicate_groups": duplicates,
            "suggested_action": "use B13 consolidate with source/reference, preserving original memories",
            "automatic_deletion": False,
            "source_memories_preserved": True,
        }

    def consolidate_memories(
        self,
        memory_ids,
        summary: str,
        *,
        source: str,
        reference: str,
        meaning: str = "",
    ) -> dict:
        """Delegates consolidation to B13; sources are preserved and linked."""
        return self.memory_continuity.consolidate(
            memory_ids,
            summary,
            source=source,
            reference=reference,
            meaning=meaning,
        )

    def compress_memories(
        self,
        memory_ids,
        summary: str,
        *,
        source: str,
        reference: str,
        meaning: str = "",
        archive_sources: bool = False,
    ) -> dict:
        """Creates a B13 summary view and optionally archives sources logically.

        Compression never destroys provenance. The detailed memories remain in the
        same official store and can be restored/recalled for audit.
        """
        ids = list(dict.fromkeys(int(value) for value in memory_ids))[: self.MAX_RESULTS]
        if not ids:
            raise ValueError("compressão requer ao menos uma memória")
        consolidated = self.consolidate_memories(
            ids,
            summary,
            source=source,
            reference=reference,
            meaning=meaning,
        )
        archive_result = None
        if archive_sources:
            archive_result = self.archive_memories(
                ids,
                reason=f"compressed into memory {consolidated.get('memory_id')}",
                apply=True,
            )
        return {
            "mode": "source-preserving-summary",
            "summary_memory": consolidated,
            "source_memory_ids": ids,
            "source_memories_preserved": True,
            "sources_logically_archived": bool(archive_sources),
            "archive": archive_result,
        }

    def _memory_archive_records(self, memory_ids) -> tuple[list[dict], list[int]]:
        ids = list(dict.fromkeys(int(value) for value in memory_ids))[: self.MAX_RESULTS]
        records = []
        missing = []
        for memory_id in ids:
            record = self.memory_continuity.memory_record(memory_id)
            if record is None:
                missing.append(memory_id)
            else:
                records.append(record)
        return records, missing

    def archive_memories(self, memory_ids, *, reason: str, apply: bool = False) -> dict:
        """Logical, reversible archive in existing cognitive_memory metadata."""
        reason = _clean(reason)
        if not reason:
            raise ValueError("arquivamento exige motivo")
        records, missing = self._memory_archive_records(memory_ids)
        plan = {
            "memory_ids": [int(item["id"]) for item in records],
            "missing": missing,
            "reason": reason,
            "apply": bool(apply),
            "physical_deletion": False,
            "reversible": True,
            "archived": 0,
        }
        if not apply or not records:
            return plan

        archived_at = _now()
        with engine.begin() as conn:
            for record in records:
                metadata = deepcopy(record.get("metadata") or {})
                history = list(metadata.get("b32_archive_history") or [])[-31:]
                event = {"archived_at": archived_at, "reason": reason, "actor": "B32-cognitive-maintenance"}
                history.append(event)
                metadata["b32_archive_history"] = history
                metadata["b32_archive"] = event
                conn.execute(
                    text("UPDATE cognitive_memory SET metadata_json=:metadata,updated_at=:updated WHERE id=:id"),
                    {
                        "id": int(record["id"]),
                        "metadata": json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                        "updated": archived_at,
                    },
                )
        plan["archived"] = len(records)
        plan["archived_at"] = archived_at
        return plan

    def restore_archived_memories(self, memory_ids) -> dict:
        """Removes the current archive marker while preserving archive history."""
        records, missing = self._memory_archive_records(memory_ids)
        restored = 0
        restored_at = _now()
        with engine.begin() as conn:
            for record in records:
                metadata = deepcopy(record.get("metadata") or {})
                current = metadata.pop("b32_archive", None)
                if current is None:
                    continue
                history = list(metadata.get("b32_archive_history") or [])[-31:]
                history.append({"restored_at": restored_at, "actor": "B32-cognitive-maintenance"})
                metadata["b32_archive_history"] = history[-32:]
                conn.execute(
                    text("UPDATE cognitive_memory SET metadata_json=:metadata,updated_at=:updated WHERE id=:id"),
                    {
                        "id": int(record["id"]),
                        "metadata": json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                        "updated": restored_at,
                    },
                )
                restored += 1
        return {
            "restored": restored,
            "missing": missing,
            "physical_recreation": False,
            "history_preserved": True,
            "restored_at": restored_at,
        }

    def reorganization_plan(self, *, limit: int = 50) -> dict:
        """Inspects materialized namespaces only; logical 1B spaces are never scanned."""
        limit = self._bounded(limit, 100)
        namespaces = self.knowledge.store.list_namespaces()[:limit]
        materialized = []
        for item in namespaces:
            stats = self.knowledge.store.stats(namespace=item["namespace"])
            materialized.append({
                "namespace": item["namespace"],
                "logical_capacity": int(item["logical_capacity"]),
                "materialized_knowledge": int(stats.get("knowledge", 0)),
                "aliases": int(stats.get("aliases", 0)),
                "facets": int(stats.get("facets", 0)),
                "claim_links": int(stats.get("claim_links", 0)),
            })
        return {
            "namespaces": materialized,
            "fts5_available": bool(self.knowledge.store.fts_available),
            "reindex_is_explicit": True,
            "logical_capacity_scanned": False,
            "materialized_rows_only": True,
        }

    def rebuild_search_index(self, *, apply: bool = False) -> dict:
        """Explicit FTS5 reorganization over materialized rows only."""
        if not self.knowledge.store.fts_available:
            return {"available": False, "applied": False, "reason": "FTS5 unavailable; textual fallback remains active"}
        if not apply:
            return {"available": True, "applied": False, "requires_explicit_apply": True}
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO universal_knowledge_fts(universal_knowledge_fts) VALUES('rebuild')"))
        self.knowledge.cache.invalidate()
        return {"available": True, "applied": True, "cache_invalidated": True, "scope": "materialized universal knowledge rows"}

    def functional_forgetting_candidates(
        self,
        *,
        max_importance: float = 0.2,
        window: int = 2_000,
        limit: int = 100,
    ) -> list[dict]:
        """Returns candidates only; forgetting never silently destroys a memory."""
        window = self._bounded(window, self.MAX_WINDOW)
        limit = self._bounded(limit, self.MAX_RESULTS)
        threshold = _clamp(max_importance, 0.2)
        with engine.connect() as conn:
            rows = conn.execute(text("""
                WITH recent AS (
                    SELECT id,kind,memory_key,content,importance,created_at,updated_at,metadata_json
                    FROM cognitive_memory ORDER BY id DESC LIMIT :window
                )
                SELECT * FROM recent
                WHERE importance <= :threshold AND kind NOT IN ('autobiographical','people','project','decision')
                ORDER BY importance ASC, id ASC LIMIT :limit
            """), {"window": window, "threshold": threshold, "limit": limit}).mappings().all()
        output = []
        for row in rows:
            item = dict(row)
            try:
                item["metadata"] = json.loads(item.get("metadata_json") or "{}")
            except (TypeError, json.JSONDecodeError):
                item["metadata"] = {}
            output.append(item)
        return output

    def cache_maintenance(self, *, invalidate: bool = False) -> dict:
        before = self.knowledge.cache.stats()
        if invalidate:
            self.knowledge.cache.invalidate()
        return {"before": before, "after": self.knowledge.cache.stats(), "invalidated": bool(invalidate)}

    def maintenance_cycle(self, *, repair_safe_graph_edges: bool = False, window: int = 2_000) -> dict:
        """Bounded maintenance pass; no destructive forgetting or alias merge."""
        started = _now()
        report = {
            "started_at": started,
            "duplicates": self.duplicate_memory_candidates(window=window, limit=100),
            "alias_collisions": self.alias_collisions(limit=100),
            "contradictions": self.contradictions(limit=100),
            "graph": self.graph_integrity(limit=100, repair=repair_safe_graph_edges),
            "forgetting_candidates": self.functional_forgetting_candidates(window=window, limit=100),
            "reorganization": self.reorganization_plan(limit=50),
            "cache": self.cache_maintenance(invalidate=False),
            "capacity": self.capacity_contract(),
            "bounded": True,
            "automatic_source_deletion": False,
            "automatic_alias_merge": False,
            "automatic_archive": False,
            "automatic_reindex": False,
        }
        issues = (
            len(report["duplicates"])
            + len(report["alias_collisions"])
            + len(report["contradictions"])
            + int(report["graph"]["dangling_count"])
        )
        report["issue_count"] = issues
        report["completed_at"] = _now()
        if self.self_improvement is not None:
            score = 1.0 if issues == 0 else max(0.0, 1.0 - min(issues, 100) / 100.0)
            self.self_improvement.record("B32", "maintenance_integrity", score, {
                "issues": issues,
                "bounded": True,
                "repair_safe_graph_edges": bool(repair_safe_graph_edges),
            })
        return report

    def stats(self) -> dict:
        capacity = self.capacity_contract()
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "bounded_windows": True,
            "max_window": self.MAX_WINDOW,
            "destructive_by_default": False,
            "source_preserving_consolidation": True,
            "source_preserving_compression": True,
            "logical_archive": True,
            "archive_reversible": True,
            "explicit_reindex_only": True,
            "registered_blocks_1b_ready": capacity["one_billion_ready"],
            "missing_block_namespaces": capacity["missing"],
        }

    def handle(self, text_value: str) -> str | None:
        raw = _clean(text_value)
        low = raw.casefold()
        if low in {"status bloco 32", "status manutenção cognitiva", "status manutencao cognitiva"}:
            stats = self.stats()
            return (
                f"🧹 BLOCO 32 — MANUTENÇÃO COGNITIVA: {stats['catalog']['addressable_contents']} "
                f"situações endereçáveis | bounded=SIM | destrutivo por padrão=NÃO | "
                f"blocos 1B registrados={stats['registered_blocks_1b_ready']}."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🧹 {item['id']} — {item['domain']} / {item['branch']} / {item['lens']}"
        return None
