from uuid import uuid4

from core.attention_salience import (
    ADDRESSABLE_CONTENTS,
    ATTENTION_BRANCHES,
    ATTENTION_DOMAINS,
    ATTENTION_LENSES,
    ATTENTION_POLICY,
    CANONICAL_NODES,
    VARIANT_AXES,
    VARIANTS_PER_NODE,
    AttentionCatalog,
    AttentionSalience,
)
from core.memory_continuity import MemoryContinuity
from core.mind import CognitiveSuite
from core.self_model import SelfModel
from core.star_identity import StarIdentity
from core.state import StarState
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _block(*, max_candidates=32, max_focus=8):
    suite = CognitiveSuite()
    knowledge = UniversalKnowledgeArchitecture(suite.epistemics, suite.graph)
    state = StarState()
    self_model = SelfModel(knowledge, identity=StarIdentity(), state=state, mind=suite)
    memory = MemoryContinuity(
        knowledge,
        memory=suite.memory,
        graph=suite.graph,
        projects=suite.projects,
        self_model=self_model,
    )
    block = AttentionSalience(
        knowledge,
        memory_continuity=memory,
        state=state,
        self_model=self_model,
        max_candidates=max_candidates,
        max_focus=max_focus,
    )
    return block, knowledge, suite, state, memory


def test_block14_catalog_is_exactly_1b_on_demand():
    catalog = AttentionCatalog()
    stats = catalog.stats()
    assert len(ATTENTION_DOMAINS) == 10
    assert len(ATTENTION_BRANCHES) == 50
    assert len(ATTENTION_LENSES) == 10
    assert CANONICAL_NODES == 500
    assert VARIANTS_PER_NODE == 2_000_000
    assert ADDRESSABLE_CONTENTS == 1_000_000_000
    assert stats["materialization"] == "on-demand"
    assert stats["preloaded_candidates"] == 0
    assert catalog.content_id(0, 0) == "ATTN-B14-0000000001"
    assert catalog.content_id(499, 1_999_999) == "ATTN-B14-1000000000"
    assert catalog.get_variant("ATTN-B14-1000000001") is None


def test_block14_variant_axes_multiply_to_2m_per_node():
    sizes = {name: len(values) for name, values in VARIANT_AXES}
    assert sizes == {
        "candidate_source": 10,
        "goal_alignment": 10,
        "recency": 10,
        "risk": 10,
        "urgency": 5,
        "confidence": 4,
        "attention_state": 10,
    }
    product = 1
    for value in sizes.values():
        product *= value
    assert product == 2_000_000


def test_every_requested_attention_concept_has_five_branches():
    assert set(ATTENTION_DOMAINS) == {
        "attention", "salience", "priority", "active_goals", "active_entities",
        "recent_context", "hypotheses", "temporary_results", "risks", "urgency",
    }
    assert all(sum(branch.domain == domain for branch in ATTENTION_BRANCHES) == 5 for domain in ATTENTION_DOMAINS)


def test_b14_reuses_exact_b13_working_memory_instead_of_parallel_buffer():
    block, _knowledge, _suite, _state, memory = _block()
    assert block.working is memory.working
    goal = block.set_active_goal("ship-b14", "validar bloco 14 sem regressões", priority=0.9)
    assert memory.working.get(goal["key"])["content"] == "validar bloco 14 sem regressões"
    stats = block.stats()
    assert stats["working_memory_shared_with_b13"] is True
    assert stats["parallel_working_memory"] is False


def test_active_goals_entities_hypotheses_and_results_are_roles_in_working_memory():
    block, _knowledge, _suite, _state, _memory = _block()
    block.set_active_goal("goal", "corrigir falha no sistema", priority=0.9)
    block.set_active_entity("star-core", "STAR Core", importance=0.8, entity_type="system")
    block.add_hypothesis("hyp", "a falha pode estar no roteamento", confidence=0.4)
    block.add_temporary_result("tmp", "teste parcial aprovado", importance=0.7)
    snap = block.snapshot()
    assert len(snap["active_goals"]) == 1
    assert len(snap["active_entities"]) == 1
    assert len(snap["hypotheses"]) == 1
    assert len(snap["temporary_results"]) == 1
    assert snap["hypotheses"][0]["metadata"]["epistemic_kind"] == "hypothesis"


def test_attention_state_reads_star_state_and_does_not_duplicate_it():
    block, _knowledge, _suite, state, _memory = _block()
    state.update(attention=73, focus=81, cognitive_load=22, energy=67)
    observed = block.attention_state()
    assert observed["source"] == "core.state.StarState"
    assert observed["attention"] == 73
    assert observed["focus"] == 81
    assert observed["cognitive_load"] == 22
    assert observed["energy"] == 67
    assert block.stats()["parallel_state"] is False


