"""SQLite local para entidades, relações, fontes e busca da STAR."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from threading import RLock
import unicodedata
import re
from typing import Iterable

from .entities import Entity, KnowledgeSource, Relationship


def normalize_search_text(value: str) -> str:
    text = unicodedata.normalize("NFD", str(value or "").lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


class KnowledgeStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    def _initialize(self):
        with self._lock, self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    original_name TEXT,
                    category TEXT NOT NULL,
                    universe TEXT,
                    publisher TEXT,
                    species TEXT,
                    gender TEXT,
                    origin TEXT,
                    origin_place TEXT,
                    status TEXT,
                    first_appearance TEXT,
                    description TEXT,
                    personality TEXT,
                    history_summary TEXT,
                    image TEXT,
                    search_text TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_entities_identity
                ON entities(normalized_name, COALESCE(universe, ''), category);

                CREATE INDEX IF NOT EXISTS idx_entities_universe
                ON entities(universe);

                CREATE INDEX IF NOT EXISTS idx_entities_category
                ON entities(category);

                CREATE TABLE IF NOT EXISTS aliases (
                    entity_id TEXT NOT NULL,
                    alias TEXT NOT NULL,
                    normalized_alias TEXT NOT NULL,
                    PRIMARY KEY(entity_id, normalized_alias),
                    FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_aliases_normalized
                ON aliases(normalized_alias);

                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    target_name TEXT NOT NULL,
                    target_id TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE(source_id, predicate, target_name),
                    FOREIGN KEY(source_id) REFERENCES entities(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_relationships_source
                ON relationships(source_id, predicate);

                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    page INTEGER,
                    url TEXT,
                    retrieved_at TEXT,
                    field_name TEXT,
                    UNIQUE(entity_id, source_type, source_ref, page, field_name),
                    FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sources_entity
                ON sources(entity_id);
                """
            )

    @staticmethod
    def _json(value) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _entity_search_text(entity: Entity) -> str:
        values = [
            entity.name,
            entity.original_name or "",
            " ".join(entity.aliases),
            entity.universe or "",
            entity.publisher or "",
            " ".join(entity.team),
            entity.species or "",
            entity.origin or "",
            entity.origin_place or "",
            " ".join(entity.occupation),
            " ".join(entity.affiliations),
            entity.description or "",
            " ".join(entity.powers),
            " ".join(entity.abilities),
            " ".join(entity.tags),
        ]
        return normalize_search_text(" ".join(values))

    def upsert_entity(self, entity: Entity) -> str:
        normalized_name = normalize_search_text(entity.name)
        search_text = self._entity_search_text(entity)
        with self._lock, self._connect() as db:
            existing = db.execute(
                """
                SELECT id FROM entities
                WHERE normalized_name = ?
                  AND COALESCE(universe, '') = COALESCE(?, '')
                  AND category = ?
                """,
                (normalized_name, entity.universe, entity.category),
            ).fetchone()
            if existing:
                entity.id = existing["id"]

            db.execute(
                """
                INSERT INTO entities (
                    id, name, normalized_name, original_name, category, universe,
                    publisher, species, gender, origin, origin_place, status,
                    first_appearance, description, personality, history_summary,
                    image, search_text, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    normalized_name=excluded.normalized_name,
                    original_name=excluded.original_name,
                    category=excluded.category,
                    universe=excluded.universe,
                    publisher=excluded.publisher,
                    species=excluded.species,
                    gender=excluded.gender,
                    origin=excluded.origin,
                    origin_place=excluded.origin_place,
                    status=excluded.status,
                    first_appearance=excluded.first_appearance,
                    description=excluded.description,
                    personality=excluded.personality,
                    history_summary=excluded.history_summary,
                    image=excluded.image,
                    search_text=excluded.search_text,
                    data_json=excluded.data_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    entity.id,
                    entity.name,
                    normalized_name,
                    entity.original_name,
                    entity.category,
                    entity.universe,
                    entity.publisher,
                    entity.species,
                    entity.gender,
                    entity.origin,
                    entity.origin_place,
                    entity.status,
                    entity.first_appearance,
                    entity.description,
                    entity.personality,
                    entity.history_summary,
                    entity.image,
                    search_text,
                    self._json(entity.to_dict()),
                ),
            )
            db.execute("DELETE FROM aliases WHERE entity_id = ?", (entity.id,))
            db.executemany(
                "INSERT OR IGNORE INTO aliases(entity_id, alias, normalized_alias) VALUES (?, ?, ?)",
                [
                    (entity.id, alias, normalize_search_text(alias))
                    for alias in entity.aliases
                    if str(alias).strip()
                ],
            )
            db.execute("DELETE FROM relationships WHERE source_id = ?", (entity.id,))
            db.executemany(
                """
                INSERT OR IGNORE INTO relationships
                (source_id, predicate, target_name, target_id, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        entity.id,
                        relation.predicate,
                        relation.target_name,
                        relation.target_id,
                        self._json(relation.metadata),
                    )
                    for relation in entity.relationships
                ],
            )
            db.execute("DELETE FROM sources WHERE entity_id = ?", (entity.id,))
            db.executemany(
                """
                INSERT OR IGNORE INTO sources
                (entity_id, source_type, source_ref, page, url, retrieved_at, field_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        entity.id,
                        source.source_type,
                        source.source_ref,
                        source.page,
                        source.url,
                        source.retrieved_at,
                        source.field_name,
                    )
                    for source in entity.sources
                ],
            )
        return entity.id

    def upsert_many(self, entities: Iterable[Entity]) -> int:
        count = 0
        for entity in entities:
            self.upsert_entity(entity)
            count += 1
        return count

    def _row_to_entity(self, row: sqlite3.Row) -> Entity:
        data = json.loads(row["data_json"])
        data["relationships"] = [
            Relationship(**item) for item in data.get("relationships", [])
        ]
        data["sources"] = [
            KnowledgeSource(**item) for item in data.get("sources", [])
        ]
        return Entity(**data)

    def get(self, entity_id: str) -> Entity | None:
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT * FROM entities WHERE id = ?", (str(entity_id),)
            ).fetchone()
        return self._row_to_entity(row) if row else None

    def find_exact(self, name_or_alias: str, universe: str | None = None) -> Entity | None:
        term = normalize_search_text(name_or_alias)
        with self._lock, self._connect() as db:
            params = [term]
            universe_sql = ""
            if universe:
                universe_sql = " AND e.universe = ?"
                params.append(universe)
            row = db.execute(
                f"""
                SELECT DISTINCT e.*
                FROM entities e
                LEFT JOIN aliases a ON a.entity_id = e.id
                WHERE (e.normalized_name = ? OR a.normalized_alias = ?)
                {universe_sql}
                LIMIT 1
                """,
                [term, term, *params[1:]],
            ).fetchone()
        return self._row_to_entity(row) if row else None

    def search(self, query: str = "", filters: dict | None = None, limit: int = 20) -> list[Entity]:
        normalized = normalize_search_text(query)
        tokens = [token for token in normalized.split() if token]
        filters = dict(filters or {})
        clauses = []
        params: list[object] = []

        if tokens:
            for token in tokens:
                clauses.append("e.search_text LIKE ?")
                params.append(f"%{token}%")

        for key in ("universe", "publisher", "category", "species", "status"):
            value = filters.get(key)
            if value:
                clauses.append(f"LOWER(COALESCE(e.{key}, '')) = LOWER(?)")
                params.append(str(value))

        sql = "SELECT DISTINCT e.* FROM entities e"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY e.name COLLATE NOCASE LIMIT ?"
        params.append(max(1, min(int(limit), 5000)))

        with self._lock, self._connect() as db:
            rows = db.execute(sql, params).fetchall()
        return [self._row_to_entity(row) for row in rows]

    def list_entities(self, category: str | None = None, universe: str | None = None, limit: int = 5000) -> list[Entity]:
        filters = {}
        if category:
            filters["category"] = category
        if universe:
            filters["universe"] = universe
        return self.search("", filters=filters, limit=limit)

    def relations(self, entity_id: str, predicate: str | None = None) -> list[Relationship]:
        params: list[object] = [str(entity_id)]
        sql = "SELECT predicate, target_name, target_id, metadata_json FROM relationships WHERE source_id = ?"
        if predicate:
            sql += " AND predicate = ?"
            params.append(predicate)
        sql += " ORDER BY predicate, target_name"
        with self._lock, self._connect() as db:
            rows = db.execute(sql, params).fetchall()
        return [
            Relationship(
                predicate=row["predicate"],
                target_name=row["target_name"],
                target_id=row["target_id"],
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
            for row in rows
        ]

    def count(self, category: str | None = None) -> int:
        with self._lock, self._connect() as db:
            if category:
                row = db.execute(
                    "SELECT COUNT(*) AS n FROM entities WHERE category = ?",
                    (category,),
                ).fetchone()
            else:
                row = db.execute("SELECT COUNT(*) AS n FROM entities").fetchone()
        return int(row["n"])
