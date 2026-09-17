"""Agenda persistente + scheduler proativo da STAR.

Este módulo usa o mesmo ``star.db``. O scheduler só produz eventos cognitivos e
notificações; ele nunca executa ferramentas, comandos de SO ou movimentos.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import json
import re
import threading
import time
from typing import Callable

from sqlalchemy import text

from database.database import engine


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS star_agenda_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        due_at TEXT NOT NULL,
        recurrence TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_fired_at TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_star_agenda_due ON star_agenda_items(status, due_at)",
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.astimezone()
    return value.astimezone(timezone.utc).isoformat()


def _load(value: str | None) -> dict:
    try:
        raw = json.loads(value or "{}")
        return raw if isinstance(raw, dict) else {}
    except json.JSONDecodeError:
        return {}


class AgendaManager:
    """Fonte única de lembretes/agenda no SQLite oficial da STAR."""

    MAX_TITLE = 500

    def __init__(self):
        with engine.begin() as conn:
            for ddl in _SCHEMA:
                conn.execute(text(ddl))

    @staticmethod
    def _row(row) -> dict:
        return {**dict(row), "metadata": _load(row["metadata_json"])}

    def add(self, title: str, due_at: datetime, *, recurrence: str | None = None, metadata=None) -> dict:
        title = " ".join(str(title or "").split())[:self.MAX_TITLE]
        if not title:
            raise ValueError("lembrete sem conteúdo")
        recurrence = str(recurrence or "").strip().lower() or None
        if recurrence not in {None, "daily", "weekly"}:
            raise ValueError("recorrência suportada: daily/weekly")
        now = _iso(_utcnow())
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO star_agenda_items(title,due_at,recurrence,status,metadata_json,created_at,updated_at)
                VALUES (:title,:due,:recurrence,'active',:meta,:now,:now)
            """), {"title": title, "due": _iso(due_at), "recurrence": recurrence,
                    "meta": json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True), "now": now})
            item_id = int(result.lastrowid)
        return self.get(item_id)

    def get(self, item_id: int) -> dict | None:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM star_agenda_items WHERE id=:id"), {"id": int(item_id)}).mappings().first()
        return None if row is None else self._row(row)

    def list(self, *, status: str | None = "active", limit: int = 100) -> list[dict]:
        params = {"limit": max(1, min(int(limit), 500))}
        where = ""
        if status:
            where = "WHERE status=:status"
            params["status"] = str(status)
        with engine.connect() as conn:
            rows = conn.execute(text(f"SELECT * FROM star_agenda_items {where} ORDER BY due_at ASC, id ASC LIMIT :limit"), params).mappings().all()
        return [self._row(row) for row in rows]

    def cancel(self, item_id: int) -> bool:
        with engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE star_agenda_items SET status='cancelled', updated_at=:now
                WHERE id=:id AND status='active'
            """), {"id": int(item_id), "now": _iso(_utcnow())})
        return bool(result.rowcount)

    def due(self, *, now: datetime | None = None, limit: int = 32) -> list[dict]:
        now_iso = _iso(now or _utcnow())
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT * FROM star_agenda_items
                WHERE status='active' AND due_at<=:now
                ORDER BY due_at ASC, id ASC LIMIT :limit
            """), {"now": now_iso, "limit": max(1, min(int(limit), 64))}).mappings().all()
        return [self._row(row) for row in rows]

    def mark_fired(self, item_id: int, *, fired_at: datetime | None = None) -> dict | None:
        item = self.get(item_id)
        if item is None or item["status"] != "active":
            return item
        fired = fired_at or _utcnow()
        recurrence = item.get("recurrence")
        if recurrence in {"daily", "weekly"}:
            due = datetime.fromisoformat(item["due_at"])
            step = timedelta(days=1 if recurrence == "daily" else 7)
            while due <= fired:
                due += step
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE star_agenda_items SET due_at=:due,last_fired_at=:fired,updated_at=:fired WHERE id=:id
                """), {"due": _iso(due), "fired": _iso(fired), "id": int(item_id)})
        else:
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE star_agenda_items SET status='completed',last_fired_at=:fired,updated_at=:fired WHERE id=:id
                """), {"fired": _iso(fired), "id": int(item_id)})
        return self.get(item_id)

    @staticmethod
    def _local_due(day_offset: int, hour: int, minute: int, now: datetime) -> datetime:
        local = now.astimezone()
        due = local.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=day_offset)
        if day_offset == 0 and due <= local:
            due += timedelta(days=1)
        return due

    def parse_and_add(self, utterance: str, *, now: datetime | None = None) -> dict | None:
        raw = " ".join(str(utterance or "").strip().split())
        low = raw.casefold()
        now = now or _utcnow()
        patterns = (
            (r"^(?:star[, ]+)?(?:me )?lembre(?:-me)? em (\d+) (minuto|minutos|hora|horas|dia|dias) de (.+)$", "relative"),
            (r"^(?:star[, ]+)?(?:me )?lembre(?:-me)? (hoje|amanh[ãa]) (?:à|a|às|as) (\d{1,2})(?::(\d{2}))? de (.+)$", "clock"),
            (r"^(?:star[, ]+)?(?:me )?lembre(?:-me)? (hoje|amanh[ãa]) de (.+) (?:à|a|às|as) (\d{1,2})(?::(\d{2}))?$", "clock_tail"),
        )
        for pattern, mode in patterns:
            match = re.match(pattern, low, flags=re.I)
            if not match:
                continue
            if mode == "relative":
                amount = int(match.group(1)); unit = match.group(2); title = raw[-len(match.group(3)):]
                if amount <= 0 or amount > 3650:
                    raise ValueError("intervalo de lembrete fora do limite")
                if unit.startswith("minuto"):
                    due = now + timedelta(minutes=amount)
                elif unit.startswith("hora"):
                    due = now + timedelta(hours=amount)
                else:
                    due = now + timedelta(days=amount)
            elif mode == "clock":
                day, hour, minute, content = match.groups()
                due = self._local_due(1 if day.startswith("amanh") else 0, int(hour), int(minute or 0), now)
                title = raw[-len(content):]
            else:
                day, content, hour, minute = match.groups()
                due = self._local_due(1 if day.startswith("amanh") else 0, int(hour), int(minute or 0), now)
                # Mantém a grafia original removendo o sufixo horário.
                title = re.sub(r"\s+(?:à|a|às|as)\s+\d{1,2}(?::\d{2})?$", "", raw, flags=re.I)
                title = re.sub(r"^(?:star[, ]+)?(?:me )?lembre(?:-me)?\s+(?:hoje|amanh[ãa])\s+de\s+", "", title, flags=re.I)
            return self.add(title, due, metadata={"source": "conversation", "parsed_from": raw})
        return None

    def handle(self, text_value: str) -> str | None:
        raw = " ".join(str(text_value or "").strip().split())
        low = raw.casefold()
        if re.search(r"\b(?:lembre|lembre-me)\b", low):
            item = self.parse_and_add(raw)
            if item is None:
                return None
            due = datetime.fromisoformat(item["due_at"]).astimezone()
            return f"⭐ Lembrete #{item['id']} salvo para {due.strftime('%d/%m/%Y %H:%M')}: {item['title']}"
        if low in {"agenda", "minha agenda", "meus lembretes", "listar lembretes", "quais meus lembretes"}:
            items = self.list(status="active", limit=20)
            if not items:
                return "⭐ Sua agenda não tem lembretes ativos."
            lines = []
            for item in items:
                due = datetime.fromisoformat(item["due_at"]).astimezone().strftime("%d/%m %H:%M")
                lines.append(f"#{item['id']} — {due} — {item['title']}")
            return "⭐ Agenda ativa:\n" + "\n".join(lines)
        match = re.match(r"^(?:cancelar|cancele|remover|apagar) lembrete #?(\d+)$", low)
        if match:
            ok = self.cancel(int(match.group(1)))
            return "⭐ Lembrete cancelado." if ok else "⭐ Não encontrei esse lembrete ativo."
        return None

    def stats(self) -> dict:
        active = len(self.list(status="active", limit=500))
        return {"active": active, "database": "star.db", "indexed_due_time": True, "executes_actions": False}


