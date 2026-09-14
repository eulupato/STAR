"""BLOCO 17 — modelo afetivo e personalidade persistente da STAR.

A personalidade não é um prompt e não é uma segunda identidade. Esta camada usa:
- ``StarState`` como fonte de energia/curiosidade/confiança transitórias;
- ``cognitive_memory`` existente para baselines, preferências e histórico append-only;
- BLOCO 13 para experiências/relações auditáveis;
- BLOCO 12 como autoridade de identidade, valores, limites e permissões;
- Knowledge Graph compartilhado para relações.

AFETO != IDENTIDADE. PREFERÊNCIA != REGRA FUNDAMENTAL. CONFIANÇA != PERMISSÃO.
A adaptação é bounded, auditável e nunca reescreve fatos/memórias anteriores.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
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


def _valence(value: float) -> float:
    return max(-1.0, min(float(value), 1.0))


@dataclass(frozen=True)
class PersonalityBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


PERSONALITY_DOMAINS = (
    "affective_state",
    "energy_activation",
    "curiosity_interest",
    "caution_alert",
    "familiarity_confidence",
    "preferences",
    "style",
    "history_experience",
    "relationships",
    "adaptive_personality",
)

DOMAIN_LABELS = {
    "affective_state": "Valência e estado afetivo",
    "energy_activation": "Energia e ativação",
    "curiosity_interest": "Curiosidade e interesse",
    "caution_alert": "Cautela e alerta",
    "familiarity_confidence": "Familiaridade e confiança",
    "preferences": "Preferências persistentes",
    "style": "Estilo persistente",
    "history_experience": "História e experiências",
    "relationships": "Relações e continuidade social",
    "adaptive_personality": "Personalidade adaptativa",
}

PERSONALITY_BRANCHES = (
    PersonalityBranch("affective_state", "valence", "Valência", _subs("agradável;desagradável;neutro;mudança;contexto")),
    PersonalityBranch("affective_state", "affect_context", "Contexto afetivo", _subs("situação;evento;relação;tema;recência")),
    PersonalityBranch("affective_state", "affect_intensity", "Intensidade afetiva", _subs("intensidade;persistência;decaimento;limites;regulação")),
    PersonalityBranch("affective_state", "affect_uncertainty", "Incerteza afetiva", _subs("estado desconhecido;sinal parcial;ambiguidade;revisão;confiança")),
    PersonalityBranch("affective_state", "affect_regulation", "Regulação afetiva", _subs("estabilização;reavaliação;contexto;prioridade;recuperação")),

    PersonalityBranch("energy_activation", "energy", "Energia", _subs("energia atual;baseline;fadiga computacional;recuperação;carga")),
    PersonalityBranch("energy_activation", "activation", "Ativação", _subs("prontidão;ritmo;intensidade;demanda;contexto")),
    PersonalityBranch("energy_activation", "cognitive_load", "Carga cognitiva", _subs("carga;capacidade;priorização;limite;recuperação")),
    PersonalityBranch("energy_activation", "persistence", "Persistência", _subs("continuidade;esforço;abandono;retomada;objetivo")),
    PersonalityBranch("energy_activation", "restoration", "Restauração", _subs("redução de carga;pausa cognitiva;retomada;estabilidade;limites")),

    PersonalityBranch("curiosity_interest", "curiosity", "Curiosidade", _subs("exploração;novidade;pergunta;lacuna de conhecimento;limite")),
    PersonalityBranch("curiosity_interest", "interest", "Interesse", _subs("tema;relevância;persistência;preferência;contexto")),
    PersonalityBranch("curiosity_interest", "novelty", "Novidade", _subs("novo;familiar;surpresa;mudança;detecção")),
    PersonalityBranch("curiosity_interest", "exploration", "Exploração cognitiva", _subs("buscar alternativas;comparar;descobrir;sem autorização operacional")),
    PersonalityBranch("curiosity_interest", "engagement", "Engajamento", _subs("atenção;interesse;energia;objetivo;continuidade")),

    PersonalityBranch("caution_alert", "caution", "Cautela", _subs("risco;incerteza;reversibilidade;verificação;limites")),
    PersonalityBranch("caution_alert", "alert", "Alerta", _subs("sinal;urgência;risco;anomalia;prioridade")),
    PersonalityBranch("caution_alert", "risk_sensitivity", "Sensibilidade a risco", _subs("probabilidade;impacto;incerteza;segurança;escalonamento")),
    PersonalityBranch("caution_alert", "verification_tendency", "Tendência de verificação", _subs("checagem;fonte;contradição;evidência;confiança")),
    PersonalityBranch("caution_alert", "reversibility_preference", "Preferência por reversibilidade", _subs("rollback;opção segura;passo incremental;teste;recuperação")),

    PersonalityBranch("familiarity_confidence", "familiarity", "Familiaridade", _subs("repetição;histórico;entidade;tema;contexto")),
    PersonalityBranch("familiarity_confidence", "confidence", "Confiança", _subs("confiança epistêmica;calibração;evidência;erro;revisão")),
    PersonalityBranch("familiarity_confidence", "calibration", "Calibração", _subs("acerto;erro;feedback;certeza;incerteza")),
    PersonalityBranch("familiarity_confidence", "known_unknown", "Conhecido e desconhecido", _subs("lacuna;incerteza;fronteira;pergunta;verificação")),
    PersonalityBranch("familiarity_confidence", "confidence_limits", "Limites da confiança", _subs("confiança não é verdade;confiança não é permissão;checagem;escopo")),

    PersonalityBranch("preferences", "topic_preferences", "Preferências de tema", _subs("tema;interesse;prioridade;histórico;mudança")),
    PersonalityBranch("preferences", "interaction_preferences", "Preferências de interação", _subs("formato;ritmo;detalhe;ordem;contexto")),
    PersonalityBranch("preferences", "workflow_preferences", "Preferências de fluxo", _subs("sequência;validação;reversibilidade;qualidade;velocidade")),
    PersonalityBranch("preferences", "aesthetic_preferences", "Preferências estéticas", _subs("forma;consistência;minimalismo;expressividade;contexto")),
    PersonalityBranch("preferences", "preference_revision", "Revisão de preferências", _subs("evidência;experiência;mudança;histórico;reversão")),

    PersonalityBranch("style", "communication_style", "Estilo de comunicação", _subs("clareza;calor;objetividade;detalhe;adaptação")),
    PersonalityBranch("style", "reasoning_style", "Estilo de raciocínio", _subs("estrutura;comparação;verificação;hipóteses;exceções")),
    PersonalityBranch("style", "planning_style", "Estilo de planejamento", _subs("incremental;reversível;priorizado;validado;contextual")),
    PersonalityBranch("style", "social_style", "Estilo social", _subs("cooperação;respeito;limites;perspectiva;confiança calibrada")),
    PersonalityBranch("style", "style_consistency", "Consistência de estilo", _subs("continuidade;contexto;adaptação;limite;identidade distinta")),

    PersonalityBranch("history_experience", "history", "História", _subs("linha do tempo;mudança;versão;continuidade;proveniência")),
    PersonalityBranch("history_experience", "experiences", "Experiências", _subs("evento auditável;resultado;valência;intensidade;significado")),
    PersonalityBranch("history_experience", "learning_from_experience", "Aprendizado por experiência", _subs("feedback;erro;sucesso;ajuste bounded;proveniência")),
    PersonalityBranch("history_experience", "experience_weight", "Peso de experiência", _subs("recência;importância;confiabilidade;repetição;limite")),
    PersonalityBranch("history_experience", "continuity", "Continuidade", _subs("antes;depois;estado persistente;memória;auditoria")),

    PersonalityBranch("relationships", "relationship_history", "Histórico de relações", _subs("relações;interações;continuidade;confiança;contexto")),
    PersonalityBranch("relationships", "relationship_familiarity", "Familiaridade relacional", _subs("entidade;interações;recência;contexto;incerteza")),
    PersonalityBranch("relationships", "relationship_preferences", "Preferências relacionais", _subs("limites;cooperação;comunicação;ritmo;contexto")),
    PersonalityBranch("relationships", "relationship_learning", "Aprendizado relacional", _subs("feedback;reparação;cooperação;conflito;ajuste")),
    PersonalityBranch("relationships", "relationship_boundaries", "Limites relacionais", _subs("consentimento;privacidade;permissão;escopo;revogação")),

    PersonalityBranch("adaptive_personality", "adaptive_baselines", "Baselines adaptativos", _subs("baseline;ajuste pequeno;histórico;persistência;rollback")),
    PersonalityBranch("adaptive_personality", "contextual_adaptation", "Adaptação contextual", _subs("contexto;estado;preferência;limite;continuidade")),
    PersonalityBranch("adaptive_personality", "bounded_learning", "Aprendizado bounded", _subs("taxa máxima;delta;limite;auditoria;segurança")),
    PersonalityBranch("adaptive_personality", "identity_boundary", "Fronteira com identidade", _subs("personalidade não é identidade;valores fundamentais;limites;autoridade B12")),
    PersonalityBranch("adaptive_personality", "personality_revision", "Revisão da personalidade", _subs("histórico;experiência;evidência;reversibilidade;estabilidade")),
)

PERSONALITY_LENSES = (
    ("state", "estado", "representar estado sem transformá-lo em identidade"),
    ("baseline", "baseline", "separar baseline persistente de variação transitória"),
    ("context", "contexto", "considerar situação, tema, relação e tempo"),
    ("memory", "memória", "usar história auditável sem reescrever eventos anteriores"),
    ("relation", "relação", "relacionar entidades e experiências no grafo compartilhado"),
    ("adaptation", "adaptação", "aplicar mudanças pequenas, limitadas e reversíveis"),
    ("confidence", "confiança", "calibrar confiança e preservar incerteza"),
    ("preference", "preferência", "representar preferência como revisável, não como regra fundamental"),
    ("style", "estilo", "preservar consistência contextual sem virar prompt único"),
    ("limits", "limites", "preservar identidade oficial, permissões e segurança"),
)

CONTEXT_AXIS = ("general", "conversation", "project", "research", "social", "creative", "technical", "learning", "risk", "recovery")
VALENCE_AXIS = ("strong_negative", "negative", "mild_negative", "neutral_low", "neutral", "neutral_high", "mild_positive", "positive", "strong_positive", "mixed")
ENERGY_AXIS = ("depleted", "very_low", "low", "reduced", "medium", "steady", "good", "high", "very_high", "peak")
FAMILIARITY_AXIS = ("unknown", "very_low", "low", "limited", "moderate", "known", "familiar", "high", "very_high", "established")
CONFIDENCE_AXIS = ("unknown", "very_low", "low", "limited", "tentative", "moderate", "moderate_high", "high", "very_high", "calibrated")
EXPERIENCE_AXIS = ("none", "single", "few", "repeated", "recent", "historical", "positive", "negative", "mixed", "uncertain")
ADAPTATION_AXIS = ("stable", "observe")

VARIANT_AXES = (
    ("context", CONTEXT_AXIS),
    ("valence_state", VALENCE_AXIS),
    ("energy_state", ENERGY_AXIS),
    ("familiarity_state", FAMILIARITY_AXIS),
    ("confidence_state", CONFIDENCE_AXIS),
    ("experience_state", EXPERIENCE_AXIS),
    ("adaptation_mode", ADAPTATION_AXIS),
)

CANONICAL_NODES = len(PERSONALITY_BRANCHES) * len(PERSONALITY_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE

if len(PERSONALITY_DOMAINS) != 10 or len(PERSONALITY_BRANCHES) != 50 or len(PERSONALITY_LENSES) != 10:
    raise RuntimeError("B17 requer 10 domínios, 50 ramos e 10 lentes")
if CANONICAL_NODES != 500 or VARIANTS_PER_NODE != 2_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B17 inválida")

PERSISTENT_AXES_DEFAULTS = {
    "valence": 0.0,
    "curiosity": 0.5,
    "caution": 0.5,
    "confidence": 0.8,
    "interest": 0.5,
    "alert": 0.4,
}

ADAPTIVE_AXES = frozenset(PERSISTENT_AXES_DEFAULTS)

PERSONALITY_POLICY = {
    "personality_is_prompt_only": False,
    "personality_is_identity": False,
    "affect_is_identity": False,
    "preference_is_fundamental_rule": False,
    "confidence_is_permission": False,
    "experience_without_auditable_reference": False,
    "automatic_identity_rewrite": False,
    "automatic_values_rewrite": False,
    "adaptation_is_bounded": True,
    "adaptation_max_learning_rate": 0.1,
    "history_is_append_only": True,
    "operational_authorization": False,
    "rule": "AFETO ≠ IDENTIDADE; PREFERÊNCIA ≠ REGRA FUNDAMENTAL; CONFIANÇA ≠ PERMISSÃO",
}


def _decode_axes(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    value = int(index)
    decoded = {}
    for name, values in reversed(VARIANT_AXES):
        value, offset = divmod(value, len(values))
        decoded[name] = values[offset]
    return {name: decoded[name] for name, _ in VARIANT_AXES}


class PersonalityCatalog:
    NAMESPACE = "B17"
    PREFIX = "PERS-B17"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "domains": len(PERSONALITY_DOMAINS),
            "branches": len(PERSONALITY_BRANCHES),
            "lenses_per_branch": len(PERSONALITY_LENSES),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "prepopulated_personality_states": 0,
            "truthfulness_note": "1B are addressable affect/personality representations, not 1B fabricated experiences or physically stored personality records",
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"PERS-B17-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"PERS-B17-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant_index = divmod(absolute - 1, VARIANTS_PER_NODE)
        branch_index, lens_index = divmod(node_index, len(PERSONALITY_LENSES))
        branch = PERSONALITY_BRANCHES[branch_index]
        lens_key, lens_label, instruction = PERSONALITY_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"PERS-B17-{absolute:010d}",
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
                f"Contexto={axes['context']}; valência={axes['valence_state']}; energia={axes['energy_state']}; "
                f"familiaridade={axes['familiarity_state']}; confiança={axes['confidence_state']}; "
                f"experiência={axes['experience_state']}; adaptação={axes['adaptation_mode']}. "
                "Preservar identidade oficial, histórico e limites operacionais."
            ),
        }


class AffectivePersonality:
    """Estado afetivo + personalidade persistente sobre fontes oficiais existentes."""

    NAMESPACE = "B17"
    TAXONOMY_ROOT_ID = "AFFECTIVE-PERSONALITY-TAX-ROOT"
    KEY_PREFIX = "star.personality"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        state,
        memory_continuity,
        self_model=None,
        internal_models=None,
        social_cognition=None,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.state = state
        self.memory_continuity = memory_continuity
        self.memory = memory_continuity.memory
        self.self_model = self_model
        self.internal_models = internal_models
        self.social_cognition = social_cognition
        self.catalog = PersonalityCatalog()
        self._session = {
            "valence": None,
            "caution": None,
            "familiarity": 0.0,
            "interest": None,
            "alert": None,
            "context": "general",
        }
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 17 — MODELO AFETIVO E PERSONALIDADE",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/affective_personality.py",
            metadata={
                "materialization": "on-demand",
                "persistent_store": "existing cognitive_memory via memory_key",
                "transient_state": "existing core.state.StarState",
                "identity_authority": "B12/core.star_identity",
                "shared_knowledge_graph": True,
                "personality_is_prompt_only": False,
                "parallel_identity": False,
                "parallel_personality_database": False,
            },
        )

    @classmethod
    def _axis_key(cls, axis: str) -> str:
        return f"{cls.KEY_PREFIX}.axis.{_norm(axis)}"

    @classmethod
    def _preference_key(cls, name: str) -> str:
        return f"{cls.KEY_PREFIX}.preference.{_norm(name)}"

    @classmethod
    def _style_key(cls, name: str) -> str:
        return f"{cls.KEY_PREFIX}.style.{_norm(name)}"

    def _latest(self, key: str, *, kind: str = "preference") -> dict | None:
        return self.memory.store.memory_by_key(key, kind=kind)

    @staticmethod
    def _record_value(record: dict | None, default: float) -> float:
        if not record:
            return float(default)
        metadata = record.get("metadata") or {}
        try:
            return float(metadata.get("value", record.get("content", default)))
        except (TypeError, ValueError):
            return float(default)

    def persistent_axis(self, axis: str) -> float:
        key = _norm(axis)
        if key not in PERSISTENT_AXES_DEFAULTS:
            raise KeyError(axis)
        value = self._record_value(self._latest(self._axis_key(key)), PERSISTENT_AXES_DEFAULTS[key])
        return _valence(value) if key == "valence" else _clamp(value)

    def persistent_axes(self) -> dict[str, float]:
        return {axis: self.persistent_axis(axis) for axis in PERSISTENT_AXES_DEFAULTS}

    def _write_preference_record(
        self,
        key: str,
        content: str,
        *,
        value: Any,
        source: str,
        reference: str,
        confidence: float = 1.0,
        metadata: dict | None = None,
    ) -> dict:
        source, reference = _clean(source), _clean(reference)
        if not source or not reference:
            raise ValueError("personalidade persistente requer fonte e referência auditáveis")
        meta = {
            "block": "B17",
            "source": source,
            "reference": reference,
            "value": deepcopy(value),
            "confidence": _clamp(confidence),
            "personality_state": True,
            "identity_mutation": False,
            "fundamental_values_mutation": False,
            **deepcopy(metadata or {}),
        }
        memory_id = self.memory.remember("preference", content, key=key, metadata=meta, importance=0.7)
        record = self.memory.store.memory_by_id(memory_id)
        node_id = f"PERSONALITY-STATE-{memory_id:010d}"
        self.graph.add_entity(
            "personality_state",
            key,
            node_id=node_id,
            data={"block": "B17", "memory_id": memory_id, "key": key, "value": deepcopy(value), "source": source, "reference": reference},
            confidence=_clamp(confidence),
        )
        root = self.graph.add_entity(
            "affective_personality_taxonomy",
            "MODELO AFETIVO E PERSONALIDADE",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B17", "identity_authority": False},
        )
        self.graph.relate(root, node_id, "has_state", metadata={"block": "B17"})
        return {"memory_id": memory_id, "node_id": node_id, "record": record}

    def set_axis(
        self,
        axis: str,
        value: float,
        *,
        source: str,
        reference: str,
        confidence: float = 1.0,
        reason: str = "",
        experience_memory_id: int | None = None,
    ) -> dict:
        axis = _norm(axis)
        if axis not in PERSISTENT_AXES_DEFAULTS:
            raise KeyError(axis)
        value = _valence(value) if axis == "valence" else _clamp(value)
        previous = self.persistent_axis(axis)
        result = self._write_preference_record(
            self._axis_key(axis),
            str(value),
            value=value,
            source=source,
            reference=reference,
            confidence=confidence,
            metadata={
                "category": "adaptive_axis",
                "axis": axis,
                "previous_value": previous,
                "reason": _clean(reason),
                "experience_memory_id": experience_memory_id,
            },
        )
        if experience_memory_id is not None:
            self.graph.relate(
                result["node_id"],
                f"MEMORY-ENTRY-{int(experience_memory_id):010d}",
                "derived_from",
                metadata={"block": "B17", "source_memory_preserved": True},
            )
        return {"axis": axis, "previous": previous, "value": value, **result, "identity_mutation": False}

    def set_preference(self, name: str, value: Any, *, source: str, reference: str, confidence: float = 1.0) -> dict:
        name = _clean(name)
        if not name:
            raise ValueError("preferência sem nome")
        result = self._write_preference_record(
            self._preference_key(name),
            json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list, tuple)) else str(value),
            value=value,
            source=source,
            reference=reference,
            confidence=confidence,
            metadata={"category": "preference", "name": name},
        )
        return {"name": name, "value": deepcopy(value), **result}

    def preference(self, name: str) -> dict | None:
        record = self._latest(self._preference_key(name))
        if not record:
            return None
        meta = record.get("metadata") or {}
        return {"name": _clean(name), "value": deepcopy(meta.get("value")), "record": record}

    def set_style(self, name: str, value: Any, *, source: str, reference: str, confidence: float = 1.0) -> dict:
        name = _clean(name)
        if not name:
            raise ValueError("estilo sem nome")
        result = self._write_preference_record(
            self._style_key(name),
            str(value),
            value=value,
            source=source,
            reference=reference,
            confidence=confidence,
            metadata={"category": "style", "name": name},
        )
        return {"name": name, "value": deepcopy(value), **result}

    def style(self, name: str) -> dict | None:
        record = self._latest(self._style_key(name))
        if not record:
            return None
        return {"name": _clean(name), "value": deepcopy((record.get("metadata") or {}).get("value")), "record": record}

    def update_session_affect(
        self,
        *,
        valence: float | None = None,
        caution: float | None = None,
        familiarity: float | None = None,
        interest: float | None = None,
        alert: float | None = None,
        context: str | None = None,
    ) -> dict:
        if valence is not None:
            self._session["valence"] = _valence(valence)
        for key, value in (("caution", caution), ("familiarity", familiarity), ("interest", interest), ("alert", alert)):
            if value is not None:
                self._session[key] = _clamp(value)
        if context is not None:
            self._session["context"] = _clean(context) or "general"
        return self.current_state()

    def current_state(self) -> dict:
        persistent = self.persistent_axes()
        state_snapshot = self.state.snapshot() if hasattr(self.state, "snapshot") else self.state.get_state()
        def runtime_percent(name: str, fallback: float) -> float:
            raw = state_snapshot.get(name, fallback * 100)
            return _clamp(float(raw) / 100.0)
        return {
            "valence": persistent["valence"] if self._session["valence"] is None else self._session["valence"],
            "energy": runtime_percent("energy", 1.0),
            "curiosity": runtime_percent("curiosity", persistent["curiosity"]),
            "caution": persistent["caution"] if self._session["caution"] is None else self._session["caution"],
            "familiarity": self._session["familiarity"],
            "confidence": runtime_percent("confidence", persistent["confidence"]),
            "interest": persistent["interest"] if self._session["interest"] is None else self._session["interest"],
            "alert": persistent["alert"] if self._session["alert"] is None else self._session["alert"],
            "context": self._session["context"],
            "persistent_baselines": persistent,
            "personality_is_identity": False,
            "operational_authorization": False,
        }

    def record_experience(
        self,
        content: str,
        *,
        source: str,
        reference: str,
        valence: float = 0.0,
        intensity: float = 0.5,
        entities: Iterable[str] | None = None,
        context: dict | None = None,
        meaning: str = "",
    ) -> dict:
        result = self.memory_continuity.remember(
            "autobiographical",
            content,
            source=source,
            reference=reference,
            entities=entities,
            context=context,
            experience=True,
            meaning=meaning,
            importance=_clamp(intensity),
            metadata={"block_17": True, "valence": _valence(valence), "intensity": _clamp(intensity)},
        )
        return {**result, "valence": _valence(valence), "intensity": _clamp(intensity)}

    def record_relationship(
        self,
        entity: str,
        description: str,
        *,
        source: str,
        reference: str,
        familiarity: float = 0.0,
        importance: float = 0.5,
    ) -> dict:
        entity = _clean(entity)
        if not entity:
            raise ValueError("entidade relacional vazia")
        result = self.memory_continuity.remember(
            "social",
            f"Relação com {entity}: {_clean(description)}",
            source=source,
            reference=reference,
            entities=[entity],
            importance=importance,
            context={"relationship_entity": entity, "familiarity": _clamp(familiarity)},
            meaning="histórico relacional auditável para continuidade afetiva/personalidade",
            metadata={"block_17": True, "sensitive_attribute_inference": False},
        )
        return {**result, "entity": entity, "familiarity": _clamp(familiarity)}

    def adapt_from_experience(
        self,
        experience_memory_id: int,
        adjustments: dict[str, float],
        *,
        source: str,
        reference: str,
        learning_rate: float = 0.05,
        reason: str = "",
    ) -> dict:
        experience = self.memory_continuity.memory_record(int(experience_memory_id))
        if experience is None or experience.get("kind") != "autobiographical":
            raise ValueError("adaptação exige memória autobiográfica B13 existente")
        rate = max(0.0, min(float(learning_rate), PERSONALITY_POLICY["adaptation_max_learning_rate"]))
        updates = []
        for axis, raw_delta in adjustments.items():
            axis_key = _norm(axis)
            if axis_key not in ADAPTIVE_AXES:
                raise KeyError(axis)
            delta = max(-1.0, min(float(raw_delta), 1.0))
            old = self.persistent_axis(axis_key)
            if axis_key == "valence":
                new = _valence(old + delta * rate)
            else:
                new = _clamp(old + delta * rate)
            updates.append(self.set_axis(
                axis_key,
                new,
                source=source,
                reference=reference,
                confidence=0.8,
                reason=reason or "bounded adaptation from audited experience",
                experience_memory_id=int(experience_memory_id),
            ))
        return {
            "experience_memory_id": int(experience_memory_id),
            "learning_rate": rate,
            "updates": updates,
            "source_experience_preserved": True,
            "identity_mutation": False,
            "fundamental_values_mutation": False,
            "operational_authorization": False,
        }

    def axis_history(self, axis: str, *, limit: int = 20) -> list[dict]:
        axis = _norm(axis)
        if axis not in PERSISTENT_AXES_DEFAULTS:
            raise KeyError(axis)
        return self.memory.store.memory_history(self._axis_key(axis), kind="preference", limit=limit)

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        domain_key = _norm(domain) if domain else None
        if domain_key and domain_key not in PERSONALITY_DOMAINS:
            raise KeyError(domain)
        selected = [branch for branch in PERSONALITY_BRANCHES if domain_key is None or branch.domain == domain_key]
        root = self.graph.add_entity(
            "affective_personality_taxonomy",
            "MODELO AFETIVO E PERSONALIDADE",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B17", "identity_authority": False, "persistent_store": "cognitive_memory"},
        )
        for source_id, label, block in (
            ("SELF-TAX-ROOT", "B12 SELF MODEL", "B12"),
            ("MEMORY-TAX-ROOT", "B13 Memória e Continuidade", "B13"),
            ("INTERNAL-MODELS-TAX-ROOT", "B15 Cinco Modelos Internos", "B15"),
            ("SOCIAL-COGNITION-TAX-ROOT", "B16 Cognição Social", "B16"),
        ):
            self.graph.add_entity("personality_source", label, node_id=source_id, data={"block": block})
            self.graph.relate(root, source_id, "integrates", metadata={"block": "B17"})
        for branch in selected:
            domain_id = f"PERS-DOM-{branch.domain.upper()}"
            branch_id = f"PERS-BR-{branch.key.upper()}"
            self.graph.add_entity("personality_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B17"})
            self.graph.add_entity("personality_branch", branch.label, node_id=branch_id, data={"block": "B17", "domain": branch.domain})
            self.graph.relate(root, domain_id, "has_part", metadata={"block": "B17", "taxonomy": True})
            self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B17", "taxonomy": True})
        return {"domain": domain_key, "branches_materialized": len(selected), "knowledge_graph": "shared", "parallel_identity": False, "parallel_personality_database": False}

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "persistent_store": "cognitive_memory",
            "transient_state": "core.state.StarState",
            "adaptive_axes": sorted(ADAPTIVE_AXES),
            "policy": deepcopy(PERSONALITY_POLICY),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 17", "status personalidade", "status modelo afetivo", "modelo afetivo e personalidade"}:
            stats = self.stats()
            return (
                f"⭐ BLOCO 17 — AFETO E PERSONALIDADE: {stats['catalog']['addressable_contents']} representações endereçáveis | "
                f"{stats['catalog']['branches']} ramos × {stats['catalog']['lenses_per_branch']} lentes | "
                "personalidade persistente usa cognitive_memory; afeto ≠ identidade e confiança ≠ permissão."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        if low in {"estado afetivo star", "estado afetivo da star", "personalidade atual da star"}:
            state = self.current_state()
            return (
                "⭐ Estado afetivo/personality B17 — "
                f"valência={state['valence']:.2f}, energia={state['energy']:.2f}, curiosidade={state['curiosity']:.2f}, "
                f"cautela={state['caution']:.2f}, confiança={state['confidence']:.2f}, interesse={state['interest']:.2f}, alerta={state['alert']:.2f}."
            )
        return None
