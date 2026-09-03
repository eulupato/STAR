"""Conversation Variation Engine da STAR.

Gera small talk procedural, coerente e com memória curta anti-repetição.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime
import random
import re
import unicodedata

from .personality import DEFAULT_PERSONALITY, PersonalityProfile


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFD", str(text or "").lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


class ConversationVariationEngine:
    GREETINGS = {
        "ola", "oi", "e ai", "eai", "opa", "salve", "hey", "hei",
        "bom dia", "boa tarde", "boa noite",
    }
    STATUS = {
        "como vai", "como esta", "como estas", "tudo bem", "tudo certo",
        "beleza", "ta tudo bem", "esta tudo bem",
    }
    THANKS = {"obrigado", "obrigada", "valeu", "brigado", "brigada", "agradecido"}
    FAREWELLS = {"tchau", "ate mais", "ate logo", "falou", "fui", "boa noite star"}

    GENERIC_OPENINGS = (
        "Oi!", "Olá!", "E aí!", "Opa!", "Ei!", "Oi, oi!", "Olá por aí!",
        "E aí, tudo certo?", "Oi, que bom te ver!", "Olá de novo!",
        "E aí, como você está?", "Oi! Tudo tranquilo?", "Opa, chegou!",
        "Olá! Que bom ter você aqui.", "Ei! Estou por aqui.",
    )
    GENERIC_CORES = (
        "Que bom falar com você.",
        "Estou acompanhando você por aqui.",
        "Cheguei junto.",
        "Estou pronta para continuar de onde fizer sentido.",
        "Pode mandar.",
        "Estou atenta ao que você quiser fazer agora.",
        "Tô por aqui e funcionando direitinho.",
        "Vamos nessa.",
        "Estou com você nessa.",
        "Pode trazer a próxima ideia.",
        "Estou pronta para conversar ou fazer alguma coisa.",
        "Fiquei curiosa para saber o que vem agora.",
    )
    GENERIC_ENDINGS = (
        "O que você quer fazer?",
        "Por onde começamos?",
        "Quer conversar sobre alguma coisa?",
        "Qual é a ideia de agora?",
        "O que está passando pela sua cabeça?",
        "Quer ir para alguma ilha ou ficar por aqui?",
        "O que você precisa?",
        "Me conta.",
        "Qual é o próximo passo?",
        "Vamos fazer o quê agora?",
    )

    PERIOD_OPENINGS = {
        "morning": (
            "Bom dia!", "Bom dia por aí!", "Oi, bom dia!", "Bom dia! Tudo certo?",
            "Bom dia! Que bom te ver.", "Ei, bom dia!", "Opa, bom dia!",
            "Bom dia de novo!", "Bom dia! Estou por aqui.", "Bom dia! Vamos nessa.",
            "Oi! Começando o dia?", "Bom dia! Pronta por aqui.",
        ),
        "afternoon": (
            "Boa tarde!", "Oi, boa tarde!", "Boa tarde por aí!", "Ei, boa tarde!",
            "Opa, boa tarde!", "Boa tarde! Tudo certo?", "Boa tarde! Que bom te ver.",
            "Boa tarde de novo!", "Boa tarde! Estou por aqui.", "Boa tarde! Vamos nessa.",
            "Oi! Como está a tarde?", "Boa tarde! Pronta por aqui.",
        ),
        "night": (
            "Boa noite!", "Oi, boa noite!", "Boa noite por aí!", "Ei, boa noite!",
            "Opa, boa noite!", "Boa noite! Tudo certo?", "Boa noite! Que bom te ver.",
            "Boa noite de novo!", "Boa noite! Estou por aqui.", "Boa noite! Vamos nessa.",
            "Oi! Como está a noite?", "Boa noite! Pronta por aqui.",
        ),
    }

    STATUS_OPENINGS = (
        "Estou bem!", "Tudo certo por aqui!", "Estou ótima por aqui!",
        "Funcionando direitinho!", "Tudo tranquilo comigo!", "Estou bem, sim!",
        "Por aqui está tudo certo!", "Estou em ordem!", "Estou legal!",
        "Tudo funcionando!", "Estou firme por aqui!", "Estou bem e atenta!",
    )
    STATUS_CORES = (
        "E gostei de você perguntar.",
        "Bom saber que você quis checar.",
        "Estou acompanhando nossa conversa normalmente.",
        "Minha sessão está estável.",
        "Estou pronta para continuar.",
        "Sem nada estranho por aqui agora.",
        "Minha parte de conversa está acordada.",
        "Estou acompanhando o contexto.",
        "Estou por dentro do que estamos fazendo.",
        "Tudo seguindo normalmente deste lado.",
    )
    STATUS_ENDINGS = (
        "E você, como está?", "E por aí?", "Como você está?",
        "Tudo bem com você também?", "Seu dia está indo bem?",
        "Como estão as coisas por aí?", "Você está bem?",
        "E aí, tudo certo com você?", "Como você está se sentindo hoje?",
        "Quer me contar como está?",
    )

    THANKS_RESPONSES = (
        "Imagina!", "De nada!", "Por nada!", "Sempre que precisar.",
        "Valeu você!", "Disponha.", "Sem problema!", "Fechado!",
        "Tranquilo!", "Que isso, tamo junto.",
    )
    FAREWELL_RESPONSES = (
        "Até mais!", "Tchau!", "A gente se fala!", "Até daqui a pouco!",
        "Vai lá. Até mais!", "Falou!", "Até logo!", "Nos vemos!",
        "Beleza, até depois!", "Certo. Até mais!",
    )

    def __init__(
        self,
        personality: PersonalityProfile = DEFAULT_PERSONALITY,
        *,
        rng: random.Random | None = None,
        recent_limit: int = 24,
    ):
        self.personality = personality
        self.rng = rng or random.SystemRandom()
        self.recent_responses = deque(maxlen=max(8, int(recent_limit)))
        self.recent_openings = deque(maxlen=8)
        self.recent_closings = deque(maxlen=8)
        self.recent_patterns = deque(maxlen=12)

    @staticmethod
    def _period(now: datetime | None = None) -> str:
        hour = (now or datetime.now()).hour
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 18:
            return "afternoon"
        return "night"

    @classmethod
    def detect_intent(cls, text: str) -> tuple[str | None, str | None]:
        normalized = normalize(text)
        if normalized in cls.GREETINGS:
            if normalized == "bom dia":
                return "greeting", "morning"
            if normalized == "boa tarde":
                return "greeting", "afternoon"
            if normalized == "boa noite":
                return "greeting", "night"
            return "greeting", None
        if normalized in cls.STATUS:
            return "status", None
        if normalized in cls.THANKS:
            return "thanks", None
        if normalized in cls.FAREWELLS:
            return "farewell", None
        return None, None

    @classmethod
    def variation_space(cls, intent: str, subtype: str | None = None) -> int:
        if intent == "greeting":
            openings = cls.PERIOD_OPENINGS.get(subtype, cls.GENERIC_OPENINGS)
            return len(openings) * len(cls.GENERIC_CORES) * len(cls.GENERIC_ENDINGS)
        if intent == "status":
            return len(cls.STATUS_OPENINGS) * len(cls.STATUS_CORES) * len(cls.STATUS_ENDINGS)
        if intent == "thanks":
            return len(cls.THANKS_RESPONSES)
        if intent == "farewell":
            return len(cls.FAREWELL_RESPONSES)
        return 0

    def _pick_avoiding(self, options, recent):
        candidates = [item for item in options if item not in recent]
        pool = candidates or list(options)
        return self.rng.choice(pool)

    def _compose(self, openings, cores, endings, pattern: str) -> str:
        for _ in range(20):
            opening = self._pick_avoiding(openings, self.recent_openings)
            core = self.rng.choice(cores)
            closing = self._pick_avoiding(endings, self.recent_closings)
            response = f"{opening} {core} {closing}".strip()
            pattern_key = f"{pattern}|{opening}|{closing}"
            if (
                response not in self.recent_responses
                and pattern_key not in self.recent_patterns
                and not any(
                    phrase in normalize(response)
                    for phrase in map(normalize, self.personality.avoid_phrases)
                )
            ):
                self.recent_responses.append(response)
                self.recent_openings.append(opening)
                self.recent_closings.append(closing)
                self.recent_patterns.append(pattern_key)
                return response

        response = f"{self.rng.choice(openings)} {self.rng.choice(cores)} {self.rng.choice(endings)}"
        self.recent_responses.append(response)
        return response

    def generate(
        self,
        text: str,
        *,
        context: dict | None = None,
        now: datetime | None = None,
    ) -> str | None:
        intent, subtype = self.detect_intent(text)
        if intent is None:
            return None

        if intent == "greeting":
            actual_period = self._period(now)
            # Saudação temporal só é repetida quando combina com o horário.
            # Em caso de divergência, usamos uma abertura neutra para não soar incoerente.
            effective = subtype if subtype == actual_period else None
            openings = self.PERIOD_OPENINGS.get(effective, self.GENERIC_OPENINGS)
            return self._compose(openings, self.GENERIC_CORES, self.GENERIC_ENDINGS, f"greeting:{effective or 'generic'}")

        if intent == "status":
            return self._compose(
                self.STATUS_OPENINGS,
                self.STATUS_CORES,
                self.STATUS_ENDINGS,
                "status",
            )

        if intent == "thanks":
            response = self._pick_avoiding(self.THANKS_RESPONSES, self.recent_responses)
            self.recent_responses.append(response)
            return response

        if intent == "farewell":
            response = self._pick_avoiding(self.FAREWELL_RESPONSES, self.recent_responses)
            self.recent_responses.append(response)
            return response

        return None

    def status(self) -> dict:
        return {
            "recent_responses": len(self.recent_responses),
            "greeting_variations": self.variation_space("greeting"),
            "morning_greeting_variations": self.variation_space("greeting", "morning"),
            "status_variations": self.variation_space("status"),
        }
