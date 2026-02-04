import json
import re
from typing import Generator, Optional
from sqlalchemy.orm import Session

from core.logger import get_logger
from services.tool_router import ToolRouter
from repositories.conversation_repo import get_conversation, create_conversation
from repositories.message_repo import fetch_history, save_messages
from tools.safety import post_process_response

logger = get_logger(__name__)

# ----------------------------------------------------
# FOLLOW-UP DETECTION CONFIG (STRICT)
# ----------------------------------------------------

FOLLOWUP_PRONOUNS = {
    "it", "this", "that", "he", "she", "they",
    "him", "her", "them", "those"
}

VAGUE_CONTINUATIONS = {
    "and", "then", "continue", "next", "more"
}

SHORT_QUERY_WORD_COUNT = 4

# Strong indicators of a NEW topic (hard reset)
TOPIC_RESET_KEYWORDS = {
    "code", "python", "java", "api", "error",
    "weather", "price", "news", "stock",
    "youtube", "video", "link", "url"
}

# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------

def _get_last_user_message(history: list[dict]) -> Optional[str]:
    for msg in reversed(history):
        if msg["role"] == "user" and msg["message"].strip():
            return msg["message"]
    return None


def _contains_topic_reset(message: str) -> bool:
    msg = message.lower()
    return any(k in msg for k in TOPIC_RESET_KEYWORDS)


def _is_potential_followup(message: str) -> bool:
    msg = message.lower().strip()
    words = msg.split()

    # Very short and vague
    if len(words) <= SHORT_QUERY_WORD_COUNT:
        return True

    # Pronoun-based dependency
    if any(re.search(rf"\b{p}\b", msg) for p in FOLLOWUP_PRONOUNS):
        return True

    # Vague continuation phrases
    if any(msg.startswith(v) for v in VAGUE_CONTINUATIONS):
        return True

    return False


def _are_domains_compatible(prev: str, curr: str) -> bool:
    """
    Conservative domain safety gate.
    If domains differ, DO NOT normalize.
    """

    domain_keywords = {
        "tech": ["code", "api", "error", "bug", "python", "java"],
        "weather": ["weather", "temperature", "rain"],
        "politics": ["minister", "government", "election"],
        "media": ["song", "movie", "lyrics", "video", "youtube"],
    }

    def detect(text: str) -> Optional[str]:
        for domain, keys in domain_keywords.items():
            if any(k in text for k in keys):
                return domain
        return None

    prev_domain = detect(prev.lower())
    curr_domain = detect(curr.lower())

    if prev_domain and curr_domain and prev_domain != curr_domain:
        return False

    return True


# ----------------------------------------------------
# FOLLOW-UP NORMALIZATION (SAFE)
# ----------------------------------------------------

def _normalize_followup(prev: str, curr: str) -> Optional[str]:
    """
    Normalize ONLY if clarity improves.
    Returns None if rewrite is unsafe.
    """

    curr_l = curr.lower()

    # Pronoun resolution
    if any(p in curr_l for p in FOLLOWUP_PRONOUNS):
        return f"{curr.strip()} ({prev.strip()})"

    # Ultra-short vague continuation
    if len(curr.split()) <= 3:
        return f"{prev.strip()} — {curr.strip()}"

    return None


def _resolve_followup(
    message: str,
    last_user_message: Optional[str]
) -> tuple[str, bool]:

    # No history → not a follow-up
    if not last_user_message:
        return message, False

    # Hard topic reset → skip follow-up logic
    if _contains_topic_reset(message):
        logger.info(
            "FOLLOWUP_SKIPPED | reason=topic_reset | message=%s",
            message
        )
        return message, False

    # Linguistically not a follow-up
    if not _is_potential_followup(message):
        return message, False

    # Domain mismatch → unsafe
    if not _are_domains_compatible(last_user_message, message):
        logger.info(
            "FOLLOWUP_REJECTED | reason=domain_mismatch | prev=%s | curr=%s",
            last_user_message,
            message
        )
        return message, False

    normalized = _normalize_followup(
        prev=last_user_message,
        curr=message
    )

    # Normalization did not help
    if not normalized:
        return message, False

    logger.info(
        "FOLLOWUP_NORMALIZED | raw=%s | prev=%s | normalized=%s",
        message,
        last_user_message,
        normalized
    )

    return normalized, True


# ----------------------------------------------------
# CORE CHAT FLOW
# ----------------------------------------------------

def process_chat_stream_core(
    *,
    db: Session,
    user_id: int,
    message: str,
    conversation_id: int | None
) -> Generator[str, None, None]:

    try:
        conversation = None

        if conversation_id is not None:
            conversation = get_conversation(
                db,
                conversation_id=conversation_id,
                user_id=user_id
            )

        if conversation is None:
            conversation = create_conversation(
                db,
                user_id=user_id
            )

        # Emit metadata once
        yield f'__META__{json.dumps({"conversation_id": conversation.id})}\n'

        history = fetch_history(
            db,
            conversation_id=conversation.id,
            user_id=user_id
        )

        conversation_history = [
            {"role": m.role, "message": m.message}
            for m in history
        ]

        last_user_message = _get_last_user_message(conversation_history)

        normalized_message, is_followup = _resolve_followup(
            message=message,
            last_user_message=last_user_message
        )

        logger.info(
            "MESSAGE_CLASSIFICATION | followup=%s | normalized=%s",
            is_followup,
            normalized_message if is_followup else "N/A"
        )

        assistant_full_response = ""

        stream = ToolRouter.stream_response(
            message=normalized_message,
            conversation_history=conversation_history
        )

        for chunk in stream:
            assistant_full_response += chunk
            yield chunk

        assistant_full_response = post_process_response(
            assistant_full_response
        )

        save_messages(
            db,
            conversation_id=conversation.id,
            user_message=message,
            assistant_message=assistant_full_response
        )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("CHAT_STREAM_CORE_FAILED")
        raise