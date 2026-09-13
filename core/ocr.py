"""OCR local sob demanda para o RAG da STAR."""
from __future__ import annotations

from pathlib import Path

from core.labs import DocumentRAG


class OCRUnavailable(RuntimeError):
    pass


class OCREngine:
    """Extrai PDF textual primeiro e usa PyMuPDF/Tesseract só quando necessário."""

    def __init__(self, rag: DocumentRAG | None = None):
        self.rag = rag or DocumentRAG()

    @staticmethod
    def _plain_pdf(path: Path) -> tuple[str, int, int]:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        page_texts = [(page.extract_text() or "") for page in reader.pages]
        populated = sum(1 for text_value in page_texts if len(text_value.strip()) >= 40)
        return "\n\n".join(page_texts), populated, len(page_texts)

    def extract_pdf(self, path: str | Path, *, languages: str = "por+eng", force_ocr: bool = False) -> dict:
        path = Path(path).expanduser().resolve()
        if not path.is_file() or path.suffix.lower() != ".pdf":
            raise ValueError("OCR espera um arquivo PDF existente")
        text_content, populated, pages = self._plain_pdf(path)
        if not force_ocr and pages and populated / pages >= 0.7:
            return {"text": text_content, "engine": "pypdf", "ocr_used": False, "pages": pages, "ocr_pages": 0}
        try:
            import pymupdf
        except ImportError as exc:
            raise OCRUnavailable("PDF parece escaneado; instale requirements-intelligence.txt e Tesseract para OCR") from exc
        doc = pymupdf.open(str(path))
        output, ocr_pages = [], 0
        for page in doc:
            direct = page.get_text("text") or ""
            if not force_ocr and len(direct.strip()) >= 40:
                output.append(direct)
                continue
            try:
                textpage = page.get_textpage_ocr(language=languages, dpi=200, full=True)
                output.append(page.get_text("text", textpage=textpage) or "")
                ocr_pages += 1
            except Exception as exc:
                raise OCRUnavailable(f"Tesseract/PyMuPDF OCR indisponível: {exc}") from exc
        return {"text": "\n\n".join(output), "engine": "pymupdf+tesseract", "ocr_used": True,
                "pages": len(doc), "ocr_pages": ocr_pages}

    def ingest_pdf(self, path: str | Path, *, languages: str = "por+eng", force_ocr: bool = False, metadata=None) -> dict:
        result = self.extract_pdf(path, languages=languages, force_ocr=force_ocr)
        path = Path(path).expanduser().resolve()
        meta = dict(metadata or {}); meta.update({"ocr_engine": result["engine"], "ocr_used": result["ocr_used"], "ocr_pages": result["ocr_pages"]})
        ingested = self.rag.ingest_text(result["text"], source=str(path), title=path.name, metadata=meta)
        return {**ingested, **{k: v for k, v in result.items() if k != "text"}}

    @staticmethod
    def stats() -> dict:
        try:
            import pymupdf  # noqa: F401
            pymupdf_available = True
        except ImportError:
            pymupdf_available = False
        return {"status": "optional-local", "pymupdf_available": pymupdf_available,
                "tesseract_external_required_for_ocr": True, "plain_pdf_fallback": "pypdf"}
