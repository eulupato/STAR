"""Verifica que a IA externa está protegida/desativada."""

from core.ai_engine import AIEngine


def run_test():
    ai = AIEngine()
    assert ai.enabled is False
    try:
        ai.is_available()
    except RuntimeError:
        print("✅ IA externa bloqueada no modo offline.")
        return
    raise AssertionError("AIEngine deveria estar bloqueado.")


if __name__ == "__main__":
    run_test()
