import time


class StarCore:
    """Núcleo central da STAR com MIND V2 e fallback compatível com V1.9."""

    def __init__(
        self,
        router,
        executive,
        state,
        identity=None,
        internal_knowledge=None,
        mind=None,
    ):
        self.router = router
        self.executive = executive
        self.state = state
        self.identity = identity
        self.internal_knowledge = internal_knowledge
        self.mind = mind
        self.tools = None
        self.skills = None
        self.packs = None
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

    def _try_computer(self, user_input, _context=None):
        try:
            from modules.computer_control import parse as parse_computer

            return parse_computer(
                user_input,
                allow_network=self.network_enabled,
            )
        except Exception as exc:
            print(f"⚠️ Ação local indisponível: {exc}")
            return None

    def _try_math(self, user_input, _context=None):
        try:
            from core.math_engine import solve_text

            solved = solve_text(user_input)
            if solved:
                expr, value = solved
                return f"🧠✨ {expr} = {value}"
        except Exception:
            pass
        return None

    def _context_recall(self, user_input, _context=None):
        if self.mind is None:
            return None
        return self.mind.context.local_response(
            user_input,
            self.mind.working_memory,
        )

    def _legacy_response(self, user_input, _context=None):
        request_start = time.perf_counter()
        request = {
            "input": str(user_input or "").strip(),
            "identity": self._get_identity(),
            "state": self._get_state(),
        }

        # Compatibilidade para quando a MIND estiver desativada.
        import re

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
            normalized
            in {
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
        print(
            f"🧭 Rota: {route['response_type'] or 'local'} | "
            f"{total_time:.3f}s (router {route_time:.3f}s)"
        )
        return response

    def _process_v19(self, user_input):
        action = self._try_computer(user_input)
        if action:
            return action

        solved = self._try_math(user_input)
        if solved:
            return solved

        return self._legacy_response(user_input)

    def process(self, user_input):
        text = str(user_input or "").strip()

        if self.mind is None:
            return self._process_v19(text)

        handlers = {
            "context_recall": self._context_recall,
            "computer_control": self._try_computer,
            "math": self._try_math,
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
                print(
                    f"🧠 MIND: {trace.selected_step} | "
                    f"salience {trace.salience:.2f} | {trace.elapsed_ms:.1f}ms"
                )
            return response
        except Exception as exc:
            # A MIND nunca deve transformar uma falha cognitiva em falha total.
            print(f"⚠️ MIND V2 indisponível, usando fundação V1.9: {exc}")
            return self._process_v19(text)

    def mind_status(self):
        if self.mind is None:
            return {"version": None, "active": False}
        return self.mind.status(network_enabled=self.network_enabled)

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
