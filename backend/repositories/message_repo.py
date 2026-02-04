from sqlalchemy.orm import Session
from models.message import Message
from models.conversations import Conversation


def fetch_history(
    db: Session,
    *,
    conversation_id: int,
    user_id: int
):
    """
    Fetch full conversation history in chronological order.

    Guarantees:
    - Only messages belonging to the user
    - Ordered for correct context reconstruction
    """
    return (
        db.query(Message)
        .join(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .order_by(Message.created_at.asc())
        .all()
    )


def save_messages(
    db: Session,
    *,
    conversation_id: int,
    user_message: str,
    assistant_message: str,
    # ------------------------------------------------
    # Optional (future-safe, not persisted yet)
    # ------------------------------------------------
    normalized_user_message: str | None = None,
    is_followup: bool | None = None
):
    """
    Persist user + assistant messages.

    IMPORTANT DESIGN RULES:
    - user_message is ALWAYS the raw user input
    - assistant_message is ONLY what the assistant replied
    - normalized_user_message is NOT stored yet
      (used only for routing / tools / LLM)
    - is_followup is NOT stored yet
      (kept for future analytics / UI)

    This function is intentionally backward-compatible.
    """

    # NOTE:
    # We intentionally do NOT persist normalized_user_message
    # or is_followup to avoid polluting conversation history.
    # These will be added later via metadata or a separate table.

    db.add_all([
        Message(
            conversation_id=conversation_id,
            role="user",
            message=user_message
        ),
        Message(
            conversation_id=conversation_id,
            role="assistant",
            message=assistant_message
        )
    ])


def delete_messages(
    db: Session,
    *,
    conversation_id: int
):
    """
    Hard delete all messages for a conversation.

    Used when:
    - Conversation is deleted
    - Reset / cleanup flows
    """
    db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).delete(synchronize_session=False)