"""Camada semântica híbrida sobre o RAG existente da STAR.

Mantém SQLite/FTS5 como fonte de verdade. Embeddings são índices derivados e podem
ser reconstruídos. Sentence Transformers é opcional; sem ele existe fallback local
hashing para robustez, explicitamente identificado como não-neural.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import re
from sqlalchemy import text

from database.database import engine
from database.cognitive_store import CognitiveStore


class HashingEmbeddingBackend:
    name = "hashing-v1"
    neural = False

    def __init__(self, dimensions: int = 384):
        self.dimensions = max(64, min(int(dimensions), 2048))

    def encode(self, texts: list[str]) -> list[list[float]]:
        result = []
        for text_value in texts:
            tokens = re.findall(r"[\wÀ-ÿ]+", str(text_value).lower())
            features = Counter(tokens)
            features.update("#" + "".join(g) for token in tokens for g in zip(token, token[1:], token[2:]) if len(token) >= 3)
            vector = [0.0] * self.dimensions
            for feature, count in features.items():
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
                bucket = int.from_bytes(digest, "little") % self.dimensions
                sign = -1.0 if digest[0] & 1 else 1.0
                vector[bucket] += sign * (1.0 + math.log1p(count))
            norm = math.sqrt(sum(v * v for v in vector)) or 1.0
            result.append([v / norm for v in vector])
        return result


class SentenceTransformerBackend:
    neural = True

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.name = f"sentence-transformers:{model_name}"
        self.dimensions = int(self.model.get_sentence_embedding_dimension())

    def encode(self, texts: list[str]) -> list[list[float]]:
        values = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [[float(x) for x in row] for row in values]


class HybridSemanticRAG:
    def __init__(self, store: CognitiveStore | None = None, *, prefer_neural: bool = True, model_name: str | None = None):
        self.store = store or CognitiveStore()
        self.backend_error = None
        if prefer_neural:
            try:
                self.backend = SentenceTransformerBackend(model_name or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            except Exception as exc:
                self.backend_error = f"{type(exc).__name__}: {exc}"
                self.backend = HashingEmbeddingBackend()
        else:
            self.backend = HashingEmbeddingBackend()
        self._ensure_schema()

    def _ensure_schema(self):
        with engine.begin() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS cognitive_chunk_embeddings (
                chunk_id INTEGER NOT NULL,
                backend TEXT NOT NULL,
                dimensions INTEGER NOT NULL,
                vector_json TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(chunk_id, backend)
            )"""))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_backend ON cognitive_chunk_embeddings(backend)"))

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b)) / ((math.sqrt(sum(x*x for x in a)) or 1.0) * (math.sqrt(sum(y*y for y in b)) or 1.0))

    def index_missing(self, *, limit: int = 500, batch_size: int = 32) -> dict:
        limit = max(1, min(int(limit), 10000)); batch_size = max(1, min(int(batch_size), 128))
        with engine.connect() as conn:
            rows = conn.execute(text("""SELECT c.chunk_id,c.content FROM cognitive_document_chunks c
                LEFT JOIN cognitive_chunk_embeddings e ON e.chunk_id=c.chunk_id AND e.backend=:b
                WHERE e.chunk_id IS NULL ORDER BY c.chunk_id LIMIT :n"""), {"b": self.backend.name, "n": limit}).mappings().all()
        indexed = 0
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            vectors = self.backend.encode([row["content"] for row in batch])
            with engine.begin() as conn:
                for row, vector in zip(batch, vectors):
                    digest = hashlib.sha256(row["content"].encode("utf-8", errors="ignore")).hexdigest()
                    conn.execute(text("""INSERT INTO cognitive_chunk_embeddings(chunk_id,backend,dimensions,vector_json,content_hash)
                        VALUES(:c,:b,:d,:v,:h) ON CONFLICT(chunk_id,backend) DO UPDATE SET
                        dimensions=excluded.dimensions,vector_json=excluded.vector_json,content_hash=excluded.content_hash,updated_at=CURRENT_TIMESTAMP"""),
                        {"c": int(row["chunk_id"]), "b": self.backend.name, "d": self.backend.dimensions,
                         "v": json.dumps(vector, separators=(",", ":")), "h": digest})
                    indexed += 1
        return {"indexed": indexed, "backend": self.backend.name, "neural": self.backend.neural, "remaining_unknown": len(rows) == limit}

    def search(self, query: str, *, top_k: int = 5, candidate_limit: int = 2000, lexical_weight: float = 0.35) -> list[dict]:
        query = str(query).strip()
        if not query:
            return []
        top_k = max(1, min(int(top_k), 50)); lexical_weight = max(0.0, min(float(lexical_weight), 1.0))
        self.index_missing(limit=min(candidate_limit, 500))
        query_vec = self.backend.encode([query])[0]
        with engine.connect() as conn:
            rows = conn.execute(text("""SELECT e.chunk_id,e.vector_json,c.document_id,c.chunk_index,c.content,
                d.title,d.source,d.metadata_json FROM cognitive_chunk_embeddings e
                JOIN cognitive_document_chunks c ON c.chunk_id=e.chunk_id
                JOIN cognitive_documents d ON d.document_id=c.document_id
                WHERE e.backend=:b ORDER BY e.chunk_id DESC LIMIT :n"""), {"b": self.backend.name, "n": max(top_k, min(int(candidate_limit), 10000))}).mappings().all()
        lexical = {int(row["chunk_id"]): rank for rank, row in enumerate(self.store.search_documents(query, min(50, candidate_limit)), 1)}
        results = []
        for row in rows:
            vector = json.loads(row["vector_json"])
            semantic = self._cosine(query_vec, vector)
            lex_rank = lexical.get(int(row["chunk_id"]))
            lex_score = 0.0 if lex_rank is None else 1.0 / lex_rank
            score = (1.0 - lexical_weight) * semantic + lexical_weight * lex_score
            results.append({"chunk_id": int(row["chunk_id"]), "document_id": int(row["document_id"]),
                            "chunk_index": int(row["chunk_index"]), "title": row["title"], "source": row["source"],
                            "content": row["content"], "semantic_score": semantic, "lexical_score": lex_score,
                            "score": score, "backend": self.backend.name})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def stats(self) -> dict:
        with engine.connect() as conn:
            count = int(conn.execute(text("SELECT COUNT(*) FROM cognitive_chunk_embeddings WHERE backend=:b"), {"b": self.backend.name}).scalar_one())
        return {"status": "active-local", "backend": self.backend.name, "neural": self.backend.neural,
                "indexed_chunks": count, "backend_error": self.backend_error,
                "sqlite_vec_optional": True, "source_of_truth": "SQLite FTS5/document tables"}
