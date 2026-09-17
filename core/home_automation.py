"""Home Automation da STAR com Home Assistant opcional.

A automação residencial reutiliza B01/B33 e exige confirmação local de duas
etapas para qualquer mutação. Tokens do Home Assistant ficam apenas no ambiente.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
import re
import secrets
from urllib.parse import urlparse

import requests
from sqlalchemy import text

from database.database import engine


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS star_home_entities (
        alias TEXT PRIMARY KEY,
        entity_id TEXT NOT NULL UNIQUE,
        label TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS star_home_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        action TEXT NOT NULL,
        entity_id TEXT,
        status TEXT NOT NULL,
        details_json TEXT NOT NULL DEFAULT '{}'
    )""",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value) -> str:
    return " ".join(str(value or "").split())


@dataclass
class PendingHomeAction:
    code: str
    alias: str
    entity_id: str
    service: str
    expires_at: datetime


class HomeAssistantAdapter:
    def __init__(self, *, base_url: str | None = None, token: str | None = None, session=None):
        self.base_url = (base_url or os.getenv("STAR_HOME_ASSISTANT_URL") or "").rstrip("/")
        self.token = token or os.getenv("STAR_HOME_ASSISTANT_TOKEN") or ""
        self.session = session or requests.Session()

    @property
    def configured(self) -> bool:
        if not self.base_url or not self.token:
            return False
        parsed = urlparse(self.base_url)
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username and not parsed.password

    def _headers(self) -> dict:
        if not self.configured:
            raise RuntimeError("Home Assistant não configurado")
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def states(self, *, timeout: float = 8.0) -> list[dict]:
        response = self.session.get(self.base_url + "/api/states", headers=self._headers(), timeout=timeout)
        response.raise_for_status()
        rows = response.json()
        return rows if isinstance(rows, list) else []

    def state(self, entity_id: str, *, timeout: float = 8.0) -> dict | None:
        response = self.session.get(self.base_url + "/api/states/" + entity_id, headers=self._headers(), timeout=timeout)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        value = response.json()
        return value if isinstance(value, dict) else None

    def call(self, domain: str, service: str, entity_id: str, *, timeout: float = 8.0) -> dict:
        response = self.session.post(
            f"{self.base_url}/api/services/{domain}/{service}",
            headers=self._headers(),
            json={"entity_id": entity_id},
            timeout=timeout,
        )
        response.raise_for_status()
        try:
            body = response.json()
        except ValueError:
            body = None
        return {"ok": True, "status_code": response.status_code, "response": body}


