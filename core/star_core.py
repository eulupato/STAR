from datetime import datetime
import time

from core.agents import AgentManager
from core.commands import strip_wake_word
from core.conversation import ConversationEngine
from core.evolution import IntegratedEvolutionSuite
from core.language_manager import LanguageManager
from core.mind import CognitiveSuite
from core.thematic_voice import parse_thematic_voice
from core.weather import WeatherService, weather_description


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
        self.mind = CognitiveSuite()

        cultural = getattr(self.executive, "religion_magic_knowledge", None)
        mdrive_manager = getattr(self.executive, "knowledge_packs", None)
        self.evolution = IntegratedEvolutionSuite(
            self.mind,
            cultural_knowledge=cultural,
            mdrive_manager=mdrive_manager,
        )
        self.people = self.evolution.people
        self.cure = self.evolution.cure
        self.web = self.evolution.web

        self.last_intent = None
        self.user_name = None
        self._network_enabled = False
        self.weather.enabled = False

    @property
    def network_enabled(self) -> bool:
        return bool(self._network_enabled)

    @network_enabled.setter
    def network_enabled(self, value) -> None:
        """Única trava operacional de rede do Core.

        Qualquer superfície que altere ``network_enabled`` — GUI, comando ou teste —
        sincroniza também o provider meteorológico compartilhado. Outros módulos web
        continuam recebendo o flag explicitamente. Assim OFFLINE não depende de cada
        chamador lembrar de bloquear o clima separadamente.
        """
        enabled = bool(value)
        self._network_enabled = enabled
        weather = getattr(self, "weather", None)
        if weather is not None:
            weather.enabled = enabled

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

    def now_status(self, *, include_weather: bool = True) -> str:
        """Painel textual compartilhado por PC/Watch/Mobile.

        Tudo é local, exceto clima ao vivo, que só é consultado quando ONLINE já foi
        autorizado. O método não ativa rede por conta própria.
        """
        now = datetime.now()
        try:
            cure = self.cure.stats()
        except Exception:
            cure = {}
        try:
            people = self.people.stats()
        except Exception:
            people = {"people": 0}
        try:
            mdrive_stats = self.mdrives.stats() if getattr(self, "mdrives", None) is not None else {}
        except Exception:
            mdrive_stats = {}
        lines = [
            f"🕒 {now.strftime('%H:%M')} • {now.strftime('%d/%m/%Y')}",
            f"🌍 {self.language.display()}",
            "🌐 ONLINE autorizado" if self.network_enabled else "🔒 OFFLINE",
            f"🩹 Cura: {'known-good ativo' if cure.get('known_good') else 'sem baseline'}",
            f"👥 People: {people.get('people', 0)} perfil(is)",
            f"💾 M.drives: {mdrive_stats.get('mdrives', mdrive_stats.get('drives', 0))}",
        ]
        if include_weather:
            if not self.network_enabled:
                lines.append("☁ Clima ao vivo: offline — nenhuma rede foi acionada.")
            else:
                snapshot = self.weather.current()
                if snapshot is None:
                    lines.append("☁ Clima: indisponível agora.")
                else:
                    lines.append(
                        f"☁ {snapshot.location}: {snapshot.temperature_c:.0f} °C, "
                        f"{weather_description(snapshot.weather_code)}, umidade {snapshot.humidity_pct}%"
                    )
        return "STAR • AGORA\n" + "\n".join(lines)

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
        normalized_early = " ".join(str(user_input or "").casefold().strip().split())

        if normalized_early in {"modo online", "ativar internet", "ativar modo online", "ficar online", "internet on"}:
            self.network_enabled = True
            return "🌐 Modo ONLINE ativado. A internet será usada apenas por capacidades que declaram necessidade de rede."
        if normalized_early in {"modo offline", "desativar internet", "desativar modo online", "ficar offline", "internet off"}:
            self.network_enabled = False
            return "🔒 Modo OFFLINE ativado. A STAR continuará usando somente recursos e conhecimento locais."
        if normalized_early in {"status internet", "status online", "rede"}:
            return "🌐 ONLINE autorizado." if self.network_enabled else "🔒 OFFLINE — rede externa desativada."
        if normalized_early in {"agora", "status agora", "painel agora", "star agora"}:
            return self.now_status(include_weather=True)

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
            evolution_action = self.evolution.handle(
                user_input,
                network_enabled=self.network_enabled,
                allow_actions=allow_actions,
            )
            if evolution_action:
                self.last_intent = "evolution"
                return evolution_action
        except (ImportError, OSError, RuntimeError, ValueError, TimeoutError) as exc:
            print(f"⚠️ STAR Evolution não concluiu a operação: {exc}")

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
            normalized in {"qual e o significado", "qual é o significado", "e o significado", "o significado"}
            and self.last_intent in {"meaning", "full_name", "name"}
        ):
            return self.internal_knowledge.answer("o que significa star")
        if normalized in {"qual meu nome", "qual e meu nome", "qual é meu nome"} and self.user_name:
            return f"Você me disse que seu nome é {self.user_name}. ⭐"

        conversation_response = self.conversation.respond(request["input"], user_name=self.user_name)
        if conversation_response:
            self.last_intent = "conversation"
            return conversation_response

        route_start = time.perf_counter()
        route = self.router.route(request)
        self.last_intent = route.get("response_type")
        route_time = time.perf_counter() - route_start
        response = self.executive.execute(request=request, route=route)

        unknown = str(response).startswith("Ainda não tenho uma resposta confiável")
        if unknown:
            try:
                learned = self.web.answer(request["input"], network_enabled=self.network_enabled, auto_learn=True)
                if learned:
                    response = learned
                    self.last_intent = "web_knowledge" if self.network_enabled else "learned_local_cache"
            except (OSError, RuntimeError, ValueError, TimeoutError) as exc:
                print(f"⚠️ Web Knowledge indisponível: {exc}")

        total_time = time.perf_counter() - request_start
        print(f"🧭 Rota: {route['response_type'] or 'local'} | {total_time:.3f}s (router {route_time:.3f}s)")
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
