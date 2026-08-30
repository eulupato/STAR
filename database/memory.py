from database.database import Base, SessionLocal, engine
from database.models import Message


class Memory:
    """Memória persistente simples da conversa da STAR."""

    def __init__(self):
        Base.metadata.create_all(engine)
        self.session = SessionLocal()

    def save(self, sender, content):
        message = Message(sender=sender, content=str(content))
        self.session.add(message)
        self.session.commit()
        return message

    def load(self):
        return (
            self.session.query(Message)
            .order_by(Message.id.asc())
            .all()
        )

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass
