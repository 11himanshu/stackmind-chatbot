from sqlalchemy.orm import Session

# IMPORTANT:
# functions.py is a backward-compatibility layer only.
# It must NOT import ChatService.
# It must NOT import services beyond chat_core.
# It only exposes functions used by routers.

from services.chat_core import process_chat_stream_core
from repositories.conversation_repo import (
    list_conversations,
    delete_conversation as delete_conversation_repo,
)
from repositories.message_repo import fetch_history, delete_messages


# ============================================================
# STREAMING CHAT (BACKWARD COMPAT)
# ============================================================

def process_chat_stream(
    db: Session,
    user_id: int,
    message: str,
    conversation_id: int | None = None
):
    return process_chat_stream_core(
        db=db,
        user_id=user_id,
        message=message,
        conversation_id=conversation_id
    )


# ============================================================
# CONVERSATION HISTORY (FIXED: IMAGES + IDS)
# ============================================================

def get_conversation_history(
    db: Session,
    user_id: int,
    conversation_id: int
):
    messages = fetch_history(
        db,
        conversation_id=conversation_id,
        user_id=user_id
    )

    return [
        {
            "id": m.id,
            "role": m.role,
            "message": m.message,
            "images": (m.message_meta or {}).get("images", []),
            "timestamp": m.created_at,
        }
        for m in messages
    ]


# ============================================================
# LIST CONVERSATIONS
# ============================================================

def list_user_conversations(
    db: Session,
    user_id: int
):
    conversations = list_conversations(
        db,
        user_id=user_id
    )

    results = []

    from models.message import Message

    for c in conversations:
        first_user_msg = (
            db.query(Message)
            .filter(
                Message.conversation_id == c.id,
                Message.role == "user"
            )
            .order_by(Message.created_at.asc())
            .first()
        )

        title = (
            first_user_msg.message[:60] + "…"
            if first_user_msg and first_user_msg.message
            else "New conversation"
        )

        results.append({
            "id": c.id,
            "title": title
        })

    return results


# ============================================================
# DELETE CONVERSATION (FIXED: NO RECURSION)
# ============================================================

def delete_conversation(
    db: Session,
    user_id: int,
    conversation_id: int
) -> bool:
    # delete messages first (FK safety)
    delete_messages(
        db,
        conversation_id=conversation_id
    )

    deleted = delete_conversation_repo(
        db,
        conversation_id=conversation_id,
        user_id=user_id
    )

    if not deleted:
        return False

    db.commit()
    return True