def test_scoring_uses_goals_entities_risk_urgency_recency_and_confidence():
    block, _knowledge, _suite, _state, _memory = _block()
    block.set_active_goal("g", "corrigir roteamento STAR", priority=1.0)
    block.set_active_entity("e", "STAR Core", importance=1.0)
    score = block.score({
        "content": "corrigir roteamento do STAR Core",
        "priority": 0.8,
        "salience": 0.7,
        "recency": 0.9,
        "risk": 0.6,
        "urgency": 0.5,
        "confidence": 0.75,
    })
    assert 0.0 <= score["score"] <= 1.0
    assert score["components"]["goal_relevance"] > 0
    assert score["components"]["entity_relevance"] > 0
    assert score["components"]["risk"] == 0.6
    assert score["components"]["urgency"] == 0.5
    assert score["selection_is_inference"] is True
    assert score["operational_authorization"] is False


def test_risk_and_urgency_can_raise_rank_but_never_authorize_action():
    block, _knowledge, _suite, _state, _memory = _block()
    normal = {"id": "normal", "content": "item comum", "priority": 0.5, "salience": 0.5, "risk": 0.0, "urgency": 0.0}
    risky = {"id": "risk", "content": "item de risco", "priority": 0.5, "salience": 0.5, "risk": 1.0, "urgency": 1.0}
    result = block.select_relevant([normal, risky], limit=2)
    assert result["selected"][0]["candidate"]["id"] == "risk"
    assert all(item["operational_authorization"] is False for item in result["selected"])
    assert ATTENTION_POLICY["risk_may_raise_attention"] is True
    assert ATTENTION_POLICY["urgency_grants_permission"] is False


def test_selection_is_bounded_and_truncates_generator_without_loading_all_items():
    block, _knowledge, _suite, _state, _memory = _block(max_candidates=16, max_focus=4)
    produced = {"count": 0}

    def candidates():
        for index in range(10000):
            produced["count"] += 1
            yield {"id": index, "content": f"candidate {index}", "priority": index % 10 / 10}

    result = block.select_relevant(candidates(), limit=4)
    assert result["considered"] == 16
    assert result["input_truncated"] is True
    assert produced["count"] == 17
    assert len(result["selected"]) == 4
    assert result["loads_all_available_contents"] is False


def test_invalid_candidates_are_rejected_without_breaking_selection():
    block, _knowledge, _suite, _state, _memory = _block()
    result = block.select_relevant([{}, "invalid", {"content": "válido", "priority": 1.0}], limit=4)
    assert result["rejected_invalid"] == 2
    assert len(result["selected"]) == 1
    assert result["selected"][0]["content"] == "válido"


def test_select_from_memory_queries_b13_then_focuses_bounded_results():
    block, _knowledge, _suite, _state, memory = _block(max_candidates=32, max_focus=5)
    marker = uuid4().hex
    memory.remember("semantic", f"contexto importante {marker}", source="unit-test", importance=0.9)
    memory.remember("working", f"resultado recente {marker}", source="unit-test", importance=1.0)
    result = block.select_from_memory(marker, recall_limit=20, focus_limit=5)
    assert result["considered"] >= 2
    assert len(result["selected"]) <= 5
    assert result["loads_all_available_contents"] is False


def test_recent_context_is_bounded_view_of_b13_working_memory():
    block, _knowledge, _suite, _state, memory = _block(max_focus=4)
    for index in range(10):
        memory.working.add(f"ctx {index}", source="unit-test")
    recent = block.recent_context(limit=100)
    assert len(recent) == 4
    assert recent[-1]["content"] == "ctx 9"


def test_taxonomy_uses_shared_graph_and_links_b13_and_star_state():
    block, knowledge, suite, _state, _memory = _block()
    result = block.materialize_taxonomy("risks")
    assert result["branches_materialized"] == 5
    assert result["knowledge_graph"] == "shared"
    assert result["parallel_attention_graph_created"] is False
    assert block.graph is knowledge.graph is suite.graph
    labels = {item["label"] for item in suite.graph.neighbors("ATTENTION-TAX-ROOT")}
    assert "B13 Working Memory" in labels
    assert "StarState" in labels
    assert "Riscos" in labels


def test_policy_catalog_prompt_and_handlers_are_explicit_nonintrusive():
    assert ATTENTION_POLICY["bounded_candidate_window"] is True
    assert ATTENTION_POLICY["loads_all_available_contents"] is False
    assert ATTENTION_POLICY["selection_is_fact"] is False
    assert ATTENTION_POLICY["salience_grants_permission"] is False

    item = AttentionCatalog().get_variant("ATTN-B14-0000000001")
    assert item["domain"] == "attention"
    assert item["branch"] == "focus_target"
    assert item["lens"] == "signal"
    assert "janela bounded" in item["prompt"]

    block, _knowledge, _suite, _state, _memory = _block()
    assert "BLOCO 14" in block.handle("status bloco 14")
    assert "ATTN-B14-0000000001" in block.handle("ATTN-B14-0000000001")
    assert block.handle("uma conversa comum sem comando de atenção") is None
