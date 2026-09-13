from uuid import uuid4

from core.cognitive_catalog import CognitiveContentCatalog, THEME_ORDER
from core.labs import CodeLab, DocumentRAG, MathLab, ResearchAgent, SimulationLab
from core.mind import CognitiveSuite, MetacognitionEngine, TruthVerifier


def test_cognitive_catalog_exact_scale_and_boundaries():
    catalog = CognitiveContentCatalog()
    stats = catalog.stats()
    assert stats["themes"] == 15
    assert stats["canonical_nodes_per_theme"] == 1000
    assert stats["contents_per_theme"] == 1_000_000
    assert stats["total_content_variations"] == 15_000_000
    for theme in THEME_ORDER:
        first = catalog.content_id(theme, 0, 0)
        last = catalog.content_id(theme, 999, 999)
        assert first.endswith("-0000001")
        assert last.endswith("-1000000")
        assert catalog.get_variant(first)["theme"] == theme
        assert catalog.get_variant(last)["theme"] == theme


def test_suite_exposes_all_requested_capabilities():
    suite = CognitiveSuite()
    stats = suite.stats()
    assert stats["capabilities"] == 15
    assert stats["support_contents_per_capability"] == 1_000_000
    assert stats["support_contents_total"] == 15_000_000
    assert stats["canonical_nodes_total"] == 15_000
    assert stats["autonomous_code_modification"] is False


def test_reasoning_planning_and_metacognition():
    suite = CognitiveSuite()
    reasoning = suite.reasoning.analyze("Projetar um software sem internet e com baixa latência")
    assert "software" in reasoning["domains"]
    assert reasoning["constraints"]
    plan = suite.planner.plan("criar um software local")
    assert len(plan["steps"]) == 6
    assert plan["steps"][1]["depends_on"] == (1,)
    meta = MetacognitionEngine().assess("qual é o dado atual?", current_information=True)
    assert meta["recommended_action"] == "research_if_network_allowed"


def test_cognitive_memory_graph_project_and_user_model_are_persistent():
    suite = CognitiveSuite()
    marker = uuid4().hex
    memory_id = suite.memory.remember("decision", f"decisão {marker}", importance=0.9)
    assert memory_id > 0
    assert any(marker in row["content"] for row in suite.memory.recall(marker))

    a = suite.graph.add_entity("concept", f"A {marker}")
    b = suite.graph.add_entity("concept", f"B {marker}")
    suite.graph.relate(a, b, "related_to")
    assert any(row["relation"] == "related_to" for row in suite.graph.neighbors(a))

    project_name = f"Projeto {marker}"
    project = suite.projects.create(project_name, "validar persistência")
    assert project["status"] == "active"
    events = suite.projects.add_event(project_name, "decision", "usar arquitetura integrada")
    assert events[-1]["event_type"] == "decision"

    suite.user_model.set(f"format_{marker}", {"style": "concise"}, confidence=1.0, source="declared")
    assert suite.user_model.get(f"format_{marker}")["value"]["style"] == "concise"


def test_scientific_reasoning_and_truth_verification_do_not_invent_certainty():
    suite = CognitiveSuite()
    scientific = suite.science.evaluate("A aumenta B", observations=[{"stance": "support"}, {"stance": "refute"}])
    assert scientific["evidence_summary"]["observations"] == 2
    verifier = TruthVerifier()
    empty = verifier.verify("afirmação sem fonte")
    assert empty["verdict"] == "insufficient_evidence"
    supported = verifier.verify("afirmação", [
        {"stance": "support", "credibility": 1.0, "source": "primary"},
        {"stance": "support", "credibility": 0.9, "source": "replication"},
        {"stance": "support", "credibility": 0.8, "source": "review"},
    ])
    assert supported["verdict"] == "supported"
    assert supported["confidence"] > 0.8


