"""Leitura de PDF com fallback OCR local e cache de páginas."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile

from core.logging_config import get_logger

log = get_logger("knowledge.pdf")


@dataclass(frozen=True)
class PdfPage:
    number: int
    text: str
    image_path: str | None = None
    used_ocr: bool = False


class PdfDocumentReader:
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _fitz():
        try:
            import fitz
            return fitz
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF não está instalado. Execute pip install PyMuPDF."
            ) from exc

    def page_count(self, pdf_path: str | Path) -> int:
        fitz = self._fitz()
        with fitz.open(str(pdf_path)) as doc:
            return len(doc)

    def _render_page(self, page, output: Path, dpi: int = 144) -> str:
        if output.exists() and output.stat().st_size > 0:
            return str(output)
        matrix = self._fitz().Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pix.save(str(output))
        return str(output)

    @staticmethod
    def _ocr_image(image_path: Path) -> str:
        executable = shutil.which("tesseract")
        if not executable:
            raise RuntimeError(
                "Tesseract não foi encontrado. Instale-o ou importe sem OCR."
            )
        result = subprocess.run(
            [executable, str(image_path), "stdout", "-l", "eng", "--psm", "6"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Falha no Tesseract.")
        return result.stdout.strip()

    def iter_pages(
        self,
        pdf_path: str | Path,
        *,
        start_page: int = 1,
        end_page: int | None = None,
        allow_ocr: bool = False,
        render_images: bool = True,
        min_text_chars: int = 80,
    ):
        fitz = self._fitz()
        source = Path(pdf_path)
        if not source.exists():
            raise FileNotFoundError(source)

        cache_root = self.cache_dir / source.stem
        cache_root.mkdir(parents=True, exist_ok=True)

        with fitz.open(str(source)) as doc:
            last = len(doc) if end_page is None else min(len(doc), int(end_page))
            first = max(1, int(start_page))
            for index in range(first - 1, last):
                page = doc.load_page(index)
                text = (page.get_text("text") or "").strip()
                image_path = None
                used_ocr = False

                needs_image = render_images or (
                    allow_ocr and len(text) < int(min_text_chars)
                )
                if needs_image:
                    image_file = cache_root / f"page_{index + 1:04d}.png"
                    image_path = self._render_page(page, image_file)

                if allow_ocr and len(text) < int(min_text_chars):
                    try:
                        text = self._ocr_image(Path(image_path))
                        used_ocr = bool(text)
                    except RuntimeError as exc:
                        log.warning(
                            "OCR indisponível na página %s de %s: %s",
                            index + 1,
                            source.name,
                            exc,
                        )

                yield PdfPage(
                    number=index + 1,
                    text=text,
                    image_path=image_path,
                    used_ocr=used_ocr,
                )
