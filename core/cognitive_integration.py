"""Integração cognitiva do caminho normal de resposta da STAR.

Este módulo NÃO cria outro cérebro, memória, planner, personalidade ou sistema de
raciocínio. Ele conecta os componentes já existentes (B12-B24) ao Router/Executive
e produz uma posição cognitiva efêmera antes da expressão.

Princípios:
- informação do usuário não vira crença/opinião da STAR automaticamente;
- FAST PATH evita o ciclo profundo quando ele não agrega valor;
- DELIBERATIVE PATH reutiliza o MindLoop B24 e seus componentes oficiais;
- opinião persistente usa o mesmo ``cognitive_memory`` já utilizado pela STAR,
  mas com ``kind=opinion`` separado de ``preference``;
- pensar/decidir não executa ferramentas nem concede permissões;
- a expressão é derivada da posição cognitiva, não de falas específicas por input.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from time import perf_counter
import re
import unicodedata
from typing import Any, Iterable


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _canonical_topic(value: Any) -> str:
    """Normaliza somente bordas linguísticas, sem tentar inferir o assunto."""
    text = _norm(value)
    previous = None
    while text and text != previous:
        previous = text
        text = re.sub(
            r"^(?:sobre|do|da|dos|das|de|no|na|nos|nas|o|a|os|as|um|uma)\s+",
            "",
            text,
        ).strip()
    return text


def _slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _canonical_topic(value)).strip("_")[:120]


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


OPINION_REQUEST_HINTS = (
    "o que voce acha", "qual sua opiniao", "voce acha", "acha que",
    "gostou", "voce gosta", "voce prefere", "qual voce prefere",
    "fica bonito", "fico bonito", "fica bonita", "fico bonita",
    "vale a pena", "voce escolheria", "qual escolheria",
)

DECISION_HINTS = (
    "devo ", "vale a pena", "qual escolher", "o que eu faco", "o que faco",
    "qual e melhor", "qual seria melhor", "me ajuda a decidir", "decisao",
    "planeje", "planejar", "compare", "comparar",
)

DELIBERATIVE_HINTS = (
    "analise", "analisar", "raciocine", "raciocinar", "por que", "porque",
    "hipotese", "hipótese", "consequencia", "consequência", "risco",
    "simule", "simular", "discorda", "concorda", "argumento",
)

AESTHETIC_HINTS = (
    "roupa", "look", "visual", "estilo", "jaqueta", "camisa", "vestido",
    "tenis", "tênis", "sapato", "cabelo", "maquiagem", "design", "logo",
    "foto", "imagem",
)

POSITIVE_TERMS = (
    "gostei", "gosto", "amo", "bonito", "bonita", "otimo", "ótimo",
    "excelente", "legal", "bom", "boa", "incrivel", "incrível", "perfeito",
)
NEGATIVE_TERMS = (
    "nao gostei", "não gostei", "odeio", "horrivel", "horrível", "pessimo",
    "péssimo", "feio", "feia", "ruim", "chato", "chata", "terrivel", "terrível",
)

ARGUMENT_HINTS = ("porque", "pois", "ja que", "já que", "por causa", "motivo")
RISK_HINTS = (
    "perigo", "perigoso", "risco", "machucar", "quebrar", "perder", "urgente",
    "agora", "prazo", "atrasado", "emergencia", "emergência",
)


class CognitiveIntegration:
    """Ponte fina entre o pipeline estável e a cognição já existente."""

    SCHEMA = "star.cognitive_position.v1"
    OPINION_KEY_PREFIX = "star.opinion"

    def __init__(self, star):
        self.star = star
        self.mind_loop = star.mind_loop
        self.memory = star.memory_continuity
        self.personality = star.affective_personality
        self.social = star.social_cognition
        self.identity = star.identity
        self._last_position: dict | None = None

    # ------------------------------------------------------------------
    # Seleção de caminho
    # ------------------------------------------------------------------
    def select_path(self, text: str, *, internal_response: bool = False) -> str:
        raw = _clean(text)
        norm = _norm(raw)
        if not raw or internal_response:
            return "FAST"
        words = norm.split()
        if self._is_opinion_request(norm) or any(h in norm for h in DECISION_HINTS):
            return "DELIBERATIVE"
        if any(h in norm for h in DELIBERATIVE_HINTS):
            return "DELIBERATIVE"
        if "?" in raw and len(words) >= 10:
            return "DELIBERATIVE"
        if len(words) >= 24:
            return "DELIBERATIVE"
        if self._user_stance(raw) is not None and len(words) >= 3:
            return "DELIBERATIVE"
        return "FAST"

    def perceived_intent(self, text: str) -> str:
        raw = _clean(text)
        norm = _norm(raw)
        if self._is_opinion_request(norm):
            return "request_opinion"
        if any(h in norm for h in DECISION_HINTS):
            return "decision_support"
        if self._user_stance(raw) is not None:
            return "share_opinion"
        if "?" in raw:
            return "question"
        return "information_or_conversation"

    # ------------------------------------------------------------------
    # Opiniões persistentes no store oficial, separadas de preferências
    # ------------------------------------------------------------------
    @classmethod
    def _opinion_key(cls, topic: str) -> str:
        return f"{cls.OPINION_KEY_PREFIX}.{_slug(topic)}"

    def _opinion_store(self):
        """Retorna o CognitiveStore/EpistemicStore já usado pelo B13/B17."""
        cognitive_memory = getattr(self.memory, "memory", None)
        store = getattr(cognitive_memory, "store", None)
        if store is None:
            raise RuntimeError("store cognitivo oficial indisponível")
        return store

    def opinion(self, topic: str) -> dict | None:
        if not _clean(topic):
            return None
        record = self._opinion_store().memory_by_key(self._opinion_key(topic), kind="opinion")
        if not record:
            return None
        metadata = record.get("metadata") or {}
        value = deepcopy(metadata.get("value"))
        if not isinstance(value, dict) or value.get("epistemic_kind") != "opinion":
            return None
        value["record"] = record
        return value

    def record_opinion(
        self,
        topic: str,
        position: str,
        *,
        intensity: float = 0.5,
        justification: str = "",
        evidence: Iterable[str] | None = None,
        related_preferences: Iterable[str] | None = None,
        related_values: Iterable[str] | None = None,
        confidence: float = 0.6,
        origin: str = "deliberation",
        source: str,
        reference: str,
        reason: str = "",
    ) -> dict:
        topic = _clean(topic)
        position = _clean(position)
        source = _clean(source)
        reference = _clean(reference)
        if not topic or not position:
            raise ValueError("opinião requer tema e posição")
        if not source or not reference:
            raise ValueError("opinião persistente requer fonte e referência auditáveis")

        previous = self.opinion(topic)
        previous_record = (previous or {}).get("record") or {}
        value = {
            "epistemic_kind": "opinion",
            "topic": topic,
            "position": position,
            "intensity": _clamp(intensity),
            "justification": _clean(justification) or None,
            "evidence": tuple(_clean(x) for x in (evidence or ()) if _clean(x))[:16],
            "related_preferences": tuple(_clean(x) for x in (related_preferences or ()) if _clean(x))[:16],
            "related_values": tuple(_clean(x) for x in (related_values or ()) if _clean(x))[:16],
            "confidence": _clamp(confidence),
            "origin": _clean(origin) or "deliberation",
            "reason": _clean(reason) or None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "revision_of_memory_id": previous_record.get("id"),
            "user_claim_is_source_of_star_opinion": False,
            "fact": False,
        }
        metadata = {
            "block": "COGNITIVE-INTEGRATION",
            "epistemic_kind": "opinion",
            "value": deepcopy(value),
            "source": source,
            "reference": reference,
            "confidence": _clamp(confidence),
            "identity_mutation": False,
            "fundamental_values_mutation": False,
            "permission_mutation": False,
            "preference_kind": False,
        }
        store = self._opinion_store()
        memory_id = store.remember(
            "opinion",
            f"{topic}: {position}",
            key=self._opinion_key(topic),
            metadata=metadata,
            importance=0.7,
        )
        record = store.memory_by_id(memory_id)
        return {**value, "memory_id": memory_id, "record": record, "history_preserved": True}

    def revise_opinion(self, topic: str, position: str, **kwargs) -> dict:
        if self.opinion(topic) is None:
            raise ValueError("não existe opinião anterior para revisar")
        kwargs.setdefault("origin", "revision")
        return self.record_opinion(topic, position, **kwargs)

    # ------------------------------------------------------------------
    # Posição cognitiva
    # ------------------------------------------------------------------
    def build_position(self, request: dict, route: dict | None = None) -> dict:
        started = perf_counter()
        route = route or {}
        text = _clean(request.get("input"))
        internal = bool(route.get("internal_response"))

        t0 = perf_counter()
        path = route.get("cognitive_path") or self.select_path(text, internal_response=internal)
        path_ms = (perf_counter() - t0) * 1000

        intent = self.perceived_intent(text)
        topic = self._extract_topic(text, intent)
        user_stance = self._user_stance(text)

        t0 = perf_counter()
        affect = self.personality.current_state()
        affect_ms = (perf_counter() - t0) * 1000

        t0 = perf_counter()
        star_opinion = self.opinion(topic) if topic else None
        memories = []
        if path == "DELIBERATIVE" and topic:
            memories = self.memory.recall(topic, limit=6)
        memory_ms = (perf_counter() - t0) * 1000

        missing = self._missing_context(text, intent)
        risk = self._risk_score(text)
        urgency = self._urgency_score(text)
        goal = self._goal_for(intent, topic)

        cycle = None
        loop_ms = 0.0
        if path == "DELIBERATIVE":
            t0 = perf_counter()
            cycle = self.mind_loop.run_cycle(
                text,
                query=topic or text,
                goal=goal,
                missing_context=missing,
                risk=risk,
                urgency=urgency,
                permission=False,
                capability=False,
                safety_ok=False,
                active_limit=16,
            )
            loop_ms = (perf_counter() - t0) * 1000

        identity = self._identity_snapshot()
        values = tuple((identity.get("purpose") or {}).get("principles") or ())[:8]
        social_context = {
            "actor": request.get("actor") or "session_user",
            "relationship": request.get("relationship") or "session",
            "familiarity": affect.get("familiarity", 0.0),
            "trust_grants_permission": False,
            "authorization_inferred": False,
        }

        epistemic = self._epistemic_summary(cycle, memories)
        confidence = self._position_confidence(cycle, star_opinion)
        needs = self._needs(cycle, missing, star_opinion, user_stance, intent)
        disagreement = self._disagreement(star_opinion, user_stance)
        tone = self._tone(affect, confidence, risk, urgency)
        decision = self._communication_decision(
            intent=intent,
            topic=topic,
            star_opinion=star_opinion,
            user_stance=user_stance,
            needs=needs,
            disagreement=disagreement,
            risk=risk,
            urgency=urgency,
        )
        initiative = self._initiative_candidate(text, risk, urgency, needs)

        position = {
            "schema": self.SCHEMA,
            "processing_path": path,
            "subject": topic or None,
            "perceived_intent": intent,
            "input_classification": "information_received",
            "user_statement_becomes_star_belief": False,
            "state": affect,
            "social_context": social_context,
            "values": values,
            "user_position": user_stance,
            "star_opinion": star_opinion,
            "epistemic": epistemic,
            "confidence": confidence,
            "uncertainties": tuple(missing),
            "needs": needs,
            "disagreement": disagreement,
            "decision": decision,
            "tone": tone,
            "initiative": initiative,
            "cycle_id": (cycle or {}).get("cycle_id"),
            "execution_performed": False,
            "operational_authorization": False,
            "timings_ms": {
                "path_selection": round(path_ms, 3),
                "affective_processing": round(affect_ms, 3),
                "memory_retrieval": round(memory_ms, 3),
                "mind_loop": round(loop_ms, 3),
            },
        }
        position = self._drop_empty(position)
        position["timings_ms"]["position_total"] = round((perf_counter() - started) * 1000, 3)
        self._last_position = deepcopy(position)

        # Posição efêmera compartilhada: working memory, não novo banco.
        self.memory.working.add(
            f"posição cognitiva: {intent} / {topic or 'sem tema explícito'}",
            key="cognitive_integration:last_position",
            importance=0.8 if path == "DELIBERATIVE" else 0.4,
            context={
                "schema": self.SCHEMA,
                "processing_path": path,
                "confidence": confidence,
                "decision": decision,
            },
            source="CognitiveIntegration",
            metadata={"persistent": False, "operational_authorization": False},
        )
        return position

    def last_position(self) -> dict | None:
        return deepcopy(self._last_position)

    # ------------------------------------------------------------------
    # Expressão: usa a posição; não decide identidade nem fatos.
    # ------------------------------------------------------------------
    def expression(self, position: dict) -> str | None:
        started = perf_counter()
        intent = position.get("perceived_intent")
        topic = position.get("subject") or "isso"
        opinion = position.get("star_opinion") or {}
        needs = position.get("needs") or {}
        disagreement = position.get("disagreement") or {}
        confidence = float(position.get("confidence", 0.0))
        result = None

        if intent in {"request_opinion", "share_opinion"}:
            if opinion:
                stance = _clean(opinion.get("position"))
                reason = _clean(opinion.get("justification"))
                prefix = "Eu vejo diferente" if disagreement.get("active") else "Minha posição"
                confidence_phrase = "" if confidence >= 0.7 else " por enquanto"
                result = f"{prefix}{confidence_phrase} sobre {topic}: {stance}."
                if reason:
                    result += f" {reason}"
                if needs.get("ask"):
                    result += f" {self._question_for_missing(position.get('uncertainties') or ())}"
            else:
                if needs.get("ask"):
                    result = (
                        f"Ainda não tenho base suficiente para formar uma opinião honesta sobre {topic}. "
                        f"{self._question_for_missing(position.get('uncertainties') or ())}"
                    )
                else:
                    result = (
                        f"Ainda não formei uma opinião própria sólida sobre {topic}. "
                        "Prefiro manter isso como indefinido do que copiar automaticamente a sua posição."
                    )

        if result is None and (position.get("decision") or {}).get("communicate_warning"):
            result = (
                "Eu teria cautela com essa decisão agora. "
                "O contexto indica risco ou urgência suficiente para eu não tratar isso como uma escolha neutra."
            )

        elapsed = (perf_counter() - started) * 1000
        position.setdefault("timings_ms", {})["expression_generation"] = round(elapsed, 3)
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _is_opinion_request(norm: str) -> bool:
        return any(h in norm for h in OPINION_REQUEST_HINTS)

    @staticmethod
    def _user_stance(text: str) -> dict | None:
        norm = _norm(text)
        neg = sum(1 for term in NEGATIVE_TERMS if _norm(term) in norm)
        pos = sum(1 for term in POSITIVE_TERMS if _norm(term) in norm)
        if not neg and not pos:
            return None
        if neg == pos:
            label = "mixed"
            valence = 0.0
        elif neg > pos:
            label = "negative"
            valence = -min(1.0, 0.4 + 0.15 * neg)
        else:
            label = "positive"
            valence = min(1.0, 0.4 + 0.15 * pos)
        return {
            "epistemic_kind": "user_opinion",
            "stance": label,
            "valence": valence,
            "becomes_star_opinion": False,
        }

    def _extract_topic(self, text: str, intent: str) -> str:
        raw = _clean(text).strip(" ?!.,")
        norm = _norm(raw)
        copula = re.search(
            r"^(?:eu acho que\s+)?(.+?)\s+(?:e|eh|parece|ficou|esta|ta)\s+"
            r"(?:muito\s+)?(?:horrivel|pessimo|ruim|bom|otimo|excelente|bonito|bonita|feio|feia)\b",
            norm,
        )
        if copula:
            return _canonical_topic(copula.group(1))[:160]
        cleaned = norm
        for hint in sorted(OPINION_REQUEST_HINTS, key=len, reverse=True):
            cleaned = cleaned.replace(hint, " ")
        cleaned = re.sub(r"\b(star|voce|você|eu|me|minha|meu|sobre|disso|disto|acha|opiniao)\b", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = _canonical_topic(cleaned)
        if intent == "decision_support" and not cleaned:
            return "decisão atual"
        return (cleaned or _canonical_topic(raw) or raw)[:160]

    @staticmethod
    def _missing_context(text: str, intent: str) -> tuple[str, ...]:
        norm = _norm(text)
        missing: list[str] = []
        if intent == "request_opinion" and any(_norm(h) in norm for h in AESTHETIC_HINTS):
            if not any(h in norm for h in ("foto", "imagem", "vestindo", "estou usando", "descricao", "descrição")):
                missing.append("características visuais ou descrição")
            if not any(h in norm for h in ("ocasiao", "ocasião", "festa", "trabalho", "escola", "show", "evento", "dia a dia")):
                missing.append("ocasião")
        return tuple(missing)

    @staticmethod
    def _goal_for(intent: str, topic: str) -> str:
        if intent in {"request_opinion", "share_opinion"}:
            return f"formar ou revisar posição independente sobre {topic or 'o tema'}"
        if intent == "decision_support":
            return f"avaliar decisão sobre {topic or 'a situação'}"
        if intent == "question":
            return f"responder com confiança calibrada sobre {topic or 'a pergunta'}"
        return "interpretar a interação e decidir o que vale comunicar"

    @staticmethod
    def _risk_score(text: str) -> float:
        norm = _norm(text)
        hits = sum(1 for term in RISK_HINTS if _norm(term) in norm)
        return _clamp(hits * 0.18)

    @staticmethod
    def _urgency_score(text: str) -> float:
        norm = _norm(text)
        hits = sum(1 for term in ("agora", "urgente", "imediatamente", "prazo", "atrasado", "hoje") if term in norm)
        return _clamp(hits * 0.22)

    def _identity_snapshot(self) -> dict:
        if self.identity is None:
            return {}
        try:
            return deepcopy(self.identity.get())
        except AttributeError:
            return deepcopy(getattr(self.identity, "data", {}) or {})

    @staticmethod
    def _epistemic_summary(cycle: dict | None, memories: list[dict]) -> dict:
        if cycle is None:
            return {"memory_items": len(memories), "fact_from_user_claim": False}
        stages = cycle.get("stages") or {}
        knowledge = ((stages.get("conhecimento") or {}).get("items") or [])
        interpretation = stages.get("interpretacao") or {}
        meta = stages.get("metacognicao") or {}
        result = {
            "memory_items": len(memories),
            "knowledge_items": len(knowledge),
            "inference": interpretation.get("conclusion") or interpretation.get("summary"),
            "hypotheses": interpretation.get("hypotheses"),
            "known": meta.get("knows"),
            "unknown": meta.get("does_not_know"),
            "sources": meta.get("sources"),
            "fact_from_user_claim": False,
            "inference_is_fact": False,
            "opinion_is_fact": False,
        }
        return CognitiveIntegration._drop_empty(result)

    @staticmethod
    def _position_confidence(cycle: dict | None, opinion: dict | None) -> float:
        if opinion is not None:
            return _clamp(opinion.get("confidence", 0.5))
        if cycle is None:
            return 0.5
        meta = ((cycle.get("stages") or {}).get("metacognicao") or {})
        return _clamp(meta.get("confidence", 0.4))

    @staticmethod
    def _needs(cycle: dict | None, missing: Iterable[str], opinion: dict | None,
               user_stance: dict | None, intent: str) -> dict:
        meta = ((cycle or {}).get("stages") or {}).get("metacognicao") or {}
        missing = tuple(missing)
        return {
            "research": bool(meta.get("needs_research")),
            "ask": bool(missing or meta.get("needs_question")),
            "review": bool(meta.get("needs_review")),
            "independent_opinion_missing": bool(intent in {"request_opinion", "share_opinion"} and opinion is None),
            "user_opinion_received": bool(user_stance),
        }

    @staticmethod
    def _disagreement(opinion: dict | None, user_stance: dict | None) -> dict:
        if not opinion or not user_stance:
            return {"active": False}
        star = _norm(opinion.get("position"))
        user = user_stance.get("stance")
        positive = any(term in star for term in ("gosto", "positivo", "bom", "otimo", "excelente", "agrada"))
        negative = any(term in star for term in ("nao gosto", "negativo", "ruim", "horrivel", "desagrada"))
        active = (positive and user == "negative") or (negative and user == "positive")
        return {
            "active": bool(active),
            "reason": "posição persistente da STAR difere da opinião recebida" if active else None,
            "user_claim_overwrites_star": False,
        }

    @staticmethod
    def _tone(affect: dict, confidence: float, risk: float, urgency: float) -> dict:
        return {
            "directness": "high" if urgency >= 0.5 else "normal",
            "caution": "high" if risk >= 0.5 or float(affect.get("caution", 0.5)) >= 0.7 else "normal",
            "certainty": "confident" if confidence >= 0.75 else ("tentative" if confidence < 0.5 else "balanced"),
            "energy": affect.get("energy"),
            "familiarity": affect.get("familiarity"),
        }

    @staticmethod
    def _communication_decision(*, intent: str, topic: str, star_opinion: dict | None,
                                user_stance: dict | None, needs: dict, disagreement: dict,
                                risk: float, urgency: float) -> dict:
        if needs.get("ask"):
            action = "ask_for_context"
        elif disagreement.get("active"):
            action = "express_independent_disagreement"
        elif intent == "request_opinion" and star_opinion:
            action = "express_opinion"
        elif intent == "request_opinion":
            action = "state_uncertainty"
        elif risk >= 0.5 or urgency >= 0.7:
            action = "warn_or_flag"
        else:
            action = "continue_normal_response"
        return {
            "communicative_action": action,
            "topic": topic or None,
            "communicate_warning": action == "warn_or_flag",
            "should_disagree": bool(disagreement.get("active")),
            "should_ask": bool(needs.get("ask")),
            "execution_performed": False,
        }

    @staticmethod
    def _initiative_candidate(text: str, risk: float, urgency: float, needs: dict) -> dict:
        relevance = max(risk, urgency)
        should_surface = bool(relevance >= 0.7 and not needs.get("ask"))
        return {
            "eligible": should_surface,
            "relevance": round(relevance, 3),
            "reason": "risk_or_urgency" if should_surface else None,
            "automatic_interruption": False,
            "requires_external_scheduler_or_event": True,
        }

    @staticmethod
    def _question_for_missing(missing: Iterable[str]) -> str:
        items = [str(x) for x in missing if _clean(x)]
        if not items:
            return "Você consegue me dar um pouco mais de contexto?"
        if len(items) == 1:
            return f"Antes de fechar minha opinião, me diga {items[0]}."
        return f"Antes de fechar minha opinião, preciso de {items[0]} e {items[1]}."

    @staticmethod
    def _drop_empty(value: Any) -> Any:
        if isinstance(value, dict):
            out = {}
            for key, item in value.items():
                cleaned = CognitiveIntegration._drop_empty(item)
                if cleaned is not None and cleaned != () and cleaned != [] and cleaned != {}:
                    out[key] = cleaned
            return out
        if isinstance(value, list):
            return [CognitiveIntegration._drop_empty(x) for x in value if x is not None]
        if isinstance(value, tuple):
            return tuple(CognitiveIntegration._drop_empty(x) for x in value if x is not None)
        return value
