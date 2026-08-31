"""Executive da STAR MIND V2."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExecutionResult:
    response: str
    selected_step: str
    errors: list[str] = field(default_factory=list)


class MindExecutive:
    def __init__(self, capabilities):
        self.capabilities = capabilities

    def execute(self, plan, handlers, text: str, context: dict, network_enabled=False):
        errors = []

        for step in plan.steps:
            if not self.capabilities.is_available(
                step.capability,
                network_enabled=network_enabled,
            ):
                errors.append(f"{step.name}: capability indisponível")
                continue

            handler = handlers.get(step.name)
            if handler is None:
                errors.append(f"{step.name}: handler ausente")
                continue

            try:
                response = handler(text, context)
            except Exception as exc:
                errors.append(f"{step.name}: {type(exc).__name__}: {exc}")
                continue

            if response is not None and str(response).strip():
                return ExecutionResult(
                    response=str(response),
                    selected_step=step.name,
                    errors=errors,
                )

        return ExecutionResult(
            response=(
                "Não consegui concluir esta solicitação com as capacidades "
                "disponíveis agora."
            ),
            selected_step="none",
            errors=errors,
        )
