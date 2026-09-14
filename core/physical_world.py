"""BLOCO 4 — Modelo Físico Fundamental do Mundo da STAR.

Este módulo não duplica as bases científicas de Física. Ele modela o mundo físico
como uma camada operacional sobre o BLOCO 3 (conhecimento universal), reutiliza
as bases de Física existentes quando uma referência científica é necessária e
mantém cenas/objetos observados como estado transitório — nunca como verdade
canônica automática.

Escala lógica do BLOCO 4:
50 temas físicos x 10 subtemas = 500 nós canônicos.
Cada nó combina:
OBJETO(10) x MATERIAL(10) x PROPRIEDADE(10) x ESTADO(5) x AMBIENTE(5)
x AÇÃO(5) x CONSEQUÊNCIA(4) x RISCO(4) = 2.000.000 variações.
500 x 2.000.000 = 1.000.000.000 representações endereçáveis em B04.

As variações são esquemas de raciocínio/materialização sob demanda; não são um
bilhão de fatos independentes pesquisados nem um bilhão de linhas no SQLite.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import re
from typing import Any

from core.universal_knowledge import UniversalKnowledgeArchitecture


PHYSICAL_TOPICS = (
    ("matter", "matéria"),
    ("objects", "objetos"),
    ("surfaces", "superfícies"),
    ("space", "espaço"),
    ("volume", "volume"),
    ("mass", "massa"),
    ("weight", "peso"),
    ("density", "densidade"),
    ("shape", "forma"),
    ("size", "tamanho"),
    ("distance", "distância"),
    ("position", "posição"),
    ("direction", "direção"),
    ("orientation", "orientação"),
    ("motion", "movimento"),
    ("velocity", "velocidade"),
    ("acceleration", "aceleração"),
    ("force", "força"),
    ("equilibrium", "equilíbrio"),
    ("gravity", "gravidade"),
    ("impact", "impacto"),
    ("collision", "colisão"),
    ("friction", "atrito"),
    ("pressure", "pressão"),
    ("temperature", "temperatura"),
    ("heat", "calor"),
    ("cold", "frio"),
    ("sound", "som"),
    ("light", "luz"),
    ("shadow", "sombra"),
    ("reflection", "reflexão"),
    ("electricity", "eletricidade"),
    ("magnetism", "magnetismo"),
    ("liquids", "líquidos"),
    ("gases", "gases"),
    ("solids", "sólidos"),
    ("object_permanence", "permanência de objetos"),
    ("affordances", "affordances"),
    ("materials", "materiais"),
    ("time", "tempo"),
    ("causality", "causalidade"),
    ("prediction", "previsão"),
    ("energy", "energia"),
    ("deformation", "deformação"),
    ("stability", "estabilidade"),
    ("buoyancy", "flutuabilidade"),
    ("flow", "fluxo"),
    ("contact", "contato"),
    ("containment", "contenção"),
    ("risk", "risco físico"),
)

PHYSICAL_SUBTHEMES = (
    ("definition_measurement", "definição, grandezas e medição"),
    ("intrinsic_properties", "propriedades intrínsecas"),
    ("extrinsic_properties", "propriedades extrínsecas"),
    ("state_conditions", "estado e condições"),
    ("spatial_relations", "relações espaciais"),
    ("interactions", "interações"),
    ("transformations", "transformações"),
    ("causal_mechanisms", "mecanismos causais"),
    ("affordances_constraints", "affordances e restrições"),
    ("prediction_risk", "previsão, consequência e risco"),
)

OBJECT_FAMILIES = (
    "generic_object",
    "small_item",
    "large_object",
    "tool",
    "container",
    "structure",
    "mechanism",
    "vehicle_component",
    "natural_body",
    "surface_element",
)

MATERIAL_FAMILIES = (
    "metal",
    "polymer",
    "glass_ceramic",
    "wood_fiber",
    "stone_mineral",
    "rubber_elastomer",
    "liquid",
    "gas",
    "composite",
    "unknown_mixed",
)

PROPERTY_FAMILIES = (
    "mechanical",
    "thermal",
    "electrical",
    "optical",
    "magnetic",
    "geometric",
    "inertial",
    "surface",
    "fluid",
    "phase",
)

STATE_FAMILIES = (
    "rest_or_static",
    "moving_or_rotating",
    "loaded_or_deformed",
    "heated_or_cooled",
    "flowing_or_pressurized",
)

ENVIRONMENT_FAMILIES = (
    "indoor_or_controlled",
    "outdoor_gravity",
    "wet_or_fluid",
    "thermal_extreme",
    "electromagnetic_or_acoustic",
)

ACTION_FAMILIES = (
    "contact_push_pull",
    "drop_impact_collision",
    "heat_cool",
    "immerse_pour_flow",
    "energize_rotate_expose",
)

CONSEQUENCE_CLASSES = (
    "no_material_change",
    "reversible_change",
    "motion_or_energy_transfer",
    "irreversible_change_or_damage",
)

RISK_CLASSES = (
    "low",
    "moderate",
    "high",
    "unknown_requires_measurement",
)

MATRIX_AXES = (
    ("OBJECT", OBJECT_FAMILIES),
    ("MATERIAL", MATERIAL_FAMILIES),
    ("PROPERTY", PROPERTY_FAMILIES),
    ("STATE", STATE_FAMILIES),
    ("ENVIRONMENT", ENVIRONMENT_FAMILIES),
    ("ACTION", ACTION_FAMILIES),
    ("CONSEQUENCE", CONSEQUENCE_CLASSES),
    ("RISK", RISK_CLASSES),
)

PHYSICAL_CANONICAL_NODES = len(PHYSICAL_TOPICS) * len(PHYSICAL_SUBTHEMES)
PHYSICAL_VARIANTS_PER_NODE = 1
for _, values in MATRIX_AXES:
    PHYSICAL_VARIANTS_PER_NODE *= len(values)
PHYSICAL_ADDRESSABLE_CONTENTS = PHYSICAL_CANONICAL_NODES * PHYSICAL_VARIANTS_PER_NODE

if len(PHYSICAL_TOPICS) != 50:
    raise RuntimeError("BLOCO 4 deve manter exatamente 50 temas físicos")
if len(PHYSICAL_SUBTHEMES) != 10:
    raise RuntimeError("BLOCO 4 deve manter exatamente 10 subtemas por tema")
if PHYSICAL_CANONICAL_NODES != 500:
    raise RuntimeError("BLOCO 4 deve manter exatamente 500 nós canônicos")
if PHYSICAL_VARIANTS_PER_NODE != 2_000_000:
    raise RuntimeError("BLOCO 4 deve manter exatamente 2.000.000 combinações por nó")
if PHYSICAL_ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("BLOCO 4 deve manter exatamente 1B de representações endereçáveis")


PHYSICAL_QUANTITIES = {
    "volume": {"unit": "m³", "kind": "scalar", "relation": "extent of occupied space"},
    "mass": {"unit": "kg", "kind": "scalar", "relation": "inertial/gravitational mass parameter"},
    "weight": {"unit": "N", "kind": "vector", "relation": "W = m g for a specified gravitational field"},
    "density": {"unit": "kg/m³", "kind": "scalar", "relation": "rho = m / V"},
    "distance": {"unit": "m", "kind": "scalar", "relation": "separation/path length"},
    "position": {"unit": "m", "kind": "vector", "relation": "location relative to a reference frame"},
    "velocity": {"unit": "m/s", "kind": "vector", "relation": "rate of change of position"},
    "acceleration": {"unit": "m/s²", "kind": "vector", "relation": "rate of change of velocity"},
    "force": {"unit": "N", "kind": "vector", "relation": "net force relates to acceleration in the applicable model"},
    "pressure": {"unit": "Pa", "kind": "scalar", "relation": "normal force per area"},
    "temperature": {"unit": "K", "kind": "scalar", "relation": "thermodynamic temperature"},
    "time": {"unit": "s", "kind": "scalar", "relation": "duration/order parameter"},
    "sound_frequency": {"unit": "Hz", "kind": "scalar", "relation": "oscillations per second"},
    "light_wavelength": {"unit": "m", "kind": "scalar", "relation": "spatial period of electromagnetic radiation"},
    "electric_potential": {"unit": "V", "kind": "scalar", "relation": "electric potential difference"},
    "electric_current": {"unit": "A", "kind": "scalar", "relation": "charge flow rate"},
    "magnetic_flux_density": {"unit": "T", "kind": "vector", "relation": "magnetic field quantity B"},
}

OBJECT_PERMANENCE_RULES = (
    "perder observação não equivale a deixar de existir",
    "um objeto persiste no world model até evidência de remoção, destruição ou transformação",
    "posição/estado não observados depois de oclusão tornam-se incertos; não devem ser inventados",
)

AFFORDANCE_RULES = {
    "flat": ("support",),
    "stable": ("support", "place_on"),
    "handle": ("grasp", "carry"),
    "small": ("grasp", "carry"),
    "hollow": ("contain",),
    "container": ("contain", "pour_into"),
    "round": ("roll",),
    "wheel": ("roll", "rotate"),
    "smooth": ("slide",),
    "low_friction": ("slide",),
    "flexible": ("bend", "wrap"),
    "elastic": ("deform_reversibly",),
    "sharp": ("cut_or_pierce",),
    "conductive": ("conduct_electricity",),
    "insulating": ("electrically_isolate",),
    "transparent": ("transmit_light",),
    "reflective": ("reflect_light",),
    "ferromagnetic": ("interact_strongly_with_magnetic_field",),
    "liquid": ("flow", "pour"),
    "gas": ("flow", "expand_to_available_volume"),
    "buoyant": ("float_when_conditions_allow",),
}


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _clean(value).casefold()).strip("_")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PhysicalWorldCatalog:
    """1B de esquemas físicos em B04, decodificados sob demanda."""

    PREFIX = "PHY"
    NAMESPACE = "B04"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "themes": len(PHYSICAL_TOPICS),
            "subthemes_per_theme": len(PHYSICAL_SUBTHEMES),
            "canonical_nodes": PHYSICAL_CANONICAL_NODES,
            "variants_per_node": PHYSICAL_VARIANTS_PER_NODE,
            "addressable_contents": PHYSICAL_ADDRESSABLE_CONTENTS,
            "matrix": {name: len(values) for name, values in MATRIX_AXES},
            "materialization": "on-demand",
            "prepopulated_knowledge_rows": 0,
            "truthfulness_note": (
                "1B são cenários/esquemas físicos combinatórios endereçáveis; "
                "não representam 1B de fatos científicos independentes pesquisados"
            ),
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        node_index = int(node_index)
        variant_index = int(variant_index)
        if not 0 <= node_index < PHYSICAL_CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= variant_index < PHYSICAL_VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = node_index * PHYSICAL_VARIANTS_PER_NODE + variant_index + 1
        return f"PHY-B04-{absolute:010d}"

    @staticmethod
    def _decode_variant(variant_index: int) -> dict:
        remainder = int(variant_index)
        decoded = {}
        for name, values in reversed(MATRIX_AXES):
            remainder, index = divmod(remainder, len(values))
            decoded[name.lower()] = values[index]
        if remainder:
            raise IndexError(variant_index)
        return decoded

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"PHY-B04-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= PHYSICAL_ADDRESSABLE_CONTENTS:
            return None

        node_index, variant_index = divmod(absolute - 1, PHYSICAL_VARIANTS_PER_NODE)
        topic_index, subtheme_index = divmod(node_index, len(PHYSICAL_SUBTHEMES))
        topic_key, topic_label = PHYSICAL_TOPICS[topic_index]
        subtheme_key, subtheme_label = PHYSICAL_SUBTHEMES[subtheme_index]
        matrix = self._decode_variant(variant_index)
        return {
            "id": f"PHY-B04-{absolute:010d}",
            "namespace": "B04",
            "node_index": node_index,
            "variant_index": variant_index,
            "topic": topic_key,
            "topic_label": topic_label,
            "subtheme": subtheme_key,
            "subtheme_label": subtheme_label,
            **matrix,
            "prompt": (
                f"Analisar {topic_label} / {subtheme_label} no cenário "
                f"OBJETO={matrix['object']}, MATERIAL={matrix['material']}, "
                f"PROPRIEDADE={matrix['property']}, ESTADO={matrix['state']}, "
                f"AMBIENTE={matrix['environment']}, AÇÃO={matrix['action']}, "
                f"CONSEQUÊNCIA={matrix['consequence']}, RISCO={matrix['risk']}. "
                "Separar observação de inferência, usar causalidade explícita, "
                "declarar incerteza e nunca tratar a previsão como autorização de ação."
            ),
        }


class PhysicalWorldModel:
    """World model físico: conhecimento B04 + estado transitório + inferência qualitativa."""

    NAMESPACE = "B04"

    def __init__(self, knowledge: UniversalKnowledgeArchitecture):
        self.knowledge = knowledge
        self.catalog = PhysicalWorldCatalog()
        self._objects: dict[str, dict] = {}
        self._physics_engine = None
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 4 — MODELO FÍSICO FUNDAMENTAL DO MUNDO",
            logical_capacity=PHYSICAL_ADDRESSABLE_CONTENTS,
            source="core/physical_world.py",
            metadata={
                "materialization": "on-demand",
                "role": "physical-world-model",
                "scientific_reference": "existing physics knowledge engines",
                "scene_state": "transient-not-canonical",
            },
        )

    def observe_object(
        self,
        object_id: str,
        *,
        label: str,
        material: str | None = None,
        properties: list[str] | tuple[str, ...] | None = None,
        state: str | None = None,
        environment: str | None = None,
        position: Any = None,
        orientation: Any = None,
        size: Any = None,
        mass: Any = None,
        temperature: Any = None,
        observed_at: str | None = None,
    ) -> dict:
        object_id = _clean(object_id)
        label = _clean(label)
        if not object_id or not label:
            raise ValueError("objeto observado exige object_id e label")
        previous = self._objects.get(object_id, {})
        record = {
            **previous,
            "object_id": object_id,
            "label": label,
            "material": _clean(material) or previous.get("material"),
            "properties": sorted({_norm(x) for x in (properties or previous.get("properties", [])) if _norm(x)}),
            "state": _clean(state) or previous.get("state") or "unknown",
            "environment": _clean(environment) or previous.get("environment") or "unknown",
            "position": position if position is not None else previous.get("position"),
            "orientation": orientation if orientation is not None else previous.get("orientation"),
            "size": size if size is not None else previous.get("size"),
            "mass": mass if mass is not None else previous.get("mass"),
            "temperature": temperature if temperature is not None else previous.get("temperature"),
            "visibility": "observed",
            "existence_status": "present_observed",
            "observed_at": observed_at or _now(),
            "state_confidence": 1.0,
        }
        self._objects[object_id] = record
        return deepcopy(record)

    def mark_unobserved(self, object_id: str, *, reason: str = "occluded") -> dict:
        if object_id not in self._objects:
            raise KeyError(object_id)
        item = dict(self._objects[object_id])
        item["visibility"] = "unobserved"
        item["existence_status"] = "present_inferred"
        item["state_confidence"] = min(float(item.get("state_confidence", 1.0)), 0.7)
        item["unobserved_reason"] = _clean(reason) or "occluded"
        item["note"] = OBJECT_PERMANENCE_RULES[1]
        self._objects[object_id] = item
        return deepcopy(item)

    def remove_object(self, object_id: str, *, evidence: str) -> dict:
        if object_id not in self._objects:
            raise KeyError(object_id)
        evidence = _clean(evidence)
        if not evidence:
            raise ValueError("remoção exige evidência explícita")
        item = dict(self._objects[object_id])
        item["visibility"] = "not_present"
        item["existence_status"] = "removed_or_transformed"
        item["removal_evidence"] = evidence
        item["state_confidence"] = 1.0
        self._objects[object_id] = item
        return deepcopy(item)

    def get_object(self, object_id: str) -> dict | None:
        item = self._objects.get(object_id)
        return None if item is None else deepcopy(item)

    def scene(self) -> list[dict]:
        return [deepcopy(item) for item in self._objects.values()]

    @staticmethod
    def infer_affordances(properties: list[str] | tuple[str, ...], *, state: str | None = None) -> dict:
        tags = {_norm(item) for item in properties if _norm(item)}
        state_tag = _norm(state)
        if state_tag:
            tags.add(state_tag)
        affordances = []
        for tag, values in AFFORDANCE_RULES.items():
            if tag in tags:
                affordances.extend(values)
        return {
            "properties": sorted(tags),
            "affordances": sorted(set(affordances)),
            "epistemic_kind": "inference",
            "note": "affordance é capacidade física potencial; contexto, escala e restrições ainda precisam ser checados",
        }

    @staticmethod
    def predict_interaction(
        *,
        object_label: str,
        material: str,
        properties: list[str] | tuple[str, ...],
        state: str,
        environment: str,
        action: str,
    ) -> dict:
        tags = {_norm(x) for x in properties if _norm(x)}
        material_tag = _norm(material)
        state_tag = _norm(state)
        environment_tag = _norm(environment)
        action_tag = _norm(action)
        mechanisms: list[str] = []
        consequences: list[str] = []
        hazards: list[str] = []
        confidence = 0.45

        if any(key in action_tag for key in ("impact", "collision", "drop", "hit")):
            mechanisms.append("transferência de momento e energia no contato")
            consequences.append("mudança de velocidade, vibração ou deformação")
            confidence += 0.10
            if {"brittle", "fragile"} & tags or material_tag in {"glass", "ceramic", "glass_ceramic"}:
                consequences.append("fratura ou dano irreversível é plausível")
                hazards.append("fragmentação/impacto")
                confidence += 0.10

        if any(key in action_tag for key in ("push", "pull", "force")):
            mechanisms.append("força resultante pode alterar movimento ou equilíbrio")
            consequences.append("translação, rotação ou deformação conforme restrições")
            confidence += 0.08
            if {"low_friction", "smooth"} & tags:
                consequences.append("deslizamento torna-se mais plausível")

        if any(key in action_tag for key in ("heat", "warm", "cool", "cold")):
            mechanisms.append("transferência térmica por diferença de temperatura")
            consequences.append("temperatura e possivelmente estado/deformação podem mudar")
            confidence += 0.10
            if "flammable" in tags and any(key in action_tag for key in ("heat", "warm")):
                hazards.append("ignição é possível se limites térmicos forem excedidos")

        if any(key in action_tag for key in ("pour", "immerse", "flow")) or material_tag in {"liquid", "gas"}:
            mechanisms.append("escoamento responde a pressão, gravidade, geometria e viscosidade")
            consequences.append("redistribuição espacial do fluido")
            confidence += 0.08
            if "floor" in environment_tag and material_tag == "liquid":
                hazards.append("superfície molhada pode alterar atrito")

        if any(key in action_tag for key in ("energize", "electric", "voltage", "current")):
            mechanisms.append("campo elétrico/circuito pode produzir corrente se houver caminho condutor")
            consequences.append("efeitos elétricos e térmicos dependem de tensão, resistência e geometria")
            confidence += 0.08
            if "conductive" in tags or material_tag == "metal" or "wet" in environment_tag:
                hazards.append("risco elétrico requer valores e isolamento conhecidos")

        if any(key in action_tag for key in ("magnet", "field")) or "magnetic" in environment_tag:
            mechanisms.append("campo magnético pode exercer força/torque em materiais ou correntes compatíveis")
            if "ferromagnetic" in tags or material_tag in {"iron", "steel", "metal"}:
                consequences.append("atração, alinhamento ou torque tornam-se plausíveis")
                confidence += 0.08

        if any(key in action_tag for key in ("light", "illuminate", "expose")):
            if "opaque" in tags:
                mechanisms.append("bloqueio da propagação direta da luz")
                consequences.append("formação de sombra")
                confidence += 0.08
            if "reflective" in tags:
                mechanisms.append("reflexão óptica na superfície")
                consequences.append("redirecionamento de luz")
                confidence += 0.08

        if any(key in action_tag for key in ("sound", "vibrate")):
            mechanisms.append("vibração mecânica pode propagar onda no meio material")
            consequences.append("som/vibração dependem do meio, frequência e acoplamento")
            confidence += 0.06

        if any(key in state_tag for key in ("pressurized", "pressure")):
            mechanisms.append("diferença de pressão produz força sobre superfícies")
            if "sealed" in tags:
                consequences.append("tensões no recipiente dependem de pressão, geometria e resistência")
                hazards.append("falha estrutural não pode ser excluída sem medições")

        if not mechanisms:
            mechanisms.append("mecanismo insuficientemente especificado")
            consequences.append("não há previsão física robusta sem propriedades, ação e condições mensuráveis")

        confidence = max(0.0, min(confidence, 0.85))
        risk = "unknown_requires_measurement"
        if hazards:
            risk = "high" if any("elétrico" in h or "ignição" in h or "falha estrutural" in h for h in hazards) else "moderate"

        return {
            "object": _clean(object_label),
            "material": _clean(material),
            "properties": sorted(tags),
            "state": _clean(state),
            "environment": _clean(environment),
            "action": _clean(action),
            "mechanisms": mechanisms,
            "consequences": consequences,
            "risk": risk,
            "hazards": hazards,
            "confidence": confidence,
            "epistemic_kind": "inference",
            "requires_measurement_for_quantitative_prediction": True,
            "operational_authorization": False,
            "note": (
                "previsão qualitativa do world model; não substitui dados, modelo científico adequado, "
                "simulação/medição nem concede autorização para agir"
            ),
        }

    def physics_reference(self, query: str) -> dict | None:
        if self._physics_engine is None:
            from core.physics_knowledge_150k import PhysicsKnowledgeEngine, SOURCES
            self._physics_engine = (PhysicsKnowledgeEngine(), SOURCES)
        engine, sources = self._physics_engine
        topic = engine.match(query)
        if topic is None:
            return None
        return {
            "topic_id": topic.id,
            "domain": topic.domain,
            "level": topic.level,
            "title": topic.title,
            "formula": topic.formula,
            "summary": topic.summary,
            "source": sources[topic.source],
            "reuse": "core.physics_knowledge_150k",
        }

    def promote_canonical_physical(
        self,
        record_id: str,
        canonical_label: str,
        *,
        knowledge_type: str = "concept",
        topic: str,
        subtopics: list[str] | tuple[str, ...] | None = None,
        aliases: list[str] | tuple[str, ...] | None = None,
        properties: dict | None = None,
        contexts: list[str] | tuple[str, ...] | None = None,
        rules: list | tuple | None = None,
        exceptions: list | tuple | None = None,
        summary: str = "",
    ) -> dict:
        topic_key = _norm(topic)
        valid_topics = {key for key, _ in PHYSICAL_TOPICS}
        if topic_key not in valid_topics:
            raise ValueError(f"tema físico inválido: {topic}")
        return self.knowledge.promote_canonical(
            record_id,
            canonical_label,
            knowledge_type=knowledge_type,
            namespace=self.NAMESPACE,
            summary=summary,
            aliases=aliases,
            properties=properties,
            categories=["physical_world", topic_key],
            subtopics=subtopics,
            contexts=contexts,
            rules=rules,
            exceptions=exceptions,
            provenance={"physical_world_block": "B04", "topic": topic_key, "source_record_id": record_id},
        )

    def relate_physical(self, source_id: str, target_id: str, relation: str, *, weight: float = 1.0) -> dict:
        return self.knowledge.relate(
            source_id,
            target_id,
            relation,
            weight=weight,
            metadata={"physical_world": True, "block": "B04"},
        )

    def stats(self) -> dict:
        namespace = self.knowledge.store.get_namespace(self.NAMESPACE)
        return {
            "status": "experimental-integrated",
            "namespace": namespace,
            "catalog": self.catalog.stats(),
            "topics": [label for _, label in PHYSICAL_TOPICS],
            "matrix_axes": {name: list(values) for name, values in MATRIX_AXES},
            "quantities": PHYSICAL_QUANTITIES,
            "object_permanence_rules": list(OBJECT_PERMANENCE_RULES),
            "scene_objects": len(self._objects),
            "scene_persistence": "transient-world-model-not-canonical-knowledge",
            "knowledge_source": "BLOCO 3 universal knowledge",
            "epistemic_source": "BLOCO 2",
            "physics_reference": "core.physics_knowledge_150k",
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None

        if low in {
            "status bloco 4",
            "status mundo fisico",
            "status mundo físico",
            "modelo fisico fundamental do mundo",
            "modelo físico fundamental do mundo",
        }:
            stats = self.stats()
            return (
                "🌍 BLOCO 4 — MODELO FÍSICO FUNDAMENTAL DO MUNDO: "
                f"{stats['catalog']['addressable_contents']} conteúdos endereçáveis em B04 | "
                f"{stats['catalog']['themes']} temas × {stats['catalog']['subthemes_per_theme']} subtemas | "
                "matriz OBJETO×MATERIAL×PROPRIEDADE×ESTADO×AMBIENTE×AÇÃO×CONSEQUÊNCIA×RISCO | "
                f"objetos transitórios em cena={stats['scene_objects']} | "
                "Física científica=REUTILIZADA."
            )

        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🌍 {item['id']} — {item['topic_label']} / {item['subtheme_label']}\n{item['prompt']}"

        reference = re.match(r"^(?:referencia fisica|referência física|base fisica|base física)\s+(.+)$", raw, re.I)
        if reference:
            result = self.physics_reference(reference.group(1))
            if not result:
                return "Não encontrei uma referência física local específica para essa consulta."
            return (
                f"📐 {result['title']} — {result['summary']} "
                f"Relação-base: {result['formula']}. Fonte: {result['source']}."
            )

        return None
