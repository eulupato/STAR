import json
from pathlib import Path
from uuid import uuid4
import zipfile

from core.knowledge_research_documents import (
    DocumentExtractor,
    Group3KnowledgeServices,
    IntelligentProactiveScheduler,
    OfflineDictionaryMaterializer,
    SafeKnowledgeUpdater,
    SemanticFileSearch,
)
from core.mind import CognitiveSuite
from core.offline_dictionary import OfflineDictionaryStore
from modules.automation import AgendaManager
from modules.internet import GeneralWebSearch, _safe_public_url


def _write_zip(path: Path, files: dict[str, str]):
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def test_document_extractor_supports_docx_xlsx_and_pptx_without_heavy_office_dependencies(tmp_path):
    docx = tmp_path / "sample.docx"
    _write_zip(docx, {
        "word/document.xml": '<w:document xmlns:w="urn:w"><w:body><w:p><w:r><w:t>STAR documento DOCX</w:t></w:r></w:p></w:body></w:document>'
    })
    xlsx = tmp_path / "sample.xlsx"
    _write_zip(xlsx, {
        "xl/sharedStrings.xml": '<sst xmlns="urn:x"><si><t>Planilha STAR</t></si></sst>',
        "xl/worksheets/sheet1.xml": '<worksheet xmlns="urn:x"><sheetData><row><c t="s"><v>0</v></c><c><v>42</v></c></row></sheetData></worksheet>',
    })
    pptx = tmp_path / "sample.pptx"
    _write_zip(pptx, {
        "ppt/slides/slide1.xml": '<p:sld xmlns:p="urn:p" xmlns:a="urn:a"><p:cSld><a:t>Slide STAR</a:t></p:cSld></p:sld>'
    })

    extractor = DocumentExtractor()
    assert "STAR documento DOCX" in extractor.extract(docx, ocr_if_needed=False).text
    xlsx_text = extractor.extract(xlsx, ocr_if_needed=False).text
    assert "Planilha STAR" in xlsx_text and "42" in xlsx_text
    assert "Slide STAR" in extractor.extract(pptx, ocr_if_needed=False).text
    stats = extractor.stats()
    assert {"docx", "xlsx", "pptx", "pdf"}.issubset(set(stats["formats"]))
    assert stats["office_open_xml_without_extra_dependency"] is True


def test_enhanced_rag_keeps_existing_store_and_retrieval(tmp_path):
    marker = uuid4().hex
    docx = tmp_path / f"{marker}.docx"
    _write_zip(docx, {
        "word/document.xml": f'<w:document xmlns:w="urn:w"><w:body><w:p><w:r><w:t>{marker} energia conservação documento Office</w:t></w:r></w:p></w:body></w:document>'
    })
    suite = CognitiveSuite()
    group3 = Group3KnowledgeServices(suite.store, suite.growth)
    suite.rag = group3.rag
    result = suite.rag.ingest_file(docx, ocr_if_needed=False)
    assert result["created"] is True
    assert result["format"] == "docx"
    hits = suite.rag.search(marker, top_k=3)
    assert hits and marker in hits[0].content


def test_semantic_file_index_is_persistent_local_and_does_not_scan_automatically(tmp_path):
    marker = uuid4().hex
    root = tmp_path / marker
    root.mkdir()
    target = root / "astronomia.txt"
    target.write_text("exoplaneta astronomia telescópio atmosfera planeta distante", encoding="utf-8")
    search = SemanticFileSearch()
    before = search.status()
    assert before["running"] is False
    indexed = search.index(root, max_files=20)
    assert indexed["indexed"] >= 1
    hits = search.search("exoplaneta telescópio", limit=5)
    assert hits
    assert hits[0]["path"] == str(target.resolve())
    assert hits[0]["backend"] in {"hashed-text-vector", "sentence-transformers-local"}


def test_web_search_is_opt_in_and_blocks_private_targets():
    result = GeneralWebSearch().search("STAR test", network_enabled=False)
    assert result["ok"] is False
    assert result["reason"] == "network_disabled"
    assert result["verification"]["truth_claim"] is False
    assert _safe_public_url("http://127.0.0.1:8000/private") is False
    assert _safe_public_url("http://localhost/private") is False
    assert _safe_public_url("file:///etc/passwd") is False


class _FakeWeb:
    def search(self, query, *, limit=8, network_enabled=False, verify=True):
        assert network_enabled is True
        return {
            "ok": True,
            "results": [
                {"title": "Fonte A", "snippet": "Evidência longa e independente para atualização segura do conhecimento.", "url": "https://a.example/item", "source_domain": "a.example", "retrieved_at": "2026-09-17T00:00:00+00:00", "provenance_verified": True, "retrieval_status": "retrievable"},
                {"title": "Fonte B", "snippet": "Segunda evidência longa e independente para verificação de proveniência.", "url": "https://b.example/item", "source_domain": "b.example", "retrieved_at": "2026-09-17T00:00:00+00:00", "provenance_verified": True, "retrieval_status": "retrievable"},
            ],
            "verification": {"status": "multi_source_provenance_verified", "independent_domains": 2},
        }


class _FakeGrowth:
    def __init__(self):
        self.records = None

    def ingest(self, theme, records, *, target_count=1, run_date=None):
        self.records = list(records)
        return {"theme": theme, "accepted": len(self.records), "duplicates": 0, "rejected": 0, "status": "complete"}


def test_safe_knowledge_update_requires_provenance_and_never_promotes_canonical_fact():
    growth = _FakeGrowth()
    updater = SafeKnowledgeUpdater(growth, web=_FakeWeb())
    result = updater.refresh("reasoning", "teste", network_enabled=True)
    assert result["ok"] is True
    assert result["accepted"] == 2
    assert result["canonical_promotion"] is False
    assert growth.records
    assert all(row["metadata"]["canonical_fact"] is False for row in growth.records)
    assert all(row["metadata"]["automatic_promotion"] is False for row in growth.records)


def test_offline_dictionary_materializer_reuses_existing_dictionary_database(tmp_path):
    source = tmp_path / "dictionary.jsonl"
    source.write_text(json.dumps({
        "term": "galaxy",
        "source_locale": "en-US",
        "target_locale": "pt-BR",
        "translation": "galáxia",
        "source": "unit-test",
        "priority": 50,
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    db = tmp_path / "dictionary.sqlite3"
    materializer = OfflineDictionaryMaterializer(db)
    result = materializer.materialize([{"path": str(source), "format": "jsonl"}])
    assert result["ready"] is True
    assert result["rows_processed"] == 1
    status = materializer.status()
    assert status["translation_rows"] == 1
    store = OfflineDictionaryStore(db)
    assert store.lookup("galaxy", "en-US", "pt-BR") == "galáxia"


def test_intelligent_notifications_score_relevance_and_suppress_recent_duplicates():
    scheduler = IntelligentProactiveScheduler(AgendaManager(), relevance_threshold=0.55, duplicate_seconds=300)
    low = scheduler.emit("ambient", "ruído rotineiro", importance=0.1, notify=True)
    assert low["notify"] is False
    important = scheduler.emit("reminder_due", "Lembrete importante", importance=0.8, payload={"user_requested": True}, notify=True)
    assert important["notify"] is True
    duplicate = scheduler.emit("reminder_due", "Lembrete importante", importance=0.8, payload={"user_requested": True}, notify=True)
    assert duplicate["notify"] is False
    assert duplicate["payload"]["notification_relevance"]["duplicate"] is True
    assert scheduler.stats()["intelligent_relevance"] is True
