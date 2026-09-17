"""Grupo 3 — conhecimento, pesquisa e documentos da STAR.

Integra capacidades novas aos sistemas existentes sem criar outro RAG, banco de
conhecimento ou mecanismo de memória. Documentos continuam no ``DocumentRAG`` e
no ``star.db``; pesquisa web produz evidência com proveniência; atualização
automática é append-only e nunca promove conteúdo web a fato canônico sozinha.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

from sqlalchemy import text

from core.cognitive_catalog import THEME_ORDER
from core.labs import DocumentRAG
from core.offline_dictionary import DEFAULT_DB, OfflineDictionaryStore
from database.database import engine
from modules.automation import ProactiveScheduler
from modules.internet import GeneralWebSearch


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value) -> str:
    return " ".join(str(value or "").split())


def _natural_key(path: str) -> list:
    return [int(x) if x.isdigit() else x.casefold() for x in re.split(r"(\d+)", path)]


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    source: str
    format: str
    extraction: str
    ocr_used: bool
    metadata: dict


class OCRExtractor:
    """OCR local sob demanda usando Tesseract; nunca envia imagem à rede."""

    def __init__(self, executable: str | None = None):
        self.executable = executable or os.getenv("STAR_TESSERACT") or shutil.which("tesseract")

    @property
    def available(self) -> bool:
        return bool(self.executable)

    def image(self, path: str | Path, *, language: str = "por+eng") -> str:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        if not self.available:
            raise RuntimeError("OCR local requer o executável Tesseract configurado em STAR_TESSERACT ou no PATH")
        proc = subprocess.run(
            [str(self.executable), str(path), "stdout", "-l", str(language), "--psm", "6"],
            text=True, capture_output=True, timeout=120, check=False,
        )
        if proc.returncode != 0:
            detail = _clean(proc.stderr)[-500:]
            raise RuntimeError(f"Tesseract falhou ({proc.returncode}): {detail or 'sem detalhe'}")
        return proc.stdout.strip()

    def pdf(self, path: str | Path, *, language: str = "por+eng", max_pages: int = 80) -> str:
        if not self.available:
            raise RuntimeError("OCR local requer Tesseract")
        try:
            import fitz  # PyMuPDF opcional; usado apenas para rasterizar PDF escaneado.
        except ImportError as exc:
            raise RuntimeError("OCR de PDF escaneado requer a dependência opcional PyMuPDF") from exc
        path = Path(path).expanduser().resolve()
        doc = fitz.open(str(path))
        pages = []
        try:
            for page_index in range(min(len(doc), max(1, min(int(max_pages), 500)))):
                page = doc.load_page(page_index)
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    temp_path = Path(tmp.name)
                    pix.save(str(temp_path))
                try:
                    value = self.image(temp_path, language=language)
                    if value:
                        pages.append(value)
                finally:
                    temp_path.unlink(missing_ok=True)
        finally:
            doc.close()
        return "\n\n".join(pages).strip()

    def stats(self) -> dict:
        return {
            "backend": "tesseract-cli",
            "available": self.available,
            "pdf_renderer": "PyMuPDF optional",
            "network_required": False,
        }


class DocumentExtractor:
    """Extrator único do RAG para texto, PDF, Office Open XML e imagens."""

    TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json", ".py", ".rst", ".log", ".yaml", ".yml"}
    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
    OFFICE_SUFFIXES = {".docx", ".xlsx", ".pptx"}
    SUPPORTED_SUFFIXES = TEXT_SUFFIXES | IMAGE_SUFFIXES | OFFICE_SUFFIXES | {".pdf"}

    def __init__(self, *, ocr: OCRExtractor | None = None):
        self.ocr = ocr or OCRExtractor()

    @staticmethod
    def _xml_text(payload: bytes, tags: tuple[str, ...] = ("t",)) -> list[str]:
        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            return []
        values = []
        for element in root.iter():
            local = element.tag.rsplit("}", 1)[-1]
            if local in tags and element.text:
                value = _clean(element.text)
                if value:
                    values.append(value)
        return values

    def _docx(self, path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            try:
                payload = archive.read("word/document.xml")
            except KeyError as exc:
                raise ValueError("DOCX sem word/document.xml") from exc
        return "\n".join(self._xml_text(payload)).strip()

    def _pptx(self, path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            names = sorted(
                (n for n in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                key=_natural_key,
            )
            slides = []
            for name in names:
                text_parts = self._xml_text(archive.read(name))
                if text_parts:
                    slides.append(" ".join(text_parts))
        return "\n\n".join(slides).strip()

    def _xlsx(self, path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            shared = []
            if "xl/sharedStrings.xml" in archive.namelist():
                try:
                    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                    for item in root.iter():
                        if item.tag.rsplit("}", 1)[-1] == "si":
                            pieces = [x.text or "" for x in item.iter() if x.tag.rsplit("}", 1)[-1] == "t"]
                            shared.append(_clean(" ".join(pieces)))
                except ET.ParseError:
                    shared = []
            sheet_names = sorted(
                (n for n in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)),
                key=_natural_key,
            )
            rows_out = []
            for name in sheet_names:
                try:
                    root = ET.fromstring(archive.read(name))
                except ET.ParseError:
                    continue
                for row in root.iter():
                    if row.tag.rsplit("}", 1)[-1] != "row":
                        continue
                    values = []
                    for cell in row:
                        if cell.tag.rsplit("}", 1)[-1] != "c":
                            continue
                        cell_type = cell.attrib.get("t")
                        value = ""
                        if cell_type == "inlineStr":
                            value = " ".join(x.text or "" for x in cell.iter() if x.tag.rsplit("}", 1)[-1] == "t")
                        else:
                            raw = next((x.text for x in cell if x.tag.rsplit("}", 1)[-1] == "v"), None)
                            if raw is not None:
                                if cell_type == "s":
                                    try:
                                        value = shared[int(raw)]
                                    except (ValueError, IndexError):
                                        value = raw
                                else:
                                    value = raw
                        value = _clean(value)
                        if value:
                            values.append(value)
                    if values:
                        rows_out.append(" | ".join(values))
        return "\n".join(rows_out).strip()

    def _pdf(self, path: Path, *, ocr_if_needed: bool, ocr_language: str) -> tuple[str, bool, str]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf não está instalado") from exc
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        text_value = "\n\n".join(x for x in pages if x).strip()
        useful_chars = len(re.sub(r"\s+", "", text_value))
        if useful_chars >= max(40, len(reader.pages) * 12):
            return text_value, False, "pypdf"
        if not ocr_if_needed:
            return text_value, False, "pypdf-low-text"
        ocr_text = self.ocr.pdf(path, language=ocr_language)
        return ocr_text or text_value, bool(ocr_text), "pypdf+tesseract" if ocr_text else "pypdf-low-text"

    def extract(self, path: str | Path, *, ocr_if_needed: bool = True, ocr_language: str = "por+eng") -> ExtractedDocument:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        size = path.stat().st_size
        if size > 100 * 1024 * 1024:
            raise ValueError("arquivo acima do limite de 100 MB")
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_SUFFIXES:
            raise ValueError(f"formato não suportado: {suffix}")
        ocr_used = False
        if suffix in self.TEXT_SUFFIXES:
            value = path.read_text(encoding="utf-8", errors="replace")
            extraction = "text"
        elif suffix == ".docx":
            value, extraction = self._docx(path), "docx-ooxml"
        elif suffix == ".pptx":
            value, extraction = self._pptx(path), "pptx-ooxml"
        elif suffix == ".xlsx":
            value, extraction = self._xlsx(path), "xlsx-ooxml"
        elif suffix == ".pdf":
            value, ocr_used, extraction = self._pdf(path, ocr_if_needed=ocr_if_needed, ocr_language=ocr_language)
        else:
            if not ocr_if_needed:
                raise ValueError("imagem requer OCR habilitado")
            value = self.ocr.image(path, language=ocr_language)
            ocr_used, extraction = True, "tesseract"
        value = str(value or "").strip()
        return ExtractedDocument(
            text=value,
            source=str(path),
            format=suffix.removeprefix("."),
            extraction=extraction,
            ocr_used=ocr_used,
            metadata={"size_bytes": size, "modified_ns": path.stat().st_mtime_ns, "local_only": True},
        )

    def stats(self) -> dict:
        return {
            "formats": sorted(s.removeprefix(".") for s in self.SUPPORTED_SUFFIXES),
            "office_open_xml_without_extra_dependency": True,
            "ocr": self.ocr.stats(),
        }


class EnhancedDocumentRAG(DocumentRAG):
    """O mesmo DocumentRAG, apenas com extração ampliada antes da ingestão."""

    def __init__(self, store=None, *, extractor: DocumentExtractor | None = None):
        super().__init__(store)
        self.extractor = extractor or DocumentExtractor()

    def ingest_file(self, path: str | Path, *, metadata=None, ocr_if_needed: bool = True) -> dict:
        extracted = self.extractor.extract(path, ocr_if_needed=ocr_if_needed)
        if not extracted.text:
            raise ValueError("documento sem texto indexável após extração/OCR")
        merged = dict(metadata or {})
        merged.update({
            "format": extracted.format,
            "extraction": extracted.extraction,
            "ocr_used": extracted.ocr_used,
            "provenance": extracted.source,
            "local_only": True,
        })
        result = self.ingest_text(extracted.text, source=extracted.source, title=Path(extracted.source).name, metadata=merged)
        result.update({"format": extracted.format, "extraction": extracted.extraction, "ocr_used": extracted.ocr_used})
        return result


class LocalTextVectorizer:
    """Embeddings locais: modelo local opcional; fallback vetorial determinístico."""

    DIMENSIONS = 256

    def __init__(self):
        self.model = None
        self.backend = "hashed-text-vector"
        model_path = str(os.getenv("STAR_EMBEDDING_MODEL") or "").strip()
        if model_path and Path(model_path).expanduser().exists():
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(str(Path(model_path).expanduser()), local_files_only=True)
                self.backend = "sentence-transformers-local"
            except (ImportError, OSError, TypeError, ValueError):
                self.model = None

    @staticmethod
    def _normalize(text_value: str) -> str:
        value = unicodedata.normalize("NFKD", str(text_value or "").casefold())
        return "".join(c for c in value if not unicodedata.combining(c))

    def vectorize(self, text_value: str) -> list[float]:
        text_value = str(text_value or "")[:120_000]
        if self.model is not None:
            vector = self.model.encode([text_value], normalize_embeddings=True, show_progress_bar=False)[0]
            return [float(x) for x in vector]
        normalized = self._normalize(text_value)
        tokens = re.findall(r"[a-z0-9]{2,}", normalized)
        features = tokens[:12000]
        for token in tokens[:5000]:
            padded = f"^{token}$"
            features.extend(padded[i:i + 3] for i in range(max(0, len(padded) - 2)))
        vector = [0.0] * self.DIMENSIONS
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8", errors="ignore"), digest_size=4).digest()
            raw = int.from_bytes(digest, "big")
            index = raw % self.DIMENSIONS
            vector[index] += -1.0 if raw & 1 else 1.0
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]

    @staticmethod
    def similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        return float(sum(x * y for x, y in zip(a, b)))


_FILE_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS star_file_semantic_index (
        path TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        suffix TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        modified_ns INTEGER NOT NULL,
        sample_text TEXT NOT NULL,
        vector_json TEXT NOT NULL,
        vector_backend TEXT NOT NULL,
        indexed_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_star_file_semantic_title ON star_file_semantic_index(title)",
)


class SemanticFileSearch:
    """Índice vetorial local de arquivos; indexação explícita e não bloqueia a UI."""

    IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache"}

    def __init__(self, *, extractor: DocumentExtractor | None = None):
        self.extractor = extractor or DocumentExtractor()
        self.vectorizer = LocalTextVectorizer()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._progress = {"running": False, "root": None, "indexed": 0, "skipped": 0, "errors": 0, "finished_at": None}
        with engine.begin() as conn:
            for ddl in _FILE_SCHEMA:
                conn.execute(text(ddl))

    def _candidate_files(self, root: Path, max_files: int):
        count = 0
        for path in root.rglob("*"):
            if count >= max_files:
                break
            try:
                if not path.is_file() or path.suffix.lower() not in self.extractor.SUPPORTED_SUFFIXES:
                    continue
                if any(part in self.IGNORED_DIRS for part in path.parts):
                    continue
                count += 1
                yield path
            except OSError:
                continue

    def index(self, root: str | Path, *, max_files: int = 5000, max_file_mb: int = 25) -> dict:
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(root)
        indexed = skipped = errors = 0
        with self._lock:
            self._progress.update({"running": True, "root": str(root), "indexed": 0, "skipped": 0, "errors": 0, "finished_at": None})
        try:
            for path in self._candidate_files(root, max(1, min(int(max_files), 100_000))):
                try:
                    stat = path.stat()
                    if stat.st_size > max(1, int(max_file_mb)) * 1024 * 1024:
                        skipped += 1
                        continue
                    with engine.connect() as conn:
                        existing = conn.execute(text("SELECT modified_ns,size_bytes FROM star_file_semantic_index WHERE path=:p"), {"p": str(path)}).mappings().first()
                    if existing and int(existing["modified_ns"]) == stat.st_mtime_ns and int(existing["size_bytes"]) == stat.st_size:
                        skipped += 1
                        continue
                    extracted = self.extractor.extract(path, ocr_if_needed=False)
                    sample = extracted.text[:80_000].strip()
                    if not sample:
                        skipped += 1
                        continue
                    vector = self.vectorizer.vectorize(path.name + "\n" + sample)
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO star_file_semantic_index(path,title,suffix,size_bytes,modified_ns,sample_text,vector_json,vector_backend,indexed_at)
                            VALUES (:path,:title,:suffix,:size,:mtime,:sample,:vector,:backend,:now)
                            ON CONFLICT(path) DO UPDATE SET title=excluded.title,suffix=excluded.suffix,size_bytes=excluded.size_bytes,
                              modified_ns=excluded.modified_ns,sample_text=excluded.sample_text,vector_json=excluded.vector_json,
                              vector_backend=excluded.vector_backend,indexed_at=excluded.indexed_at
                        """), {"path": str(path), "title": path.name, "suffix": path.suffix.lower(), "size": stat.st_size,
                               "mtime": stat.st_mtime_ns, "sample": sample, "vector": json.dumps(vector),
                               "backend": self.vectorizer.backend, "now": _now()})
                    indexed += 1
                except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, json.JSONDecodeError):
                    errors += 1
                with self._lock:
                    self._progress.update({"indexed": indexed, "skipped": skipped, "errors": errors})
        finally:
            with self._lock:
                self._progress.update({"running": False, "indexed": indexed, "skipped": skipped, "errors": errors, "finished_at": _now()})
        return self.status()

    def start_index(self, root: str | Path, *, max_files: int = 5000, max_file_mb: int = 25) -> dict:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return self.status()
            self._thread = threading.Thread(
                target=self.index,
                kwargs={"root": root, "max_files": max_files, "max_file_mb": max_file_mb},
                name="star-file-semantic-index", daemon=True,
            )
            self._thread.start()
        return self.status()

    def search(self, query: str, *, limit: int = 10, scan_limit: int = 10000) -> list[dict]:
        query = _clean(query)
        if not query:
            return []
        qv = self.vectorizer.vectorize(query)
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT path,title,suffix,size_bytes,sample_text,vector_json,vector_backend,indexed_at
                FROM star_file_semantic_index ORDER BY indexed_at DESC LIMIT :limit
            """), {"limit": max(1, min(int(scan_limit), 50000))}).mappings().all()
        scored = []
        for row in rows:
            try:
                vector = json.loads(row["vector_json"])
            except json.JSONDecodeError:
                continue
            score = self.vectorizer.similarity(qv, vector) if row["vector_backend"] == self.vectorizer.backend else 0.0
            if score <= 0:
                continue
            scored.append({
                "path": row["path"], "title": row["title"], "suffix": row["suffix"],
                "size_bytes": int(row["size_bytes"]), "score": score,
                "snippet": _clean(row["sample_text"])[:300], "backend": row["vector_backend"],
            })
        scored.sort(key=lambda x: (-x["score"], x["path"]))
        return scored[:max(1, min(int(limit), 50))]

    def status(self) -> dict:
        with engine.connect() as conn:
            total = int(conn.execute(text("SELECT COUNT(*) FROM star_file_semantic_index")).scalar_one())
        with self._lock:
            progress = dict(self._progress)
        return {"indexed_files": total, "vector_backend": self.vectorizer.backend, "database": "star.db", **progress}


class SafeKnowledgeUpdater:
    """Atualiza evidência local com web verificada sem sobrescrever conhecimento canônico."""

    def __init__(self, growth, *, web: GeneralWebSearch | None = None):
        self.growth = growth
        self.web = web or GeneralWebSearch()

    def refresh(self, theme: str, query: str, *, network_enabled: bool = False, limit: int = 8) -> dict:
        if theme not in THEME_ORDER:
            raise KeyError(theme)
        result = self.web.search(query, limit=limit, network_enabled=network_enabled, verify=True)
        if not result.get("ok"):
            return {"ok": False, "reason": result.get("reason"), "accepted": 0, "verification": result.get("verification", {})}
        verified = [x for x in result["results"] if x.get("provenance_verified") and len(_clean(x.get("snippet"))) >= 20]
        domains = {x.get("source_domain") for x in verified if x.get("source_domain")}
        if len(verified) < 2 or len(domains) < 2:
            return {
                "ok": False, "reason": "insufficient_independent_verified_sources", "accepted": 0,
                "verification": result["verification"], "candidates": len(verified),
            }
        records = []
        for item in verified:
            records.append({
                "content": f"Evidência web: {_clean(item.get('title'))}. {_clean(item.get('snippet'))}",
                "source": item["url"],
                "source_type": "web_research_evidence",
                "retrieved_at": item["retrieved_at"],
                "confidence": 0.65,
                "metadata": {
                    "query": query, "source_domain": item.get("source_domain"),
                    "retrieval_status": item.get("retrieval_status"),
                    "canonical_fact": False, "automatic_promotion": False,
                    "provenance_verified": True,
                },
            })
        ingest = self.growth.ingest(theme, records, target_count=1)
        return {
            "ok": True, "theme": theme, "query": query,
            "accepted": ingest["accepted"], "duplicates": ingest["duplicates"], "rejected": ingest["rejected"],
            "verification": result["verification"], "canonical_promotion": False,
            "note": "conteúdo foi armazenado como evidência pesquisável com proveniência, não como verdade canônica",
        }


class OfflineDictionaryMaterializer:
    """Materializa dumps completos locais usando o builder já existente."""

    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.store = OfflineDictionaryStore(self.db_path)

    def materialize(self, entries: list[dict]) -> dict:
        from scripts.build_offline_dictionaries import connect, import_kaikki, import_normalized
        if not entries:
            raise ValueError("nenhum dump informado")
        db = connect(self.db_path)
        total = 0
        sources = []
        try:
            for entry in entries:
                path = Path(entry["path"]).expanduser().resolve()
                if not path.is_file():
                    raise FileNotFoundError(path)
                fmt = str(entry.get("format") or "jsonl").lower()
                if fmt == "kaikki":
                    locale = str(entry.get("source_locale") or "")
                    if not locale:
                        raise ValueError("source_locale é obrigatório para Kaikki")
                    added = import_kaikki(db, path, locale)
                elif fmt in {"jsonl", "tsv"}:
                    added = import_normalized(db, path, fmt)
                else:
                    raise ValueError(f"formato de materialização inválido: {fmt}")
                total += added
                sources.append({"path": str(path), "format": fmt, "rows": added})
            db.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('schema','1')")
            db.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('materialized_at',?)", (_now(),))
            db.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('materialized_sources',?)", (json.dumps(sources, ensure_ascii=False),))
            db.commit()
        finally:
            db.close()
        return {"database": str(self.db_path), "rows_processed": total, "sources": sources, "ready": self.store.full_index_ready}

    def status(self) -> dict:
        rows = 0
        metadata = {}
        if self.store.full_index_ready:
            import sqlite3
            try:
                with sqlite3.connect(self.db_path) as db:
                    rows = int(db.execute("SELECT COUNT(*) FROM translations").fetchone()[0])
                    metadata = {str(k): str(v) for k, v in db.execute("SELECT key,value FROM metadata").fetchall()}
            except (sqlite3.Error, OSError):
                metadata = {}
        return {
            "ready": self.store.full_index_ready,
            "database": str(self.db_path),
            "translation_rows": rows,
            "metadata": metadata,
            "source_families": self.store.source_stats(),
            "bundled_large_dumps": False,
        }


class IntelligentProactiveScheduler(ProactiveScheduler):
    """Refina o scheduler existente com relevância, urgência e antirrepetição."""

    KIND_BONUS = {
        "reminder_due": 0.35,
        "safety": 0.45,
        "security": 0.45,
        "health_signal": 0.30,
        "knowledge_update": 0.15,
        "research_update": 0.12,
        "ambient": -0.15,
    }

    def __init__(self, agenda, *, poll_seconds: float = 1.0, max_queue: int = 128, relevance_threshold: float = 0.55, duplicate_seconds: float = 300.0):
        super().__init__(agenda, poll_seconds=poll_seconds, max_queue=max_queue)
        self.relevance_threshold = max(0.0, min(float(relevance_threshold), 1.0))
        self.duplicate_seconds = max(0.0, min(float(duplicate_seconds), 86400.0))
        self._recent_notifications: dict[str, float] = {}

    def relevance(self, kind: str, content: str, *, payload=None, importance: float = 0.5) -> dict:
        payload = dict(payload or {})
        importance = max(0.0, min(float(importance), 1.0))
        score = importance * 0.65 + self.KIND_BONUS.get(str(kind), 0.0)
        reasons = [f"importance={importance:.2f}"]
        urgency = payload.get("urgency")
        if urgency is not None:
            try:
                urgency_value = max(0.0, min(float(urgency), 1.0))
                score += urgency_value * 0.20
                reasons.append(f"urgency={urgency_value:.2f}")
            except (TypeError, ValueError):
                pass
        relevance = payload.get("relevance")
        if relevance is not None:
            try:
                relevance_value = max(0.0, min(float(relevance), 1.0))
                score += relevance_value * 0.15
                reasons.append(f"context={relevance_value:.2f}")
            except (TypeError, ValueError):
                pass
        if payload.get("user_requested"):
            score += 0.25
            reasons.append("user_requested")
        fingerprint = hashlib.sha256(f"{kind}\n{_clean(content).casefold()}".encode("utf-8")).hexdigest()
        previous = self._recent_notifications.get(fingerprint)
        duplicate = previous is not None and time.monotonic() - previous < self.duplicate_seconds
        if duplicate:
            score -= 0.60
            reasons.append("recent_duplicate")
        score = max(0.0, min(score, 1.0))
        return {"score": score, "threshold": self.relevance_threshold, "relevant": score >= self.relevance_threshold, "duplicate": duplicate, "fingerprint": fingerprint, "reasons": reasons}

    def emit(self, kind: str, content: str, *, payload=None, importance: float = 0.5, notify: bool = True) -> dict:
        payload = dict(payload or {})
        assessment = self.relevance(kind, content, payload=payload, importance=importance)
        should_notify = bool(notify) and assessment["relevant"]
        payload["notification_relevance"] = {k: v for k, v in assessment.items() if k != "fingerprint"}
        event = super().emit(kind, content, payload=payload, importance=importance, notify=should_notify)
        if should_notify:
            self._recent_notifications[assessment["fingerprint"]] = time.monotonic()
            if len(self._recent_notifications) > 512:
                cutoff = time.monotonic() - self.duplicate_seconds
                self._recent_notifications = {k: v for k, v in self._recent_notifications.items() if v >= cutoff}
        return event

    def stats(self) -> dict:
        data = super().stats()
        data.update({
            "intelligent_relevance": True,
            "relevance_threshold": self.relevance_threshold,
            "duplicate_seconds": self.duplicate_seconds,
            "recent_notification_fingerprints": len(self._recent_notifications),
        })
        return data


class Group3KnowledgeServices:
    """Ponto de integração fino do Grupo 3 sobre MIND/RAG/growth já existentes."""

    def __init__(self, store, growth, *, network_enabled_provider=None):
        self.extractor = DocumentExtractor()
        self.rag = EnhancedDocumentRAG(store, extractor=self.extractor)
        self.web = GeneralWebSearch()
        self.updater = SafeKnowledgeUpdater(growth, web=self.web)
        self.files = SemanticFileSearch(extractor=self.extractor)
        self.dictionaries = OfflineDictionaryMaterializer()
        self.network_enabled_provider = network_enabled_provider or (lambda: False)

    def _network_enabled(self) -> bool:
        try:
            return bool(self.network_enabled_provider())
        except (TypeError, ValueError, RuntimeError):
            return False

    def handle(self, text_value: str) -> str | None:
        raw = _clean(text_value)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status grupo 3", "status conhecimento pesquisa documentos", "status de pesquisa e documentos"}:
            status = self.stats()
            file_status = status["semantic_files"]
            dictionary = status["dictionaries"]
            return (
                "⭐ Grupo 3 ativo: web com proveniência; RAG TXT/MD/CSV/JSON/PY/PDF/DOCX/XLSX/PPTX; "
                f"OCR={'ATIVO' if status['documents']['ocr']['available'] else 'AGUARDANDO TESSERACT'}; "
                f"índice semântico={file_status['indexed_files']} arquivos ({file_status['vector_backend']}); "
                f"dicionário completo={'MATERIALIZADO' if dictionary['ready'] else 'AGUARDANDO DUMPS LOCAIS'}; "
                "atualização automática=EVIDÊNCIA APPEND-ONLY, sem promoção canônica automática."
            )
        if low in {"status dicionario offline", "status dicionário offline", "status dos dicionarios offline", "status dos dicionários offline"}:
            item = self.dictionaries.status()
            return f"📖 Dicionários offline: {'prontos' if item['ready'] else 'não materializados'} | relações={item['translation_rows']} | banco={item['database']}"
        match = re.match(r"^(?:star[, ]+)?(?:indexe|indexar|adicione ao rag|adicionar ao rag) (?:o )?(?:documento|arquivo)\s+(.+)$", raw, re.I)
        if match:
            result = self.rag.ingest_file(match.group(1).strip())
            return f"📚 Documento indexado no RAG existente: id={result['document_id']} | formato={result['format']} | chunks={result['chunks']} | OCR={'sim' if result['ocr_used'] else 'não'}."
        match = re.match(r"^(?:star[, ]+)?(?:ocr|leia com ocr|extrair texto de)\s+(.+)$", raw, re.I)
        if match:
            item = self.extractor.extract(match.group(1).strip(), ocr_if_needed=True)
            preview = _clean(item.text)[:1600]
            return f"🔎 OCR/extração local ({item.extraction}, {item.format}): {preview or 'nenhum texto reconhecido'}"
        match = re.match(r"^(?:star[, ]+)?(?:indexe arquivos em|indexar arquivos em|crie indice de arquivos em|crie índice de arquivos em)\s+(.+)$", raw, re.I)
        if match:
            status = self.files.start_index(match.group(1).strip())
            return f"🗂️ Indexação semântica iniciada sem bloquear a interface: raiz={status.get('root') or match.group(1).strip()} | backend={status['vector_backend']}."
        if low in {"status da indexacao de arquivos", "status da indexação de arquivos", "status indice de arquivos", "status índice de arquivos"}:
            status = self.files.status()
            return f"🗂️ Índice de arquivos: {status['indexed_files']} persistidos | execução={'ATIVA' if status['running'] else 'PARADA'} | novos={status['indexed']} | ignorados={status['skipped']} | erros={status['errors']} | backend={status['vector_backend']}."
        match = re.match(r"^(?:star[, ]+)?(?:busque semanticamente nos arquivos|busque nos arquivos|pesquise nos arquivos)\s+(.+)$", raw, re.I)
        if match:
            hits = self.files.search(match.group(1), limit=8)
            if not hits:
                return "🗂️ Não encontrei arquivos no índice semântico. Indexe primeiro uma pasta com 'indexe arquivos em <pasta>'."
            return "🗂️ Arquivos semanticamente relacionados:\n" + "\n".join(f"- {x['title']} ({x['score']:.3f}) — {x['path']}" for x in hits)
        match = re.match(r"^(?:star[, ]+)?(?:pesquise na web|pesquisar na web|pesquise na internet|pesquisar na internet)\s+(.+)$", raw, re.I)
        if match:
            result = self.web.search(match.group(1), limit=8, network_enabled=self._network_enabled(), verify=True)
            if not result["ok"]:
                if result.get("reason") == "network_disabled":
                    return "A pesquisa web geral está pronta, mas o modo ONLINE está desativado."
                return "Não consegui obter resultados web verificáveis agora."
            lines = []
            for item in result["results"][:8]:
                marker = "✓" if item.get("provenance_verified") else "?"
                lines.append(f"- [{marker}] {item['title']} — {item['url']}")
            verification = result["verification"]
            return "🌐 Pesquisa web com proveniência:\n" + "\n".join(lines) + f"\nVerificação: {verification['status']} | domínios={verification['independent_domains']} | verdade automática=NÃO."
        themes = "|".join(re.escape(x) for x in THEME_ORDER)
        match = re.match(rf"^(?:star[, ]+)?(?:atualize conhecimento|atualizar conhecimento)\s+({themes})\s+sobre\s+(.+)$", raw, re.I)
        if match:
            theme = match.group(1).casefold()
            result = self.updater.refresh(theme, match.group(2), network_enabled=self._network_enabled())
            if not result["ok"]:
                if result.get("reason") == "network_disabled":
                    return "A atualização segura está pronta, mas o modo ONLINE está desativado."
                return "Não atualizei o conhecimento: faltaram pelo menos duas fontes independentes com proveniência recuperável."
            return f"🧠 Conhecimento atualizado com {result['accepted']} evidências novas e {result['duplicates']} duplicadas. Promoção automática a fato canônico: NÃO."
        return None

    def stats(self) -> dict:
        return {
            "web_general": {"network_opt_in": True, "provenance_verification": True},
            "documents": self.extractor.stats(),
            "semantic_files": self.files.status(),
            "dictionaries": self.dictionaries.status(),
            "automatic_knowledge_update": {"append_only": True, "canonical_promotion": False, "multi_source_required": True},
        }
