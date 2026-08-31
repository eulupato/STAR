"""Salience Engine determinístico da STAR MIND V2."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SalienceAssessment:
    score: float
    priority: str
    signals: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


class SalienceEngine:
    COMMAND_PREFIXES = (
        "abra ", "feche ", "procure ", "busque ", "calcule ", "faça ",
        "crie ", "mostre ", "diga ", "lembre ", "continue ", "execute ",
    )
    CONTINUITY = ("isso", "aquilo", "continue", "de novo", "anterior")
    URGENT = ("urgente", "agora", "imediatamente")

    def assess(self, text: str) -> SalienceAssessment:
        raw = str(text or "").strip()
        normalized = raw.lower()
        score = 0.25
        signals = []

        if "?" in raw:
            score += 0.18
            signals.append("question")

        if normalized.startswith(self.COMMAND_PREFIXES):
            score += 0.22
            signals.append("command")

        if "star" in normalized:
            score += 0.10
            signals.append("direct_address")

        if any(token in normalized for token in self.CONTINUITY):
            score += 0.14
            signals.append("continuity")

        if any(token in normalized for token in self.URGENT):
            score += 0.16
            signals.append("urgency")

        if len(raw) > 180:
            score += 0.08
            signals.append("complex_input")

        score = round(min(1.0, score), 3)
        if score >= 0.72:
            priority = "high"
        elif score < 0.35:
            priority = "low"
        else:
            priority = "normal"

        return SalienceAssessment(score, priority, tuple(signals))
