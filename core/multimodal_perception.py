"""BLOCO 25 — PERCEPÇÃO MULTIMODAL.

Camada perceptiva compartilhada da STAR. Não substitui STAR Vision, áudio, voz,
localização ou sensores: recebe observações reais desses providers, normaliza,
faz fusão bounded e publica somente evidência perceptiva no B23/B24.

1B representa um espaço lógico endereçável de padrões perceptivos. Nada aqui
pré-carrega 1B objetos na RAM e ausência de sensor nunca é convertida em observação.
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
    text = "".join(c for c in text if not unicodedata.combining(c)).casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return default


MODALITIES = (
    "vision", "audio", "voice", "screen", "location",
    "sensor", "movement", "objects", "people", "environment", "time",
)

# 10 domínios x 10 ramos x 10 lentes = 1000 nós; cada nó possui 1M
# combinações interpretativas => 1B endereçáveis, materializadas sob demanda.
_DOMAINS = {
    "vision": ("forma", "cor", "textura", "profundidade", "luz", "cena", "gesto", "texto_visual", "mudanca_visual", "oclusao"),
    "audio_voice": ("fala", "prosodia", "som_ambiente", "musica", "impacto", "alarme", "direcao_sonora", "ritmo", "silencio", "mudanca_sonora"),
    "screen": ("janela", "texto_tela", "icone", "controle", "estado_ui", "notificacao", "erro_visual", "navegacao", "mudanca_tela", "foco"),
    "location_time": ("local", "proximidade", "trajeto", "regiao", "hora", "duracao", "sequencia", "recencia", "agenda", "mudanca_espacial"),
    "sensors": ("aceleracao", "rotacao", "orientacao", "temperatura", "pressao", "luminosidade", "proximidade", "estado_dispositivo", "conectividade", "qualidade_sinal"),
    "movement": ("direcao", "velocidade", "aceleracao", "trajetoria", "postura", "gesto", "aproximacao", "afastamento", "parada", "mudanca_movimento"),
    "objects": ("classe", "atributo", "estado", "posicao", "relacao", "uso", "mudanca", "quantidade", "identidade_incerta", "risco_objeto"),
    "people": ("presenca", "fala_pessoa", "movimento_pessoa", "gesto_pessoa", "posicao_pessoa", "interacao", "identidade_incerta", "grupo", "distancia", "mudanca_pessoa"),
    "environment": ("ambiente", "iluminacao", "ruido", "clima_local", "superficie", "espaco", "atividade", "perigo", "mudanca_ambiente", "contexto_fisico"),
    "fusion_events": ("coincidencia", "corroboracao", "conflito", "evento", "causalidade_incerta", "continuidade", "novidade", "anomalia", "confianca_fundida", "contexto_multimodal"),
}
_LENSES = ("caracteristica", "objeto", "evento", "som", "movimento", "ambiente", "situacao", "relacao", "incerteza", "tempo")
_AXES = (
    ("context", ("indoor","outdoor","device","social","work","leisure","transit","unknown","mixed","safety")),
    ("confidence", ("vlow","low","mlow","moderate","mhigh","high","vhigh","conflict","unknown","mixed")),
    ("temporal", ("instant","recent","session","day","week","long","historical","future","unknown","mixed")),
    ("salience", ("none","vlow","low","mlow","moderate","mhigh","high","vhigh","critical","mixed")),
    ("relation", ("isolated","same_source","cross_modal","spatial","temporal","causal_candidate","social","object","environment","mixed")),
    ("state", ("observed","provided","derived","fused","changed","stable","partial","occluded","unknown","conflicted")),
)
CANONICAL_NODES = len(_DOMAINS) * 10 * len(_LENSES)
VARIANTS_PER_NODE = prod(len(v) for _, v in _AXES)
ADDRESSABLE_CONTENTS = CANONICAL_NODES * VARIANTS_PER_NODE
if CANONICAL_NODES != 1000 or VARIANTS_PER_NODE != 1_000_000 or ADDRESSABLE_CONTENTS != 1_000_000_000:
    raise RuntimeError("escala B25 inválida")


@dataclass(frozen=True)
class PerceptualPattern:
    domain: str
    branch: str
    lens: str


class PerceptualCatalog:
    NAMESPACE = "B25"

    def stats(self) -> dict:
        return {
            "namespace": self.NAMESPACE,
            "modalities": MODALITIES,
            "domains": len(_DOMAINS),
            "canonical_nodes": CANONICAL_NODES,
            "variants_per_node": VARIANTS_PER_NODE,
            "addressable_contents": ADDRESSABLE_CONTENTS,
            "materialization": "on-demand",
            "truthfulness_note": "1B are addressable perceptual interpretations, not 1B observations or objects loaded in RAM",
        }

    @staticmethod
    def content_id(node_index: int, variant_index: int) -> str:
        if not 0 <= int(node_index) < CANONICAL_NODES:
            raise IndexError(node_index)
        if not 0 <= int(variant_index) < VARIANTS_PER_NODE:
            raise IndexError(variant_index)
        absolute = int(node_index) * VARIANTS_PER_NODE + int(variant_index) + 1
        return f"PERCEPT-B25-{absolute:010d}"

    def get_variant(self, identifier: str) -> dict | None:
        match = re.fullmatch(r"PERCEPT-B25-(\d{10})", _clean(identifier).upper())
        if not match:
            return None
        absolute = int(match.group(1))
        if not 1 <= absolute <= ADDRESSABLE_CONTENTS:
            return None
        node_index, variant = divmod(absolute - 1, VARIANTS_PER_NODE)
        domain_index, rest = divmod(node_index, 100)
        branch_index, lens_index = divmod(rest, 10)
        domain = tuple(_DOMAINS)[domain_index]
        branch = _DOMAINS[domain][branch_index]
        axes = {}
        value = variant
        for name, values in reversed(_AXES):
            value, offset = divmod(value, len(values))
            axes[name] = values[offset]
        axes = {name: axes[name] for name, _ in _AXES}
        return {
            "id": f"PERCEPT-B25-{absolute:010d}",
            "namespace": "B25",
            "domain": domain,
            "branch": branch,
            "lens": _LENSES[lens_index],
            **axes,
            "epistemic_kind": "perceptual_pattern",
            "is_observation": False,
        }


class MultimodalPerception:
    """Hub bounded de observações reais + Sensor Fusion."""

    NAMESPACE = "B25"
    MAX_BUFFER = 128
    MAX_FUSED = 32

    def __init__(self, knowledge: UniversalKnowledgeArchitecture):
        self.knowledge = knowledge
        self.graph = knowledge.graph
        self.catalog = PerceptualCatalog()
        self._buffer = deque(maxlen=self.MAX_BUFFER)
        self._providers: dict[str, Any] = {}
        self._counter = 0
        self.knowledge.register_namespace(
            "B25", "BLOCO 25 — PERCEPÇÃO MULTIMODAL",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/multimodal_perception.py",
            metadata={
                "materialization": "on-demand",
                "modalities": MODALITIES,
                "sensor_fusion": True,
                "bounded_buffer": self.MAX_BUFFER,
                "fabricates_observations": False,
                "operational_authorization": False,
            },
        )

    def attach_provider(self, modality: str, provider: Any) -> None:
        key = _norm(modality)
        if key not in MODALITIES:
            raise ValueError(f"modalidade não suportada: {modality}")
        self._providers[key] = provider

    def detach_provider(self, modality: str) -> None:
        self._providers.pop(_norm(modality), None)

    def ingest(self, modality: str, observation: dict, *, source: str = "") -> dict:
        key = _norm(modality)
        if key not in MODALITIES:
            raise ValueError(f"modalidade não suportada: {modality}")
        if not isinstance(observation, dict):
            raise TypeError("observation deve ser dict")
        content = _clean(observation.get("content") or observation.get("label") or observation.get("event"))
        if not content:
            raise ValueError("observação perceptiva requer content/label/event")
        self._counter += 1
        item = {
            "observation_id": f"B25-OBS-{self._counter:08d}",
            "modality": key,
            "content": content,
            "source": _clean(source or observation.get("source")) or f"b25:{key}",
            "timestamp": _clean(observation.get("timestamp")) or datetime.now(timezone.utc).isoformat(),
            "confidence": _clamp(observation.get("confidence"), 0.5),
            "importance": _clamp(observation.get("importance"), 0.6),
            "risk": _clamp(observation.get("risk"), 0.0),
            "urgency": _clamp(observation.get("urgency"), 0.0),
            "entities": tuple(_clean(x) for x in observation.get("entities", ()) if _clean(x))[:16],
            "attributes": deepcopy(dict(observation.get("attributes") or {})),
            "event_key": _clean(observation.get("event_key")) or None,
            "epistemic_kind": "observation",
            "fabricated": False,
            "operational_authorization": False,
        }
        self._buffer.append(item)
        return deepcopy(item)

    def poll_providers(self, *, per_provider_limit: int = 8) -> list[dict]:
        collected = []
        limit = max(1, min(int(per_provider_limit), 16))
        for modality, provider in tuple(self._providers.items()):
            if not hasattr(provider, "workspace_observations"):
                continue
            try:
                raw_items = list(provider.workspace_observations(limit=limit) or ())[:limit]
            except (OSError, RuntimeError, ValueError):
                continue
            for raw in raw_items:
                if isinstance(raw, dict):
                    collected.append(self.ingest(modality, raw, source=raw.get("source") or f"provider:{modality}"))
        return collected

    @staticmethod
    def _fusion_key(item: dict) -> str:
        if item.get("event_key"):
            return "event:" + _norm(item["event_key"])
        entities = tuple(sorted(_norm(x) for x in item.get("entities", ()) if _norm(x)))
        if entities:
            return "entities:" + "|".join(entities[:4])
        return "content:" + _norm(item.get("content"))[:80]

    def fuse(self, observations: Iterable[dict] | None = None, *, limit: int = 16) -> list[dict]:
        items = [deepcopy(x) for x in (observations if observations is not None else self._buffer) if isinstance(x, dict)]
        items = items[-self.MAX_BUFFER:]
        groups: dict[str, list[dict]] = {}
        for item in items:
            groups.setdefault(self._fusion_key(item), []).append(item)

        fused = []
        for key, group in groups.items():
            modalities = tuple(sorted({str(x.get("modality") or "unknown") for x in group}))
            miss_probability = 1.0
            for x in group:
                miss_probability *= 1.0 - (0.85 * _clamp(x.get("confidence"), 0.5))
            confidence = _clamp(1.0 - miss_probability)
            contents = []
            for x in group:
                value = _clean(x.get("content"))
                if value and value not in contents:
                    contents.append(value)
            # Divergência explícita entre conteúdos não é apagada pela fusão.
            conflict = len(contents) > 1 and len(group) > 1
            entities = []
            for x in group:
                for entity in x.get("entities", ()):
                    if entity not in entities:
                        entities.append(entity)
            fused.append({
                "content": contents[0] if len(contents) == 1 else " | ".join(contents[:4]),
                "source": "B25 Sensor Fusion",
                "modalities": modalities,
                "confidence": confidence,
                "importance": max((_clamp(x.get("importance"), 0.6) for x in group), default=0.6),
                "risk": max((_clamp(x.get("risk"), 0.0) for x in group), default=0.0),
                "urgency": max((_clamp(x.get("urgency"), 0.0) for x in group), default=0.0),
                "entities": tuple(entities[:16]),
                "evidence_ids": tuple(x.get("observation_id") for x in group if x.get("observation_id"))[:16],
                "fusion_key": key,
                "cross_modal": len(modalities) > 1,
                "conflict": conflict,
                "epistemic_kind": "fused_observation",
                "fabricated": False,
                "operational_authorization": False,
            })
        fused.sort(key=lambda x: (x["risk"], x["urgency"], x["importance"], x["confidence"]), reverse=True)
        return fused[:max(1, min(int(limit), self.MAX_FUSED))]

    def workspace_observations(self, limit: int = 16) -> list[dict]:
        self.poll_providers(per_provider_limit=4)
        return self.fuse(limit=limit)

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace("B25"),
            "catalog": self.catalog.stats(),
            "providers": tuple(sorted(self._providers)),
            "buffered_observations": len(self._buffer),
            "buffer_limit": self.MAX_BUFFER,
            "sensor_fusion": True,
            "fabricates_observations": False,
        }

    def handle(self, text: str) -> str | None:
        raw = _clean(text)
        low = raw.casefold()
        if low in {"status bloco 25", "status percepção multimodal", "status percepcao multimodal"}:
            s = self.stats()
            return (
                f"👁️ BLOCO 25 — PERCEPÇÃO MULTIMODAL: {s['catalog']['addressable_contents']} padrões endereçáveis | "
                f"{len(MODALITIES)} modalidades | Sensor Fusion=ATIVO | providers={len(s['providers'])}."
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"👁️ {item['id']} — {item['domain']} / {item['branch']} / {item['lens']}"
        return None
