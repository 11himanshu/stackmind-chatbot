import re
import json
import logging
from typing import Generator
from sqlalchemy.orm import Session

from models.conversations import Conversation
from models.message import Message
from utils import _post_clean, _violates_identity

logger = logging.getLogger(__name__)

# ============================================================
# Optional LLM import
# - Streaming ONLY
# - Single LLM call per user message
# ============================================================
try:
    from llm_service import get_llm_response_stream
    USE_LLM = True
except ImportError:
    USE_LLM = False


# ============================================================
# STREAMING CHAT PROCESSOR (PRODUCTION-GRADE)
# ============================================================
def process_chat_stream(
    db: Session,
    user_id: int,
    message: str,
    conversation_id: int | None = None
) -> Generator[str, None, None]:
    """
    Streaming chat with persistence.

    GUARANTEES:
    --------------------------------
    - ONE LLM call per message
    - ONE conversation per chat session
    - conversation_id emitted ONCE as metadata
    - ONLY assistant text is streamed
    - Markdown is never polluted
    - Messages are persisted AFTER stream completes
    """

    logger.info("Entered process_chat_stream")

    # ========================================================
    # Fetch existing conversation (ONLY if id provided)
    # ========================================================
    conversation = None

    if conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            .first()
        )

        if conversation:
            logger.info(f"Using existing conversation_id={conversation_id}")
        else:
            logger.warning(
                f"Invalid conversation_id={conversation_id} for user_id={user_id}"
            )

    # ========================================================
    # Create new conversation ONLY when id is None
    # ========================================================
    if conversation is None:
        logger.info("Creating new conversation")
        conversation = Conversation(user_id=user_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    logger.info(f"Active conversation_id={conversation.id}")

    # ========================================================
    # SEND METADATA ONCE (FRONTEND MUST STRIP THIS)
    # ========================================================
    yield f'__META__{json.dumps({"conversation_id": conversation.id})}\n'

    # ========================================================
    # Fetch conversation history for LLM context
    # ========================================================
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    llm_history = [
        {"role": m.role, "message": m.message}
        for m in history
    ]

    logger.info(
        f"Fetched {len(history)} messages "
        f"for conversation_id={conversation.id}"
    )

    # ========================================================
    # STREAM LLM RESPONSE (TEXT ONLY)
    # ========================================================
    assistant_full_response = ""

    if not USE_LLM:
        logger.warning("LLM disabled, echoing message")
        assistant_full_response = f"Echo: {message}"
        yield assistant_full_response
    else:
        logger.info("Starting LLM streaming")

        try:
            stream = get_llm_response_stream(
                message=message,
                conversation_history=llm_history
            )

            for chunk in stream:
                if not chunk:
                    continue

                assistant_full_response += chunk
                yield chunk  # 🔥 PURE TEXT — NO METADATA

        except Exception:
            logger.exception("LLM streaming failed")
            assistant_full_response = "Sorry, something went wrong."
            yield assistant_full_response

    # ========================================================
    # POST-PROCESS RESPONSE (SAFETY ONLY)
    # ========================================================
    assistant_full_response = _post_clean(assistant_full_response)

    if _violates_identity(assistant_full_response):
        assistant_full_response = (
            "I am Himanshu’s Bot. "
            "I was built by Himanshu, the brain behind this masterpiece."
        )

    # ========================================================
    # PERSIST MESSAGES (AFTER STREAM COMPLETES)
    # ========================================================
    logger.info("Persisting messages to database")

    db.add_all([
        Message(
            conversation_id=conversation.id,
            role="user",
            message=message
        ),
        Message(
            conversation_id=conversation.id,
            role="assistant",
            message=assistant_full_response
        )
    ])

    db.commit()

    logger.info(
        f"Messages saved successfully | conversation_id={conversation.id}"
    )


# ============================================================
# FETCH FULL CONVERSATION HISTORY
# ============================================================
def get_conversation_history(
    db: Session,
    user_id: int,
    conversation_id: int
) -> list[dict]:
    """
    Fetch full conversation history for frontend.
    SINGLE SOURCE OF TRUTH for history rendering.
    """

    messages = (
        db.query(Message)
        .join(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    return [
        {
            "role": m.role,
            "message": m.message,
            "timestamp": m.created_at
        }
        for m in messages
    ]


# ============================================================
# DELETE CONVERSATION
# ============================================================
def delete_conversation(
    db: Session,
    user_id: int,
    conversation_id: int
) -> bool:
    """
    Delete conversation and all messages.
    """

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .first()
    )

    if not conversation:
        return False

    db.delete(conversation)
    db.commit()
    return True


# ============================================================
# LIST CONVERSATIONS FOR SIDEBAR
# ============================================================
def list_user_conversations(
    db: Session,
    user_id: int
) -> list[dict]:
    """
    List conversations for sidebar.
    """

    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.id.desc())
        .all()
    )

    results = []

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
# DELETE CONVERSATION
# ============================================================
def delete_conversation(
    db: Session,
    user_id: int,
    conversation_id: int
) -> bool:
    db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).delete(synchronize_session=False)

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .first()
    )

    if not conversation:
        return False

    db.delete(conversation)
    db.commit()
    return True