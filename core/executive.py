from time import perf_counter


class Executive:
    """Executivo V1.9: conhecimento local primeiro; IA/modelos são recursos opcionais."""

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
        offline_knowledge=None,
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
        self.offline_knowledge = offline_knowledge
        self.natural_interaction = None
        self.last_cognitive_position = None

    def execute(self, request, route):
        text = request.get("input", "")
        response_started = perf_counter()
        position = None
        turn_context = None
        cognitive_request = request

        # A camada de interação prepara somente contexto para cognição. Ela não
        # executa ferramentas, não concede permissões e não muda a consulta usada
        # pelos engines factuais abaixo.
        if self.natural_interaction is not None:
            try:
                turn_context = self.natural_interaction.begin_turn(text)
                cognitive_request = dict(request)
                cognitive_input = turn_context.get("contextual_input") or text
                if turn_context.get("has_visual_evidence"):
                    cognitive_input = f"{cognitive_input} [imagem disponível pela percepção]"
                cognitive_request.update({
                    "input": cognitive_input,
                    "original_input": text,
                    "dialogue_context": turn_context,
                    "actor": turn_context.get("actor"),
                    "relationship": turn_context.get("relationship"),
                })
            except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError):
                turn_context = None
                cognitive_request = request

        def finish(answer, source):
            return self._finish(
                answer,
                position,
                response_started,
                source=source,
                user_text=text,
                turn_context=turn_context,
            )

        if self.cognitive_integration is not None:
            position = self.cognitive_integration.build_position(cognitive_request, route)
            request["cognitive_position"] = position
            self.last_cognitive_position = position
            cognitive_expression = self.cognitive_integration.expression(position)
            if cognitive_expression:
                return finish(cognitive_expression, "cognitive_expression")

        if self.internal_knowledge:
            answer = self.internal_knowledge.answer(text)
            if answer:
                return finish(answer, "internal_knowledge")

        # Conhecimento offline real/enciclopédico vem antes dos matchers temáticos
        # legados. Isso evita que uma coincidência lexical fraca em Física/PLUS
        # sequestre uma pergunta factual simples.
        if self.offline_knowledge is not None:
            try:
                answer = self.offline_knowledge.answer(text)
            except (OSError, RuntimeError, TypeError, ValueError):
                answer = None
            if answer:
                return finish(answer, "offline_knowledge")

        # Quando a própria consulta pede profundidade/pesquisa/benchmark/dados,
        # a camada PLUS pode responder antes. Isso preserva o comportamento já
        # validado e não altera IDs nem remove as bases legadas.
        if self.knowledge_expansion and self.knowledge_expansion.prefers(text):
            answer = self.knowledge_expansion.answer(text)
            if answer:
                return finish(answer, "knowledge_expansion")

        # Física e Química permanecem antes dos catálogos amplos. O currículo
        # contém muitos termos genéricos e não deve engolir rotas científicas.
        if self.physics_knowledge:
            answer = self.physics_knowledge.answer(text)
            if answer:
                return finish(answer, "physics_knowledge")

        if self.chemistry_knowledge:
            answer = self.chemistry_knowledge.answer(text)
            if answer:
                return finish(answer, "chemistry_knowledge")

        if self.multidisciplinary_knowledge:
            answer = self.multidisciplinary_knowledge.answer(text)
            if answer:
                return finish(answer, "multidisciplinary_knowledge")

        if self.curriculum_knowledge:
            answer = self.curriculum_knowledge.answer(text)
            if answer:
                return finish(answer, "curriculum_knowledge")

        if self.knowledge_expansion:
            answer = self.knowledge_expansion.answer(text)
            if answer:
                return finish(answer, "knowledge_expansion_fallback")

        if self.knowledge_packs:
            answer = self.knowledge_packs.answer(text)
            if answer:
                return finish(answer, "knowledge_pack")

        words = str(text).strip().split()
        if len(words) <= 2:
            return finish(
                "Entendi a palavra, mas ainda não sei o que você quer descobrir sobre ela. 😊 "
                "Pode me fazer uma pergunta ou me dar um pouco mais de contexto?",
                "bounded_fallback",
            )

        return finish(
            "Ainda não tenho uma resposta confiável para isso na minha base local. "
            "Prefiro ser sincera a inventar algo. 😊 Se você quiser, esse conhecimento "
            "pode entrar em um Knowledge Pack quando ampliarmos minha biblioteca.",
            "unknown_fallback",
        )

    def _finish(self, answer, position, started, *, source, user_text="", turn_context=None):
        if position is not None:
            timings = position.setdefault("timings_ms", {})
            timings["response_generation"] = round((perf_counter() - started) * 1000, 3)
            position["response_source"] = source

        if self.natural_interaction is not None:
            try:
                return self.natural_interaction.finish_turn(
                    user_text,
                    answer,
                    intent=(position or {}).get("perceived_intent"),
                    cognitive_position=position,
                    response_source=source,
                    turn_context=turn_context,
                )
            except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError):
                pass
        return answer
