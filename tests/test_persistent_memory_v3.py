from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.memory import Memory


def make_memory(tmp_path):
    db_engine = create_engine(
        f"sqlite:///{(tmp_path / 'memory.db').as_posix()}",
        future=True,
    )
    session_factory = sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
    )
    return Memory(
        session_factory=session_factory,
        db_engine=db_engine,
    )


def test_persistent_memory_loads_recent_messages_in_order(tmp_path):
    memory = make_memory(tmp_path)
    memory.save("Você", "um")
    memory.save("STAR", "dois")
    memory.save("Você", "três")

    recent = memory.load(limit=2)
    assert [item.content for item in recent] == ["dois", "três"]
    memory.close()


def test_persistent_memory_can_load_full_history(tmp_path):
    memory = make_memory(tmp_path)
    memory.save("Você", "A")
    memory.save("STAR", "B")
    assert [item.content for item in memory.load()] == ["A", "B"]
    memory.close()
