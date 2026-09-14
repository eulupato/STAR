"""BLOCO 15 — cinco modelos internos integrados.

Este módulo NÃO cria cinco modelos paralelos. Ele coordena exatamente o
``CognitiveModels`` do BLOCO 1 e o conecta às fontes especializadas já existentes.
Cada modelo recebe um espaço lógico de 1B de representações, mas conhecimento,
memória e estado continuam em suas fontes oficiais e no Knowledge Graph comum.
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


MODEL_ORDER = (
    "world_model",
    "human_model",
    "social_model",
    "self_model",
    "situation_model",
)

MODEL_LABELS = {
    "world_model": "WORLD MODEL",
    "human_model": "HUMAN MODEL",
    "social_model": "SOCIAL MODEL",
    "self_model": "SELF MODEL",
    "situation_model": "SITUATION MODEL",
}

MODEL_PREFIXES = {
    "world_model": "WORLD-B15",
    "human_model": "HUMAN-B15",
    "social_model": "SOCIAL-B15",
    "self_model": "SELF-B15",
    "situation_model": "SITUATION-B15",
}

# Dez áreas por modelo. Os dados reais permanecem nas fontes abaixo; estas áreas
# apenas definem como cada modelo os referencia e organiza.
MODEL_AREAS = {
    "world_model": (
        ("physical_environment", "ambiente físico"),
        ("objects_materials", "objetos e materiais"),
        ("space_location", "espaço e localização"),
        ("time_change", "tempo e mudança"),
        ("events", "eventos externos"),
        ("causality", "causalidade e mecanismos"),
        ("infrastructure", "infraestrutura"),
        ("technology", "tecnologia e sistemas"),
        ("life_ecology", "vida e ecologia no mundo"),
        ("external_systems", "sistemas externos"),
    ),
    "human_model": (
        ("identity_context", "identidade e contexto humano"),
        ("body_life", "corpo e vida"),
        ("mind_psychology", "mente e psicologia"),
        ("needs", "necessidades humanas"),
        ("development", "desenvolvimento e ciclo de vida"),
        ("communication", "linguagem e comunicação"),
        ("behavior", "comportamento observado"),
        ("declared_preferences", "preferências declaradas"),
        ("capabilities_constraints", "capacidades e limitações humanas"),
        ("human_environment", "pessoa no ambiente"),
    ),
    "social_model": (
        ("roles", "papéis sociais"),
        ("relationships", "relações"),
        ("groups", "grupos e comunidades"),
        ("norms", "normas e expectativas"),
        ("culture", "cultura"),
        ("institutions", "instituições e estruturas sociais"),
        ("social_communication", "comunicação social"),
        ("trust_conflict", "confiança e conflito"),
        ("cooperation", "cooperação e coordenação"),
        ("permissions_boundaries", "limites, consentimento e permissões sociais"),
    ),
    "self_model": (
        ("identity", "identidade da STAR"),
        ("version_history", "versão e história"),
        ("capabilities", "capacidades"),
        ("limitations", "limitações"),
        ("resources", "recursos"),
        ("devices", "dispositivos"),
        ("state", "estado próprio"),
        ("permissions", "permissões"),
        ("goals_values", "objetivos e valores"),
        ("memory_uncertainty", "memória, conhecimento e incerteza"),
    ),
    "situation_model": (
        ("current_context", "contexto atual"),
        ("active_goal", "objetivo ativo"),
        ("active_entities", "entidades ativas"),
        ("recent_events", "eventos recentes"),
        ("evidence", "evidência disponível"),
        ("hypotheses", "hipóteses abertas"),
        ("risks", "riscos"),
        ("urgency", "urgência"),
        ("permissions", "permissões e limites atuais"),
        ("expected_outcomes", "resultados esperados"),
    ),
}

ASPECTS = (
    ("elements", "entidades e elementos", "quais elementos pertencem ao domínio"),
    ("state", "estado e propriedades", "qual estado/propriedade está representado e com que fonte"),
    ("relations", "relações", "como elementos se relacionam sem duplicar os dados de origem"),
    ("dynamics", "dinâmica e mudança", "como estados mudam ao longo do tempo ou contexto"),
    ("uncertainty", "incerteza e evidência", "qual evidência, confiança e desconhecido acompanham a representação"),
)

MODEL_LENSES = (
    ("definition", "definição"),
    ("observation", "observação"),
    ("memory", "memória"),
    ("knowledge", "conhecimento"),
    ("relation", "relação"),
    ("context", "contexto"),
    ("prediction", "previsão"),
    ("risk", "risco"),
    ("confidence", "confiança"),
    ("update", "atualização"),
)

EPISTEMIC_CLASS_AXIS = (
    "fact", "observation", "declared", "memory", "inference",
    "hypothesis", "prediction", "unknown", "conflict", "simulation",
)
TEMPORAL_SCOPE_AXIS = (
    "current", "recent", "session", "today", "short_term",
    "medium_term", "long_term", "historical", "future", "undated",
)
CONTEXT_SCOPE_AXIS = (
    "general", "conversation", "project", "task", "environment",
    "device", "social", "human", "self", "situation",
)
RELATION_MODE_AXIS = (
    "related_to", "part_of", "contains", "causes", "depends_on",
    "supports", "contradicts", "precedes", "follows", "contextualizes",
)
CONFIDENCE_AXIS = ("very_low", "low", "medium", "high", "verified")
SALIENCE_AXIS = ("background", "available", "relevant", "focused")
UPDATE_MODE_AXIS = (
    "observe", "refresh", "link", "contextualize", "compare",
    "predict", "verify", "revise", "supersede", "retain_unknown",
)

VARIANT_AXES = (
    ("epistemic_class", EPISTEMIC_CLASS_AXIS),
    ("temporal_scope", TEMPORAL_SCOPE_AXIS),
    ("context_scope", CONTEXT_SCOPE_AXIS),
    ("relation_mode", RELATION_MODE_AXIS),
    ("confidence", CONFIDENCE_AXIS),
    ("salience", SALIENCE_AXIS),
    ("update_mode", UPDATE_MODE_AXIS),
)

NODES_PER_MODEL = 10 * len(ASPECTS) * len(MODEL_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_PER_MODEL = NODES_PER_MODEL * VARIANTS_PER_NODE
TOTAL_B15_ADDRESSABLE = ADDRESSABLE_PER_MODEL * len(MODEL_ORDER)

if any(len(MODEL_AREAS[name]) != 10 for name in MODEL_ORDER):
    raise RuntimeError("B15 requer exatamente 10 áreas por modelo")
if len(ASPECTS) != 5 or len(MODEL_LENSES) != 10:
    raise RuntimeError("B15 requer 5 aspectos e 10 lentes")
if NODES_PER_MODEL != 500 or VARIANTS_PER_NODE != 2_000_000:
    raise RuntimeError("matriz B15 inválida")
if ADDRESSABLE_PER_MODEL != 1_000_000_000 or TOTAL_B15_ADDRESSABLE != 5_000_000_000:
    raise RuntimeError("B15 requer 1B por modelo e 5B no total")

# Fontes autoritativas por visão. Referenciar uma fonte não copia seus registros.
MODEL_SOURCE_REFS = {
    "world_model": (
        ("B04", "PhysicalWorldModel"),
        ("B05", "ScientificFoundations"),
        ("B11", "EverydayTechnologyFoundations"),
    ),
    "human_model": (
        ("B06", "HumanLifeFoundations"),
        ("B07", "HumanPsychologyFoundations"),
        ("B08", "LanguageCommunicationFoundations"),
        ("B10", "HumanContextFoundations"),
        ("B13", "People/Object/Episodic Memory"),
    ),
    "social_model": (
        ("B08", "LanguageCommunicationFoundations"),
        ("B09", "SocietyCultureFoundations"),
        ("B10", "HumanContextFoundations"),
        ("B13", "Social Memory"),
    ),
    "self_model": (
        ("B12", "SelfModel"),
        ("B13", "Autobiographical/Semantic Memory"),
        ("B14", "AttentionSalience"),
    ),
    "situation_model": (
        ("B01", "CognitiveModels.situation"),
        ("B13", "MemoryContinuity"),
        ("B14", "AttentionSalience"),
        ("B12", "SelfModel permissions/state"),
    ),
}

INTERNAL_MODEL_POLICY = {
    "parallel_models_created": False,
    "foundation_models_source": "BLOCO 1 CognitiveModels",
    "copies_source_knowledge": False,
    "shared_knowledge_graph": True,
    "one_star": True,
    "model_is_star": False,
    "model_output_is_fact": False,
    "situation_is_temporary_and_revisable": True,
    "self_model_redefines_identity": False,
    "operational_authorization": False,
    "rule": "OS CINCO MODELOS SÃO VISÕES COOPERATIVAS DA MESMA STAR; REPRESENTAÇÃO ≠ DUPLICAÇÃO E MODELO ≠ AUTORIZAÇÃO",
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


@dataclass(frozen=True)
class ModelAddress:
    model: str
    area: str
    aspect: str
    lens: str
    variant_index: int


class InternalModelsCatalog:
    NAMESPACE = "B15"

    @staticmethod
    def _model(value: str) -> str:
        aliases = {
            "world": "world_model", "world_model": "world_model",
            "human": "human_model", "human_model": "human_model",
            "social": "social_model", "social_model": "social_model",
            "self": "self_model", "self_model": "self_model",
            "situation": "situation_model", "situation_model": "situation_model",
        }
        key = aliases.get(_norm(value), _norm(value))
        if key not in MODEL_ORDER:
            raise KeyError(value)
        return key

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "models": 5,
            "areas_per_model": 10,
            "aspects_per_area": 5,
            "lenses_per_aspect": 10,
            "canonical_nodes_per_model": NODES_PER_MODEL,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_per_model": ADDRESSABLE_PER_MODEL,
            "total_addressable": TOTAL_B15_ADDRESSABLE,
            "materialization": "on-demand",
            "prepopulated_model_rows": 0,
            "truthfulness_note": "5B are virtual model representations (1B/model) over shared sources; not 5B copied facts or rows",
        }

    @staticmethod
    def content_id(model: str, node_index: int, variant_index: int) -> str:
        model = InternalModelsCatalog._model(model)
        if not 0 <= int(node_index) < NODES_PER_MODEL:
            raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"{MODEL_PREFIXES[model]}-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        raw = _clean(identifier).upper()
        selected_model = None
        number = None
        for model, prefix in MODEL_PREFIXES.items():
            match = re.fullmatch(re.escape(prefix) + r"-(\d{10})", raw)
            if match:
                selected_model = model
                number = int(match.group(1))
                break
        if selected_model is None or number is None or not 1 <= number <= ADDRESSABLE_PER_MODEL:
            return None
        node_index, variant_index = divmod(number - 1, VARIANTS_PER_NODE)
        area_index, within_area = divmod(node_index, len(ASPECTS) * len(MODEL_LENSES))
        aspect_index, lens_index = divmod(within_area, len(MODEL_LENSES))
        area_key, area_label = MODEL_AREAS[selected_model][area_index]
        aspect_key, aspect_label, aspect_instruction = ASPECTS[aspect_index]
        lens_key, lens_label = MODEL_LENSES[lens_index]
        axes = _decode_axes(variant_index)
        return {
            "id": f"{MODEL_PREFIXES[selected_model]}-{number:010d}",
            "namespace": "B15",
            "model": selected_model,
            "model_label": MODEL_LABELS[selected_model],
            "area": area_key,
            "area_label": area_label,
            "aspect": aspect_key,
            "aspect_label": aspect_label,
            "lens": lens_key,
            "lens_label": lens_label,
            **axes,
            "prompt": (
                f"{MODEL_LABELS[selected_model]} / {area_label} / {aspect_label} / {lens_label}: {aspect_instruction}. "
                f"Estado epistêmico={axes['epistemic_class']}; tempo={axes['temporal_scope']}; contexto={axes['context_scope']}; "
                f"relação={axes['relation_mode']}; confiança={axes['confidence']}; saliência={axes['salience']}; atualização={axes['update_mode']}. "
                "Usar referências compartilhadas; não copiar conhecimento da fonte nem converter modelo em fato/autorização."
            ),
        }


class IntegratedInternalModels:
    """Coordenador/view dos cinco CognitiveModels já existentes no BLOCO 1."""

    NAMESPACE = "B15"
    TAXONOMY_ROOT_ID = "MODELS-B15-ROOT"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        foundation_models,
        physical_world=None,
        human_life=None,
        human_psychology=None,
        language_communication=None,
        society_culture=None,
        human_contexts=None,
        everyday_technology=None,
        self_model=None,
        memory_continuity=None,
        attention_salience=None,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.foundation_models = foundation_models
        self.sources = {
            "physical_world": physical_world,
            "human_life": human_life,
            "human_psychology": human_psychology,
            "language_communication": language_communication,
            "society_culture": society_culture,
            "human_contexts": human_contexts,
            "everyday_technology": everyday_technology,
            "self_model": self_model,
            "memory_continuity": memory_continuity,
            "attention_salience": attention_salience,
        }
        self.catalog = InternalModelsCatalog()
        expected = set(MODEL_ORDER)
        actual = set(self.foundation_models.names())
        if actual != expected:
            raise RuntimeError(f"B15 requer os cinco CognitiveModels do B01; encontrados {sorted(actual)}")
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 15 — CINCO MODELOS INTERNOS",
            logical_capacity=TOTAL_B15_ADDRESSABLE,
            source="core/internal_models.py",
            metadata={
                "materialization": "on-demand",
                "subspaces": {MODEL_LABELS[name]: ADDRESSABLE_PER_MODEL for name in MODEL_ORDER},
                "foundation_models": "core.foundations.CognitiveModels",
                "parallel_models": False,
                "copies_source_knowledge": False,
                "shared_graph": True,
            },
        )

    @staticmethod
    def _model(value: str) -> str:
        return InternalModelsCatalog._model(value)

    def record(self, model: str, kind: str, value, *, source: str | None = None, confidence: float | None = None) -> dict:
        """Delega ao frame original do B01; não mantém um segundo frame."""
        return self.foundation_models.record(self._model(model), kind, value, source=source, confidence=confidence)

    def set_context(self, model: str, **context) -> dict:
        return self.foundation_models.set_context(self._model(model), **context)

    def shared_sources(self, model: str) -> list[dict]:
        key = self._model(model)
        return [
            {"block": block, "source": source, "mode": "reference_not_copy"}
            for block, source in MODEL_SOURCE_REFS[key]
        ]

    def model_view(self, model: str) -> dict:
        key = self._model(model)
        snapshot = self.foundation_models.snapshot(key)
        return {
            "model": key,
            "label": MODEL_LABELS[key],
            "definition": self.foundation_models.definition(key),
            "context": deepcopy(snapshot.get("context") or {}),
            "epistemic_counts": {
                kind: len(snapshot.get(kind) or ())
                for kind in self.foundation_models.KINDS
            },
            "shared_sources": self.shared_sources(key),
            "addressable_capacity": ADDRESSABLE_PER_MODEL,
            "copies_source_knowledge": False,
            "operational_authorization": False,
        }

    def all_views(self) -> dict[str, dict]:
        return {name: self.model_view(name) for name in MODEL_ORDER}

    def cooperate(
        self,
        *,
        current_input: str = "",
        goal: str = "",
        active_entities: Iterable[str] | None = None,
        evidence: Iterable[str] | None = None,
        risk: float = 0.0,
        urgency: float = 0.0,
    ) -> dict:
        """Atualiza o SITUATION MODEL com referências bounded aos quatro modelos.

        Não executa ação e não duplica datasets. O resultado permanece observação /
        inferência contextual temporária.
        """
        entities = tuple(_clean(item) for item in (active_entities or ()) if _clean(item))[:16]
        evidence_items = tuple(_clean(item) for item in (evidence or ()) if _clean(item))[:16]
        attention_snapshot = None
        if self.sources["attention_salience"] is not None:
            attention_snapshot = self.sources["attention_salience"].snapshot()
        memory_recent = []
        if self.sources["memory_continuity"] is not None:
            memory_recent = self.sources["memory_continuity"].working.list(limit=8)
        self_snapshot = None
        if self.sources["self_model"] is not None:
            raw_self = self.sources["self_model"].snapshot()
            self_snapshot = {
                "release": deepcopy(raw_self.get("release")),
                "state": deepcopy(raw_self.get("state")),
                "permissions": deepcopy(raw_self.get("permissions")),
                "objectives": deepcopy(raw_self.get("objectives")),
                "uncertainties": deepcopy(raw_self.get("uncertainties")),
            }

        situation_context = {
            "current_input": _clean(current_input),
            "goal": _clean(goal),
            "active_entities": entities,
            "evidence": evidence_items,
            "risk": _clamp(risk),
            "urgency": _clamp(urgency),
            "recent_memory_refs": tuple(item.get("working_id") for item in memory_recent),
            "attention": None if attention_snapshot is None else {
                "active_goals": len(attention_snapshot.get("active_goals") or ()),
                "active_entities": len(attention_snapshot.get("active_entities") or ()),
                "hypotheses": len(attention_snapshot.get("hypotheses") or ()),
                "last_selection": deepcopy(attention_snapshot.get("last_selection")),
            },
            "self": self_snapshot,
            "source_models": ("world_model", "human_model", "social_model", "self_model"),
            "temporary": True,
            "operational_authorization": False,
        }
        self.foundation_models.set_context("situation_model", **situation_context)
        return {
            "model": "SITUATION MODEL",
            "cooperating_models": tuple(MODEL_LABELS[name] for name in MODEL_ORDER),
            "context": deepcopy(situation_context),
            "foundation_situation": self.foundation_models.situation(),
            "shared_data": True,
            "copied_source_datasets": False,
            "operational_authorization": False,
        }

    @staticmethod
    def _model_node_id(model: str) -> str:
        return f"MODELS-B15-{model.upper()}"

    @staticmethod
    def _area_node_id(model: str, area: str) -> str:
        return f"MODELS-B15-{model.upper()}-{area.upper()}"

    @staticmethod
    def _aspect_node_id(model: str, area: str, aspect: str) -> str:
        return f"MODELS-B15-{model.upper()}-{area.upper()}-{aspect.upper()}"

    def materialize_taxonomy(self, model: str | None = None) -> dict:
        selected_models = [self._model(model)] if model else list(MODEL_ORDER)
        root = self.graph.add_entity(
            "internal_models_taxonomy",
            "CINCO MODELOS INTERNOS",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B15", "parallel_models": False},
        )
        b01 = self.graph.add_entity(
            "internal_models_source",
            "B01 CognitiveModels",
            node_id="MODELS-B15-SOURCE-B01",
            data={"source": "core/foundations.py::CognitiveModels", "block": "B01"},
        )
        self.graph.relate(root, b01, "extends", metadata={"block": "B15"})

        model_ids: dict[str, str] = {}
        aspect_count = 0
        for model_key in selected_models:
            model_id = self._model_node_id(model_key)
            model_ids[model_key] = model_id
            self.graph.add_entity(
                "internal_model",
                MODEL_LABELS[model_key],
                node_id=model_id,
                data={"block": "B15", "model": model_key, "capacity": ADDRESSABLE_PER_MODEL},
            )
            self.graph.relate(root, model_id, "has_part", metadata={"block": "B15"})
            for block, source in MODEL_SOURCE_REFS[model_key]:
                source_id = f"MODELS-B15-SOURCE-{model_key.upper()}-{block}"
                self.graph.add_entity(
                    "model_source_reference", f"{block} {source}", node_id=source_id,
                    data={"block": block, "source": source, "mode": "reference_not_copy"},
                )
                self.graph.relate(model_id, source_id, "references", metadata={"block": "B15", "copies_data": False})
            for area_key, area_label in MODEL_AREAS[model_key]:
                area_id = self._area_node_id(model_key, area_key)
                self.graph.add_entity("internal_model_area", area_label, node_id=area_id, data={"block": "B15", "model": model_key})
                self.graph.relate(model_id, area_id, "has_part", metadata={"block": "B15"})
                for aspect_key, aspect_label, _instruction in ASPECTS:
                    aspect_id = self._aspect_node_id(model_key, area_key, aspect_key)
                    self.graph.add_entity("internal_model_aspect", aspect_label, node_id=aspect_id, data={"block": "B15", "model": model_key, "area": area_key})
                    self.graph.relate(area_id, aspect_id, "has_part", metadata={"block": "B15"})
                    aspect_count += 1

        # SITUATION integra as outras quatro visões, sem as incorporar fisicamente.
        situation_id = self._model_node_id("situation_model")
        if "situation_model" in selected_models:
            for other in MODEL_ORDER[:-1]:
                other_id = self._model_node_id(other)
                # garante nó de referência mesmo quando materializando apenas situation.
                self.graph.add_entity("internal_model", MODEL_LABELS[other], node_id=other_id, data={"block": "B15", "model": other, "capacity": ADDRESSABLE_PER_MODEL})
                self.graph.relate(situation_id, other_id, "integrates_view", metadata={"block": "B15", "copies_data": False})
        return {
            "models_materialized": len(selected_models),
            "aspects_materialized": aspect_count,
            "knowledge_graph": "shared",
            "parallel_models_created": False,
            "copies_source_knowledge": False,
            "model_ids": model_ids,
        }

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "foundation_models_reused": True,
            "foundation_model_names": list(self.foundation_models.names()),
            "parallel_models_created": False,
            "shared_knowledge_graph": True,
            "copies_source_knowledge": False,
            "policy": deepcopy(INTERNAL_MODEL_POLICY),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 15", "status cinco modelos", "cinco modelos internos", "status modelos internos"}:
            stats = self.stats()["catalog"]
            return (
                f"⭐ BLOCO 15 — CINCO MODELOS INTERNOS: 5 modelos × {stats['addressable_per_model']} = "
                f"{stats['total_addressable']} representações endereçáveis | B01 CognitiveModels reutilizado | grafo compartilhado."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['model_label']} / {item['area_label']} / {item['aspect_label']} / {item['lens_label']}\n{item['prompt']}"
        match = re.fullmatch(r"(?:visao|visão|status)\s+(world|human|social|self|situation)(?:\s+model)?", low)
        if match:
            view = self.model_view(match.group(1))
            return (
                f"⭐ {view['label']}: {view['addressable_capacity']} representações endereçáveis | "
                f"fontes compartilhadas={len(view['shared_sources'])} | cópia de conhecimento=NÃO | autorização operacional=NÃO."
            )
        return None
