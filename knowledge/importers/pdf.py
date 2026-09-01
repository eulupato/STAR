"""Leitura de PDF com OCR opcional, cache e candidatos de imagem."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil
import subprocess

from core.logging_config import get_logger

log = get_logger("knowledge.pdf")


@dataclass(frozen=True)
class PdfPage:
    number: int
    text: str
    image_path: str | None = None
    portrait_path: str | None = None
    image_candidates: tuple[str, ...] = field(default_factory=tuple)
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

    def _extract_image_candidates(self, doc, page, cache_root: Path, page_number: int):
        """Extrai imagens embutidas que parecem retratos/arte, não scans da página."""
        page_area = max(float(page.rect.width * page.rect.height), 1.0)
        candidates = []

        try:
            infos = page.get_image_info(xrefs=True)
        except Exception as exc:
            log.debug("Não foi possível inspecionar imagens da pág. %s: %s", page_number, exc)
            return []

        seen_xrefs = set()
        for info in infos:
            xref = int(info.get("xref") or 0)
            if xref <= 0 or xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            bbox = info.get("bbox")
            width = int(info.get("width") or 0)
            height = int(info.get("height") or 0)
            if not bbox or width < 160 or height < 160:
                continue

            try:
                area = max(float((bbox[2] - bbox[0]) * (bbox[3] - bbox[1])), 0.0)
            except Exception:
                area = 0.0
            ratio = area / page_area

            # >82% normalmente é a página escaneada inteira, não um retrato.
            if ratio >= 0.82 or ratio < 0.025:
                continue

            extracted = doc.extract_image(xref)
            data = extracted.get("image")
            ext = str(extracted.get("ext") or "png").lower()
            if not data:
                continue
            if ext not in {"png", "jpg", "jpeg", "webp"}:
                ext = "png"

            output = cache_root / f"page_{page_number:04d}_xref_{xref}.{ext}"
            if not output.exists():
                output.write_bytes(data)

            aspect = width / max(height, 1)
            portrait_bonus = 0.25 if 0.35 <= aspect <= 1.15 else 0.0
            score = min(ratio, 0.65) + portrait_bonus
            candidates.append((score, str(output)))

        candidates.sort(key=lambda item: item[0], reverse=True)
        return [path for _score, path in candidates]

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
                page_number = index + 1
                page = doc.load_page(index)
                text = (page.get_text("text") or "").strip()
                image_path = None
                used_ocr = False
                image_candidates = []

                if render_images:
                    image_candidates = self._extract_image_candidates(
                        doc, page, cache_root, page_number
                    )

                needs_page_render = allow_ocr and len(text) < int(min_text_chars)
                if needs_page_render:
                    image_file = cache_root / f"page_{page_number:04d}.png"
                    image_path = self._render_page(page, image_file)

                if allow_ocr and len(text) < int(min_text_chars):
                    try:
                        text = self._ocr_image(Path(image_path))
                        used_ocr = bool(text)
                    except RuntimeError as exc:
                        log.warning(
                            "OCR indisponível na página %s de %s: %s",
                            page_number,
                            source.name,
                            exc,
                        )

                yield PdfPage(
                    number=page_number,
                    text=text,
                    image_path=image_path,
                    portrait_path=image_candidates[0] if image_candidates else None,
                    image_candidates=tuple(image_candidates),
                    used_ocr=used_ocr,
                )
