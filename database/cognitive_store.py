"""Persistência cognitiva usando o mesmo SQLite da STAR.

Este módulo é uma camada de dados, não um segundo sistema de memória. Ele usa o
`engine` oficial de `database.database` e cria tabelas incrementais para memória
tipada, grafo, projetos, RAG, pesquisa, perfil e avaliação.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from database.database import engine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True)


def _load(value: str | None):
    try:
        return json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}


SCHEMA = (
    """CREATE TABLE IF NOT EXISTS cognitive_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        memory_key TEXT,
        content TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        importance REAL NOT NULL DEFAULT 0.5,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_cognitive_memory_kind ON cognitive_memory(kind)",
    "CREATE INDEX IF NOT EXISTS idx_cognitive_memory_key ON cognitive_memory(memory_key)",
    """CREATE TABLE IF NOT EXISTS knowledge_nodes (
        node_id TEXT PRIMARY KEY,
        node_type TEXT NOT NULL,
        label TEXT NOT NULL,
        data_json TEXT NOT NULL DEFAULT '{}',
        confidence REAL NOT NULL DEFAULT 1.0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS knowledge_edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        relation TEXT NOT NULL,
        weight REAL NOT NULL DEFAULT 1.0,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        UNIQUE(source_id, target_id, relation)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source ON knowledge_edges(source_id)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target ON knowledge_edges(target_id)",
    """CREATE TABLE IF NOT EXISTS cognitive_projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        objective TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'active',
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS cognitive_project_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_project_events_project ON cognitive_project_events(project_id)",
    """CREATE TABLE IF NOT EXISTS cognitive_user_model (
        model_key TEXT PRIMARY KEY,
        value_json TEXT NOT NULL,
        confidence REAL NOT NULL DEFAULT 1.0,
        source TEXT NOT NULL DEFAULT 'declared',
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS cognitive_documents (
        document_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        content_hash TEXT NOT NULL UNIQUE,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS cognitive_document_chunks (
        chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        content TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        UNIQUE(document_id, chunk_index)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_document_chunks_doc ON cognitive_document_chunks(document_id)",
    """CREATE TABLE IF NOT EXISTS cognitive_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        component TEXT NOT NULL,
        metric TEXT NOT NULL,
        score REAL NOT NULL,
        details_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_evaluations_component ON cognitive_evaluations(component)",
    """CREATE TABLE IF NOT EXISTS cognitive_research_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        title TEXT NOT NULL,
        url TEXT,
        doi TEXT,
        published TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_research_query ON cognitive_research_sources(query)",
    """CREATE TABLE IF NOT EXISTS cognitive_facts (
        content_hash TEXT PRIMARY KEY,
        theme TEXT NOT NULL,
        content TEXT NOT NULL,
        source TEXT NOT NULL,
        source_type TEXT NOT NULL,
        retrieved_at TEXT NOT NULL,
        confidence REAL NOT NULL DEFAULT 0.5,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_cognitive_facts_theme ON cognitive_facts(theme)",
    """CREATE TABLE IF NOT EXISTS cognitive_growth_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date TEXT NOT NULL,
        theme TEXT NOT NULL,
        target_count INTEGER NOT NULL,
        accepted_count INTEGER NOT NULL,
        duplicate_count INTEGER NOT NULL,
        rejected_count INTEGER NOT NULL,
        sources_count INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""",
)

FTS_SCHEMA = """CREATE VIRTUAL TABLE IF NOT EXISTS cognitive_document_fts
USING fts5(chunk_id UNINDEXED, title, source, content, tokenize='unicode61 remove_diacritics 2')"""


