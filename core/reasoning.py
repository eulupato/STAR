from core.mind import ReasoningEngine

__all__ = ["ReasoningEngine", "analyze"]


def analyze(problem: str) -> dict:
    return ReasoningEngine().analyze(problem)
