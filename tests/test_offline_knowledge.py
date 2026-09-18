import json

from core.executive import Executive
from core.knowledge_research_documents import RealKnowledgeMaterializer
from core.physics_knowledge_150k import PhysicsKnowledgeEngine
from core.offline_knowledge import BILLION, CATEGORY_SOURCES, OfflineKnowledgeService
from database.cognitive_store import CognitiveStore


def test_all_offline_categories_have_real_billion_target():
    materializer = RealKnowledgeMaterializer()
    result = materializer.ensure_namespaces(CATEGORY_SOURCES)
    assert result["target_per_namespace"] == BILLION
    assert len(CATEGORY_SOURCES) >= 30
    for category in CATEGORY_SOURCES:
        state = materializer.status(category)
        assert state["target_count"] == BILLION
        assert state["billion_claim_allowed"] is (state["materialized_real_count"] >= BILLION)


def test_offline_seed_answers_capital_of_brazil():
    store = CognitiveStore()
    service = OfflineKnowledgeService(store, real_materializer=RealKnowledgeMaterializer())
    answer = service.answer("Qual a capital do Brasil?")
    assert answer is not None
    assert "Brasília" in answer


def test_anaphoric_ordinal_followup_does_not_trigger_fact_retrieval():
    store = CognitiveStore()
    service = OfflineKnowledgeService(store, real_materializer=RealKnowledgeMaterializer())
    assert service.search("E o segundo?") == []


def test_offline_fact_search_prefers_full_query_overlap():
    store = CognitiveStore()
    store.ingest_facts("geography", [{
        "content": "A capital de Testelândia é Cidade Teste.",
        "source": "test://geography",
        "source_type": "test",
        "confidence": 0.99,
    }], target_count=BILLION)
    rows = store.search_facts("qual a capital de Testelândia", limit=5)
    assert rows
    assert "Cidade Teste" in rows[0]["content"]
    assert rows[0]["query_overlap"] >= 0.5


class _NoAnswer:
    def answer(self, text):
        return None


class _Offline:
    def answer(self, text):
        if "capital" in text.casefold():
            return "A capital de Testelândia é Cidade Teste."
        return None


class _WrongPhysics:
    def answer(self, text):
        return "RESPOSTA ERRADA DO MATCHER DE FÍSICA"


def test_executive_uses_offline_knowledge_before_legacy_matchers():
    executive = Executive(
        internal_knowledge=_NoAnswer(),
        physics_knowledge=_WrongPhysics(),
        offline_knowledge=_Offline(),
    )
    answer = executive.execute({"input": "Qual a capital de Testelândia?"}, {"mode": "FAST"})
    assert "Cidade Teste" in answer
    assert "RESPOSTA ERRADA" not in answer


def test_physics_does_not_hijack_ambiguous_quanto_e_uma_acao():
    physics = PhysicsKnowledgeEngine()
    assert physics.match("Quanto é uma ação?") is None
    assert physics.match("Quanto é a velocidade da luz?") is not None


def test_seed_file_has_one_sourced_fact_for_every_category():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    rows = [
        json.loads(line)
        for line in (root / "knowledge" / "offline_core_facts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    covered = {row["theme"] for row in rows}
    assert set(CATEGORY_SOURCES) == covered
    assert all(row.get("source") and row.get("source_type") for row in rows)
    assert all(float(row.get("confidence", 0)) >= 0.8 for row in rows)
