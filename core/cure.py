"""CURA — diagnóstico e autocorreção controlada.

A CURA não modifica código automaticamente. Ela apenas registra diagnóstico,
proposta e validação para que uma alteração seja aplicada por um processo externo
explicitamente autorizado.
"""

from dataclasses import dataclass, field


@dataclass
class CureReport:
    problem: str
    proposal: str
    validated: bool = False
    applied: bool = False
    tests_passed: bool = False
    notes: list[str] = field(default_factory=list)


class CureSystem:
    def diagnose(self, problem):
        return CureReport(
            problem=str(problem),
            proposal="Diagnosticar a causa, propor uma correção mínima e validá-la antes da aplicação.",
        )

    def validate(self, report, tests_passed=False):
        report.validated = bool(tests_passed)
        report.tests_passed = bool(tests_passed)
        return report

    def apply(self, report):
        if not report.validated:
            raise RuntimeError("Correção não validada; nenhuma alteração foi aplicada.")
        report.applied = False
        report.notes.append("Aplicação automática permanece bloqueada nesta versão.")
        return report