@dataclass(frozen=True)
class ProactiveEvent:
    event_id: str
    kind: str
    content: str
    created_at: str
    importance: float
    notify: bool
    payload: dict


class ProactiveScheduler:
    """Thread temporal bounded que apenas emite eventos, nunca ações."""

    def __init__(self, agenda: AgendaManager, *, poll_seconds: float = 1.0, max_queue: int = 128):
        self.agenda = agenda
        self.poll_seconds = max(0.5, min(float(poll_seconds), 60.0))
        self._queue = deque(maxlen=max(16, min(int(max_queue), 512)))
        self._callbacks: list[Callable[[dict], None]] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._counter = 0

    def subscribe(self, callback: Callable[[dict], None]) -> None:
        if callable(callback) and callback not in self._callbacks:
            self._callbacks.append(callback)

    def emit(self, kind: str, content: str, *, payload=None, importance: float = 0.5, notify: bool = True) -> dict:
        self._counter += 1
        event = ProactiveEvent(
            event_id=f"PROACTIVE-{int(time.time() * 1000)}-{self._counter:04d}",
            kind=str(kind or "event")[:80], content=" ".join(str(content or "").split())[:1000],
            created_at=_iso(_utcnow()), importance=max(0.0, min(float(importance), 1.0)),
            notify=bool(notify), payload=dict(payload or {}),
        )
        data = asdict(event)
        with self._lock:
            self._queue.append(data)
        for callback in tuple(self._callbacks):
            try:
                callback(dict(data))
            except Exception:
                # Callback de UI/integrador não pode derrubar o scheduler.
                continue
        return data

    def drain(self, *, limit: int = 16, notify_only: bool = True) -> list[dict]:
        result = []
        with self._lock:
            remaining = deque(maxlen=self._queue.maxlen)
            while self._queue:
                item = self._queue.popleft()
                if len(result) < max(1, min(int(limit), 64)) and (not notify_only or item.get("notify")):
                    result.append(item)
                else:
                    remaining.append(item)
            self._queue.extend(remaining)
        return result

    def tick(self, *, now: datetime | None = None) -> list[dict]:
        fired = []
        moment = now or _utcnow()
        for item in self.agenda.due(now=moment, limit=32):
            fired.append(self.emit(
                "reminder_due", f"Lembrete: {item['title']}",
                payload={"agenda_id": item["id"], "due_at": item["due_at"]}, importance=0.8, notify=True,
            ))
            self.agenda.mark_fired(item["id"], fired_at=moment)
        return fired

    def _run(self) -> None:
        while not self._stop.wait(self.poll_seconds):
            try:
                self.tick()
            except Exception:
                # A agenda persiste; um tick ruim é retomado no próximo ciclo.
                continue

    def start(self):
        if self._thread and self._thread.is_alive():
            return self
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="star-proactive-scheduler", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=max(1.0, self.poll_seconds + 0.5))

    def stats(self) -> dict:
        return {
            "running": bool(self._thread and self._thread.is_alive()),
            "queue_size": len(self._queue), "poll_seconds": self.poll_seconds,
            "executes_actions": False, "agenda": self.agenda.stats(),
        }
