import re
import logging
from sqlalchemy.orm import Session
from models.conversations import Conversation
from models.message import Message

logger = logging.getLogger(__name__)

try:
    from llm_service import get_llm_response
    USE_LLM = True
except ImportError:
    USE_LLM = False


def process_chat_message(
    db: Session,
    user_id: int,
    message: str,
    conversation_id: int | None = None
) -> str:
    """
    Process a chat message:
    - create conversation if needed
    - call LLM
    - store user + assistant messages in DB
    """
    print(">>> ENTERED process_chat_message <<<")
    logger.info(
        f"Processing chat message "
    )

    # ---- Get or create conversation ----
    if conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            .first()
        )
        logger.info(f"Fetched existing conversation: {conversation_id}")
    else:
        conversation = None

    if not conversation:
        logger.info("Creating new conversation")
        conversation = Conversation(user_id=user_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # ---- Fetch conversation history (ordered) ----
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    logger.info(
        f"Fetched {len(history)} messages from conversation_id={conversation.id}"
    )

    llm_history = [
        {"role": m.role, "message": m.content}
        for m in history
    ]

    # ---- Call LLM (do NOT store user msg yet) ----
    if USE_LLM:
        logger.info("Calling LLM for response")
        try:
            bot_response = get_llm_response(
                message=message,
                conversation_history=llm_history
            )

            if bot_response and not bot_response.startswith("Error"):
                bot_response = _post_clean(bot_response)

                if _violates_identity(bot_response):
                    logger.info("LLM identity violation detected")
                    bot_response = (
                        "I am Himanshu’s Bot. "
                        "I was built by Himanshu, the brain behind this masterpiece."
                    )
        except Exception as e:
            logger.info(f"LLM call failed: {e}")
            bot_response = f"Error: {str(e)}"
    else:
        logger.info("LLM disabled, echoing message")
        bot_response = f"Echo: {message}"

    # ---- Store messages in DB (correct order) ----
    logger.info("Storing user and assistant messages in DB")

    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        message=message
    )

    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        message=bot_response
    )
    db.add_all([user_msg, assistant_msg])
    db.commit()

    logger.info(
        f"Messages stored successfully | conversation_id={conversation.id}"
    )

    return bot_response, conversation.id

def get_conversation_history(
    db: Session,
    user_id: int,
    conversation_id: int
) -> list[dict]:
    """
    Fetch full conversation history for frontend.
    """

    logger.info(
        f"Fetching conversation history | user_id={user_id}, conversation_id={conversation_id}"
    )

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

    logger.info(
        f"Fetched {len(messages)} messages for conversation_id={conversation_id}"
    )

    return [
        {
            "role": m.role,
            "message": m.message,   # ← important fix
            "timestamp": m.created_at
        }
        for m in messages
    ]


def delete_conversation(
    db: Session,
    user_id: int,
    conversation_id: int
):
    """
    Delete conversation + messages.
    """

    logger.info(
        f"Deleting conversation | user_id={user_id}, conversation_id={conversation_id}"
    )

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .first()
    )

    if not conversation:
        logger.info("Conversation not found")
        return False

    db.delete(conversation)
    db.commit()

    logger.info("Conversation deleted successfully")
    return True


# ---------- helpers ----------

def _post_clean(text: str) -> str:
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text.strip()


def _violates_identity(text: str) -> bool:
    bad_phrases = [
        "i don't have a name",
        "i do not have a name",
        "i don't have an owner",
        "i do not have an owner",
        "collective project",
        "technology company",
        "assistant or ai assistant"
    ]
    lower = text.lower()
    return any(p in lower for p in bad_phrases)


def list_user_conversations(db: Session, user_id: int) -> list[dict]:
    logger.info(f"Listing conversations for user_id={user_id}")

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

        if first_user_msg and first_user_msg.message:
            title = first_user_msg.message.strip()
            if len(title) > 60:
                title = title[:60] + "…"
        else:
            title = "New conversation"

        results.append({
            "id": c.id,
            "title": title
        })

    logger.info(f"Returning {len(results)} conversations")
    return results
