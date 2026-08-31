"""Memória de trabalho volátil da STAR MIND V2."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import RLock


@dataclass(frozen=True)
class MemoryTurn:
    role: str
    content: str
    created_at: str


class WorkingMemory:
    """Memória curta da sessão, separada do banco persistente."""

    def __init__(self, max_turns: int = 24):
        self._turns = deque(maxlen=max(8, int(max_turns)))
        self._facts: dict[str, str] = {}
        self._active_task: str | None = None
        self._lock = RLock()

    def add_turn(self, role: str, content: str) -> MemoryTurn:
        turn = MemoryTurn(
            role=str(role),
            content=str(content),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._turns.append(turn)
        return turn

    def recent(self, role: str | None = None, limit: int = 6) -> list[MemoryTurn]:
        with self._lock:
            turns = list(self._turns)
        if role is not None:
            turns = [turn for turn in turns if turn.role == role]
        return turns[-max(0, int(limit)):]

    def set_fact(self, key: str, value: str):
        with self._lock:
            self._facts[str(key)] = str(value)

    def get_fact(self, key: str, default=None):
        with self._lock:
            return self._facts.get(str(key), default)

    def facts(self) -> dict[str, str]:
        with self._lock:
            return dict(self._facts)

    def set_active_task(self, task: str | None):
        with self._lock:
            self._active_task = None if task is None else str(task)

    @property
    def active_task(self):
        with self._lock:
            return self._active_task

    def clear(self):
        with self._lock:
            self._turns.clear()
            self._facts.clear()
            self._active_task = None

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "turns": [asdict(turn) for turn in list(self._turns)[-8:]],
                "facts": dict(self._facts),
                "active_task": self._active_task,
                "turn_count": len(self._turns),
            }
