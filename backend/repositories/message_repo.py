from sqlalchemy.orm import Session
from models.message import Message
from models.conversations import Conversation


# ============================================================
# FETCH HISTORY
# ============================================================

def fetch_history(
    db: Session,
    *,
    conversation_id: int,
    user_id: int,
):
    """
    Fetch full conversation history in chronological order.

    Guarantees:
    - Messages belong to the user
    - Correct order for LLM + UI
    - Stable ordering even when timestamps are identical
    """
    return (
        db.query(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        # 🔑 CRITICAL FIX: secondary ordering by ID
        .order_by(
            Message.created_at.asc(),
            Message.id.asc(),
        )
        .all()
    )


# ============================================================
# SAVE MESSAGES (USER + ASSISTANT)
# ============================================================

def save_messages(
    db: Session,
    *,
    conversation_id: int,
    user_message: str,
    assistant_message: str,
    assistant_meta: dict | None = None,
    # ------------------------------------------------
    # Reserved (NOT persisted yet)
    # ------------------------------------------------
    normalized_user_message: str | None = None,
    is_followup: bool | None = None,
):
    """
    Persist one user message and one assistant message.

    Design rules:
    - User message: raw input only
    - Assistant message: rendered text only
    - assistant_meta: structured assistant data (images, tools)
    - No normalized or followup data persisted yet
    """

    db.add_all([
        Message(
            conversation_id=conversation_id,
            role="user",
            message=user_message,
            message_meta=None,
        ),
        Message(
            conversation_id=conversation_id,
            role="assistant",
            message=assistant_message,
            message_meta=assistant_meta,
        ),
    ])


# ============================================================
# DELETE MESSAGES (FK SAFE)
# ============================================================

def delete_messages(
    db: Session,
    *,
    conversation_id: int,
):
    """
    Hard delete all messages for a conversation.

    Called before deleting the conversation row.
    """
    (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .delete(synchronize_session=False)
    )