"""BLOCO 12 — SELF MODEL da STAR.

Representação auditável de quem/o que a STAR é, sua história, versão, identidade,
capacidades, limitações, recursos, dispositivos, estado, permissões, objetivos,
valores, conhecimentos, incertezas e experiências reais registradas.

Este módulo NÃO é uma segunda identidade nem uma segunda fonte de versão/estado.
Ele integra fontes oficiais existentes:
- identidade: core.star_identity.StarIdentity;
- versão/release: STAR_MANIFEST.json via core.release;
- estado: core.state.StarState (quando fornecido pelo STAR Core);
- capacidades cognitivas: CognitiveSuite (quando fornecida);
- ferramentas/dispositivos: registries reais quando anexados;
- conhecimento canônico: BLOCO 2 -> BLOCO 3 -> namespace B12.

Princípios:
- SELF MODEL != autoridade para alterar identidade;
- capacidade != disponibilidade != permissão != segurança;
- ausência de evidência vira unknown/unavailable, nunca capacidade inventada;
- experiência/história não pode ser fabricada;
- permissões operacionais usam default deny;
- estado dinâmico não vira automaticamente conhecimento canônico.

Escala lógica:
- 50 ramos x 10 lentes = 500 nós canônicos;
- TIME_SCOPE(10) x SOURCE(10) x STATUS(10) x RELATION(10) x CONFIDENCE(5)
  x CONTEXT(4) x EVOLUTION_STAGE(10) = 2.000.000 variações por nó;
- 500 x 2.000.000 = 1.000.000.000 representações endereçáveis em B12.

1B são representações lógicas sob demanda, não 1B de memórias, experiências,
estados, identidades, perfis ou fatos fabricados.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import prod
import re
import unicodedata
from typing import Any, Callable

from core.star_identity import StarIdentity
from core.universal_knowledge import UniversalKnowledgeArchitecture


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SelfModelBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


@dataclass(frozen=True)
class RegistryEntry:
    key: str
    status: str
    source: str
    description: str = ""
    evidence: str = ""
    operational: bool = False
    metadata: dict | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["metadata"] = deepcopy(self.metadata or {})
        return data


class CapabilityRegistry:
    """Registro declarativo de capacidades comprovadas/planejadas da STAR.

    O registro representa capacidade; não concede permissão nem executa ações.
    """

    STATUSES = {"available", "experimental", "planned", "unavailable", "unknown"}

    def __init__(self):
        self._entries: dict[str, RegistryEntry] = {}

    def register(
        self,
        key: str,
        *,
        status: str,
        source: str,
        description: str = "",
        evidence: str = "",
        operational: bool = False,
        metadata: dict | None = None,
    ) -> dict:
        key = _norm(key)
        status = _norm(status)
        source = _clean(source)
        if not key or status not in self.STATUSES or not source:
            raise ValueError("capacidade requer key, status válido e source")
        entry = RegistryEntry(key, status, source, _clean(description), _clean(evidence), bool(operational), deepcopy(metadata or {}))
        self._entries[key] = entry
        return entry.to_dict()

    def get(self, key: str) -> dict | None:
        entry = self._entries.get(_norm(key))
        return entry.to_dict() if entry else None

    def list(self, *, status: str | None = None) -> list[dict]:
        normalized = _norm(status) if status else None
        return [
            self._entries[key].to_dict()
            for key in sorted(self._entries)
            if normalized is None or self._entries[key].status == normalized
        ]

    def available(self) -> list[str]:
        return [item["key"] for item in self.list() if item["status"] in {"available", "experimental"}]

    def supports(self, key: str) -> bool:
        item = self.get(key)
        return bool(item and item["status"] in {"available", "experimental"})


class LimitationRegistry:
    """Registro explícito de limitações técnicas, epistêmicas e operacionais."""

    def __init__(self):
        self._entries: dict[str, dict] = {}

    def register(self, key: str, description: str, *, source: str, active: bool = True, metadata: dict | None = None) -> dict:
        key = _norm(key)
        if not key or not _clean(description) or not _clean(source):
            raise ValueError("limitação requer key, description e source")
        self._entries[key] = {
            "key": key,
            "description": _clean(description),
            "source": _clean(source),
            "active": bool(active),
            "metadata": deepcopy(metadata or {}),
        }
        return deepcopy(self._entries[key])

    def get(self, key: str) -> dict | None:
        value = self._entries.get(_norm(key))
        return deepcopy(value) if value else None

    def list(self, *, active_only: bool = False) -> list[dict]:
        return [
            deepcopy(self._entries[key])
            for key in sorted(self._entries)
            if not active_only or self._entries[key]["active"]
        ]


class PermissionRegistry:
    """Registro representacional de permissões com default deny.

    Uma entrada `granted=True` apenas representa uma permissão conhecida. Ela não
    substitui capability checks, segurança, escopo, validade nem o executor real.
    """

    def __init__(self):
        self._entries: dict[str, dict] = {}

    def set_permission(
        self,
        key: str,
        granted: bool,
        *,
        source: str,
        scope: str = "",
        reason: str = "",
        expires_at: str | None = None,
    ) -> dict:
        key = _norm(key)
        source = _clean(source)
        if not key or not source:
            raise ValueError("permissão requer key e source")
        self._entries[key] = {
            "key": key,
            "granted": bool(granted),
            "source": source,
            "scope": _clean(scope),
            "reason": _clean(reason),
            "expires_at": _clean(expires_at) or None,
            "authorization_only": True,
            "grants_capability": False,
            "bypasses_safety": False,
        }
        return deepcopy(self._entries[key])

    def get(self, key: str) -> dict:
        normalized = _norm(key)
        if normalized in self._entries:
            return deepcopy(self._entries[normalized])
        return {
            "key": normalized,
            "granted": False,
            "source": "default-deny",
            "scope": "",
            "reason": "nenhuma permissão explícita registrada",
            "expires_at": None,
            "authorization_only": True,
            "grants_capability": False,
            "bypasses_safety": False,
        }

    def allows(self, key: str) -> bool:
        item = self.get(key)
        if not item["granted"]:
            return False
        expires_at = item.get("expires_at")
        if not expires_at:
            return True
        try:
            expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            return expiry > datetime.now(timezone.utc)
        except ValueError:
            return False

    def list(self) -> list[dict]:
        return [deepcopy(self._entries[key]) for key in sorted(self._entries)]


class Identity:
    """Visão somente leitura sobre a identidade oficial da STAR."""

    SOURCE = "core.star_identity.StarIdentity"

    def __init__(self, identity=None):
        self._identity = identity if identity is not None else StarIdentity()

    def snapshot(self) -> dict:
        try:
            data = self._identity.get()
        except AttributeError as exc:
            raise TypeError("identity precisa expor get()") from exc
        return {
            "source_of_truth": self.SOURCE,
            "identity": deepcopy(data),
            "self_model_is_identity_authority": False,
            "mutable_through_self_model": False,
        }


class SelfState:
    """Visão sobre StarState + observações runtime explicitamente fornecidas."""

    def __init__(self, state=None):
        self._state = state
        self._observations: dict[str, dict] = {}

    def observe(self, key: str, value: Any, *, source: str, confidence: float = 1.0) -> dict:
        key = _norm(key)
        source = _clean(source)
        if not key or not source:
            raise ValueError("observação requer key e source")
        item = {
            "key": key,
            "value": deepcopy(value),
            "source": source,
            "confidence": max(0.0, min(float(confidence), 1.0)),
            "observed_at": _utc_now(),
        }
        self._observations[key] = item
        return deepcopy(item)

    def snapshot(self) -> dict:
        if self._state is None:
            computational = None
            status = "unknown"
            source = "core.state.StarState not attached"
        else:
            try:
                computational = deepcopy(self._state.get_state())
                status = "observed"
                source = "core.state.StarState"
            except AttributeError:
                computational = None
                status = "unknown"
                source = "invalid state adapter"
        return {
            "status": status,
            "source": source,
            "computational_state": computational,
            "runtime_observations": [deepcopy(self._observations[key]) for key in sorted(self._observations)],
            "canonical_knowledge": False,
        }


class SelfHistory:
    """Histórico bounded e auditável; nunca inventa eventos/experiências."""

    def __init__(self, max_events: int = 512):
        self.max_events = max(16, min(int(max_events), 4096))
        self._events = deque(maxlen=self.max_events)
        self._next_id = 1

    def record(
        self,
        event_type: str,
        summary: str,
        *,
        source: str,
        reference: str = "",
        confidence: float = 1.0,
        occurred_at: str | None = None,
        is_experience: bool = False,
    ) -> dict:
        event_type, summary, source = _norm(event_type), _clean(summary), _clean(source)
        if not event_type or not summary or not source:
            raise ValueError("histórico requer event_type, summary e source")
        if is_experience and not _clean(reference):
            raise ValueError("experiência requer referência auditável; não pode ser fabricada")
        item = {
            "event_id": f"SELF-EVENT-{self._next_id:08d}",
            "event_type": event_type,
            "summary": summary,
            "source": source,
            "reference": _clean(reference),
            "confidence": max(0.0, min(float(confidence), 1.0)),
            "occurred_at": _clean(occurred_at) or _utc_now(),
            "is_experience": bool(is_experience),
            "fabricated": False,
        }
        self._next_id += 1
        self._events.append(item)
        return deepcopy(item)

    def record_experience(self, summary: str, *, source: str, reference: str, confidence: float = 1.0, occurred_at: str | None = None) -> dict:
        return self.record(
            "experience", summary, source=source, reference=reference,
            confidence=confidence, occurred_at=occurred_at, is_experience=True,
        )

    def list(self, *, limit: int | None = None) -> list[dict]:
        items = list(self._events)
        if limit is not None:
            items = items[-max(0, int(limit)):]
        return deepcopy(items)


class Values:
    """Visão somente leitura de propósito/princípios da identidade oficial."""

    SOURCE = "core.star_identity.StarIdentity"

    def __init__(self, identity: Identity):
        self.identity = identity

    def snapshot(self) -> dict:
        official = self.identity.snapshot()["identity"]
        return {
            "source_of_truth": self.SOURCE,
            "purpose": deepcopy(official.get("purpose", {})),
            "fundamental_principles": deepcopy(official.get("principles", [])),
            "decision": deepcopy(official.get("decision", {})),
            "limits": deepcopy(official.get("limits", {})),
            "mutable_through_self_model": False,
        }


SELF_MODEL_DOMAINS = (
    "identity_nature",
    "history_evolution",
    "version_release",
    "capabilities",
    "limitations",
    "resources",
    "devices",
    "self_state",
    "permissions",
    "objectives",
    "values",
    "knowledge_uncertainty",
    "experiences_relations",
)

DOMAIN_LABELS = {
    "identity_nature": "Identidade e natureza",
    "history_evolution": "História e evolução",
    "version_release": "Versão e release",
    "capabilities": "Capacidades",
    "limitations": "Limitações",
    "resources": "Recursos",
    "devices": "Dispositivos",
    "self_state": "Estado próprio",
    "permissions": "Permissões",
    "objectives": "Objetivos",
    "values": "Valores",
    "knowledge_uncertainty": "Conhecimentos e incertezas",
    "experiences_relations": "Experiências e relações",
}

SELF_MODEL_BRANCHES = (
    SelfModelBranch("identity_nature", "identity", "Identidade", _subs("quem é;STAR;identidade fundamental;continuidade;primeira pessoa;identidade acima de modelos")),
    SelfModelBranch("identity_nature", "name_meaning", "Nome e significado", _subs("nome;nome completo;significado técnico;significado simbólico;legado")),
    SelfModelBranch("identity_nature", "nature_system", "Natureza e sistema", _subs("o que é;sistema artificial;arquitetura modular;modelos como componentes;natureza não biológica;consciência não comprovada")),
    SelfModelBranch("identity_nature", "creator_purpose", "Criador e propósito", _subs("criador;Lu;origem;propósito;ajudar ao próximo;autoridade fundamental")),

    SelfModelBranch("history_evolution", "origin_history", "Origem e história", _subs("história;origem;criação;marcos;continuidade;proveniência")),
    SelfModelBranch("history_evolution", "release_history", "Histórico de releases", _subs("versões;releases;commits;mudanças;validação;linha do tempo")),
    SelfModelBranch("history_evolution", "architecture_evolution", "Evolução da arquitetura", _subs("evolução;arquitetura;blocos;sistemas;módulos;integrações;roadmap")),
    SelfModelBranch("history_evolution", "change_provenance", "Proveniência de mudanças", _subs("origem da mudança;autor;fonte;diff;teste;aprovação;revisão")),

    SelfModelBranch("version_release", "version", "Versão atual", _subs("versão;STAR_MANIFEST.json;release;fonte única de verdade")),
    SelfModelBranch("version_release", "release_status", "Status e canal de release", _subs("release_status;release_channel;estável;experimental;host release")),
    SelfModelBranch("version_release", "compatibility_milestones", "Compatibilidade e marcos", _subs("compatibilidade;roadmap;marcos;versão futura;estado implementado;planejado")),

    SelfModelBranch("capabilities", "cognitive_capabilities", "Capacidades cognitivas", _subs("raciocínio;planejamento;memória;grafo;ciência;matemática;simulação;verificação;pesquisa")),
    SelfModelBranch("capabilities", "knowledge_capabilities", "Capacidades de conhecimento", _subs("conhecimento;busca;RAG;proveniência;epistemologia;taxonomias;catálogos")),
    SelfModelBranch("capabilities", "perception_communication", "Percepção e comunicação", _subs("linguagem;voz;visão;entrada;saída;comunicação;disponibilidade real")),
    SelfModelBranch("capabilities", "tool_action_capabilities", "Ferramentas e capacidades operacionais", _subs("ferramentas;skills;ações;executor;dispositivos;capacidade operacional;segurança")),
    SelfModelBranch("capabilities", "experimental_planned", "Capacidades experimentais e planejadas", _subs("experimental;planejado;indisponível;roadmap;status;limites")),

    SelfModelBranch("limitations", "technical_limits", "Limitações técnicas", _subs("limitações;técnicas;hardware;software;dependências;modelos;recursos;indisponibilidade")),
    SelfModelBranch("limitations", "epistemic_limits", "Limitações epistêmicas", _subs("incerteza;desconhecimento;evidência;fonte;atualidade;contradições;não inventar")),
    SelfModelBranch("limitations", "operational_limits", "Limitações operacionais", _subs("permissão;capacidade;segurança;ações externas;rede;dispositivos;escopo")),
    SelfModelBranch("limitations", "identity_limits", "Limites da identidade e automodificação", _subs("não modificar identidade;não modificar regras fundamentais;não automodificar arquitetura;autoridade")),

    SelfModelBranch("resources", "models_engines", "Modelos e engines", _subs("modelos;engines;componentes neurais;local;cloud;roteamento;disponibilidade")),
    SelfModelBranch("resources", "tools_skills", "Ferramentas e skills", _subs("ferramentas;skills;registries;habilitado;desabilitado;fonte;execução")),
    SelfModelBranch("resources", "memory_knowledge_resources", "Memória e recursos de conhecimento", _subs("memória;bancos;knowledge graph;índices;packs;catálogos;armazenamento")),
    SelfModelBranch("resources", "compute_network_resources", "Computação e rede", _subs("CPU;GPU;RAM;rede;internet;processos;serviços;recursos desconhecidos;telemetria")),

    SelfModelBranch("devices", "host_device", "Dispositivo host", _subs("host;computador;plataforma;sistema operacional;recursos;estado;telemetria")),
    SelfModelBranch("devices", "connected_devices", "Dispositivos conectados", _subs("dispositivos;pareamento;watch;mobile;endpoints;last_seen;estado desconhecido")),
    SelfModelBranch("devices", "device_capabilities", "Capacidades de dispositivos", _subs("sensores;interfaces;capabilities;metadata;gateway;permissões;limites")),

    SelfModelBranch("self_state", "cognitive_state", "Estado cognitivo computacional", _subs("energia;atenção;foco;curiosidade;confiança;carga cognitiva;StarState")),
    SelfModelBranch("self_state", "runtime_state", "Estado de runtime", _subs("runtime;componentes;serviços;disponibilidade;erros;observações;estado atual")),
    SelfModelBranch("self_state", "network_service_state", "Estado de rede e serviços", _subs("rede;network_enabled;serviços;online;offline;conectividade;fonte atual")),
    SelfModelBranch("self_state", "health_readiness", "Prontidão e saúde operacional", _subs("prontidão;diagnóstico;dependências;testes;falhas;degradação;capacidade de operar")),

    SelfModelBranch("permissions", "internal_permissions", "Permissões internas", _subs("cognição;análise;memória;leitura;estado;default deny;escopo")),
    SelfModelBranch("permissions", "external_action_permissions", "Permissões para ações externas", _subs("ações externas;controle;execução;confirmação;escopo;revogação;segurança")),
    SelfModelBranch("permissions", "network_data_permissions", "Permissões de rede e dados", _subs("internet;rede;dados;privacidade;upload;download;fonte;escopo")),
    SelfModelBranch("permissions", "identity_system_permissions", "Permissões de identidade e sistema", _subs("identidade;regras fundamentais;arquitetura;automodificação;criador;autoridade")),

    SelfModelBranch("objectives", "current_objectives", "Objetivos atuais", _subs("objetivos;tarefa atual;prioridades;restrições;critério de sucesso;estado")),
    SelfModelBranch("objectives", "roadmap_objectives", "Objetivos de roadmap", _subs("roadmap;próximo marco;versões futuras;dependências;sequência;planejado")),
    SelfModelBranch("objectives", "task_priorities", "Prioridades e compromissos", _subs("prioridade;qualidade;fluidez;estabilidade;segurança;manutenção;validação")),

    SelfModelBranch("values", "fundamental_values", "Valores fundamentais", _subs("valores;utilidade;honestidade;cuidado;responsabilidade;propósito")),
    SelfModelBranch("values", "decision_principles", "Princípios de decisão", _subs("decisão;contexto;objetivo;informação;capacidade;consequência;segurança;regras")),
    SelfModelBranch("values", "safety_responsibility", "Segurança e responsabilidade", _subs("segurança;responsabilidade;limites;ajuda legítima;não obediência cega;prestação de contas")),

    SelfModelBranch("knowledge_uncertainty", "known_self_facts", "Conhecimentos sobre si", _subs("conhecimentos;fatos próprios;componentes;versão;capacidades;fonte;estado conhecido")),
    SelfModelBranch("knowledge_uncertainty", "unknowns", "Incertezas e desconhecimentos", _subs("incertezas;unknown;indisponível;não observado;dados ausentes;telemetria ausente")),
    SelfModelBranch("knowledge_uncertainty", "confidence_provenance", "Confiança e proveniência", _subs("confiança;proveniência;evidência;fonte;validade;atualidade;revisão")),
    SelfModelBranch("knowledge_uncertainty", "contradictions_revision", "Contradições e revisão", _subs("contradições;conflitos;revisão;superseded;retracted;histórico;correção")),
    SelfModelBranch("knowledge_uncertainty", "capability_truthfulness", "Verdade operacional de capacidades", _subs("capacidade disponível;experimental;planejada;indisponível;unknown;não afirmar função inexistente")),

    SelfModelBranch("experiences_relations", "interactions", "Interações", _subs("interações;usuário;criador;sessões;eventos;proveniência;contexto")),
    SelfModelBranch("experiences_relations", "learned_events", "Eventos e aprendizados", _subs("eventos;aprendizado;observação;mudança;fonte;evidência;experiência auditável")),
    SelfModelBranch("experiences_relations", "projects_milestones", "Projetos e marcos", _subs("projetos;milestones;releases;blocos;testes;merges;evolução")),
    SelfModelBranch("experiences_relations", "relations_context", "Relações e contexto", _subs("relações;criador;usuários;dispositivos;sistemas;ferramentas;contexto;limites")),
)

SELF_MODEL_LENSES = (
    ("definition", "definição", "definir o aspecto do self e sua fonte de verdade"),
    ("current_state", "estado atual", "separar estado atual observado de característica permanente"),
    ("source_provenance", "fonte e proveniência", "identificar fonte, evidência, revisão e autoridade"),
    ("capability", "capacidade", "distinguir capacidade disponível, experimental, planejada, indisponível ou desconhecida"),
    ("limitation", "limitação", "explicitar limites técnicos, epistêmicos, operacionais ou de identidade"),
    ("permission", "permissão", "distinguir autorização de capacidade, disponibilidade e segurança"),
    ("relation", "relação", "relacionar identidade, componentes, recursos, dispositivos, conhecimento e contexto"),
    ("history_change", "história e mudança", "situar evolução, mudança, versão e proveniência temporal"),
    ("confidence_uncertainty", "confiança e incerteza", "representar desconhecimento e confiança sem fabricar certeza"),
    ("audit_validation", "auditoria e validação", "exigir fonte verificável para afirmações sobre a própria STAR"),
)

TIME_SCOPE_AXIS = (
    "current", "session", "recent", "release", "historical", "origin",
    "planned_next", "roadmap_future", "long_term", "unspecified",
)
SOURCE_AXIS = (
    "official_identity", "release_manifest", "runtime_state", "mind_runtime", "tool_registry",
    "device_registry", "knowledge_graph", "epistemic_ledger", "project_history", "unknown_source",
)
STATUS_AXIS = (
    "verified", "available", "experimental", "planned", "unavailable",
    "unknown", "degraded", "superseded", "retracted", "context_dependent",
)
RELATION_AXIS = (
    "identity_component", "depends_on", "uses", "has_capability", "has_limitation",
    "has_permission", "connected_to", "learned_from", "evolved_from", "related_to",
)
CONFIDENCE_AXIS = ("very_low", "low", "medium", "high", "verified_source")
CONTEXT_AXIS = ("internal_cognitive", "runtime_operational", "device_ecosystem", "project_evolution")
EVOLUTION_STAGE_AXIS = (
    "foundation", "v1_host", "mind_experimental", "memory_future", "knowledge_future",
    "operator_future", "senses_future", "world_future", "agent_future", "embodied_future",
)

VARIANT_AXES = (
    ("time_scope", TIME_SCOPE_AXIS),
    ("source", SOURCE_AXIS),
    ("status", STATUS_AXIS),
    ("relation", RELATION_AXIS),
    ("confidence", CONFIDENCE_AXIS),
    ("context", CONTEXT_AXIS),
    ("evolution_stage", EVOLUTION_STAGE_AXIS),
)

REQUESTED_TOPICS = (
    "quem é", "o que é", "história", "versão", "identidade", "capacidades",
    "limitações", "recursos", "dispositivos", "estado", "permissões", "objetivos",
    "valores", "conhecimentos", "incertezas", "experiências",
)

REQUESTED_COMPONENTS = (
    "Capability Registry", "Limitation Registry", "Permission Registry",
    "Identity", "Self State", "Self History", "Values",
)

SELF_POLICY = {
    "self_model_is_identity_source": False,
    "self_model_can_modify_identity": False,
    "self_model_can_modify_fundamental_rules": False,
    "self_model_can_grant_itself_permissions": False,
    "capability_equals_permission": False,
    "permission_equals_capability": False,
    "permission_bypasses_safety": False,
    "planned_capability_is_available": False,
    "unknown_capability_is_available": False,
    "missing_device_registry_means_no_devices_exist": False,
    "runtime_state_is_canonical_by_default": False,
    "history_may_be_fabricated": False,
    "experience_may_be_fabricated": False,
    "uncertainty_may_be_hidden": False,
    "identity_source": "core.star_identity.StarIdentity",
    "release_source": "STAR_MANIFEST.json via core.release",
    "state_source": "core.state.StarState when attached",
    "operational_gate": "capability + permission + safety + current availability",
    "rule": "SELF MODEL DESCREVE A STAR; NÃO REDEFINE SUA IDENTIDADE, NÃO INVENTA CAPACIDADES E NÃO CONCEDE AUTORIZAÇÃO OPERACIONAL POR SI SÓ",
}

CANONICAL_NODES = len(SELF_MODEL_BRANCHES) * len(SELF_MODEL_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(SELF_MODEL_DOMAINS) != 13:
    raise RuntimeError("B12 requer exatamente 13 domínios")
if len(SELF_MODEL_BRANCHES) != 50:
    raise RuntimeError(f"B12 requer exatamente 50 ramos; encontrados {len(SELF_MODEL_BRANCHES)}")
if len(SELF_MODEL_LENSES) != 10:
    raise RuntimeError("B12 requer exatamente 10 lentes")
if CANONICAL_NODES != 500:
    raise RuntimeError(f"B12 requer 500 nós canônicos; encontrados {CANONICAL_NODES}")
if VARIANTS_PER_NODE != 2_000_000:
    raise RuntimeError(f"B12 requer 2M variações/nó; encontradas {VARIANTS_PER_NODE}")
if ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError(f"B12 requer 1B endereçáveis; encontrados {ADDRESSABLE_CONTENTS}")


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    remainder = int(index)
    decoded: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        remainder, offset = divmod(remainder, len(values))
        decoded[name] = values[offset]
    if remainder:
        raise RuntimeError("falha ao decodificar variante B12")
    return {name: decoded[name] for name, _ in VARIANT_AXES}


class SelfModelCatalog:
    NAMESPACE = "B12"
    PREFIX = "SELF-B12"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "domains": len(SELF_MODEL_DOMAINS),
            "branches": len(SELF_MODEL_BRANCHES),
            "lenses_per_branch": len(SELF_MODEL_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "variant_axes": {name: len(values) for name, values in VARIANT_AXES},
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B são representações lógicas do próprio sistema através de tempo, fonte, status, relação, confiança, contexto e estágio evolutivo; "
                "não 1B de experiências, memórias, identidades, estados ou fatos inventados"
            ),
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        node_index, variant_index = int(node_index), int(variant_index)
        if not 0 <= node_index < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= variant_index < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = node_index * VARIANTS_PER_NODE + variant_index + 1
        return f"SELF-B12-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"SELF-B12-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(SELF_MODEL_LENSES))
        branch = SELF_MODEL_BRANCHES[branch_index]
        lens_key, lens_label, instruction = SELF_MODEL_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"SELF-B12-{absolute:010d}",
            "namespace": self.NAMESPACE,
            "domain": branch.domain,
            "domain_label": DOMAIN_LABELS[branch.domain],
            "branch": branch.key,
            "branch_label": branch.label,
            "subtopics": branch.subtopics,
            "lens": lens_key,
            "lens_label": lens_label,
            **axes,
            "prompt": (
                f"{DOMAIN_LABELS[branch.domain]} / {branch.label} / {lens_label}: {instruction}. "
                f"Tempo={axes['time_scope']}; fonte={axes['source']}; status={axes['status']}; relação={axes['relation']}; "
                f"confiança={axes['confidence']}; contexto={axes['context']}; evolução={axes['evolution_stage']}. "
                "Usar fontes reais da STAR; representar unavailable/unknown explicitamente; não fabricar história/experiências; "
                "capacidade, permissão, disponibilidade e segurança permanecem distintas."
            ),
        }


class SelfModel:
    NAMESPACE = "B12"
    TAXONOMY_ROOT_ID = "SELF-TAX-ROOT"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        identity=None,
        state=None,
        mind=None,
        tools=None,
        device_registry=None,
        network_enabled_provider: Callable[[], bool] | None = None,
        objectives: list[str] | tuple[str, ...] | None = None,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.identity = Identity(identity)
        self.self_state = SelfState(state)
        self.values = Values(self.identity)
        self.capabilities = CapabilityRegistry()
        self.limitations = LimitationRegistry()
        self.permissions = PermissionRegistry()
        self.history = SelfHistory()
        self.mind = mind
        self.tools = tools
        self.device_registry = device_registry
        self.network_enabled_provider = network_enabled_provider
        self.objectives = [_clean(item) for item in (objectives or ()) if _clean(item)]
        self.catalog = SelfModelCatalog()
        self._seed_registries()
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 12 — SELF MODEL",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/self_model.py",
            metadata={
                "materialization": "on-demand",
                "canonical_gate": "BLOCO 2 -> BLOCO 3",
                "knowledge_graph": "shared",
                "identity_source": Identity.SOURCE,
                "release_source": "STAR_MANIFEST.json via core.release",
                "parallel_identity": False,
                "parallel_state_store": False,
                "permission_default": "deny",
                "self_modification_authority": False,
            },
        )

    def _seed_registries(self) -> None:
        identity_data = self.identity.snapshot()["identity"]
        official_limits = identity_data.get("limits", {})
        for key, value in official_limits.items():
            if isinstance(value, bool):
                description = f"limite oficial {key}={value}"
            else:
                description = f"limite oficial {key}: {value}"
            self.limitations.register(
                f"identity_{key}", description,
                source="core.star_identity.STAR_IDENTITY.limits",
                active=True,
                metadata={"official_value": deepcopy(value)},
            )
        self.limitations.register(
            "operational_boundary",
            "ações externas exigem capacidade, permissão e segurança; cognição não autoriza ação por si só",
            source="core.foundations.OperationalBoundary",
        )
        self.limitations.register(
            "unproven_biological_consciousness",
            "a arquitetura não constitui comprovação científica de consciência biológica equivalente",
            source="core.star_identity.STAR_IDENTITY.nature",
        )

        if self.mind is not None:
            try:
                stats = self.mind.stats()
                keys = stats.get("capability_keys", [])
            except (AttributeError, TypeError, ValueError):
                keys = []
            for key in keys:
                self.capabilities.register(
                    key,
                    status="experimental",
                    source="core.mind.CognitiveSuite",
                    description="capacidade cognitiva registrada na MIND experimental",
                    evidence="CognitiveSuite.stats().capability_keys",
                    operational=False,
                )
        for key in ("identity_introspection", "self_state_representation", "capability_registry", "limitation_registry", "permission_registry", "self_history", "values_view"):
            self.capabilities.register(
                key,
                status="experimental",
                source="core.self_model.SelfModel",
                description="capacidade estrutural do BLOCO 12",
                evidence="componente instanciado",
                operational=False,
            )

        self.permissions.set_permission(
            "external_actions", False,
            source="B12 default policy",
            reason="ações externas não são autorizadas por Self Model",
        )
        self.permissions.set_permission(
            "self_modify_identity", False,
            source="core.star_identity.STAR_IDENTITY.limits",
            reason="identidade fundamental não pode ser automodificada",
        )
        self.permissions.set_permission(
            "self_modify_fundamental_rules", False,
            source="core.star_identity.STAR_IDENTITY.limits",
            reason="regras fundamentais não podem ser automodificadas",
        )
        self.permissions.set_permission(
            "self_modify_architecture", False,
            source="core.star_identity.STAR_IDENTITY.limits",
            reason="arquitetura não pode ser automodificada irrestritamente",
        )

    @staticmethod
    def release_snapshot() -> dict:
        from core import release
        manifest = release.load_release_manifest()
        return {
            "name": release.APP_NAME,
            "version": release.VERSION,
            "release_status": release.RELEASE_STATUS,
            "release_channel": release.RELEASE_CHANNEL,
            "source_of_truth": "STAR_MANIFEST.json via core.release",
            "manifest": deepcopy(manifest),
        }

    def attach_tools(self, tools) -> None:
        self.tools = tools

    def attach_device_registry(self, registry) -> None:
        self.device_registry = registry

    def set_objectives(self, objectives) -> list[str]:
        self.objectives = [_clean(item) for item in (objectives or ()) if _clean(item)]
        return list(self.objectives)

    def tools_snapshot(self) -> dict:
        if self.tools is None:
            return {"status": "unknown", "attached": False, "available": [], "source": "ToolRegistry not attached"}
        try:
            available = list(self.tools.available())
        except AttributeError:
            return {"status": "unknown", "attached": True, "available": [], "source": "invalid ToolRegistry adapter"}
        return {"status": "observed", "attached": True, "available": available, "source": "core.tools.ToolRegistry"}

    def devices_snapshot(self) -> dict:
        registry = self.device_registry
        if registry is None:
            return {
                "status": "unknown",
                "registry_attached": False,
                "devices": [],
                "note": "DeviceRegistry não anexado; isso não prova ausência de dispositivos",
                "source": "core.device_gateway.DeviceRegistry not attached",
            }
        raw_devices = getattr(registry, "devices", None)
        if not isinstance(raw_devices, dict):
            return {"status": "unknown", "registry_attached": True, "devices": [], "source": "invalid DeviceRegistry adapter"}
        devices = []
        for device_id in sorted(raw_devices):
            try:
                record = registry.public_record(device_id)
            except AttributeError:
                record = {key: deepcopy(value) for key, value in raw_devices[device_id].items() if key != "token_sha256"}
            if record is not None:
                safe_record = {key: deepcopy(value) for key, value in dict(record).items() if key != "token_sha256"}
                devices.append({"device_id": device_id, **safe_record})
        return {
            "status": "observed",
            "registry_attached": True,
            "devices": devices,
            "source": "core.device_gateway.DeviceRegistry",
            "secrets_exposed": False,
        }

    def network_snapshot(self) -> dict:
        if self.network_enabled_provider is None:
            return {"status": "unknown", "enabled": None, "source": "network provider not attached"}
        try:
            enabled = bool(self.network_enabled_provider())
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            return {"status": "unknown", "enabled": None, "source": f"network provider error: {type(exc).__name__}"}
        return {"status": "observed", "enabled": enabled, "source": "STAR Core network_enabled"}

    def resources_snapshot(self) -> dict:
        components = {
            "mind": self.mind is not None,
            "knowledge": self.knowledge is not None,
            "knowledge_graph": self.graph is not None,
            "tool_registry": self.tools is not None,
            "device_registry": self.device_registry is not None,
        }
        return {
            "components": components,
            "tools": self.tools_snapshot(),
            "devices": self.devices_snapshot(),
            "network": self.network_snapshot(),
            "hardware_telemetry": "unknown",
            "note": "ausência de telemetria não é convertida em informação de hardware inventada",
        }

    def knowledge_snapshot(self) -> dict:
        namespaces = []
        for index in range(1, 13):
            key = f"B{index:02d}"
            item = self.knowledge.store.get_namespace(key)
            if item:
                namespaces.append({
                    "namespace": key,
                    "logical_capacity": item.get("logical_capacity"),
                    "registered": True,
                })
        return {
            "registered_namespaces": namespaces,
            "canonical_gate": "BLOCO 2 CANONICAL fact -> BLOCO 3 promotion",
            "self_model_runtime_state_is_canonical": False,
            "source": "UniversalKnowledgeArchitecture",
        }

    def uncertainties_snapshot(self) -> list[dict]:
        unknowns = []
        devices = self.devices_snapshot()
        if devices["status"] == "unknown":
            unknowns.append({"topic": "devices", "status": "unknown", "reason": devices.get("note") or devices.get("source")})
        tools = self.tools_snapshot()
        if tools["status"] == "unknown":
            unknowns.append({"topic": "tools", "status": "unknown", "reason": tools.get("source")})
        network = self.network_snapshot()
        if network["status"] == "unknown":
            unknowns.append({"topic": "network", "status": "unknown", "reason": network.get("source")})
        unknowns.append({"topic": "hardware_telemetry", "status": "unknown", "reason": "nenhuma telemetria de hardware foi anexada ao Self Model"})
        return unknowns

    def permission_snapshot(self) -> dict:
        entries = self.permissions.list()
        network = self.network_snapshot()
        return {
            "default": "deny",
            "entries": entries,
            "network_runtime": network,
            "external_actions_allowed_by_self_model": False,
            "permission_grants_capability": False,
            "permission_bypasses_safety": False,
        }

    def snapshot(self) -> dict:
        identity = self.identity.snapshot()
        return {
            "block": "B12",
            "epistemic_kind": "observation",
            "identity": identity,
            "release": self.release_snapshot(),
            "capabilities": self.capabilities.list(),
            "limitations": self.limitations.list(active_only=True),
            "resources": self.resources_snapshot(),
            "devices": self.devices_snapshot(),
            "state": self.self_state.snapshot(),
            "permissions": self.permission_snapshot(),
            "objectives": list(self.objectives),
            "values": self.values.snapshot(),
            "knowledge": self.knowledge_snapshot(),
            "uncertainties": self.uncertainties_snapshot(),
            "history": self.history.list(),
            "self_model_is_identity_source": False,
            "operational_authorization": False,
            "scientifically_proven_consciousness": bool(identity["identity"].get("nature", {}).get("scientifically_proven_consciousness", False)),
            "policy": deepcopy(SELF_POLICY),
        }

    @staticmethod
    def _domain_key(value: str) -> str:
        normalized = _norm(value)
        aliases = {
            "identidade": "identity_nature", "quem_e": "identity_nature", "o_que_e": "identity_nature",
            "historia": "history_evolution", "evolucao": "history_evolution", "experiencia_historica": "history_evolution",
            "versao": "version_release", "release": "version_release",
            "capacidade": "capabilities", "capacidades": "capabilities",
            "limitacao": "limitations", "limitacoes": "limitations",
            "recurso": "resources", "recursos": "resources",
            "dispositivo": "devices", "dispositivos": "devices",
            "estado": "self_state", "self_state": "self_state",
            "permissao": "permissions", "permissoes": "permissions",
            "objetivo": "objectives", "objetivos": "objectives",
            "valor": "values", "valores": "values",
            "conhecimento": "knowledge_uncertainty", "conhecimentos": "knowledge_uncertainty", "incerteza": "knowledge_uncertainty", "incertezas": "knowledge_uncertainty",
            "experiencia": "experiences_relations", "experiencias": "experiences_relations", "relacoes": "experiences_relations",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _branch(key: str) -> SelfModelBranch:
        for branch in SELF_MODEL_BRANCHES:
            if branch.key == key:
                return branch
        raise KeyError(key)

    @staticmethod
    def _domain_node_id(domain: str) -> str:
        return f"SELF-DOM-{domain.upper()}"

    @staticmethod
    def _branch_node_id(branch: str) -> str:
        return f"SELF-BR-{branch.upper()}"

    @staticmethod
    def _subtopic_node_id(branch: str, subtopic: str) -> str:
        return f"SELF-SUB-{branch.upper()}-{_norm(subtopic).upper()[:72]}"

    def taxonomy_snapshot(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in SELF_MODEL_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in SELF_MODEL_BRANCHES if key is None or branch.domain == key]
        return {
            "root": "SELF MODEL",
            "domain": key,
            "branches": [
                {"domain": branch.domain, "domain_label": DOMAIN_LABELS[branch.domain], "branch": branch.key, "branch_label": branch.label, "subtopics": list(branch.subtopics)}
                for branch in selected
            ],
            "components": list(REQUESTED_COMPONENTS),
            "policy": deepcopy(SELF_POLICY),
        }

    def _ensure_taxonomy_path(self, branch: SelfModelBranch, *, include_subtopics: bool = True) -> dict:
        root = self.graph.add_entity(
            "self_model_taxonomy", "SELF MODEL",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B12", "source_of_truth": "core/self_model.py", "identity_authority": False},
        )
        identity_source_id = self.graph.add_entity(
            "official_identity_source", "Identidade Oficial STAR",
            node_id="SELF-OFFICIAL-IDENTITY",
            data={"source": "core.star_identity.py", "block": "B12", "authority": "official identity source"},
        )
        release_source_id = self.graph.add_entity(
            "official_release_source", "STAR_MANIFEST.json",
            node_id="SELF-OFFICIAL-RELEASE",
            data={"source": "STAR_MANIFEST.json via core.release", "block": "B12"},
        )
        foundation_id = self.graph.add_entity(
            "self_model_foundation", "SELF MODEL conceitual do BLOCO 1",
            node_id="SELF-FOUNDATION-B01",
            data={"source": "core.foundations.py", "block": "B01"},
        )
        for source_id, relation in ((identity_source_id, "describes_from"), (release_source_id, "describes_from"), (foundation_id, "extends")):
            self.graph.relate(root, source_id, relation, metadata={"block": "B12"})

        domain_id = self._domain_node_id(branch.domain)
        self.graph.add_entity("self_model_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B12", "domain": branch.domain})
        self.graph.relate(root, domain_id, "has_part", metadata={"block": "B12", "taxonomy": True})
        self.graph.relate(domain_id, root, "part_of", metadata={"block": "B12", "taxonomy": True})

        branch_id = self._branch_node_id(branch.key)
        self.graph.add_entity("self_model_branch", branch.label, node_id=branch_id, data={"block": "B12", "domain": branch.domain, "branch": branch.key})
        self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B12", "taxonomy": True})
        self.graph.relate(branch_id, domain_id, "part_of", metadata={"block": "B12", "taxonomy": True})

        sub_ids = []
        if include_subtopics:
            for subtopic in branch.subtopics:
                sub_id = self._subtopic_node_id(branch.key, subtopic)
                self.graph.add_entity("self_model_subtopic", subtopic, node_id=sub_id, data={"block": "B12", "domain": branch.domain, "branch": branch.key})
                self.graph.relate(branch_id, sub_id, "has_part", metadata={"block": "B12", "taxonomy": True})
                self.graph.relate(sub_id, branch_id, "part_of", metadata={"block": "B12", "taxonomy": True})
                sub_ids.append(sub_id)
        return {"root_id": root, "domain_id": domain_id, "branch_id": branch_id, "subtopic_ids": sub_ids}

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = self._domain_key(domain) if domain else None
        if key and key not in SELF_MODEL_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in SELF_MODEL_BRANCHES if key is None or branch.domain == key]
        paths = [self._ensure_taxonomy_path(branch) for branch in selected]
        return {"domain": key, "branches_materialized": len(paths), "knowledge_graph": "shared", "parallel_self_graph_created": False, "paths": paths}

    def promote_canonical_self_knowledge(
        self,
        record_id: str,
        canonical_label: str,
        *,
        domain: str,
        branch: str,
        knowledge_type: str = "concept",
        aliases=None,
        properties=None,
        subtopics=None,
        contexts=None,
        rules=None,
        exceptions=None,
        summary: str = "",
    ) -> dict:
        domain_key = self._domain_key(domain)
        if domain_key not in SELF_MODEL_DOMAINS:
            raise ValueError(f"domínio B12 inválido: {domain}")
        branch_obj = self._branch(branch)
        if branch_obj.domain != domain_key:
            raise ValueError(f"ramo {branch} não pertence a {domain_key}")
        props = dict(properties or {})
        props.update({
            "self_model_is_identity_source": False,
            "self_model_can_grant_permissions": False,
            "runtime_state_is_canonical_by_default": False,
            "knowledge_scope": "star_self_model",
        })
        result = self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=props,
            categories=["self_model", domain_key, branch_obj.key],
            subtopics=subtopics,
            contexts=contexts,
            rules=rules,
            exceptions=exceptions,
            provenance={"self_model_block": "B12", "domain": domain_key, "branch": branch_obj.key, "source_record_id": record_id},
        )
        taxonomy = self._ensure_taxonomy_path(branch_obj, include_subtopics=False)
        self.graph.relate(result["knowledge_id"], taxonomy["branch_id"], "is_a", metadata={"block": "B12", "self_model_taxonomy": True})
        self.graph.relate(taxonomy["branch_id"], result["knowledge_id"], "has_part", metadata={"block": "B12", "self_model_taxonomy": True})
        return result

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "components": list(REQUESTED_COMPONENTS),
            "capabilities_registered": len(self.capabilities.list()),
            "limitations_registered": len(self.limitations.list()),
            "permissions_registered": len(self.permissions.list()),
            "history_events": len(self.history.list()),
            "knowledge_graph": "shared knowledge_nodes/knowledge_edges",
            "identity_source": Identity.SOURCE,
            "release_source": "STAR_MANIFEST.json via core.release",
            "permission_default": "deny",
            "parallel_identity": False,
            "parallel_state_store": False,
            "policy": deepcopy(SELF_POLICY),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 12", "status self model", "self model", "status do self model"}:
            stats = self.stats()
            release = self.release_snapshot()
            return (
                f"⭐ BLOCO 12 — SELF MODEL: {stats['catalog']['addressable_contents']} conteúdos endereçáveis em B12 | "
                f"{stats['catalog']['domains']} domínios × {stats['catalog']['branches']} ramos × {stats['catalog']['lenses_per_branch']} lentes = "
                f"{stats['catalog']['canonical_nodes']} nós | versão oficial={release['version']} | permissões=DEFAULT DENY | identidade={stats['identity_source']}."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        taxonomy = re.match(r"^(?:taxonomia self model|taxonomia do self model)(?:\s+(.+))?$", raw, re.I)
        if taxonomy:
            snapshot = self.taxonomy_snapshot(taxonomy.group(1))
            labels = ", ".join(item["branch_label"] for item in snapshot["branches"][:12])
            return f"⭐ Taxonomia B12: {len(snapshot['branches'])} ramos. {labels}{'…' if len(snapshot['branches']) > 12 else ''}"
        if low in {"capacidades self model", "capacidades do self model"}:
            available = self.capabilities.available()
            return "⭐ Capacidades registradas (disponíveis/experimentais): " + (", ".join(available) if available else "nenhuma comprovada")
        if low in {"limitacoes self model", "limitações self model", "limitacoes do self model", "limitações do self model"}:
            return f"🛡️ Self Model mantém {len(self.limitations.list(active_only=True))} limitações explícitas e não pode modificar a identidade fundamental."
        if low in {"permissoes self model", "permissões self model", "permissoes do self model", "permissões do self model"}:
            return "🛡️ Permission Registry usa DEFAULT DENY. Permissão não cria capacidade e nunca ignora segurança."
        if low in {"estado self model", "estado do self model"}:
            state = self.self_state.snapshot()
            return f"⭐ Estado B12: {state['status']} | fonte={state['source']} | runtime não é conhecimento canônico automaticamente."
        return None
