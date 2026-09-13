"""STAR Guardian alpha: permissões, auditoria e idempotência de ações.

O Guardian segue default-deny para ações desconhecidas/sensíveis, registra decisões
no SQLite oficial da STAR e impede repetição acidental de efeitos colaterais por uma
chave idempotente. Não é ainda um sandbox de SO nem um cofre criptográfico completo.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from sqlalchemy import text

from database.database import engine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ActionPolicy:
    action: str
    risk: str = "medium"
    remote_allowed: bool = False
    network_required: bool = False
    confirmation_required: bool = True
    description: str = ""


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    action: str
    reason: str
    risk: str
    requires_confirmation: bool
    audit_id: int | None = None


DEFAULT_POLICIES = {
    "read.status": ActionPolicy("read.status", "low", True, False, False, "Leitura de estado"),
    "read.files": ActionPolicy("read.files", "low", False, False, False, "Busca/indexação local somente leitura"),
    "research.network": ActionPolicy("research.network", "medium", True, True, False, "Pesquisa externa declarada"),
    "camera.local": ActionPolicy("camera.local", "medium", False, False, True, "Acesso local à câmera"),
    "screen.local": ActionPolicy("screen.local", "medium", False, False, True, "Captura local de tela"),
    "app.open": ActionPolicy("app.open", "medium", False, False, True, "Abrir aplicativo"),
    "app.close": ActionPolicy("app.close", "high", False, False, True, "Fechar aplicativo"),
    "system.lock": ActionPolicy("system.lock", "high", False, False, True, "Bloquear computador"),
    "file.write": ActionPolicy("file.write", "high", False, False, True, "Alterar arquivo"),
    "code.execute": ActionPolicy("code.execute", "high", False, False, True, "Executar código"),
    "repository.modify": ActionPolicy("repository.modify", "critical", False, True, True, "Modificar repositório"),
}


class Guardian:
    def __init__(self):
        self.policies = dict(DEFAULT_POLICIES)
        self._ensure_schema()

    def _ensure_schema(self):
        with engine.begin() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS guardian_permissions (
                action TEXT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 1,
                remote_allowed INTEGER NOT NULL DEFAULT 0,
                confirmation_required INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            )"""))
            conn.execute(text("""CREATE TABLE IF NOT EXISTS guardian_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                origin TEXT NOT NULL,
                subject TEXT,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )"""))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_guardian_audit_time ON guardian_audit_log(timestamp)"))
            conn.execute(text("""CREATE TABLE IF NOT EXISTS guardian_action_claims (
                claim_key TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                result_json TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""))

    def register_policy(self, policy: ActionPolicy):
        self.policies[policy.action] = policy

    def configure(self, action: str, *, enabled: bool = True, remote_allowed: bool | None = None, confirmation_required: bool | None = None):
        policy = self.policies.get(action, ActionPolicy(action))
        remote = policy.remote_allowed if remote_allowed is None else bool(remote_allowed)
        confirm = policy.confirmation_required if confirmation_required is None else bool(confirmation_required)
        with engine.begin() as conn:
            conn.execute(text("""INSERT INTO guardian_permissions(action,enabled,remote_allowed,confirmation_required,updated_at)
            VALUES(:a,:e,:r,:c,:u) ON CONFLICT(action) DO UPDATE SET
            enabled=excluded.enabled,remote_allowed=excluded.remote_allowed,
            confirmation_required=excluded.confirmation_required,updated_at=excluded.updated_at"""),
            {"a": action, "e": int(bool(enabled)), "r": int(remote), "c": int(confirm), "u": _now()})

    def _override(self, action: str) -> dict | None:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM guardian_permissions WHERE action=:a"), {"a": action}).mappings().first()
        return None if row is None else dict(row)

    def _audit(self, action: str, origin: str, subject: str | None, decision: str, reason: str, metadata=None) -> int:
        with engine.begin() as conn:
            result = conn.execute(text("""INSERT INTO guardian_audit_log(timestamp,action,origin,subject,decision,reason,metadata_json)
            VALUES(:t,:a,:o,:s,:d,:r,:m)"""), {"t": _now(), "a": action, "o": origin, "s": subject,
            "d": decision, "r": reason, "m": json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)})
            return int(result.lastrowid)

    def authorize(self, action: str, *, origin: str = "local", remote: bool = False,
                  network_enabled: bool = False, confirmed: bool = False,
                  subject: str | None = None, metadata=None) -> AuthorizationDecision:
        policy = self.policies.get(action)
        if policy is None:
            audit_id = self._audit(action, origin, subject, "deny", "unknown_action_default_deny", metadata)
            return AuthorizationDecision(False, action, "unknown_action_default_deny", "critical", True, audit_id)
        override = self._override(action)
        enabled = True if override is None else bool(override["enabled"])
        remote_allowed = policy.remote_allowed if override is None else bool(override["remote_allowed"])
        confirmation_required = policy.confirmation_required if override is None else bool(override["confirmation_required"])
        if not enabled:
            reason = "disabled_by_policy"
        elif remote and not remote_allowed:
            reason = "remote_not_allowed"
        elif policy.network_required and not network_enabled:
            reason = "network_disabled"
        elif confirmation_required and not confirmed:
            reason = "confirmation_required"
        else:
            reason = "allowed"
        allowed = reason == "allowed"
        audit_id = self._audit(action, origin, subject, "allow" if allowed else "deny", reason, metadata)
        return AuthorizationDecision(allowed, action, reason, policy.risk, confirmation_required, audit_id)

    @staticmethod
    def claim_key(action: str, payload) -> str:
        raw = json.dumps({"action": action, "payload": payload}, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def claim_once(self, action: str, payload, *, claim_key: str | None = None) -> dict:
        key = claim_key or self.claim_key(action, payload)
        now = _now()
        with engine.begin() as conn:
            existing = conn.execute(text("SELECT * FROM guardian_action_claims WHERE claim_key=:k"), {"k": key}).mappings().first()
            if existing:
                result = json.loads(existing["result_json"]) if existing["result_json"] else None
                return {"claimed": False, "claim_key": key, "status": existing["status"], "result": result}
            conn.execute(text("INSERT INTO guardian_action_claims(claim_key,action,status,created_at,updated_at) VALUES(:k,:a,'claimed',:n,:n)"), {"k": key, "a": action, "n": now})
        return {"claimed": True, "claim_key": key, "status": "claimed", "result": None}

    def complete_claim(self, claim_key: str, result, *, status: str = "completed"):
        with engine.begin() as conn:
            conn.execute(text("UPDATE guardian_action_claims SET result_json=:r,status=:s,updated_at=:u WHERE claim_key=:k"),
                         {"r": json.dumps(result, ensure_ascii=False, sort_keys=True, default=str), "s": status, "u": _now(), "k": claim_key})

    def audit(self, *, limit: int = 100) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM guardian_audit_log ORDER BY id DESC LIMIT :n"), {"n": max(1, min(int(limit), 1000))}).mappings().all()
        return [dict(row) for row in rows]

    @staticmethod
    def redact(text_value: str) -> str:
        text_value = str(text_value)
        patterns = [
            r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*([^\s,;]+)",
            r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
            r"\bsk-[A-Za-z0-9_-]{16,}\b",
        ]
        for pattern in patterns:
            text_value = re.sub(pattern, lambda m: (m.group(1) + "=<redacted>") if m.lastindex and m.lastindex >= 2 else "<redacted>", text_value)
        return text_value

    def stats(self) -> dict:
        return {"status": "alpha", "policies": len(self.policies), "default_deny_unknown": True,
                "audit_log": True, "idempotent_claims": True, "os_grade_sandbox": False,
                "encrypted_secrets_vault": False}
