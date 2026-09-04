import time


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
        request_start = time.perf_counter()

        # A interface local mantém as ações existentes. Endpoints remotos podem
        # chamar process(..., allow_actions=False) enquanto o Permission Manager
        # completo ainda não existe.
        if allow_actions:
            try:
                from modules.computer_control import parse as parse_computer
                action = parse_computer(user_input, allow_network=self.network_enabled)
                if action:
                    return action
            except Exception as exc:
                print(f"⚠️ Ação local indisponível: {exc}")

        try:
            from core.math_engine import solve_text
            solved = solve_text(user_input)
            if solved:
                expr, value = solved
                return f"🧠✨ {expr} = {value}"
        except Exception:
            pass
        request = {
            "input": str(user_input or "").strip(),
            "identity": self._get_identity(),
            "state": self._get_state(),
        }

        # Pequena memória de sessão para fatos simples e continuidade imediata.
        import re
        name_match = re.search(r"\bmeu nome (?:e|é)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,40})", request["input"], re.I)
        if name_match:
            self.user_name = name_match.group(1).strip().split()[0]
            return f"Prazer, {self.user_name}! ⭐ Agora vou me lembrar do seu nome durante esta sessão."
        normalized = request["input"].strip().lower()
        if normalized in {"qual e o significado", "qual é o significado", "e o significado", "o significado"} and self.last_intent in {"meaning", "full_name", "name"}:
            return self.internal_knowledge.answer("o que significa star")
        if normalized in {"qual meu nome", "qual e meu nome", "qual é meu nome"} and self.user_name:
            return f"Você me disse que seu nome é {self.user_name}. ⭐"
        route_start = time.perf_counter()
        route = self.router.route(request)
        self.last_intent = route.get("response_type")
        route_time = time.perf_counter() - route_start
        # A matemática já foi tratada pelo math_engine no início do pipeline.
        # Evitamos manter dois interpretadores matemáticos concorrentes.
        response = self.executive.execute(request=request, route=route)
        total_time = time.perf_counter() - request_start

        # Diagnóstico curto para o terminal, sem poluir a GUI.
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
