"""BLOCO 19 — planejamento e tomada de decisão.

Evolui o Planner já existente sem criar um Planner paralelo. Coordena:
OBJETIVO -> ESTADO ATUAL -> ESTADO DESEJADO -> OBSTÁCULOS -> OPÇÕES ->
SIMULAÇÃO -> RISCO -> PLANO -> DECISÃO -> VERIFICAÇÃO.

Planejar não executa ações. Decisão cognitiva não concede autorização operacional.
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
class PlanningBranch:
    stage: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


STAGES = (
    "goal",
    "current_state",
    "desired_state",
    "obstacles",
    "options",
    "simulation",
    "risk",
    "plan",
    "decision",
    "verification",
)

STAGE_LABELS = {
    "goal": "OBJETIVO",
    "current_state": "ESTADO ATUAL",
    "desired_state": "ESTADO DESEJADO",
    "obstacles": "OBSTÁCULOS",
    "options": "OPÇÕES",
    "simulation": "SIMULAÇÃO",
    "risk": "RISCO",
    "plan": "PLANO",
    "decision": "DECISÃO",
    "verification": "VERIFICAÇÃO",
}

_STAGE_BRANCHES = {
    "goal": (
        ("goal_definition", "Definição do objetivo", "objetivo;escopo;resultado;critério;prioridade"),
        ("goal_constraints", "Restrições do objetivo", "restrições;limites;regras;dependências;recursos"),
        ("goal_success", "Critérios de sucesso", "sucesso;medição;aceitação;qualidade;resultado"),
        ("goal_priority", "Prioridade do objetivo", "prioridade;urgência;importância;dependência;ordem"),
        ("goal_alignment", "Alinhamento do objetivo", "valores;regras;projeto;usuário;segurança"),
    ),
    "current_state": (
        ("state_snapshot", "Snapshot do estado atual", "estado atual;situação;recursos;restrições;contexto"),
        ("knowns_unknowns", "Conhecidos e desconhecidos", "fatos;desconhecidos;hipóteses;incerteza;fonte"),
        ("resource_state", "Estado dos recursos", "recursos;capacidade;disponibilidade;ferramentas;tempo"),
        ("dependency_state", "Estado das dependências", "dependências;pré-condições;bloqueios;interfaces;ordem"),
        ("state_freshness", "Atualidade do estado", "recência;validade;telemetria;observação;desatualização"),
    ),
    "desired_state": (
        ("target_state", "Estado-alvo", "estado desejado;resultado;propriedades;limites;qualidade"),
        ("minimum_viable_target", "Alvo mínimo viável", "mínimo;essencial;critério;trade-off;escopo"),
        ("ideal_target", "Estado ideal", "ideal;ótimo;qualidade;benefício;limites"),
        ("acceptance_conditions", "Condições de aceitação", "aceitação;teste;medição;critério;verificação"),
        ("target_consistency", "Consistência do alvo", "contradição;restrição;compatibilidade;prioridade;revisão"),
    ),
    "obstacles": (
        ("obstacle_identification", "Identificação de obstáculos", "obstáculo;bloqueio;restrição;dependência;risco"),
        ("root_obstacle", "Causa-raiz de obstáculo", "causa raiz;sintoma;dependência;falha;diagnóstico"),
        ("constraint_conflicts", "Conflitos de restrição", "conflito;regra;prioridade;trade-off;incompatibilidade"),
        ("uncertainty_obstacles", "Obstáculos por incerteza", "incerteza;dados ausentes;hipótese;verificação;lacuna"),
        ("mitigation_paths", "Caminhos de mitigação", "mitigação;alternativa;contorno;redução;sequência"),
    ),
    "options": (
        ("option_generation", "Geração de opções", "opção;alternativa;estratégia;caminho;variante"),
        ("option_feasibility", "Viabilidade de opções", "viabilidade;capacidade;recurso;tempo;restrição"),
        ("option_tradeoffs", "Trade-offs entre opções", "benefício;custo;risco;tempo;qualidade"),
        ("option_reversibility", "Reversibilidade das opções", "rollback;reversibilidade;compromisso;teste;recuperação"),
        ("option_diversity", "Diversidade de alternativas", "alternativa independente;viés;exploração;baseline;comparação"),
    ),
    "simulation": (
        ("simulate_option", "Simulação de opção", "simulação;estado inicial;mudança;resultado;assunção"),
        ("scenario_comparison", "Comparação de cenários", "cenário;alternativa;resultado;diferença;trade-off"),
        ("counterfactual_plan", "Contrafactual de planejamento", "contrafactual;e se;baseline;mudança;consequência"),
        ("sensitivity_plan", "Sensibilidade do plano", "sensibilidade;parâmetro;robustez;dependência;variação"),
        ("simulation_limits", "Limites da simulação", "modelo ≠ realidade;assunção;erro;incerteza;escopo"),
    ),
    "risk": (
        ("risk_identification", "Identificação de risco", "risco;probabilidade;impacto;exposição;incerteza"),
        ("failure_modes", "Modos de falha", "falha;causa;efeito;detecção;mitigação"),
        ("risk_reversibility", "Risco e reversibilidade", "rollback;custo de reversão;irreversível;recuperação;teste"),
        ("risk_tolerance", "Tolerância a risco", "limite;prudência;impacto;contexto;segurança"),
        ("risk_mitigation", "Mitigação de risco", "mitigar;prevenir;reduzir;monitorar;fallback"),
    ),
    "plan": (
        ("plan_decomposition", "Decomposição do plano", "passos;subtarefas;ordem;dependência;resultado"),
        ("plan_dependencies", "Dependências do plano", "dependência;pré-condição;ordem;paralelismo;bloqueio"),
        ("plan_resources", "Recursos do plano", "recurso;capacidade;ferramenta;tempo;disponibilidade"),
        ("plan_checkpoints", "Checkpoints do plano", "checkpoint;validação;critério;rollback;observação"),
        ("plan_adaptation", "Adaptação do plano", "replanejamento;feedback;mudança;erro;estado novo"),
    ),
    "decision": (
        ("decision_criteria", "Critérios de decisão", "critério;peso;prioridade;risco;benefício"),
        ("option_ranking", "Ranking de opções", "ranking;comparação;score;trade-off;incerteza"),
        ("decision_rationale", "Racional auditável", "justificativa;critério;evidência;limite;alternativa"),
        ("decision_reversibility", "Reversibilidade da decisão", "reversível;commit;rollback;adiamento;experimento"),
        ("decision_boundary", "Fronteira decisão/ação", "decisão ≠ execução;permissão;capacidade;segurança;autorização"),
    ),
    "verification": (
        ("plan_verification", "Verificação do plano", "verificação;passos;restrições;objetivo;consistência"),
        ("outcome_verification", "Verificação do resultado", "resultado;estado desejado;medição;diferença;erro"),
        ("assumption_verification", "Verificação de assunções", "assunção;evidência;teste;incerteza;revisão"),
        ("risk_verification", "Verificação de risco", "risco;mitigação;residual;monitoramento;limite"),
        ("decision_review", "Revisão da decisão", "feedback;prediction error;replanejamento;histórico;aprendizado"),
    ),
}

PLANNING_BRANCHES = tuple(
    PlanningBranch(stage, key, label, _subs(subtopics))
    for stage, branches in _STAGE_BRANCHES.items()
    for key, label, subtopics in branches
)

PLANNING_LENSES = (
    ("definition", "definição", "explicitar o elemento do planejamento"),
    ("evidence", "evidência", "separar fatos, memória, inferência e hipótese"),
    ("constraints", "restrições", "preservar regras, limites e dependências"),
    ("alternatives", "alternativas", "manter mais de uma opção quando aplicável"),
    ("simulation", "simulação", "comparar cenários sem confundir simulação com realidade"),
    ("risk", "risco", "avaliar impacto, probabilidade e reversibilidade"),
    ("priority", "prioridade", "ordenar sem converter prioridade em permissão"),
    ("uncertainty", "incerteza", "declarar lacunas e confiança"),
    ("verification", "verificação", "produzir checks auditáveis"),
    ("authorization", "autorização", "separar decisão cognitiva de execução operacional"),
)

CONTEXT_AXIS = ("personal", "project", "technical", "scientific", "social", "organizational", "physical", "digital", "emergency", "mixed")
CONSTRAINT_AXIS = ("none", "time", "cost", "resource", "safety", "policy", "permission", "dependency", "quality", "multiple")
UNCERTAINTY_AXIS = ("unknown", "very_high", "high", "moderate_high", "moderate", "limited", "low", "very_low", "calibrated", "conflicting")
TIME_AXIS = ("immediate", "minutes", "hours", "day", "week", "month", "quarter", "year", "long_term", "open")
RISK_AXIS = ("unknown", "minimal", "low", "moderate_low", "moderate", "moderate_high", "high", "very_high", "critical", "mixed")
SOURCE_AXIS = ("B03", "B13", "B14", "B15", "B16", "B17", "B18", "SELF", "USER", "TOOLS")
MODE_AXIS = ("primary", "alternative")

VARIANT_AXES = (
    ("context", CONTEXT_AXIS),
    ("constraint_mode", CONSTRAINT_AXIS),
    ("uncertainty", UNCERTAINTY_AXIS),
    ("time_horizon", TIME_AXIS),
    ("risk_level", RISK_AXIS),
    ("source_space", SOURCE_AXIS),
    ("planning_mode", MODE_AXIS),
)

CANONICAL_NODES = len(PLANNING_BRANCHES) * len(PLANNING_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(STAGES) != 10 or len(PLANNING_BRANCHES) != 50 or len(PLANNING_LENSES) != 10:
    raise RuntimeError("B19 requer 10 etapas, 50 ramos e 10 lentes")
if CANONICAL_NODES != 500 or VARIANTS_PER_NODE != 2_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B19 inválida")

PLANNING_POLICY = {
    "planning_is_execution": False,
    "decision_is_execution": False,
    "recommendation_is_permission": False,
    "priority_is_permission": False,
    "risk_is_permission": False,
    "simulation_is_reality": False,
    "automatic_execution": False,
    "execution_requires_permission": True,
    "execution_requires_capability": True,
    "execution_requires_safety": True,
    "bounded_context_selection": True,
    "operational_authorization": False,
    "rule": "PLANO ≠ AÇÃO; DECISÃO COGNITIVA ≠ EXECUÇÃO; RECOMENDAÇÃO ≠ PERMISSÃO",
}


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    value = int(index)
    out = {}
    for name, values in reversed(VARIANT_AXES):
        value, offset = divmod(value, len(values))
        out[name] = values[offset]
    return {name: out[name] for name, _ in VARIANT_AXES}


class PlanningCatalog:
    NAMESPACE = "B19"
    PREFIX = "PLAN-B19"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "stages": len(STAGES),
            "branches": len(PLANNING_BRANCHES),
            "lenses_per_branch": len(PLANNING_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "prepopulated_plans": 0,
            "truthfulness_note": "1B are addressable planning contexts/representations, not 1B precomputed plans or decisions",
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"PLAN-B19-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"PLAN-B19-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(PLANNING_LENSES))
        branch = PLANNING_BRANCHES[branch_index]
        lens_key, lens_label, instruction = PLANNING_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"PLAN-B19-{absolute:010d}",
            "namespace": self.NAMESPACE,
            "stage": branch.stage,
            "stage_label": STAGE_LABELS[branch.stage],
            "branch": branch.key,
            "branch_label": branch.label,
            "subtopics": branch.subtopics,
            "lens": lens_key,
            "lens_label": lens_label,
            **axes,
            "prompt": (
                f"{STAGE_LABELS[branch.stage]} / {branch.label} / {lens_label}: {instruction}. "
                f"Contexto={axes['context']}; restrição={axes['constraint_mode']}; incerteza={axes['uncertainty']}; "
                f"tempo={axes['time_horizon']}; risco={axes['risk_level']}; fonte={axes['source_space']}; "
                f"modo={axes['planning_mode']}. Preservar PLANO ≠ AÇÃO e DECISÃO ≠ EXECUÇÃO."
            ),
        }


class PlanningDecision:
    """Coordena o Planner oficial com simulação, risco, memória e boundary B01."""

    NAMESPACE = "B19"
    TAXONOMY_ROOT_ID = "PLANNING-DECISION-TAX-ROOT"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        planner,
        reasoning_simulation,
        memory_continuity=None,
        attention_salience=None,
        internal_models=None,
        operational_boundary=None,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.planner = planner
        self.reasoning_simulation = reasoning_simulation
        self.memory_continuity = memory_continuity
        self.attention_salience = attention_salience
        self.internal_models = internal_models
        self.operational_boundary = operational_boundary
        self.catalog = PlanningCatalog()
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 19 — PLANEJAMENTO E TOMADA DE DECISÃO",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/planning_decision.py",
            metadata={
                "materialization": "on-demand",
                "reuses_existing_planner": True,
                "uses_b18_simulation_risk": True,
                "uses_b14_bounded_context": True,
                "uses_b13_memory": True,
                "uses_b01_operational_boundary": True,
                "automatic_execution": False,
                "shared_knowledge_graph": True,
                "parallel_planner_created": False,
            },
        )

    @staticmethod
    def _normalize_option(raw: Any, index: int) -> dict:
        if isinstance(raw, str):
            return {
                "id": f"option_{index}",
                "label": _clean(raw),
                "changes": {},
                "consequences": [],
                "utility": 0.5,
                "reversibility": 0.5,
                "assumptions": [],
            }
        if not isinstance(raw, dict):
            raise ValueError("opção deve ser texto ou dict")
        label = _clean(raw.get("label") or raw.get("name") or raw.get("id") or f"Opção {index}")
        return {
            "id": _norm(raw.get("id") or label) or f"option_{index}",
            "label": label,
            "changes": deepcopy(dict(raw.get("changes") or {})),
            "consequences": deepcopy(list(raw.get("consequences") or ()))[:64],
            "utility": _clamp(raw.get("utility", 0.5)),
            "reversibility": _clamp(raw.get("reversibility", 0.5)),
            "assumptions": deepcopy(list(raw.get("assumptions") or ()))[:32],
        }

    def select_context(self, candidates: Iterable[dict], *, limit: int = 16) -> dict:
        if self.reasoning_simulation is not None:
            return self.reasoning_simulation.select_context(candidates, limit=limit)
        selected = list(candidates)[: max(1, min(int(limit), 32))]
        return {"selected": selected, "bounded": True, "source": "B19 local bounded fallback", "operational_authorization": False}

    @staticmethod
    def _desired_match(simulated_state: dict, desired_state: dict) -> float:
        desired = dict(desired_state or {})
        if not desired:
            return 0.5
        matched = sum(1 for key, value in desired.items() if simulated_state.get(key) == value)
        return matched / max(1, len(desired))

    def compare_options(self, current_state: dict, desired_state: dict, options: Iterable[Any]) -> list[dict]:
        normalized = [self._normalize_option(item, i) for i, item in enumerate(list(options or ())[:32], 1)]
        results = []
        for option in normalized:
            simulation = self.reasoning_simulation.simulate_state(
                deepcopy(current_state),
                deepcopy(option["changes"]),
                assumptions=deepcopy(option["assumptions"]),
            )
            risk = self.reasoning_simulation.assess_risk(deepcopy(option["consequences"]))
            desired_match = self._desired_match(simulation["simulated_state"], desired_state)
            score = (
                0.35 * option["utility"]
                + 0.25 * option["reversibility"]
                + 0.25 * (1.0 - _clamp(risk["max_risk"]))
                + 0.15 * desired_match
            )
            results.append({
                **deepcopy(option),
                "simulation": simulation,
                "risk": risk,
                "desired_state_match": desired_match,
                "comparison_score": score,
                "execution_performed": False,
                "operational_authorization": False,
            })
        results.sort(key=lambda item: (item["comparison_score"], item["reversibility"], item["utility"]), reverse=True)
        return results

    def evaluate_execution_boundary(
        self,
        intent: str,
        *,
        permission: bool = False,
        capability: bool = False,
        safety_ok: bool = False,
        authorization_source: str | None = None,
    ) -> dict:
        if self.operational_boundary is None:
            can_act = bool(permission and capability and safety_ok)
            missing = [name for name, ok in (("permission", permission), ("capability", capability), ("safety_ok", safety_ok)) if not ok]
            result = {"intent": _clean(intent), "can_act": can_act, "missing": missing, "authorization_source": authorization_source if permission else None}
        else:
            result = self.operational_boundary.evaluate(
                intent,
                permission=permission,
                capability=capability,
                safety_ok=safety_ok,
                authorization_source=authorization_source,
            )
        return {
            **result,
            "execution_performed": False,
            "planning_granted_permission": False,
            "note": "B19 never executes; even can_act=True only means a separate execution layer may evaluate the action",
        }

    def verify_plan(self, artifact: dict) -> dict:
        checks = {
            "goal_present": bool(_clean(artifact.get("goal"))),
            "current_state_present": isinstance(artifact.get("current_state"), dict),
            "desired_state_present": isinstance(artifact.get("desired_state"), dict),
            "options_compared": bool(artifact.get("options")),
            "simulation_present": all("simulation" in item for item in artifact.get("options", ())) if artifact.get("options") else False,
            "risk_present": all("risk" in item for item in artifact.get("options", ())) if artifact.get("options") else False,
            "plan_present": bool(artifact.get("plan", {}).get("steps")),
            "decision_present": bool(artifact.get("decision", {}).get("selected_option")),
            "execution_not_performed": artifact.get("execution_performed") is False,
        }
        return {
            "checks": checks,
            "passed": all(checks.values()),
            "failed": [name for name, ok in checks.items() if not ok],
            "operational_authorization": False,
        }

    def plan_decision(
        self,
        goal: str,
        *,
        current_state: dict | None = None,
        desired_state: dict | None = None,
        obstacles: Iterable[str] | None = None,
        options: Iterable[Any] | None = None,
        constraints: Iterable[str] | None = None,
        context_candidates: Iterable[dict] | None = None,
        context_limit: int = 16,
        permission: bool = False,
        capability: bool = False,
        safety_ok: bool = False,
        authorization_source: str | None = None,
    ) -> dict:
        goal = _clean(goal)
        if not goal:
            raise ValueError("objetivo vazio")

        current = deepcopy(dict(current_state or {}))
        desired = deepcopy(dict(desired_state or {}))
        obstacles_copy = tuple(_clean(item) for item in (obstacles or ()) if _clean(item))[:64]
        constraints_copy = tuple(_clean(item) for item in (constraints or ()) if _clean(item))[:64]
        context = self.select_context(context_candidates or (), limit=context_limit)

        raw_options = list(options or ())[:32]
        if not raw_options:
            raw_options = [{"label": "Manter estado e coletar mais contexto", "changes": {}, "utility": 0.25, "reversibility": 1.0,
                            "consequences": [{"consequence": "atraso", "probability": 0.5, "impact": 0.2, "reversibility": 1.0}]}]

        compared = self.compare_options(current, desired, raw_options)
        selected = deepcopy(compared[0])
        base_plan = self.planner.plan(goal, constraints=list(constraints_copy))

        decision = {
            "selected_option": selected["id"],
            "selected_label": selected["label"],
            "comparison_score": selected["comparison_score"],
            "risk": selected["risk"],
            "desired_state_match": selected["desired_state_match"],
            "rationale": "highest bounded comparison score from utility, reversibility, risk and desired-state match",
            "alternatives_preserved": [item["id"] for item in compared[1:]],
            "decision_is_execution": False,
        }

        boundary = self.evaluate_execution_boundary(
            f"execute plan: {goal}",
            permission=permission,
            capability=capability,
            safety_ok=safety_ok,
            authorization_source=authorization_source,
        )

        artifact = {
            "goal": goal,
            "current_state": current,
            "desired_state": desired,
            "obstacles": obstacles_copy,
            "constraints": constraints_copy,
            "selected_context": deepcopy(context.get("selected", [])),
            "context_bounded": bool(context.get("bounded", True)),
            "options": compared,
            "plan": deepcopy(base_plan),
            "decision": decision,
            "execution_boundary": boundary,
            "execution_performed": False,
            "operational_authorization": False,
            "pipeline": tuple(STAGE_LABELS[stage] for stage in STAGES),
        }
        artifact["verification"] = self.verify_plan(artifact)

        if self.memory_continuity is not None:
            item = self.memory_continuity.working.add(
                f"Plano B19: {goal} -> {decision['selected_label']}",
                key="b19:last_plan",
                importance=0.8,
                context={"goal": goal, "selected_option": decision["selected_option"], "verification_passed": artifact["verification"]["passed"]},
                source="B19 planning decision",
                metadata={"block": "B19", "epistemic_kind": "decision", "execution_performed": False},
            )
            artifact["working_memory_id"] = item["working_id"]

        return artifact

    def record_decision(self, artifact: dict, *, source: str, reference: str, importance: float = 0.7) -> dict:
        if self.memory_continuity is None:
            raise RuntimeError("B13 memory continuity indisponível")
        if not _clean(reference):
            raise ValueError("registro persistente de decisão exige referência auditável")
        goal = _clean(artifact.get("goal"))
        decision = deepcopy(artifact.get("decision") or {})
        if not goal or not decision.get("selected_option"):
            raise ValueError("artefato de decisão inválido")
        content = f"Decisão B19: {goal} -> {decision.get('selected_label')}"
        metadata = {
            "block": "B19",
            "source": _clean(source),
            "reference": _clean(reference),
            "goal": goal,
            "decision": decision,
            "verification": deepcopy(artifact.get("verification") or {}),
            "meaning": "registro auditável de decisão cognitiva; não prova execução",
            "execution_performed": False,
            "operational_authorization": False,
            "canonical_knowledge": False,
        }
        memory_id = self.memory_continuity.memory.remember(
            "decision",
            content,
            key=f"b19:decision:{_norm(goal)}",
            metadata=metadata,
            importance=_clamp(importance),
        )
        record = self.memory_continuity.memory.store.memory_by_id(memory_id)
        if record is None:
            raise RuntimeError("decisão B19 persistida não pôde ser relida")
        root = self.graph.add_entity(
            "planning_decision_taxonomy",
            "PLANEJAMENTO E TOMADA DE DECISÃO",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B19", "automatic_execution": False},
        )
        node_id = f"PLANNING-DECISION-{memory_id:010d}"
        self.graph.add_entity(
            "planning_decision",
            content[:160],
            node_id=node_id,
            data={"block": "B19", "memory_id": memory_id, "reference": _clean(reference), "execution_performed": False},
        )
        self.graph.relate(root, node_id, "has_recorded_decision", metadata={"block": "B19"})
        return {
            "memory_id": memory_id,
            "memory_node_id": node_id,
            "kind": "decision",
            "persistent": True,
            "record": record,
            "execution_performed": False,
            "operational_authorization": False,
        }

    def materialize_taxonomy(self, stage: str | None = None) -> dict:
        stage_key = _norm(stage) if stage else None
        if stage_key and stage_key not in STAGES:
            raise KeyError(stage)
        branches = [branch for branch in PLANNING_BRANCHES if stage_key is None or branch.stage == stage_key]
        root = self.graph.add_entity(
            "planning_decision_taxonomy",
            "PLANEJAMENTO E TOMADA DE DECISÃO",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B19", "fact_authority": False, "automatic_execution": False},
        )
        for source_id, label in (
            ("MEMORY-TAX-ROOT", "B13 Memory"),
            ("ATTENTION-TAX-ROOT", "B14 Attention"),
            ("INTERNAL-MODELS-TAX-ROOT", "B15 Models"),
            ("REASONING-SIMULATION-TAX-ROOT", "B18 Reasoning"),
        ):
            self.graph.add_entity("planning_source", label, node_id=source_id, data={"block": "B19"})
            self.graph.relate(root, source_id, "integrates", metadata={"block": "B19"})
        for branch in branches:
            stage_id = f"PLAN-STAGE-{branch.stage.upper()}"
            branch_id = f"PLAN-BR-{branch.key.upper()}"
            self.graph.add_entity("planning_stage", STAGE_LABELS[branch.stage], node_id=stage_id, data={"block": "B19"})
            self.graph.add_entity("planning_branch", branch.label, node_id=branch_id, data={"block": "B19"})
            self.graph.relate(root, stage_id, "has_part", metadata={"block": "B19"})
            self.graph.relate(stage_id, branch_id, "has_part", metadata={"block": "B19"})
        return {"stage": stage_key, "branches_materialized": len(branches), "knowledge_graph": "shared", "parallel_planner_created": False}

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace("B19"),
            "catalog": self.catalog.stats(),
            "policy": deepcopy(PLANNING_POLICY),
            "reuses": {
                "planner": "CognitiveSuite.planner",
                "reasoning_simulation": "B18 ReasoningSimulation",
                "memory": "B13 MemoryContinuity",
                "attention": "B14 AttentionSalience",
                "operational_boundary": "B01 FoundationSuite.boundary",
            },
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 19", "status planejamento", "status planner", "planejamento e tomada de decisao", "planejamento e tomada de decisão"}:
            stats = self.stats()["catalog"]
            return (
                f"⭐ BLOCO 19 — PLANEJAMENTO: {stats['addressable_contents']} representações | "
                f"{stats['branches']} ramos × {stats['lenses_per_branch']} lentes | "
                "PLANO ≠ AÇÃO; DECISÃO ≠ EXECUÇÃO."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['stage_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
