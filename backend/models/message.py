from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from db import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(
    Integer,
    ForeignKey("conversations.id", ondelete="CASCADE"),
    nullable=False,
    index=True
)
    role = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())