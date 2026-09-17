"""Grupo 4 — Guardian, segurança, casa e integrações pessoais da STAR.

Não cria um segundo sistema de permissões. Toda ação externa continua subordinada
ao B01/B33. Credenciais são lidas do ambiente e nunca persistidas pelo módulo.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from email.message import EmailMessage
import hashlib
import imaplib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import smtplib
import subprocess
import tempfile
import time
from urllib.parse import quote

import requests
from sqlalchemy import text

from database.database import engine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value) -> str:
    return " ".join(str(value or "").split())


class ContainerSandbox:
    """Execução de código dentro de container quando Docker/Podman existe.

    Não chama o runtime local como fallback e usa --pull=never para nunca baixar
    imagens escondido. Sem runtime/imagem, a capacidade permanece indisponível.
    """

    def __init__(self, *, image: str | None = None, runtime: str | None = None):
        requested = str(runtime or os.getenv("STAR_SANDBOX_RUNTIME") or "").strip()
        if requested:
            self.runtime = shutil.which(requested)
        else:
            self.runtime = shutil.which("docker") or shutil.which("podman")
        self.image = str(image or os.getenv("STAR_SANDBOX_IMAGE") or "python:3.12-alpine").strip()

    @property
    def available(self) -> bool:
        return bool(self.runtime and self._image_available())

    def _image_available(self) -> bool:
        if not self.runtime:
            return False
        try:
            proc = subprocess.run(
                [self.runtime, "image", "inspect", self.image],
                capture_output=True, text=True, timeout=5, check=False,
            )
            return proc.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    def run_python(
        self,
        code: str,
        *,
        timeout: float = 5.0,
        memory_mb: int = 128,
        cpus: float = 0.5,
        pids_limit: int = 64,
    ) -> dict:
        code = str(code or "")
        if not code.strip():
            raise ValueError("código vazio")
        if len(code) > 200_000:
            raise ValueError("código acima do limite do sandbox")
        if not self.runtime:
            return {"ok": False, "available": False, "reason": "container_runtime_missing", "stdout": "", "stderr": ""}
        if not self._image_available():
            return {
                "ok": False, "available": False, "reason": "sandbox_image_missing",
                "image": self.image, "stdout": "", "stderr": "",
                "note": "A STAR não baixa imagens de container automaticamente.",
            }

        timeout = max(0.5, min(float(timeout), 30.0))
        memory_mb = max(32, min(int(memory_mb), 2048))
        cpus = max(0.1, min(float(cpus), 4.0))
        pids_limit = max(16, min(int(pids_limit), 256))
        with tempfile.TemporaryDirectory(prefix="star_sandbox_") as tmp:
            root = Path(tmp)
            source = root / "main.py"
            source.write_text(code, encoding="utf-8")
            command = [
                self.runtime, "run", "--rm", "--pull=never",
                "--network", "none",
                "--memory", f"{memory_mb}m",
                "--cpus", str(cpus),
                "--pids-limit", str(pids_limit),
                "--read-only",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
                "--user", "65534:65534",
                "-v", f"{root.resolve()}:/workspace:ro",
                "-w", "/workspace",
                self.image,
                "python", "-I", "-S", "main.py",
            ]
            try:
                proc = subprocess.run(
                    command, capture_output=True, text=True,
                    timeout=timeout, check=False,
                )
                return {
                    "ok": proc.returncode == 0,
                    "available": True,
                    "reason": None,
                    "stdout": proc.stdout[-20000:],
                    "stderr": proc.stderr[-20000:],
                    "returncode": proc.returncode,
                    "timed_out": False,
                    "runtime": Path(self.runtime).name,
                    "image": self.image,
                    "network": "disabled",
                    "filesystem": "read-only",
                }
            except subprocess.TimeoutExpired as exc:
                return {
                    "ok": False, "available": True, "reason": "timeout",
                    "stdout": (exc.stdout or "")[-20000:] if isinstance(exc.stdout, str) else "",
                    "stderr": "tempo limite excedido",
                    "returncode": None, "timed_out": True,
                    "runtime": Path(self.runtime).name, "image": self.image,
                }
            except OSError as exc:
                return {"ok": False, "available": False, "reason": type(exc).__name__, "stdout": "", "stderr": str(exc)}

    def stats(self) -> dict:
        return {
            "runtime": Path(self.runtime).name if self.runtime else None,
            "image": self.image,
            "available": self.available,
            "network_default": "none",
            "read_only_root": True,
            "capabilities_dropped": True,
            "no_new_privileges": True,
            "automatic_image_download": False,
            "host_fallback": False,
        }


_SECURITY_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS star_security_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        summary TEXT NOT NULL,
        details_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_star_security_created ON star_security_events(created_at)",
)


class SecurityAgent:
    """Auditor defensivo read-only por padrão."""

    SECRET_PATTERNS = (
        ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
        ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
        ("generic_secret", re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password)\s*[=:]\s*['\"][^'\"]{8,}['\"]")),
    )
    IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "runtime"}
    TEXT_SUFFIXES = {".py", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".md", ".txt", ".ps1", ".bat", ".sh"}

    def __init__(self, root: str | Path, *, sandbox: ContainerSandbox | None = None):
        self.root = Path(root).resolve()
        self.sandbox = sandbox or ContainerSandbox()
        with engine.begin() as conn:
            for ddl in _SECURITY_SCHEMA:
                conn.execute(text(ddl))

    def _record(self, event_type: str, severity: str, summary: str, details=None) -> None:
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO star_security_events(event_type,severity,summary,details_json,created_at) "
                "VALUES (:t,:s,:m,:d,:c)"
            ), {
                "t": event_type, "s": severity, "m": _clean(summary)[:1000],
                "d": json.dumps(details or {}, ensure_ascii=False, sort_keys=True),
                "c": _now(),
            })

    def scan_repository(self, *, max_files: int = 5000, max_bytes: int = 2_000_000) -> dict:
        findings = []
        scanned = 0
        for path in self.root.rglob("*"):
            if scanned >= max(1, min(int(max_files), 20000)):
                break
            try:
                if not path.is_file() or path.suffix.lower() not in self.TEXT_SUFFIXES:
                    continue
                if any(part in self.IGNORE_DIRS for part in path.relative_to(self.root).parts):
                    continue
                if path.stat().st_size > max_bytes:
                    continue
                scanned += 1
                payload = path.read_text(encoding="utf-8", errors="ignore")
                for kind, pattern in self.SECRET_PATTERNS:
                    if pattern.search(payload):
                        findings.append({"kind": kind, "path": str(path.relative_to(self.root)), "severity": "high"})
                        break
            except (OSError, ValueError):
                continue
        status = "clean" if not findings else "attention"
        result = {"status": status, "scanned_files": scanned, "findings": findings[:100], "bounded": True}
        self._record("repository_scan", "info" if not findings else "high", f"scan {status}", result)
        return result

    def dependency_audit(self) -> dict:
        executable = shutil.which("pip-audit")
        requirements = self.root / "requirements.txt"
        if not executable or not requirements.is_file():
            return {"available": False, "reason": "pip-audit_or_requirements_missing", "vulnerabilities": None}
        try:
            proc = subprocess.run(
                [executable, "-r", str(requirements), "--format", "json"],
                cwd=self.root, capture_output=True, text=True, timeout=120, check=False,
            )
            parsed = None
            try:
                parsed = json.loads(proc.stdout or "[]")
            except json.JSONDecodeError:
                parsed = None
            result = {
                "available": True, "ok": proc.returncode == 0,
                "returncode": proc.returncode, "report": parsed,
                "stderr": _clean(proc.stderr)[-1000:],
            }
            self._record("dependency_audit", "info" if proc.returncode == 0 else "high", "auditoria de dependências", result)
            return result
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"available": True, "ok": False, "reason": type(exc).__name__}

    def recent_events(self, limit: int = 20) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT event_type,severity,summary,details_json,created_at "
                "FROM star_security_events ORDER BY id DESC LIMIT :n"
            ), {"n": max(1, min(int(limit), 100))}).mappings().all()
        out = []
        for row in rows:
            item = dict(row)
            try:
                item["details"] = json.loads(item.pop("details_json"))
            except json.JSONDecodeError:
                item["details"] = {}
            out.append(item)
        return out

    def stats(self) -> dict:
        return {
            "status": "available-readonly-defensive",
            "repository_scan": True,
            "dependency_audit_if_installed": True,
            "audit_log": "star.db",
            "automatic_remediation": False,
            "sandbox": self.sandbox.stats(),
        }

    def contextual_handle(self, raw: str, *, network_enabled: bool = False, remote: bool = False) -> str | None:
        low = _clean(raw).casefold()
        if low in {"status segurança", "status da segurança", "status security agent"}:
            s = self.stats()
            return (
                "🛡️ Security Agent ativo em modo defensivo/read-only. "
                f"Sandbox={'disponível' if s['sandbox']['available'] else 'indisponível até Docker/Podman+imagem local'}; "
                "remediação automática=DESATIVADA."
            )
        if low in {"audite segurança", "auditar segurança", "verifique a segurança do projeto"}:
            if remote:
                return "A auditoria do repositório exige solicitação local."
            report = self.scan_repository()
            return f"🛡️ Auditoria concluída: {report['scanned_files']} arquivos; {len(report['findings'])} achados."
        return None


class HomeAssistantAdapter:
    def __init__(self, *, base_url: str | None = None, token: str | None = None, session=None):
        self.base_url = str(base_url or os.getenv("STAR_HOME_ASSISTANT_URL") or "").rstrip("/")
        self.token = str(token or os.getenv("STAR_HOME_ASSISTANT_TOKEN") or "")
        self.session = session or requests.Session()

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.token)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def states(self) -> list[dict]:
        if not self.configured:
            return []
        response = self.session.get(self.base_url + "/api/states", headers=self._headers(), timeout=8)
        response.raise_for_status()
        rows = response.json()
        return rows if isinstance(rows, list) else []

    def state(self, entity_id: str) -> dict | None:
        if not self.configured:
            return None
        response = self.session.get(
            self.base_url + "/api/states/" + quote(entity_id, safe="._"),
            headers=self._headers(), timeout=8,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        value = response.json()
        return value if isinstance(value, dict) else None

    def service(self, domain: str, service: str, entity_id: str) -> dict:
        if not self.configured:
            raise RuntimeError("Home Assistant não configurado")
        response = self.session.post(
            f"{self.base_url}/api/services/{quote(domain)}/{quote(service)}",
            headers=self._headers(), json={"entity_id": entity_id}, timeout=8,
        )
        response.raise_for_status()
        try:
            value = response.json()
        except ValueError:
            value = []
        return {"ok": True, "result": value}


class HomeAutomation:
    """Casa real via Home Assistant; leitura livre, escrita sempre gated."""

    SENSITIVE_DOMAINS = {"lock", "alarm_control_panel", "cover", "camera"}

    def __init__(self, autonomy_limits, *, adapter: HomeAssistantAdapter | None = None):
        self.autonomy_limits = autonomy_limits
        self.adapter = adapter or HomeAssistantAdapter()

    def list_devices(self, *, network_enabled: bool) -> list[dict]:
        if not network_enabled or not self.adapter.configured:
            return []
        rows = self.adapter.states()
        return [{
            "entity_id": x.get("entity_id"),
            "state": x.get("state"),
            "name": (x.get("attributes") or {}).get("friendly_name"),
        } for x in rows[:500]]

    def read_state(self, entity_id: str, *, network_enabled: bool) -> dict | None:
        if not network_enabled or not self.adapter.configured:
            return None
        return self.adapter.state(entity_id)

    def execute(self, entity_id: str, action: str, *, network_enabled: bool, local_confirmed: bool, authenticated: bool = False) -> dict:
        entity_id = str(entity_id or "").strip()
        if "." not in entity_id:
            return {"ok": False, "reason": "invalid_entity"}
        domain = entity_id.split(".", 1)[0]
        service = {"on": "turn_on", "off": "turn_off", "toggle": "toggle"}.get(action)
        if service is None:
            return {"ok": False, "reason": "unsupported_action"}
        sensitive = domain in self.SENSITIVE_DOMAINS
        decision = self.autonomy_limits.evaluate(
            "home_automation",
            permission=bool(local_confirmed),
            capability=bool(network_enabled and self.adapter.configured),
            safety_ok=not sensitive or bool(authenticated),
            authenticated=authenticated,
            authentication_required=sensitive,
            mutation_requested=True,
            mutation_permission=bool(local_confirmed),
            authorization_source="local-confirmed-home-command" if local_confirmed else None,
        )
        if not decision.get("can_act"):
            return {"ok": False, "reason": "blocked", "decision": decision}
        try:
            result = self.adapter.service(domain, service, entity_id)
            return {"ok": True, "entity_id": entity_id, "action": action, "provider": "home-assistant", **result}
        except requests.RequestException as exc:
            return {"ok": False, "reason": type(exc).__name__}

    def stats(self) -> dict:
        return {
            "provider": "home-assistant",
            "configured": self.adapter.configured,
            "read_supported": True,
            "write_supported": True,
            "sensitive_domains_require_authentication": sorted(self.SENSITIVE_DOMAINS),
            "authority": "B01/B33",
            "automatic_actions": False,
        }

    def contextual_handle(self, raw: str, *, network_enabled: bool = False, remote: bool = False) -> str | None:
        value = _clean(raw)
        low = value.casefold()
        if low in {"status casa", "status home", "status automação residencial", "status automacao residencial"}:
            s = self.stats()
            return f"🏠 Home Automation: provider=Home Assistant | configurado={'SIM' if s['configured'] else 'NÃO'} | ações automáticas=NÃO."
        if low in {"listar dispositivos da casa", "liste os dispositivos da casa"}:
            if not network_enabled:
                return "A rede está desativada; não consultei o Home Assistant."
            devices = self.list_devices(network_enabled=True)
            if not devices:
                return "Nenhum dispositivo disponível ou Home Assistant não configurado."
            return "🏠 " + " | ".join(f"{x['entity_id']}={x['state']}" for x in devices[:20])
        match = re.match(r"^(?:estado de|estado do)\s+([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)$", low)
        if match:
            state = self.read_state(match.group(1), network_enabled=network_enabled)
            return "Dispositivo não disponível." if not state else f"🏠 {match.group(1)} = {state.get('state')}"
        match = re.match(r"^confirme\s+(ligar|desligar|alternar)\s+([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)$", low)
        if match:
            if remote:
                return "Ações da casa exigem confirmação local."
            action = {"ligar": "on", "desligar": "off", "alternar": "toggle"}[match.group(1)]
            result = self.execute(match.group(2), action, network_enabled=network_enabled, local_confirmed=True, authenticated=False)
            return "🏠 Ação executada." if result.get("ok") else "🏠 Ação bloqueada/indisponível: " + str(result.get("reason"))
        return None


class PersonalIntegrations:
    """E-mail, calendário e mensagens por protocolos padrão e credenciais externas."""

    def __init__(self, autonomy_limits, agenda):
        self.autonomy_limits = autonomy_limits
        self.agenda = agenda

    @staticmethod
    def _email_config() -> dict:
        return {
            "imap_host": os.getenv("STAR_EMAIL_IMAP_HOST"),
            "imap_port": int(os.getenv("STAR_EMAIL_IMAP_PORT", "993")),
            "smtp_host": os.getenv("STAR_EMAIL_SMTP_HOST"),
            "smtp_port": int(os.getenv("STAR_EMAIL_SMTP_PORT", "465")),
            "username": os.getenv("STAR_EMAIL_USERNAME"),
            "password": os.getenv("STAR_EMAIL_PASSWORD"),
            "from": os.getenv("STAR_EMAIL_FROM") or os.getenv("STAR_EMAIL_USERNAME"),
        }

    def inbox(self, *, limit: int = 10, network_enabled: bool = False) -> list[dict]:
        cfg = self._email_config()
        if not network_enabled or not cfg["imap_host"] or not cfg["username"] or not cfg["password"]:
            return []
        client = imaplib.IMAP4_SSL(cfg["imap_host"], cfg["imap_port"])
        try:
            client.login(cfg["username"], cfg["password"])
            client.select("INBOX", readonly=True)
            status, data = client.search(None, "ALL")
            if status != "OK":
                return []
            ids = data[0].split()[-max(1, min(int(limit), 50)):]
            out = []
            for msg_id in reversed(ids):
                status, payload = client.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
                if status != "OK" or not payload:
                    continue
                raw = b"".join(x[1] for x in payload if isinstance(x, tuple) and isinstance(x[1], bytes)).decode("utf-8", errors="replace")
                headers = {}
                for line in raw.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        headers[k.casefold()] = _clean(v)
                out.append({"from": headers.get("from"), "subject": headers.get("subject"), "date": headers.get("date")})
            return out
        finally:
            try:
                client.logout()
            except Exception:
                pass

    def send_email(self, to: str, subject: str, body: str, *, network_enabled: bool, local_confirmed: bool) -> dict:
        cfg = self._email_config()
        decision = self.autonomy_limits.evaluate(
            "send_email", permission=local_confirmed,
            capability=bool(network_enabled and cfg["smtp_host"] and cfg["username"] and cfg["password"]),
            safety_ok=True, mutation_requested=True, mutation_permission=local_confirmed,
            authorization_source="local-confirmed-personal-integration" if local_confirmed else None,
        )
        if not decision.get("can_act"):
            return {"ok": False, "reason": "blocked", "decision": decision}
        message = EmailMessage()
        message["From"] = cfg["from"]
        message["To"] = str(to).strip()
        message["Subject"] = str(subject)[:300]
        message.set_content(str(body))
        try:
            with smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"], timeout=10) as smtp:
                smtp.login(cfg["username"], cfg["password"])
                smtp.send_message(message)
            return {"ok": True, "provider": "smtp", "to": message["To"]}
        except (OSError, smtplib.SMTPException) as exc:
            return {"ok": False, "reason": type(exc).__name__}

    @staticmethod
    def _caldav_config() -> dict:
        return {
            "url": os.getenv("STAR_CALDAV_URL"),
            "username": os.getenv("STAR_CALDAV_USERNAME"),
            "password": os.getenv("STAR_CALDAV_PASSWORD"),
        }

    def create_caldav_event(self, title: str, start_iso: str, end_iso: str, *, network_enabled: bool, local_confirmed: bool) -> dict:
        cfg = self._caldav_config()
        decision = self.autonomy_limits.evaluate(
            "calendar_create", permission=local_confirmed,
            capability=bool(network_enabled and cfg["url"] and cfg["username"] and cfg["password"]),
            safety_ok=True, mutation_requested=True, mutation_permission=local_confirmed,
            authorization_source="local-confirmed-personal-integration" if local_confirmed else None,
        )
        if not decision.get("can_act"):
            return {"ok": False, "reason": "blocked", "decision": decision}
        try:
            start = datetime.fromisoformat(start_iso)
            end = datetime.fromisoformat(end_iso)
        except ValueError:
            return {"ok": False, "reason": "invalid_datetime"}
        uid = secrets.token_hex(12) + "@star.local"
        def fmt(dt):
            if dt.tzinfo is None:
                dt = dt.astimezone()
            return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ics = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//STAR//Personal Integrations//PT-BR\r\n"
            f"BEGIN:VEVENT\r\nUID:{uid}\r\nDTSTAMP:{fmt(datetime.now(timezone.utc))}\r\n"
            f"DTSTART:{fmt(start)}\r\nDTEND:{fmt(end)}\r\nSUMMARY:{_clean(title)}\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        target = cfg["url"].rstrip("/") + "/" + quote(uid) + ".ics"
        try:
            response = requests.put(
                target, data=ics.encode("utf-8"),
                auth=(cfg["username"], cfg["password"]),
                headers={"Content-Type": "text/calendar; charset=utf-8"},
                timeout=10,
            )
            if response.status_code not in {200, 201, 204}:
                return {"ok": False, "reason": f"http_{response.status_code}"}
            return {"ok": True, "provider": "caldav", "uid": uid}
        except requests.RequestException as exc:
            return {"ok": False, "reason": type(exc).__name__}

    def send_message(self, text_value: str, *, network_enabled: bool, local_confirmed: bool) -> dict:
        url = os.getenv("STAR_MESSAGE_WEBHOOK_URL")
        token = os.getenv("STAR_MESSAGE_WEBHOOK_TOKEN")
        decision = self.autonomy_limits.evaluate(
            "send_message", permission=local_confirmed,
            capability=bool(network_enabled and url),
            safety_ok=True, mutation_requested=True, mutation_permission=local_confirmed,
            authorization_source="local-confirmed-personal-integration" if local_confirmed else None,
        )
        if not decision.get("can_act"):
            return {"ok": False, "reason": "blocked", "decision": decision}
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = requests.post(url, headers=headers, json={"text": str(text_value)}, timeout=10)
            if not (200 <= response.status_code < 300):
                return {"ok": False, "reason": f"http_{response.status_code}"}
            return {"ok": True, "provider": "webhook"}
        except requests.RequestException as exc:
            return {"ok": False, "reason": type(exc).__name__}

    def stats(self) -> dict:
        email = self._email_config()
        caldav = self._caldav_config()
        return {
            "email_imap": bool(email["imap_host"] and email["username"] and email["password"]),
            "email_smtp": bool(email["smtp_host"] and email["username"] and email["password"]),
            "calendar_local": True,
            "calendar_caldav": bool(caldav["url"] and caldav["username"] and caldav["password"]),
            "message_webhook": bool(os.getenv("STAR_MESSAGE_WEBHOOK_URL")),
            "credentials_persisted_by_star": False,
            "writes_require_local_confirmation": True,
            "authority": "B01/B33",
        }

    def contextual_handle(self, raw: str, *, network_enabled: bool = False, remote: bool = False) -> str | None:
        value = _clean(raw)
        low = value.casefold()
        if low in {"status integrações", "status integracoes", "status assistente pessoal"}:
            s = self.stats()
            return (
                "📨 Integrações pessoais: "
                f"IMAP={'SIM' if s['email_imap'] else 'NÃO'} | SMTP={'SIM' if s['email_smtp'] else 'NÃO'} | "
                f"CalDAV={'SIM' if s['calendar_caldav'] else 'NÃO'} | Mensagens={'SIM' if s['message_webhook'] else 'NÃO'} | "
                "agenda local=SIM."
            )
        if low in {"listar emails", "listar e-mails", "meus emails recentes", "meus e-mails recentes"}:
            if remote:
                return "Leitura de e-mail exige solicitação local."
            rows = self.inbox(limit=10, network_enabled=network_enabled)
            if not rows:
                return "Nenhum e-mail disponível ou integração IMAP não configurada."
            return "📨 " + " | ".join(f"{x.get('from')}: {x.get('subject')}" for x in rows)
        match = re.match(r"^confirme enviar mensagem\s+(.+)$", value, re.I)
        if match:
            if remote:
                return "Envio de mensagem exige confirmação local."
            result = self.send_message(match.group(1), network_enabled=network_enabled, local_confirmed=True)
            return "📨 Mensagem enviada." if result.get("ok") else "📨 Envio bloqueado/indisponível: " + str(result.get("reason"))
        return None


class GuardianServices:
    def __init__(self, *, root, autonomy_limits, agenda, sandbox: ContainerSandbox | None = None):
        self.sandbox = sandbox or ContainerSandbox()
        self.security = SecurityAgent(root, sandbox=self.sandbox)
        self.home = HomeAutomation(autonomy_limits)
        self.personal = PersonalIntegrations(autonomy_limits, agenda)

    def stats(self) -> dict:
        return {
            "sandbox": self.sandbox.stats(),
            "security": self.security.stats(),
            "home": self.home.stats(),
            "personal": self.personal.stats(),
        }
