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
        index=True
    )

    role = Column(
        String,
        nullable=False
    )

    message = Column(
        String,
        nullable=False
    )

    # ----------------------------------------------------
    # OPTIONAL METADATA (forward-compatible)
    #
    # Examples:
    # - is_followup: bool
    # - normalized_query: str
    # - domain: str
    # - freshness: str (static | real_time)
    # - tool_used: str
    #
    # NOTE:
    # - Nullable → old rows remain valid
    # - JSON → no schema changes for future features
    # ----------------------------------------------------
    message_meta = Column(JSON,nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )