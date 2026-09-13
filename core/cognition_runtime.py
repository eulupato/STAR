"""Runtime cognitivo incremental: contexto, saliência e seleção de motores.

Não substitui o STAR MIND. Ele fornece estruturas operacionais pequenas para que
MIND/Core tenham contexto priorizado e uma política explícita de escolha de engine.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import math
import re
import time


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(value: str) -> set[str]:
    return {x for x in re.findall(r"[\wÀ-ÿ]+", str(value).lower()) if len(x) > 1}


@dataclass(frozen=True)
class ContextItem:
    kind: str
    content: str
    importance: float
    timestamp: str
    monotonic_time: float
    metadata: dict


class WorkingContext:
    """Janela de contexto local, limitada e priorizável; não é memória persistente."""

    def __init__(self, max_items: int = 128):
        self.items = deque(maxlen=max(16, min(int(max_items), 2048)))

    def add(self, kind: str, content: str, *, importance: float = 0.5, metadata=None) -> dict:
        item = ContextItem(str(kind), str(content), max(0.0, min(float(importance), 1.0)), _now(), time.monotonic(), dict(metadata or {}))
        self.items.append(item)
        return asdict(item)

    def select(self, query: str = "", *, limit: int = 12, half_life_seconds: float = 900.0) -> list[dict]:
        now = time.monotonic(); query_tokens = _tokens(query); scored = []
        for item in self.items:
            age = max(0.0, now - item.monotonic_time)
            recency = math.exp(-math.log(2) * age / max(1.0, half_life_seconds))
            item_tokens = _tokens(item.content)
            relevance = 0.0 if not query_tokens else len(query_tokens & item_tokens) / max(1, len(query_tokens))
            score = 0.45 * item.importance + 0.35 * relevance + 0.20 * recency
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [{**asdict(item), "salience": round(score, 6)} for score, item in scored[:max(1, min(int(limit), 100))]]

    def clear(self):
        self.items.clear()


class SalienceEngine:
    """Prioriza eventos por relevância, novidade, risco e urgência declarados."""

    @staticmethod
    def score(*, relevance: float = 0.5, novelty: float = 0.5, risk: float = 0.0,
              urgency: float = 0.0, user_priority: float = 0.5) -> float:
        values = [max(0.0, min(float(v), 1.0)) for v in (relevance, novelty, risk, urgency, user_priority)]
        relevance, novelty, risk, urgency, user_priority = values
        raw = 0.30 * relevance + 0.15 * novelty + 0.20 * risk + 0.15 * urgency + 0.20 * user_priority
        return round(max(0.0, min(raw, 1.0)), 6)


@dataclass(frozen=True)
class EngineProfile:
    name: str
    capabilities: tuple[str, ...]
    local: bool = True
    network_required: bool = False
    cost: float = 0.0
    latency: float = 0.5
    quality: float = 0.5
    enabled: bool = True


class ModelRouter:
    """Seleciona engines por capacidade/restrições; não inventa modelos instalados."""

    def __init__(self):
        self.profiles: dict[str, EngineProfile] = {}
        self.register(EngineProfile("internal_knowledge", ("knowledge", "identity"), quality=0.65, latency=0.05))
        self.register(EngineProfile("math_sympy", ("math", "symbolic"), quality=0.95, latency=0.05))
        self.register(EngineProfile("document_rag", ("documents", "rag"), quality=0.75, latency=0.2))
        self.register(EngineProfile("semantic_rag", ("documents", "rag", "semantic"), quality=0.82, latency=0.35))
        self.register(EngineProfile("research_hub", ("research", "literature"), local=False, network_required=True, cost=0.05, latency=0.8, quality=0.85))
        self.register(EngineProfile("scientific_simulation", ("simulation", "science"), quality=0.9, latency=0.4))

    def register(self, profile: EngineProfile):
        self.profiles[profile.name] = profile

    def choose(self, capability: str, *, network_enabled: bool = False, prefer_local: bool = True,
               max_cost: float = 1.0) -> dict | None:
        capability = str(capability).strip().lower()
        candidates = []
        for profile in self.profiles.values():
            if not profile.enabled or capability not in profile.capabilities:
                continue
            if profile.network_required and not network_enabled:
                continue
            if profile.cost > max_cost:
                continue
            local_bonus = 0.15 if prefer_local and profile.local else 0.0
            score = 0.65 * profile.quality - 0.20 * profile.latency - 0.15 * profile.cost + local_bonus
            candidates.append((score, profile))
        if not candidates:
            return None
        candidates.sort(key=lambda x: (x[0], x[1].quality), reverse=True)
        score, profile = candidates[0]
        return {**asdict(profile), "routing_score": round(score, 6)}

    def stats(self) -> dict:
        return {"profiles": len(self.profiles), "enabled": sum(1 for x in self.profiles.values() if x.enabled),
                "automatic_external_model_discovery": False, "policy": "explicit registered engines only"}


class CognitiveRuntime:
    def __init__(self):
        self.context = WorkingContext()
        self.salience = SalienceEngine()
        self.router = ModelRouter()

    def observe(self, kind: str, content: str, *, relevance=0.5, novelty=0.5, risk=0.0, urgency=0.0, user_priority=0.5, metadata=None):
        importance = self.salience.score(relevance=relevance, novelty=novelty, risk=risk, urgency=urgency, user_priority=user_priority)
        return self.context.add(kind, content, importance=importance, metadata=metadata)

    def stats(self) -> dict:
        return {"status": "alpha-local", "working_context_items": len(self.context.items),
                "salience": "weighted explicit factors", "model_router": self.router.stats(),
                "persistent_memory_source": "existing CognitiveStore", "parallel_memory_system": False}
