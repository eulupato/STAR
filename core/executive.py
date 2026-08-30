class Executive:
    """Executivo V1.6: offline por padrão; nunca chama IA quando desativada."""
    def __init__(self, model_manager=None, internal_knowledge=None):
        self.model_manager=model_manager
        self.internal_knowledge=internal_knowledge
    def execute(self, request, route):
        text=request.get("input", "")
        if self.internal_knowledge:
            answer=self.internal_knowledge.answer(text)
            if answer: return answer
        words=str(text).strip().split()
        if len(words) <= 2:
            return "Entendi a palavra, mas ainda não sei o que você quer descobrir sobre ela. 😊 Pode me fazer uma pergunta ou me dar um pouco mais de contexto?"
        return ("Ainda não tenho uma resposta confiável para isso na minha base local. Prefiro ser sincera a inventar algo. 😊 "
                "Se você quiser, esse conhecimento pode entrar em um Knowledge Pack quando ampliarmos minha biblioteca.")
