import pytest

from core.star_core import StarCore


class FakeRouter:
    def route(self, request):
        return {"response_type": "fallback"}


class FakeExecutive:
    def execute(self, request, route):
        return "fallback"


class FakeState:
    def get_state(self):
        return {}


def _core():
    return StarCore(
        router=FakeRouter(),
        executive=FakeExecutive(),
        state=FakeState(),
    )


def test_expected_math_error_can_fall_through(monkeypatch):
    import core.math_engine

    def fail(_text):
        raise ZeroDivisionError("divisão por zero")

    monkeypatch.setattr(core.math_engine, "solve_text", fail)
    assert _core().process("1 / 0", allow_actions=False) == "fallback"


def test_unexpected_math_engine_error_is_not_silenced(monkeypatch):
    import core.math_engine

    def fail(_text):
        raise RuntimeError("defeito inesperado")

    monkeypatch.setattr(core.math_engine, "solve_text", fail)
    with pytest.raises(RuntimeError, match="defeito inesperado"):
        _core().process("2 + 2", allow_actions=False)
