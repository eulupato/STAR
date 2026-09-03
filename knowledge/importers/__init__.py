"""Importadores da STAR Knowledge V3."""
from .pdf import PdfDocumentReader, PdfPage
from .heroes import HeroEncyclopediaImporter

__all__ = ["HeroEncyclopediaImporter", "PdfDocumentReader", "PdfPage"]
