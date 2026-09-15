"""BLOCO 20 — metacognição.

Coordena o ``MetacognitionEngine`` já existente com epistemologia, memória,
atenção, verificação e raciocínio. A camada avalia o que a STAR sabe, não sabe,
acredita, inferiu e quando precisa pesquisar/perguntar/revisar sem varrer todo o
espaço lógico de conhecimento.

Metacognição não promove inferência a fato e não concede autorização operacional.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import prod
import re
import unicodedata
from typing import Any, Iterable

from core.universal_knowledge import UniversalKnowledgeArchitecture


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


@dataclass(frozen=True)
class MetacognitiveBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


_DOMAINS = {
    "knowledge_state": (
        ("known", "O que sabe", "sabe;conhecimento disponível;resposta local;escopo;validade"),
        ("unknown", "O que não sabe", "não sabe;desconhecido;lacuna;ausência;limite"),
        ("knowledge_boundary", "Fronteira do conhecimento", "escopo;limite;domínio;cobertura;desconhecido"),
        ("knowledge_freshness", "Atualidade do conhecimento", "recência;validade temporal;desatualização;data;revisão"),
        ("knowledge_availability", "Disponibilidade do conhecimento", "local;memória;grafo;fonte;recuperação"),
    ),
    "belief_inference": (
        ("belief", "O que acredita", "acredita;crença operacional;plausibilidade;confiança;revisável"),
        ("inference", "O que inferiu", "inferiu;inferência;premissas;conclusão;hipótese"),
        ("belief_vs_fact", "Crença versus fato", "crença ≠ fato;inferência ≠ fato;status epistêmico;proveniência"),
        ("assumptions", "Assunções", "assunção;premissa;condição;hipótese;limite"),
        ("alternative_hypotheses", "Hipóteses alternativas", "alternativa;explicação concorrente;contrafactual;incerteza"),
    ),
    "confidence_uncertainty": (
        ("confidence", "Confiança", "confiança;calibração;evidência;força;intervalo"),
        ("uncertainty", "Incerteza", "incerteza;desconhecido;variância;lacuna;limite"),
        ("confidence_calibration", "Calibração", "calibração;prediction error;acerto;erro;histórico"),
        ("confidence_sources", "Confiança por fonte", "credibilidade;fonte;proveniência;independência;corroboração"),
        ("confidence_limits", "Limites de confiança", "excesso de confiança;baixa confiança;domínio;escopo;revisão"),
    ),
    "sources_provenance": (
        ("source_presence", "Existência de fonte", "fonte existe;sem fonte;proveniência;origem;referência"),
        ("source_quality", "Qualidade da fonte", "credibilidade;qualidade;primária;secundária;autoridade"),
        ("source_independence", "Independência de fontes", "independência;dependência;cópia;corroboração;diversidade"),
        ("source_trace", "Rastreabilidade", "trace;referência;registro;data;origem"),
        ("source_conflict", "Conflito entre fontes", "fontes conflitantes;discordância;contradição;revisão"),
    ),
    "contradictions": (
        ("contradiction_detection", "Detecção de contradições", "contradições;conflito;incompatibilidade;detecção"),
        ("contradiction_preservation", "Preservação de contradições", "não apagar;histórico;versões;proveniência"),
        ("contradiction_resolution", "Resolução provisória", "resolver;comparar evidência;manter disputa;revisar"),
        ("self_contradiction", "Contradição interna", "memória;modelo;crença;inferência;inconsistência"),
        ("temporal_contradiction", "Contradição temporal", "mudança;versão;data;estado antigo;estado atual"),
    ),
    "research_need": (
        ("research_trigger", "Necessidade de pesquisar", "precisa pesquisar;frescor;lacuna;fonte externa;verificação"),
        ("research_scope", "Escopo de pesquisa", "pergunta;termos;domínio;fontes;limites"),
        ("local_first", "Local-first", "memória;conhecimento local;ferramenta;rede;pesquisa"),
        ("fresh_information", "Informação atual", "atual;recente;tempo real;mudança;pesquisa"),
        ("research_stop", "Critério de parada", "evidência suficiente;confiança;corroboração;custo;limite"),
    ),
    "question_need": (
        ("question_trigger", "Necessidade de perguntar", "precisa perguntar;ambiguidade;contexto ausente;preferência"),
        ("missing_context", "Contexto ausente", "parâmetro;restrição;objetivo;referência;escopo"),
        ("clarification", "Clarificação", "pergunta;desambiguação;termo;intenção declarada;opção"),
        ("user_dependent_fact", "Informação dependente do usuário", "preferência;estado pessoal;arquivo;decisão;declaração"),
        ("question_cost", "Custo de perguntar", "necessidade;interrupção;melhor esforço;assunção explícita"),
    ),
    "review_need": (
        ("review_trigger", "Necessidade de revisar", "precisa revisar;contradição;erro;baixa confiança;mudança"),
        ("revision_scope", "Escopo da revisão", "claim;memória;modelo;plano;previsão"),
        ("revision_evidence", "Evidência para revisão", "fonte nova;observação;prediction error;teste;feedback"),
        ("revision_history", "Histórico da revisão", "versão;antes;depois;proveniência;razão"),
        ("review_outcome", "Resultado da revisão", "mantido;refinado;superado;retraído;incerto"),
    ),
    "decision_readiness": (
        ("answer_readiness", "Prontidão para responder", "responder;confiança;fonte;escopo;limites"),
        ("plan_readiness", "Prontidão para planejar", "objetivo;estado;restrições;opções;incerteza"),
        ("decision_readiness", "Prontidão para decidir", "decisão;evidência;risco;alternativas;verificação"),
        ("defer", "Adiar julgamento", "insuficiente;aguardar;pesquisar;perguntar;revisar"),
        ("epistemic_humility", "Humildade epistêmica", "não sei;incerto;limite;confiança calibrada;transparência"),
    ),
    "self_monitoring": (
        ("reasoning_monitor", "Monitorar raciocínio", "raciocínio;assunções;inferências;erros;alternativas"),
        ("memory_monitor", "Monitorar memória", "memória;fonte;recência;conflito;recordação"),
        ("model_monitor", "Monitorar modelos", "World Model;Human Model;Social Model;Self Model;Situation Model"),
        ("prediction_monitor", "Monitorar previsões", "previsão;prediction error;calibração;feedback"),
        ("learning_monitor", "Monitorar aprendizado", "aprendizado;revisão;consistência;origem;mudança"),
    ),
}

DOMAIN_LABELS = {
    "knowledge_state": "Estado do conhecimento",
    "belief_inference": "Crenças e inferências",
    "confidence_uncertainty": "Confiança e incerteza",
    "sources_provenance": "Fontes e proveniência",
    "contradictions": "Contradições",
    "research_need": "Necessidade de pesquisa",
    "question_need": "Necessidade de perguntar",
    "review_need": "Necessidade de revisão",
    "decision_readiness": "Prontidão cognitiva",
    "self_monitoring": "Automonitoramento cognitivo",
}

METACOGNITIVE_BRANCHES = tuple(
    MetacognitiveBranch(domain, key, label, _subs(subtopics))
    for domain, branches in _DOMAINS.items()
    for key, label, subtopics in branches
)

METACOGNITIVE_LENSES = (
    ("state", "estado", "classificar o estado epistêmico atual"),
    ("evidence", "evidência", "identificar evidência e lacunas"),
    ("source", "fonte", "preservar origem e rastreabilidade"),
    ("confidence", "confiança", "calibrar confiança sem transformar score em verdade"),
    ("contradiction", "contradição", "detectar e preservar conflitos"),
    ("alternatives", "alternativas", "manter hipóteses concorrentes"),
    ("freshness", "atualidade", "avaliar validade temporal"),
    ("action_need", "próximo passo", "escolher entre responder, pesquisar, perguntar ou revisar"),
    ("limits", "limites", "declarar o que permanece desconhecido"),
    ("audit", "auditoria", "produzir artefato explicável e rastreável"),
)

CONTEXT_AXIS = ("conversation", "project", "scientific", "technical", "social", "personal", "historical", "current", "decision", "mixed")
EPISTEMIC_AXIS = ("known", "unknown", "belief", "inference", "hypothesis", "prediction", "memory", "observation", "disputed", "superseded")
CONFIDENCE_AXIS = ("none", "very_low", "low", "moderate_low", "moderate", "moderate_high", "high", "very_high", "calibrated", "conflicting")
SOURCE_AXIS = ("none", "B02", "B03", "B13", "B15", "B18", "B19", "user", "tool", "external")
CONTRADICTION_AXIS = ("none", "possible", "single", "multiple", "temporal", "source_conflict", "memory_conflict", "model_conflict", "unresolved", "resolved_provisionally")
NEXT_STEP_AXIS = ("answer", "verify", "research", "ask", "review", "defer", "compare", "simulate", "retrieve", "monitor")
MODE_AXIS = ("primary", "alternative")
VARIANT_AXES = (
    ("context", CONTEXT_AXIS), ("epistemic_state", EPISTEMIC_AXIS),
    ("confidence_band", CONFIDENCE_AXIS), ("source_space", SOURCE_AXIS),
    ("contradiction_state", CONTRADICTION_AXIS), ("next_step", NEXT_STEP_AXIS),
    ("mode", MODE_AXIS),
)

CANONICAL_NODES = len(METACOGNITIVE_BRANCHES) * len(METACOGNITIVE_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE
if len(_DOMAINS) != 10 or len(METACOGNITIVE_BRANCHES) != 50 or len(METACOGNITIVE_LENSES) != 10:
    raise RuntimeError("B20 requer 10 domínios, 50 ramos e 10 lentes")
if CANONICAL_NODES != 500 or VARIANTS_PER_NODE != 2_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B20 inválida")

METACOGNITION_POLICY = {
    "belief_is_fact": False,
    "inference_is_fact": False,
    "confidence_is_truth": False,
    "absence_of_evidence_is_proof_of_falsehood": False,
    "contradictions_are_silently_erased": False,
    "research_need_grants_network_permission": False,
    "question_need_blocks_best_effort_by_default": False,
    "review_rewrites_history": False,
    "bounded_context_selection": True,
    "operational_authorization": False,
    "rule": "SABER ≠ ACREDITAR ≠ INFERIR; CONFIANÇA ≠ VERDADE; NECESSIDADE DE PESQUISA ≠ PERMISSÃO DE REDE",
}


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    value = int(index); out = {}
    for name, values in reversed(VARIANT_AXES):
        value, offset = divmod(value, len(values)); out[name] = values[offset]
    return {name: out[name] for name, _ in VARIANT_AXES}


class MetacognitionCatalog:
    NAMESPACE = "B20"
    PREFIX = "META-B20"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE, "domains": 10, "branches": 50,
            "lenses_per_branch": 10, "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS, "materialization": "on-demand",
            "prepopulated_assessments": 0,
            "truthfulness_note": "1B are addressable metacognitive contexts, not 1B precomputed self-assessments",
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < CANONICAL_NODES: raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE: raise IndexError(variant_index)
        n = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"META-B20-{n:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"META-B20-(\d{10})", _clean(identifier).upper())
        if not match: return None
        n = int(match.group(1))
        if not 1 <= n <= ADDRESSABLE_CONTENTS: return None
        node_i, variant_i = divmod(n - 1, VARIANTS_PER_NODE)
        branch_i, lens_i = divmod(node_i, 10)
        branch = METACOGNITIVE_BRANCHES[branch_i]
        lens_key, lens_label, instruction = METACOGNITIVE_LENSES[lens_i]
        axes = _decode_axes(variant_i)
        return {
            "id": f"META-B20-{n:010d}", "namespace": "B20", "domain": branch.domain,
            "domain_label": DOMAIN_LABELS[branch.domain], "branch": branch.key,
            "branch_label": branch.label, "subtopics": branch.subtopics,
            "lens": lens_key, "lens_label": lens_label, **axes,
            "prompt": f"Avaliar {branch.label} pela lente {lens_label}; {instruction}. Preservar fonte, confiança, contradições e limites.",
        }


class Metacognition:
    NAMESPACE = "B20"
    TAXONOMY_ROOT_ID = "METACOGNITION-TAX-ROOT"

    def __init__(self, knowledge: UniversalKnowledgeArchitecture, *, base_engine, verifier=None,
                 memory_continuity=None, attention_salience=None, reasoning_simulation=None,
                 planning_decision=None, self_model=None):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.base_engine = base_engine
        self.verifier = verifier
        self.memory_continuity = memory_continuity
        self.attention_salience = attention_salience
        self.reasoning_simulation = reasoning_simulation
        self.planning_decision = planning_decision
        self.self_model = self_model
        self.catalog = MetacognitionCatalog()
        self.knowledge.register_namespace(
            self.NAMESPACE, "BLOCO 20 — METACOGNIÇÃO", logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/metacognition.py", metadata={
                "materialization": "on-demand", "reuses_existing_metacognition_engine": True,
                "shared_knowledge_graph": True, "bounded_selection": True,
                "parallel_metacognition_engine_created": False,
            },
        )

    def select_context(self, candidates: Iterable[dict], *, limit: int = 16) -> dict:
        limit = max(1, min(int(limit), 32))
        if self.attention_salience is not None:
            result = self.attention_salience.select_relevant(candidates, limit=limit)
            return {**result, "bounded": True, "source": "B14 AttentionSalience"}
        selected = []
        iterator = iter(candidates)
        truncated = False
        for _ in range(limit + 1):
            try: item = next(iterator)
            except StopIteration: break
            if len(selected) < limit: selected.append(deepcopy(item))
            else: truncated = True
        return {"selected": selected, "bounded": True, "truncated": truncated, "source": "B20 bounded fallback"}

    @staticmethod
    def _source_list(sources: Iterable[Any] | None) -> list[str]:
        out = []
        for source in sources or ():
            if isinstance(source, dict):
                value = _clean(source.get("source") or source.get("reference") or source.get("id"))
            else:
                value = _clean(source)
            if value and value not in out: out.append(value)
            if len(out) >= 32: break
        return out

    def assess(self, query: str, *, local_answer: bool = False, confidence: float | None = None,
               current_information: bool = False, sources: Iterable[Any] | None = None,
               contradictions: Iterable[Any] | None = None, belief: str = "", inference: str = "",
               candidates: Iterable[dict] | None = None, missing_context: Iterable[str] | None = None,
               network_allowed: bool = False) -> dict:
        query = _clean(query)
        if not query: raise ValueError("consulta metacognitiva vazia")
        source_list = self._source_list(sources)
        contradiction_list = deepcopy(list(contradictions or ()))[:32]
        missing = tuple(_clean(x) for x in (missing_context or ()) if _clean(x))[:16]
        selected = self.select_context(candidates or (), limit=16)
        base = self.base_engine.assess(
            query, local_answer=bool(local_answer), confidence=confidence,
            current_information=bool(current_information),
        )
        conf = _clamp(base.get("confidence", 0.0))
        known = bool(local_answer and source_list and conf >= 0.5 and not contradiction_list)
        unknown = not bool(local_answer) or conf < 0.35
        disputed = bool(contradiction_list)
        needs_research = bool(current_information or unknown or (conf < 0.65 and not missing) or disputed)
        needs_question = bool(missing)
        needs_review = bool(disputed or (local_answer and conf < 0.65) or (bool(belief) and not source_list))
        if needs_question:
            recommended = "ask"
        elif needs_review:
            recommended = "review"
        elif needs_research:
            recommended = "research_if_network_allowed" if network_allowed else "research_when_authorized"
        elif known:
            recommended = "answer_with_sources_and_confidence"
        else:
            recommended = base.get("recommended_action", "verify")
        return {
            "query": query,
            "knows": known,
            "does_not_know": unknown,
            "belief": _clean(belief) or None,
            "belief_is_fact": False,
            "inference": _clean(inference) or None,
            "inference_is_fact": False,
            "confidence": conf,
            "sources": source_list,
            "has_source": bool(source_list),
            "contradictions": contradiction_list,
            "has_contradictions": disputed,
            "missing_context": missing,
            "needs_research": needs_research,
            "needs_question": needs_question,
            "needs_review": needs_review,
            "network_allowed": bool(network_allowed),
            "research_need_grants_network_permission": False,
            "recommended_action": recommended,
            "selected_context": selected.get("selected", []),
            "context_bounded": True,
            "base_assessment": deepcopy(base),
            "operational_authorization": False,
        }

    def verify_readiness(self, claim: str, evidence: Iterable[dict] | None = None) -> dict:
        claim = _clean(claim)
        if not claim: raise ValueError("claim vazio")
        if self.verifier is None:
            return {"claim": claim, "verdict": "verifier_unavailable", "ready": False, "confidence": 0.0}
        result = self.verifier.verify(claim, list(evidence or ())[:64])
        return {**result, "ready": result.get("verdict") == "supported" and float(result.get("confidence", 0.0)) >= 0.6,
                "canonical_promotion_performed": False}

    def monitor_prediction(self, predicted: float, observed: float, *, context: str = "") -> dict:
        if self.reasoning_simulation is None:
            raise RuntimeError("B18 ReasoningSimulation indisponível")
        error = self.reasoning_simulation.prediction_error(predicted, observed, context=context)
        return {"prediction_error": error, "review_recommended": error["relative_error"] >= 0.2,
                "history_rewritten": False}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = _norm(domain) if domain else None
        if key and key not in _DOMAINS: raise KeyError(domain)
        branches = [b for b in METACOGNITIVE_BRANCHES if key is None or b.domain == key]
        root = self.graph.add_entity("metacognition_taxonomy", "METACOGNIÇÃO", node_id=self.TAXONOMY_ROOT_ID,
                                     data={"block":"B20", "operational_authorization":False})
        for source_id, label in (("MEMORY-TAX-ROOT","B13 Memory"),("ATTENTION-TAX-ROOT","B14 Attention"),
                                 ("REASONING-SIMULATION-TAX-ROOT","B18 Reasoning"),("PLANNING-DECISION-TAX-ROOT","B19 Planning")):
            self.graph.add_entity("metacognitive_source", label, node_id=source_id, data={"block":"B20"})
            self.graph.relate(root, source_id, "integrates", metadata={"block":"B20"})
        for branch in branches:
            dom_id=f"META-DOM-{branch.domain.upper()}"; br_id=f"META-BR-{branch.key.upper()}"
            self.graph.add_entity("metacognition_domain", DOMAIN_LABELS[branch.domain], node_id=dom_id, data={"block":"B20"})
            self.graph.add_entity("metacognition_branch", branch.label, node_id=br_id, data={"block":"B20"})
            self.graph.relate(root, dom_id, "has_part", metadata={"block":"B20"})
            self.graph.relate(dom_id, br_id, "has_part", metadata={"block":"B20"})
        return {"domain": key, "branches_materialized": len(branches), "knowledge_graph":"shared",
                "parallel_metacognition_engine_created": False}

    def stats(self) -> dict:
        return {"status":"experimental-integrated", "namespace":self.knowledge.store.get_namespace("B20"),
                "catalog":self.catalog.stats(), "policy":deepcopy(METACOGNITION_POLICY),
                "reuses":"CognitiveSuite.metacognition"}

    def handle(self, text: str) -> str | None:
        raw=_clean(text); low=raw.casefold()
        if not raw: return None
        if low in {"status bloco 20","status metacognicao","status metacognição","metacognicao","metacognição"}:
            c=self.catalog.stats()
            return f"⭐ BLOCO 20 — METACOGNIÇÃO: {c['addressable_contents']} representações | contexto bounded | saber ≠ acreditar ≠ inferir."
        item=self.catalog.get_variant(raw.upper())
        if item: return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
