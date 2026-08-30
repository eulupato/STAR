class Memory:

    def __init__(self):
        self.conversation = []

    # =========================================================
    # ADICIONAR UMA MENSAGEM
    # =========================================================

    def add_message(self, role, message):

        self.conversation.append({
            "role": role,
            "message": message
        })

    # =========================================================
    # HISTÓRICO COMPLETO
    # =========================================================

    def get_history(self):

        return self.conversation.copy()

    # =========================================================
    # ÚLTIMA MENSAGEM
    # =========================================================

    def get_last_message(self):

        if not self.conversation:
            return None

        return self.conversation[-1]

    # =========================================================
    # LIMPAR CONVERSA
    # =========================================================

    def clear(self):

        self.conversation.clear()

    # =========================================================
    # QUANTIDADE DE MENSAGENS
    # =========================================================

    def count(self):

        return len(self.conversation)