"""BLOCO 25 — PERCEPÇÃO MULTIMODAL.

Camada local-first de ingestão e Sensor Fusion sobre providers opcionais. O módulo
não inicia câmera, microfone, captura de tela, localização ou sensores por conta
própria. Observações entram explicitamente ou por coleta autorizada, permanecem
bounded e a fusão é inferência — nunca fato canônico automático.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
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


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return max(0.0, min(float(default), 1.0))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _unique(values: Iterable[Any], *, limit: int = 64) -> tuple[str, ...]:
    out: list[str] = []
    for value in values:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
        if len(out) >= limit:
            break
    return tuple(out)


REQUIRED_MODALITIES = (
    "vision", "audio", "voice", "screen", "location", "sensors", "motion",
    "objects", "people", "environment", "time",
)

INTEGRATED_REFERENCES = {
    "vision": ("modules.vision", "modules.vision_model (hand tracking only)"),
    "audio": ("voice.audio_input.AudioRecorder",),
    "voice": ("voice.manager", "voice.audio_input.AudioRecorder"),
    "screen": ("modules.computer_control.take_screenshot (manual action only)",),
    "location": (),
    "sensors": (),
    "motion": ("modules.vision gesture/point tracking",),
    "objects": (),
    "people": (),
    "environment": (),
    "time": ("system clock timestamp metadata",),
}

PERCEPTION_POLICY = {
    "automatic_camera_start": False,
    "automatic_microphone_start": False,
    "automatic_screen_capture": False,
    "automatic_location_access": False,
    "automatic_sensor_polling": False,
    "provider_collection_requires_explicit_permission": True,
    "fused_perception_is_canonical_fact": False,
    "sensor_fusion_is_inference": True,
    "contradictions_are_preserved": True,
    "loads_full_logical_space": False,
    "runtime_buffer_bounded": True,
    "operational_authorization": False,
    "rule": "PERCEPÇÃO ≠ FATO CANÔNICO; PROVIDER DISPONÍVEL ≠ PERMISSÃO PARA CAPTURAR",
}


@dataclass(frozen=True)
class PerceptionBranch:
    domain: str
    key: str
    label: str
    subtopics: tuple[str, ...]


def _subs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(";") if item.strip())


_DOMAINS = {
    "vision": (
        ("visual_signal", "Sinal visual", "visão;imagem;frame;características;confiança"),
        ("visual_features", "Características visuais", "cor;forma;textura;bordas;luminosidade"),
        ("visual_objects", "Objetos visuais", "objetos;partes;estado;posição;oclusão"),
        ("visual_people", "Pessoas no campo visual", "pessoas;presença;postura;contexto;incerteza"),
        ("visual_events", "Eventos visuais", "mudança;aparecimento;desaparecimento;movimento;evento"),
    ),
    "audio_voice": (
        ("audio_signal", "Sinal de áudio", "áudio;onda;intensidade;frequência;ruído"),
        ("sound_events", "Eventos sonoros", "sons;evento;origem;duração;ambiente"),
        ("voice_signal", "Voz", "voz;fala;turno;prosódia;confiança"),
        ("speech_features", "Características de fala", "ritmo;pausas;volume;pitch;conteúdo"),
        ("acoustic_context", "Contexto acústico", "silêncio;ruído;direção;distância;ambiente"),
    ),
    "screen_digital": (
        ("screen_frame", "Tela", "tela;frame;janela;aplicativo;estado"),
        ("ui_elements", "Elementos de interface", "botão;menu;campo;ícone;layout"),
        ("screen_text", "Texto na tela", "texto;rótulo;documento;mensagem;contexto"),
        ("digital_events", "Eventos digitais", "notificação;mudança;foco;erro;evento"),
        ("screen_context", "Contexto de tela", "app;tarefa;janela;privacidade;incerteza"),
    ),
    "location_spatial": (
        ("location", "Localização", "localização;coordenada;lugar;precisão;fonte"),
        ("spatial_relation", "Relações espaciais", "perto;longe;dentro;fora;direção"),
        ("navigation_context", "Contexto de navegação", "rota;posição;destino;movimento;escala"),
        ("place_environment", "Lugar e ambiente", "local;ambiente;região;interior;exterior"),
        ("location_uncertainty", "Incerteza espacial", "precisão;erro;sinal;atualização;unknown"),
    ),
    "sensors_motion": (
        ("sensor_state", "Estado de sensores", "sensores;leitura;estado;calibração;disponibilidade"),
        ("motion", "Movimento", "movimento;velocidade;direção;mudança;trajetória"),
        ("orientation", "Orientação e aceleração", "orientação;aceleração;rotação;postura;vetor"),
        ("gesture_movement", "Gestos e movimentos", "gesto;mão;corpo;sequência;intenção não presumida"),
        ("sensor_health", "Qualidade do sensor", "latência;ruído;falha;calibração;confiança"),
    ),
    "objects_people": (
        ("object_presence", "Presença de objetos", "objeto;presença;identidade provável;posição;estado"),
        ("object_relation", "Relações entre objetos", "sobre;dentro;perto;parte;interação"),
        ("people_presence", "Presença de pessoas", "pessoa;presença;distância;posição;privacidade"),
        ("people_relations", "Relações perceptíveis", "proximidade;grupo;interação;sem inferir intenção"),
        ("object_person_interaction", "Interação pessoa-objeto", "uso;contato;movimento;contexto;alternativas"),
    ),
    "environment": (
        ("environment_type", "Tipo de ambiente", "ambiente;interno;externo;construído;natural"),
        ("ambient_conditions", "Condições ambientais", "luz;som;temperatura declarada;visibilidade;ruído"),
        ("environment_events", "Eventos ambientais", "mudança;evento;risco;origem;tempo"),
        ("environment_hazards", "Riscos ambientais", "risco;obstáculo;alerta;incerteza;contexto"),
        ("environment_context", "Contexto ambiental", "atividade;local;pessoas;objetos;situação"),
    ),
    "time": (
        ("timestamp", "Tempo e timestamp", "tempo;timestamp;relógio;fonte;fuso"),
        ("duration", "Duração", "duração;intervalo;início;fim;incerteza"),
        ("sequence", "Sequência temporal", "antes;depois;ordem;evento;causalidade não presumida"),
        ("recurrence", "Recorrência", "padrão;repetição;frequência;ciclo;janela"),
        ("synchronization", "Sincronização", "modalidades;latência;janela temporal;clock;alinhamento"),
    ),
    "events_patterns": (
        ("event_detection", "Detecção de eventos", "evento;mudança;sinal;limiar;contexto"),
        ("pattern_recognition", "Padrões perceptivos", "padrão;semelhança;repetição;característica;incerteza"),
        ("novelty", "Novidade e mudança", "novidade;desvio;baseline;mudança;alerta"),
        ("cross_modal", "Correspondência entre modalidades", "visão;som;movimento;tempo;entidade"),
        ("perceptual_uncertainty", "Incerteza perceptiva", "confiança;ruído;ambiguidade;alternativas;revisão"),
    ),
    "sensor_fusion": (
        ("fusion", "Sensor Fusion", "fusão;modalidades;observações;inferência;proveniência"),
        ("temporal_alignment", "Alinhamento temporal", "timestamp;janela;latência;ordem;sincronização"),
        ("confidence_fusion", "Combinação de confiança", "confiança;qualidade;fonte;discordância;calibração"),
        ("contradiction_fusion", "Contradições entre sensores", "conflito;features;fontes;preservação;revisão"),
        ("fused_situation", "Situação perceptiva fundida", "situação;objetos;pessoas;sons;movimentos;ambiente"),
    ),
}

DOMAIN_LABELS = {
    "vision": "Visão",
    "audio_voice": "Áudio e voz",
    "screen_digital": "Tela e contexto digital",
    "location_spatial": "Localização e espaço",
    "sensors_motion": "Sensores e movimento",
    "objects_people": "Objetos e pessoas",
    "environment": "Ambiente",
    "time": "Tempo",
    "events_patterns": "Eventos e padrões",
    "sensor_fusion": "Sensor Fusion",
}

PERCEPTION_BRANCHES = tuple(
    PerceptionBranch(domain, key, label, _subs(subtopics))
    for domain, branches in _DOMAINS.items()
    for key, label, subtopics in branches
)

PERCEPTION_LENSES = (
    ("feature", "característica", "identificar características sem extrapolar além do sinal"),
    ("entity", "entidade", "relacionar objetos/pessoas preservando incerteza"),
    ("event", "evento", "representar eventos e mudanças observáveis"),
    ("relation", "relação", "relacionar sinais, entidades e modalidades"),
    ("temporal", "tempo", "preservar timestamp, ordem e latência"),
    ("spatial", "espaço", "preservar posição e precisão quando disponíveis"),
    ("confidence", "confiança", "calibrar confiança e qualidade da fonte"),
    ("context", "contexto", "situar a observação no ambiente/situação"),
    ("alternatives", "alternativas", "preservar ambiguidades e contradições"),
    ("fusion", "fusão", "combinar evidências sem promover fato automaticamente"),
)

CHANNEL_AXIS = ("vision", "audio_voice", "screen", "location", "sensors", "motion", "objects_people", "environment", "time", "multimodal")
FEATURE_AXIS = ("presence", "identity", "state", "position", "shape_signal", "intensity", "movement", "change", "relation", "unknown")
CONFIDENCE_AXIS = ("unknown", "very_low", "low", "moderate_low", "moderate", "moderate_high", "high", "very_high", "calibrated", "conflicting")
TEMPORAL_AXIS = ("instant", "milliseconds", "seconds", "recent", "session", "recurrent", "sequence", "historical", "future_prediction", "unknown")
RELATION_AXIS = ("independent", "co_observed", "supports", "conflicts", "contextualizes")
SOURCE_AXIS = ("provider", "explicit_input", "derived_fusion", "unknown")
CONTEXT_AXIS = ("private", "public", "home", "work", "mobility", "digital", "social", "emergency", "ambient", "mixed")
VARIANT_AXES = (
    ("channel", CHANNEL_AXIS),
    ("feature", FEATURE_AXIS),
    ("confidence", CONFIDENCE_AXIS),
    ("temporal", TEMPORAL_AXIS),
    ("relation", RELATION_AXIS),
    ("source", SOURCE_AXIS),
    ("context", CONTEXT_AXIS),
)

CANONICAL_NODES = len(PERCEPTION_BRANCHES) * len(PERCEPTION_LENSES)
VARIANTS_PER_NODE = prod(len(values) for _, values in VARIANT_AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE
if len(_DOMAINS) != 10 or len(PERCEPTION_BRANCHES) != 50 or len(PERCEPTION_LENSES) != 10:
    raise RuntimeError("B25 requer 10 domínios, 50 ramos e 10 lentes")
if CANONICAL_NODES != 500 or VARIANTS_PER_NODE != 2_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B25 inválida")


def _decode(index: int) -> dict[str, str]:
    if not 0 <= int(index) < VARIANTS_PER_NODE:
        raise IndexError(index)
    value = int(index)
    out: dict[str, str] = {}
    for name, values in reversed(VARIANT_AXES):
        value, offset = divmod(value, len(values))
        out[name] = values[offset]
    return {name: out[name] for name, _ in VARIANT_AXES}


class PerceptionCatalog:
    def stats(self) -> dict:
        return {
            "namespace": "B25",
            "domains": 10,
            "branches": 50,
            "lenses_per_branch": 10,
            "canonical_nodes": 500,
            "variants_per_node": 2_000_000,
            "addressable_contents": 1_000_000_000,
            "materialization": "on-demand",
            "preloaded_patterns": 0,
            "truthfulness_note": "1B are addressable perceptual contexts/patterns, not pre-recorded sensor data",
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < 500 or not 0 <= int(variant_index) < 2_000_000:
            raise IndexError((node_index, variant_index))
        return f"PER-B25-{int(node_index) * 2_000_000 + int(variant_index) + 1:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"PER-B25-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= 1_000_000_000:
            return None
        node_index, variant_index = divmod(absolute - 1, 2_000_000)
        branch_index, lens_index = divmod(node_index, 10)
        branch = PERCEPTION_BRANCHES[branch_index]
        lens_key, lens_label, instruction = PERCEPTION_LENSES[lens_index]
        return {
            "id": f"PER-B25-{absolute:010d}",
            "namespace": "B25",
            "domain": branch.domain,
            "domain_label": DOMAIN_LABELS[branch.domain],
            "branch": branch.key,
            "branch_label": branch.label,
            "subtopics": branch.subtopics,
            "lens": lens_key,
            "lens_label": lens_label,
            **_decode(variant_index),
            "prompt": f"{branch.label} / {lens_label}: {instruction}. Sensor Fusion preserva fonte, confiança e contradições.",
        }


class SensorFusion:
    """Fusão bounded e explicável de observações já obtidas."""

    def __init__(self, max_inputs: int = 32):
        self.max_inputs = max(2, min(int(max_inputs), 64))

    @staticmethod
    def _feature_conflicts(observations: list[dict]) -> tuple[dict, ...]:
        by_key: dict[str, dict[str, list[str]]] = {}
        for obs in observations:
            features = obs.get("features") or {}
            if not isinstance(features, dict):
                continue
            for key, raw_value in features.items():
                k = _clean(key)
                value = _clean(raw_value)
                if not k or not value:
                    continue
                by_key.setdefault(k, {}).setdefault(value, []).append(obs["observation_id"])
        conflicts = []
        for key, values in by_key.items():
            if len(values) > 1:
                conflicts.append({"feature": key, "values": deepcopy(values)})
        return tuple(conflicts[:32])

    @staticmethod
    def _relations(observations: list[dict]) -> tuple[dict, ...]:
        relations: list[dict] = []
        for index, left in enumerate(observations):
            left_entities = set(left.get("objects") or ()) | set(left.get("people") or ())
            for right in observations[index + 1:]:
                right_entities = set(right.get("objects") or ()) | set(right.get("people") or ())
                shared = sorted(left_entities & right_entities)
                relation = "shared_entity" if shared else "co_observed"
                relations.append({
                    "source_id": left["observation_id"],
                    "target_id": right["observation_id"],
                    "relation": relation,
                    "shared_entities": shared[:8],
                })
                if len(relations) >= 64:
                    return tuple(relations)
        return tuple(relations)

    def fuse(self, observations: Iterable[dict], *, fusion_id: str) -> dict:
        items = [deepcopy(item) for item in list(observations)[: self.max_inputs] if isinstance(item, dict)]
        if not items:
            return {
                "fusion_id": fusion_id,
                "status": "empty",
                "source_observations": (),
                "modalities": (),
                "epistemic_kind": "inference",
                "canonical_fact": False,
                "fabricated": False,
                "operational_authorization": False,
            }
        conflicts = self._feature_conflicts(items)
        confidences = [_clamp(item.get("confidence"), 0.5) for item in items]
        base_confidence = sum(confidences) / len(confidences)
        conflict_discount = max(0.5, 1.0 - min(len(conflicts), 5) * 0.08)
        fused_confidence = round(_clamp(base_confidence * conflict_discount), 6)
        modalities = _unique(item.get("modality") for item in items)
        objects = _unique(value for item in items for value in (item.get("objects") or ()))
        people = _unique(value for item in items for value in (item.get("people") or ()))
        events = _unique(value for item in items for value in (item.get("events") or ()))
        sounds = _unique(value for item in items for value in (item.get("sounds") or ()))
        movements = _unique(value for item in items for value in (item.get("movements") or ()))
        environments = _unique(item.get("environment") for item in items if item.get("environment"))
        locations = _unique(item.get("location") for item in items if item.get("location"))
        snippets = _unique((item.get("content") for item in items), limit=4)
        summary = " | ".join(snippets) if snippets else f"Fusão de {len(items)} observações"
        return {
            "fusion_id": fusion_id,
            "status": "fused",
            "content": summary,
            "source_observations": tuple(item["observation_id"] for item in items),
            "modalities": modalities,
            "confidence": fused_confidence,
            "importance": max(_clamp(item.get("importance"), 0.5) for item in items),
            "risk": max(_clamp(item.get("risk"), 0.0) for item in items),
            "urgency": max(_clamp(item.get("urgency"), 0.0) for item in items),
            "objects": objects,
            "people": people,
            "events": events,
            "sounds": sounds,
            "movements": movements,
            "environments": environments,
            "locations": locations,
            "relations": self._relations(items),
            "contradictions": conflicts,
            "sources": tuple({"source": item.get("source"), "reference": item.get("reference")} for item in items),
            "observed_at": tuple(item.get("observed_at") for item in items),
            "epistemic_kind": "inference",
            "sensor_fusion": True,
            "canonical_fact": False,
            "fabricated": False,
            "operational_authorization": False,
        }


class MultimodalPerception:
    NAMESPACE = "B25"
    TAXONOMY_ROOT_ID = "MULTIMODAL-PERCEPTION-TAX-ROOT"

    def __init__(
        self,
        knowledge: UniversalKnowledgeArchitecture,
        *,
        max_observations: int = 128,
        max_fusions: int = 64,
    ):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.max_observations = max(32, min(int(max_observations), 512))
        self.max_fusions = max(16, min(int(max_fusions), 128))
        self._observations: deque[dict] = deque(maxlen=self.max_observations)
        self._fusions: deque[dict] = deque(maxlen=self.max_fusions)
        self._providers: dict[str, Any] = {}
        self._observation_counter = 0
        self._fusion_counter = 0
        self.fusion = SensorFusion(max_inputs=32)
        self.catalog = PerceptionCatalog()
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 25 — PERCEPÇÃO MULTIMODAL",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/multimodal_perception.py",
            metadata={
                "materialization": "on-demand",
                "runtime_observation_buffer": self.max_observations,
                "runtime_fusion_buffer": self.max_fusions,
                "sensor_fusion": True,
                "automatic_capture": False,
                "existing_references": deepcopy(INTEGRATED_REFERENCES),
                "persistent_sensor_store": False,
            },
        )

    def register_provider(self, modality: str, provider: Any) -> dict:
        key = _norm(modality)
        if key not in REQUIRED_MODALITIES:
            raise KeyError(modality)
        if provider is None:
            raise ValueError("provider não pode ser None")
        self._providers[key] = provider
        return self.provider_status(key)

    def unregister_provider(self, modality: str) -> None:
        self._providers.pop(_norm(modality), None)

    def provider_status(self, modality: str | None = None) -> dict:
        keys = (_norm(modality),) if modality is not None else REQUIRED_MODALITIES
        result: dict[str, dict] = {}
        for key in keys:
            if key not in REQUIRED_MODALITIES:
                raise KeyError(key)
            provider = self._providers.get(key)
            result[key] = {
                "provider_attached": provider is not None,
                "status": "attached_idle" if provider is not None else "unavailable",
                "integrated_references": INTEGRATED_REFERENCES.get(key, ()),
                "automatic_collection": False,
                "permission_required_to_collect": True,
            }
        return result[_norm(modality)] if modality is not None else result

    def workspace_available(self) -> bool:
        return bool(self._observations or self._fusions)

    def ingest(
        self,
        modality: str,
        content: Any = "",
        *,
        source: str,
        reference: str = "",
        observed_at: str | None = None,
        confidence: float = 0.5,
        importance: float = 0.5,
        risk: float = 0.0,
        urgency: float = 0.0,
        features: dict | None = None,
        objects: Iterable[Any] | None = None,
        people: Iterable[Any] | None = None,
        events: Iterable[Any] | None = None,
        sounds: Iterable[Any] | None = None,
        movements: Iterable[Any] | None = None,
        environment: Any = None,
        location: Any = None,
        metadata: dict | None = None,
    ) -> dict:
        key = _norm(modality)
        if key not in REQUIRED_MODALITIES:
            raise KeyError(modality)
        if not _clean(source):
            raise ValueError("observação requer source")
        structured = any((features, objects, people, events, sounds, movements, environment, location))
        if not _clean(content) and not structured:
            raise ValueError("observação vazia")
        self._observation_counter += 1
        observation = {
            "observation_id": f"PERCEPT-OBS-{self._observation_counter:010d}",
            "modality": key,
            "content": _clean(content),
            "source": _clean(source),
            "reference": _clean(reference) or None,
            "observed_at": _clean(observed_at) or _now(),
            "confidence": _clamp(confidence),
            "importance": _clamp(importance),
            "risk": _clamp(risk, 0.0),
            "urgency": _clamp(urgency, 0.0),
            "features": deepcopy(dict(features or {})),
            "objects": _unique(objects or ()),
            "people": _unique(people or ()),
            "events": _unique(events or ()),
            "sounds": _unique(sounds or ()),
            "movements": _unique(movements or ()),
            "environment": _clean(environment) or None,
            "location": _clean(location) or None,
            "metadata": deepcopy(metadata or {}),
            "epistemic_kind": "observation",
            "canonical_fact": False,
            "fabricated": False,
            "operational_authorization": False,
        }
        self._observations.append(observation)
        return deepcopy(observation)

    def ingest_batch(self, observations: Iterable[dict], *, fuse: bool = False) -> dict:
        ingested = []
        for raw in list(observations)[:64]:
            if not isinstance(raw, dict):
                continue
            payload = deepcopy(raw)
            modality = payload.pop("modality", None)
            source = payload.pop("source", None)
            content = payload.pop("content", "")
            if modality and source:
                ingested.append(self.ingest(modality, content, source=source, **payload))
        result = {"ingested": tuple(ingested), "count": len(ingested), "bounded": True}
        if fuse and ingested:
            result["fusion"] = self.fuse_recent(limit=min(len(ingested), 32))
        return result

    def recent(self, *, modality: str | None = None, limit: int = 16) -> list[dict]:
        key = _norm(modality) if modality else None
        if key and key not in REQUIRED_MODALITIES:
            raise KeyError(modality)
        selected = [item for item in reversed(self._observations) if key is None or item["modality"] == key]
        return deepcopy(selected[: max(1, min(int(limit), 64))])

    def fuse_recent(self, *, limit: int = 16) -> dict:
        observations = list(reversed(self._observations))[: max(2, min(int(limit), 32))]
        self._fusion_counter += 1
        result = self.fusion.fuse(reversed(observations), fusion_id=f"PERCEPT-FUSION-{self._fusion_counter:010d}")
        if result.get("status") == "fused":
            self._fusions.append(result)
        return deepcopy(result)

    def collect(self, modalities: Iterable[str] | None = None, *, permission: bool = False, limit_per_modality: int = 8) -> dict:
        requested = tuple(_norm(item) for item in (modalities or self._providers.keys()))
        requested = tuple(item for item in requested if item in REQUIRED_MODALITIES)
        if not permission:
            return {
                "collected": (),
                "requested": requested,
                "permission": False,
                "providers_called": False,
                "denied": True,
                "operational_authorization": False,
            }
        collected = []
        failures = []
        per_limit = max(1, min(int(limit_per_modality), 16))
        for modality in requested:
            provider = self._providers.get(modality)
            if provider is None:
                continue
            try:
                if hasattr(provider, "read_observations"):
                    raw = provider.read_observations(limit=per_limit)
                elif callable(provider):
                    raw = provider(limit=per_limit)
                else:
                    failures.append({"modality": modality, "error": "unsupported_provider_interface"})
                    continue
            except (OSError, RuntimeError, ValueError, TypeError, AttributeError) as exc:
                failures.append({"modality": modality, "error": type(exc).__name__})
                continue
            items = raw if isinstance(raw, (list, tuple)) else [raw]
            for item in list(items)[:per_limit]:
                if isinstance(item, dict):
                    payload = deepcopy(item)
                    content = payload.pop("content", "")
                    source = payload.pop("source", f"provider:{modality}")
                    payload.pop("modality", None)
                    collected.append(self.ingest(modality, content, source=source, **payload))
        return {
            "collected": tuple(collected),
            "count": len(collected),
            "requested": requested,
            "permission": True,
            "providers_called": True,
            "failures": tuple(failures),
            "bounded": True,
            "operational_authorization": False,
        }

    def workspace_observations(self, limit: int = 16) -> list[dict]:
        limit = max(1, min(int(limit), 32))
        candidates: list[dict] = []
        for fusion in reversed(self._fusions):
            entities = _unique((*fusion.get("objects", ()), *fusion.get("people", ())))
            candidates.append({
                "content": fusion.get("content") or "multimodal fusion",
                "source": "perception:fusion",
                "importance": fusion.get("importance", 0.6),
                "risk": fusion.get("risk", 0.0),
                "urgency": fusion.get("urgency", 0.0),
                "confidence": fusion.get("confidence", 0.5),
                "entities": entities,
                "metadata": deepcopy(fusion),
            })
            if len(candidates) >= limit:
                return candidates
        for obs in reversed(self._observations):
            entities = _unique((*obs.get("objects", ()), *obs.get("people", ())))
            candidates.append({
                "content": obs.get("content") or f"{obs['modality']} observation",
                "source": f"perception:{obs['modality']}",
                "importance": obs.get("importance", 0.5),
                "risk": obs.get("risk", 0.0),
                "urgency": obs.get("urgency", 0.0),
                "confidence": obs.get("confidence", 0.5),
                "entities": entities,
                "metadata": deepcopy(obs),
            })
            if len(candidates) >= limit:
                break
        return candidates

    def snapshot(self) -> dict:
        return {
            "observations_buffered": len(self._observations),
            "fusions_buffered": len(self._fusions),
            "max_observations": self.max_observations,
            "max_fusions": self.max_fusions,
            "workspace_available": self.workspace_available(),
            "providers": self.provider_status(),
            "recent": self.recent(limit=8) if self._observations else [],
            "policy": deepcopy(PERCEPTION_POLICY),
        }

    def materialize_taxonomy(self, domain: str | None = None) -> dict:
        key = _norm(domain) if domain else None
        if key and key not in _DOMAINS:
            raise KeyError(domain)
        branches = [branch for branch in PERCEPTION_BRANCHES if key is None or branch.domain == key]
        root = self.graph.add_entity(
            "multimodal_perception_taxonomy",
            "PERCEPÇÃO MULTIMODAL",
            node_id=self.TAXONOMY_ROOT_ID,
            data={"block": "B25", "sensor_fusion": True, "automatic_capture": False},
        )
        for source_id, label in (
            ("GLOBAL-WORKSPACE-TAX-ROOT", "B23 Global Workspace"),
            ("MIND-LOOP-TAX-ROOT", "B24 Mind Loop"),
            ("PHYSICAL-WORLD-TAX-ROOT", "B04 Physical World"),
        ):
            self.graph.add_entity("perception_integration", label, node_id=source_id, data={"block": "B25"})
            self.graph.relate(root, source_id, "integrates", metadata={"block": "B25"})
        for branch in branches:
            domain_id = f"PER-DOM-{branch.domain.upper()}"
            branch_id = f"PER-BR-{branch.key.upper()}"
            self.graph.add_entity("perception_domain", DOMAIN_LABELS[branch.domain], node_id=domain_id, data={"block": "B25"})
            self.graph.add_entity("perception_branch", branch.label, node_id=branch_id, data={"block": "B25"})
            self.graph.relate(root, domain_id, "has_part", metadata={"block": "B25"})
            self.graph.relate(domain_id, branch_id, "has_part", metadata={"block": "B25"})
        return {"domain": key, "branches_materialized": len(branches), "shared_graph": True, "parallel_sensor_store": False}

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace("B25"),
            "catalog": self.catalog.stats(),
            "modalities": REQUIRED_MODALITIES,
            "providers": self.provider_status(),
            "sensor_fusion": True,
            "policy": deepcopy(PERCEPTION_POLICY),
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if not raw:
            return None
        if low in {"status bloco 25", "status percepção multimodal", "status percepcao multimodal", "percepção multimodal", "percepcao multimodal", "sensor fusion"}:
            return (
                f"⭐ BLOCO 25 — PERCEPÇÃO MULTIMODAL: {ADDRESSABLE_CONTENTS} representações | "
                f"{len(REQUIRED_MODALITIES)} modalidades/contextos | Sensor Fusion=SIM | captura automática=NÃO."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"⭐ {item['id']} — {item['domain_label']} / {item['branch_label']} / {item['lens_label']}\n{item['prompt']}"
        return None
