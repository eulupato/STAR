import gzip
import json
import uuid

from core.knowledge_research_documents import RealKnowledgeMaterializer


def _namespace(prefix="test"):
    return f"{prefix}_{uuid.uuid4().hex}"


def test_real_knowledge_counts_only_physical_unique_records(tmp_path):
    path = tmp_path / "facts.jsonl"
    rows = [
        {"subject": "Brasil", "relation": "capital", "object": "Brasília"},
        {"subject": "Argentina", "relation": "capital", "object": "Buenos Aires"},
        {"subject": "Japão", "relation": "capital", "object": "Tóquio"},
    ]
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")

    namespace = _namespace("geography")
    materializer = RealKnowledgeMaterializer()
    first = materializer.register_source(
        namespace,
        path,
        source_format="jsonl",
        source_type="test-fixture",
        license_name="test-only",
    )
    assert first["registered"] is True
    assert first["record_count"] == 3
    status = materializer.status(namespace)
    assert status["materialized_real_count"] == 3
    assert status["target_count"] == 1_000_000_000
    assert status["billion_claim_allowed"] is False
    assert status["status"] == "partial"

    duplicate = materializer.register_source(
        namespace,
        path,
        source_format="jsonl",
        source_type="test-fixture",
        license_name="test-only",
    )
    assert duplicate["registered"] is False
    assert duplicate["duplicate_source"] is True
    assert materializer.status(namespace)["materialized_real_count"] == 3


def test_real_knowledge_streams_compressed_ntriples(tmp_path):
    path = tmp_path / "wikidata.nt.gz"
    with gzip.open(path, "wt", encoding="utf-8") as stream:
        stream.write("<http://www.wikidata.org/entity/Q155> <http://www.wikidata.org/prop/direct/P36> <http://www.wikidata.org/entity/Q2844> .\n")
        stream.write("<http://www.wikidata.org/entity/Q414> <http://www.wikidata.org/prop/direct/P36> <http://www.wikidata.org/entity/Q1486> .\n")
        stream.write("\n")

    namespace = _namespace("wikidata")
    materializer = RealKnowledgeMaterializer()
    result = materializer.register_source(
        namespace,
        path,
        source_format="ntriples",
        source_type="wikidata-rdf-dump",
        license_name="CC0",
        metadata={"provenance": "Wikidata"},
    )
    assert result["record_count"] == 2
    assert materializer.status(namespace)["materialized_real_count"] == 2


def test_real_knowledge_rejects_empty_or_invalid_sources(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("\nnot-json\n", encoding="utf-8")
    materializer = RealKnowledgeMaterializer()
    try:
        materializer.register_source(
            _namespace(),
            path,
            source_format="jsonl",
            source_type="test-fixture",
            license_name="test-only",
        )
    except ValueError as exc:
        assert "sem registros válidos" in str(exc)
    else:
        raise AssertionError("fonte inválida deveria ser rejeitada")
