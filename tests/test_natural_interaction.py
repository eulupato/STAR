import json
import uuid

from core.conversation import ConversationEngine
from core.natural_interaction import NaturalInteraction
from main import create_star


class FakeSurfaceModel:
    def __init__(self, response="Tá, entendi 😄. Me conta mais."):
        self.response = response
        self.calls = []

    def generate(self, message, context=None, **kwargs):
        self.calls.append({"packet": json.loads(message), "context": context, "kwargs": kwargs})
        return self.response


def _use_fake_surface(star, response="Tá, entendi 😄. Me conta mais."):
    fake = FakeSurfaceModel(response)
    star.natural_interaction._expression_model = fake
    star.natural_interaction._default_model = None
    star.natural_interaction._model_enabled = True
    return fake


def _disable_surface_model(star):
    star.natural_interaction._expression_model = None
    star.natural_interaction._default_model = None
    star.natural_interaction._model_enabled = False


def test_natural_runtime_is_one_expression_layer_not_a_parallel_brain():
    star = create_star()
    stats = star.natural_interaction.stats()
    assert stats["status"] == "active-integrated"
    assert stats["model_is_star"] is False
    assert stats["model_decides_facts"] is False
    assert stats["model_grants_permissions"] is False
    assert star.conversation.natural_interaction is star.natural_interaction
    assert star.executive.natural_interaction is star.natural_interaction


def test_smalltalk_can_be_freely_verbalized_from_semantic_fallback():
    star = create_star()
    fake = _use_fake_surface(star, "Oii 😄 Tô aqui. O que aconteceu?")
    response = star.process("oi")
    assert response == "Oii 😄 Tô aqui. O que aconteceu?"
    assert len(fake.calls) == 1
    packet = fake.calls[0]["packet"]
    assert packet["user_message"] == "oi"
    assert packet["semantic_answer"]
    assert "affective_state" in packet
    assert "somente a camada de expressão" in fake.calls[0]["context"].casefold()


def test_operational_commands_do_not_pass_through_freeform_expression():
    star = create_star()
    fake = _use_fake_surface(star, "ISSO NÃO DEVE APARECER")
    response = star.process("que horas são")
    assert response != "ISSO NÃO DEVE APARECER"
    assert fake.calls == []


def test_multiturn_followup_carries_previous_topic_into_cognition():
    star = create_star()
    fake = _use_fake_surface(star, "Entendi. E sobre isso eu manteria minha leitura por enquanto.")

    star.process("O que você acha do filme Matrix?")
    first_topic = star.natural_interaction.active_topic
    assert first_topic

    star.process("E o segundo?")
    assert len(fake.calls) >= 2
    packet = fake.calls[-1]["packet"]
    assert packet["reference_target"] == first_topic
    assert star.natural_interaction.last_reference_target == first_topic


def test_missing_visual_context_is_not_fabricated_for_aesthetic_opinion():
    star = create_star()
    _disable_surface_model(star)
    response = star.process("STAR, você acha que eu fico bonito com essa roupa?")
    position = star.executive.last_cognitive_position
    assert position is not None
    assert position["processing_path"] == "DELIBERATIVE"
    assert any("características visuais" in item for item in position.get("uncertainties", ()))
    assert any("ocasião" in item for item in position.get("uncertainties", ()))
    assert "ocasião" in response


def test_real_b25_visual_observation_removes_fake_visual_gap_but_not_occasion_gap():
    star = create_star()
    _disable_surface_model(star)
    star.multimodal_perception.ingest(
        "vision",
        {
            "content": "pessoa usando camisa preta e calça clara",
            "confidence": 0.9,
            "event_key": f"look-{uuid.uuid4().hex}",
        },
        source="unit-test-camera",
    )
    star.process("STAR, você acha que eu fico bonito com essa roupa?")
    position = star.executive.last_cognitive_position
    uncertainties = tuple(position.get("uncertainties", ()))
    assert not any("características visuais" in item for item in uncertainties)
    assert any("ocasião" in item for item in uncertainties)


def test_declared_name_becomes_persistent_b26_person_without_authentication():
    star = create_star()
    name = "Nina" + uuid.uuid4().hex[:7]
    response = star.process(f"meu nome é {name}")
    assert "Prazer" in response
    assert star.people_entities.active_person_name == name
    assert star.natural_interaction.active_person_name == name
    candidates = star.people_entities.find_people(name)
    assert len(candidates) == 1
    assert candidates[0]["authenticated"] is False


def test_profile_and_visual_identity_evidence_persist_without_becoming_authentication():
    star = create_star()
    name = "Ana" + uuid.uuid4().hex[:7]
    result = star.people_entities.ingest_profile(
        name,
        {"apelido": "Aninha", "cor_preferida": "azul"},
        aliases=("Aninha",),
        source="unit-test-profile",
        reference=f"profile://{uuid.uuid4().hex}",
        identity_evidence=(
            {
                "modality": "vision",
                "source": "unit-test-image",
                "reference": f"image://{uuid.uuid4().hex}",
                "descriptor": "evidência visual associada ao perfil",
                "confidence": 0.82,
            },
        ),
    )
    assert result["authenticated"] is False
    assert result["grants_permission"] is False
    assert result["identity_evidence"][0]["raw_biometric_stored"] is False
    context = star.people_entities.person_context(result["person"]["person_id"], limit=16)
    assert context["memories"]
    assert any("Perfil declarado" in item["content"] for item in context["memories"])


def test_dialogue_history_is_bounded_and_persistence_is_not_raw_every_turn():
    star = create_star()
    _disable_surface_model(star)
    runtime = star.natural_interaction
    for index in range(runtime.history.maxlen + 5):
        context = runtime.begin_turn(f"mensagem casual {index}")
        runtime.finish_turn(
            f"mensagem casual {index}",
            f"resposta {index}",
            intent="conversation",
            turn_context=context,
        )
    assert len(runtime.history) == runtime.history.maxlen
    stats = runtime.stats()
    assert stats["persistent_transcript_each_turn"] is False
    assert stats["continuity_anchor_every_turns"] == 8


def test_weather_semantics_remain_verbatim_even_when_surface_model_is_connected():
    class NoWeather:
        def current(self, location=None):
            return None

    engine = ConversationEngine(NoWeather())
    star = create_star()
    fake = _use_fake_surface(star, "inventei o clima")
    engine.natural_interaction = star.natural_interaction
    response = engine.respond("como está o tempo?")
    assert "não consegui confirmar" in response
    assert fake.calls == []
