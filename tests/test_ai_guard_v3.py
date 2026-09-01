from core.ai_engine import AIEngine


def test_external_ai_adapter_is_disabled_by_default():
    ai = AIEngine()
    assert ai.enabled is False

    try:
        ai.is_available()
    except RuntimeError as exc:
        assert "desativado" in str(exc).lower()
    else:
        raise AssertionError("AIEngine não deve acessar rede quando desativado.")
