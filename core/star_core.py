import time

from core.agents import AgentManager
from core.commands import strip_wake_word
from core.conversation import ConversationEngine
from core.everyday_technology import EverydayTechnologyFoundations
from core.foundations import FoundationSuite
from core.human_contexts import HumanContextFoundations
from core.human_life import HumanLifeFoundations
from core.human_psychology import HumanPsychologyFoundations
from core.language_communication import LanguageCommunicationFoundations
from core.language_manager import LanguageManager
from core.mind import CognitiveSuite
from core.physical_world import PhysicalWorldModel
from core.scientific_foundations import ScientificFoundations
from core.society_culture import SocietyCultureFoundations
from core.thematic_voice import parse_thematic_voice
from core.universal_knowledge import UniversalKnowledgeArchitecture
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

        # BLOCO 1: fundamentos centrais reutilizáveis. A suíte usa a identidade
        # oficial existente e não cria uma STAR paralela.
        self.foundations = FoundationSuite(identity=self.identity)

        # STAR MIND V2 alpha. Usa o mesmo SQLite oficial e só intercepta pedidos
        # cognitivos explícitos, preservando o roteamento estável da Foundation.
        self.mind = CognitiveSuite()

        # BLOCO 3: organiza conhecimento canônico sobre o ledger epistêmico e o
        # Knowledge Graph já existentes. Não cria outro banco, outro grafo ou
        # outra identidade. A referência também fica exposta na MIND para reuso.
        self.knowledge = UniversalKnowledgeArchitecture(
            self.mind.epistemics,
            self.mind.graph,
        )
        self.mind.knowledge = self.knowledge

        # BLOCO 4: world model físico compartilhado. Conhecimento canônico usa
        # BLOCO 3/B02; objetos de cena são transitórios e não viram fatos por
        # simples observação. A base científica de Física existente é reutilizada.
        self.physical_world = PhysicalWorldModel(self.knowledge)
        self.mind.physical_world = self.physical_world

        # BLOCO 5: fundamentos científicos sobre o mesmo conhecimento universal,
        # ledger epistêmico e Knowledge Graph. Reutiliza o ScientificReasoner e
        # os provedores locais existentes em vez de criar outro Scientific Engine.
        self.scientific_foundations = ScientificFoundations(
            self.knowledge,
            reasoner=self.mind.science,
        )
        self.mind.scientific_foundations = self.scientific_foundations

        # BLOCO 6: vida, corpo e necessidades humanas como especialização da
        # ciência existente. Usa o mesmo B02/B03/Knowledge Graph e nunca converte
        # sinais, necessidades ou conhecimento geral em diagnóstico automático.
        self.human_life = HumanLifeFoundations(
            self.knowledge,
            scientific_foundations=self.scientific_foundations,
        )
        self.mind.human_life = self.human_life

        # BLOCO 7: mente humana e psicologia como camada interpretativa geral.
        # Compartilha B02/B03/Knowledge Graph e a base biológica do B06, sem
        # diagnóstico, perfil psicológico ou leitura de intenção automática.
        self.human_psychology = HumanPsychologyFoundations(
            self.knowledge,
            human_life=self.human_life,
        )
        self.mind.human_psychology = self.human_psychology

        # BLOCO 8: conhecimento de linguagem e comunicação. Reutiliza o mesmo
        # LanguageManager operacional e o mesmo B02/B03/Knowledge Graph; conhecer
        # um idioma não implica que seu locale/tradutor operacional esteja pronto.
        self.language_communication = LanguageCommunicationFoundations(
            self.knowledge,
            language_manager=self.language,
            human_psychology=self.human_psychology,
        )
        self.mind.language_communication = self.language_communication

        # BLOCO 9: sociedade e cultura. Integra História, Geografia, Sociologia e
        # Filosofia já existentes como referências e amplia a taxonomia social
        # sobre o mesmo B02/B03/Knowledge Graph, sem banco ou grafo paralelo.
        self.society_culture = SocietyCultureFoundations(
            self.knowledge,
            human_psychology=self.human_psychology,
            language_communication=self.language_communication,
        )
        self.mind.society_culture = self.society_culture

        # BLOCO 10: contexto humano situado. Reusa B06-B09 e cruza pessoa, idade,
        # ambiente, relação, necessidade, risco, norma, cultura e contexto sem
        # converter idade/deficiência/papel em capacidade ou autorização automática.
        self.human_contexts = HumanContextFoundations(
            self.knowledge,
            human_life=self.human_life,
            human_psychology=self.human_psychology,
            language_communication=self.language_communication,
            society_culture=self.society_culture,
        )
        self.mind.human_contexts = self.human_contexts

        # BLOCO 11: mundo cotidiano e tecnológico. Relaciona objetos, sistemas,
        # funções, usos, riscos, estados e contextos sobre B04/B05/B10 e as bases
        # multidisciplinares existentes, sem criar outro motor técnico ou banco.
        self.everyday_technology = EverydayTechnologyFoundations(
            self.knowledge,
            physical_world=self.physical_world,
            scientific_foundations=self.scientific_foundations,
            human_contexts=self.human_contexts,
        )
        self.mind.everyday_technology = self.everyday_technology

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

        foundation_action = self.foundations.handle(user_input)
        if foundation_action:
            self.last_intent = "foundations"
            return foundation_action

        physical_action = self.physical_world.handle(user_input)
        if physical_action:
            self.last_intent = "physical_world"
            return physical_action

        scientific_action = self.scientific_foundations.handle(user_input)
        if scientific_action:
            self.last_intent = "scientific_foundations"
            return scientific_action

        human_life_action = self.human_life.handle(user_input)
        if human_life_action:
            self.last_intent = "human_life"
            return human_life_action

        psychology_action = self.human_psychology.handle(user_input)
        if psychology_action:
            self.last_intent = "human_psychology"
            return psychology_action

        language_communication_action = self.language_communication.handle(user_input)
        if language_communication_action:
            self.last_intent = "language_communication"
            return language_communication_action

        society_culture_action = self.society_culture.handle(user_input)
        if society_culture_action:
            self.last_intent = "society_culture"
            return society_culture_action

        human_context_action = self.human_contexts.handle(user_input)
        if human_context_action:
            self.last_intent = "human_contexts"
            return human_context_action

        everyday_technology_action = self.everyday_technology.handle(user_input)
        if everyday_technology_action:
            self.last_intent = "everyday_technology"
            return everyday_technology_action

        knowledge_action = self.knowledge.handle(user_input)
        if knowledge_action:
            self.last_intent = "universal_knowledge"
            return knowledge_action

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