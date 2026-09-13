"""Índice local e seguro de arquivos para o futuro STAR Operator."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from sqlalchemy import text

from database.database import engine


class FileIndex:
    DEFAULT_EXCLUDES = {".git", ".venv", "__pycache__", "node_modules", ".idea", ".vscode"}

    def __init__(self):
        with engine.begin() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS operator_files (
                path TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                suffix TEXT NOT NULL,
                size INTEGER NOT NULL,
                modified_ns INTEGER NOT NULL,
                content_fingerprint TEXT,
                indexed_at TEXT NOT NULL
            )"""))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_operator_files_name ON operator_files(name)"))

    @staticmethod
    def _fingerprint(path: Path, max_bytes: int = 65536) -> str | None:
        if path.stat().st_size > 20 * 1024 * 1024:
            return None
        try:
            with path.open("rb") as handle:
                sample = handle.read(max_bytes)
            return hashlib.sha256(sample).hexdigest()
        except OSError:
            return None

    def index(self, root: str | Path, *, recursive: bool = True, max_files: int = 10000, excludes=None) -> dict:
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(root)
        excluded = self.DEFAULT_EXCLUDES | set(excludes or ())
        iterator = root.rglob("*") if recursive else root.glob("*")
        indexed = skipped = 0; now = datetime.now(timezone.utc).isoformat()
        for path in iterator:
            if indexed >= max(1, min(int(max_files), 100000)):
                break
            if not path.is_file() or any(part in excluded for part in path.parts):
                skipped += 1; continue
            try:
                stat = path.stat()
                with engine.begin() as conn:
                    conn.execute(text("""INSERT INTO operator_files(path,name,suffix,size,modified_ns,content_fingerprint,indexed_at)
                    VALUES(:p,:n,:s,:z,:m,:f,:i) ON CONFLICT(path) DO UPDATE SET
                    name=excluded.name,suffix=excluded.suffix,size=excluded.size,modified_ns=excluded.modified_ns,
                    content_fingerprint=excluded.content_fingerprint,indexed_at=excluded.indexed_at"""),
                    {"p": str(path), "n": path.name, "s": path.suffix.lower(), "z": int(stat.st_size),
                     "m": int(stat.st_mtime_ns), "f": self._fingerprint(path), "i": now})
                indexed += 1
            except OSError:
                skipped += 1
        return {"root": str(root), "indexed": indexed, "skipped": skipped, "recursive": bool(recursive)}

    def search(self, query: str, *, suffix: str | None = None, limit: int = 50) -> list[dict]:
        tokens = [x for x in str(query).lower().split() if x][:8]
        params = {"n": max(1, min(int(limit), 500))}; clauses = []
        for i, token in enumerate(tokens):
            params[f"q{i}"] = f"%{token}%"; clauses.append(f"lower(name) LIKE :q{i}")
        where = " AND ".join(clauses) if clauses else "1=1"
        if suffix:
            params["suffix"] = suffix.lower() if str(suffix).startswith(".") else "." + str(suffix).lower()
            where += " AND suffix=:suffix"
        with engine.connect() as conn:
            rows = conn.execute(text(f"SELECT * FROM operator_files WHERE {where} ORDER BY name LIMIT :n"), params).mappings().all()
        return [dict(row) for row in rows]

    def stats(self) -> dict:
        with engine.connect() as conn:
            count = int(conn.execute(text("SELECT COUNT(*) FROM operator_files")).scalar_one())
        return {"status": "alpha-read-only", "indexed_files": count, "background_scan": False,
                "writes_or_deletes": False, "semantic_content_index": False}
