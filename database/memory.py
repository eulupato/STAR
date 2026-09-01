from database.database import Base, SessionLocal, engine
from database.models import Message
from core.logging_config import get_logger

log = get_logger("memory")


class Memory:
    """Memória persistente simples da conversa da STAR."""

    def __init__(self, *, session_factory=SessionLocal, db_engine=engine):
        Base.metadata.create_all(db_engine)
        self.session = session_factory()

    def save(self, sender, content):
        message = Message(sender=sender, content=str(content))
        self.session.add(message)
        self.session.commit()
        return message

    def load(self, limit: int | None = None):
        query = self.session.query(Message)
        if limit is None:
            return query.order_by(Message.id.asc()).all()

        safe_limit = max(1, min(int(limit), 1000))
        recent = (
            query.order_by(Message.id.desc())
            .limit(safe_limit)
            .all()
        )
        return list(reversed(recent))

    def close(self):
        try:
            self.session.close()
        except Exception as exc:
            log.warning("Falha ao fechar sessão de memória: %s", exc)
