"""Event Bus local da STAR MIND V2."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable
from uuid import uuid4


@dataclass(frozen=True)
class MindEvent:
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "mind"
    event_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventBus:
    """Barramento local síncrono, pequeno e observável."""

    def __init__(self, history_limit: int = 256):
        self._subscribers: dict[str, list[Callable[[MindEvent], None]]] = {}
        self._history = deque(maxlen=max(32, int(history_limit)))
        self._lock = RLock()

    def subscribe(self, event_type: str, callback: Callable[[MindEvent], None]):
        with self._lock:
            self._subscribers.setdefault(str(event_type), []).append(callback)
        return callback

    def unsubscribe(self, event_type: str, callback):
        with self._lock:
            callbacks = self._subscribers.get(str(event_type), [])
            if callback in callbacks:
                callbacks.remove(callback)

    def publish(self, event_type: str, payload=None, source: str = "mind") -> MindEvent:
        event = MindEvent(
            event_type=str(event_type),
            payload=dict(payload or {}),
            source=str(source),
        )
        with self._lock:
            self._history.append(event)
            callbacks = list(self._subscribers.get(event.event_type, []))
            callbacks += list(self._subscribers.get("*", []))

        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                continue
        return event

    def recent(self, limit: int = 20) -> list[MindEvent]:
        limit = max(0, int(limit))
        with self._lock:
            if not limit:
                return []
            return list(self._history)[-limit:]

    def count(self) -> int:
        with self._lock:
            return len(self._history)

    def snapshot(self, limit: int = 10) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self.recent(limit)]
