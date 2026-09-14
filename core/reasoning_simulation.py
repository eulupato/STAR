"""BLOCO 18 — raciocínio, causalidade e simulação.

Coordena as capacidades de raciocínio/simulação/verificação já existentes no MIND.
Não cria outro ReasoningEngine, outro SimulationLab ou outro ledger de fatos.
Conclusões derivadas permanecem inferências/hipóteses e não alteram fatos originais.

INFERÊNCIA != FATO. SIMULAÇÃO != OBSERVAÇÃO. PREVISÃO != CERTEZA.
CONTRAFACTUAL != HISTÓRIA REAL.
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
class ReasoningBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


_BRANCHES = {
    "causality": (
        ("cause_effect", "Causa e efeito", "causa;efeito;mecanismo;temporalidade;dependência"),
        ("confounders", "Confundidores", "confundidor;causa comum;viés;controle;alternativas"),
        ("causal_chain", "Cadeia causal", "causa intermediária;mediação;sequência;dependência;propagação"),
        ("causal_strength", "Força causal", "evidência;efeito;dose-resposta;consistência;incerteza"),
        ("correlation_limits", "Limites da correlação", "correlação não implica causalidade;coincidência;seleção;viés"),
    ),
    "analogy": (
        ("structural_analogy", "Analogia estrutural", "estrutura;mapeamento;correspondência;relação;limites"),
        ("functional_analogy", "Analogia funcional", "função;papel;resultado;mecanismo;limites"),
        ("cross_domain_analogy", "Analogia entre domínios", "transferência;domínios;semelhança;diferença;risco"),
        ("analogy_limits", "Limites da analogia", "diferenças;quebra de correspondência;exceções;escopo"),
        ("analogy_hypothesis", "Hipótese por analogia", "hipótese;evidência;teste;incerteza;revisão"),
    ),
    "abstraction": (
        ("feature_extraction", "Extração de características", "característica;relevância;representação;ruído;contexto"),
        ("concept_abstraction", "Abstração conceitual", "conceito;categoria;essência operacional;variação;limite"),
        ("hierarchy_abstraction", "Abstração hierárquica", "nível;parte;todo;categoria;subcategoria"),
        ("pattern_abstraction", "Abstração de padrões", "padrão;regularidade;repetição;estrutura;incerteza"),
        ("abstraction_loss", "Perda por abstração", "detalhe perdido;exceção;contexto;oversimplificação;limites"),
    ),
    "generalization": (
        ("induction", "Indução", "observações;padrão;amostra;escopo;incerteza"),
        ("scope", "Escopo da generalização", "população;domínio;tempo;condição;limite"),
        ("transfer", "Transferência", "contexto novo;semelhança;adaptação;teste;risco"),
        ("overgeneralization", "Sobregeneralização", "amostra pequena;viés;extrapolação;limite;correção"),
        ("generalization_test", "Teste de generalização", "holdout;novo caso;replicação;contraexemplo;revisão"),
    ),
    "exceptions": (
        ("exception_detection", "Detecção de exceções", "exceção;outlier;condição;regra;contexto"),
        ("counterexample", "Contraexemplo", "refutação;limite;caso;hipótese;revisão"),
        ("edge_cases", "Casos extremos", "fronteira;limite;condição rara;falha;robustez"),
        ("rule_refinement", "Refinamento de regra", "regra;condição;exceção;escopo;versão"),
        ("exception_preservation", "Preservação de exceções", "não apagar;proveniência;relação;memória;auditoria"),
    ),
    "counterfactuals": (
        ("minimal_change", "Mudança contrafactual mínima", "intervenção;uma variável;baseline;consequência;comparação"),
        ("alternative_world", "Mundo alternativo", "hipótese;premissa alterada;cenário;resultado;separação"),
        ("counterfactual_causality", "Causalidade contrafactual", "se não;necessidade;suficiência;causa;limites"),
        ("what_if", "Raciocínio e se / contrafactuais", "contrafactuais;e se;hipótese;alternativa;consequência;incerteza"),
        ("counterfactual_limits", "Limites contrafactuais", "não observado;modelo;assunção;incerteza;história preservada"),
    ),
    "simulation": (
        ("state_simulation", "Simulação de estado", "estado inicial;transição;parâmetro;resultado;assunção"),
        ("model_simulation", "Simulação por modelo", "modelo;equação;parâmetro;resultado;validade"),
        ("scenario_simulation", "Simulação de cenário", "cenário;hipótese;evento;consequência;comparação"),
        ("sensitivity", "Análise de sensibilidade", "parâmetro;variação;robustez;dependência;incerteza"),
        ("simulation_limits", "Limites da simulação", "modelo ≠ realidade;assunção;erro;validação;escopo"),
    ),
    "prediction": (
        ("prediction", "Previsão", "previsão;base;evidência;horizonte;confiança"),
        ("prediction_interval", "Intervalo de previsão", "faixa;incerteza;erro;probabilidade;calibração"),
        ("prediction_error", "Prediction error", "previsto;observado;erro;feedback;atualização"),
        ("forecast_revision", "Revisão de previsão", "evidência nova;erro;recalibração;histórico;versão"),
        ("prediction_limits", "Limites da previsão", "incerteza;evento raro;mudança de regime;modelo;escopo"),
    ),
    "risk_consequences": (
        ("risk", "Risco", "probabilidade;impacto;incerteza;exposição;mitigação"),
        ("consequences", "Consequências", "efeito direto;efeito indireto;segunda ordem;tempo;stakeholder"),
        ("tradeoffs", "Trade-offs", "benefício;custo;risco;alternativa;prioridade"),
        ("failure_modes", "Modos de falha", "falha;causa;efeito;detecção;mitigação"),
        ("risk_uncertainty", "Incerteza de risco", "desconhecido;cauda;intervalo;cenário;prudência"),
    ),
    "reversibility_integration": (
        ("reversibility", "Reversibilidade", "rollback;recuperação;custo de reversão;irreversível;teste"),
        ("decision_reversibility", "Reversibilidade de decisão", "opção;commit;adiamento;experimento;rollback"),
        ("cross_block_reasoning", "Raciocínio entre blocos", "mundo;humano;social;self;memória;atenção"),
        ("evidence_integration", "Integração de evidências", "fonte;conflito;peso;proveniência;incerteza"),
        ("derived_conclusion", "Conclusão derivada", "premissas;inferência;hipótese;verificação;fatos preservados"),
    ),
}

REASONING_DOMAINS = tuple(_BRANCHES)
DOMAIN_LABELS = {
    "causality": "Causalidade", "analogy": "Analogia", "abstraction": "Abstração",
    "generalization": "Generalização", "exceptions": "Exceções", "counterfactuals": "Contrafactuais",
    "simulation": "Simulação", "prediction": "Previsão e prediction error",
    "risk_consequences": "Risco e consequências", "reversibility_integration": "Reversibilidade e integração",
}
REASONING_BRANCHES = tuple(
    ReasoningBranch(domain, key, label, _subs(subtopics))
    for domain, branches in _BRANCHES.items()
    for key, label, subtopics in branches
)

REASONING_LENSES = (
    ("mechanism", "mecanismo", "explicitar mecanismo ou transformação proposta"),
    ("evidence", "evidência", "separar observação, fato canônico, memória e inferência"),
    ("assumptions", "assunções", "declarar premissas e condições de validade"),
    ("alternatives", "alternativas", "comparar hipóteses e explicações concorrentes"),
    ("exceptions", "exceções", "buscar contraexemplos e condições de quebra"),
    ("uncertainty", "incerteza", "quantificar ou declarar incerteza de dados/modelo"),
    ("simulation", "simulação", "separar mundo simulado do mundo observado"),
    ("prediction", "previsão", "definir resultado esperado, horizonte e erro possível"),
    ("risk", "risco", "avaliar consequências e reversibilidade"),
    ("verification", "verificação", "produzir checks auditáveis sem promover inferência a fato"),
)

CONTEXT_AXIS = ("physical", "scientific", "human", "social", "technical", "project", "conversation", "historical", "future", "mixed")
EVIDENCE_AXIS = ("canonical_fact", "observation", "memory", "measurement", "source_report", "model_output", "simulation_output", "inference", "conflicting", "insufficient")
SCALE_AXIS = ("component", "object", "person", "group", "system", "environment", "project", "organization", "society", "cross_domain")
UNCERTAINTY_AXIS = ("unknown", "very_high", "high", "moderate_high", "moderate", "limited", "low", "very_low", "calibrated", "conflicting")
TIME_AXIS = ("instant", "minutes", "hours", "day", "week", "month", "year", "long_term", "historical", "counterfactual")
SOURCE_AXIS = ("B03", "B04", "B05", "B06", "B07", "B09", "B13", "B15", "B16", "B17")
MODE_AXIS = ("primary", "alternative")
VARIANT_AXES = (
    ("context", CONTEXT_AXIS), ("evidence_mode", EVIDENCE_AXIS), ("scale", SCALE_AXIS),
    ("uncertainty", UNCERTAINTY_AXIS), ("time_horizon", TIME_AXIS), ("source_block", SOURCE_AXIS),
    ("reasoning_mode", MODE_AXIS),
)
CANONICAL_NODES = len(REASONING_BRANCHES) * len(REASONING_LENSES)
VARIANTS_PER_NODE = prod(len(v) for _, v in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE
if len(REASONING_DOMAINS) != 10 or len(REASONING_BRANCHES) != 50 or len(REASONING_LENSES) != 10:
    raise RuntimeError("B18 requer 10 domínios, 50 ramos e 10 lentes")
if CANONICAL_NODES != 500 or VARIANTS_PER_NODE != 2_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B18 inválida")

REASONING_POLICY = {
    "inference_is_fact": False,
    "simulation_is_observation": False,
    "prediction_is_certainty": False,
    "counterfactual_is_history": False,
    "derived_conclusion_mutates_original_facts": False,
    "canonical_promotion_without_b2_gate": False,
    "bounded_context_selection": True,
    "operational_authorization": False,
    "rule": "INFERÊNCIA ≠ FATO; SIMULAÇÃO ≠ OBSERVAÇÃO; PREVISÃO ≠ CERTEZA; CONTRAFACTUAL ≠ HISTÓRIA",
}


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    value = int(index); out = {}
    for name, values in reversed(VARIANT_AXES):
        value, offset = divmod(value, len(values)); out[name] = values[offset]
    return {name: out[name] for name, _ in VARIANT_AXES}


class ReasoningCatalog:
    NAMESPACE = "B18"
    def stats(self) -> dict:
        return {"namespace": "B18", "domains": 10, "branches": 50, "lenses_per_branch": 10,
                "canonical_nodes": CANONICAL_NODES, "variants_per_node": VARIANTS_PER_NODE,
                "addressable_contents": ADDRESSABLE_CONTENTS, "materialization": "on-demand",
                "prepopulated_conclusions": 0,
                "truthfulness_note": "1B are addressable reasoning contexts/representations, not 1B independently proven conclusions"}
    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < CANONICAL_NODES: raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE: raise IndexError(variant_index)
        n = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"RSN-B18-{n:010d}"
    def get_variant(self, identifier: str) -> dict | None:
        m = re.fullmatch(r"RSN-B18-(\d{10})", _clean(identifier).upper())
        if not m: return None
        n = int(m.group(1))
        if not 1 <= n <= ADDRESSABLE_CONTENTS: return None
        node_i, variant_i = divmod(n - 1, VARIANTS_PER_NODE)
        branch_i, lens_i = divmod(node_i, 10)
        branch = REASONING_BRANCHES[branch_i]
        lens_key, lens_label, instruction = REASONING_LENSES[lens_i]
        axes = _decode_axes(variant_i)
        return {"id": f"RSN-B18-{n:010d}", "namespace": "B18", "domain": branch.domain,
                "domain_label": DOMAIN_LABELS[branch.domain], "branch": branch.key, "branch_label": branch.label,
                "subtopics": branch.subtopics, "lens": lens_key, "lens_label": lens_label, **axes,
                "prompt": f"{branch.label}/{lens_label}: {instruction}; contexto={axes['context']}; evidência={axes['evidence_mode']}; escala={axes['scale']}; incerteza={axes['uncertainty']}; preservar fatos originais."}


class ReasoningSimulation:
    NAMESPACE = "B18"
    TAXONOMY_ROOT_ID = "REASONING-SIMULATION-TAX-ROOT"

    def __init__(self, knowledge: UniversalKnowledgeArchitecture, *, reasoning, simulation, verifier,
                 memory_continuity=None, attention_salience=None, internal_models=None,
                 social_cognition=None, affective_personality=None):
        self.knowledge = knowledge; self.graph = knowledge.graph
        self.reasoning = reasoning; self.simulation = simulation; self.verifier = verifier
        self.memory_continuity = memory_continuity; self.attention_salience = attention_salience
        self.internal_models = internal_models; self.social_cognition = social_cognition
        self.affective_personality = affective_personality; self.catalog = ReasoningCatalog()
        self.knowledge.register_namespace(self.NAMESPACE, "BLOCO 18 — RACIOCÍNIO, CAUSALIDADE E SIMULAÇÃO",
            logical_capacity=ADDRESSABLE_CONTENTS, source="core/reasoning_simulation.py",
            metadata={"materialization":"on-demand", "reuses_existing_reasoning_engine":True,
                      "reuses_existing_simulation_lab":True, "reuses_existing_verifier":True,
                      "shared_knowledge_graph":True, "original_facts_mutated":False})

    def select_context(self, candidates: Iterable[dict], *, limit: int = 16) -> dict:
        if self.attention_salience is None:
            selected = list(candidates)[:max(1, min(int(limit), 32))]
            return {"selected": selected, "bounded": True, "source": "local bounded fallback", "operational_authorization": False}
        result = self.attention_salience.select_relevant(candidates, limit=limit)
        return {**result, "bounded": True, "source": "B14 AttentionSalience"}

    def analyze(self, problem: str, *, candidates: Iterable[dict] | None = None, limit: int = 16) -> dict:
        artifact = self.reasoning.analyze(problem)
        selected = self.select_context(candidates or (), limit=limit)
        return {"artifact": artifact, "selected_context": selected["selected"], "bounded": True,
                "epistemic_kind": "inference", "canonical_fact": False,
                "original_facts_mutated": False, "operational_authorization": False}

    def causal_analysis(self, cause: str, effect: str, *, evidence=None, alternatives=None, confounders=None) -> dict:
        cause, effect = _clean(cause), _clean(effect)
        if not cause or not effect: raise ValueError("causa e efeito são obrigatórios")
        evidence_copy = deepcopy(list(evidence or ()))[:64]
        alternatives_copy = tuple(_clean(x) for x in (alternatives or ()) if _clean(x))[:32]
        confounders_copy = tuple(_clean(x) for x in (confounders or ()) if _clean(x))[:32]
        return {"cause": cause, "effect": effect, "evidence": evidence_copy,
                "alternative_causes": alternatives_copy, "confounders": confounders_copy,
                "causal_claim_proven": False, "epistemic_kind": "hypothesis",
                "verification_needed": True, "original_evidence_mutated": False}

    def analogy(self, source: str, target: str, *, mappings=None, limits=None) -> dict:
        if not _clean(source) or not _clean(target): raise ValueError("fonte e alvo da analogia são obrigatórios")
        return {"source": _clean(source), "target": _clean(target), "mappings": deepcopy(list(mappings or ()))[:64],
                "limits": tuple(_clean(x) for x in (limits or ()) if _clean(x))[:32],
                "epistemic_kind": "inference", "analogy_proves_equivalence": False}

    def generalize(self, observations: Iterable[Any], *, scope: str, exceptions=None) -> dict:
        obs = deepcopy(list(observations))[:128]
        if not obs: raise ValueError("generalização requer observações")
        return {"observations": obs, "scope": _clean(scope),
                "exceptions": deepcopy(list(exceptions or ()))[:64], "epistemic_kind": "inference",
                "universal_claim": False, "requires_new_cases_for_verification": True}

    def counterfactual(self, base_facts: Any, *, changed_assumption: Any, projected_consequences=None) -> dict:
        baseline = deepcopy(base_facts)
        hypothetical = {"base_reference": deepcopy(base_facts), "changed_assumption": deepcopy(changed_assumption),
                        "projected_consequences": deepcopy(list(projected_consequences or ()))[:64]}
        return {"baseline": baseline, "counterfactual": hypothetical, "epistemic_kind": "simulation",
                "counterfactual_is_history": False, "original_facts_mutated": False}

    def simulate_state(self, initial_state: dict, changes: dict, *, assumptions=None) -> dict:
        before = deepcopy(initial_state); after = deepcopy(initial_state)
        for key, value in dict(changes or {}).items(): after[key] = deepcopy(value)
        return {"initial_state": before, "simulated_state": after,
                "changes": deepcopy(dict(changes or {})), "assumptions": deepcopy(list(assumptions or ()))[:64],
                "epistemic_kind": "simulation", "simulation_is_observation": False,
                "original_state_mutated": False}

    def run_numeric_simulation(self, kind: str, **parameters) -> dict:
        kind = _norm(kind)
        allowed = {"projectile": self.simulation.projectile, "exponential": self.simulation.exponential,
                   "monte_carlo_pi": self.simulation.monte_carlo_pi}
        if kind not in allowed: raise ValueError("simulação numérica B18 não suportada")
        return {"kind": kind, "parameters": deepcopy(parameters), "result": allowed[kind](**parameters),
                "epistemic_kind": "simulation", "simulation_is_observation": False}

    def prediction(self, statement: str, *, basis=None, confidence: float = 0.5, horizon: str = "") -> dict:
        statement = _clean(statement)
        if not statement: raise ValueError("previsão vazia")
        result = {"prediction": statement, "basis": deepcopy(list(basis or ()))[:64],
                  "confidence": _clamp(confidence), "horizon": _clean(horizon),
                  "epistemic_kind": "prediction", "certainty": False, "observed": False}
        if self.memory_continuity is not None:
            wm = self.memory_continuity.working.add(statement, key="b18:last_prediction", importance=0.7,
                context={"horizon": result["horizon"], "confidence": result["confidence"]}, source="B18 prediction",
                metadata={"block":"B18", "epistemic_kind":"prediction"})
            result["working_memory_id"] = wm["working_id"]
        return result

    def prediction_error(self, predicted: float, observed: float, *, context: str = "") -> dict:
        p, o = float(predicted), float(observed); signed = o - p
        denom = max(abs(o), abs(p), 1e-12)
        return {"predicted": p, "observed": o, "signed_error": signed, "absolute_error": abs(signed),
                "relative_error": abs(signed) / denom, "context": _clean(context),
                "prediction_rewritten_as_fact": False, "observed_value_preserved": True}

    def assess_risk(self, consequences: Iterable[dict]) -> dict:
        items = []
        for raw in list(consequences or ())[:64]:
            if not isinstance(raw, dict): continue
            probability = _clamp(raw.get("probability", 0.5)); impact = _clamp(raw.get("impact", 0.5))
            reversibility = _clamp(raw.get("reversibility", 0.5)); score = probability * impact * (1.0 - 0.5 * reversibility)
            items.append({"consequence": _clean(raw.get("consequence")), "probability": probability,
                          "impact": impact, "reversibility": reversibility, "risk_score": score})
        return {"items": items, "max_risk": max((x["risk_score"] for x in items), default=0.0),
                "risk_is_permission": False, "operational_authorization": False}

    def derive_conclusion(self, premises: Iterable[Any], conclusion: str, *, method: str = "inference", confidence: float = 0.5) -> dict:
        premise_copy = deepcopy(list(premises))[:128]; conclusion = _clean(conclusion)
        if not conclusion: raise ValueError("conclusão vazia")
        result = {"premises": premise_copy, "conclusion": conclusion, "method": _norm(method) or "inference",
                  "confidence": _clamp(confidence), "epistemic_kind": "inference", "canonical_fact": False,
                  "original_facts_mutated": False, "requires_verification": True, "operational_authorization": False}
        if self.memory_continuity is not None:
            wm = self.memory_continuity.working.add(conclusion, source="B18 derived conclusion", importance=_clamp(confidence),
                context={"method": result["method"]}, metadata={"block":"B18", "epistemic_kind":"inference", "canonical_fact":False})
            result["working_memory_id"] = wm["working_id"]
        return result

    def verify_claim(self, claim: str, evidence=None) -> dict:
        return self.verifier.verify(claim, list(evidence or ()))

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = _norm(domain) if domain else None
        if key and key not in REASONING_DOMAINS: raise KeyError(domain)
        branches = [b for b in REASONING_BRANCHES if key is None or b.domain == key]
        root = self.graph.add_entity("reasoning_simulation_taxonomy", "RACIOCÍNIO, CAUSALIDADE E SIMULAÇÃO",
            node_id=self.TAXONOMY_ROOT_ID, data={"block":"B18", "fact_authority":False})
        for source_id, label in (("MEMORY-TAX-ROOT","B13 Memory"),("ATTENTION-TAX-ROOT","B14 Attention"),
                                 ("INTERNAL-MODELS-TAX-ROOT","B15 Models"),("SOCIAL-COGNITION-TAX-ROOT","B16 Social"),
                                 ("AFFECTIVE-PERSONALITY-TAX-ROOT","B17 Personality")):
            self.graph.add_entity("reasoning_source", label, node_id=source_id, data={"block":"B18"})
            self.graph.relate(root, source_id, "integrates", metadata={"block":"B18"})
        for branch in branches:
            domain_id=f"RSN-DOM-{branch.domain.upper()}"; branch_id=f"RSN-BR-{branch.key.upper()}"
            self.graph.add_entity("reasoning_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block":"B18"})
            self.graph.add_entity("reasoning_branch", branch.label, node_id=branch_id, data={"block":"B18"})
            self.graph.relate(root, domain_id, "has_part", metadata={"block":"B18"})
            self.graph.relate(domain_id, branch_id, "has_part", metadata={"block":"B18"})
        return {"domain":key, "branches_materialized":len(branches), "knowledge_graph":"shared",
                "parallel_reasoning_engine_created":False, "parallel_simulation_lab_created":False}

    def stats(self) -> dict:
        return {"status":"experimental-integrated", "namespace":self.knowledge.store.get_namespace("B18"),
                "catalog":self.catalog.stats(), "policy":deepcopy(REASONING_POLICY),
                "reuses":{"reasoning":"CognitiveSuite.reasoning", "simulation":"CognitiveSuite.simulation", "verifier":"CognitiveSuite.verifier"}}

    def handle(self, text: str) -> str | None:
        raw=_clean(text); low=raw.casefold()
        if not raw: return None
        if low in {"status bloco 18","status raciocinio e simulacao","status raciocínio e simulação","raciocinio causal","raciocínio causal"}:
            s=self.stats(); c=s["catalog"]
            return f"⭐ BLOCO 18 — RACIOCÍNIO/SIMULAÇÃO: {c['addressable_contents']} representações | {c['branches']} ramos × {c['lenses_per_branch']} lentes | inferência ≠ fato; simulação ≠ observação."
        item=self.catalog.get_variant(raw.upper())
        if item: return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
