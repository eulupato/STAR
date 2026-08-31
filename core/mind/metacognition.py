"""Metacognição operacional da STAR MIND V2.

Armazena telemetria e decisões de roteamento observáveis. Não registra cadeia
privada de raciocínio.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CognitiveTrace:
    request_id: str
    input_excerpt: str
    salience: float
    priority: str
    plan_steps: tuple[str, ...]
    selected_step: str
    elapsed_ms: float
    event_count: int
    errors: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


class Metacognition:
    def __init__(self, history_limit: int = 64):
        self._traces = deque(maxlen=max(16, int(history_limit)))

    def record(self, trace: CognitiveTrace):
        self._traces.append(trace)
        return trace

    @property
    def last(self):
        return self._traces[-1] if self._traces else None

    def snapshot(self, limit: int = 5):
        return [trace.to_dict() for trace in list(self._traces)[-limit:]]
