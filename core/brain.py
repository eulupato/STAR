from core.memory import Memory


class Brain:

    def __init__(self):

        self.online = False

        # =====================================================
        # MEMÓRIA
        # =====================================================

        self.memory = Memory()

        # =====================================================
        # CONTEXTO
        # =====================================================

        self.context = {
            "last_message": None,
            "last_intent": None,
            "last_response": None,
            "conversation_started": False,
            "message_count": 0,
        }

        # =====================================================
        # ESTADO
        # =====================================================

        self.state = "IDLE"

    # =========================================================
    # INICIALIZAÇÃO
    # =========================================================

    def initialize(self):

        self.online = True
        self.state = "IDLE"

        print("Cérebro STAR inicializado")

    # =========================================================
    # PROCESSAMENTO
    # =========================================================

    def process(self, message):

        if not self.online:
            return "Meu cérebro está offline."

        self.state = "THINKING"

        message = self.normalize(message)

        if not message:

            response = "Pode falar comigo. ⭐"

            self.update_context(
                message,
                "empty",
                response
            )

            self.state = "SPEAKING"

            return response

        # =====================================================
        # GUARDAR MENSAGEM DO USUÁRIO
        # =====================================================

        self.memory.add_message(
            "user",
            message
        )

        # =====================================================
        # IDENTIFICAR INTENÇÃO
        # =====================================================

        intent = self.detect_intent(message)

        # =====================================================
        # GERAR RESPOSTA
        # =====================================================

        response = self.generate_response(
            message,
            intent
        )

        # =====================================================
        # GUARDAR RESPOSTA DA STAR
        # =====================================================

        self.memory.add_message(
            "star",
            response
        )

        # =====================================================
        # ATUALIZAR CONTEXTO
        # =====================================================

        self.update_context(
            message,
            intent,
            response
        )

        self.state = "SPEAKING"

        return response

    # =========================================================
    # NORMALIZAÇÃO
    # =========================================================

    def normalize(self, message):

        if not isinstance(message, str):
            return ""

        return " ".join(
            message.strip().lower().split()
        )

    # =========================================================
    # INTENÇÃO
    # =========================================================

    def detect_intent(self, message):

        if self.is_greeting(message):
            return "greeting"

        if self.is_identity_question(message):
            return "identity"

        if self.is_wellbeing_question(message):
            return "wellbeing"

        if self.is_capabilities_question(message):
            return "capabilities"

        if self.is_goodbye(message):
            return "goodbye"

        return "unknown"

    # =========================================================
    # RESPOSTA
    # =========================================================

    def generate_response(self, message, intent):

        previous_intent = self.context["last_intent"]
        message_count = self.context["message_count"]

        if intent == "greeting":

            if message_count > 0 and previous_intent == "greeting":

                return (
                    "Oi novamente! ⭐ "
                    "Ainda estou aqui."
                )

            return (
                "Olá! ⭐ Eu sou a STAR. "
                "É um prazer falar com você!"
            )

        if intent == "identity":

            if previous_intent == "identity":

                return (
                    "Como eu estava dizendo, meu nome é STAR. ⭐ "
                    "Meu sistema significa "
                    "System for Thought, Analysis and Response."
                )

            return (
                "Eu sou a STAR — "
                "System for Thought, Analysis and Response. ⭐ "
                "Ainda estou em desenvolvimento, "
                "mas já estou pronta para conversar com você."
            )

        if intent == "wellbeing":

            return (
                "Estou bem! ⭐ "
                "Meu sistema está funcionando e estou pronta "
                "para conversar com você."
            )

        if intent == "capabilities":

            if previous_intent == "identity":

                return (
                    "Ainda estou aprendendo. ⭐ "
                    "Por enquanto consigo conversar, processar "
                    "mensagens e manter o contexto básico desta "
                    "conversa. Novas capacidades serão adicionadas "
                    "conforme meu desenvolvimento avançar."
                )

            return (
                "Ainda estou aprendendo. ⭐ "
                "No momento consigo conversar, "
                "processar algumas mensagens e utilizar minha "
                "memória básica. Novas capacidades serão "
                "adicionadas conforme meu desenvolvimento avançar."
            )

        if intent == "goodbye":

            return (
                "Até logo! ⭐ "
                "Estarei aqui quando você voltar."
            )

        if previous_intent == "greeting":

            return (
                "Entendi. ⭐ "
                "Ainda não sei responder isso, "
                "mas estou aprendendo."
            )

        return (
            "Ainda não sei responder isso. ⭐ "
            "Essa capacidade ainda está em desenvolvimento."
        )

    # =========================================================
    # CONTEXTO
    # =========================================================

    def update_context(
        self,
        message,
        intent,
        response
    ):

        self.context["last_message"] = message
        self.context["last_intent"] = intent
        self.context["last_response"] = response

        self.context["conversation_started"] = True
        self.context["message_count"] += 1

    # =========================================================
    # ACESSAR CONTEXTO
    # =========================================================

    def get_context(self):

        return self.context.copy()

    # =========================================================
    # ACESSAR MEMÓRIA
    # =========================================================

    def get_memory(self):

        return self.memory.get_history()

    # =========================================================
    # ACESSAR ESTADO
    # =========================================================

    def get_state(self):

        return self.state

    # =========================================================
    # SAUDAÇÃO
    # =========================================================

    def is_greeting(self, message):

        greetings = [
            "olá",
            "ola",
            "oi",
            "oie",
            "oiee",
            "hey",
            "hello",
            "hi",
            "bom dia",
            "boa tarde",
            "boa noite",
        ]

        return message in greetings

    # =========================================================
    # IDENTIDADE
    # =========================================================

    def is_identity_question(self, message):

        identity_phrases = [
            "quem é você",
            "quem e você",
            "quem e voce",
            "qual seu nome",
            "qual é seu nome",
            "qual e seu nome",
            "seu nome",
            "me fale sobre você",
            "me fale sobre voce",
            "fale sobre você",
            "fale sobre voce",
        ]

        return any(
            phrase in message
            for phrase in identity_phrases
        )

    # =========================================================
    # BEM-ESTAR
    # =========================================================

    def is_wellbeing_question(self, message):

        wellbeing_phrases = [
            "tudo bem",
            "como você está",
            "como voce esta",
            "como você tá",
            "como voce ta",
            "como está você",
            "como esta voce",
        ]

        return any(
            phrase in message
            for phrase in wellbeing_phrases
        )

    # =========================================================
    # CAPACIDADES
    # =========================================================

    def is_capabilities_question(self, message):

        capability_phrases = [
            "o que você sabe fazer",
            "o que voce sabe fazer",
            "o que você consegue fazer",
            "o que voce consegue fazer",
            "o que você pode fazer",
            "o que voce pode fazer",
            "quais são suas capacidades",
            "quais sao suas capacidades",
            "quais suas capacidades",
        ]

        return any(
            phrase in message
            for phrase in capability_phrases
        )

    # =========================================================
    # DESPEDIDA
    # =========================================================

    def is_goodbye(self, message):

        goodbye_phrases = [
            "tchau",
            "até logo",
            "ate logo",
            "até mais",
            "ate mais",
            "até depois",
            "ate depois",
            "falou",
            "bye",
        ]

        return message in goodbye_phrases

    # =========================================================
    # DESLIGAMENTO
    # =========================================================

    def shutdown(self):

        self.online = False
        self.state = "IDLE"

        print("Brain offline.")