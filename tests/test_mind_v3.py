import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.mind import EventBus, WorkingMemory
from main import create_star


def test_event_bus_records_and_dispatches():
    bus = EventBus(history_limit=32)
    seen = []
    bus.subscribe("test", lambda event: seen.append(event.payload["value"]))
    bus.publish("test", {"value": 7})
    assert seen == [7]
    assert bus.count() == 1


def test_working_memory_is_bounded_and_keeps_facts():
    memory = WorkingMemory(max_turns=8)
    for index in range(12):
        memory.add_turn("user", str(index))
    memory.set_fact("user_name", "Teste")
    assert memory.snapshot()["turn_count"] == 8
    assert memory.get_fact("user_name") == "Teste"


def test_mind_is_active_inside_v3():
    star = create_star()
    status = star.mind_status()
    assert status["active"] is True
    assert status["generation"] == "MIND"
    assert "Event Bus" in status["architecture"]


def test_context_keeps_session_name():
    star = create_star()
    first = star.process("meu nome é Aurora")
    second = star.process("qual meu nome")
    assert "Aurora" in first
    assert "Aurora" in second
    assert star.mind.metacognition.last.selected_step == "context_recall"


def test_mind_preserves_math_priority():
    star = create_star()
    answer = star.process("quanto é 2+2")
    assert "4" in answer
    assert star.mind.metacognition.last.selected_step == "math"


def test_mind_preserves_offline_local_actions():
    star = create_star()
    star.network_enabled = False
    answer = star.process("que horas são?")
    assert "Agora são" in answer
    assert star.mind.metacognition.last.selected_step == "computer_control"


def test_mind_keeps_network_guard():
    star = create_star()
    star.network_enabled = False
    answer = star.process("abra o google")
    assert "Ative o modo ONLINE" in answer
    assert star.mind.metacognition.last.selected_step == "computer_control"


def test_internal_knowledge_uses_legacy_executor_inside_mind():
    star = create_star()
    answer = star.process("qual o seu nome?")
    assert answer
    assert star.mind.metacognition.last.selected_step == "legacy_reasoning"


def test_mind_diagnostic_command_is_local():
    star = create_star()
    answer = star.process("diagnóstico da mente")
    assert "MIND ATIVA" in answer


def test_local_fallback_still_works_when_mind_is_disabled():
    star = create_star()
    star.mind = None
    assert "4" in star.process("quanto é 2+2")
