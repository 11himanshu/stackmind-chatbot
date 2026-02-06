from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from db import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role = Column(
        String,
        nullable=False,  # "user" | "assistant"
    )

    message = Column(
        String,
        nullable=False,
    )

    # ----------------------------------------------------
    # OPTIONAL ASSISTANT METADATA
    #
    # Stored ONLY for assistant messages.
    #
    # Examples:
    # {
    #   "images": [{ url, alt, credit }]
    #   "tool": "image"
    # }
    #
    # Rules:
    # - NULL for user messages
    # - JSON for forward compatibility
    # ----------------------------------------------------
    message_meta = Column(
        JSON,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )