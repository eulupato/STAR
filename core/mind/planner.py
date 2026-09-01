"""Planner operacional da STAR MIND.

O plano contém apenas etapas executáveis e metadados de roteamento.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PlanStep:
    name: str
    capability: str
    purpose: str

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class OperationalPlan:
    priority: str
    steps: tuple[PlanStep, ...]

    def to_dict(self):
        return {
            "priority": self.priority,
            "steps": [step.to_dict() for step in self.steps],
        }


class Planner:
    """Ordena capacidades locais do menor custo para o maior."""

    def build(self, text: str, salience, context: dict) -> OperationalPlan:
        steps = (
            PlanStep(
                "context_recall",
                "context",
                "Resolver continuidade e fatos de sessão.",
            ),
            PlanStep(
                "conversation",
                "conversation",
                "Responder small talk local sem modelo externo.",
            ),
            PlanStep(
                "computer_control",
                "computer_control",
                "Verificar ações locais ou online autorizadas.",
            ),
            PlanStep(
                "math",
                "math",
                "Resolver matemática determinística.",
            ),
            PlanStep(
                "knowledge_search",
                "universal_search",
                "Consultar entidades, grafo e conhecimento local.",
            ),
            PlanStep(
                "legacy_reasoning",
                "legacy_reasoning",
                "Usar Router, Executive e conhecimento interno consolidados.",
            ),
        )
        return OperationalPlan(priority=salience.priority, steps=steps)
