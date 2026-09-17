"""CURA — diagnóstico e autocorreção inteligente controlada.

A CURA diagnostica causa provável, reúne evidências, propõe correção mínima e
pode validar candidatos em sandbox. Aplicação automática no repositório continua
bloqueada: corrigir código requer um processo externo explicitamente autorizado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass
class CureReport:
    problem: str
    proposal: str
    validated: bool = False
    applied: bool = False
    tests_passed: bool = False
    notes: list[str] = field(default_factory=list)
    root_cause: str | None = None
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    failure_class: str = "unknown"
    candidate_validation: dict | None = None


class CureSystem:
    """Diagnóstico bounded com validação opcional em container real."""

    PATTERNS = (
        ("import", re.compile(r"(ModuleNotFoundError|ImportError|cannot import|No module named)", re.I)),
        ("type", re.compile(r"(TypeError|unexpected keyword|missing .* argument)", re.I)),
        ("key", re.compile(r"(KeyError|missing key|not found in mapping)", re.I)),
        ("attribute", re.compile(r"(AttributeError|has no attribute)", re.I)),
        ("syntax", re.compile(r"(SyntaxError|IndentationError)", re.I)),
        ("timeout", re.compile(r"(Timeout|timed out|tempo limite)", re.I)),
        ("network", re.compile(r"(ConnectionError|ConnectTimeout|DNS|NameResolution|network)", re.I)),
        ("permission", re.compile(r"(PermissionError|AccessDenied|forbidden|unauthorized)", re.I)),
        ("database", re.compile(r"(sqlite|sqlalchemy|OperationalError|IntegrityError)", re.I)),
        ("assertion", re.compile(r"(AssertionError|assert .* failed|failed,)", re.I)),
    )

    def __init__(self, *, sandbox=None):
        self.sandbox = sandbox

    @classmethod
    def _classify(cls, payload: str) -> str:
        for name, pattern in cls.PATTERNS:
            if pattern.search(payload):
                return name
        return "unknown"

    @staticmethod
    def _root_cause(failure_class: str, payload: str) -> tuple[str, float]:
        rules = {
            "import": ("dependência/import ausente, incompatível ou caminho de módulo incorreto", 0.72),
            "type": ("contrato de chamada incompatível com a assinatura real da função", 0.78),
            "key": ("contrato de dados divergente: chave esperada não existe no estado real", 0.72),
            "attribute": ("API/objeto real diverge do atributo esperado pelo chamador", 0.76),
            "syntax": ("erro sintático ou estrutural impede carregar/executar o código", 0.95),
            "timeout": ("operação excedeu a janela de execução; investigar bloqueio, I/O ou custo", 0.62),
            "network": ("falha de conectividade/provider; não substituir por dado inventado", 0.64),
            "permission": ("operação não possui permissão/autorização suficiente", 0.85),
            "database": ("falha de persistência/esquema/consulta; revisar transação e compatibilidade", 0.72),
            "assertion": ("comportamento real diverge do comportamento esperado pelo teste", 0.66),
            "unknown": ("causa ainda não isolada; reproduzir com logs mínimos antes de alterar código", 0.25),
        }
        cause, confidence = rules[failure_class]
        if "Traceback" in payload:
            confidence = min(0.95, confidence + 0.05)
        return cause, confidence

    def diagnose(self, problem, *, logs: str = "", traceback: str = ""):
        problem = str(problem)
        payload = "\n".join(x for x in (problem, str(logs or ""), str(traceback or "")) if x)
        failure_class = self._classify(payload)
        cause, confidence = self._root_cause(failure_class, payload)
        evidence = []
        for line in payload.splitlines():
            line = line.strip()
            if line and (
                "Error" in line or "Exception" in line or "failed" in line.casefold()
                or "Traceback" in line or "assert" in line.casefold()
            ):
                evidence.append(line[:500])
            if len(evidence) >= 12:
                break
        proposal = (
            "Reproduzir a falha de forma mínima, confirmar o contrato esperado e o estado real, "
            f"corrigir a causa raiz classificada como '{failure_class}', executar testes focados "
            "e depois a suíte completa antes de qualquer aplicação."
        )
        return CureReport(
            problem=problem,
            proposal=proposal,
            root_cause=cause,
            confidence=confidence,
            evidence=evidence,
            failure_class=failure_class,
        )

    def validate(self, report, tests_passed=False):
        report.validated = bool(tests_passed)
        report.tests_passed = bool(tests_passed)
        if not tests_passed:
            report.notes.append("Validação externa ainda não passou; candidato não está aprovado.")
        return report

    def validate_python_candidate(self, report: CureReport, code: str, *, timeout: float = 5.0) -> CureReport:
        if self.sandbox is None:
            report.candidate_validation = {"ok": False, "available": False, "reason": "sandbox_not_configured"}
            report.notes.append("Sandbox não configurado; nenhuma execução local insegura foi usada como fallback.")
            return report
        result = self.sandbox.run_python(code, timeout=timeout)
        report.candidate_validation = result
        report.tests_passed = bool(result.get("ok"))
        report.validated = bool(result.get("ok"))
        if not result.get("available", False):
            report.notes.append("Sandbox real indisponível; validação permaneceu fechada.")
        elif not result.get("ok"):
            report.notes.append("Candidato falhou dentro do sandbox; nenhuma aplicação será permitida.")
        else:
            report.notes.append("Candidato executou no sandbox; ainda requer testes do projeto antes de aplicação.")
        return report

    def apply(self, report):
        if not report.validated:
            raise RuntimeError("Correção não validada; nenhuma alteração foi aplicada.")
        report.applied = False
        report.notes.append(
            "Aplicação automática permanece bloqueada. CURA diagnostica/testa; "
            "alteração do repositório exige autorização e fluxo externo auditável."
        )
        return report

    def stats(self) -> dict:
        sandbox = self.sandbox.stats() if self.sandbox is not None and hasattr(self.sandbox, "stats") else {"available": False}
        return {
            "status": "controlled-intelligent-diagnostics",
            "root_cause_classification": True,
            "evidence_capture": True,
            "candidate_sandbox_validation": True,
            "sandbox_available": bool(sandbox.get("available")),
            "automatic_repository_modification": False,
            "automatic_apply": False,
        }

    def handle(self, text: str) -> str | None:
        raw = " ".join(str(text or "").strip().split())
        low = raw.casefold()
        if low in {"status cura", "status da cura", "cura status"}:
            s = self.stats()
            return (
                "🩹 CURA: diagnóstico de causa-raiz + evidência + validação controlada | "
                f"sandbox real={'SIM' if s['sandbox_available'] else 'INDISPONÍVEL'} | "
                "aplicação automática=NÃO."
            )
        match = re.match(r"^(?:cura[, ]+)?diagnostique\s+(.+)$", raw, re.I)
        if match:
            report = self.diagnose(match.group(1))
            return (
                f"🩹 CURA — classe={report.failure_class} | confiança={report.confidence:.2f} | "
                f"causa provável: {report.root_cause}. Próximo passo: {report.proposal}"
            )
        return None
