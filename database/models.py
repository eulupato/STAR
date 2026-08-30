from sqlalchemy import Column, Integer, Text, DateTime
from datetime import datetime

from database.database import Base


class Message(Base):

    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True
    )

    sender = Column(
        Text
    )

    content = Column(
        Text
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )