from time import perf_counter


class Executive:
    """Executivo V1.9: conhecimento local primeiro; IA externa permanece opcional."""

    def __init__(
        self,
        model_manager=None,
        internal_knowledge=None,
        knowledge_packs=None,
        physics_knowledge=None,
        chemistry_knowledge=None,
        multidisciplinary_knowledge=None,
        knowledge_expansion=None,
        curriculum_knowledge=None,
        cognitive_integration=None,
    ):
        self.model_manager = model_manager
        self.internal_knowledge = internal_knowledge
        self.knowledge_packs = knowledge_packs
        self.physics_knowledge = physics_knowledge
        self.chemistry_knowledge = chemistry_knowledge
        self.multidisciplinary_knowledge = multidisciplinary_knowledge
        self.knowledge_expansion = knowledge_expansion
        self.curriculum_knowledge = curriculum_knowledge
        self.cognitive_integration = cognitive_integration
        self.last_cognitive_position = None

    def execute(self, request, route):
        text = request.get("input", "")
        response_started = perf_counter()
        position = None

        if self.cognitive_integration is not None:
            position = self.cognitive_integration.build_position(request, route)
            request["cognitive_position"] = position
            self.last_cognitive_position = position
            cognitive_expression = self.cognitive_integration.expression(position)
            if cognitive_expression:
                return self._finish(
                    cognitive_expression,
                    position,
                    response_started,
                    source="cognitive_expression",
                )

        if self.internal_knowledge:
            answer = self.internal_knowledge.answer(text)
            if answer:
                return self._finish(answer, position, response_started, source="internal_knowledge")

        # Quando a própria consulta pede profundidade/pesquisa/benchmark/dados,
        # a camada PLUS pode responder antes. Isso preserva o comportamento já
        # validado e não altera IDs nem remove as bases legadas.
        if self.knowledge_expansion and self.knowledge_expansion.prefers(text):
            answer = self.knowledge_expansion.answer(text)
            if answer:
                return self._finish(answer, position, response_started, source="knowledge_expansion")

        # Física e Química permanecem antes dos catálogos amplos. O currículo
        # contém muitos termos genéricos (energia, campo, pressão, memória etc.)
        # e não deve engolir rotas científicas que já são mais específicas.
        if self.physics_knowledge:
            answer = self.physics_knowledge.answer(text)
            if answer:
                return self._finish(answer, position, response_started, source="physics_knowledge")

        if self.chemistry_knowledge:
            answer = self.chemistry_knowledge.answer(text)
            if answer:
                return self._finish(answer, position, response_started, source="chemistry_knowledge")

        if self.multidisciplinary_knowledge:
            answer = self.multidisciplinary_knowledge.answer(text)
            if answer:
                return self._finish(answer, position, response_started, source="multidisciplinary_knowledge")

        # Camada curricular granular: cobre os novos subtemas e relações quando
        # as fontes estáveis anteriores não possuem uma resposta mais adequada.
        if self.curriculum_knowledge:
            answer = self.curriculum_knowledge.answer(text)
            if answer:
                return self._finish(answer, position, response_started, source="curriculum_knowledge")

        # Fallback PLUS: tópicos novos e específicos que não existem nas bases
        # anteriores ainda podem ser resolvidos sem exigir a palavra "avançado".
        if self.knowledge_expansion:
            answer = self.knowledge_expansion.answer(text)
            if answer:
                return self._finish(answer, position, response_started, source="knowledge_expansion_fallback")

        if self.knowledge_packs:
            answer = self.knowledge_packs.answer(text)
            if answer:
                return self._finish(answer, position, response_started, source="knowledge_pack")

        words = str(text).strip().split()
        if len(words) <= 2:
            return self._finish(
                "Entendi a palavra, mas ainda não sei o que você quer descobrir sobre ela. 😊 "
                "Pode me fazer uma pergunta ou me dar um pouco mais de contexto?",
                position,
                response_started,
                source="bounded_fallback",
            )

        return self._finish(
            "Ainda não tenho uma resposta confiável para isso na minha base local. "
            "Prefiro ser sincera a inventar algo. 😊 Se você quiser, esse conhecimento "
            "pode entrar em um Knowledge Pack quando ampliarmos minha biblioteca.",
            position,
            response_started,
            source="unknown_fallback",
        )

    @staticmethod
    def _finish(answer, position, started, *, source):
        if position is not None:
            timings = position.setdefault("timings_ms", {})
            timings["response_generation"] = round((perf_counter() - started) * 1000, 3)
            position["response_source"] = source
        return answer
