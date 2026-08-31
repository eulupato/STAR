"""Cognitive Loop da STAR V2.0 MIND."""

from __future__ import annotations

import time
from uuid import uuid4

from .capabilities import CapabilityRegistry
from .context import ContextEngine
from .event_bus import EventBus
from .executive import MindExecutive
from .metacognition import CognitiveTrace, Metacognition
from .planner import Planner
from .salience import SalienceEngine
from .working_memory import WorkingMemory


class StarMind:
    """Orquestrador cognitivo local e determinístico da V2.0."""

    DIAGNOSTIC_COMMANDS = {
        "diagnostico da mente",
        "diagnóstico da mente",
        "status da mente",
        "status mind",
        "mind status",
    }

    def __init__(self):
        self.events = EventBus()
        self.working_memory = WorkingMemory()
        self.context = ContextEngine()
        self.salience = SalienceEngine()
        self.capabilities = CapabilityRegistry.defaults()
        self.planner = Planner()
        self.executive = MindExecutive(self.capabilities)
        self.metacognition = Metacognition()
        self._diagnostic_commands_normalized = {
            self.context.normalize(command)
            for command in self.DIAGNOSTIC_COMMANDS
        }

    def _safe_publish(self, event_type, payload=None, source="mind"):
        try:
            return self.events.publish(event_type, payload, source)
        except Exception:
            return None

    def process(self, text: str, handlers: dict, network_enabled: bool = False) -> str:
        started = time.perf_counter()
        request_id = uuid4().hex[:12]
        text = str(text or "").strip()

        if not text:
            return "Pode me dizer o que você precisa? ⭐"

        self._safe_publish(
            "input.received",
            {"request_id": request_id, "length": len(text)},
            "perception",
        )

        try:
            self.working_memory.add_turn("user", text)
            self.context.observe_user(text, self.working_memory)
        except Exception:
            pass

        assessment = self.salience.assess(text)
        context_snapshot = self.context.snapshot(self.working_memory)
        normalized = self.context.normalize(text)

        if normalized in self._diagnostic_commands_normalized:
            selected_step = "mind_diagnostics"
            plan_steps = ("mind_diagnostics",)
            errors = ()
            response = self.diagnostic_text()
        else:
            plan = self.planner.build(text, assessment, context_snapshot)
            self._safe_publish(
                "plan.created",
                {
                    "request_id": request_id,
                    "priority": plan.priority,
                    "steps": [step.name for step in plan.steps],
                },
                "planner",
            )
            result = self.executive.execute(
                plan=plan,
                handlers=handlers,
                text=text,
                context=context_snapshot,
                network_enabled=network_enabled,
            )
            response = result.response
            selected_step = result.selected_step
            plan_steps = tuple(step.name for step in plan.steps)
            errors = tuple(result.errors)

        try:
            self.working_memory.add_turn("star", response)
            self.context.observe_response(selected_step)
        except Exception:
            pass

        self._safe_publish(
            "response.generated",
            {
                "request_id": request_id,
                "executor": selected_step,
                "has_errors": bool(errors),
            },
            "executive",
        )

        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        try:
            self.metacognition.record(
                CognitiveTrace(
                    request_id=request_id,
                    input_excerpt=text[:120],
                    salience=assessment.score,
                    priority=assessment.priority,
                    plan_steps=plan_steps,
                    selected_step=selected_step,
                    elapsed_ms=elapsed_ms,
                    event_count=self.events.count(),
                    errors=errors,
                )
            )
        except Exception:
            pass

        return response

    def status(self, network_enabled: bool = False) -> dict:
        last = self.metacognition.last
        memory_snapshot = self.working_memory.snapshot()
        return {
            "version": "2.0",
            "active": True,
            "architecture": [
                "Event Bus",
                "Working Memory",
                "Context Engine",
                "Salience Engine",
                "Planner",
                "Executive",
                "Capability Registry",
                "Operational Metacognition",
            ],
            "events": self.events.count(),
            "working_memory_turns": memory_snapshot["turn_count"],
            "facts": len(memory_snapshot["facts"]),
            "last_executor": last.selected_step if last else None,
            "capabilities": self.capabilities.list(network_enabled),
        }

    def diagnostic_text(self) -> str:
        status = self.status()
        executor = status["last_executor"] or "nenhum ainda"
        return (
            "🧠 MIND V2 ATIVA. "
            f"Event Bus: {status['events']} eventos; "
            f"memória de trabalho: {status['working_memory_turns']} turnos; "
            f"fatos de sessão: {status['facts']}; "
            f"último executor: {executor}."
        )
