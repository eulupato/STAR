"""Planner operacional da STAR MIND V2.

O plano contém somente etapas executáveis e metadados de roteamento. Ele não
armazena nem expõe raciocínio privado passo a passo.
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
    """Preserva a ordem segura da V1.9 dentro de uma estrutura extensível."""

    def build(self, text: str, salience, context: dict) -> OperationalPlan:
        steps = (
            PlanStep(
                "context_recall",
                "context",
                "Resolver continuidade imediata antes de ferramentas.",
            ),
            PlanStep(
                "computer_control",
                "computer_control",
                "Verificar se a entrada é uma ação local ou online autorizada.",
            ),
            PlanStep(
                "math",
                "math",
                "Resolver matemática determinística sem modelo externo.",
            ),
            PlanStep(
                "legacy_reasoning",
                "legacy_reasoning",
                "Usar conhecimento interno, Router e Executive estáveis.",
            ),
        )
        return OperationalPlan(priority=salience.priority, steps=steps)
