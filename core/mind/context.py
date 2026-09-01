"""Context Engine consolidado da STAR MIND."""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import re
import unicodedata


@dataclass(frozen=True)
class EntityReference:
    name: str
    entity_id: str | None = None
    category: str | None = None


class ContextEngine:
    NAME_RE = re.compile(
        r"\b(?:meu nome (?:é|e)|eu me chamo|me chamo)\s+"
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,40})",
        re.IGNORECASE,
    )
    ENTITY_PROMPT_RE = re.compile(
        r"\b(?:quem (?:é|e|foi)|fale sobre|me fale sobre|sobre)\s+"
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ0-9' .\-]{1,80})",
        re.IGNORECASE,
    )
    PRONOUN_RE = re.compile(
        r"\b(ele|ela|dele|dela|nele|nela|esse|essa|deste|desta|desse|dessa)\b",
        re.IGNORECASE,
    )

    STOPWORDS = {
        "a", "as", "o", "os", "de", "da", "do", "das", "dos", "e", "é",
        "em", "um", "uma", "que", "para", "pra", "por", "com", "me", "eu",
        "voce", "você", "star", "isso", "isto", "aquilo", "quem", "qual",
        "quais", "onde", "como", "quando",
    }

    def __init__(self):
        self.turn_index = 0
        self.current_topic: str | None = None
        self.last_executor: str | None = None
        self._entities = deque(maxlen=12)
        self.last_resolved_text: str | None = None

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

    def track_entity(
        self,
        name: str,
        *,
        entity_id: str | None = None,
        category: str | None = None,
    ):
        name = str(name or "").strip()
        if not name:
            return
        normalized = self.normalize(name)
        self._entities = deque(
            [item for item in self._entities if self.normalize(item.name) != normalized],
            maxlen=12,
        )
        self._entities.append(EntityReference(name, entity_id, category))

    @property
    def current_entity(self) -> EntityReference | None:
        return self._entities[-1] if self._entities else None

    def resolve_reference_text(self, text: str) -> str:
        raw = str(text or "")
        entity = self.current_entity
        if entity is None or not self.PRONOUN_RE.search(raw):
            return raw
        return self.PRONOUN_RE.sub(entity.name, raw)

    def _observe_explicit_entity(self, text: str):
        match = self.ENTITY_PROMPT_RE.search(str(text or ""))
        if not match:
            return
        candidate = match.group(1).strip(" ?!.")
        if candidate and self.normalize(candidate) not in self.STOPWORDS:
            self.track_entity(candidate)

    def observe_user(self, text: str, memory):
        self.turn_index += 1
        self.last_resolved_text = self.resolve_reference_text(text)

        match = self.NAME_RE.search(str(text or ""))
        if match:
            name = match.group(1).strip().split()[0]
            if name:
                memory.set_fact("user_name", name)

        self._observe_explicit_entity(self.last_resolved_text)

        topic = self._infer_topic(self.last_resolved_text)
        if topic:
            self.current_topic = topic

    def observe_response(self, executor: str | None):
        self.last_executor = executor

    def local_response(self, text: str, memory):
        normalized = self.normalize(text)

        if normalized in {
            "qual meu nome", "qual e meu nome", "qual o meu nome",
            "voce lembra meu nome", "lembra meu nome",
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
            "o que eu acabei de dizer", "o que eu disse",
            "qual foi minha mensagem anterior",
        }:
            user_turns = memory.recent(role="user", limit=2)
            if len(user_turns) >= 2:
                return f"Você tinha dito: “{user_turns[-2].content}”"

        if normalized in {"de quem estamos falando", "quem e ele", "quem e ela"}:
            entity = self.current_entity
            if entity:
                return f"Estamos falando de {entity.name}."

        return None

    def snapshot(self, memory) -> dict:
        return {
            "turn_index": self.turn_index,
            "current_topic": self.current_topic,
            "last_executor": self.last_executor,
            "facts": memory.facts(),
            "active_task": memory.active_task,
            "current_entity": asdict(self.current_entity) if self.current_entity else None,
            "recent_entities": [asdict(item) for item in self._entities],
            "resolved_text": self.last_resolved_text,
        }