def test_math_lab_symbolic_capabilities():
    lab = MathLab()
    assert lab.available
    assert lab.derivative("x^3 + 2*x", "x") == "3*x**2 + 2"
    assert lab.integral("2*x", "x") == "x**2"
    assert set(lab.solve("x^2=4", "x")) == {"-2", "2"}
    assert lab.simplify("x + x") == "2*x"


def test_simulation_lab_is_reproducible():
    projectile = SimulationLab.projectile(10, 45, steps=11)
    assert projectile["range_m"] > 10
    assert len(projectile["points"]) == 11
    pi1 = SimulationLab.monte_carlo_pi(5000, seed=123)
    pi2 = SimulationLab.monte_carlo_pi(5000, seed=123)
    assert pi1 == pi2
    ode = SimulationLab.integrate_ode(lambda _t, y: y, 1.0, 0.0, 1.0, 0.05)
    assert 2.6 < ode["final"] < 2.8


def test_code_lab_allows_small_safe_python_and_blocks_os_access():
    lab = CodeLab()
    ok = lab.run("import math\nprint(int(math.sqrt(81)))")
    assert ok["ok"] and ok["stdout"].strip() == "9"
    blocked = lab.run("import os\nprint(os.getcwd())")
    assert not blocked["ok"]
    assert "import bloqueado" in blocked["stderr"]


def test_document_rag_indexes_deduplicates_and_retrieves():
    suite = CognitiveSuite()
    marker = uuid4().hex
    text = (f"{marker} física energia conservação experimento validação. " * 80).strip()
    first = suite.rag.ingest_text(text, source=f"unit:{marker}", title=f"Doc {marker}")
    second = suite.rag.ingest_text(text, source=f"unit:{marker}", title=f"Doc {marker}")
    assert first["created"] is True
    assert second["created"] is False
    hits = suite.rag.search(marker, top_k=3)
    assert hits and marker in hits[0].content
    grounded = suite.rag.grounded_context(marker)
    assert grounded["hits"] >= 1
    assert grounded["citations"][0]["source"] == f"unit:{marker}"


def test_research_agent_is_network_gated_and_has_a_reproducible_plan():
    suite = CognitiveSuite()
    offline = suite.research.search_crossref("quantum gravity", network_enabled=False)
    assert offline["ok"] is False and offline["reason"] == "network_disabled"
    plan = ResearchAgent.research_plan("quantum gravity")
    assert len(plan["steps"]) >= 5


def test_multiagent_and_self_improvement_are_bounded():
    suite = CognitiveSuite()
    result = suite.agents.run([
        {"agent": "reasoning", "kwargs": {"problem": "analisar um experimento científico"}},
        {"agent": "planning", "kwargs": {"goal": "criar software"}},
    ])
    assert not result["errors"]
    assert len(result["results"]) == 2
    component = f"unit-{uuid4().hex}"
    suite.self_improvement.record(component, "quality", 0.4, {"reason": "teste"})
    report = suite.self_improvement.report(component)
    assert report["mean_score"] == 0.4
    assert report["recommendations"]


def test_daily_growth_counts_only_unique_sourced_records():
    suite = CognitiveSuite()
    marker = uuid4().hex
    record = {"content": f"Informação validada e suficientemente longa para o teste {marker}.", "source": f"unit:{marker}", "source_type": "test", "confidence": 0.9}
    first = suite.growth.ingest("reasoning", [record], target_count=1)
    second = suite.growth.ingest("reasoning", [record], target_count=1)
    assert first["accepted"] == 1 and first["status"] == "complete"
    assert second["accepted"] == 0 and second["duplicates"] == 1 and second["status"] == "partial"


def test_chat_handlers_are_explicit_and_non_intrusive():
    suite = CognitiveSuite()
    assert suite.handle("uma pergunta comum sobre qualquer coisa") is None
    assert "Plano:" in suite.handle("planeje construir um sistema local")
    assert "Resultado" in suite.handle("derive x^2 em x")
    assert "Simulação" in suite.handle("simule lançamento 10 a 45 graus")
    assert "STAR MIND" in suite.handle("status mind")
