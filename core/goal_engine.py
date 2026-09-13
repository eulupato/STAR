"""Goal Engine durável da STAR.

Implementa objetivos e tarefas persistentes com dependências, checkpoints e execução
idempotente. A autonomia continua controlada: handlers externos precisam ser
registrados explicitamente e ações sensíveis devem passar pelo Guardian.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from sqlalchemy import text

from database.database import engine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dump(value) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def _load(value):
    try:
        return json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}


class GoalEngine:
    VALID_TASK_STATES = {"pending", "running", "blocked", "completed", "failed", "cancelled"}

    def __init__(self, guardian=None):
        self.guardian = guardian
        self._ensure_schema()

    def _ensure_schema(self):
        with engine.begin() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS cognitive_goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                objective TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""))
            conn.execute(text("""CREATE TABLE IF NOT EXISTS cognitive_goal_tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                task_key TEXT NOT NULL,
                title TEXT NOT NULL,
                handler TEXT,
                payload_json TEXT NOT NULL DEFAULT '{}',
                dependencies_json TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'pending',
                result_json TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(goal_id, task_key)
            )"""))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goal_tasks_goal ON cognitive_goal_tasks(goal_id,status)"))
            conn.execute(text("""CREATE TABLE IF NOT EXISTS cognitive_goal_checkpoints (
                checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""))

    def create(self, name: str, objective: str, tasks: list[dict] | None = None, *, metadata=None) -> dict:
        name, objective = str(name).strip(), str(objective).strip()
        if not name or not objective:
            raise ValueError("nome e objetivo são obrigatórios")
        now = _now()
        with engine.begin() as conn:
            result = conn.execute(text("INSERT INTO cognitive_goals(name,objective,metadata_json,created_at,updated_at) VALUES(:n,:o,:m,:t,:t)"),
                                  {"n": name, "o": objective, "m": _dump(metadata), "t": now})
            goal_id = int(result.lastrowid)
            for index, task in enumerate(tasks or [], 1):
                task_key = str(task.get("key") or f"task-{index}")
                dependencies = list(task.get("depends_on") or [])
                conn.execute(text("""INSERT INTO cognitive_goal_tasks(goal_id,task_key,title,handler,payload_json,dependencies_json,created_at,updated_at)
                    VALUES(:g,:k,:t,:h,:p,:d,:n,:n)"""), {"g": goal_id, "k": task_key,
                    "t": str(task.get("title") or task_key), "h": task.get("handler"), "p": _dump(task.get("payload") or {}),
                    "d": json.dumps(dependencies, ensure_ascii=False), "n": now})
        return self.get(goal_id)

    def get(self, goal_id: int) -> dict | None:
        with engine.connect() as conn:
            goal = conn.execute(text("SELECT * FROM cognitive_goals WHERE goal_id=:g"), {"g": int(goal_id)}).mappings().first()
            if goal is None:
                return None
            tasks = conn.execute(text("SELECT * FROM cognitive_goal_tasks WHERE goal_id=:g ORDER BY task_id"), {"g": int(goal_id)}).mappings().all()
        result = dict(goal); result["metadata"] = _load(result.pop("metadata_json", "{}")); result["tasks"] = []
        for task in tasks:
            item = dict(task)
            item["payload"] = _load(item.pop("payload_json", "{}"))
            item["dependencies"] = _load(item.pop("dependencies_json", "[]"))
            item["result"] = _load(item.pop("result_json", None)) if item.get("result_json") else None
            result["tasks"].append(item)
        return result

    def list(self, *, status: str | None = None, limit: int = 100) -> list[dict]:
        params = {"n": max(1, min(int(limit), 500))}; where = ""
        if status:
            where = "WHERE status=:s"; params["s"] = status
        with engine.connect() as conn:
            rows = conn.execute(text(f"SELECT goal_id,name,objective,status,created_at,updated_at FROM cognitive_goals {where} ORDER BY updated_at DESC LIMIT :n"), params).mappings().all()
        return [dict(r) for r in rows]

    def ready_tasks(self, goal_id: int) -> list[dict]:
        goal = self.get(goal_id)
        if goal is None:
            raise KeyError(goal_id)
        states = {t["task_key"]: t["status"] for t in goal["tasks"]}
        ready = []
        for task in goal["tasks"]:
            if task["status"] != "pending":
                continue
            if all(states.get(dep) == "completed" for dep in task["dependencies"]):
                ready.append(task)
        return ready

    def update_task(self, task_id: int, status: str, *, result=None) -> dict:
        if status not in self.VALID_TASK_STATES:
            raise ValueError("estado de tarefa inválido")
        with engine.begin() as conn:
            row = conn.execute(text("SELECT goal_id FROM cognitive_goal_tasks WHERE task_id=:t"), {"t": int(task_id)}).mappings().first()
            if row is None:
                raise KeyError(task_id)
            conn.execute(text("UPDATE cognitive_goal_tasks SET status=:s,result_json=:r,attempts=attempts+1,updated_at=:u WHERE task_id=:t"),
                         {"s": status, "r": None if result is None else _dump(result), "u": _now(), "t": int(task_id)})
            conn.execute(text("UPDATE cognitive_goals SET updated_at=:u WHERE goal_id=:g"), {"u": _now(), "g": row["goal_id"]})
        self._refresh_goal(row["goal_id"])
        return self.get(row["goal_id"])

    def _refresh_goal(self, goal_id: int):
        goal = self.get(goal_id)
        states = [t["status"] for t in goal["tasks"]]
        if states and all(s == "completed" for s in states):
            state = "completed"
        elif any(s == "failed" for s in states):
            state = "needs_attention"
        else:
            state = "active"
        with engine.begin() as conn:
            conn.execute(text("UPDATE cognitive_goals SET status=:s,updated_at=:u WHERE goal_id=:g"), {"s": state, "u": _now(), "g": int(goal_id)})

    def checkpoint(self, goal_id: int, label: str, state=None) -> int:
        snapshot = state if state is not None else self.get(goal_id)
        if snapshot is None:
            raise KeyError(goal_id)
        with engine.begin() as conn:
            result = conn.execute(text("INSERT INTO cognitive_goal_checkpoints(goal_id,label,state_json,created_at) VALUES(:g,:l,:s,:t)"),
                                  {"g": int(goal_id), "l": str(label), "s": _dump(snapshot), "t": _now()})
            return int(result.lastrowid)

    def latest_checkpoint(self, goal_id: int) -> dict | None:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM cognitive_goal_checkpoints WHERE goal_id=:g ORDER BY checkpoint_id DESC LIMIT 1"), {"g": int(goal_id)}).mappings().first()
        if row is None:
            return None
        data = dict(row); data["state"] = _load(data.pop("state_json")); return data

    def run_ready(self, goal_id: int, handlers: dict[str, callable], *, max_tasks: int = 8) -> dict:
        executed = []
        for task in self.ready_tasks(goal_id)[:max(1, min(int(max_tasks), 32))]:
            handler_name = task.get("handler")
            if not handler_name or handler_name not in handlers:
                executed.append({"task": task["task_key"], "status": "blocked", "reason": "handler_unavailable"})
                continue
            payload = task.get("payload") or {}
            claim = None
            if self.guardian is not None:
                claim = self.guardian.claim_once(f"goal:{handler_name}", {"goal": goal_id, "task": task["task_key"], "payload": payload})
                if not claim["claimed"] and claim["status"] == "completed":
                    self.update_task(task["task_id"], "completed", result=claim["result"])
                    executed.append({"task": task["task_key"], "status": "reused"})
                    continue
            try:
                result = handlers[handler_name](**payload)
                self.update_task(task["task_id"], "completed", result=result)
                if claim:
                    self.guardian.complete_claim(claim["claim_key"], result)
                executed.append({"task": task["task_key"], "status": "completed"})
            except Exception as exc:
                self.update_task(task["task_id"], "failed", result={"error": f"{type(exc).__name__}: {exc}"})
                if claim:
                    self.guardian.complete_claim(claim["claim_key"], {"error": str(exc)}, status="failed")
                executed.append({"task": task["task_key"], "status": "failed", "error": str(exc)})
        self.checkpoint(goal_id, "run_ready")
        return {"goal": self.get(goal_id), "executed": executed}

    def stats(self) -> dict:
        with engine.connect() as conn:
            goals = int(conn.execute(text("SELECT COUNT(*) FROM cognitive_goals")).scalar_one())
            pending = int(conn.execute(text("SELECT COUNT(*) FROM cognitive_goal_tasks WHERE status='pending'")).scalar_one())
        return {"status": "alpha", "goals": goals, "pending_tasks": pending, "durable_checkpoints": True, "idempotent_execution": self.guardian is not None}
