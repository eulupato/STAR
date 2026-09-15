"""BLOCO 24 — MIND LOOP.

Orquestra os componentes cognitivos existentes da STAR em um ciclo explícito e
bounded. O loop não cria outra memória, outro planner, outros modelos ou outro
executor. A etapa AÇÃO apenas avalia elegibilidade; nenhuma ferramenta/dispositivo
é executado por este módulo.
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


MIND_LOOP_STAGES = (
    "PERCEBER",
    "CONTEXTO",
    "WORKING MEMORY",
    "SALIÊNCIA",
    "MEMÓRIA",
    "CONHECIMENTO",
    "MODELOS",
    "INTERPRETAÇÃO",
    "SIMULAÇÃO",
    "METACOGNIÇÃO",
    "JULGAMENTO",
    "DECISÃO",
    "AÇÃO",
    "RESULTADO",
    "EXPERIÊNCIA",
    "APRENDIZADO",
    "ATUALIZAÇÃO",
)

STAGE_KEYS = (
    "perceber", "contexto", "working_memory", "saliencia", "memoria",
    "conhecimento", "modelos", "interpretacao", "simulacao", "metacognicao",
    "julgamento", "decisao", "acao", "resultado", "experiencia",
    "aprendizado", "atualizacao",
)


@dataclass(frozen=True)
class MindLoopBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


_DOMAINS = {
    "perception_context": (
        ("perceive", "PERCEBER", "percepção;entrada;modalidade;evento;sinal"),
        ("context", "CONTEXTO", "contexto;situação;objetivo;entidades;tempo"),
        ("perception_status", "Estado perceptivo", "available;unavailable;observado;fornecido;incerteza"),
        ("temporal_anchor", "Âncora temporal", "agora;recente;sequência;ordem;tempo"),
        ("context_revision", "Revisão de contexto", "novo sinal;mudança;revisão;situação;atualização"),
    ),
    "working_attention": (
        ("working_memory", "WORKING MEMORY", "working memory;ativo;temporário;bounded;B13"),
        ("salience", "SALIÊNCIA", "saliência;atenção;prioridade;relevância;B14"),
        ("active_goal", "Objetivo ativo", "objetivo;prioridade;planejamento;contexto"),
        ("active_entities", "Entidades ativas", "entidade;pessoa;objeto;relação;recência"),
        ("attention_limits", "Limites atencionais", "top-k;janela;truncamento;não carregar tudo"),
    ),
    "memory_knowledge": (
        ("memory", "MEMÓRIA", "recall;episódica;semântica;continuidade;B13"),
        ("knowledge", "CONHECIMENTO", "B03;query;índice;cache;proveniência"),
        ("sources", "Fontes", "origem;referência;proveniência;rastreabilidade"),
        ("contradictions", "Contradições", "conflito;versões;revisão;incerteza"),
        ("retrieval_relevance", "Relevância de recuperação", "query;contexto;top-k;seleção;bounded"),
    ),
    "models_interpretation": (
        ("models", "MODELOS", "World Model;Human Model;Social Model;Self Model;Situation Model"),
        ("situation_model", "Situation Model", "agora;entidades;evidência;risco;urgência"),
        ("interpretation", "INTERPRETAÇÃO", "interpretação;inferência;contexto;significado"),
        ("hypotheses", "Hipóteses", "hipótese;alternativas;incerteza;explicações"),
        ("model_cooperation", "Cooperação dos modelos", "B15;referências;shared;sem duplicar"),
    ),
    "simulation_reasoning": (
        ("simulation", "SIMULAÇÃO", "simulação;estado;mudança;assunção;B18"),
        ("prediction", "Previsão", "prediction;horizonte;confiança;erro"),
        ("causality", "Causalidade", "causa;efeito;evidência;alternativas"),
        ("counterfactual", "Contrafactual", "what-if;baseline;hipotético;história ≠ simulação"),
        ("risk", "Risco e consequência", "risco;consequência;reversibilidade;probabilidade"),
    ),
    "meta_judgment": (
        ("metacognition", "METACOGNIÇÃO", "sabe;não sabe;confiança;fonte;B20"),
        ("unknowns", "Desconhecidos", "lacuna;incerteza;perguntar;pesquisar"),
        ("review", "Revisão", "contradição;baixa confiança;revisão;fonte"),
        ("judgment", "JULGAMENTO", "julgamento;prontidão;risco;limites"),
        ("epistemic_humility", "Humildade epistêmica", "não sei;limite;defer;transparência"),
    ),
    "decision_action": (
        ("decision", "DECISÃO", "decisão;alternativas;verificação;B19"),
        ("planning", "Planejamento", "objetivo;estado;opções;plano;risco"),
        ("action", "AÇÃO", "ação;elegibilidade;boundary;permissão;capacidade"),
        ("operational_boundary", "Fronteira operacional", "permissão;capacidade;segurança;default deny"),
        ("no_auto_execution", "Sem execução automática", "planejar ≠ agir;decidir ≠ executar;separação"),
    ),
    "result_experience": (
        ("result", "RESULTADO", "resultado;observação;efeito;estado pós-ação"),
        ("observed_outcome", "Resultado observado", "observado;fonte;referência;tempo"),
        ("experience", "EXPERIÊNCIA", "experiência;autobiográfica;auditoria;B13;B21"),
        ("audit_reference", "Referência auditável", "fonte;referência;proveniência;não fabricar"),
        ("outcome_context", "Contexto do resultado", "objetivo;situação;risco;entidades;significado"),
    ),
    "learning_update": (
        ("learning", "APRENDIZADO", "aprendizado;experiência;B21;adaptação"),
        ("prediction_error", "Prediction error", "previsto;observado;erro;revisão"),
        ("consolidation", "Consolidação", "memória;resumo;origem;relação"),
        ("knowledge_integration", "ATUALIZAÇÃO", "B22;integração;modelos;contexto"),
        ("update_limits", "Limites de atualização", "sem autoedição;sem fato automático;histórico preservado"),
    ),
    "loop_control": (
        ("stage_order", "Ordem do ciclo", "17 etapas;ordem;pipeline;ciclo"),
        ("bounded_retrieval", "Recuperação bounded", "B23;B14;top-k;1B lógico;não varrer tudo"),
        ("workspace", "Workspace ativo", "B23;broadcast;janela;índice ativo"),
        ("continuity", "Continuidade", "B13;estado;memória;experiência;próximo ciclo"),
        ("audit", "Auditoria do ciclo", "etapas;fontes;confiança;resultado;sem execução"),
    ),
}

DOMAIN_LABELS = {
    "perception_context": "Percepção e contexto",
    "working_attention": "Working memory e atenção",
    "memory_knowledge": "Memória e conhecimento",
    "models_interpretation": "Modelos e interpretação",
    "simulation_reasoning": "Simulação e raciocínio",
    "meta_judgment": "Metacognição e julgamento",
    "decision_action": "Decisão e ação",
    "result_experience": "Resultado e experiência",
    "learning_update": "Aprendizado e atualização",
    "loop_control": "Controle do Mind Loop",
}

MIND_LOOP_BRANCHES = tuple(
    MindLoopBranch(domain, key, label, _subs(subtopics))
    for domain, branches in _DOMAINS.items()
    for key, label, subtopics in branches
)

MIND_LOOP_LENSES = (
    ("source", "fonte", "preservar origem e referência"),
    ("relevance", "relevância", "selecionar apenas o necessário"),
    ("state", "estado", "representar o estado atual da etapa"),
    ("confidence", "confiança", "preservar incerteza e calibração"),
    ("context", "contexto", "situar no ciclo corrente"),
    ("relation", "relação", "conectar etapas sem duplicar dados"),
    ("risk", "risco", "considerar risco sem converter em permissão"),
    ("temporal", "tempo", "preservar ordem, recência e continuidade"),
    ("limits", "limites", "declarar indisponibilidade e fronteiras"),
    ("audit", "auditoria", "explicar o que entrou e saiu do ciclo"),
)

SOURCE_AXIS = ("perception", "B13", "B14", "B15", "B18", "B19", "B20", "B21", "B22", "B23")
CONTEXT_AXIS = ("conversation", "project", "physical", "social", "technical", "scientific", "personal", "emergency", "planning", "mixed")
EPISTEMIC_AXIS = ("observation", "declared", "memory", "fact", "inference", "hypothesis", "prediction", "simulation", "unknown", "disputed")
PRIORITY_AXIS = ("none", "very_low", "low", "moderate_low", "moderate", "moderate_high", "high", "very_high", "critical", "mixed")
CONFIDENCE_AXIS = ("very_low", "low", "moderate", "high", "very_high")
MODE_AXIS = ("input", "active", "derived", "review")
TIME_AXIS = ("instant", "recent", "session", "day", "week", "long_term", "historical", "future", "unknown", "mixed")
VARIANT_AXES = (
    ("source_space", SOURCE_AXIS),
    ("context", CONTEXT_AXIS),
    ("epistemic_state", EPISTEMIC_AXIS),
    ("priority", PRIORITY_AXIS),
    ("confidence", CONFIDENCE_AXIS),
    ("mode", MODE_AXIS),
    ("time_scope", TIME_AXIS),
)

CANONICAL_NODES = len(MIND_LOOP_BRANCHES) * len(MIND_LOOP_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE
if len(_DOMAINS) != 10 or len(MIND_LOOP_BRANCHES) != 50 or len(MIND_LOOP_LENSES) != 10:
    raise RuntimeError("B24 requer 10 domínios, 50 ramos e 10 lentes")
if CANONICAL_NODES != 500 or VARIANTS_PER_NODE != 2_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B24 inválida")

MIND_LOOP_POLICY = {
    "loads_full_previous_blocks": False,
    "bounded_retrieval": True,
    "workspace_source": "B23",
    "attention_source": "B14",
    "working_memory_source": "B13",
    "decision_executes_action": False,
    "action_stage_executes_tools": False,
    "unobserved_result_is_fabricated": False,
    "unaudited_experience_is_persisted": False,
    "learning_can_modify_core_code": False,
    "canonical_promotion_automatic": False,
    "operational_authorization": False,
    "rule": "CICLO COGNITIVO ≠ EXECUÇÃO AUTOMÁTICA; RESULTADO NÃO OBSERVADO ≠ EXPERIÊNCIA INVENTADA",
}


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    value = int(index)
    out: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        value, offset = divmod(value, len(values))
        out[name] = values[offset]
    return {name: out[name] for name, _ in VARIANT_AXES}


class MindLoopCatalog:
    NAMESPACE = "B24"
    PREFIX = "LOOP-B24"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "domains": 10,
            "branches": 50,
            "lenses_per_branch": 10,
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "precomputed_cycles": 0,
            "truthfulness_note": "1B are addressable loop contexts, not 1B cycles loaded or executed",
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"LOOP-B24-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"LOOP-B24-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, 10)
        branch = MIND_LOOP_BRANCHES[branch_index]
        lens_key, lens_label, instruction = MIND_LOOP_LENSES[lens_index]
        return {
            "id": f"LOOP-B24-{absolute:010d}",
            "namespace": "B24",
            "domain": branch.domain,
            "domain_label": DOMAIN_LABELS[branch.domain],
            "branch": branch.key,
            "branch_label": branch.label,
            "subtopics": branch.subtopics,
            "lens": lens_key,
            "lens_label": lens_label,
            **_decode_axes(variant_index),
            "prompt": f"{branch.label} / {lens_label}: {instruction}. Recuperar somente o necessário e preservar fronteiras operacionais.",
        }


class MindLoop:
    """Orquestrador bounded do ciclo cognitivo da STAR."""

    NAMESPACE = "B24"
    TAXONOMY_ROOT_ID = "MIND-LOOP-TAX-ROOT"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        global_workspace,
        memory_continuity,
        attention_salience,
        internal_models,
        reasoning_simulation,
        metacognition,
        planning_decision,
        learning_evolution,
        knowledge_integration,
        operational_boundary=None,
        social_cognition=None,
        perception_provider=None,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.global_workspace = global_workspace
        self.memory_continuity = memory_continuity
        self.attention_salience = attention_salience
        self.internal_models = internal_models
        self.reasoning_simulation = reasoning_simulation
        self.metacognition = metacognition
        self.planning_decision = planning_decision
        self.learning_evolution = learning_evolution
        self.knowledge_integration = knowledge_integration
        self.operational_boundary = operational_boundary
        self.social_cognition = social_cognition
        self.perception_provider = perception_provider
        self.catalog = MindLoopCatalog()
        self._cycle_counter = 0
        self._last_cycle: dict | None = None
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 24 — MIND LOOP",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/mind_loop.py",
            metadata={
                "materialization": "on-demand",
                "stages": MIND_LOOP_STAGES,
                "retrieval": "B23/B14 bounded top-k",
                "automatic_execution": False,
                "parallel_memory": False,
                "parallel_models": False,
                "parallel_planner": False,
            },
        )

    def attach_perception(self, provider) -> None:
        self.perception_provider = provider

    def _perception(self, explicit: Iterable[dict] | None) -> dict:
        if explicit is not None:
            items = [deepcopy(item) for item in list(explicit)[:16] if isinstance(item, dict)]
            return {"status": "provided", "items": items, "provider_available": self.perception_provider is not None, "fabricated": False}
        if self.perception_provider is not None and hasattr(self.perception_provider, "workspace_observations"):
            items = deepcopy(list(self.perception_provider.workspace_observations(limit=16) or ()))[:16]
            available = bool(items)
            checker = getattr(self.perception_provider, "workspace_available", None)
            if callable(checker):
                try:
                    available = bool(checker())
                except (RuntimeError, TypeError, AttributeError):
                    available = bool(items)
            return {"status": "provider" if items else "idle", "items": items, "provider_available": available, "fabricated": False}
        return {"status": "unavailable", "items": [], "provider_available": False, "fabricated": False}

    @staticmethod
    def _active_entities(active: Iterable[dict]) -> tuple[str, ...]:
        out: list[str] = []
        for item in active:
            for entity in item.get("entities") or ():
                value = _clean(entity)
                if value and value not in out:
                    out.append(value)
                if len(out) >= 16:
                    return tuple(out)
        return tuple(out)

    @staticmethod
    def _result_content(result: Any) -> str:
        if isinstance(result, dict):
            for key in ("content", "result", "outcome", "message", "status"):
                if _clean(result.get(key)):
                    return _clean(result.get(key))
        return _clean(result)

    def run_cycle(
        self,
        input_text: str = "",
        *,
        query: str = "",
        perception: Iterable[dict] | None = None,
        context_candidates: Iterable[dict] | None = None,
        goal: str = "",
        current_state: dict | None = None,
        desired_state: dict | None = None,
        obstacles: Iterable[str] | None = None,
        options: Iterable[Any] | None = None,
        constraints: Iterable[str] | None = None,
        risk: float = 0.0,
        urgency: float = 0.0,
        missing_context: Iterable[str] | None = None,
        permission: bool = False,
        capability: bool = False,
        safety_ok: bool = False,
        authorization_source: str | None = None,
        observed_result: Any = None,
        result_source: str = "",
        result_reference: str = "",
        predicted_value: float | None = None,
        observed_value: float | None = None,
        learning_observations: Iterable[Any] | None = None,
        learning_scope: str = "cycle",
        active_limit: int = 16,
    ) -> dict:
        self._cycle_counter += 1
        cycle_id = f"B24-CYCLE-{self._cycle_counter:08d}"
        input_text = _clean(input_text)
        query_text = _clean(query) or input_text or _clean(goal)
        goal = _clean(goal)
        current = deepcopy(dict(current_state or {}))
        desired = deepcopy(dict(desired_state or {}))
        option_list = deepcopy(list(options or ())[:32])
        limit = max(4, min(int(active_limit), min(self.global_workspace.max_active, 32)))
        stages: dict[str, Any] = {}

        # 1 — PERCEBER: somente sinais fornecidos ou buffer real de provider.
        percept = self._perception(perception)
        stages["perceber"] = percept

        # 2 — CONTEXTO: B23 agrega candidatos/retrieval e B14 seleciona top-k.
        workspace = self.global_workspace.activate(
            query=query_text,
            perception=percept["items"],
            candidates=context_candidates,
            goal=goal,
            language_input=input_text,
            limit=limit,
        )
        active = deepcopy(workspace.get("active") or [])
        stages["contexto"] = {
            "workspace": workspace,
            "active_count": len(active),
            "bounded": True,
            "loads_full_logical_space": False,
        }

        # 3 — WORKING MEMORY: o mesmo buffer bounded do B13.
        wm_content = query_text or "Mind Loop context update"
        wm_item = self.memory_continuity.working.add(
            wm_content,
            key="b24:last_cycle_input",
            importance=0.7,
            context={"cycle_id": cycle_id, "goal": goal, "active_count": len(active)},
            source="B24 Mind Loop",
            metadata={"block": "B24", "epistemic_kind": "declared_information" if input_text else "observation"},
        )
        stages["working_memory"] = {"item": wm_item, "shared_with_b13": True, "bounded": True}

        # 4 — SALIÊNCIA: reutiliza os scores já produzidos pelo B14 dentro do B23.
        stages["saliencia"] = {
            "active": active,
            "scores": [item.get("attention_score") for item in active],
            "source": "B14 via B23",
            "priority_is_permission": False,
        }

        # 5 — MEMÓRIA: recall limitado.
        recalled = self.memory_continuity.recall(query_text, limit=8) if query_text else self.memory_continuity.working.list(limit=8)
        stages["memoria"] = {"items": deepcopy(recalled[:8]), "limit": 8, "bounded": True}

        # 6 — CONHECIMENTO: query indexada/limitada pelo B03.
        knowledge_items = self.knowledge.query(query_text, limit=8) if query_text else []
        stages["conhecimento"] = {"items": deepcopy(knowledge_items[:8]), "limit": 8, "bounded": True}

        # 7 — MODELOS: os mesmos cinco modelos B15 cooperam no Situation Model.
        entities = self._active_entities(active)
        evidence = tuple(_clean(item.get("content")) for item in active if _clean(item.get("content")))[:16]
        models = self.internal_models.cooperate(
            current_input=input_text or query_text,
            goal=goal,
            active_entities=entities,
            evidence=evidence,
            risk=_clamp(risk),
            urgency=_clamp(urgency),
        )
        stages["modelos"] = models

        # 8 — INTERPRETAÇÃO: inferência B18 sobre o conjunto ativo, sem promover fato.
        interpretation = self.reasoning_simulation.analyze(
            query_text or "current situation",
            candidates=active,
            limit=min(8, limit),
        )
        stages["interpretacao"] = interpretation

        # 9 — SIMULAÇÃO: baseline/alteração hipotética, nunca observação.
        first_option = option_list[0] if option_list else None
        changes = deepcopy(first_option.get("changes") or {}) if isinstance(first_option, dict) else {}
        simulation = self.reasoning_simulation.simulate_state(current, changes, assumptions=["B24 bounded cycle simulation"])
        stages["simulacao"] = simulation

        # 10 — METACOGNIÇÃO: avalia fontes, confiança e lacunas sem conceder rede.
        source_refs = ["B13"] if recalled else []
        if knowledge_items:
            source_refs.append("B03")
        if active:
            source_refs.append("B23")
        confidence = 0.7 if knowledge_items else (0.6 if recalled or active else 0.3)
        meta = self.metacognition.assess(
            query_text or "current cycle",
            local_answer=bool(recalled or knowledge_items or active),
            confidence=confidence,
            sources=source_refs,
            candidates=active,
            missing_context=missing_context,
            network_allowed=False,
        )
        stages["metacognicao"] = meta

        # 11 — JULGAMENTO: artefato revisável, não fato/autorização.
        judgment = {
            "confidence": meta.get("confidence"),
            "recommended_action": meta.get("recommended_action"),
            "needs_research": meta.get("needs_research"),
            "needs_question": meta.get("needs_question"),
            "needs_review": meta.get("needs_review"),
            "risk": _clamp(risk),
            "urgency": _clamp(urgency),
            "ready_for_decision": bool(goal and not meta.get("needs_question")),
            "epistemic_kind": "inference",
            "operational_authorization": False,
        }
        stages["julgamento"] = judgment

        # 12 — DECISÃO: B19 pode planejar/decidir, mas nunca executar.
        decision = None
        if goal:
            decision = self.planning_decision.plan_decision(
                goal,
                current_state=current,
                desired_state=desired,
                obstacles=obstacles,
                options=option_list,
                constraints=constraints,
                context_candidates=active,
                context_limit=min(8, limit),
                permission=permission,
                capability=capability,
                safety_ok=safety_ok,
                authorization_source=authorization_source,
            )
            stages["decisao"] = decision
        else:
            stages["decisao"] = {"status": "deferred", "reason": "no explicit goal", "execution_performed": False}

        # 13 — AÇÃO: somente boundary/elegibilidade; nada é executado aqui.
        if decision is not None:
            boundary = deepcopy(decision.get("execution_boundary") or {})
        elif self.operational_boundary is not None:
            boundary = self.operational_boundary.evaluate(
                f"mind loop: {query_text or 'context'}",
                permission=permission,
                capability=capability,
                safety_ok=safety_ok,
                authorization_source=authorization_source,
            )
        else:
            boundary = {"can_act": bool(permission and capability and safety_ok)}
        stages["acao"] = {
            "boundary": boundary,
            "eligible_for_separate_execution": bool(boundary.get("can_act")),
            "execution_performed": False,
            "mind_loop_executes_tools": False,
            "operational_authorization": False,
        }

        # 14 — RESULTADO: só existe quando foi realmente observado/fornecido.
        observed = observed_result is not None
        result_content = self._result_content(observed_result) if observed else ""
        stages["resultado"] = {
            "observed": observed,
            "content": result_content or None,
            "raw": deepcopy(observed_result) if observed else None,
            "source": _clean(result_source) or None,
            "reference": _clean(result_reference) or None,
            "fabricated": False,
        }

        # 15 — EXPERIÊNCIA: exige resultado + fonte + referência auditável.
        experience = {"recorded": False, "reason": "no observed result", "fabricated": False}
        if observed:
            if _clean(result_source) and _clean(result_reference) and result_content:
                recorded = self.learning_evolution.record_experience(
                    result_content,
                    source=result_source,
                    reference=result_reference,
                    context={"cycle_id": cycle_id, "goal": goal},
                    meaning="B24 observed Mind Loop result",
                )
                experience = {"recorded": True, **recorded, "fabricated": False}
            else:
                experience = {"recorded": False, "reason": "source_and_reference_required", "fabricated": False}
        stages["experiencia"] = experience

        # 16 — APRENDIZADO: somente sobre experiência auditável; nunca edita código.
        learning: dict[str, Any] = {
            "performed": False,
            "experience_required": True,
            "code_mutation": False,
            "automatic_code_modification": False,
        }
        if experience.get("recorded"):
            learning = {
                "performed": True,
                "experience_memory_id": experience.get("memory_id"),
                "prediction_feedback": None,
                "generalization": None,
                "consistency": self.learning_evolution.assess_consistency(
                    result_content,
                    sources=[result_source],
                    confidence=0.7,
                ),
                "code_mutation": False,
                "automatic_code_modification": False,
            }
            if predicted_value is not None and observed_value is not None:
                learning["prediction_feedback"] = self.learning_evolution.prediction_feedback(
                    predicted_value,
                    observed_value,
                    source=result_source,
                    reference=result_reference,
                    context=learning_scope,
                )
            observations = list(learning_observations or ())[:32]
            if observations:
                learning["generalization"] = self.learning_evolution.generalize(
                    observations,
                    scope=learning_scope,
                    source=result_source,
                    reference=result_reference,
                )
        stages["aprendizado"] = learning

        # 17 — ATUALIZAÇÃO: resultado observado informa Situation Model via B22.
        update: dict[str, Any] = {"performed": False, "reason": "no audited observed result", "canonical_promotion_performed": False}
        if experience.get("recorded"):
            integrated = self.knowledge_integration.integrate_situation(
                result_content,
                source=result_source,
                reference=result_reference,
                active_entities=entities,
                evidence=evidence,
                goal=goal,
                risk=_clamp(risk),
                urgency=_clamp(urgency),
            )
            update = {
                "performed": True,
                "integration": integrated,
                "canonical_promotion_performed": False,
                "core_code_modified": False,
            }
        stages["atualizacao"] = update

        cycle = {
            "cycle_id": cycle_id,
            "sequence": MIND_LOOP_STAGES,
            "stage_keys": STAGE_KEYS,
            "stages": stages,
            "active_limit": limit,
            "active_count": len(active),
            "bounded_retrieval": True,
            "loads_full_previous_blocks": False,
            "execution_performed": False,
            "operational_authorization": False,
            "canonical_promotion_performed": False,
            "core_code_modified": False,
        }
        self._last_cycle = deepcopy(cycle)
        return cycle

    def last_cycle(self) -> dict | None:
        return deepcopy(self._last_cycle)

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = _norm(domain) if domain else None
        if key and key not in _DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in MIND_LOOP_BRANCHES if key is None or branch.domain == key]
        root = self.graph.add_entity(
            "mind_loop_taxonomy",
            "MIND LOOP",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B24", "automatic_execution": False},
        )
        for source_id, label in (
            ("MEMORY-TAX-ROOT", "B13 Memory"),
            ("ATTENTION-TAX-ROOT", "B14 Attention"),
            ("MODELS-B15-ROOT", "B15 Models"),
            ("REASONING-SIMULATION-TAX-ROOT", "B18 Reasoning"),
            ("PLANNING-DECISION-TAX-ROOT", "B19 Planning"),
            ("METACOGNITION-TAX-ROOT", "B20 Metacognition"),
            ("LEARNING-EVOLUTION-TAX-ROOT", "B21 Learning"),
            ("KNOWLEDGE-INTEGRATION-TAX-ROOT", "B22 Knowledge Integration"),
            ("GLOBAL-WORKSPACE-TAX-ROOT", "B23 Workspace"),
        ):
            self.graph.add_entity("mind_loop_source", label, node_id=source_id, data={"block": "B24"})
            self.graph.relate(root, source_id, "integrates", metadata={"block": "B24"})
        for branch in selected:
            domain_id = f"LOOP-DOM-{branch.domain.upper()}"
            branch_id = f"LOOP-BR-{branch.key.upper()}"
            self.graph.add_entity("mind_loop_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B24"})
            self.graph.add_entity("mind_loop_branch", branch.label, node_id=branch_id, data={"block": "B24"})
            self.graph.relate(root, domain_id, "has_part", metadata={"block": "B24"})
            self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B24"})
        return {"domain": key, "branches_materialized": len(selected), "shared_graph": True, "parallel_loop_store": False}

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace("B24"),
            "catalog": self.catalog.stats(),
            "stages": MIND_LOOP_STAGES,
            "policy": deepcopy(MIND_LOOP_POLICY),
            "last_cycle_id": None if self._last_cycle is None else self._last_cycle.get("cycle_id"),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 24", "status mind loop", "mind loop", "status ciclo cognitivo"}:
            stats = self.catalog.stats()
            return (
                f"⭐ BLOCO 24 — MIND LOOP: {stats['addressable_contents']} representações | "
                f"{len(MIND_LOOP_STAGES)} etapas | recuperação bounded | ação automática = NÃO."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
