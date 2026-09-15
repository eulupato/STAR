from __future__ import annotations

from core.cognitive_integration import CognitiveIntegration
from core.executive import Executive
from core.router import Router


class FakeWorkingMemory:
    def __init__(self):
        self.items = []

    def add(self, content, **kwargs):
        item = {"content": content, **kwargs}
        self.items.append(item)
        return item


class FakeMemoryContinuity:
    def __init__(self):
        self.working = FakeWorkingMemory()
        self.items = []

    def recall(self, query, limit=6):
        query = str(query).casefold()
        return [item for item in self.items if query in item.get("content", "").casefold()][:limit]


class FakePersonality:
    def __init__(self):
        self.preferences = {}
        self.history = []
        self.affect = {
            "valence": 0.1,
            "energy": 0.8,
            "curiosity": 0.7,
            "caution": 0.4,
            "familiarity": 0.6,
            "confidence": 0.8,
            "interest": 0.7,
            "alert": 0.3,
            "context": "conversation",
        }
        self._next_id = 1

    def current_state(self):
        return dict(self.affect)

    def preference(self, name):
        record = self.preferences.get(name)
        if record is None:
            return None
        return {"name": name, "value": record["value"], "record": dict(record)}

    def set_preference(self, name, value, *, source, reference, confidence=1.0):
        memory_id = self._next_id
        self._next_id += 1
        record = {
            "id": memory_id,
            "name": name,
            "value": value,
            "source": source,
            "reference": reference,
            "confidence": confidence,
        }
        self.preferences[name] = record
        self.history.append(record)
        return {"memory_id": memory_id, "record": record}


class FakeMindLoop:
    def __init__(self):
        self.calls = []
        self.counter = 0

    def run_cycle(self, text, **kwargs):
        self.counter += 1
        self.calls.append((text, kwargs))
        missing = tuple(kwargs.get("missing_context") or ())
        return {
            "cycle_id": f"FAKE-{self.counter}",
            "stages": {
                "conhecimento": {"items": []},
                "interpretacao": {
                    "epistemic_kind": "inference",
                    "summary": "interpretação revisável",
                    "hypotheses": ["hipótese A", "hipótese B"],
                },
                "metacognicao": {
                    "knows": False,
                    "does_not_know": True,
                    "confidence": 0.45,
                    "sources": [],
                    "needs_research": True,
                    "needs_question": bool(missing),
                    "needs_review": False,
                },
            },
            "execution_performed": False,
            "operational_authorization": False,
        }


class FakeIdentity:
    def get(self):
        return {
            "purpose": {
                "principles": ["ser útil", "ser honesta", "ser cuidadosa", "ser responsável"]
            }
        }


class FakeStar:
    def __init__(self):
        self.mind_loop = FakeMindLoop()
        self.memory_continuity = FakeMemoryContinuity()
        self.affective_personality = FakePersonality()
        self.social_cognition = object()
        self.identity = FakeIdentity()


def _integration():
    star = FakeStar()
    return CognitiveIntegration(star), star


def test_fast_path_for_simple_interaction_does_not_run_full_mind_loop():
    integration, star = _integration()
    position = integration.build_position({"input": "oi"}, {"internal_response": False})
    assert position["processing_path"] == "FAST"
    assert star.mind_loop.calls == []
    assert position["execution_performed"] is False
    assert position["operational_authorization"] is False


def test_opinion_and_decision_inputs_escalate_to_deliberative_path():
    integration, star = _integration()
    assert integration.select_path("STAR, o que você acha dessa roupa?") == "DELIBERATIVE"
    assert integration.select_path("Me ajuda a decidir qual opção é melhor") == "DELIBERATIVE"
    position = integration.build_position({"input": "STAR, o que você acha desse filme?"}, {})
    assert position["processing_path"] == "DELIBERATIVE"
    assert len(star.mind_loop.calls) == 1
    assert position["cycle_id"] == "FAKE-1"


def test_user_opinion_never_overwrites_star_opinion_and_disagreement_is_possible():
    integration, _star = _integration()
    integration.record_opinion(
        "esse filme",
        "eu gosto bastante dele",
        intensity=0.8,
        justification="A ideia central me interessa, apesar do ritmo irregular.",
        confidence=0.82,
        source="unit-test",
        reference="test://opinion/film/1",
    )

    position = integration.build_position({"input": "Esse filme é horrível."}, {})
    assert position["user_position"]["stance"] == "negative"
    assert position["user_position"]["becomes_star_opinion"] is False
    assert position["star_opinion"]["position"] == "eu gosto bastante dele"
    assert position["disagreement"]["active"] is True
    assert position["decision"]["should_disagree"] is True

    response = integration.expression(position)
    assert response.startswith("Eu vejo diferente")
    assert "A ideia central me interessa" in response


