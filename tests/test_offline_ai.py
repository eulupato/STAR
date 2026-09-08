import pytest

from core.ai_engine import AIEngine


def test_external_ai_is_disabled_by_default():
    ai = AIEngine()

    assert ai.enabled is False
    with pytest.raises(RuntimeError, match="desativado"):
        ai.is_available()
