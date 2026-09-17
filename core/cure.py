"""CURA — diagnóstico e autocorreção controlada.

A CURA pode diagnosticar logs, localizar uma causa provável, preparar/validar um
patch em worktree descartável e registrar evidências. Alterar o repositório real
continua exigindo autorização explícita, permissão de mutação e validação prévia.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

from sqlalchemy import text

from database.database import engine


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS star_cure_cases (
        case_id TEXT PRIMARY KEY,
        problem TEXT NOT NULL,
        diagnosis_json TEXT NOT NULL DEFAULT '{}',
        proposal TEXT NOT NULL,
        patch_hash TEXT,
        validation_json TEXT NOT NULL DEFAULT '{}',
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_star_cure_status ON star_cure_cases(status, updated_at)",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value) -> str:
    return " ".join(str(value or "").split())


@dataclass
class CureReport:
    problem: str
    proposal: str
    validated: bool = False
    applied: bool = False
    tests_passed: bool = False
    notes: list[str] = field(default_factory=list)
    case_id: str = field(default_factory=lambda: "CURE-" + uuid.uuid4().hex[:12].upper())
    diagnosis: dict = field(default_factory=dict)
    validation: dict = field(default_factory=dict)
    patch_hash: str | None = None


class CureSystem:
    """Guardian/CURA: diagnostica e valida; não ganha autonomia irrestrita."""

    MAX_LOG_CHARS = 200_000
    MAX_PATCH_BYTES = 1_000_000

    def __init__(self, *, sandbox=None, autonomy_limits=None):
        self.sandbox = sandbox
        self.autonomy_limits = autonomy_limits
        with engine.begin() as conn:
            for ddl in _SCHEMA:
                conn.execute(text(ddl))

    @staticmethod
    def analyze_logs(logs: str | None) -> dict:
        raw = str(logs or "")[-CureSystem.MAX_LOG_CHARS:]
        failed_tests = re.findall(r"(?m)^FAILED\s+([^\s]+)", raw)
        exceptions = re.findall(
            r"(?m)^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Warning)):\s*(.+)$",
            raw,
        )
        frames = re.findall(r'File "([^"]+)", line (\d+)(?:, in ([^\n]+))?', raw)
        signals = []
        low = raw.casefold()
        mapping = (
            ("modulenotfounderror", "dependência/import ausente ou ambiente inconsistente"),
            ("importerror", "falha de import/compatibilidade"),
            ("syntaxerror", "erro sintático"),
            ("typeerror", "contrato/tipo de chamada incompatível"),
            ("attributeerror", "atributo/API divergente"),
            ("keyerror", "chave/contrato de dados ausente"),
            ("filenotfounderror", "caminho/asset/dependência local ausente"),
            ("timeouterror", "operação excedeu limite de tempo"),
            ("assertionerror", "comportamento divergiu da expectativa do teste"),
        )
        for needle, meaning in mapping:
            if needle in low:
                signals.append(meaning)
        likely_files = []
        for path, _, _ in reversed(frames):
            if path not in likely_files:
                likely_files.append(path)
        return {
            "failed_tests": failed_tests[:50],
            "exceptions": [{"type": t, "message": _clean(m)} for t, m in exceptions[-20:]],
            "frames": [{"file": p, "line": int(line), "function": _clean(fn)} for p, line, fn in frames[-30:]],
            "likely_files": likely_files[:20],
            "signals": list(dict.fromkeys(signals)),
            "logs_present": bool(raw.strip()),
        }

    def _persist(self, report: CureReport, status: str) -> None:
        now = _now()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO star_cure_cases(case_id,problem,diagnosis_json,proposal,patch_hash,validation_json,status,created_at,updated_at)
                VALUES (:id,:problem,:diagnosis,:proposal,:patch,:validation,:status,:now,:now)
                ON CONFLICT(case_id) DO UPDATE SET
                    diagnosis_json=excluded.diagnosis_json,
                    proposal=excluded.proposal,
                    patch_hash=excluded.patch_hash,
                    validation_json=excluded.validation_json,
                    status=excluded.status,
                    updated_at=excluded.updated_at
            """), {
                "id": report.case_id,
                "problem": report.problem,
                "diagnosis": json.dumps(report.diagnosis, ensure_ascii=False, sort_keys=True),
                "proposal": report.proposal,
                "patch": report.patch_hash,
                "validation": json.dumps(report.validation, ensure_ascii=False, sort_keys=True),
                "status": status,
                "now": now,
            })

    def diagnose(self, problem, logs: str | None = None):
        problem = _clean(problem)
        diagnosis = self.analyze_logs(logs)
        targets = diagnosis.get("likely_files") or []
        if targets:
            proposal = (
                "Investigar a primeira divergência reproduzível em "
                + ", ".join(targets[:3])
                + "; aplicar a menor correção causal e validar em worktree descartável."
            )
        else:
            proposal = "Reproduzir a falha, isolar a causa raiz, propor a menor correção causal e validá-la antes da aplicação."
        report = CureReport(problem=problem, proposal=proposal, diagnosis=diagnosis)
        self._persist(report, "diagnosed")
        return report

    def validate(self, report, tests_passed=False):
        report.validated = bool(tests_passed)
        report.tests_passed = bool(tests_passed)
        report.validation = {"legacy_validation": True, "tests_passed": bool(tests_passed)}
        self._persist(report, "validated" if report.validated else "validation_failed")
        return report

    @staticmethod
    def _patch_paths(patch_text: str) -> list[str]:
        paths = []
        for match in re.finditer(r"(?m)^\+\+\+\s+b/(.+)$", patch_text):
            path = match.group(1).strip()
            if path != "/dev/null" and path not in paths:
                paths.append(path)
        return paths

    @staticmethod
    def _compile_python_files(worktree: Path, paths: list[str]) -> dict:
        errors = []
        checked = 0
        for relative in paths:
            if not relative.endswith(".py"):
                continue
            target = (worktree / relative).resolve()
            try:
                target.relative_to(worktree.resolve())
            except ValueError:
                errors.append(f"caminho fora do worktree: {relative}")
                continue
            if not target.is_file():
                continue
            checked += 1
            try:
                compile(target.read_text(encoding="utf-8"), str(target), "exec")
            except (SyntaxError, UnicodeError, OSError) as exc:
                errors.append(f"{relative}: {type(exc).__name__}: {exc}")
        return {"checked": checked, "ok": not errors, "errors": errors}

    def _sandbox_tests(self, worktree: Path, test_args: tuple[str, ...], timeout: float) -> dict:
        if self.sandbox is None or not self.sandbox.ready():
            return {"executed": False, "passed": False, "reason": "os_sandbox_unavailable"}
        backend = self.sandbox.backend
        if backend in {"docker", "podman"}:
            argv = ["python", "-m", "pytest", "-q", *test_args]
        else:
            import sys
            argv = [sys.executable, "-m", "pytest", "-q", *test_args]
        try:
            command = self.sandbox.build_command(worktree, argv, network=False, memory_mb=1024, cpus=1.0)
            proc = subprocess.run(
                command,
                cwd=worktree,
                env={"PATH": os.environ.get("PATH", "")},
                text=True,
                capture_output=True,
                timeout=max(5.0, min(float(timeout), 900.0)),
                check=False,
            )
            return {
                "executed": True,
                "passed": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout[-20000:],
                "stderr": proc.stderr[-20000:],
                "backend": backend,
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"executed": True, "passed": False, "reason": type(exc).__name__, "backend": backend}

    def validate_patch(
        self,
        report: CureReport,
        patch_text: str,
        repo_path: str | Path,
        *,
        test_args: tuple[str, ...] = ("tests",),
        timeout: float = 300.0,
    ) -> CureReport:
        patch_bytes = str(patch_text).encode("utf-8")
        if not patch_bytes or len(patch_bytes) > self.MAX_PATCH_BYTES:
            raise ValueError("patch vazio ou acima do limite")
        repo = Path(repo_path).expanduser().resolve()
        if not (repo / ".git").exists():
            raise ValueError("repo_path não aponta para um checkout Git")
        report.patch_hash = hashlib.sha256(patch_bytes).hexdigest()
        patch_paths = self._patch_paths(str(patch_text))
        validation = {
            "patch_hash": report.patch_hash,
            "paths": patch_paths,
            "worktree_only": True,
            "real_repo_modified": False,
            "syntax": None,
            "tests": None,
        }
        with tempfile.TemporaryDirectory(prefix="star_cure_worktree_") as tmp:
            worktree = Path(tmp) / "repo"
            add = subprocess.run(
                ["git", "-C", str(repo), "worktree", "add", "--detach", str(worktree), "HEAD"],
                text=True, capture_output=True, timeout=30, check=False,
            )
            if add.returncode != 0:
                validation["reason"] = "worktree_create_failed"
                validation["stderr"] = add.stderr[-4000:]
            else:
                try:
                    check = subprocess.run(
                        ["git", "-C", str(worktree), "apply", "--check", "-"],
                        input=str(patch_text), text=True, capture_output=True, timeout=15, check=False,
                    )
                    if check.returncode != 0:
                        validation["reason"] = "patch_check_failed"
                        validation["stderr"] = check.stderr[-4000:]
                    else:
                        applied = subprocess.run(
                            ["git", "-C", str(worktree), "apply", "-"],
                            input=str(patch_text), text=True, capture_output=True, timeout=15, check=False,
                        )
                        if applied.returncode != 0:
                            validation["reason"] = "patch_apply_failed"
                            validation["stderr"] = applied.stderr[-4000:]
                        else:
                            validation["syntax"] = self._compile_python_files(worktree, patch_paths)
                            if validation["syntax"]["ok"]:
                                validation["tests"] = self._sandbox_tests(worktree, tuple(test_args), timeout)
                finally:
                    subprocess.run(
                        ["git", "-C", str(repo), "worktree", "remove", "--force", str(worktree)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20, check=False,
                    )
        tests = validation.get("tests") or {}
        report.tests_passed = bool(tests.get("passed"))
        report.validated = bool((validation.get("syntax") or {}).get("ok")) and report.tests_passed
        report.validation = validation
        if report.validated:
            report.notes.append("Patch validado em worktree descartável + sandbox; repositório real não foi alterado.")
        else:
            report.notes.append("Patch não foi autorizado para aplicação: validação completa não passou.")
        self._persist(report, "validated" if report.validated else "validation_failed")
        return report

    def apply(self, report, *, explicit_authorization: bool = False):
        # Mantém compatibilidade e default deny. Aplicação real é uma operação
        # separada porque o report não carrega o conteúdo do patch.
        if not report.validated:
            raise RuntimeError("Correção não validada; nenhuma alteração foi aplicada.")
        report.applied = False
        if explicit_authorization:
            report.notes.append("Autorização declarada sem patch alvo; use apply_patch() com os gates completos.")
        else:
            report.notes.append("Aplicação automática permanece bloqueada sem autorização explícita.")
        self._persist(report, "validated_not_applied")
        return report

    def apply_patch(
        self,
        report: CureReport,
        patch_text: str,
        repo_path: str | Path,
        *,
        explicit_authorization: bool,
        mutation_permission: bool,
        safety_ok: bool,
    ) -> CureReport:
        digest = hashlib.sha256(str(patch_text).encode("utf-8")).hexdigest()
        if not report.validated or not report.tests_passed or report.patch_hash != digest:
            raise RuntimeError("o patch informado não corresponde a uma validação aprovada")
        if not (explicit_authorization and mutation_permission and safety_ok):
            raise PermissionError("aplicação exige autorização explícita + permissão de mutação + segurança")
        if self.autonomy_limits is not None:
            decision = self.autonomy_limits.evaluate(
                "cure_apply_patch",
                permission=True,
                capability=True,
                safety_ok=True,
                mutation_requested=True,
                mutation_permission=True,
                authorization_source="explicit-local-cure-approval",
            )
            if not decision.get("can_act"):
                raise PermissionError("B01/B33 bloqueou a mutação")
        repo = Path(repo_path).expanduser().resolve()
        dirty = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            text=True, capture_output=True, timeout=10, check=False,
        )
        if dirty.returncode != 0 or dirty.stdout.strip():
            raise RuntimeError("repositório não está limpo; CURA não sobrepõe trabalho existente")
        check = subprocess.run(
            ["git", "-C", str(repo), "apply", "--check", "-"],
            input=str(patch_text), text=True, capture_output=True, timeout=15, check=False,
        )
        if check.returncode != 0:
            raise RuntimeError("patch deixou de aplicar limpo: " + _clean(check.stderr)[-500:])
        applied = subprocess.run(
            ["git", "-C", str(repo), "apply", "-"],
            input=str(patch_text), text=True, capture_output=True, timeout=15, check=False,
        )
        if applied.returncode != 0:
            raise RuntimeError("git apply falhou: " + _clean(applied.stderr)[-500:])
        report.applied = True
        report.notes.append("Patch aplicado ao working tree após gates explícitos; commit automático=NÃO.")
        self._persist(report, "applied_worktree_uncommitted")
        return report

    def recent_cases(self, limit: int = 20) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT case_id,problem,proposal,status,patch_hash,updated_at
                FROM star_cure_cases ORDER BY updated_at DESC LIMIT :limit
            """), {"limit": max(1, min(int(limit), 100))}).mappings().all()
        return [dict(row) for row in rows]

    def stats(self) -> dict:
        return {
            "controlled_diagnosis": True,
            "log_root_cause_analysis": True,
            "disposable_worktree_validation": True,
            "os_sandbox_tests": bool(self.sandbox and self.sandbox.ready()),
            "automatic_repo_modification": False,
            "explicit_mutation_gate": True,
            "database": "star.db",
        }

    def handle_context(self, text_value: str, *, network_enabled: bool = False, remote: bool = False) -> str | None:
        raw = _clean(text_value)
        low = raw.casefold()
        if low in {"status cura", "status da cura", "cura status"}:
            s = self.stats()
            return (
                "🩺 CURA controlada: diagnóstico=ATIVO | worktree descartável=ATIVO | "
                f"sandbox de testes={'ATIVO' if s['os_sandbox_tests'] else 'INDISPONÍVEL/FAIL-CLOSED'} | "
                "aplicação automática=NÃO."
            )
        if low.startswith("cura diagnostique ") or low.startswith("cura diagnostica "):
            if remote:
                return "A CURA pode receber diagnóstico remoto somente como leitura; aplicação continua bloqueada."
            problem = raw.split(" ", 2)[-1]
            report = self.diagnose(problem)
            return f"🩺 {report.case_id}: {report.proposal}"
        return None
