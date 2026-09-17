"""Security Agent da STAR.

Agente read-only por padrão: audita configuração, integridade, segredos comuns,
dependências e superfícies operacionais. Não cria um segundo Permission Manager
e não corrige nada silenciosamente; B01/B33 continuam sendo a autoridade.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from sqlalchemy import text

from database.database import engine


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS star_security_audit (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        scope TEXT NOT NULL,
        score REAL NOT NULL,
        findings_json TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_star_security_audit_time ON star_security_audit(created_at)",
)


@dataclass(frozen=True)
class SecurityFinding:
    severity: str
    code: str
    message: str
    evidence: str | None = None


class SecurityAgent:
    MAX_FILES = 4000
    MAX_FILE_BYTES = 2_000_000
    SCANNABLE_SUFFIXES = {
        ".py", ".json", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".md",
        ".txt", ".ps1", ".bat", ".sh", ".js", ".ts", ".swift", ".kt", ".kts",
    }
    SKIP_DIRS = {
        ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
        "runtime", "build", "dist",
    }
    SECRET_PATTERNS = (
        ("private_key", "critical", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
        ("github_token", "high", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
        ("aws_access_key", "high", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("bearer_literal", "medium", re.compile(r"(?i)authorization\s*[:=]\s*[\"']?bearer\s+[A-Za-z0-9._~+/-]{20,}")),
    )

    def __init__(self, *, star=None, root: str | Path | None = None, sandbox=None):
        self.star = star
        self.root = Path(root or Path(__file__).resolve().parents[1]).resolve()
        self.sandbox = sandbox
        with engine.begin() as conn:
            for ddl in _SCHEMA:
                conn.execute(text(ddl))

    def _iter_files(self):
        count = 0
        for path in self.root.rglob("*"):
            if count >= self.MAX_FILES:
                break
            try:
                if not path.is_file() or path.suffix.lower() not in self.SCANNABLE_SUFFIXES:
                    continue
                if any(part in self.SKIP_DIRS for part in path.relative_to(self.root).parts):
                    continue
                if path.stat().st_size > self.MAX_FILE_BYTES:
                    continue
                count += 1
                yield path
            except (OSError, ValueError):
                continue

    def scan_secrets(self) -> list[SecurityFinding]:
        findings = []
        for path in self._iter_files():
            try:
                value = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            relative = str(path.relative_to(self.root))
            for code, severity, pattern in self.SECRET_PATTERNS:
                if pattern.search(value):
                    findings.append(SecurityFinding(
                        severity, code, "possível segredo versionado detectado", relative
                    ))
                    if len(findings) >= 100:
                        return findings
        return findings

    def dependency_audit(self) -> list[SecurityFinding]:
        executable = shutil.which("pip-audit")
        if not executable:
            return [SecurityFinding("info", "pip_audit_unavailable", "pip-audit não está instalado; auditoria CVE opcional não foi executada.")]
        try:
            proc = subprocess.run(
                [executable, "--local", "--format", "json", "--progress-spinner", "off"],
                text=True, capture_output=True, timeout=60, check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return [SecurityFinding("info", "pip_audit_failed", f"pip-audit indisponível: {type(exc).__name__}")]
        if proc.returncode == 0:
            return []
        try:
            payload = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError:
            return [SecurityFinding("medium", "dependency_audit_nonzero", "pip-audit retornou vulnerabilidades/erro.", (proc.stderr or "")[-500:])]
        findings = []
        dependencies = payload.get("dependencies", []) if isinstance(payload, dict) else payload
        for dep in dependencies or []:
            vulns = dep.get("vulns") or []
            for vuln in vulns[:10]:
                findings.append(SecurityFinding(
                    "high",
                    "dependency_vulnerability",
                    f"{dep.get('name')} {dep.get('version')} — {vuln.get('id')}",
                    str(vuln.get("fix_versions") or "sem correção informada"),
                ))
        return findings[:100]

    def configuration_audit(self) -> list[SecurityFinding]:
        findings = []
        if self.sandbox is None or not self.sandbox.ready():
            findings.append(SecurityFinding(
                "medium", "os_sandbox_unavailable",
                "sandbox de SO/container não está pronto; código não confiável deve permanecer bloqueado."
            ))
        star = self.star
        if star is not None:
            if bool(getattr(star, "network_enabled", False)):
                findings.append(SecurityFinding("info", "network_mode_enabled", "modo de rede está habilitado nesta sessão."))
            gateway = getattr(star, "device_gateway", None)
            if gateway is not None:
                url = str(getattr(gateway, "url", ""))
                if url.startswith("http://"):
                    findings.append(SecurityFinding(
                        "medium", "gateway_plain_http",
                        "Device Gateway está em HTTP; use apenas LAN privada até existir TLS/mTLS.",
                        url,
                    ))
        return findings

    def integrity_snapshot(self, paths: tuple[str, ...] = ("main.py", "config.py", "STAR_MANIFEST.json")) -> dict:
        items = {}
        for relative in paths:
            path = (self.root / relative).resolve()
            try:
                path.relative_to(self.root)
            except ValueError:
                continue
            if path.is_file():
                items[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"algorithm": "sha256", "files": items, "generated_at": datetime.now(timezone.utc).isoformat()}

    @staticmethod
    def _score(findings: list[SecurityFinding]) -> float:
        penalties = {"critical": 0.35, "high": 0.20, "medium": 0.08, "low": 0.03, "info": 0.0}
        return max(0.0, 1.0 - sum(penalties.get(item.severity, 0.05) for item in findings))

    def scan(self, *, include_dependencies: bool = False) -> dict:
        findings = [*self.configuration_audit(), *self.scan_secrets()]
        if include_dependencies:
            findings.extend(self.dependency_audit())
        score = self._score(findings)
        result = {
            "score": score,
            "findings": [asdict(x) for x in findings],
            "integrity": self.integrity_snapshot(),
            "read_only": True,
            "automatic_remediation": False,
            "permission_authority": "B01/B33",
        }
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO star_security_audit(created_at,scope,score,findings_json)
                VALUES (:at,:scope,:score,:findings)
            """), {
                "at": datetime.now(timezone.utc).isoformat(),
                "scope": "dependencies+repo" if include_dependencies else "repo",
                "score": score,
                "findings": json.dumps(result["findings"], ensure_ascii=False, sort_keys=True),
            })
        return result

    def recent(self, limit: int = 10) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT audit_id,created_at,scope,score FROM star_security_audit
                ORDER BY audit_id DESC LIMIT :limit
            """), {"limit": max(1, min(int(limit), 50))}).mappings().all()
        return [dict(x) for x in rows]

    def stats(self) -> dict:
        return {
            "status": "available-read-only",
            "secret_scan": True,
            "dependency_audit_optional": bool(shutil.which("pip-audit")),
            "integrity_snapshot": True,
            "automatic_remediation": False,
            "sandbox_ready": bool(self.sandbox and self.sandbox.ready()),
            "database": "star.db",
        }

    def handle_context(self, text_value: str, *, network_enabled: bool = False, remote: bool = False) -> str | None:
        raw = " ".join(str(text_value or "").split())
        low = raw.casefold()
        if low in {"status segurança", "status seguranca", "status security", "security status"}:
            s = self.stats()
            return (
                "🛡️ Security Agent: auditoria read-only=ATIVA | segredos=ATIVO | "
                f"sandbox={'ATIVO' if s['sandbox_ready'] else 'INDISPONÍVEL/FAIL-CLOSED'} | "
                "correção automática=NÃO | autoridade=B01/B33."
            )
        if low in {"auditoria de segurança", "auditoria de seguranca", "scan de segurança", "scan de seguranca"}:
            result = self.scan(include_dependencies=False)
            serious = [x for x in result["findings"] if x["severity"] in {"critical", "high", "medium"}]
            return f"🛡️ Auditoria concluída: score={result['score']:.2f} | achados relevantes={len(serious)} | remediação automática=NÃO."
        return None
