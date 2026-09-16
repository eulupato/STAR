"""BLOCO 33 — limites de autonomia da STAR.

Formaliza separações entre cognição e execução usando o OperationalBoundary do
BLOCO 1 como única autoridade operacional. Este bloco não cria Permission
Manager paralelo, não autentica pessoas e não executa ferramentas por conta própria.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.block_knowledge_catalog import StructuredBillionCatalog
from core.commands import match_command


DISTINCTIONS = (
    "PENSAR ≠ EXECUTAR",
    "CONCLUIR ≠ ALTERAR",
    "CURIOSIDADE ≠ ACESSO",
    "RECOMENDAR ≠ AGIR",
    "RECONHECER ≠ AUTENTICAR",
    "SIMULAR ≠ EXECUTAR",
)

DOMAINS = {
    "thinking_execution": ("reason", "plan", "imagine", "infer", "compare", "judge", "decide", "intend", "prepare", "execute"),
    "conclusion_change": ("conclude", "recommend_change", "draft_change", "preview_change", "validate_change", "request_change", "authorize_change", "apply_change", "verify_change", "rollback"),
    "curiosity_access": ("notice", "wonder", "ask", "search_local", "request_access", "grant_access", "read_data", "network_access", "device_access", "restricted_access"),
    "recommendation_action": ("suggest", "rank", "explain", "warn", "propose", "request_confirmation", "schedule_candidate", "execute_reversible", "execute_irreversible", "verify_result"),
    "recognition_authentication": ("detect_person", "recognize_candidate", "match_signal", "confidence", "ambiguity", "challenge", "credential", "authenticate", "authorize", "revoke"),
    "simulation_execution": ("model", "simulate", "predict", "counterfactual", "sandbox", "dry_run", "proposal", "approval", "execute", "observe"),
    "permissions": ("none", "read", "write", "network", "device", "account", "personal_data", "sensitive", "irreversible", "revoked"),
    "risk": ("negligible", "low", "moderate", "high", "critical", "privacy", "financial", "physical", "security", "unknown"),
    "action_scope": ("internal", "memory", "knowledge", "file", "application", "web", "device", "body", "account", "external_system"),
    "verification": ("capability", "permission", "authentication", "safety", "scope", "purpose", "expiry", "provenance", "result", "audit"),
}
LENSES = ("intent", "context", "permission", "capability", "safety", "authentication", "risk", "reversibility", "audit", "result")
AXES = (
    ("actor", ("star", "creator", "user", "authenticated_user", "device", "tool", "agent", "service", "unknown", "system")),
    ("permission_state", ("none", "requested", "granted_read", "granted_write", "granted_network", "granted_device", "limited", "expired", "revoked", "unknown")),
    ("risk_level", ("r0", "r1", "r2", "r3", "r4", "r5", "privacy", "security", "physical", "unknown")),
    ("action_state", ("thought", "simulated", "recommended", "queued", "awaiting_auth", "authorized", "executing", "observed", "failed", "rolled_back")),
    ("scope", ("internal", "read_local", "write_local", "network", "personal_data", "device", "body", "account", "external", "unknown")),
    ("decision", ("allow_cognition", "allow_read", "allow_reversible", "require_permission", "require_auth", "require_confirmation", "require_safety", "deny", "defer", "audit")),
)
CATALOG = StructuredBillionCatalog(
    namespace="B33",
    domains=DOMAINS,
    lenses=LENSES,
    axes=AXES,
    truthfulness_note="1B representa combinações de autonomia/permissão endereçáveis; nenhuma combinação concede permissão sozinha.",
)
ADDRESSABLE_CONTENTS = CATALOG.addressable_contents


class AutonomyLimits:
    """Policy layer que delega autorização final ao B01 OperationalBoundary."""

    NAMESPACE = "B33"

    def __init__(self, knowledge, *, operational_boundary):
        self.knowledge = knowledge
        self.boundary = operational_boundary
        self.catalog = CATALOG
        self.knowledge.register_namespace(
            self.NAMESPACE,
            "BLOCO 33 — LIMITES DE AUTONOMIA",
            logical_capacity=ADDRESSABLE_CONTENTS,
            source="core/autonomy_limits.py",
            metadata={
                "materialization": "on-demand",
                "authority": "B01 OperationalBoundary",
                "parallel_permission_system": False,
                "default_deny_execution": True,
                "recognition_is_authentication": False,
                "simulation_executes": False,
            },
        )

    def evaluate(
        self,
        intent: str,
        *,
        permission: bool = False,
        capability: bool = False,
        safety_ok: bool = False,
        authenticated: bool = False,
        authentication_required: bool = False,
        mutation_requested: bool = False,
        mutation_permission: bool = False,
        curiosity: bool = False,
        recommendation: bool = False,
        recognition_confidence: float | None = None,
        simulation: bool = False,
        authorization_source: str | None = None,
    ) -> dict:
        effective_permission = bool(permission)
        missing_extra = []
        if authentication_required and not authenticated:
            effective_permission = False
            missing_extra.append("authentication")
        if mutation_requested and not mutation_permission:
            effective_permission = False
            missing_extra.append("mutation_permission")

        base = self.boundary.evaluate(
            intent,
            permission=effective_permission,
            capability=capability,
            safety_ok=safety_ok,
            curiosity=curiosity,
            inference_available=bool(recommendation or simulation or recognition_confidence is not None),
            cognitive_autonomy=True,
            authorization_source=authorization_source if effective_permission else None,
        )
        missing = list(dict.fromkeys([*base.get("missing", []), *missing_extra]))
        can_execute = bool(base.get("can_act")) and not missing
        return {
            **deepcopy(base),
            "can_act": can_execute,
            "missing": missing,
            "authenticated": bool(authenticated),
            "authentication_required": bool(authentication_required),
            "mutation_requested": bool(mutation_requested),
            "mutation_permission": bool(mutation_permission),
            "recognition_confidence": recognition_confidence,
            "recognition_used_as_authentication": False,
            "curiosity_used_as_permission": False,
            "recommendation_used_as_action": False,
            "simulation_used_as_execution": False,
            "distinctions": DISTINCTIONS,
            "rule": "; ".join(DISTINCTIONS),
        }

    def gate_command(
        self,
        text: str,
        *,
        local_permission: bool,
        network_enabled: bool,
    ) -> dict | None:
        """Maps the existing command registry into the same B01 boundary."""
        match = match_command(text)
        if match is None:
            return None

        risk = str(match.risk or "read")
        if risk == "read":
            return {
                "matched": True,
                "intent": match.intent,
                "risk": risk,
                "can_proceed": True,
                "operational_execution": False,
                "reason": "read-only cognition/query",
            }

        if risk == "network":
            decision = self.evaluate(
                match.intent,
                permission=bool(local_permission and network_enabled),
                capability=bool(network_enabled),
                safety_ok=True,
                authorization_source="local-user+network-mode" if local_permission and network_enabled else None,
            )
        elif risk == "confirm":
            decision = self.evaluate(
                match.intent,
                permission=False,
                capability=True,
                safety_ok=True,
                authentication_required=match.agent == "security",
                authenticated=False,
            )
        else:  # write/local side effect
            decision = self.evaluate(
                match.intent,
                permission=bool(local_permission),
                capability=True,
                safety_ok=bool(local_permission),
                authorization_source="local-interaction" if local_permission else None,
            )

        can_proceed = bool(decision["can_act"])
        return {
            "matched": True,
            "intent": match.intent,
            "agent": match.agent,
            "risk": risk,
            "can_proceed": can_proceed,
            "operational_execution": True,
            "decision": decision,
            "message": None if can_proceed else (
                "A ação foi reconhecida, mas permanece bloqueada pela fronteira de autonomia: "
                + ", ".join(decision.get("missing") or ["autorização insuficiente"])
                + "."
            ),
        }

    def stats(self) -> dict:
        return {
            "status": "experimental-integrated",
            "namespace": self.knowledge.store.get_namespace(self.NAMESPACE),
            "catalog": self.catalog.stats(),
            "distinctions": DISTINCTIONS,
            "authority": "B01 OperationalBoundary",
            "parallel_permission_system": False,
            "default_deny_execution": True,
            "recognition_is_authentication": False,
        }

    def handle(self, text: str) -> str | None:
        raw = " ".join(str(text or "").strip().split())
        low = raw.casefold()
        if low in {"status bloco 33", "status limites de autonomia", "limites de autonomia"}:
            return (
                f"🛡️ BLOCO 33 — LIMITES DE AUTONOMIA: {ADDRESSABLE_CONTENTS} situações endereçáveis | "
                "autoridade=B01 | execução=DEFAULT DENY | " + " | ".join(DISTINCTIONS)
            )
        item = self.catalog.get_variant(raw.upper())
        if item:
            return f"🛡️ {item['id']} — {item['domain']} / {item['branch']} / {item['lens']}"
        return None
