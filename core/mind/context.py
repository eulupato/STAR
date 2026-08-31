"""Context Engine da STAR MIND V2."""

from __future__ import annotations

import re
import unicodedata


class ContextEngine:
    NAME_RE = re.compile(
        r"\b(?:meu nome (?:é|e)|eu me chamo|me chamo)\s+"
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,40})",
        re.IGNORECASE,
    )

    STOPWORDS = {
        "a", "as", "o", "os", "de", "da", "do", "das", "dos", "e", "é",
        "em", "um", "uma", "que", "para", "pra", "por", "com", "me", "eu",
        "voce", "você", "star", "isso", "isto", "aquilo",
    }

    def __init__(self):
        self.turn_index = 0
        self.current_topic: str | None = None
        self.last_executor: str | None = None

    @staticmethod
    def normalize(text: str) -> str:
        value = str(text or "").lower().strip()
        value = "".join(
            char
            for char in unicodedata.normalize("NFD", value)
            if unicodedata.category(char) != "Mn"
        )
        value = re.sub(r"[^a-z0-9\s]", " ", value)
        return " ".join(value.split())

    def _infer_topic(self, text: str) -> str | None:
        words = [
            word for word in self.normalize(text).split()
            if len(word) > 2 and word not in self.STOPWORDS
        ]
        if not words:
            return self.current_topic
        return " ".join(words[:4])

    def observe_user(self, text: str, memory):
        self.turn_index += 1
        match = self.NAME_RE.search(str(text or ""))
        if match:
            name = match.group(1).strip().split()[0]
            if name:
                memory.set_fact("user_name", name)

        topic = self._infer_topic(text)
        if topic:
            self.current_topic = topic

    def observe_response(self, executor: str | None):
        self.last_executor = executor

    def local_response(self, text: str, memory):
        normalized = self.normalize(text)

        if normalized in {
            "qual meu nome",
            "qual e meu nome",
            "qual o meu nome",
            "voce lembra meu nome",
            "lembra meu nome",
        }:
            name = memory.get_fact("user_name")
            if name:
                return f"Você me disse que seu nome é {name}. ⭐"

        if self.NAME_RE.search(str(text or "")):
            name = memory.get_fact("user_name")
            if name:
                return (
                    f"Prazer, {name}! ⭐ Vou manter seu nome na minha memória "
                    "de trabalho durante esta sessão."
                )

        if normalized in {
            "o que eu acabei de dizer",
            "o que eu disse",
            "qual foi minha mensagem anterior",
        }:
            user_turns = memory.recent(role="user", limit=2)
            if len(user_turns) >= 2:
                return f"Você tinha dito: “{user_turns[-2].content}”"

        return None

    def snapshot(self, memory) -> dict:
        return {
            "turn_index": self.turn_index,
            "current_topic": self.current_topic,
            "last_executor": self.last_executor,
            "facts": memory.facts(),
            "active_task": memory.active_task,
        }