class CognitiveStore:
    def __init__(self):
        self.fts5_available = False
        self._ensure_schema()

    def _ensure_schema(self):
        with engine.begin() as conn:
            for ddl in SCHEMA:
                conn.execute(text(ddl))
            try:
                conn.execute(text(FTS_SCHEMA))
                self.fts5_available = True
            except OperationalError:
                self.fts5_available = False

    def remember(self, kind: str, content: str, *, key: str | None = None, metadata=None, importance: float = 0.5) -> int:
        now = _now()
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO cognitive_memory(kind, memory_key, content, metadata_json, importance, created_at, updated_at)
                VALUES (:kind, :key, :content, :meta, :importance, :now, :now)
            """), {"kind": kind, "key": key, "content": str(content), "meta": _json(metadata), "importance": float(importance), "now": now})
            return int(result.lastrowid)

    def recall(self, query: str, *, kinds: Iterable[str] | None = None, limit: int = 10) -> list[dict]:
        tokens = [t for t in re.findall(r"[\wÀ-ÿ]+", str(query).lower()) if len(t) > 1][:12]
        params = {"limit": max(1, min(int(limit), 100))}
        clauses = []
        for i, token in enumerate(tokens):
            params[f"q{i}"] = f"%{token}%"
            clauses.append(f"lower(content) LIKE :q{i}")
        where = " OR ".join(clauses) or "1=1"
        kind_values = tuple(kinds or ())
        if kind_values:
            holders = []
            for i, kind in enumerate(kind_values):
                params[f"k{i}"] = kind
                holders.append(f":k{i}")
            where = f"({where}) AND kind IN ({','.join(holders)})"
        sql = text(f"""
            SELECT id, kind, memory_key, content, metadata_json, importance, created_at, updated_at
            FROM cognitive_memory WHERE {where}
            ORDER BY importance DESC, id DESC LIMIT :limit
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()
        return [{**dict(row), "metadata": _load(row["metadata_json"])} for row in rows]

    def upsert_node(self, node_id: str, node_type: str, label: str, *, data=None, confidence: float = 1.0):
        now = _now()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO knowledge_nodes(node_id,node_type,label,data_json,confidence,created_at,updated_at)
                VALUES (:id,:type,:label,:data,:confidence,:now,:now)
                ON CONFLICT(node_id) DO UPDATE SET
                  node_type=excluded.node_type,label=excluded.label,data_json=excluded.data_json,
                  confidence=excluded.confidence,updated_at=excluded.updated_at
            """), {"id": node_id, "type": node_type, "label": label, "data": _json(data), "confidence": float(confidence), "now": now})
        return node_id

    def add_edge(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0, metadata=None):
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO knowledge_edges(source_id,target_id,relation,weight,metadata_json,created_at)
                VALUES (:s,:t,:r,:w,:m,:now)
                ON CONFLICT(source_id,target_id,relation) DO UPDATE SET
                  weight=excluded.weight, metadata_json=excluded.metadata_json
            """), {"s": source_id, "t": target_id, "r": relation, "w": float(weight), "m": _json(metadata), "now": _now()})

    def neighbors(self, node_id: str, *, relation: str | None = None, limit: int = 50) -> list[dict]:
        params = {"id": node_id, "limit": max(1, min(int(limit), 500))}
        rel = ""
        if relation:
            rel = " AND e.relation=:relation"
            params["relation"] = relation
        with engine.connect() as conn:
            rows = conn.execute(text(f"""
                SELECT e.source_id,e.target_id,e.relation,e.weight,e.metadata_json,
                       n.node_type,n.label,n.data_json,n.confidence
                FROM knowledge_edges e
                LEFT JOIN knowledge_nodes n ON n.node_id = CASE WHEN e.source_id=:id THEN e.target_id ELSE e.source_id END
                WHERE (e.source_id=:id OR e.target_id=:id){rel}
                ORDER BY e.weight DESC LIMIT :limit
            """), params).mappings().all()
        return [{**dict(r), "metadata": _load(r["metadata_json"]), "node_data": _load(r["data_json"])} for r in rows]

    def create_project(self, name: str, objective: str = "", metadata=None) -> dict:
        now = _now()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO cognitive_projects(name,objective,status,metadata_json,created_at,updated_at)
                VALUES (:name,:objective,'active',:meta,:now,:now)
                ON CONFLICT(name) DO UPDATE SET objective=excluded.objective,metadata_json=excluded.metadata_json,updated_at=excluded.updated_at
            """), {"name": name.strip(), "objective": objective.strip(), "meta": _json(metadata), "now": now})
        return self.get_project(name)

    def get_project(self, name: str) -> dict | None:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM cognitive_projects WHERE lower(name)=lower(:name)"), {"name": name.strip()}).mappings().first()
        return None if row is None else {**dict(row), "metadata": _load(row["metadata_json"])}

    def list_projects(self, status: str | None = None, limit: int = 100) -> list[dict]:
        params = {"limit": max(1, min(int(limit), 500))}
        where = ""
        if status:
            where = "WHERE status=:status"
            params["status"] = status
        with engine.connect() as conn:
            rows = conn.execute(text(f"SELECT * FROM cognitive_projects {where} ORDER BY updated_at DESC LIMIT :limit"), params).mappings().all()
        return [{**dict(r), "metadata": _load(r["metadata_json"])} for r in rows]

    def add_project_event(self, project_id: int, event_type: str, content: str, metadata=None):
        now = _now()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO cognitive_project_events(project_id,event_type,content,metadata_json,created_at)
                VALUES (:pid,:type,:content,:meta,:now)
            """), {"pid": int(project_id), "type": event_type, "content": content, "meta": _json(metadata), "now": now})
            conn.execute(text("UPDATE cognitive_projects SET updated_at=:now WHERE project_id=:pid"), {"now": now, "pid": int(project_id)})

    def project_events(self, project_id: int, limit: int = 100) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT * FROM cognitive_project_events WHERE project_id=:pid ORDER BY id ASC LIMIT :limit
            """), {"pid": int(project_id), "limit": max(1, min(int(limit), 1000))}).mappings().all()
        return [{**dict(r), "metadata": _load(r["metadata_json"])} for r in rows]

    def set_user_model(self, key: str, value, *, confidence: float = 1.0, source: str = "declared"):
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO cognitive_user_model(model_key,value_json,confidence,source,updated_at)
                VALUES (:key,:value,:confidence,:source,:now)
                ON CONFLICT(model_key) DO UPDATE SET value_json=excluded.value_json,
                  confidence=excluded.confidence,source=excluded.source,updated_at=excluded.updated_at
            """), {"key": key, "value": _json(value), "confidence": float(confidence), "source": source, "now": _now()})

    def get_user_model(self, key: str | None = None):
        with engine.connect() as conn:
            if key is not None:
                row = conn.execute(text("SELECT * FROM cognitive_user_model WHERE model_key=:key"), {"key": key}).mappings().first()
                return None if row is None else {**dict(row), "value": _load(row["value_json"])}
            rows = conn.execute(text("SELECT * FROM cognitive_user_model ORDER BY model_key")).mappings().all()
        return {r["model_key"]: {**dict(r), "value": _load(r["value_json"])} for r in rows}

    def add_document(self, source: str, title: str, content: str, chunks: list[str], *, metadata=None) -> tuple[int, bool]:
        digest = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
        with engine.begin() as conn:
            existing = conn.execute(text("SELECT document_id FROM cognitive_documents WHERE content_hash=:h"), {"h": digest}).scalar_one_or_none()
            if existing is not None:
                return int(existing), False
            result = conn.execute(text("""
                INSERT INTO cognitive_documents(source,title,content_hash,metadata_json,created_at)
                VALUES (:source,:title,:hash,:meta,:now)
            """), {"source": source, "title": title, "hash": digest, "meta": _json(metadata), "now": _now()})
            doc_id = int(result.lastrowid)
            for index, chunk in enumerate(chunks):
                r = conn.execute(text("""
                    INSERT INTO cognitive_document_chunks(document_id,chunk_index,content,metadata_json)
                    VALUES (:doc,:idx,:content,:meta)
                """), {"doc": doc_id, "idx": index, "content": chunk, "meta": _json(metadata)})
                if self.fts5_available:
                    conn.execute(text("INSERT INTO cognitive_document_fts(chunk_id,title,source,content) VALUES (:id,:title,:source,:content)"), {"id": int(r.lastrowid), "title": title, "source": source, "content": chunk})
        return doc_id, True

    def search_documents(self, query: str, limit: int = 5) -> list[dict]:
        limit = max(1, min(int(limit), 50))
        tokens = [t for t in re.findall(r"[\wÀ-ÿ]+", str(query).lower()) if len(t) > 1][:12]
        if self.fts5_available and tokens:
            match = " OR ".join(f'"{t.replace(chr(34), "")}"' for t in tokens)
            with engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT f.chunk_id,f.title,f.source,f.content,rank,
                           c.document_id,c.chunk_index,c.metadata_json
                    FROM cognitive_document_fts f
                    JOIN cognitive_document_chunks c ON c.chunk_id=CAST(f.chunk_id AS INTEGER)
                    WHERE cognitive_document_fts MATCH :query
                    ORDER BY rank LIMIT :limit
                """), {"query": match, "limit": limit}).mappings().all()
            return [{**dict(r), "metadata": _load(r["metadata_json"])} for r in rows]
        params = {"limit": limit}
        clauses = []
        for i, token in enumerate(tokens):
            params[f"q{i}"] = f"%{token}%"
            clauses.append(f"lower(c.content) LIKE :q{i}")
        where = " OR ".join(clauses) or "1=1"
        with engine.connect() as conn:
            rows = conn.execute(text(f"""
                SELECT c.chunk_id,d.title,d.source,c.content,c.document_id,c.chunk_index,c.metadata_json
                FROM cognitive_document_chunks c JOIN cognitive_documents d ON d.document_id=c.document_id
                WHERE {where} ORDER BY c.chunk_id DESC LIMIT :limit
            """), params).mappings().all()
        return [{**dict(r), "metadata": _load(r["metadata_json"])} for r in rows]

    def record_evaluation(self, component: str, metric: str, score: float, details=None):
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO cognitive_evaluations(component,metric,score,details_json,created_at)
                VALUES (:component,:metric,:score,:details,:now)
            """), {"component": component, "metric": metric, "score": float(score), "details": _json(details), "now": _now()})

    def evaluations(self, component: str | None = None, limit: int = 100) -> list[dict]:
        params = {"limit": max(1, min(int(limit), 1000))}
        where = ""
        if component:
            where = "WHERE component=:component"
            params["component"] = component
        with engine.connect() as conn:
            rows = conn.execute(text(f"SELECT * FROM cognitive_evaluations {where} ORDER BY id DESC LIMIT :limit"), params).mappings().all()
        return [{**dict(r), "details": _load(r["details_json"])} for r in rows]

    def cache_research_sources(self, query: str, sources: list[dict]):
        with engine.begin() as conn:
            for source in sources:
                conn.execute(text("""
                    INSERT INTO cognitive_research_sources(query,title,url,doi,published,metadata_json,created_at)
                    VALUES (:query,:title,:url,:doi,:published,:meta,:now)
                """), {"query": query, "title": source.get("title", ""), "url": source.get("url"), "doi": source.get("doi"), "published": source.get("published"), "meta": _json(source), "now": _now()})

    def ingest_facts(self, theme: str, records: Iterable[dict], *, target_count: int = 1_000_000, run_date: str | None = None) -> dict:
        accepted = duplicate = rejected = 0
        sources = set()
        now = _now()
        with engine.begin() as conn:
            for record in records:
                content = str(record.get("content") or "").strip()
                source = str(record.get("source") or "").strip()
                source_type = str(record.get("source_type") or "").strip()
                retrieved = str(record.get("retrieved_at") or now)
                if len(content) < 20 or not source or not source_type:
                    rejected += 1
                    continue
                digest = hashlib.sha256((theme + "\n" + content).encode("utf-8", errors="ignore")).hexdigest()
                result = conn.execute(text("""
                    INSERT OR IGNORE INTO cognitive_facts(content_hash,theme,content,source,source_type,retrieved_at,confidence,metadata_json,created_at)
                    VALUES (:hash,:theme,:content,:source,:stype,:retrieved,:confidence,:meta,:now)
                """), {"hash": digest, "theme": theme, "content": content, "source": source, "stype": source_type, "retrieved": retrieved, "confidence": float(record.get("confidence", 0.5)), "meta": _json(record.get("metadata")), "now": now})
                if result.rowcount:
                    accepted += 1
                    sources.add(source)
                else:
                    duplicate += 1
            status = "complete" if accepted >= target_count else "partial"
            conn.execute(text("""
                INSERT INTO cognitive_growth_runs(run_date,theme,target_count,accepted_count,duplicate_count,rejected_count,sources_count,status,created_at)
                VALUES (:date,:theme,:target,:accepted,:duplicate,:rejected,:sources,:status,:now)
            """), {"date": run_date or now[:10], "theme": theme, "target": int(target_count), "accepted": accepted, "duplicate": duplicate, "rejected": rejected, "sources": len(sources), "status": status, "now": now})
        return {"theme": theme, "target": int(target_count), "accepted": accepted, "duplicates": duplicate, "rejected": rejected, "sources": len(sources), "status": status}

    def stats(self) -> dict:
        tables = {
            "memories": "cognitive_memory", "nodes": "knowledge_nodes", "edges": "knowledge_edges",
            "projects": "cognitive_projects", "documents": "cognitive_documents", "chunks": "cognitive_document_chunks",
            "evaluations": "cognitive_evaluations", "research_sources": "cognitive_research_sources", "facts": "cognitive_facts",
        }
        out = {"fts5_available": self.fts5_available}
        with engine.connect() as conn:
            for key, table in tables.items():
                out[key] = int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one())
        return out