def test_argument_from_user_is_information_not_automatic_opinion_revision():
    integration, star = _integration()
    first = integration.record_opinion(
        "filme x",
        "positivo",
        confidence=0.75,
        source="unit-test",
        reference="test://opinion/x/1",
    )
    integration.build_position(
        {"input": "Filme X é horrível porque o segundo ato não desenvolve os personagens."},
        {},
    )
    current = integration.opinion("filme x")
    assert current["position"] == "positivo"
    assert current["record"]["id"] == first["memory_id"]
    assert len(star.affective_personality.history) == 1


def test_opinion_revision_is_explicit_auditable_and_preserves_history():
    integration, star = _integration()
    first = integration.record_opinion(
        "tema",
        "favorável",
        confidence=0.7,
        source="evidence-set-a",
        reference="evidence://a",
    )
    second = integration.revise_opinion(
        "tema",
        "mista",
        confidence=0.62,
        justification="Nova evidência reduziu minha confiança na posição anterior.",
        source="evidence-set-b",
        reference="evidence://b",
        reason="evidência nova e verificável",
    )
    assert second["revision_of_memory_id"] == first["memory_id"]
    assert second["history_preserved"] is True
    assert len(star.affective_personality.history) == 2
    assert integration.opinion("tema")["position"] == "mista"


def test_aesthetic_opinion_with_missing_context_asks_instead_of_fabricating_vision():
    integration, _star = _integration()
    position = integration.build_position({"input": "STAR, você acha que eu fico bonito com essa roupa?"}, {})
    assert position["processing_path"] == "DELIBERATIVE"
    assert position["decision"]["should_ask"] is True
    assert any("ocasião" in item for item in position["uncertainties"])
    response = integration.expression(position)
    assert "base suficiente" in response
    assert "ocasião" in response


def test_affective_state_changes_tone_without_changing_persisted_opinion():
    integration, star = _integration()
    integration.record_opinion(
        "design y",
        "positivo",
        confidence=0.8,
        source="unit-test",
        reference="test://design/y",
    )
    normal = integration.build_position({"input": "O que você acha do design Y?"}, {})
    star.affective_personality.affect["caution"] = 0.95
    cautious = integration.build_position({"input": "O que você acha do design Y?"}, {})
    assert normal["star_opinion"]["position"] == cautious["star_opinion"]["position"]
    assert normal["tone"]["caution"] == "normal"
    assert cautious["tone"]["caution"] == "high"


def test_router_exposes_fast_and_deliberative_without_creating_parallel_brains():
    integration, _star = _integration()
    router = Router(cognitive_integration=integration)
    fast = router.route({"input": "oi"})
    deep = router.route({"input": "Você acha que essa escolha é boa?"})
    assert fast["cognitive_path"] == "FAST"
    assert fast["depth"] == "basic"
    assert deep["cognitive_path"] == "DELIBERATIVE"
    assert deep["depth"] == "deliberative"
    assert "executive" in deep["nuclei"]


def test_executive_uses_cognitive_expression_before_generic_unknown_fallback():
    integration, _star = _integration()
    integration.record_opinion(
        "esse filme",
        "eu gosto dele",
        confidence=0.8,
        source="unit-test",
        reference="test://executive/opinion",
    )
    router = Router(cognitive_integration=integration)
    executive = Executive(cognitive_integration=integration)
    request = {"input": "Esse filme é horrível."}
    route = router.route(request)
    answer = executive.execute(request, route)
    assert answer.startswith("Eu vejo diferente")
    assert request["cognitive_position"]["user_statement_becomes_star_belief"] is False
    assert executive.last_cognitive_position["decision"]["should_disagree"] is True
    assert executive.last_cognitive_position["response_source"] == "cognitive_expression"


def test_continuity_keeps_same_identity_opinion_across_multiple_interactions():
    integration, _star = _integration()
    integration.record_opinion(
        "filme z",
        "positivo",
        confidence=0.78,
        source="unit-test",
        reference="test://continuity/z",
    )
    positions = [
        integration.build_position({"input": "Filme Z é horrível."}, {}),
        integration.build_position({"input": "Filme Z é ruim."}, {}),
        integration.build_position({"input": "Qual sua opinião sobre Filme Z?"}, {}),
    ]
    assert all(position["star_opinion"]["position"] == "positivo" for position in positions)
    assert positions[0]["disagreement"]["active"] is True
    assert positions[1]["disagreement"]["active"] is True
    assert integration.opinion("filme z")["confidence"] == 0.78


def test_metrics_and_working_position_are_bounded_ephemeral_artifacts():
    integration, star = _integration()
    position = integration.build_position({"input": "Compare duas alternativas e me ajude a decidir."}, {})
    timings = position["timings_ms"]
    assert "path_selection" in timings
    assert "affective_processing" in timings
    assert "memory_retrieval" in timings
    assert "mind_loop" in timings
    assert "position_total" in timings
    assert star.memory_continuity.working.items[-1]["key"] == "cognitive_integration:last_position"
    assert star.memory_continuity.working.items[-1]["metadata"]["persistent"] is False
