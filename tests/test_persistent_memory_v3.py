import pytest
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


def test_persistent_memory_rolls_back_failed_commit(tmp_path, monkeypatch):
    memory = make_memory(tmp_path)
    original_commit = memory.session.commit
    calls = {"count": 0}

    def fail_once():
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("commit failure")
        return original_commit()

    monkeypatch.setattr(memory.session, "commit", fail_once)

    with pytest.raises(RuntimeError, match="commit failure"):
        memory.save("Você", "falha")

    memory.save("STAR", "recuperado")
    assert [item.content for item in memory.load()] == ["recuperado"]
    memory.close()
