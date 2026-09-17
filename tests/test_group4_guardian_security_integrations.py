from pathlib import Path

from core.cure import CureSystem
from core.guardian_services import (
    ContainerSandbox,
    HomeAutomation,
    PersonalIntegrations,
    SecurityAgent,
)
from core.labs import CodeLab


class FakeSandbox:
    available = True

    def run_python(self, code, timeout=5.0):
        return {
            "ok": "FAIL" not in code,
            "available": True,
            "stdout": "ok" if "FAIL" not in code else "",
            "stderr": "" if "FAIL" not in code else "failed",
            "returncode": 0 if "FAIL" not in code else 1,
        }

    def stats(self):
        return {"available": True, "runtime": "fake", "host_fallback": False}


class FakeLimits:
    def evaluate(self, intent, **kwargs):
        missing = []
        if not kwargs.get("permission"):
            missing.append("permission")
        if not kwargs.get("capability"):
            missing.append("capability")
        if not kwargs.get("safety_ok"):
            missing.append("safety")
        if kwargs.get("authentication_required") and not kwargs.get("authenticated"):
            missing.append("authentication")
        if kwargs.get("mutation_requested") and not kwargs.get("mutation_permission"):
            missing.append("mutation_permission")
        return {"can_act": not missing, "missing": missing, "intent": intent}


class FakeHomeAdapter:
    configured = True

    def __init__(self):
        self.calls = []

    def states(self):
        return [{"entity_id": "light.sala", "state": "off", "attributes": {"friendly_name": "Sala"}}]

    def state(self, entity_id):
        return {"entity_id": entity_id, "state": "off"}

    def service(self, domain, service, entity_id):
        self.calls.append((domain, service, entity_id))
        return {"ok": True, "result": []}


class FakeAgenda:
    pass


def test_container_sandbox_fails_closed_without_runtime(monkeypatch):
    monkeypatch.setenv("STAR_SANDBOX_RUNTIME", "__star_missing_runtime__")
    sandbox = ContainerSandbox()
    result = sandbox.run_python("print('x')")
    assert result["ok"] is False
    assert result["available"] is False
    assert result["reason"] == "container_runtime_missing"
    assert sandbox.stats()["host_fallback"] is False


def test_codelab_secure_runner_uses_explicit_sandbox():
    sandbox = FakeSandbox()
    lab = CodeLab(sandbox=sandbox)
    result = lab.run_sandboxed("print(2 + 2)")
    assert result["ok"] is True
    assert result["available"] is True
    assert lab.stats()["os_grade_sandbox"] is True


def test_cura_classifies_root_cause_and_never_auto_applies():
    cure = CureSystem(sandbox=FakeSandbox())
    report = cure.diagnose(
        "A chamada falhou",
        logs="TypeError: function() got an unexpected keyword argument 'namespace'",
    )
    assert report.failure_class == "type"
    assert report.root_cause
    assert report.confidence > 0.5
    cure.validate_python_candidate(report, "print('candidate')")
    assert report.validated is True
    result = cure.apply(report)
    assert result.applied is False
    assert any("automática" in note or "automatica" in note for note in result.notes)


def test_security_agent_bounded_scan_detects_secret_without_remediation(tmp_path):
    (tmp_path / "safe.py").write_text("print('ok')", encoding="utf-8")
    secret_line = "api_" + "key = '" + "1234567890SECRET" + "'"
    (tmp_path / "bad.py").write_text(secret_line, encoding="utf-8")
    agent = SecurityAgent(tmp_path, sandbox=FakeSandbox())
    report = agent.scan_repository(max_files=20)
    assert report["bounded"] is True
    assert report["scanned_files"] == 2
    assert any(item["path"] == "bad.py" for item in report["findings"])
    assert agent.stats()["automatic_remediation"] is False


def test_home_automation_requires_confirmation_and_auth_for_sensitive_domains():
    adapter = FakeHomeAdapter()
    home = HomeAutomation(FakeLimits(), adapter=adapter)

    blocked = home.execute("light.sala", "on", network_enabled=True, local_confirmed=False)
    assert blocked["ok"] is False
    assert adapter.calls == []

    allowed = home.execute("light.sala", "on", network_enabled=True, local_confirmed=True)
    assert allowed["ok"] is True
    assert adapter.calls[-1] == ("light", "turn_on", "light.sala")

    sensitive = home.execute("lock.porta", "on", network_enabled=True, local_confirmed=True, authenticated=False)
    assert sensitive["ok"] is False
    assert "authentication" in sensitive["decision"]["missing"]


def test_personal_integrations_are_opt_in_and_do_not_persist_credentials(monkeypatch):
    keys = [
        "STAR_EMAIL_IMAP_HOST", "STAR_EMAIL_SMTP_HOST", "STAR_EMAIL_USERNAME",
        "STAR_EMAIL_PASSWORD", "STAR_CALDAV_URL", "STAR_CALDAV_USERNAME",
        "STAR_CALDAV_PASSWORD", "STAR_MESSAGE_WEBHOOK_URL",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    integrations = PersonalIntegrations(FakeLimits(), FakeAgenda())
    status = integrations.stats()
    assert status["email_imap"] is False
    assert status["email_smtp"] is False
    assert status["calendar_local"] is True
    assert status["credentials_persisted_by_star"] is False
    result = integrations.send_message("oi", network_enabled=True, local_confirmed=True)
    assert result["ok"] is False


def test_home_status_reports_provider_without_claiming_configuration():
    home = HomeAutomation(FakeLimits(), adapter=FakeHomeAdapter())
    text = home.contextual_handle("status casa", network_enabled=True, remote=False)
    assert "Home Assistant" in text
    assert "ações automáticas=NÃO" in text
