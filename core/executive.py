class Executive:
    """Executivo V1.9: conhecimento local primeiro; IA externa permanece opcional."""

    def __init__(self, model_manager=None, internal_knowledge=None, knowledge_packs=None):
        self.model_manager = model_manager
        self.internal_knowledge = internal_knowledge
        self.knowledge_packs = knowledge_packs

    def execute(self, request, route):
        text = request.get("input", "")

        if self.internal_knowledge:
            answer = self.internal_knowledge.answer(text)
            if answer:
                return answer

        if self.knowledge_packs:
            answer = self.knowledge_packs.answer(text)
            if answer:
                return answer

        words = str(text).strip().split()
        if len(words) <= 2:
            return (
                "Entendi a palavra, mas ainda não sei o que você quer descobrir sobre ela. 😊 "
                "Pode me fazer uma pergunta ou me dar um pouco mais de contexto?"
            )

        return (
            "Ainda não tenho uma resposta confiável para isso na minha base local. "
            "Prefiro ser sincera a inventar algo. 😊 Se você quiser, esse conhecimento "
            "pode entrar em um Knowledge Pack quando ampliarmos minha biblioteca."
        )
