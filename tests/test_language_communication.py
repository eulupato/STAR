from uuid import uuid4
import unicodedata

import pytest

from core.language_communication import (
    ADDRESSABLE_CONTENTS,
    CANONICAL_NODES,
    COMMUNICATION_BRANCHES,
    COMMUNICATION_DOMAINS,
    COMMUNICATION_LENSES,
    INTERPRETATION_POLICY,
    LANGUAGE_VARIANTS,
    REQUESTED_LANGUAGES,
    REQUESTED_TOPICS,
    VARIANT_AXES,
    VARIANTS_PER_NODE,
    CommunicationCatalog,
    LanguageCommunicationFoundations,
)
from core.language_manager import LanguageManager
from core.mind import CognitiveSuite
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _norm(text):
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return " ".join(value.replace("_", " ").split())


def _language_block(*, manager=None):
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    block = LanguageCommunicationFoundations(knowledge, language_manager=manager)
    return block, knowledge, suite


def _canonical_fact(suite: CognitiveSuite, marker: str):
    source_id = suite.epistemics.register_source(
        f"unit://language/{marker}",
        source_type="test",
        title=f"Fonte linguística {marker}",
        reliability=1.0,
        reliability_basis="unit test",
    )
    record = suite.epistemics.discover(
        f"Conhecimento linguístico geral validado {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://language-claim/{marker}",
        source_id=source_id,
        confidence=0.5,
    )
    suite.epistemics.add_evidence(
        record["record_id"],
        f"Evidência linguística rastreável {marker}",
        evidence_type="primary_source",
        stance="support",
        source_id=source_id,
        strength=1.0,
        reliability=1.0,
    )
    suite.epistemics.transition(record["record_id"], "VERIFIED", reason="evidência rastreável", actor="unit-test")
    return suite.epistemics.transition(record["record_id"], "CANONICAL", reason="claim geral apto ao B08", actor="unit-test")


def test_block8_catalog_is_exactly_1b_and_on_demand():
    catalog = CommunicationCatalog()
    stats = catalog.stats()
    assert len(COMMUNICATION_DOMAINS) == 13
    assert len(COMMUNICATION_BRANCHES) == 50
    assert len(COMMUNICATION_LENSES) == 20
    assert CANONICAL_NODES == 1_000
    assert VARIANTS_PER_NODE == 1_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["prepopulated_knowledge_rows"] == 0
    assert catalog.content_id(0, 0) == "LANG-B08-0000000001"
    assert catalog.content_id(999, 999_999) == "LANG-B08-1000000000"
    assert catalog.get_variant("LANG-B08-1000000001") is None


def test_block8_variant_space_contains_all_nine_requested_dimensions():
    sizes = {name: len(values) for name, values in VARIANT_AXES}
    assert list(sizes) == [
        "language", "dialect", "context", "intention", "register", "culture", "meaning", "structure", "situation"
    ]
    product = 1
    for size in sizes.values():
        product *= size
    assert product == 1_000_000
    item = CommunicationCatalog().get_variant("LANG-B08-1000000000")
    for dimension in sizes:
        assert dimension in item


def test_block8_contains_requested_languages_topics_and_future_extension():
    corpus = _norm(" ".join(
        [branch.label for branch in COMMUNICATION_BRANCHES]
        + [topic for branch in COMMUNICATION_BRANCHES for topic in branch.subtopics]
        + list(REQUESTED_LANGUAGES)
        + list(REQUESTED_TOPICS)
    ))
    for language in REQUESTED_LANGUAGES:
        assert _norm(language) in corpus, language
    for topic in REQUESTED_TOPICS:
        assert _norm(topic) in corpus, topic
    assert "future_language_extension" in LANGUAGE_VARIANTS
    assert "multilingual_comparative" in LANGUAGE_VARIANTS


def test_block8_separates_knowledge_languages_from_operational_runtime():
    block, _knowledge, _suite = _language_block()
    support = {item["key"]: item for item in block.runtime_language_support()["knowledge_languages"]}
    for key in ("portuguese", "english", "spanish", "french", "italian"):
        assert support[key]["knowledge_supported"] is True
        assert support[key]["operational_runtime"] is True
    for key in ("german", "mandarin_chinese", "japanese"):
        assert support[key]["knowledge_supported"] is True
        assert support[key]["operational_runtime"] is False
        assert support[key]["planned_or_extensible"] is True


def test_block8_registers_b08_on_same_universal_architecture():
    block, knowledge, _suite = _language_block()
    namespace = knowledge.store.get_namespace("B08")
    assert namespace is not None
    assert namespace["logical_capacity"] == 1_000_000_000
    assert block.knowledge is knowledge
    assert block.graph is knowledge.graph
    assert block.stats()["knowledge_graph"] == "shared knowledge_nodes/knowledge_edges"


