from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from main import create_star


def test_math_and_knowledge_packs():
    star=create_star()
    assert "4" in star.process("quanto é 2+2")
    assert star.packs.list()


def test_network_commands_respect_offline_mode():
    star=create_star()
    star.network_enabled=False
    answer=star.process("abra o google")
    assert "Ative o modo ONLINE" in answer


def test_local_command_remains_available_offline():
    star=create_star()
    star.network_enabled=False
    answer=star.process("que horas são?")
    assert "Agora são" in answer
