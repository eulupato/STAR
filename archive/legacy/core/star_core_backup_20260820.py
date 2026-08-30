import time

from core.star_identity import StarIdentity


class StarCore:
    """
    STAR CORE

    Camada superior da arquitetura STAR.

    Responsável por preservar:
    - identidade;
    - princípios;
    - contexto;
    - autoridade;
    - estado;
    - regras fundamentais.

    IMPORTANTE:

    O StarCore representa a entidade STAR.

    Modelos de IA são recursos utilizados pela STAR
    para processamento cognitivo.

    O modelo não define a identidade da STAR.
    """

    def __init__(
        self,
        router,
        executive,
        state,
    ):

        self.router = router
        self.executive = executive
        self.state = state

        self.name = "STAR"
        self.version = "2.2.0"

        # =====================================================
        # IDENTIDADE FUNDAMENTAL
        # =====================================================

        self.identity = StarIdentity()

    # =========================================================
    # IDENTIDADE
    # =========================================================

    def get_identity(self):
        """
        Retorna a identidade fundamental da STAR.
        """

        return self.identity.get()

    def get_name(self):
        """
        Retorna o nome da entidade.
        """

        return self.identity.get_name()

    def get_creator(self):
        """
        Retorna o criador da STAR.
        """

        return self.identity.get_creator()

    # =========================================================
    # ESTADO
    # =========================================================

    def get_state(self):
        """
        Retorna o estado computacional atual da STAR.
        """

        return self.state.get_state()

    # =========================================================
    # PROCESSAMENTO
    # =========================================================

    def process(self, user_input):

        if not user_input:
            return ""

        total_start = time.perf_counter()

        # =====================================================
        # REQUEST
        # =====================================================

        request_start = time.perf_counter()

        request = {
            "input": user_input,

            # Identidade estrutural da STAR
            "identity": self.identity.get(),

            # Prompt oficial de identidade
            "identity_prompt": (
                self.identity.build_prompt()
            ),

            # Estado atual da STAR
            "state": self.state.get_state(),

            # Criador
            "creator": (
                self.identity.get_creator()
            ),

            # Nome da entidade
            "star_name": (
                self.identity.get_name()
            ),
        }

        request_time = (
            time.perf_counter()
            - request_start
        )

        # =====================================================
        # ROUTER
        # =====================================================

        router_start = time.perf_counter()

        route = self.router.route(request)

        router_time = (
            time.perf_counter()
            - router_start
        )

        print(
            f"\n🧭 ROTA STAR: {route}"
        )

        # =====================================================
        # EXECUTIVO
        # =====================================================

        executive_start = time.perf_counter()

        result = self.executive.execute(
            request=request,
            route=route,
        )

        executive_time = (
            time.perf_counter()
            - executive_start
        )

        # =====================================================
        # DIAGNÓSTICO
        # =====================================================

        total_time = (
            time.perf_counter()
            - total_start
        )

        print("\n⏱️ DIAGNÓSTICO:")

        print(
            f"   Request:   {request_time:.3f}s"
        )

        print(
            f"   Router:    {router_time:.3f}s"
        )

        print(
            f"   Executivo: {executive_time:.3f}s"
        )

        print(
            f"   TOTAL:     {total_time:.3f}s"
        )

        return result