from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from db import Base

from sqlalchemy.orm import relationship

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship(
        "Message",
        cascade="all, delete-orphan",
        passive_deletes=True
    )