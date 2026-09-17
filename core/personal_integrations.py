"""Integrações pessoais opcionais da STAR.

E-mail, mensagens e calendário são providers externos opt-in. Credenciais vivem
somente em variáveis de ambiente. Saídas externas são drafts persistentes no
star.db e exigem confirmação local de duas etapas antes do envio/sincronização.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.message import EmailMessage
import email
import imaplib
import json
import os
import re
import secrets
import smtplib
import ssl
from urllib.parse import urljoin, urlparse

import requests
from sqlalchemy import text

from database.database import engine


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS star_personal_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        provider TEXT NOT NULL,
        recipient TEXT,
        subject TEXT,
        content TEXT NOT NULL,
        payload_json TEXT NOT NULL DEFAULT '{}',
        status TEXT NOT NULL DEFAULT 'draft',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        sent_at TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_star_personal_drafts_status ON star_personal_drafts(status, created_at)",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value) -> str:
    return " ".join(str(value or "").split())


def _decode_header(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except (LookupError, UnicodeError):
        return str(value)


class EmailAdapter:
    def __init__(self):
        self.smtp_host = os.getenv("STAR_EMAIL_SMTP_HOST", "").strip()
        self.smtp_port = int(os.getenv("STAR_EMAIL_SMTP_PORT", "465") or 465)
        self.smtp_security = os.getenv("STAR_EMAIL_SMTP_SECURITY", "ssl").strip().lower()
        self.imap_host = os.getenv("STAR_EMAIL_IMAP_HOST", "").strip()
        self.imap_port = int(os.getenv("STAR_EMAIL_IMAP_PORT", "993") or 993)
        self.user = os.getenv("STAR_EMAIL_USER", "").strip()
        self.password = os.getenv("STAR_EMAIL_PASSWORD", "")
        self.sender = os.getenv("STAR_EMAIL_FROM", "").strip() or self.user

    @property
    def read_configured(self) -> bool:
        return bool(self.imap_host and self.user and self.password)

    @property
    def send_configured(self) -> bool:
        return bool(self.smtp_host and self.user and self.password and self.sender)

    def recent(self, limit: int = 10) -> list[dict]:
        if not self.read_configured:
            raise RuntimeError("IMAP não configurado")
        client = imaplib.IMAP4_SSL(self.imap_host, self.imap_port, timeout=10)
        try:
            client.login(self.user, self.password)
            status, _ = client.select("INBOX", readonly=True)
            if status != "OK":
                return []
            status, data = client.search(None, "ALL")
            if status != "OK" or not data:
                return []
            ids = data[0].split()[-max(1, min(int(limit), 25)):]
            rows = []
            for message_id in reversed(ids):
                status, payload = client.fetch(message_id, "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID)])")
                if status != "OK" or not payload:
                    continue
                raw = next((part[1] for part in payload if isinstance(part, tuple) and len(part) > 1), b"")
                msg = email.message_from_bytes(raw)
                rows.append({
                    "id": message_id.decode("ascii", errors="ignore"),
                    "from": _decode_header(msg.get("From")),
                    "to": _decode_header(msg.get("To")),
                    "subject": _decode_header(msg.get("Subject")),
                    "date": _clean(msg.get("Date")),
                    "message_id": _clean(msg.get("Message-ID")),
                    "body_loaded": False,
                })
            return rows
        finally:
            try:
                client.logout()
            except imaplib.IMAP4.error:
                pass

    def send(self, to: str, subject: str, body: str) -> None:
        if not self.send_configured:
            raise RuntimeError("SMTP não configurado")
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        context = ssl.create_default_context()
        if self.smtp_security == "starttls":
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=12) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(self.user, self.password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=12, context=context) as smtp:
                smtp.login(self.user, self.password)
                smtp.send_message(message)


class TelegramAdapter:
    def __init__(self, *, session=None):
        self.token = os.getenv("STAR_TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("STAR_TELEGRAM_CHAT_ID", "").strip()
        self.session = session or requests.Session()

    @property
    def configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, content: str) -> None:
        if not self.configured:
            raise RuntimeError("Telegram não configurado")
        response = self.session.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={"chat_id": self.chat_id, "text": content},
            timeout=12,
        )
        response.raise_for_status()


class CalDAVAdapter:
    """Adapter mínimo para uma URL de coleção CalDAV já resolvida pelo usuário."""

    def __init__(self, *, session=None):
        self.collection_url = os.getenv("STAR_CALDAV_URL", "").rstrip("/")
        self.user = os.getenv("STAR_CALDAV_USER", "").strip()
        self.password = os.getenv("STAR_CALDAV_PASSWORD", "")
        self.session = session or requests.Session()

    @property
    def configured(self) -> bool:
        try:
            parsed = urlparse(self.collection_url)
        except ValueError:
            return False
        return bool(
            self.collection_url and self.user and self.password
            and parsed.scheme in {"http", "https"} and parsed.hostname
            and not parsed.username and not parsed.password
        )

    @staticmethod
    def _ical_escape(value: str) -> str:
        return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")

    def put_event(self, *, uid: str, summary: str, start: datetime, end: datetime | None = None) -> dict:
        if not self.configured:
            raise RuntimeError("CalDAV não configurado")
        if start.tzinfo is None:
            start = start.astimezone()
        start_utc = start.astimezone(timezone.utc)
        end_utc = (end or (start + timedelta(minutes=30))).astimezone(timezone.utc)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ics = "\r\n".join([
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//STAR//Personal Integrations//PT-BR",
            "BEGIN:VEVENT",
            f"UID:{self._ical_escape(uid)}",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{self._ical_escape(summary)}",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ])
        url = urljoin(self.collection_url + "/", uid + ".ics")
        response = self.session.put(
            url,
            data=ics.encode("utf-8"),
            headers={"Content-Type": "text/calendar; charset=utf-8"},
            auth=(self.user, self.password),
            timeout=12,
        )
        response.raise_for_status()
        return {"ok": True, "status_code": response.status_code, "url": url}


@dataclass
class PendingPersonalAction:
    draft_id: int
    code: str
    expires_at: datetime


class PersonalIntegrations:
    EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    def __init__(
        self,
        *,
        agenda,
        autonomy_limits,
        network_enabled_provider=lambda: False,
        email_adapter=None,
        message_adapter=None,
        calendar_adapter=None,
    ):
        self.agenda = agenda
        self.autonomy_limits = autonomy_limits
        self.network_enabled_provider = network_enabled_provider
        self.email = email_adapter or EmailAdapter()
        self.messages = message_adapter or TelegramAdapter()
        self.calendar = calendar_adapter or CalDAVAdapter()
        self._pending: dict[int, PendingPersonalAction] = {}
        with engine.begin() as conn:
            for ddl in _SCHEMA:
                conn.execute(text(ddl))

    def _create_draft(self, kind: str, provider: str, content: str, *, recipient=None, subject=None, payload=None) -> dict:
        content = str(content or "").strip()
        if not content or len(content) > 20_000:
            raise ValueError("conteúdo do rascunho vazio ou acima do limite")
        now = _now()
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO star_personal_drafts(kind,provider,recipient,subject,content,payload_json,status,created_at,updated_at)
                VALUES (:kind,:provider,:recipient,:subject,:content,:payload,'draft',:now,:now)
            """), {
                "kind": kind, "provider": provider, "recipient": recipient, "subject": subject,
                "content": content, "payload": json.dumps(payload or {}, ensure_ascii=False, sort_keys=True), "now": now,
            })
            draft_id = int(result.lastrowid)
        code = secrets.token_hex(3).upper()
        self._pending[draft_id] = PendingPersonalAction(draft_id, code, datetime.now(timezone.utc) + timedelta(minutes=5))
        draft = self.get_draft(draft_id)
        draft["confirmation_code"] = code
        draft["confirmation_expires_seconds"] = 300
        return draft

    def email_draft(self, to: str, subject: str, body: str) -> dict:
        to = str(to or "").strip()
        if not self.EMAIL_RE.fullmatch(to):
            raise ValueError("endereço de e-mail inválido")
        return self._create_draft("email", "smtp", body, recipient=to, subject=_clean(subject)[:300])

    def message_draft(self, content: str) -> dict:
        return self._create_draft("message", "telegram", content, recipient="configured-default-chat")

    def calendar_sync_draft(self, agenda_id: int) -> dict:
        item = self.agenda.get(int(agenda_id))
        if item is None:
            raise KeyError(agenda_id)
        return self._create_draft(
            "calendar_sync",
            "caldav",
            item["title"],
            payload={"agenda_id": int(agenda_id), "due_at": item["due_at"]},
        )

    def get_draft(self, draft_id: int) -> dict | None:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM star_personal_drafts WHERE id=:id"), {"id": int(draft_id)}).mappings().first()
        if row is None:
            return None
        item = dict(row)
        try:
            item["payload"] = json.loads(item.pop("payload_json"))
        except json.JSONDecodeError:
            item["payload"] = {}
        return item

    def drafts(self, *, status: str = "draft", limit: int = 20) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT id,kind,provider,recipient,subject,status,created_at
                FROM star_personal_drafts WHERE status=:status ORDER BY id DESC LIMIT :limit
            """), {"status": status, "limit": max(1, min(int(limit), 100))}).mappings().all()
        return [dict(x) for x in rows]

    def recent_email(self, limit: int = 8) -> list[dict]:
        if not self.network_enabled_provider():
            raise RuntimeError("network_disabled")
        return self.email.recent(limit=limit)

    def _boundary(self, intent: str) -> dict:
        return self.autonomy_limits.evaluate(
            intent,
            permission=True,
            capability=True,
            safety_ok=True,
            mutation_requested=True,
            mutation_permission=True,
            authorization_source="local-two-step-personal-integration",
        )

    def confirm(self, draft_id: int, code: str, *, remote: bool = False) -> dict:
        draft_id = int(draft_id)
        pending = self._pending.get(draft_id)
        draft = self.get_draft(draft_id)
        if draft is None or draft.get("status") != "draft":
            return {"ok": False, "reason": "draft_not_found"}
        if pending is None or secrets.compare_digest(pending.code, str(code or "").strip().upper()) is False:
            return {"ok": False, "reason": "invalid_confirmation"}
        self._pending.pop(draft_id, None)
        if remote:
            return {"ok": False, "reason": "local_confirmation_required"}
        if datetime.now(timezone.utc) > pending.expires_at:
            return {"ok": False, "reason": "confirmation_expired"}
        if not self.network_enabled_provider():
            return {"ok": False, "reason": "network_disabled"}
        decision = self._boundary("personal_" + draft["kind"])
        if not decision.get("can_act"):
            return {"ok": False, "reason": "boundary_blocked", "missing": decision.get("missing")}
        try:
            if draft["kind"] == "email":
                self.email.send(draft["recipient"], draft.get("subject") or "", draft["content"])
            elif draft["kind"] == "message":
                self.messages.send(draft["content"])
            elif draft["kind"] == "calendar_sync":
                payload = draft.get("payload") or {}
                due = datetime.fromisoformat(payload["due_at"])
                self.calendar.put_event(
                    uid=f"star-agenda-{payload['agenda_id']}@local",
                    summary=draft["content"],
                    start=due,
                )
            else:
                return {"ok": False, "reason": "unsupported_kind"}
        except (RuntimeError, OSError, smtplib.SMTPException, imaplib.IMAP4.error, requests.RequestException) as exc:
            return {"ok": False, "reason": type(exc).__name__}
        now = _now()
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE star_personal_drafts SET status='sent',sent_at=:now,updated_at=:now WHERE id=:id
            """), {"now": now, "id": draft_id})
        return {"ok": True, "draft_id": draft_id, "kind": draft["kind"], "provider": draft["provider"]}

    def stats(self) -> dict:
        return {
            "status": "available-when-providers-configured",
            "email_read": self.email.read_configured,
            "email_send": self.email.send_configured,
            "messaging": self.messages.configured,
            "calendar_sync": self.calendar.configured,
            "agenda_source": "existing AgendaManager/star.db",
            "drafts_pending": len(self.drafts()),
            "credentials_persisted": False,
            "two_step_confirmation": True,
            "automatic_sending": False,
            "permission_authority": "B01/B33",
        }

    def handle_context(self, text_value: str, *, network_enabled: bool = False, remote: bool = False) -> str | None:
        raw = _clean(text_value)
        low = raw.casefold()
        if low in {"status integrações pessoais", "status integracoes pessoais", "status pessoal"}:
            s = self.stats()
            return (
                "📨 Integrações pessoais: "
                f"IMAP={'SIM' if s['email_read'] else 'NÃO'} | SMTP={'SIM' if s['email_send'] else 'NÃO'} | "
                f"mensagens={'SIM' if s['messaging'] else 'NÃO'} | CalDAV={'SIM' if s['calendar_sync'] else 'NÃO'} | "
                "envio automático=NÃO."
            )
        if low in {"emails recentes", "e-mails recentes", "meus emails recentes", "meus e-mails recentes"}:
            if remote:
                return "Leitura de e-mail pessoal exige solicitação local nesta versão."
            try:
                rows = self.recent_email(8)
            except (RuntimeError, OSError, imaplib.IMAP4.error):
                return "Não consegui ler e-mails agora; verifique modo ONLINE e configuração IMAP."
            if not rows:
                return "📨 Nenhum cabeçalho recente encontrado."
            return "📨 E-mails recentes:\n" + "\n".join(
                f"- {x['from']} — {x['subject'] or '(sem assunto)'} — {x['date']}" for x in rows
            )
        m = re.match(r"^rascunho e-?mail para\s+([^\s:]+)\s*:\s*([^|]+)\|\s*(.+)$", raw, re.I)
        if m:
            if remote:
                return "Criar rascunho de envio pessoal exige interação local."
            try:
                draft = self.email_draft(m.group(1), m.group(2), m.group(3))
            except ValueError as exc:
                return f"Não criei o rascunho: {exc}"
            return (
                f"📨 Rascunho #{draft['id']} criado. Para enviar, confirme localmente com "
                f"'confirmar integração #{draft['id']} {draft['confirmation_code']}' em até 5 minutos."
            )
        m = re.match(r"^rascunho mensagem\s*:\s*(.+)$", raw, re.I)
        if m:
            if remote:
                return "Criar rascunho de mensagem exige interação local."
            draft = self.message_draft(m.group(1))
            return (
                f"💬 Rascunho #{draft['id']} criado. Confirme com "
                f"'confirmar integração #{draft['id']} {draft['confirmation_code']}'."
            )
        m = re.match(r"^(?:sincronize|sincronizar) calend[aá]rio lembrete\s+#?(\d+)$", raw, re.I)
        if m:
            if remote:
                return "Sincronização de calendário exige interação local."
            try:
                draft = self.calendar_sync_draft(int(m.group(1)))
            except KeyError:
                return "Não encontrei esse item na agenda local."
            return (
                f"📅 Sincronização preparada como rascunho #{draft['id']}. Confirme com "
                f"'confirmar integração #{draft['id']} {draft['confirmation_code']}'."
            )
        m = re.match(r"^confirmar integra[cç][aã]o\s+#?(\d+)\s+([A-F0-9]{6})$", raw, re.I)
        if m:
            result = self.confirm(int(m.group(1)), m.group(2), remote=remote)
            if result.get("ok"):
                return f"✅ Integração #{result['draft_id']} concluída via {result['provider']}."
            return f"A integração não foi executada ({result.get('reason')})."
        return None