def test_block8_taxonomy_uses_shared_graph_and_links_psychology():
    block, _knowledge, suite = _language_block()
    result = block.materialize_taxonomy("voz")
    assert result["knowledge_graph"] == "shared"
    assert result["parallel_language_graph_created"] is False
    assert result["branches_materialized"] == 3
    root_neighbors = suite.graph.neighbors("LANG-TAX-ROOT")
    labels = {item["label"] for item in root_neighbors}
    assert "Mente Humana e Psicologia" in labels
    assert "Voz, prosódia e silêncio" in labels
    branch_neighbors = suite.graph.neighbors("LANG-BR-VOICE_PROSODY", relation="has_part")
    assert any(item["node_type"] == "communication_subtopic" for item in branch_neighbors)


def test_block8_interpretation_keeps_irony_voice_gesture_and_silence_uncertain():
    block, _knowledge, _suite = _language_block()
    result = block.interpret_communication(
        "Nossa, genial.",
        context="conversa após um erro",
        language="português",
        register="informal",
        signals=["entonação descendente", "pausa", "olhar"],
    )
    assert result["epistemic_kind"] == "inference"
    assert result["certainty"] == "underdetermined"
    assert result["intention"] is None
    assert result["intention_certainty"] is False
    assert result["single_signal_proves_meaning"] is False
    assert result["alternative_interpretations_required"] is True
    joined = " ".join(result["possible_interpretations"])
    assert "ironia" in joined
    assert "comunicação indireta" in joined
    assert "não provar intenção" in joined


def test_block8_policy_rejects_single_signal_mind_reading():
    assert INTERPRETATION_POLICY["surface_form_is_single_meaning"] is False
    assert INTERPRETATION_POLICY["expression_is_certain_intention"] is False
    assert INTERPRETATION_POLICY["gesture_is_certain_intention"] is False
    assert INTERPRETATION_POLICY["prosody_is_certain_intention"] is False
    assert INTERPRETATION_POLICY["silence_is_certain_intention"] is False
    assert INTERPRETATION_POLICY["irony_sarcasm_requires_context"] is True
    assert INTERPRETATION_POLICY["automatic_mind_reading"] is False


def test_block8_canonical_knowledge_keeps_block2_gate():
    block, knowledge, suite = _language_block()
    marker = uuid4().hex
    source_id = suite.epistemics.register_source(
        f"unit://lang-discovered/{marker}", source_type="test", reliability=1.0
    )
    discovered = suite.epistemics.discover(
        f"Claim linguístico descoberto {marker}",
        epistemic_kind="fact",
        origin_type="unit_test",
        origin_ref=f"unit://lang-discovered-claim/{marker}",
        source_id=source_id,
    )
    with pytest.raises(ValueError, match="claim CANONICAL"):
        block.promote_canonical_language_knowledge(
            discovered["record_id"],
            f"Conhecimento linguístico {marker}",
            domain="semântica",
            branch="lexical_semantics",
        )

    canonical = _canonical_fact(suite, marker)
    item = block.promote_canonical_language_knowledge(
        canonical["record_id"],
        f"Conhecimento linguístico {marker}",
        domain="semântica",
        branch="lexical_semantics",
        properties={"scope": "general"},
        contexts=["educational"],
        summary="Conhecimento linguístico geral.",
    )
    assert item["namespace"] == "B08"
    assert item["properties"]["communication_intent_certainty"] is False
    assert item["properties"]["single_signal_proves_meaning"] is False
    assert item["properties"]["runtime_translation_support_implied"] is False
    trace = knowledge.trace(item["knowledge_id"])
    assert trace["canonical_claim"]["record"]["lifecycle_state"] == "CANONICAL"
    assert trace["canonical_claim"]["evidence"]


def test_block8_reuses_language_manager_for_operational_translation_without_canonicalizing(tmp_path):
    manager = LanguageManager(settings_path=tmp_path / "language.json")
    block, _knowledge, _suite = _language_block(manager=manager)
    result = block.operational_equivalent("e aí, beleza?", "en-US")
    assert result["available"] is True
    assert result["complete"] is True
    assert result["canonicalized"] is False
    assert result["target_locale"] == "en-US"


def test_block8_variant_and_handlers_are_explicit_and_nonintrusive():
    item = CommunicationCatalog().get_variant("LANG-B08-0000000001")
    assert item["domain"] == "language_systems"
    assert item["branch"] == "phonetics_phonology"
    assert item["lens"] == "concept"
    assert "Idioma=" in item["prompt"]
    assert "não provam intenção" in item["prompt"]

    block, _knowledge, _suite = _language_block()
    assert "BLOCO 8" in block.handle("status bloco 8")
    assert "LANG-B08-0000000001" in block.handle("LANG-B08-0000000001")
    assert "Português" in block.handle("idiomas bloco 8")
    assert "não trata forma" in block.handle("intenção comunicativa automática")
    assert block.handle("uma conversa cotidiana sem comando de linguagem") is None
