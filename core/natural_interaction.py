"""Runtime de interação natural da STAR.

Não é outro cérebro, memória, identidade ou sistema de decisão. Conecta contexto
de diálogo, B13/B17/B25/B26 e a posição cognitiva existente à expressão final.
Um modelo local opcional atua somente como *surface realizer*: fatos, opiniões,
incerteza, identidade, autenticação, permissões e ações continuam pertencendo à
arquitetura oficial da STAR.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import time
import unicodedata
from urllib.parse import urlparse
from typing import Any

from core.ai_engine import AIEngine


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _clip(value: Any, limit: int = 360) -> str:
    text = _clean(value)
    return text if len(text) <= limit else text[: max(0, limit - 1)].rstrip() + "…"


def _env_true(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return raw.strip().casefold() in {"1", "true", "yes", "on", "sim"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class NaturalInteraction:
    """Continuidade conversacional bounded + expressão generativa opcional."""

    MAX_TURNS = 24
    MODEL_PROBE_TTL = 60.0
    PERSIST_EVERY_TURNS = 8
    MAX_MODEL_OUTPUT = 1800

    FOLLOWUP_MARKERS = (
        "e ele", "e ela", "e isso", "e esse", "e essa", "e aquele", "e aquela",
        "e a preta", "e o preto", "e a outra", "e o outro", "e depois", "e agora",
        "mas e", "e se", "por que", "porque", "qual deles", "qual delas",
    )
    UNCERTAINTY_MARKERS = (
        "ainda não", "ainda nao", "não tenho", "nao tenho", "não sei", "nao sei",
        "base suficiente", "preciso de", "falta", "incerto", "incerta", "provisóri",
    )

    def __init__(self, star, *, expression_model=None, max_turns: int = MAX_TURNS):
        self.star = star
        self.memory = star.memory_continuity
        self.people = getattr(star, "people_entities", None)
        self.personality = star.affective_personality
        self.perception = getattr(star, "multimodal_perception", None)
        self.history = deque(maxlen=max(6, min(int(max_turns), 64)))
        self.turn_index = 0
        self.active_topic: str | None = None
        self.active_person_id: str | None = None
        self.active_person_name: str | None = None
        self.last_reference_target: str | None = None
        self.last_persisted_turn = 0
        self.session_id = hashlib.sha256(f"{_now()}|{id(self)}".encode()).hexdigest()[:16]

        self._expression_model = expression_model
        self._model_host = os.getenv("STAR_LOCAL_LLM_HOST", "http://127.0.0.1:11434").rstrip("/")
        self._model_name = os.getenv("STAR_LOCAL_LLM_MODEL", "qwen3:8b").strip() or "qwen3:8b"
        self._model_enabled = _env_true("STAR_NATURAL_DIALOGUE_LOCAL_LLM", True)
        self._model_timeout = max(1.0, min(float(os.getenv("STAR_NATURAL_DIALOGUE_TIMEOUT", "8")), 30.0))
        self._local_host_allowed = self._is_loopback_host(self._model_host)
        self._default_model = None
        if self._expression_model is None and self._model_enabled and self._local_host_allowed:
            self._default_model = AIEngine(model=self._model_name, host=self._model_host, enabled=True)
        self._probe_at = 0.0
        self._probe_available = False
        self._last_expression_mode = "semantic-fallback"
        self._last_generation_error: str | None = None

    @staticmethod
    def _is_loopback_host(url: str) -> bool:
        try:
            host = (urlparse(url).hostname or "").casefold()
        except ValueError:
            return False
        return host in {"localhost", "127.0.0.1", "::1"}

    @staticmethod
    def _known_operational_command(text: str) -> bool:
        try:
            from core.commands import match_command
            return match_command(text) is not None
        except (ImportError, RuntimeError, ValueError):
            return False

    def declare_person(self, name: str) -> dict | None:
        name = _clean(name)
        if not name or self.people is None:
            return None
        if self.active_person_name and _norm(self.active_person_name) == _norm(name):
            return {
                "person_id": self.active_person_id,
                "name": self.active_person_name,
                "reused": True,
                "authenticated": False,
            }
        if hasattr(self.people, "upsert_declared_person"):
            person = self.people.upsert_declared_person(
                name,
                source="user-self-declaration",
                reference=f"declared:{_norm(name)}",
            )
        else:
            person = self.people.create_person(
                name,
                source="user-self-declaration",
                reference=f"declared:{_norm(name)}",
                metadata={"declared_by_user": True, "authentication": False},
            )
        self.active_person_id = person.get("person_id")
        self.active_person_name = name
        self.personality.update_session_affect(familiarity=0.45, context="conversation")
        return {**person, "authenticated": False, "recognition_is_authentication": False}

    @staticmethod
    def _declared_name(text: str) -> str | None:
        match = re.search(r"\bmeu nome (?:e|é)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,40})", str(text or ""), re.I)
        return _clean(match.group(1)).split()[0] if match else None

    def _perception_context(self) -> tuple[list[dict], bool]:
        if self.perception is None or not hasattr(self.perception, "workspace_observations"):
            return [], False
        try:
            observations = list(self.perception.workspace_observations(limit=8) or ())[:8]
        except (AttributeError, RuntimeError, ValueError, OSError):
            return [], False
        has_visual = any(
            _norm(item.get("modality")) in {"vision", "screen"}
            or {_norm(value) for value in item.get("modalities", ())}.intersection({"vision", "screen"})
            for item in observations
            if isinstance(item, dict)
        )
        return deepcopy(observations), bool(has_visual)

    def _person_context(self) -> dict:
        if not self.active_person_id or self.people is None:
            return {}
        try:
            return self.people.person_context(self.active_person_id, limit=8)
        except (KeyError, RuntimeError, ValueError, OSError, AttributeError):
            return {"person_id": self.active_person_id, "bounded": True}

    def _resolve_followup(self, text: str) -> tuple[str, str | None]:
        text = _clean(text)
        if not self.active_topic or self._known_operational_command(text):
            return text, None
        norm = _norm(text)
        words = norm.split()
        marker = any(_norm(item) in norm for item in self.FOLLOWUP_MARKERS)
        short_question = len(words) <= 7 and ("?" in text or norm.startswith(("e ", "mas ", "qual ", "por que", "porque")))
        if not (marker or short_question):
            return text, None
        return f"{text} [continuação contextual: {self.active_topic}]", self.active_topic

    def begin_turn(self, text: str, *, raw_text: str | None = None) -> dict:
        text = _clean(text)
        self.turn_index += 1
        declared_name = self._declared_name(text)
        if declared_name:
            self.declare_person(declared_name)
        contextual_input, reference_target = self._resolve_followup(text)
        observations, has_visual = self._perception_context()
        context = {
            "session_id": self.session_id,
            "turn": self.turn_index,
            "input": text,
            "raw_input": _clean(raw_text) if raw_text is not None else text,
            "contextual_input": contextual_input,
            "reference_target": reference_target,
            "active_topic": self.active_topic,
            "actor": self.active_person_id or "session_user",
            "relationship": "known_person" if self.active_person_id else "session",
            "person_id": self.active_person_id,
            "person_name": self.active_person_name,
            "person_context": self._person_context(),
            "recent_turns": [deepcopy(item) for item in list(self.history)[-6:]],
            "affect": self.personality.current_state(),
            "perception": observations,
            "has_visual_evidence": has_visual,
            "bounded": True,
        }
        self.last_reference_target = reference_target
        self.memory.working.add(
            text or "interação vazia",
            key=f"natural_dialogue:user:{self.turn_index}",
            importance=0.55,
            context={
                "session_id": self.session_id,
                "turn": self.turn_index,
                "active_topic": self.active_topic,
                "active_person_id": self.active_person_id,
                "reference_target": reference_target,
            },
            source="NaturalInteraction",
            metadata={"persistent": False, "role": "user", "operational_authorization": False},
        )
        return context

    def _provisional_opinion(self, position: dict | None) -> dict | None:
        if not position or position.get("star_opinion") or (position.get("needs") or {}).get("ask"):
            return None
        if position.get("perceived_intent") not in {"request_opinion", "share_opinion", "decision_support"}:
            return None
        topic = _clean(position.get("subject"))
        if not topic:
            return None
        try:
            preference = self.personality.preference(topic)
        except (KeyError, ValueError, RuntimeError, AttributeError):
            preference = None
        if preference is not None:
            value = preference.get("value")
            if value is not None and value != "":
                confidence = float(((preference.get("record") or {}).get("metadata") or {}).get("confidence", 0.65))
                return {
                    "position": _clip(value, 320),
                    "confidence": max(0.0, min(confidence, 1.0)),
                    "basis": "B17 preference",
                    "persistent": False,
                    "fact": False,
                }
        inference = _clean((position.get("epistemic") or {}).get("inference"))
        if inference and _norm(inference) not in {"interpretacao revisavel", "inferencia revisavel"}:
            confidence = max(0.0, min(float(position.get("confidence", 0.45)), 1.0))
            if confidence >= 0.4:
                return {
                    "position": _clip(inference, 420),
                    "confidence": confidence,
                    "basis": "B24/B18 current inference",
                    "persistent": False,
                    "fact": False,
                }
        return None

    def _semantic_anchor(self, response: str, position: dict | None) -> tuple[str, dict | None]:
        provisional = self._provisional_opinion(position)
        if provisional is None:
            return _clean(response), None
        topic = _clean((position or {}).get("subject")) or "isso"
        return (
            f"Posição provisória da STAR sobre {topic}: {provisional['position']}. "
            f"Confiança aproximada {provisional['confidence']:.2f}; é uma leitura revisável, não um fato.",
            provisional,
        )

    def _model_available(self) -> bool:
        if self._expression_model is not None:
            return True
        if self._default_model is None:
            return False
        now = time.monotonic()
        if now - self._probe_at < self.MODEL_PROBE_TTL:
            return self._probe_available
        self._probe_at = now
        try:
            import requests
            self._probe_available = requests.get(self._model_host, timeout=0.35).status_code == 200
        except requests.RequestException:
            self._probe_available = False
        return self._probe_available

    @staticmethod
    def _strip_model_reasoning(text: str) -> str:
        value = re.sub(r"<think>.*?</think>", "", str(text or ""), flags=re.I | re.S)
        value = re.sub(r"^\s*(?:resposta final|resposta|output)\s*:\s*", "", value, flags=re.I)
        return _clean(value.strip().strip('"').strip())

    def _expression_packet(self, user_text: str, semantic_anchor: str, *, intent: str | None, position: dict | None, turn_context: dict | None, provisional: dict | None) -> dict:
        position = deepcopy(position or {})
        person_context = deepcopy((turn_context or {}).get("person_context") or self._person_context())
        memories = [_clip(item.get("content"), 220) for item in person_context.get("memories", ())[:4]]
        perception = [
            {
                "modality": item.get("modality") or item.get("modalities"),
                "content": _clip(item.get("content") or item.get("summary"), 220),
                "confidence": item.get("confidence"),
            }
            for item in (turn_context or {}).get("perception", ())[:4]
            if isinstance(item, dict)
        ]
        recent = [
            {"user": _clip(item.get("user"), 220), "star": _clip(item.get("star"), 260), "topic": _clip(item.get("topic"), 120)}
            for item in list(self.history)[-5:]
        ]
        cognitive_keys = (
            "perceived_intent", "subject", "confidence", "uncertainties", "needs",
            "disagreement", "decision", "tone", "initiative", "star_opinion", "user_position",
        )
        return {
            "user_message": _clip(user_text, 600),
            "semantic_answer": _clip(semantic_anchor, 1200),
            "intent": intent,
            "active_topic": self.active_topic,
            "reference_target": (turn_context or {}).get("reference_target"),
            "person": {
                "id": self.active_person_id,
                "name": self.active_person_name,
                "relationship": (turn_context or {}).get("relationship"),
                "relevant_memories": memories,
            },
            "affective_state": deepcopy((turn_context or {}).get("affect") or self.personality.current_state()),
            "cognitive_position": {key: deepcopy(position.get(key)) for key in cognitive_keys if position.get(key) is not None},
            "provisional_opinion": deepcopy(provisional),
            "perception_evidence": perception,
            "recent_turns": recent,
        }

    @staticmethod
    def _expression_system_prompt() -> str:
        return (
            "Você é SOMENTE a camada de expressão linguística da STAR. A arquitetura da STAR já decidiu o conteúdo. "
            "Reescreva a resposta semântica em português brasileiro de forma natural, fluida e espontânea, ajustando proximidade ao relacionamento informado. "
            "Preserve fatos, incertezas, limites, posição/opinião e intenção. Não acrescente fatos, percepção, memória, acesso, ação executada, autenticação, "
            "emoções humanas, consciência ou experiência subjetiva. Não copie a opinião do usuário como se fosse da STAR. "
            "Use o estado afetivo apenas para ritmo, calor, curiosidade, cautela e energia. Quando faltar contexto, faça no máximo uma pergunta útil. "
            "Evite linguagem de assistente, menus e frases engessadas. Não mostre raciocínio interno. Retorne apenas a fala final da STAR."
        )

    def _generate_natural(self, packet: dict) -> str | None:
        if not self._model_available():
            return None
        try:
            model = self._expression_model or self._default_model
            generated = model.generate(
                json.dumps(packet, ensure_ascii=False, separators=(",", ":")),
                context=self._expression_system_prompt(),
                timeout=self._model_timeout,
            )
            cleaned = self._strip_model_reasoning(generated)
        except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
            self._last_generation_error = f"{type(exc).__name__}: {_clip(exc, 180)}"
            if self._expression_model is None:
                self._probe_available = False
                self._probe_at = time.monotonic()
            return None
        if not cleaned or len(cleaned) > self.MAX_MODEL_OUTPUT:
            return None
        return cleaned

    @classmethod
    def _preserves_uncertainty(cls, anchor: str, generated: str) -> bool:
        anchor_norm = _norm(anchor)
        if not any(_norm(marker) in anchor_norm for marker in cls.UNCERTAINTY_MARKERS):
            return True
        generated_norm = _norm(generated)
        return any(_norm(marker) in generated_norm for marker in cls.UNCERTAINTY_MARKERS)

    def _should_generate(self, user_text: str, *, intent: str | None, position: dict | None, response_source: str | None) -> bool:
        if self._known_operational_command(user_text):
            return False
        if intent == "conversation":
            return True
        perceived = (position or {}).get("perceived_intent")
        if perceived in {"request_opinion", "share_opinion", "decision_support", "information_or_conversation"}:
            return True
        return response_source in {"cognitive_expression", "bounded_fallback", "unknown_fallback"}

    def _continuity_anchor(self) -> str:
        recent = list(self.history)[-self.PERSIST_EVERY_TURNS:]
        snippets = [_clip(item.get("user"), 120) for item in recent if _clean(item.get("user"))]
        topics = []
        for item in recent:
            topic = _clean(item.get("topic"))
            if topic and topic not in topics:
                topics.append(topic)
        parts = [f"Sessão de conversa {self.session_id}"]
        if self.active_person_name:
            parts.append(f"pessoa declarada={self.active_person_name}")
        if topics:
            parts.append("tópicos=" + ", ".join(topics[:5]))
        if snippets:
            parts.append("falas recentes do usuário=" + " | ".join(snippets[-4:]))
        return "; ".join(parts)

    def _persist_continuity_if_needed(self) -> None:
        if self.turn_index - self.last_persisted_turn < self.PERSIST_EVERY_TURNS or len(self.history) < 4:
            return
        content = self._continuity_anchor()
        reference = f"dialogue:{self.session_id}:{self.turn_index}"
        try:
            if self.active_person_id and self.people is not None:
                self.people.remember_interaction(
                    self.active_person_id,
                    content,
                    source="NaturalInteraction",
                    reference=reference,
                    context={"active_topic": self.active_topic, "session_id": self.session_id},
                    importance=0.55,
                )
            else:
                self.memory.remember(
                    "conversation",
                    content,
                    source="NaturalInteraction",
                    reference=reference,
                    context={"active_topic": self.active_topic, "session_id": self.session_id},
                    importance=0.5,
                    metadata={"summary_kind": "bounded_dialogue_anchor", "raw_transcript": False},
                )
            self.last_persisted_turn = self.turn_index
        except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError):
            return

    def finish_turn(self, user_text: str, response: str, *, intent: str | None = None, cognitive_position: dict | None = None, response_source: str | None = None, turn_context: dict | None = None) -> str:
        response = _clean(response)
        position = deepcopy(cognitive_position or {}) or None
        if position and _clean(position.get("subject")):
            self.active_topic = _clean(position.get("subject"))
        elif (turn_context or {}).get("reference_target"):
            self.active_topic = _clean((turn_context or {}).get("reference_target"))

        final, provisional = self._semantic_anchor(response, position)
        if self._should_generate(user_text, intent=intent, position=position, response_source=response_source):
            packet = self._expression_packet(
                user_text,
                final,
                intent=intent,
                position=position,
                turn_context=turn_context,
                provisional=provisional,
            )
            generated = self._generate_natural(packet)
            if generated and self._preserves_uncertainty(final, generated):
                final = generated
                self._last_expression_mode = "local-llm-expression"
            else:
                self._last_expression_mode = "semantic-fallback"
        else:
            self._last_expression_mode = "verbatim-operational-or-factual"

        self.history.append({
            "turn": self.turn_index,
            "user": _clip(user_text, 700),
            "star": _clip(final, 900),
            "topic": self.active_topic,
            "person_id": self.active_person_id,
            "intent": intent,
            "response_source": response_source,
            "timestamp": _now(),
        })
        self.memory.working.add(
            final or "resposta vazia",
            key=f"natural_dialogue:star:{self.turn_index}",
            importance=0.55,
            context={
                "session_id": self.session_id,
                "turn": self.turn_index,
                "active_topic": self.active_topic,
                "active_person_id": self.active_person_id,
            },
            source="NaturalInteraction",
            metadata={"persistent": False, "role": "star", "expression_mode": self._last_expression_mode},
        )
        if self.active_person_id:
            familiarity = min(0.95, 0.45 + min(self.turn_index, 10) * 0.035)
            self.personality.update_session_affect(familiarity=familiarity, context="conversation")
        self._persist_continuity_if_needed()
        return final

    def stats(self) -> dict:
        return {
            "status": "active-integrated",
            "session_id": self.session_id,
            "turns_buffered": len(self.history),
            "turn_buffer_limit": self.history.maxlen,
            "active_topic": self.active_topic,
            "active_person_id": self.active_person_id,
            "local_llm_enabled": self._model_enabled,
            "local_llm_loopback_only": True,
            "local_llm_host_allowed": self._local_host_allowed,
            "local_llm_model": self._model_name,
            "local_llm_timeout_seconds": self._model_timeout,
            "model_probe_cached_available": self._probe_available,
            "expression_mode": self._last_expression_mode,
            "last_generation_error": self._last_generation_error,
            "model_is_star": False,
            "model_decides_facts": False,
            "model_grants_permissions": False,
            "persistent_transcript_each_turn": False,
            "continuity_anchor_every_turns": self.PERSIST_EVERY_TURNS,
        }
