import pytest

fitz = pytest.importorskip("fitz")
PIL = pytest.importorskip("PIL")
from PIL import Image

from knowledge.importers.pdf import PdfDocumentReader


def test_pdf_reader_rejects_full_page_scan_as_portrait(tmp_path):
    page_img = tmp_path / "page.png"
    Image.new("RGB", (1200, 1600), "white").save(page_img)

    pdf = tmp_path / "scan.pdf"
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_image(page.rect, filename=str(page_img))
    doc.save(pdf)
    doc.close()

    reader = PdfDocumentReader(tmp_path / "cache")
    result = next(reader.iter_pages(pdf, render_images=True, allow_ocr=False))
    assert result.portrait_path is None


def test_pdf_reader_prefers_embedded_character_art(tmp_path):
    scan = tmp_path / "scan.png"
    portrait = tmp_path / "portrait.png"
    Image.new("RGB", (1200, 1600), "white").save(scan)
    Image.new("RGB", (400, 700), "gray").save(portrait)

    pdf = tmp_path / "mixed.pdf"
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_image(page.rect, filename=str(scan))
    page.insert_image(fitz.Rect(50, 80, 300, 520), filename=str(portrait))
    doc.save(pdf)
    doc.close()

    reader = PdfDocumentReader(tmp_path / "cache")
    result = next(reader.iter_pages(pdf, render_images=True, allow_ocr=False))
    assert result.portrait_path is not None
    assert Path(result.portrait_path).exists()
