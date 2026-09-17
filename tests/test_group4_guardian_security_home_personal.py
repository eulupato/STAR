from __future__ import annotations

from pathlib import Path
import subprocess
import uuid

import pytest

from core.agents import AgentManager
from core.cure import CureSystem
from core.home_automation import HomeAutomationService
from core.labs import CodeLab
from core.os_sandbox import OSSandbox
from core.personal_integrations import PersonalIntegrations
from core.security_agent import SecurityAgent


class AllowAutonomy:
    def evaluate(self, *args, **kwargs):
        return {"can_act": True, "missing": []}


class FakeSandbox:
    backend = "fake"

    def ready(self):
        return True

    def run_python(self, code, **kwargs):
        return {
            "ok": True, "stdout": "sandboxed", "stderr": "", "returncode": 0,
            "timed_out": False, "os_grade": True, "network_enabled": kwargs.get("network", False),
        }


class FakeHomeAdapter:
    configured = True

    def __init__(self):
        self.calls = []

    def state(self, entity_id):
        return {"entity_id": entity_id, "state": "off"}

    def call(self, domain, service, entity_id):
        self.calls.append((domain, service, entity_id))
        return {"ok": True}


class FakeAgenda:
    def get(self, item_id):
        if int(item_id) != 7:
            return None
        return {"id": 7, "title": "Reunião STAR", "due_at": "2026-09-18T15:00:00+00:00"}


class FakeEmail:
    read_configured = True
    send_configured = True

    def __init__(self):
        self.sent = []

    def recent(self, limit=8):
        return [{"from": "a@example.com", "subject": "Teste", "date": "hoje"}]

    def send(self, to, subject, body):
        self.sent.append((to, subject, body))


class FakeMessages:
    configured = True

    def __init__(self):
        self.sent = []

    def send(self, content):
        self.sent.append(content)


class FakeCalendar:
    configured = True

    def __init__(self):
        self.sent = []

    def put_event(self, **kwargs):
        self.sent.append(kwargs)
        return {"ok": True}


def test_os_sandbox_fails_closed_without_backend():
    sandbox = OSSandbox(backend="backend-that-does-not-exist")
    result = sandbox.run_python("print('x')")
    assert result["ok"] is False
    assert result["os_grade"] is False
    assert result["reason"] == "os_sandbox_unavailable"


def test_codelab_has_explicit_real_sandbox_path():
    lab = CodeLab(sandbox=FakeSandbox())
    result = lab.run_sandboxed("print(1)")
    assert result["ok"] is True
    assert result["os_grade"] is True


def test_cure_analyzes_logs_and_never_auto_applies():
    cure = CureSystem()
    report = cure.diagnose(
        "falha no teste",
        'Traceback\n  File "core/example.py", line 12, in run\nTypeError: argumento inválido\nFAILED tests/test_x.py::test_y',
    )
    assert report.diagnosis["failed_tests"] == ["tests/test_x.py::test_y"]
    assert report.diagnosis["exceptions"][-1]["type"] == "TypeError"
    cure.validate(report, tests_passed=True)
    result = cure.apply(report)
    assert result.validated is True
    assert result.applied is False


def test_cure_patch_validation_uses_disposable_worktree_and_fails_closed_without_sandbox(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "star@example.local"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "STAR Test"], cwd=repo, check=True)
    target = repo / "a.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo, check=True, capture_output=True)
    patch = """diff --git a/a.py b/a.py
index 7a7f9bb..0b94918 100644
--- a/a.py
+++ b/a.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
"""
    cure = CureSystem(sandbox=OSSandbox(backend="backend-that-does-not-exist"))
    report = cure.diagnose("mudar valor")
    cure.validate_patch(report, patch, repo, test_args=())
    assert target.read_text(encoding="utf-8") == "VALUE = 1\n"
    assert report.applied is False
    assert report.validated is False


def test_security_agent_is_read_only_and_detects_common_secret(tmp_path):
    (tmp_path / "sample.py").write_text('TOKEN = "ghp_' + "A" * 40 + '"\n', encoding="utf-8")
    agent = SecurityAgent(root=tmp_path, sandbox=OSSandbox(backend="backend-that-does-not-exist"))
    result = agent.scan()
    assert result["read_only"] is True
    assert result["automatic_remediation"] is False
    assert any(x["code"] == "github_token" for x in result["findings"])


def test_home_automation_requires_two_step_confirmation_and_allowlist():
    adapter = FakeHomeAdapter()
    service = HomeAutomationService(
        autonomy_limits=AllowAutonomy(),
        network_enabled_provider=lambda: True,
        adapter=adapter,
    )
    alias = "luz-" + uuid.uuid4().hex[:8]
    service.bind(alias, "light.star_test")
    request = service.request_action(alias, "turn_on")
    assert request["confirmation_required"] is True
    result = service.confirm(request["code"], remote=False)
    assert result["ok"] is True
    assert adapter.calls == [("light", "turn_on", "light.star_test")]
    with pytest.raises(ValueError):
        service.bind("porta-" + uuid.uuid4().hex[:8], "lock.front_door")


def test_home_remote_confirmation_is_blocked():
    adapter = FakeHomeAdapter()
    service = HomeAutomationService(
        autonomy_limits=AllowAutonomy(),
        network_enabled_provider=lambda: True,
        adapter=adapter,
    )
    alias = "fan-" + uuid.uuid4().hex[:8]
    service.bind(alias, "fan.star_test")
    request = service.request_action(alias, "turn_off")
    result = service.confirm(request["code"], remote=True)
    assert result["ok"] is False
    assert result["reason"] == "local_confirmation_required"
    assert adapter.calls == []


def test_personal_integrations_use_drafts_and_local_confirmation():
    email_adapter = FakeEmail()
    messages = FakeMessages()
    calendar = FakeCalendar()
    service = PersonalIntegrations(
        agenda=FakeAgenda(),
        autonomy_limits=AllowAutonomy(),
        network_enabled_provider=lambda: True,
        email_adapter=email_adapter,
        message_adapter=messages,
        calendar_adapter=calendar,
    )
    draft = service.email_draft("lu@example.com", "STAR", "teste")
    assert email_adapter.sent == []
    wrong = service.confirm(draft["id"], "000000", remote=False)
    assert wrong["ok"] is False
    result = service.confirm(draft["id"], draft["confirmation_code"], remote=False)
    assert result["ok"] is True
    assert email_adapter.sent == [("lu@example.com", "STAR", "teste")]


def test_personal_calendar_reuses_existing_agenda():
    calendar = FakeCalendar()
    service = PersonalIntegrations(
        agenda=FakeAgenda(),
        autonomy_limits=AllowAutonomy(),
        network_enabled_provider=lambda: True,
        email_adapter=FakeEmail(),
        message_adapter=FakeMessages(),
        calendar_adapter=calendar,
    )
    draft = service.calendar_sync_draft(7)
    result = service.confirm(draft["id"], draft["confirmation_code"], remote=False)
    assert result["ok"] is True
    assert calendar.sent[0]["summary"] == "Reunião STAR"


def test_agent_manager_passes_remote_context_to_sensitive_handlers():
    seen = {}

    class Handler:
        def handle_context(self, text, *, network_enabled=False, remote=False):
            seen.update(network_enabled=network_enabled, remote=remote)
            return "ok"

    manager = AgentManager()
    manager.attach_system_handlers(Handler())
    assert manager.dispatch("qualquer coisa", network_enabled=True, remote=True) == "ok"
    assert seen == {"network_enabled": True, "remote": True}
