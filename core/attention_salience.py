"""BLOCO 14 — Working Memory, Attention e Salience.

Seleciona o que importa agora sem carregar o espaço lógico inteiro. A camada
reutiliza o WorkingMemoryBuffer do BLOCO 13 e o StarState existente; não cria
outro estado cognitivo nem uma segunda working memory. Saliência, risco e urgência
alteram prioridade cognitiva, nunca concedem autorização operacional.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import islice
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


ATTENTION_DOMAINS = (
    "attention",
    "salience",
    "priority",
    "active_goals",
    "active_entities",
    "recent_context",
    "hypotheses",
    "temporary_results",
    "risks",
    "urgency",
)

DOMAIN_LABELS = {
    "attention": "Atenção",
    "salience": "Saliência",
    "priority": "Prioridade",
    "active_goals": "Objetivos ativos",
    "active_entities": "Entidades ativas",
    "recent_context": "Contexto recente",
    "hypotheses": "Hipóteses",
    "temporary_results": "Resultados temporários",
    "risks": "Riscos",
    "urgency": "Urgência",
}


@dataclass(frozen=True)
class AttentionBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(";") if item.strip())


ATTENTION_BRANCHES = (
    AttentionBranch("attention", "focus_target", "Alvo de foco", _subs("foco;alvo;escopo;seleção cognitiva")),
    AttentionBranch("attention", "focus_capacity", "Capacidade de foco", _subs("attention;focus;cognitive_load;StarState;limites")),
    AttentionBranch("attention", "switching", "Troca de foco", _subs("mudança de tarefa;interrupção;custo de troca;continuidade")),
    AttentionBranch("attention", "sustained_attention", "Atenção sustentada", _subs("persistência;duração;fadiga computacional;carga")),
    AttentionBranch("attention", "attention_window", "Janela de atenção", _subs("janela bounded;top-k;candidatos;limite de contexto")),

    AttentionBranch("salience", "novelty", "Novidade", _subs("novidade;mudança;surpresa;diferença contextual")),
    AttentionBranch("salience", "goal_relevance", "Relevância para objetivo", _subs("objetivo;alinhamento;dependência;critério de sucesso")),
    AttentionBranch("salience", "entity_relevance", "Relevância de entidade", _subs("entidade ativa;referência;menção;relação")),
    AttentionBranch("salience", "context_relevance", "Relevância contextual", _subs("contexto recente;situação;projeto;conversa")),
    AttentionBranch("salience", "change_signal", "Sinal de mudança", _subs("mudança;evento;estado novo;desvio;contradição")),

    AttentionBranch("priority", "explicit_priority", "Prioridade explícita", _subs("prioridade declarada;ordem;fila;importância")),
    AttentionBranch("priority", "goal_priority", "Prioridade por objetivo", _subs("objetivo ativo;dependência;bloqueio;valor")),
    AttentionBranch("priority", "risk_priority", "Prioridade por risco", _subs("risco;impacto;probabilidade;atenção;sem autorização")),
    AttentionBranch("priority", "urgency_priority", "Prioridade por urgência", _subs("urgência;tempo;deadline;janela crítica")),
    AttentionBranch("priority", "priority_conflicts", "Conflitos de prioridade", _subs("trade-off;conflito;empate;justificativa")),

    AttentionBranch("active_goals", "goal_registry", "Registro de objetivos ativos", _subs("objetivo;estado;fonte;importância;working memory")),
    AttentionBranch("active_goals", "goal_dependencies", "Dependências de objetivo", _subs("pré-requisito;bloqueio;sequência;relação")),
    AttentionBranch("active_goals", "goal_progress", "Progresso de objetivo", _subs("progresso;resultado;pendência;próximo passo")),
    AttentionBranch("active_goals", "goal_constraints", "Restrições de objetivo", _subs("restrição;segurança;permissão;escopo;limite")),
    AttentionBranch("active_goals", "goal_completion", "Conclusão de objetivo", _subs("critério de sucesso;conclusão;validação;remoção do foco")),

    AttentionBranch("active_entities", "entity_registry", "Registro de entidades ativas", _subs("entidade;tipo;identificador;fonte;working memory")),
    AttentionBranch("active_entities", "entity_mentions", "Menções de entidades", _subs("menção;referência;recência;frequência")),
    AttentionBranch("active_entities", "entity_relations", "Relações de entidades", _subs("relação;grafo;contexto;dependência")),
    AttentionBranch("active_entities", "entity_state", "Estado de entidade", _subs("estado observado;incerteza;atualidade;fonte")),
    AttentionBranch("active_entities", "entity_decay", "Decaimento de atividade", _subs("recência;desativação;janela;persistência contextual")),

    AttentionBranch("recent_context", "recent_turns", "Turnos recentes", _subs("conversa;mensagem;ordem;janela recente")),
    AttentionBranch("recent_context", "recent_events", "Eventos recentes", _subs("evento;mudança;data;entidades;memória")),
    AttentionBranch("recent_context", "recent_decisions", "Decisões recentes", _subs("decisão;motivo;resultado;continuidade")),
    AttentionBranch("recent_context", "recent_state", "Estado recente", _subs("estado;StarState;working memory;observação")),
    AttentionBranch("recent_context", "context_decay", "Decaimento de contexto", _subs("recência;expiração;priorização;remoção")),

    AttentionBranch("hypotheses", "open_hypotheses", "Hipóteses abertas", _subs("hipótese;alternativa;incerteza;working memory")),
    AttentionBranch("hypotheses", "hypothesis_evidence", "Evidência de hipótese", _subs("evidência;suporte;refutação;fonte;confiança")),
    AttentionBranch("hypotheses", "hypothesis_conflicts", "Conflitos entre hipóteses", _subs("alternativas;contradição;comparação;não colapsar cedo")),
    AttentionBranch("hypotheses", "hypothesis_status", "Estado de hipótese", _subs("aberta;testada;refutada;suportada;incerta")),
    AttentionBranch("hypotheses", "hypothesis_resolution", "Resolução de hipótese", _subs("teste;resultado;revisão;promoção epistêmica separada")),

    AttentionBranch("temporary_results", "intermediate_results", "Resultados intermediários", _subs("resultado temporário;cálculo;saída parcial;working memory")),
    AttentionBranch("temporary_results", "derived_values", "Valores derivados", _subs("derivação;assunção;unidade;fonte;validade")),
    AttentionBranch("temporary_results", "candidate_answers", "Respostas candidatas", _subs("candidato;comparação;confiança;verificação")),
    AttentionBranch("temporary_results", "temporary_artifacts", "Artefatos temporários", _subs("rascunho;estrutura;buffer;resultado não persistente")),
    AttentionBranch("temporary_results", "result_expiration", "Expiração de resultados", _subs("validade;stale;remoção;consolidação opcional")),

    AttentionBranch("risks", "risk_detection", "Detecção de risco", _subs("risco;sinal;hazard;consequência;incerteza")),
    AttentionBranch("risks", "risk_severity", "Severidade de risco", _subs("impacto;gravidade;prioridade;escala")),
    AttentionBranch("risks", "risk_likelihood", "Probabilidade de risco", _subs("probabilidade;evidência;incerteza;contexto")),
    AttentionBranch("risks", "risk_dependencies", "Dependências de risco", _subs("causa;condição;propagação;relação")),
    AttentionBranch("risks", "risk_attention", "Elevação de atenção por risco", _subs("saliência;atenção;prioridade;sem permissão automática")),

    AttentionBranch("urgency", "time_pressure", "Pressão temporal", _subs("tempo;deadline;janela;latência")),
    AttentionBranch("urgency", "deadline", "Prazo", _subs("deadline;data;tempo restante;fonte")),
    AttentionBranch("urgency", "interrupt_priority", "Prioridade de interrupção", _subs("interrupção;urgência;risco;trade-off")),
    AttentionBranch("urgency", "urgency_decay", "Decaimento de urgência", _subs("tempo;expiração;mudança de prioridade")),
    AttentionBranch("urgency", "urgency_boundary", "Limite operacional da urgência", _subs("urgência não autoriza ação;permissão;segurança;capacidade")),
)

ATTENTION_LENSES = (
    ("signal", "sinal", "qual sinal torna o item potencialmente relevante"),
    ("goal", "objetivo", "como o item se relaciona a objetivos ativos"),
    ("entity", "entidade", "como o item se relaciona a entidades ativas"),
    ("recency", "recência", "quanto o item depende do contexto recente"),
    ("salience", "saliência", "qual destaque cognitivo é justificável"),
    ("priority", "prioridade", "qual prioridade explícita ou derivada foi atribuída"),
    ("risk", "risco", "qual risco justifica elevar atenção sem autorizar ação"),
    ("urgency", "urgência", "qual pressão temporal altera a ordem de análise"),
    ("confidence", "confiança", "qual confiança/incerteza acompanha a seleção"),
    ("selection", "seleção", "como incluir ou excluir o item em uma janela bounded"),
)

CANDIDATE_SOURCE_AXIS = (
    "working_memory", "persistent_memory", "knowledge_search", "graph_neighbor", "current_input",
    "project", "self_state", "tool_result", "observation", "external_result",
)
GOAL_ALIGNMENT_AXIS = tuple(f"g{i}" for i in range(10))
RECENCY_AXIS = tuple(f"r{i}" for i in range(10))
RISK_AXIS = tuple(f"risk{i}" for i in range(10))
URGENCY_AXIS = ("none", "low", "medium", "high", "critical")
CONFIDENCE_AXIS = ("low", "medium", "high", "verified")
ATTENTION_STATE_AXIS = (
    "idle", "scanning", "focused", "sustained", "switching", "interrupted", "reviewing", "verifying", "risk_focus", "urgent_focus",
)
VARIANT_AXES = (
    ("candidate_source", CANDIDATE_SOURCE_AXIS),
    ("goal_alignment", GOAL_ALIGNMENT_AXIS),
    ("recency", RECENCY_AXIS),
    ("risk", RISK_AXIS),
    ("urgency", URGENCY_AXIS),
    ("confidence", CONFIDENCE_AXIS),
    ("attention_state", ATTENTION_STATE_AXIS),
)

CANONICAL_NODES = len(ATTENTION_BRANCHES) * len(ATTENTION_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(ATTENTION_DOMAINS) != 10:
    raise RuntimeError("B14 requer 10 domínios")
if len(ATTENTION_BRANCHES) != 50:
    raise RuntimeError(f"B14 requer 50 ramos; encontrados {len(ATTENTION_BRANCHES)}")
if len(ATTENTION_LENSES) != 10:
    raise RuntimeError("B14 requer 10 lentes")
if CANONICAL_NODES != 500 or VARIANTS_PER_NODE != 2_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B14 inválida")

ATTENTION_POLICY = {
    "bounded_candidate_window": True,
    "loads_all_available_contents": False,
    "selection_is_fact": False,
    "selection_is_operational_authorization": False,
    "salience_grants_permission": False,
    "urgency_grants_permission": False,
    "risk_grants_permission": False,
    "risk_may_raise_attention": True,
    "working_memory_source": "BLOCO 13 WorkingMemoryBuffer",
    "attention_state_source": "core.state.StarState",
    "rule": "SALIÊNCIA DEFINE O QUE ANALISAR PRIMEIRO; NÃO DEFINE O QUE É VERDADE NEM O QUE A STAR ESTÁ AUTORIZADA A FAZER",
}


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    remainder = int(index)
    decoded: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        remainder, offset = divmod(remainder, len(values))
        decoded[name] = values[offset]
    return {name: decoded[name] for name, _ in VARIANT_AXES}


class AttentionCatalog:
    NAMESPACE = "B14"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "domains": len(ATTENTION_DOMAINS),
            "branches": len(ATTENTION_BRANCHES),
            "lenses_per_branch": len(ATTENTION_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "preloaded_candidates": 0,
            "truthfulness_note": "1B are addressable attention/salience selection states, not 1B simultaneously loaded items",
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"ATTN-B14-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"ATTN-B14-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(ATTENTION_LENSES))
        branch = ATTENTION_BRANCHES[branch_index]
        lens_key, lens_label, instruction = ATTENTION_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"ATTN-B14-{absolute:010d}",
            "namespace": "B14",
            "domain": branch.domain,
            "domain_label": DOMAIN_LABELS[branch.domain],
            "branch": branch.key,
            "branch_label": branch.label,
            "lens": lens_key,
            "lens_label": lens_label,
            **axes,
            "prompt": (
                f"{DOMAIN_LABELS[branch.domain]} / {branch.label} / {lens_label}: {instruction}. "
                f"Fonte={axes['candidate_source']}; alinhamento={axes['goal_alignment']}; recência={axes['recency']}; "
                f"risco={axes['risk']}; urgência={axes['urgency']}; confiança={axes['confidence']}; atenção={axes['attention_state']}. "
                "Selecionar por janela bounded; saliência/risco/urgência não viram verdade ou permissão."
            ),
        }


class AttentionSalience:
    NAMESPACE = "B14"
    TAXONOMY_ROOT_ID = "ATTENTION-TAX-ROOT"
    ROLE_PREFIX = "b14:"

    WEIGHTS = {
        "explicit_priority": 0.18,
        "salience": 0.15,
        "goal_relevance": 0.18,
        "entity_relevance": 0.10,
        "recency": 0.10,
        "risk": 0.12,
        "urgency": 0.12,
        "confidence": 0.05,
    }

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        memory_continuity,
        state=None,
        self_model=None,
        max_candidates: int = 256,
        max_focus: int = 32,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.memory_continuity = memory_continuity
        self.working = memory_continuity.working
        self.state = state
        self.self_model = self_model
        self.max_candidates = max(16, min(int(max_candidates), 2048))
        self.max_focus = max(1, min(int(max_focus), 128))
        self.catalog = AttentionCatalog()
        self._last_selection: dict | None = None
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 14 — WORKING MEMORY, ATTENTION E SALIENCE",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/attention_salience.py",
            metadata={
                "materialization": "on-demand",
                "working_memory": "B13 shared bounded buffer",
                "state": "core.state.StarState when attached",
                "candidate_window": self.max_candidates,
                "parallel_working_memory": False,
                "parallel_state": False,
                "operational_authorization": False,
            },
        )

    def _role_items(self, role: str) -> list[dict]:
        role = _norm(role)
        return [item for item in self.working.list() if _norm((item.get("metadata") or {}).get("b14_role")) == role]

    def _set_role_item(self, role: str, identifier: str, content: str, *, importance: float, metadata=None) -> dict:
        role, identifier = _norm(role), _norm(identifier)
        if not role or not identifier or not _clean(content):
            raise ValueError("item ativo requer role, identifier e content")
        meta = {"b14_role": role, **deepcopy(metadata or {})}
        return self.working.add(
            content,
            key=f"{self.ROLE_PREFIX}{role}:{identifier}",
            importance=importance,
            source="B14 attention/salience",
            metadata=meta,
        )

    def set_active_goal(self, goal_id: str, content: str, *, priority: float = 0.7, metadata=None) -> dict:
        return self._set_role_item("active_goal", goal_id, content, importance=priority, metadata=metadata)

    def set_active_entity(self, entity_id: str, label: str, *, importance: float = 0.6, entity_type: str = "entity", metadata=None) -> dict:
        return self._set_role_item(
            "active_entity", entity_id, label, importance=importance,
            metadata={"entity_type": _clean(entity_type), **deepcopy(metadata or {})},
        )

    def add_hypothesis(self, hypothesis_id: str, content: str, *, confidence: float = 0.5, importance: float = 0.5) -> dict:
        return self._set_role_item("hypothesis", hypothesis_id, content, importance=importance, metadata={"confidence": _clamp(confidence), "epistemic_kind": "hypothesis"})

    def add_temporary_result(self, result_id: str, content: str, *, importance: float = 0.5, metadata=None) -> dict:
        return self._set_role_item("temporary_result", result_id, content, importance=importance, metadata=metadata)

    def recent_context(self, *, limit: int = 16) -> list[dict]:
        return self.working.list(limit=max(1, min(int(limit), self.max_focus)))

    def attention_state(self) -> dict:
        if self.state is None:
            return {"status": "unknown", "source": "StarState not attached", "attention": None, "focus": None, "cognitive_load": None}
        try:
            snapshot = self.state.get_state()
        except AttributeError:
            return {"status": "unknown", "source": "invalid StarState adapter", "attention": None, "focus": None, "cognitive_load": None}
        return {
            "status": "observed",
            "source": "core.state.StarState",
            "attention": snapshot.get("attention"),
            "focus": snapshot.get("focus"),
            "cognitive_load": snapshot.get("cognitive_load"),
            "energy": snapshot.get("energy"),
        }

    @staticmethod
    def _text_tokens(value: Any) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9À-ÿ]+", _clean(value).casefold()) if len(token) > 1}

    def _match_relevance(self, content: str, items: list[dict]) -> float:
        content_tokens = self._text_tokens(content)
        if not content_tokens or not items:
            return 0.0
        best = 0.0
        for item in items:
            tokens = self._text_tokens(item.get("content", ""))
            if not tokens:
                continue
            overlap = len(content_tokens & tokens) / max(1, min(len(content_tokens), len(tokens)))
            best = max(best, overlap * (0.5 + 0.5 * float(item.get("importance", 0.5))))
        return _clamp(best)

    @staticmethod
    def _candidate_value(candidate: dict, key: str, default: float = 0.0) -> float:
        try:
            return _clamp(float(candidate.get(key, default)))
        except (TypeError, ValueError):
            return _clamp(default)

    def score(self, candidate: dict) -> dict:
        if not isinstance(candidate, dict):
            raise TypeError("candidate deve ser dict")
        content = _clean(candidate.get("content") or candidate.get("label") or candidate.get("id"))
        if not content:
            raise ValueError("candidate requer content/label/id")
        goals = self._role_items("active_goal")
        entities = self._role_items("active_entity")
        components = {
            "explicit_priority": self._candidate_value(candidate, "priority", self._candidate_value(candidate, "importance", 0.5)),
            "salience": self._candidate_value(candidate, "salience", 0.5),
            "goal_relevance": self._candidate_value(candidate, "goal_relevance", self._match_relevance(content, goals)),
            "entity_relevance": self._candidate_value(candidate, "entity_relevance", self._match_relevance(content, entities)),
            "recency": self._candidate_value(candidate, "recency", 0.5),
            "risk": self._candidate_value(candidate, "risk", 0.0),
            "urgency": self._candidate_value(candidate, "urgency", 0.0),
            "confidence": self._candidate_value(candidate, "confidence", 0.5),
        }
        score = sum(components[key] * weight for key, weight in self.WEIGHTS.items())
        return {
            "candidate": deepcopy(candidate),
            "content": content,
            "score": round(_clamp(score), 6),
            "components": components,
            "selection_is_inference": True,
            "operational_authorization": False,
        }

    def select_relevant(self, candidates: Iterable[dict], *, limit: int = 16) -> dict:
        limit = max(1, min(int(limit), self.max_focus))
        sampled = list(islice(iter(candidates), self.max_candidates + 1))
        truncated = len(sampled) > self.max_candidates
        if truncated:
            sampled = sampled[: self.max_candidates]
        scored = []
        rejected = 0
        for candidate in sampled:
            try:
                scored.append(self.score(candidate))
            except (TypeError, ValueError):
                rejected += 1
        scored.sort(key=lambda item: (item["score"], item["components"]["risk"], item["components"]["urgency"]), reverse=True)
        selected = scored[:limit]
        result = {
            "selected": selected,
            "considered": len(sampled),
            "rejected_invalid": rejected,
            "limit": limit,
            "candidate_window": self.max_candidates,
            "input_truncated": truncated,
            "loads_all_available_contents": False,
            "selection_is_inference": True,
            "operational_authorization": False,
            "selected_at": _now(),
        }
        self._last_selection = deepcopy(result)
        return result

    def select_from_memory(self, query: str, *, recall_limit: int = 64, focus_limit: int = 16) -> dict:
        recall_limit = max(1, min(int(recall_limit), self.max_candidates))
        recalled = self.memory_continuity.recall(query, limit=recall_limit)
        candidates = [
            {
                "id": item.get("id") or item.get("working_id"),
                "content": item.get("content"),
                "importance": item.get("importance", 0.5),
                "recency": 0.8 if item.get("storage") == "working" else 0.5,
                "confidence": (item.get("metadata") or {}).get("confidence", 0.5),
                "source": f"memory:{item.get('storage')}",
            }
            for item in recalled
        ]
        return self.select_relevant(candidates, limit=focus_limit)

    def snapshot(self) -> dict:
        return {
            "block": "B14",
            "attention_state": self.attention_state(),
            "active_goals": self._role_items("active_goal"),
            "active_entities": self._role_items("active_entity"),
            "hypotheses": self._role_items("hypothesis"),
            "temporary_results": self._role_items("temporary_result"),
            "recent_context": self.recent_context(limit=16),
            "last_selection": deepcopy(self._last_selection),
            "policy": deepcopy(ATTENTION_POLICY),
        }

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        domain_key = _norm(domain) if domain else None
        if domain_key and domain_key not in ATTENTION_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in ATTENTION_BRANCHES if domain_key is None or branch.domain == domain_key]
        root = self.graph.add_entity("attention_taxonomy", "WORKING MEMORY, ATTENTION E SALIENCE", node_id=self.TAXONOMY_ROOT_ID, data={"block": "B14"})
        b13 = self.graph.add_entity("attention_memory_source", "B13 Working Memory", node_id="ATTENTION-SOURCE-B13", data={"block": "B13"})
        state = self.graph.add_entity("attention_state_source", "StarState", node_id="ATTENTION-SOURCE-STATE", data={"source": "core/state.py"})
        self.graph.relate(root, b13, "uses", metadata={"block": "B14"})
        self.graph.relate(root, state, "observes", metadata={"block": "B14"})
        for branch in selected:
            domain_id = f"ATTENTION-DOM-{branch.domain.upper()}"
            branch_id = f"ATTENTION-BR-{branch.key.upper()}"
            self.graph.add_entity("attention_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B14"})
            self.graph.add_entity("attention_branch", branch.label, node_id=branch_id, data={"block": "B14", "domain": branch.domain})
            self.graph.relate(root, domain_id, "has_part", metadata={"block": "B14"})
            self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B14"})
        return {"domain": domain_key, "branches_materialized": len(selected), "knowledge_graph": "shared", "parallel_attention_graph_created": False}

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "max_candidates": self.max_candidates,
            "max_focus": self.max_focus,
            "working_memory_shared_with_b13": True,
            "state_source": "core.state.StarState",
            "parallel_working_memory": False,
            "parallel_state": False,
            "policy": deepcopy(ATTENTION_POLICY),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 14", "status attention", "status salience", "attention e salience", "atenção e saliência", "atencao e saliencia"}:
            stats = self.stats()
            snap = self.snapshot()
            return (
                f"⭐ BLOCO 14 — ATTENTION E SALIENCE: {stats['catalog']['addressable_contents']} representações endereçáveis | "
                f"janela máxima={stats['max_candidates']} candidatos | foco máximo={stats['max_focus']} | "
                f"objetivos ativos={len(snap['active_goals'])} | entidades ativas={len(snap['active_entities'])}."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
