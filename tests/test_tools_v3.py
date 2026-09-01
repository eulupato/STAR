from core.math_engine import calculate
from core.tools import ToolRegistry


def test_tool_registry_uses_single_math_engine():
    registry = ToolRegistry()
    registry.register("math", calculate, True, "math")

    assert registry.call("math", "2+2") == 4
    assert registry.call("math", "sqrt(81)") == 9


def test_disabled_tool_is_not_callable():
    registry = ToolRegistry()
    registry.register("disabled", lambda: True, False)

    assert "disabled" not in registry.available()
    try:
        registry.call("disabled")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Ferramenta desativada não deve executar.")
