"""Persistência do BLOCO 2 sobre o SQLite oficial da STAR.

Este módulo estende o ``CognitiveStore`` por composição: não cria outro banco,
memória ou fonte de verdade. As tabelas epistêmicas vivem no mesmo ``star.db``
e o facade delega todos os métodos cognitivos existentes ao store original.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Iterable

from sqlalchemy import text

from database.cognitive_store import CognitiveStore
from database.database import engine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True)


def _load(value: str | None):
    try:
        return json.loads(value or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


def _knowledge_id(content: str) -> str:
    normalized = " ".join(str(content or "").strip().split()).casefold()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20].upper()
    return f"KNOW-{digest}"


EPISTEMIC_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS epistemic_sources (
        source_id TEXT PRIMARY KEY,
        locator TEXT NOT NULL,
        source_type TEXT NOT NULL,
        title TEXT,
        reliability REAL NOT NULL DEFAULT 0.5,
        reliability_basis TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_sources_locator ON epistemic_sources(locator)",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_sources_type ON epistemic_sources(source_type)",
    """CREATE TABLE IF NOT EXISTS epistemic_records (
        record_id TEXT PRIMARY KEY,
        content_hash TEXT NOT NULL UNIQUE,
        content TEXT NOT NULL,
        epistemic_kind TEXT NOT NULL,
        lifecycle_state TEXT NOT NULL,
        origin_type TEXT NOT NULL,
        origin_ref TEXT NOT NULL,
        origin_source_id TEXT,
        confidence REAL NOT NULL DEFAULT 0.5,
        uncertainty REAL NOT NULL DEFAULT 0.5,
        learned_at TEXT NOT NULL,
        valid_from TEXT,
        valid_until TEXT,
        stale_after TEXT,
        last_verified_at TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_records_kind ON epistemic_records(epistemic_kind)",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_records_state ON epistemic_records(lifecycle_state)",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_records_source ON epistemic_records(origin_source_id)",
    """CREATE TABLE IF NOT EXISTS epistemic_evidence (
        evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT NOT NULL,
        source_id TEXT,
        evidence_type TEXT NOT NULL,
        stance TEXT NOT NULL,
        description TEXT NOT NULL,
        strength REAL NOT NULL DEFAULT 0.5,
        reliability REAL NOT NULL DEFAULT 0.5,
        observed_at TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_evidence_record ON epistemic_evidence(record_id)",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_evidence_source ON epistemic_evidence(source_id)",
    """CREATE TABLE IF NOT EXISTS epistemic_relations (
        relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_record_id TEXT NOT NULL,
        target_record_id TEXT NOT NULL,
        relation TEXT NOT NULL,
        weight REAL NOT NULL DEFAULT 1.0,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(source_record_id, target_record_id, relation)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_relations_source ON epistemic_relations(source_record_id)",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_relations_target ON epistemic_relations(target_record_id)",
    """CREATE TABLE IF NOT EXISTS epistemic_revisions (
        revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        from_state TEXT,
        to_state TEXT,
        reason TEXT NOT NULL,
        changes_json TEXT NOT NULL DEFAULT '{}',
        actor TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_revisions_record ON epistemic_revisions(record_id)",
)


class EpistemicStore:
    """Facade incremental do store cognitivo, preservando um único banco oficial."""

    RECORD_UPDATE_FIELDS = {
        "epistemic_kind",
        "lifecycle_state",
        "origin_type",
        "origin_ref",
        "origin_source_id",
        "confidence",
        "uncertainty",
        "valid_from",
        "valid_until",
        "stale_after",
        "last_verified_at",
        "metadata_json",
    }

    def __init__(self, cognitive_store: CognitiveStore | "EpistemicStore" | None = None):
        if isinstance(cognitive_store, EpistemicStore):
            self.cognitive_store = cognitive_store.cognitive_store
        else:
            self.cognitive_store = cognitive_store or CognitiveStore()
        self._ensure_schema()

    def __getattr__(self, name):
        return getattr(self.cognitive_store, name)

    def _ensure_schema(self):
        with engine.begin() as conn:
            for ddl in EPISTEMIC_SCHEMA:
                conn.execute(text(ddl))

    def upsert_epistemic_source(
        self,
        locator: str,
        *,
        source_type: str,
        title: str | None = None,
        reliability: float = 0.5,
        reliability_basis: str | None = None,
        metadata=None,
    ) -> str:
        locator = str(locator).strip()
        source_type = str(source_type).strip()
        digest = hashlib.sha256(f"{source_type}\n{locator}".encode("utf-8")).hexdigest()[:20].upper()
        source_id = f"SRC-{digest}"
        now = _now()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO epistemic_sources(
                    source_id,locator,source_type,title,reliability,reliability_basis,
                    metadata_json,created_at,updated_at
                ) VALUES (:id,:locator,:type,:title,:reliability,:basis,:meta,:now,:now)
                ON CONFLICT(source_id) DO UPDATE SET
                    title=COALESCE(excluded.title,epistemic_sources.title),
                    reliability=excluded.reliability,
                    reliability_basis=COALESCE(excluded.reliability_basis,epistemic_sources.reliability_basis),
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
            """), {
                "id": source_id,
                "locator": locator,
                "type": source_type,
                "title": title,
                "reliability": _clamp(reliability),
                "basis": reliability_basis,
                "meta": _json(metadata),
                "now": now,
            })
        return source_id

    def get_epistemic_source(self, source_id: str | None) -> dict | None:
        if not source_id:
            return None
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM epistemic_sources WHERE source_id=:id"),
                {"id": source_id},
            ).mappings().first()
        return None if row is None else {**dict(row), "metadata": _load(row["metadata_json"])}

    def create_epistemic_record(
        self,
        record_id: str,
        content: str,
        *,
        epistemic_kind: str,
        lifecycle_state: str,
        origin_type: str,
        origin_ref: str,
        origin_source_id: str | None = None,
        confidence: float = 0.5,
        uncertainty: float = 0.5,
        learned_at: str | None = None,
        valid_from: str | None = None,
        valid_until: str | None = None,
        stale_after: str | None = None,
        metadata=None,
    ) -> dict:
        normalized = " ".join(str(content or "").strip().split())
        content_hash = hashlib.sha256(normalized.casefold().encode("utf-8")).hexdigest()
        now = _now()
        created = False
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT OR IGNORE INTO epistemic_records(
                    record_id,content_hash,content,epistemic_kind,lifecycle_state,
                    origin_type,origin_ref,origin_source_id,confidence,uncertainty,
                    learned_at,valid_from,valid_until,stale_after,last_verified_at,
                    metadata_json,created_at,updated_at
                ) VALUES (
                    :id,:hash,:content,:kind,:state,:origin_type,:origin_ref,:source,
                    :confidence,:uncertainty,:learned,:valid_from,:valid_until,:stale_after,
                    NULL,:meta,:now,:now
                )
            """), {
                "id": record_id,
                "hash": content_hash,
                "content": normalized,
                "kind": epistemic_kind,
                "state": lifecycle_state,
                "origin_type": origin_type,
                "origin_ref": origin_ref,
                "source": origin_source_id,
                "confidence": _clamp(confidence),
                "uncertainty": _clamp(uncertainty),
                "learned": learned_at or now,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "stale_after": stale_after,
                "meta": _json(metadata),
                "now": now,
            })
            created = bool(result.rowcount)
            if created:
                conn.execute(text("""
                    INSERT INTO epistemic_revisions(
                        record_id,event_type,from_state,to_state,reason,changes_json,actor,created_at
                    ) VALUES (:id,'discovered',NULL,:state,'initial discovery',:changes,'epistemic-engine',:now)
                """), {
                    "id": record_id,
                    "state": lifecycle_state,
                    "changes": _json({"epistemic_kind": epistemic_kind, "origin_type": origin_type, "origin_ref": origin_ref}),
                    "now": now,
                })
        record = self.get_epistemic_record(record_id)
        if record is None:
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT record_id FROM epistemic_records WHERE content_hash=:hash"),
                    {"hash": content_hash},
                ).scalar_one_or_none()
            record = self.get_epistemic_record(row) if row else None
        if record is None:
            raise RuntimeError("falha ao persistir registro epistêmico")
        record["created"] = created
        return record

    def get_epistemic_record(self, record_id: str) -> dict | None:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM epistemic_records WHERE record_id=:id"),
                {"id": record_id},
            ).mappings().first()
        return None if row is None else {**dict(row), "metadata": _load(row["metadata_json"])}

    def update_epistemic_record(
        self,
        record_id: str,
        changes: dict,
        *,
        event_type: str,
        reason: str,
        actor: str,
    ) -> dict:
        current = self.get_epistemic_record(record_id)
        if current is None:
            raise KeyError(record_id)
        unknown = set(changes) - self.RECORD_UPDATE_FIELDS
        if unknown:
            raise ValueError("campos epistêmicos inválidos: " + ", ".join(sorted(unknown)))
        if not changes:
            return current

        params = {"id": record_id, "now": _now()}
        assignments = []
        serialized_changes = {}
        for index, (field, value) in enumerate(changes.items()):
            key = f"v{index}"
            if field in {"confidence", "uncertainty"}:
                value = _clamp(value)
            if field == "metadata_json":
                value = _json(value)
            assignments.append(f"{field}=:{key}")
            params[key] = value
            serialized_changes[field] = {
                "from": current.get("metadata") if field == "metadata_json" else current.get(field),
                "to": _load(value) if field == "metadata_json" else value,
            }
        assignments.append("updated_at=:now")
        old_state = current.get("lifecycle_state")
        new_state = changes.get("lifecycle_state", old_state)

        with engine.begin() as conn:
            conn.execute(
                text(f"UPDATE epistemic_records SET {','.join(assignments)} WHERE record_id=:id"),
                params,
            )
            conn.execute(text("""
                INSERT INTO epistemic_revisions(
                    record_id,event_type,from_state,to_state,reason,changes_json,actor,created_at
                ) VALUES (:id,:event,:from_state,:to_state,:reason,:changes,:actor,:now)
            """), {
                "id": record_id,
                "event": event_type,
                "from_state": old_state,
                "to_state": new_state,
                "reason": str(reason or "").strip(),
                "changes": _json(serialized_changes),
                "actor": str(actor or "system").strip() or "system",
                "now": params["now"],
            })
        updated = self.get_epistemic_record(record_id)
        if updated is None:
            raise RuntimeError("registro epistêmico desapareceu após atualização")
        return updated

    def add_epistemic_evidence(
        self,
        record_id: str,
        *,
        description: str,
        evidence_type: str,
        stance: str,
        source_id: str | None = None,
        strength: float = 0.5,
        reliability: float = 0.5,
        observed_at: str | None = None,
        metadata=None,
    ) -> dict:
        now = _now()
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO epistemic_evidence(
                    record_id,source_id,evidence_type,stance,description,strength,
                    reliability,observed_at,metadata_json,created_at
                ) VALUES (:record,:source,:type,:stance,:description,:strength,:reliability,:observed,:meta,:now)
            """), {
                "record": record_id,
                "source": source_id,
                "type": evidence_type,
                "stance": stance,
                "description": description,
                "strength": _clamp(strength),
                "reliability": _clamp(reliability),
                "observed": observed_at or now,
                "meta": _json(metadata),
                "now": now,
            })
            evidence_id = int(result.lastrowid)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM epistemic_evidence WHERE evidence_id=:id"),
                {"id": evidence_id},
            ).mappings().one()
        return {**dict(row), "metadata": _load(row["metadata_json"])}

    def epistemic_evidence(self, record_id: str, limit: int = 500) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT * FROM epistemic_evidence
                WHERE record_id=:id ORDER BY evidence_id ASC LIMIT :limit
            """), {"id": record_id, "limit": max(1, min(int(limit), 5000))}).mappings().all()
        return [{**dict(row), "metadata": _load(row["metadata_json"])} for row in rows]

    def add_epistemic_relation(
        self,
        source_record_id: str,
        target_record_id: str,
        relation: str,
        *,
        weight: float = 1.0,
        metadata=None,
    ) -> dict:
        now = _now()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO epistemic_relations(
                    source_record_id,target_record_id,relation,weight,metadata_json,created_at,updated_at
                ) VALUES (:source,:target,:relation,:weight,:meta,:now,:now)
                ON CONFLICT(source_record_id,target_record_id,relation) DO UPDATE SET
                    weight=excluded.weight,metadata_json=excluded.metadata_json,updated_at=excluded.updated_at
            """), {
                "source": source_record_id,
                "target": target_record_id,
                "relation": relation,
                "weight": _clamp(weight),
                "meta": _json(metadata),
                "now": now,
            })
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT * FROM epistemic_relations
                WHERE source_record_id=:source AND target_record_id=:target AND relation=:relation
            """), {"source": source_record_id, "target": target_record_id, "relation": relation}).mappings().one()
        return {**dict(row), "metadata": _load(row["metadata_json"])}

    def epistemic_relations(self, record_id: str, limit: int = 500) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT * FROM epistemic_relations
                WHERE source_record_id=:id OR target_record_id=:id
                ORDER BY relation_id ASC LIMIT :limit
            """), {"id": record_id, "limit": max(1, min(int(limit), 5000))}).mappings().all()
        return [{**dict(row), "metadata": _load(row["metadata_json"])} for row in rows]

    def epistemic_revisions(self, record_id: str, limit: int = 1000) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT * FROM epistemic_revisions
                WHERE record_id=:id ORDER BY revision_id ASC LIMIT :limit
            """), {"id": record_id, "limit": max(1, min(int(limit), 5000))}).mappings().all()
        return [{**dict(row), "changes": _load(row["changes_json"])} for row in rows]

    def epistemic_stats(self) -> dict:
        tables = {
            "sources": "epistemic_sources",
            "records": "epistemic_records",
            "evidence": "epistemic_evidence",
            "relations": "epistemic_relations",
            "revisions": "epistemic_revisions",
        }
        result = {}
        with engine.connect() as conn:
            for key, table in tables.items():
                result[key] = int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one())
            states = conn.execute(text("""
                SELECT lifecycle_state, COUNT(*) AS count
                FROM epistemic_records GROUP BY lifecycle_state
            """)).mappings().all()
        result["by_state"] = {row["lifecycle_state"]: int(row["count"]) for row in states}
        return result

    def ingest_facts(self, theme: str, records: Iterable[dict], *, target_count: int = 1_000_000, run_date: str | None = None) -> dict:
        """Preserva a ingestão legada e cria rastreabilidade epistêmica idempotente."""
        materialized = list(records)
        result = self.cognitive_store.ingest_facts(
            theme,
            materialized,
            target_count=target_count,
            run_date=run_date,
        )
        now = _now()
        for record in materialized:
            content = " ".join(str(record.get("content") or "").strip().split())
            locator = str(record.get("source") or "").strip()
            source_type = str(record.get("source_type") or "").strip()
            if len(content) < 20 or not locator or not source_type:
                continue
            reliability = _clamp(record.get("source_reliability", record.get("confidence", 0.5)))
            source_id = self.upsert_epistemic_source(
                locator,
                source_type=source_type,
                title=record.get("source_title"),
                reliability=reliability,
                reliability_basis="knowledge ingestion metadata",
                metadata={"theme": theme},
            )
            confidence = _clamp(record.get("confidence", 0.5))
            metadata = dict(record.get("metadata") or {})
            metadata.update({"theme": theme, "legacy_source_type": source_type})
            self.create_epistemic_record(
                _knowledge_id(content),
                content,
                epistemic_kind="fact",
                lifecycle_state="DISCOVERED",
                origin_type="knowledge_ingestion",
                origin_ref=locator,
                origin_source_id=source_id,
                confidence=confidence,
                uncertainty=1.0 - confidence,
                learned_at=str(record.get("retrieved_at") or now),
                valid_from=record.get("valid_from"),
                valid_until=record.get("valid_until"),
                stale_after=record.get("stale_after"),
                metadata=metadata,
            )
        return result
