from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, Text

from database.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    sender = Column(Text)
    content = Column(Text)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
