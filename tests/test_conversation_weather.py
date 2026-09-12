from core.agents import AgentManager
from core.commands import command_count, command_variables, match_command
from core.conversation import ConversationEngine, conversation_response_count
from core.weather import WeatherSnapshot


class FakeWeather:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def current(self, location=None):
        return self.snapshot


def snapshot(*, temp=30, feels=31, rain=0.0, code=1, cloud=20):
    return WeatherSnapshot(
        location="Cidade Teste",
        temperature_c=temp,
        feels_like_c=feels,
        humidity_pct=40,
        precipitation_mm=rain,
        rain_mm=rain,
        cloud_cover_pct=cloud,
        weather_code=code,
        wind_kmh=8,
        is_day=True,
        observed_at="2026-09-12T18:00",
    )


def test_voice_catalog_has_at_least_four_thousand_distinct_variations():
    assert command_count() >= 4000


def test_voice_commands_expose_slots_and_weather_location_variable():
    variables = command_variables()
    assert "weather_current.location" in variables
    assert variables["weather_current.location"]["type"] == "free_text"

    match = match_command("STAR, como está o tempo em Porto Alegre por favor")
    assert match is not None
    assert match.intent == "weather_current"
    assert match.slots["location"] == "porto alegre"


def test_conversation_catalog_has_at_least_five_thousand_responses():
    assert conversation_response_count() >= 5000


def test_hot_weather_never_agrees_that_it_is_cold():
    engine = ConversationEngine(FakeWeather(snapshot(temp=30, feels=31)))
    response = engine.respond("Nossa, está frio hoje")
    assert response is not None
    assert "30" in response
    assert "não diria que está frio" in response


def test_cold_weather_never_agrees_that_it_is_hot():
    engine = ConversationEngine(FakeWeather(snapshot(temp=9, feels=7, code=3, cloud=90)))
    response = engine.respond("Que calor hoje")
    assert response is not None
    assert "9" in response
    assert "não chamaria de calor" in response


def test_beautiful_day_comment_is_grounded_in_weather():
    engine = ConversationEngine(FakeWeather(snapshot(temp=27, feels=28, code=1, cloud=20)))
    response = engine.respond("O dia está bonito")
    assert response is not None
    assert "dia bonito" in response
    assert "27" in response


def test_rain_claim_is_corrected_when_current_weather_is_dry():
    engine = ConversationEngine(FakeWeather(snapshot(temp=22, feels=22, rain=0, code=1, cloud=20)))
    response = engine.respond("O dia está chuvoso")
    assert response is not None
    assert "não está chovendo" in response


def test_weather_failure_does_not_hallucinate_conditions():
    engine = ConversationEngine(FakeWeather(None))
    response = engine.respond("O dia está bonito")
    assert response is not None
    assert "não consegui confirmar" in response
    assert "Prefiro não inventar" in response


def test_agent_weather_command_uses_dedicated_provider_without_enabling_general_web():
    manager = AgentManager(weather_provider=FakeWeather(snapshot(temp=25, feels=25)))
    response = manager.dispatch("qual o clima", network_enabled=False)
    assert response is not None
    assert "25" in response
    assert "Cidade Teste" in response
