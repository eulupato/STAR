import time

from core.agents import AgentManager
from core.commands import strip_wake_word
from core.conversation import ConversationEngine
from core.language_manager import LanguageManager
from core.mind import CognitiveSuite
from core.thematic_voice import parse_thematic_voice
from core.weather import WeatherService


class StarCore:
    """Núcleo central da STAR: identidade, estado, roteamento e execução."""

    def __init__(self, router, executive, state, identity=None, internal_knowledge=None):
        self.router = router
        self.executive = executive
        self.state = state
        self.identity = identity
        self.internal_knowledge = internal_knowledge
        self.tools = None
        self.skills = None
        self.packs = None

        self.weather = WeatherService()
        self.conversation = ConversationEngine(self.weather)
        self.agents = AgentManager(weather_provider=self.weather)
        self.language = LanguageManager()

        # STAR MIND V2 alpha. Usa o mesmo SQLite oficial e só intercepta pedidos
        # cognitivos explícitos, preservando o roteamento estável da Foundation.
        self.mind = CognitiveSuite()

        self.last_intent = None
        self.user_name = None
        self.network_enabled = False

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

    def process(self, user_input, allow_actions=True):
        raw_input = str(user_input or "")
        language_action = self.language.handle_command(strip_wake_word(raw_input))
        if language_action:
            return language_action

        canonical_input = self.language.translate_to_portuguese(raw_input)
        response = self._process_portuguese(canonical_input, allow_actions=allow_actions)
        return self.language.translate_response(str(response))

    def _process_portuguese(self, user_input, allow_actions=True):
        request_start = time.perf_counter()

        thematic = parse_thematic_voice(user_input)
        if thematic:
            user_input = f"{thematic.action} {thematic.query}".strip()

        try:
            from modules.vision import handle_vision_command

            vision_action = handle_vision_command(user_input, allow_actions=allow_actions)
            if vision_action:
                self.last_intent = "vision"
                return vision_action
        except (ImportError, OSError, RuntimeError, ValueError) as exc:
            print(f"⚠️ STAR Vision indisponível: {exc}")

        try:
            mind_action = self.mind.handle(user_input, network_enabled=self.network_enabled)
            if mind_action:
                self.last_intent = "mind"
                return mind_action
        except (ImportError, OSError, RuntimeError, ValueError, TimeoutError) as exc:
            print(f"⚠️ STAR MIND não concluiu a operação: {exc}")

        try:
            action = self.agents.dispatch(
                user_input,
                network_enabled=self.network_enabled,
                remote=not allow_actions,
            )
            if action:
                return action
        except (ImportError, OSError, RuntimeError, ValueError) as exc:
            print(f"⚠️ Comando indisponível: {exc}")

        try:
            from core.math_engine import solve_text

            solved = solve_text(user_input)
            if solved:
                expr, value = solved
                return f"🧠✨ {expr} = {value}"
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as exc:
            print(f"⚠️ Expressão matemática não resolvida: {exc}")

        request = {
            "input": str(user_input or "").strip(),
            "identity": self._get_identity(),
            "state": self._get_state(),
        }

        import re

        name_match = re.search(
            r"\bmeu nome (?:e|é)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,40})",
            request["input"],
            re.I,
        )
        if name_match:
            self.user_name = name_match.group(1).strip().split()[0]
            return f"Prazer, {self.user_name}! ⭐ Agora vou me lembrar do seu nome durante esta sessão."

        normalized = request["input"].strip().lower()
        if (
            normalized
            in {"qual e o significado", "qual é o significado", "e o significado", "o significado"}
            and self.last_intent in {"meaning", "full_name", "name"}
        ):
            return self.internal_knowledge.answer("o que significa star")
        if normalized in {"qual meu nome", "qual e meu nome", "qual é meu nome"} and self.user_name:
            return f"Você me disse que seu nome é {self.user_name}. ⭐"

        conversation_response = self.conversation.respond(
            request["input"],
            user_name=self.user_name,
        )
        if conversation_response:
            self.last_intent = "conversation"
            return conversation_response

        route_start = time.perf_counter()
        route = self.router.route(request)
        self.last_intent = route.get("response_type")
        route_time = time.perf_counter() - route_start
        response = self.executive.execute(request=request, route=route)
        total_time = time.perf_counter() - request_start

        print(
            f"🧭 Rota: {route['response_type'] or 'local'} | "
            f"{total_time:.3f}s (router {route_time:.3f}s)"
        )
        return response

    def _get_identity(self):
        if self.identity is None:
            return {}
        try:
            return self.identity.get()
        except AttributeError:
            try:
                return self.identity.data
            except AttributeError:
                return {}

    def _get_state(self):
        if self.state is None:
            return {}
        try:
            return self.state.get_state()
        except AttributeError:
            return getattr(self.state, "data", self.state)
