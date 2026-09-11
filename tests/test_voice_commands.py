from core.agents import AGENT_SPECS, AgentManager
from core.commands import command_count, match_command, voice_command_examples


def test_voice_catalog_has_at_least_one_thousand_unique_commands():
    commands = voice_command_examples()
    assert len(commands) == len(set(commands))
    assert command_count() >= 1000


def test_wake_word_and_accents_are_normalized():
    match = match_command("STAR, abra o Spotify")
    assert match is not None
    assert match.intent == "open_app"
    assert match.slots["target"] == "spotify"

    match = match_command("Ei STAR, aumente o volume")
    assert match is not None
    assert match.intent == "volume_up"


def test_queries_keep_useful_slots():
    match = match_command("pesquise física quântica")
    assert match is not None
    assert match.intent == "web_search"
    assert match.slots["query"] == "fisica quantica"

    match = match_command("STAR, encontre o arquivo roadmap")
    assert match is not None
    assert match.intent == "find_file"
    assert match.slots["query"] == "roadmap"


def test_sensitive_remote_commands_are_blocked():
    manager = AgentManager()
    response = manager.dispatch("STAR, feche o VS Code", remote=True)
    assert response is not None
    assert "confirmação local" in response


def test_agent_catalog_registers_all_specialized_agents_without_claiming_availability():
    assert len(AGENT_SPECS) == 19
    statuses = {spec.status for spec in AGENT_SPECS}
    assert statuses <= {"available", "partial", "planned"}
    assert any(spec.status == "planned" for spec in AGENT_SPECS)


def test_command_status_reports_generated_catalog_size():
    response = AgentManager().dispatch("quantos comandos de voz você tem")
    assert str(command_count()) in response