class HomeAutomationService:
    """Registro local + provider real + confirmação curta para mutações."""

    SAFE_DOMAINS = {"light", "switch", "fan"}
    SAFE_SERVICES = {"turn_on", "turn_off"}
    ENTITY_RE = re.compile(r"^[a-z_]+\.[A-Za-z0-9_]+$")

    def __init__(self, *, autonomy_limits, network_enabled_provider=lambda: False, adapter=None):
        self.autonomy_limits = autonomy_limits
        self.network_enabled_provider = network_enabled_provider
        self.adapter = adapter or HomeAssistantAdapter()
        self._pending: dict[str, PendingHomeAction] = {}
        with engine.begin() as conn:
            for ddl in _SCHEMA:
                conn.execute(text(ddl))

    @staticmethod
    def _alias(value: str) -> str:
        value = _clean(value).casefold()
        if not value or len(value) > 80:
            raise ValueError("alias residencial inválido")
        return value

    def bind(self, alias: str, entity_id: str, *, label: str | None = None, metadata=None) -> dict:
        alias = self._alias(alias)
        entity_id = str(entity_id or "").strip()
        if not self.ENTITY_RE.fullmatch(entity_id):
            raise ValueError("entity_id inválido")
        domain = entity_id.split(".", 1)[0]
        if domain not in self.SAFE_DOMAINS:
            raise ValueError("domínio residencial não permitido nesta versão")
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO star_home_entities(alias,entity_id,label,metadata_json,created_at)
                VALUES (:alias,:entity,:label,:meta,:at)
                ON CONFLICT(alias) DO UPDATE SET entity_id=excluded.entity_id,label=excluded.label,metadata_json=excluded.metadata_json
            """), {
                "alias": alias, "entity": entity_id, "label": label,
                "meta": json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True), "at": _now(),
            })
        return self.get(alias)

    def get(self, alias: str) -> dict | None:
        alias = self._alias(alias)
        with engine.connect() as conn:
            row = conn.execute(text("SELECT alias,entity_id,label,metadata_json,created_at FROM star_home_entities WHERE alias=:a"), {"a": alias}).mappings().first()
        if row is None:
            return None
        item = dict(row)
        try:
            item["metadata"] = json.loads(item.pop("metadata_json"))
        except json.JSONDecodeError:
            item["metadata"] = {}
        return item

    def list(self) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT alias,entity_id,label,created_at FROM star_home_entities ORDER BY alias")).mappings().all()
        return [dict(x) for x in rows]

    def read_state(self, alias: str) -> dict:
        item = self.get(alias)
        if item is None:
            return {"ok": False, "reason": "unknown_alias"}
        if not self.network_enabled_provider():
            return {"ok": False, "reason": "network_disabled"}
        if not self.adapter.configured:
            return {"ok": False, "reason": "home_assistant_not_configured"}
        try:
            state = self.adapter.state(item["entity_id"])
            return {"ok": state is not None, "alias": item["alias"], "entity_id": item["entity_id"], "state": state}
        except requests.RequestException as exc:
            return {"ok": False, "reason": type(exc).__name__}

    def request_action(self, alias: str, service: str) -> dict:
        item = self.get(alias)
        if item is None:
            return {"ok": False, "reason": "unknown_alias"}
        service = str(service or "").strip()
        domain = item["entity_id"].split(".", 1)[0]
        if domain not in self.SAFE_DOMAINS or service not in self.SAFE_SERVICES:
            return {"ok": False, "reason": "action_not_allowlisted"}
        code = secrets.token_hex(3).upper()
        pending = PendingHomeAction(
            code=code,
            alias=item["alias"],
            entity_id=item["entity_id"],
            service=service,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=90),
        )
        self._pending[code] = pending
        return {
            "ok": True,
            "confirmation_required": True,
            "code": code,
            "alias": pending.alias,
            "service": pending.service,
            "expires_seconds": 90,
        }

    def _audit(self, action: str, entity_id: str | None, status: str, details=None) -> None:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO star_home_audit(created_at,action,entity_id,status,details_json)
                VALUES (:at,:action,:entity,:status,:details)
            """), {
                "at": _now(), "action": action, "entity": entity_id, "status": status,
                "details": json.dumps(details or {}, ensure_ascii=False, sort_keys=True),
            })

    def confirm(self, code: str, *, remote: bool = False) -> dict:
        code = str(code or "").strip().upper()
        pending = self._pending.get(code)
        if pending is None:
            return {"ok": False, "reason": "confirmation_not_found"}
        if remote:
            self._audit(pending.service, pending.entity_id, "blocked_remote")
            return {"ok": False, "reason": "local_confirmation_required"}
        if datetime.now(timezone.utc) > pending.expires_at:
            self._pending.pop(code, None)
            self._audit(pending.service, pending.entity_id, "expired")
            return {"ok": False, "reason": "confirmation_expired"}
        if not self.network_enabled_provider():
            return {"ok": False, "reason": "network_disabled"}
        if not self.adapter.configured:
            return {"ok": False, "reason": "home_assistant_not_configured"}
        decision = self.autonomy_limits.evaluate(
            f"home_{pending.service}",
            permission=True,
            capability=True,
            safety_ok=True,
            mutation_requested=True,
            mutation_permission=True,
            authorization_source="local-two-step-home-confirmation",
        )
        if not decision.get("can_act"):
            self._audit(pending.service, pending.entity_id, "blocked_boundary", {"missing": decision.get("missing")})
            return {"ok": False, "reason": "boundary_blocked", "missing": decision.get("missing")}
        domain = pending.entity_id.split(".", 1)[0]
        self._pending.pop(code, None)
        try:
            result = self.adapter.call(domain, pending.service, pending.entity_id)
        except requests.RequestException as exc:
            self._audit(pending.service, pending.entity_id, "provider_error", {"type": type(exc).__name__})
            return {"ok": False, "reason": type(exc).__name__}
        self._audit(pending.service, pending.entity_id, "executed")
        return {"ok": True, "alias": pending.alias, "service": pending.service, "provider": result}

    def stats(self) -> dict:
        return {
            "status": "available-when-provider-configured",
            "provider": "Home Assistant REST",
            "configured": self.adapter.configured,
            "bound_entities": len(self.list()),
            "safe_domains": sorted(self.SAFE_DOMAINS),
            "two_step_confirmation": True,
            "locks_alarms_security_devices": False,
            "credentials_persisted": False,
            "permission_authority": "B01/B33",
        }

    def handle_context(self, text_value: str, *, network_enabled: bool = False, remote: bool = False) -> str | None:
        raw = _clean(text_value)
        low = raw.casefold()
        if low in {"status casa", "status home", "status automação residencial", "status automacao residencial"}:
            s = self.stats()
            return (
                "🏠 Home Automation: provider=Home Assistant | "
                f"configurado={'SIM' if s['configured'] else 'NÃO'} | dispositivos={s['bound_entities']} | "
                "ações físicas exigem confirmação local em duas etapas."
            )
        m = re.match(r"^(?:casa|home)\s+(?:vincule|vincular)\s+(.+?)\s*=\s*([a-z_]+\.[A-Za-z0-9_]+)$", raw, re.I)
        if m:
            if remote:
                return "Vincular dispositivo residencial exige interação local."
            try:
                item = self.bind(m.group(1), m.group(2))
                return f"🏠 '{item['alias']}' vinculado a {item['entity_id']}."
            except ValueError as exc:
                return f"Não vinculei o dispositivo: {exc}"
        m = re.match(r"^(?:casa|home)\s+(?:estado|status de)\s+(.+)$", raw, re.I)
        if m:
            result = self.read_state(m.group(1))
            if not result.get("ok"):
                return f"Não consegui consultar esse dispositivo ({result.get('reason')})."
            state = result["state"] or {}
            return f"🏠 {result['alias']}: estado={state.get('state', 'desconhecido')}."
        m = re.match(r"^(?:casa|home)\s+(ligar|desligar)\s+(.+)$", raw, re.I)
        if m:
            if remote:
                return "Ações residenciais físicas exigem solicitação e confirmação locais."
            requested = self.request_action(m.group(2), "turn_on" if m.group(1).casefold() == "ligar" else "turn_off")
            if not requested.get("ok"):
                return f"Não preparei a ação ({requested.get('reason')})."
            return (
                f"🏠 Ação preparada para '{requested['alias']}'. Confirme localmente com "
                f"'confirmar casa {requested['code']}' em até {requested['expires_seconds']}s."
            )
        m = re.match(r"^confirmar casa\s+([A-F0-9]{6})$", raw, re.I)
        if m:
            result = self.confirm(m.group(1), remote=remote)
            if result.get("ok"):
                return f"🏠 Ação {result['service']} executada em '{result['alias']}'."
            return f"A ação residencial não foi executada ({result.get('reason')})."
        return None
