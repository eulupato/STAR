"""Persistência do BLOCO 3 sobre o mesmo SQLite oficial da STAR.

A camada organiza conhecimento canônico sem duplicar o ledger epistêmico nem o
Knowledge Graph. Claims/evidências continuam nas tabelas do BLOCO 2 e relações
semânticas continuam em ``knowledge_nodes``/``knowledge_edges``. Aqui ficam
apenas metadados canônicos, aliases, facetas, vínculos de claims, eventos,
namespaces de capacidade e o índice de consulta universal.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import unicodedata

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from database.cognitive_store import CognitiveStore
from database.database import engine
from database.epistemic_store import EpistemicStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True)


def _load(value: str | None, default=None):
    try:
        return json.loads(value) if value else ({} if default is None else default)
    except (json.JSONDecodeError, TypeError):
        return {} if default is None else default


def normalize_text(value: str) -> str:
    raw = " ".join(str(value or "").strip().split()).casefold()
    decomposed = unicodedata.normalize("NFKD", raw)
    asciiish = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[\w]+", asciiish, flags=re.UNICODE))


UNIVERSAL_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS universal_namespaces (
        namespace TEXT PRIMARY KEY,
        label TEXT NOT NULL,
        logical_capacity INTEGER NOT NULL,
        source TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS universal_knowledge (
        knowledge_id TEXT PRIMARY KEY,
        namespace TEXT NOT NULL,
        canonical_label TEXT NOT NULL,
        normalized_label TEXT NOT NULL,
        knowledge_type TEXT NOT NULL,
        canonical_claim_id TEXT NOT NULL,
        summary TEXT NOT NULL DEFAULT '',
        properties_json TEXT NOT NULL DEFAULT '{}',
        rules_json TEXT NOT NULL DEFAULT '[]',
        exceptions_json TEXT NOT NULL DEFAULT '[]',
        provenance_json TEXT NOT NULL DEFAULT '{}',
        valid_from TEXT,
        valid_until TEXT,
        revision INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(namespace, normalized_label, knowledge_type)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_universal_knowledge_namespace ON universal_knowledge(namespace)",
    "CREATE INDEX IF NOT EXISTS idx_universal_knowledge_label ON universal_knowledge(normalized_label)",
    "CREATE INDEX IF NOT EXISTS idx_universal_knowledge_type ON universal_knowledge(knowledge_type)",
    "CREATE INDEX IF NOT EXISTS idx_universal_knowledge_claim ON universal_knowledge(canonical_claim_id)",
    """CREATE TABLE IF NOT EXISTS universal_aliases (
        alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id TEXT NOT NULL,
        alias TEXT NOT NULL,
        normalized_alias TEXT NOT NULL,
        locale TEXT NOT NULL DEFAULT '',
        source_ref TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(knowledge_id, normalized_alias, locale)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_universal_alias_norm ON universal_aliases(normalized_alias)",
    "CREATE INDEX IF NOT EXISTS idx_universal_alias_knowledge ON universal_aliases(knowledge_id)",
    """CREATE TABLE IF NOT EXISTS universal_claim_links (
        link_id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id TEXT NOT NULL,
        record_id TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(knowledge_id, record_id, role)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_universal_claim_knowledge ON universal_claim_links(knowledge_id)",
    "CREATE INDEX IF NOT EXISTS idx_universal_claim_record ON universal_claim_links(record_id)",
    """CREATE TABLE IF NOT EXISTS universal_facets (
        facet_id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id TEXT NOT NULL,
        facet_type TEXT NOT NULL,
        value TEXT NOT NULL,
        normalized_value TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(knowledge_id, facet_type, normalized_value)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_universal_facet_lookup ON universal_facets(facet_type, normalized_value)",
    "CREATE INDEX IF NOT EXISTS idx_universal_facet_knowledge ON universal_facets(knowledge_id)",
    """CREATE TABLE IF NOT EXISTS universal_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_time TEXT NOT NULL,
        source_record_id TEXT,
        payload_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_universal_events_knowledge ON universal_events(knowledge_id)",
    "CREATE INDEX IF NOT EXISTS idx_universal_events_time ON universal_events(event_time)",
)

UNIVERSAL_FTS_SCHEMA = """CREATE VIRTUAL TABLE IF NOT EXISTS universal_knowledge_fts
USING fts5(
    knowledge_id UNINDEXED,
    canonical_label,
    summary,
    aliases,
    facets,
    tokenize='unicode61 remove_diacritics 2'
)"""


class UniversalKnowledgeStore:
    """Facade incremental que mantém um único ``star.db`` e um único grafo."""

    UPDATE_FIELDS = {
        "summary",
        "properties_json",
        "rules_json",
        "exceptions_json",
        "provenance_json",
        "valid_from",
        "valid_until",
    }

    def __init__(self, store: EpistemicStore | CognitiveStore | None = None):
        if isinstance(store, EpistemicStore):
            self.epistemic_store = store
        else:
            self.epistemic_store = EpistemicStore(store)
        self.fts5_available = False
        self._ensure_schema()

    def __getattr__(self, name):
        return getattr(self.epistemic_store, name)

    def _ensure_schema(self):
        with engine.begin() as conn:
            for ddl in UNIVERSAL_SCHEMA:
                conn.execute(text(ddl))
            try:
                conn.execute(text(UNIVERSAL_FTS_SCHEMA))
                self.fts5_available = True
            except OperationalError:
                self.fts5_available = False

    @staticmethod
    def _namespace(value: str) -> str:
        namespace = str(value or "").strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_-]{1,15}", namespace):
            raise ValueError("namespace universal inválido")
        return namespace

    def register_namespace(
        self,
        namespace: str,
        label: str,
        *,
        logical_capacity: int = 1_000_000_000,
        source: str | None = None,
        metadata=None,
    ) -> dict:
        namespace = self._namespace(namespace)
        capacity = int(logical_capacity)
        if capacity < 1:
            raise ValueError("logical_capacity deve ser positivo")
        now = _now()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO universal_namespaces(
                    namespace,label,logical_capacity,source,metadata_json,created_at,updated_at
                ) VALUES (:namespace,:label,:capacity,:source,:meta,:now,:now)
                ON CONFLICT(namespace) DO UPDATE SET
                    label=excluded.label,
                    logical_capacity=excluded.logical_capacity,
                    source=COALESCE(excluded.source,universal_namespaces.source),
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
            """), {
                "namespace": namespace,
                "label": str(label or namespace).strip() or namespace,
                "capacity": capacity,
                "source": source,
                "meta": _json(metadata),
                "now": now,
            })
        return self.get_namespace(namespace)

    def get_namespace(self, namespace: str) -> dict | None:
        namespace = self._namespace(namespace)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM universal_namespaces WHERE namespace=:namespace"),
                {"namespace": namespace},
            ).mappings().first()
        return None if row is None else {**dict(row), "metadata": _load(row["metadata_json"])}

    def list_namespaces(self) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM universal_namespaces ORDER BY namespace")).mappings().all()
        return [{**dict(row), "metadata": _load(row["metadata_json"])} for row in rows]

    def upsert_knowledge(
        self,
        knowledge_id: str,
        *,
        namespace: str,
        canonical_label: str,
        knowledge_type: str,
        canonical_claim_id: str,
        summary: str = "",
        properties=None,
        rules=None,
        exceptions=None,
        provenance=None,
        valid_from: str | None = None,
        valid_until: str | None = None,
    ) -> dict:
        namespace = self._namespace(namespace)
        if self.get_namespace(namespace) is None:
            raise ValueError(f"namespace não registrado: {namespace}")
        canonical_label = " ".join(str(canonical_label or "").strip().split())
        normalized = normalize_text(canonical_label)
        if not canonical_label or not normalized:
            raise ValueError("canonical_label vazio")
        if not str(canonical_claim_id or "").strip():
            raise ValueError("canonical_claim_id obrigatório")
        existing = self.get_knowledge(knowledge_id)
        now = _now()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO universal_knowledge(
                    knowledge_id,namespace,canonical_label,normalized_label,knowledge_type,
                    canonical_claim_id,summary,properties_json,rules_json,exceptions_json,
                    provenance_json,valid_from,valid_until,revision,created_at,updated_at
                ) VALUES (
                    :id,:namespace,:label,:normalized,:type,:claim,:summary,:properties,
                    :rules,:exceptions,:provenance,:valid_from,:valid_until,1,:now,:now
                )
                ON CONFLICT(knowledge_id) DO UPDATE SET
                    canonical_claim_id=excluded.canonical_claim_id,
                    summary=excluded.summary,
                    properties_json=excluded.properties_json,
                    rules_json=excluded.rules_json,
                    exceptions_json=excluded.exceptions_json,
                    provenance_json=excluded.provenance_json,
                    valid_from=excluded.valid_from,
                    valid_until=excluded.valid_until,
                    updated_at=excluded.updated_at
            """), {
                "id": knowledge_id,
                "namespace": namespace,
                "label": canonical_label,
                "normalized": normalized,
                "type": str(knowledge_type).strip(),
                "claim": str(canonical_claim_id).strip(),
                "summary": str(summary or "").strip(),
                "properties": _json(properties or {}),
                "rules": _json(list(rules or [])),
                "exceptions": _json(list(exceptions or [])),
                "provenance": _json(provenance or {}),
                "valid_from": valid_from,
                "valid_until": valid_until,
                "now": now,
            })
        self._sync_fts(knowledge_id)
        record = self.get_knowledge(knowledge_id)
        if record is None:
            raise RuntimeError("falha ao persistir conhecimento universal")
        record["created"] = existing is None
        return record

    def find_by_identity(self, namespace: str, canonical_label: str, knowledge_type: str) -> dict | None:
        namespace = self._namespace(namespace)
        normalized = normalize_text(canonical_label)
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT knowledge_id FROM universal_knowledge
                WHERE namespace=:namespace AND normalized_label=:label AND knowledge_type=:type
            """), {
                "namespace": namespace,
                "label": normalized,
                "type": str(knowledge_type).strip(),
            }).scalar_one_or_none()
        return self.get_knowledge(row) if row else None

    def get_knowledge(self, knowledge_id: str) -> dict | None:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM universal_knowledge WHERE knowledge_id=:id"),
                {"id": knowledge_id},
            ).mappings().first()
        if row is None:
            return None
        item = dict(row)
        item["properties"] = _load(item["properties_json"])
        item["rules"] = _load(item["rules_json"], [])
        item["exceptions"] = _load(item["exceptions_json"], [])
        item["provenance"] = _load(item["provenance_json"])
        item["aliases"] = self.aliases(knowledge_id)
        item["facets"] = self.facets(knowledge_id)
        item["claims"] = self.claim_links(knowledge_id)
        return item

    def add_alias(
        self,
        knowledge_id: str,
        alias: str,
        *,
        locale: str = "",
        source_ref: str | None = None,
    ) -> dict:
        if self.get_knowledge(knowledge_id) is None:
            raise KeyError(knowledge_id)
        alias = " ".join(str(alias or "").strip().split())
        normalized = normalize_text(alias)
        if not alias or not normalized:
            raise ValueError("alias vazio")
        locale = str(locale or "").strip()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT OR IGNORE INTO universal_aliases(
                    knowledge_id,alias,normalized_alias,locale,source_ref,created_at
                ) VALUES (:id,:alias,:normalized,:locale,:source,:now)
            """), {
                "id": knowledge_id,
                "alias": alias,
                "normalized": normalized,
                "locale": locale,
                "source": source_ref,
                "now": _now(),
            })
        self._sync_fts(knowledge_id)
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT * FROM universal_aliases
                WHERE knowledge_id=:id AND normalized_alias=:normalized AND locale=:locale
            """), {"id": knowledge_id, "normalized": normalized, "locale": locale}).mappings().one()
        return dict(row)

    def aliases(self, knowledge_id: str) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT * FROM universal_aliases WHERE knowledge_id=:id ORDER BY alias_id
            """), {"id": knowledge_id}).mappings().all()
        return [dict(row) for row in rows]

    def add_facet(self, knowledge_id: str, facet_type: str, value: str) -> dict:
        if self.get_knowledge(knowledge_id) is None:
            raise KeyError(knowledge_id)
        facet_type = str(facet_type or "").strip().lower()
        value = " ".join(str(value or "").strip().split())
        normalized = normalize_text(value)
        if not facet_type or not value or not normalized:
            raise ValueError("faceta exige tipo e valor")
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT OR IGNORE INTO universal_facets(
                    knowledge_id,facet_type,value,normalized_value,created_at
                ) VALUES (:id,:type,:value,:normalized,:now)
            """), {
                "id": knowledge_id,
                "type": facet_type,
                "value": value,
                "normalized": normalized,
                "now": _now(),
            })
        self._sync_fts(knowledge_id)
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT * FROM universal_facets
                WHERE knowledge_id=:id AND facet_type=:type AND normalized_value=:normalized
            """), {"id": knowledge_id, "type": facet_type, "normalized": normalized}).mappings().one()
        return dict(row)

    def facets(self, knowledge_id: str) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT * FROM universal_facets WHERE knowledge_id=:id ORDER BY facet_type,facet_id
            """), {"id": knowledge_id}).mappings().all()
        return [dict(row) for row in rows]

    def link_claim(self, knowledge_id: str, record_id: str, role: str) -> dict:
        if self.get_knowledge(knowledge_id) is None:
            raise KeyError(knowledge_id)
        if self.get_epistemic_record(record_id) is None:
            raise KeyError(record_id)
        role = str(role or "").strip().lower()
        if not role:
            raise ValueError("role vazio")
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT OR IGNORE INTO universal_claim_links(knowledge_id,record_id,role,created_at)
                VALUES (:knowledge,:record,:role,:now)
            """), {"knowledge": knowledge_id, "record": record_id, "role": role, "now": _now()})
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT * FROM universal_claim_links
                WHERE knowledge_id=:knowledge AND record_id=:record AND role=:role
            """), {"knowledge": knowledge_id, "record": record_id, "role": role}).mappings().one()
        return dict(row)

    def claim_links(self, knowledge_id: str) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT * FROM universal_claim_links WHERE knowledge_id=:id ORDER BY link_id
            """), {"id": knowledge_id}).mappings().all()
        return [dict(row) for row in rows]

    def record_event(
        self,
        knowledge_id: str,
        event_type: str,
        *,
        event_time: str | None = None,
        source_record_id: str | None = None,
        payload=None,
    ) -> dict:
        if self.get_knowledge(knowledge_id) is None:
            raise KeyError(knowledge_id)
        event_type = str(event_type or "").strip()
        if not event_type:
            raise ValueError("event_type vazio")
        now = _now()
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO universal_events(
                    knowledge_id,event_type,event_time,source_record_id,payload_json,created_at
                ) VALUES (:knowledge,:type,:time,:source,:payload,:now)
            """), {
                "knowledge": knowledge_id,
                "type": event_type,
                "time": event_time or now,
                "source": source_record_id,
                "payload": _json(payload or {}),
                "now": now,
            })
            event_id = int(result.lastrowid)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM universal_events WHERE event_id=:id"),
                {"id": event_id},
            ).mappings().one()
        return {**dict(row), "payload": _load(row["payload_json"])}

    def events(self, knowledge_id: str, limit: int = 100) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT * FROM universal_events
                WHERE knowledge_id=:id ORDER BY event_time DESC,event_id DESC LIMIT :limit
            """), {"id": knowledge_id, "limit": max(1, min(int(limit), 1000))}).mappings().all()
        return [{**dict(row), "payload": _load(row["payload_json"])} for row in rows]

    def update_knowledge(self, knowledge_id: str, changes: dict) -> dict:
        current = self.get_knowledge(knowledge_id)
        if current is None:
            raise KeyError(knowledge_id)
        unknown = set(changes) - self.UPDATE_FIELDS
        if unknown:
            raise ValueError("campos universais inválidos: " + ", ".join(sorted(unknown)))
        if not changes:
            return current
        params = {"id": knowledge_id, "now": _now()}
        assignments = []
        for index, (field, value) in enumerate(changes.items()):
            key = f"v{index}"
            if field == "properties_json":
                value = _json(value or {})
            elif field in {"rules_json", "exceptions_json"}:
                value = _json(list(value or []))
            elif field == "provenance_json":
                value = _json(value or {})
            else:
                value = str(value or "").strip() if field == "summary" else value
            assignments.append(f"{field}=:{key}")
            params[key] = value
        assignments.extend(("revision=revision+1", "updated_at=:now"))
        with engine.begin() as conn:
            conn.execute(
                text(f"UPDATE universal_knowledge SET {','.join(assignments)} WHERE knowledge_id=:id"),
                params,
            )
        self._sync_fts(knowledge_id)
        updated = self.get_knowledge(knowledge_id)
        if updated is None:
            raise RuntimeError("conhecimento universal desapareceu após atualização")
        return updated

    def _sync_fts(self, knowledge_id: str):
        if not self.fts5_available:
            return
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT canonical_label,summary FROM universal_knowledge WHERE knowledge_id=:id
            """), {"id": knowledge_id}).mappings().first()
            if row is None:
                return
            aliases = " ".join(
                x[0] for x in conn.execute(
                    text("SELECT alias FROM universal_aliases WHERE knowledge_id=:id"),
                    {"id": knowledge_id},
                ).all()
            )
            facets = " ".join(
                x[0] for x in conn.execute(
                    text("SELECT value FROM universal_facets WHERE knowledge_id=:id"),
                    {"id": knowledge_id},
                ).all()
            )
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM universal_knowledge_fts WHERE knowledge_id=:id"), {"id": knowledge_id})
                conn.execute(text("""
                    INSERT INTO universal_knowledge_fts(
                        knowledge_id,canonical_label,summary,aliases,facets
                    ) VALUES (:id,:label,:summary,:aliases,:facets)
                """), {
                    "id": knowledge_id,
                    "label": row["canonical_label"],
                    "summary": row["summary"],
                    "aliases": aliases,
                    "facets": facets,
                })
        except OperationalError:
            self.fts5_available = False

    def search(self, query: str, *, namespace: str | None = None, limit: int = 10) -> list[dict]:
        normalized = normalize_text(query)
        if not normalized:
            return []
        limit = max(1, min(int(limit), 100))
        namespace_value = self._namespace(namespace) if namespace else None
        ids: list[str] = []
        scores: dict[str, float] = {}

        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT knowledge_id FROM universal_knowledge
                WHERE normalized_label=:query AND (:namespace IS NULL OR namespace=:namespace)
                UNION
                SELECT a.knowledge_id FROM universal_aliases a
                JOIN universal_knowledge u ON u.knowledge_id=a.knowledge_id
                WHERE a.normalized_alias=:query AND (:namespace IS NULL OR u.namespace=:namespace)
            """), {"query": normalized, "namespace": namespace_value}).all()
        for row in rows:
            knowledge_id = row[0]
            if knowledge_id not in ids:
                ids.append(knowledge_id)
                scores[knowledge_id] = -100.0

        if self.fts5_available and len(ids) < limit:
            tokens = [t for t in normalized.split() if t][:12]
            match = " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens)
            if match:
                try:
                    with engine.connect() as conn:
                        rows = conn.execute(text("""
                            SELECT f.knowledge_id,
                                   bm25(universal_knowledge_fts,0.0,4.0,2.0,2.0,1.0) AS score
                            FROM universal_knowledge_fts f
                            JOIN universal_knowledge u ON u.knowledge_id=f.knowledge_id
                            WHERE universal_knowledge_fts MATCH :query
                              AND (:namespace IS NULL OR u.namespace=:namespace)
                            ORDER BY score LIMIT :limit
                        """), {
                            "query": match,
                            "namespace": namespace_value,
                            "limit": limit * 3,
                        }).all()
                    for knowledge_id, score in rows:
                        if knowledge_id not in ids:
                            ids.append(knowledge_id)
                            scores[knowledge_id] = float(score)
                except OperationalError:
                    self.fts5_available = False

        if len(ids) < limit:
            like = f"%{normalized}%"
            with engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT DISTINCT u.knowledge_id
                    FROM universal_knowledge u
                    LEFT JOIN universal_aliases a ON a.knowledge_id=u.knowledge_id
                    LEFT JOIN universal_facets f ON f.knowledge_id=u.knowledge_id
                    WHERE (:namespace IS NULL OR u.namespace=:namespace)
                      AND (
                        u.normalized_label LIKE :like OR
                        a.normalized_alias LIKE :like OR
                        f.normalized_value LIKE :like OR
                        lower(u.summary) LIKE :raw_like
                      )
                    ORDER BY u.updated_at DESC LIMIT :limit
                """), {
                    "namespace": namespace_value,
                    "like": like,
                    "raw_like": f"%{str(query).strip().lower()}%",
                    "limit": limit * 3,
                }).all()
            for row in rows:
                knowledge_id = row[0]
                if knowledge_id not in ids:
                    ids.append(knowledge_id)
                    scores[knowledge_id] = 100.0

        results = []
        for knowledge_id in ids[:limit]:
            item = self.get_knowledge(knowledge_id)
            if item:
                item["search_score"] = scores.get(knowledge_id)
                results.append(item)
        return results

    def query_facet(
        self,
        facet_type: str,
        value: str,
        *,
        namespace: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        normalized = normalize_text(value)
        namespace_value = self._namespace(namespace) if namespace else None
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT f.knowledge_id
                FROM universal_facets f
                JOIN universal_knowledge u ON u.knowledge_id=f.knowledge_id
                WHERE f.facet_type=:type AND f.normalized_value=:value
                  AND (:namespace IS NULL OR u.namespace=:namespace)
                ORDER BY u.updated_at DESC LIMIT :limit
            """), {
                "type": str(facet_type).strip().lower(),
                "value": normalized,
                "namespace": namespace_value,
                "limit": max(1, min(int(limit), 500)),
            }).all()
        return [item for row in rows if (item := self.get_knowledge(row[0])) is not None]

    def stats(self) -> dict:
        tables = {
            "namespaces": "universal_namespaces",
            "knowledge": "universal_knowledge",
            "aliases": "universal_aliases",
            "claim_links": "universal_claim_links",
            "facets": "universal_facets",
            "events": "universal_events",
        }
        out = {"fts5_available": self.fts5_available}
        with engine.connect() as conn:
            for key, table in tables.items():
                out[key] = int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one())
        return out
