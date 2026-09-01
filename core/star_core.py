"""Núcleo central da STAR: identidade, MIND, conhecimento e execução."""
from __future__ import annotations

import re
import time

from core.logging_config import get_logger

log = get_logger("core")


class StarCore:
    def __init__(
        self,
        router,
        executive,
        state,
        identity=None,
        internal_knowledge=None,
        mind=None,
        knowledge=None,
        conversation=None,
    ):
        self.router = router
        self.executive = executive
        self.state = state
        self.identity = identity
        self.internal_knowledge = internal_knowledge
        self.mind = mind
        self.knowledge = knowledge
        self.conversation = conversation
        self.tools = None
        self.skills = None
        self.packs = None
        self.last_intent = None
        self.user_name = None
        self.network_enabled = False
        self.ui_context = ""

    def get_name(self):
        if self.identity is None:
            return "STAR"
        try:
            return self.identity.get_name()
        except AttributeError:
            return getattr(self.identity, "name", "STAR")

    def get_creator(self):
        if self.identity is None:
            return "Lu"
        try:
            return self.identity.get_creator()
        except AttributeError:
            return "Lu"

    def _try_computer(self, user_input, _context=None):
        try:
            from modules.computer_control import parse as parse_computer
            return parse_computer(
                user_input,
                allow_network=self.network_enabled,
            )
        except Exception as exc:
            log.error("Ação local indisponível: %s", exc)
            return None

    def _try_math(self, user_input, _context=None):
        try:
            from core.math_engine import solve_text
            solved = solve_text(user_input)
        except Exception as exc:
            log.error("Math Engine falhou: %s", exc)
            return None
        if solved:
            expr, value = solved
            return f"🧠✨ {expr} = {value}"
        return None

    def _try_conversation(self, user_input, context=None):
        if self.conversation is None:
            return None
        try:
            return self.conversation.generate(
                user_input,
                context=context or {},
            )
        except Exception as exc:
            log.error("Conversation Engine falhou: %s", exc)
            return None

    def _context_recall(self, user_input, _context=None):
        if self.mind is None:
            return None
        return self.mind.context.local_response(
            user_input,
            self.mind.working_memory,
        )

    def _try_knowledge(self, user_input, context=None):
        if self.knowledge is None:
            return None
        context = dict(context or {})
        if self.mind is not None:
            context["resolved_text"] = self.mind.context.resolve_reference_text(
                user_input
            )
        try:
            response = self.knowledge.answer(user_input, context=context)
        except Exception as exc:
            log.error("Knowledge Engine falhou: %s", exc)
            return None

        entity = getattr(self.knowledge, "last_entity", None)
        if response and entity is not None and self.mind is not None:
            self.mind.context.track_entity(
                entity.name,
                entity_id=entity.id,
                category=entity.category,
            )
        return response

    def _legacy_response(self, user_input, _context=None):
        request_start = time.perf_counter()
        request = {
            "input": str(user_input or "").strip(),
            "identity": self._get_identity(),
            "state": self._get_state(),
            "ui_context": str(self.ui_context or "").strip(),
        }

        name_match = re.search(
            r"\bmeu nome (?:e|é)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,40})",
            request["input"],
            re.I,
        )
        if name_match:
            self.user_name = name_match.group(1).strip().split()[0]
            return (
                f"Prazer, {self.user_name}! ⭐ Agora vou me lembrar do seu "
                "nome durante esta sessão."
            )

        normalized = request["input"].strip().lower()
        if (
            normalized in {
                "qual e o significado",
                "qual é o significado",
                "e o significado",
                "o significado",
            }
            and self.last_intent in {"meaning", "full_name", "name"}
            and self.internal_knowledge is not None
        ):
            return self.internal_knowledge.answer("o que significa star")

        if (
            normalized in {"qual meu nome", "qual e meu nome", "qual é meu nome"}
            and self.user_name
        ):
            return f"Você me disse que seu nome é {self.user_name}. ⭐"

        route_start = time.perf_counter()
        route = self.router.route(request)
        self.last_intent = route.get("response_type")
        route_time = time.perf_counter() - route_start

        response = self.executive.execute(request=request, route=route)
        total_time = time.perf_counter() - request_start
        context_info = f" | contexto {request['ui_context']}" if request["ui_context"] else ""
        log.info(
            "Rota %s%s | %.3fs (router %.3fs)",
            route.get("response_type") or "local",
            context_info,
            total_time,
            route_time,
        )
        return response

    def _process_without_mind(self, user_input):
        for handler in (
            self._try_conversation,
            self._try_computer,
            self._try_math,
            self._try_knowledge,
            self._legacy_response,
        ):
            response = handler(user_input, {})
            if response:
                return response
        return "Não consegui concluir esta solicitação com as capacidades disponíveis."

    def process(self, user_input):
        text = str(user_input or "").strip()

        if self.mind is None:
            return self._process_without_mind(text)

        handlers = {
            "context_recall": self._context_recall,
            "conversation": self._try_conversation,
            "computer_control": self._try_computer,
            "math": self._try_math,
            "knowledge_search": self._try_knowledge,
            "legacy_reasoning": self._legacy_response,
        }

        try:
            response = self.mind.process(
                text=text,
                handlers=handlers,
                network_enabled=self.network_enabled,
            )
            trace = self.mind.metacognition.last
            if trace is not None:
                log.info(
                    "MIND executor=%s salience=%.2f elapsed=%.1fms",
                    trace.selected_step,
                    trace.salience,
                    trace.elapsed_ms,
                )
            return response
        except Exception as exc:
            log.exception("MIND indisponível; usando pipeline local de fallback: %s", exc)
            return self._process_without_mind(text)

    def mind_status(self):
        if self.mind is None:
            return {"generation": None, "active": False}
        return self.mind.status(network_enabled=self.network_enabled)

    def knowledge_status(self):
        if self.knowledge is None:
            return {"active": False}
        return self.knowledge.status()

    def _get_identity(self):
        if self.identity is None:
            return {}
        try:
            return self.identity.get()
        except AttributeError:
            return getattr(self.identity, "data", {})

    def _get_state(self):
        if self.state is None:
            return {}
        try:
            return self.state.get_state()
        except AttributeError:
            return getattr(self.state, "data", self.state)
