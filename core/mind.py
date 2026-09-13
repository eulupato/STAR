"""STAR MIND V2 alpha: raciocínio, planejamento, memória, verificação e coordenação.

A suíte não é um LLM e não tenta expor chain-of-thought. Ela produz artefatos
operacionais auditáveis: objetivos, hipóteses, passos, evidências, checks e
níveis de confiança. Modelos locais/cloud podem ser conectados depois como
recursos, sem se tornarem a identidade da STAR.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
import hashlib
import re
from typing import Callable

from core.cognitive_catalog import CognitiveContentCatalog, THEME_ORDER
from core.labs import CodeLab, DocumentRAG, MathLab, ResearchAgent, SimulationLab
from database.cognitive_store import CognitiveStore


def _clean(text: str) -> str:
    return " ".join(str(text or "").strip().split())


@dataclass(frozen=True)
class PlanStep:
    index: int
    title: str
    purpose: str
    depends_on: tuple[int, ...] = ()
    validation: str = "resultado verificável"


class ReasoningEngine:
    DOMAIN_HINTS = {
        "software": ("codigo", "código", "python", "api", "software", "bug", "programa"),
        "science": ("hipotese", "hipótese", "experimento", "evidencia", "evidência", "cientifico", "científico"),
        "engineering": ("engenharia", "motor", "estrutura", "projeto", "mecanismo", "material"),
        "mathematics": ("equacao", "equação", "calculo", "cálculo", "matemat", "deriv", "integr"),
        "research": ("pesquisa", "artigo", "paper", "fonte", "literatura"),
    }

    def analyze(self, problem: str) -> dict:
        problem = _clean(problem)
        if not problem:
            raise ValueError("problema vazio")
        lower = problem.lower()
        domains = [name for name, hints in self.DOMAIN_HINTS.items() if any(h in lower for h in hints)] or ["general"]
        constraints = []
        for segment in re.split(r"[.;\n]", problem):
            s = segment.strip(); sl = s.lower()
            if s and any(k in sl for k in ("sem ", "com no máximo", "com no minimo", "com no mínimo", "deve ", "não pode", "nao pode", "limite", "restri")):
                constraints.append(s)
        unknowns = ["dados de entrada ainda não fornecidos" if len(problem.split()) < 8 else "incertezas e parâmetros não declarados", "critério quantitativo de sucesso" if not re.search(r"\d", problem) else "validade dos valores e unidades informados"]
        return {"problem": problem, "domains": domains, "goal": problem, "constraints": constraints, "unknowns": unknowns, "candidate_approaches": ["usar conhecimento local e regras determinísticas primeiro", "calcular/simular quando houver grandezas ou modelo formal", "buscar evidência externa somente quando frescor ou lacuna exigir"], "verification": ["checar suposições e unidades", "procurar contradições e contraexemplos", "comparar com benchmark/fonte quando disponível", "declarar limites e confiança"], "note": "artefato de raciocínio auditável; não é transcrição de pensamento interno"}


class Planner:
    def plan(self, goal: str, *, constraints: list[str] | None = None) -> dict:
        goal = _clean(goal)
        if not goal: raise ValueError("objetivo vazio")
        lower = goal.lower()
        if any(k in lower for k in ("codigo", "código", "software", "app", "sistema")):
            titles = ("Definir comportamento esperado", "Mapear arquitetura existente", "Implementar mudança mínima", "Executar testes", "Medir regressões", "Documentar e validar")
        elif any(k in lower for k in ("experimento", "hipotese", "hipótese", "cient")):
            titles = ("Definir pergunta e hipótese", "Definir variáveis e controles", "Planejar medição", "Executar/coletar dados", "Analisar incerteza", "Concluir e replicar")
        elif any(k in lower for k in ("constru", "engenharia", "mecanismo", "protótipo", "prototipo")):
            titles = ("Especificar requisitos", "Calcular limites", "Comparar conceitos", "Simular", "Prototipar com segurança", "Testar e iterar")
        else:
            titles = ("Definir objetivo", "Levantar contexto e restrições", "Decompor subtarefas", "Executar itens independentes", "Verificar resultados", "Consolidar próximo estado")
        steps = [PlanStep(i, title, f"Contribuir para: {goal}", () if i == 1 else (i - 1,), "critério explícito antes de avançar") for i, title in enumerate(titles, 1)]
        return {"goal": goal, "constraints": list(constraints or []), "steps": [asdict(s) for s in steps], "parallelizable": [4] if len(steps) >= 4 else [], "status": "planned"}


class MetacognitionEngine:
    def assess(self, query: str, *, local_answer: bool = False, confidence: float | None = None, current_information: bool = False) -> dict:
        confidence = 1.0 if local_answer and confidence is None else (0.0 if confidence is None else max(0.0, min(float(confidence), 1.0)))
        if local_answer and confidence >= 0.8 and not current_information: action = "answer_local"
        elif current_information: action = "research_if_network_allowed"
        elif local_answer: action = "verify_or_calculate"
        else: action = "search_memory_knowledge_tools_then_research"
        return {"query": _clean(query), "known": bool(local_answer), "confidence": confidence, "recommended_action": action}


class CognitiveMemory:
    KINDS = {"working", "episodic", "semantic", "conversation", "project", "decision", "error", "temporal", "people", "object", "preference"}
    def __init__(self, store: CognitiveStore): self.store = store
    def remember(self, kind: str, content: str, **kwargs) -> int:
        if kind not in self.KINDS: raise ValueError("tipo de memória inválido")
        return self.store.remember(kind, content, **kwargs)
    def recall(self, query: str, *, kinds=None, limit: int = 10) -> list[dict]: return self.store.recall(query, kinds=kinds, limit=limit)


class KnowledgeGraph:
    def __init__(self, store: CognitiveStore): self.store = store
    @staticmethod
    def stable_id(node_type: str, label: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:64]
        digest = hashlib.sha1(f"{node_type}:{label}".encode("utf-8")).hexdigest()[:10]
        return f"{node_type}:{slug}:{digest}"
    def add_entity(self, node_type: str, label: str, *, data=None, confidence: float = 1.0, node_id: str | None = None) -> str:
        node_id = node_id or self.stable_id(node_type, label)
        return self.store.upsert_node(node_id, node_type, label, data=data, confidence=confidence)
    def relate(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0, metadata=None): self.store.add_edge(source_id, target_id, relation, weight=weight, metadata=metadata)
    def neighbors(self, node_id: str, **kwargs) -> list[dict]: return self.store.neighbors(node_id, **kwargs)


class ScientificReasoner:
    def evaluate(self, hypothesis: str, *, observations: list[dict] | None = None) -> dict:
        observations = list(observations or [])
        supportive = sum(1 for x in observations if x.get("stance") == "support")
        contrary = sum(1 for x in observations if x.get("stance") == "refute")
        return {"hypothesis": _clean(hypothesis), "operationalization": "definir variáveis observáveis, unidades e protocolo", "predictions": ["previsão que diferenciaria a hipótese de alternativas", "previsão quantitativa quando o modelo permitir"], "controls": ["controle negativo/linha de base quando aplicável", "controle de confundidores conhecidos"], "evidence_summary": {"observations": len(observations), "support": supportive, "refute": contrary}, "falsification": "definir resultado observável que reduziria substancialmente a plausibilidade", "uncertainty": "quantificar erro de medição, amostragem e incerteza de modelo separadamente", "replication": "documentar protocolo, dados, parâmetros e código suficientes para repetição independente"}


class TruthVerifier:
    def verify(self, claim: str, evidence: list[dict] | None = None) -> dict:
        evidence = list(evidence or [])
        if not evidence: return {"claim": _clean(claim), "verdict": "insufficient_evidence", "confidence": 0.0, "support": 0.0, "refute": 0.0, "sources": []}
        support = refute = total = 0.0; sources = []
        for item in evidence:
            credibility = max(0.0, min(float(item.get("credibility", 0.5)), 1.0)); stance = item.get("stance", "neutral"); total += credibility
            if stance == "support": support += credibility
            elif stance == "refute": refute += credibility
            sources.append({"source": item.get("source"), "stance": stance, "credibility": credibility})
        balance = 0.0 if not total else (support - refute) / total; coverage = min(1.0, total / 3.0); confidence = min(1.0, abs(balance) * coverage)
        if total < 0.75: verdict = "insufficient_evidence"
        elif abs(balance) < 0.25: verdict = "disputed_or_mixed"
        else: verdict = "supported" if balance > 0 else "refuted"
        return {"claim": _clean(claim), "verdict": verdict, "confidence": confidence, "support": support, "refute": refute, "sources": sources}


class ProjectManager:
    def __init__(self, store: CognitiveStore): self.store = store
    def create(self, name: str, objective: str = "", metadata=None): return self.store.create_project(name, objective, metadata)
    def get(self, name: str): return self.store.get_project(name)
    def list(self, status: str | None = None): return self.store.list_projects(status)
    def add_event(self, name: str, event_type: str, content: str, metadata=None):
        project = self.store.get_project(name)
        if not project: raise KeyError(name)
        self.store.add_project_event(project["project_id"], event_type, content, metadata)
        return self.store.project_events(project["project_id"])


class UserModel:
    """Perfil explícito e auditável. Não infere atributos sensíveis automaticamente."""
    def __init__(self, store: CognitiveStore): self.store = store
    def set(self, key: str, value, *, confidence: float = 1.0, source: str = "declared"): self.store.set_user_model(key, value, confidence=confidence, source=source)
    def get(self, key: str | None = None): return self.store.get_user_model(key)


class MultiAgentOrchestrator:
    def __init__(self): self._agents: dict[str, Callable] = {}
    def register(self, name: str, fn: Callable): self._agents[name] = fn
    def available(self): return tuple(sorted(self._agents))
    def run(self, tasks: list[dict], *, max_workers: int = 4) -> dict:
        results, errors = {}, {}
        def invoke(task):
            name = task["agent"]
            if name not in self._agents: raise KeyError(f"agente não registrado: {name}")
            return self._agents[name](**task.get("kwargs", {}))
        with ThreadPoolExecutor(max_workers=max(1, min(int(max_workers), 8))) as pool:
            future_map = {pool.submit(invoke, task): i for i, task in enumerate(tasks)}
            for future in as_completed(future_map):
                i = future_map[future]
                try: results[i] = future.result()
                except Exception as exc: errors[i] = f"{type(exc).__name__}: {exc}"
        return {"results": [results.get(i) for i in range(len(tasks))], "errors": errors, "agents": self.available()}


class SelfImprovementEvaluator:
    """Avalia e recomenda; nunca altera o código automaticamente."""
    def __init__(self, store: CognitiveStore): self.store = store
    def record(self, component: str, metric: str, score: float, details=None):
        score = max(0.0, min(float(score), 1.0)); self.store.record_evaluation(component, metric, score, details); return score
    def report(self, component: str | None = None, limit: int = 100) -> dict:
        items = self.store.evaluations(component, limit)
        if not items: return {"component": component, "samples": 0, "mean_score": None, "recommendations": []}
        mean = sum(float(x["score"]) for x in items) / len(items); recommendations = []
        if mean < 0.8: recommendations.append("investigar métricas abaixo de 0,8 antes de adicionar complexidade")
        if any(float(x["score"]) < 0.5 for x in items): recommendations.append("abrir diagnóstico de causa raiz para falhas abaixo de 0,5")
        return {"component": component, "samples": len(items), "mean_score": mean, "recommendations": recommendations, "items": items}


class DailyKnowledgeGrowth:
    """Ingestão diária honesta: só conta registros únicos, com fonte e proveniência."""
    def __init__(self, store: CognitiveStore): self.store = store
    def ingest(self, theme: str, records, *, target_count: int = 1_000_000, run_date: str | None = None):
        if theme not in THEME_ORDER: raise KeyError(theme)
        return self.store.ingest_facts(theme, records, target_count=target_count, run_date=run_date)


class CognitiveSuite:
    CAPABILITIES = ("reasoning", "planning", "memory", "knowledge_graph", "scientific_reasoning", "mathematics", "simulation", "coding", "verification", "document_rag", "research", "projects", "user_model", "multi_agent", "self_improvement")

    def __init__(self, store: CognitiveStore | None = None):
        self.store = store or CognitiveStore(); self.catalog = CognitiveContentCatalog(); self.reasoning = ReasoningEngine(); self.planner = Planner(); self.metacognition = MetacognitionEngine(); self.memory = CognitiveMemory(self.store); self.graph = KnowledgeGraph(self.store); self.science = ScientificReasoner(); self.math = MathLab(); self.simulation = SimulationLab(); self.code = CodeLab(); self.verifier = TruthVerifier(); self.rag = DocumentRAG(self.store); self.research = ResearchAgent(self.store); self.projects = ProjectManager(self.store); self.user_model = UserModel(self.store); self.agents = MultiAgentOrchestrator(); self.self_improvement = SelfImprovementEvaluator(self.store); self.growth = DailyKnowledgeGrowth(self.store)
        self.agents.register("reasoning", self.reasoning.analyze); self.agents.register("planning", self.planner.plan); self.agents.register("research_plan", self.research.research_plan)

    def stats(self) -> dict:
        catalog = self.catalog.stats()
        return {"status": "experimental-v2", "capabilities": len(self.CAPABILITIES), "capability_keys": list(self.CAPABILITIES), "support_contents_per_capability": catalog["contents_per_theme"], "support_contents_total": catalog["total_content_variations"], "canonical_nodes_total": catalog["themes"] * catalog["canonical_nodes_per_theme"], "store": self.store.stats(), "math": self.math.stats(), "registered_agents": list(self.agents.available()), "autonomous_code_modification": False}

    def handle(self, text: str, *, network_enabled: bool = False) -> str | None:
        raw = _clean(text); low = raw.lower()
        if not raw: return None
        if low in {"status mind", "status da mind", "status cognitivo", "status da mente"}:
            s = self.stats(); return (f"🧠 STAR MIND: {s['capabilities']} capacidades cognitivas | {s['support_contents_total']} conteúdos operacionais endereçáveis | FTS5={'ATIVO' if s['store']['fts5_available'] else 'FALLBACK'} | SymPy={'ATIVO' if s['math']['sympy_available'] else 'INDISPONÍVEL'}.")
        m = re.match(r"^(?:star[, ]+)?(?:planeje|planejar|crie um plano para)\s+(.+)$", raw, re.I)
        if m: return self._format_plan(self.planner.plan(m.group(1)))
        m = re.match(r"^(?:star[, ]+)?(?:raciocine sobre|analise estruturadamente|raciocínio sobre|raciocinio sobre)\s+(.+)$", raw, re.I)
        if m:
            r = self.reasoning.analyze(m.group(1)); return "🧠 Análise estruturada\nObjetivo: " + r["goal"] + "\nVerificações: " + "; ".join(r["verification"])
        m = re.match(r"^(?:star[, ]+)?(?:derive|derivar)\s+(.+?)(?:\s+em\s+([A-Za-z]))?$", raw, re.I)
        if m and self.math.available: return f"∂ Resultado: {self.math.derivative(m.group(1), m.group(2) or 'x')}"
        m = re.match(r"^(?:star[, ]+)?(?:integre|integrar)\s+(.+?)(?:\s+em\s+([A-Za-z]))?$", raw, re.I)
        if m and self.math.available: return f"∫ Resultado: {self.math.integral(m.group(1), m.group(2) or 'x')}"
        m = re.match(r"^(?:star[, ]+)?(?:resolva a equação|resolva a equacao|resolver equação|resolver equacao)\s+(.+)$", raw, re.I)
        if m and self.math.available: return "🧮 Soluções: " + ", ".join(self.math.solve(m.group(1)))
        m = re.match(r"^(?:star[, ]+)?(?:simule|simular)\s+lançamento\s+([\d.,]+)\s*(?:m/s)?\s+(?:a|em)\s+([\d.,]+)\s*(?:graus|°)?$", raw, re.I)
        if m:
            result = self.simulation.projectile(float(m.group(1).replace(',', '.')), float(m.group(2).replace(',', '.'))); return f"🧪 Simulação: alcance={result['range_m']:.3f} m | voo={result['flight_time_s']:.3f} s | altura máxima={result['max_height_m']:.3f} m. Hipóteses: " + ", ".join(result["assumptions"])
        m = re.match(r"^(?:star[, ]+)?(?:busque nos documentos|pesquise nos documentos)\s+(.+)$", raw, re.I)
        if m:
            context = self.rag.grounded_context(m.group(1), top_k=5)
            if not context["hits"]: return "Não encontrei trechos indexados para essa consulta."
            return "📚 Encontrei fontes locais:\n" + "\n".join(f"[{c['index']}] {c['title']} — {c['source']}" for c in context["citations"])
        m = re.match(r"^(?:star[, ]+)?(?:pesquise artigos sobre|pesquisar artigos sobre)\s+(.+)$", raw, re.I)
        if m:
            result = self.research.search_crossref(m.group(1), rows=8, network_enabled=network_enabled)
            if not result["ok"]: return "A pesquisa acadêmica online está disponível, mas o modo de rede está desativado."
            if not result["sources"]: return "Não encontrei metadados acadêmicos para essa busca."
            return "🔎 Crossref:\n" + "\n".join(f"- {x['title']} ({x.get('published') or 's/d'}) — {x.get('doi') or x.get('url') or 'sem identificador'}" for x in result["sources"][:8])
        m = re.match(r"^(?:star[, ]+)?crie projeto\s+([^:]+)(?::\s*(.+))?$", raw, re.I)
        if m:
            p = self.projects.create(m.group(1).strip(), (m.group(2) or "").strip()); return f"📁 Projeto '{p['name']}' registrado com status {p['status']}."
        m = re.fullmatch(r"([A-Z]+-\d{7})", raw.upper())
        if m:
            item = self.catalog.get_variant(m.group(1))
            if item: return f"🧠 {item['id']} — {item['theme_label']} / {item['area']} / {item['lens_label']}\n{item['prompt']}"
        return None

    @staticmethod
    def _format_plan(plan: dict) -> str:
        lines = ["🧭 Plano: " + plan["goal"]]
        for step in plan["steps"]:
            deps = f" [depende de {','.join(map(str, step['depends_on']))}]" if step["depends_on"] else ""
            lines.append(f"{step['index']}. {step['title']}{deps} — {step['validation']}")
        return "\n".join(lines)
