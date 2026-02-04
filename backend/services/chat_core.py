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
# FOLLOW-UP DETECTION CONFIG
# ----------------------------------------------------

FOLLOWUP_PRONOUNS = {
    "it", "this", "that", "he", "she", "they",
    "him", "her", "them", "there", "those"
}

VAGUE_CONTINUATIONS = {
    "and", "then", "what about", "tell me more",
    "continue", "next", "now", "after that"
}

SHORT_QUERY_WORD_COUNT = 5


# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------

def _get_last_user_message(history: list[dict]) -> Optional[str]:
    for msg in reversed(history):
        if msg["role"] == "user" and msg["message"].strip():
            return msg["message"]
    return None


def _is_potential_followup(message: str) -> bool:
    msg = message.lower().strip()

    if len(msg.split()) <= SHORT_QUERY_WORD_COUNT:
        return True

    if any(re.search(rf"\b{p}\b", msg) for p in FOLLOWUP_PRONOUNS):
        return True

    if any(msg.startswith(v) for v in VAGUE_CONTINUATIONS):
        return True

    return False


def _are_domains_compatible(prev: str, curr: str) -> bool:
    """
    Very soft safety gate.
    Only blocks obvious cross-topic jumps.
    """

    prev_l = prev.lower()
    curr_l = curr.lower()

    domain_keywords = {
        "sports": ["match", "score", "ipl", "t20", "odi"],
        "music": ["song", "lyrics", "album", "track"],
        "tech": ["code", "error", "api", "bug"],
        "news": ["news", "headline", "breaking"],
    }

    def detect_domain(text: str) -> Optional[str]:
        for domain, keys in domain_keywords.items():
            if any(k in text for k in keys):
                return domain
        return None

    prev_domain = detect_domain(prev_l)
    curr_domain = detect_domain(curr_l)

    if prev_domain and curr_domain and prev_domain != curr_domain:
        return False

    return True


# ----------------------------------------------------
# SUBJECT EXTRACTION (KEY FIX)
# ----------------------------------------------------

def _extract_subject(question: str) -> str:
    """
    Extract the core subject of a question.

    Examples:
    - "Who sang Tere Liye?" -> "Tere Liye"
    - "What is Python?" -> "Python"
    - "When did Virat retire?" -> "Virat retire"
    """

    q = question.strip().rstrip("?")

    # Remove common leading patterns
    q = re.sub(
        r"^(who|what|when|where|why|how|can you|could you|please|tell me)\s+",
        "",
        q,
        flags=re.IGNORECASE
    )

    return q.strip()


# ----------------------------------------------------
# FOLLOW-UP NORMALIZATION (PRODUCTION GRADE)
# ----------------------------------------------------

def _normalize_followup(prev: str, curr: str) -> str:
    """
    Convert follow-up into ONE standalone question
    without hardcoding any domain logic.
    """

    subject = _extract_subject(prev)
    curr_l = curr.lower()

    # Question intent mapping
    if any(k in curr_l for k in ["who", "when", "where", "why", "how"]):
        return f"{curr.strip()} about {subject}?"

    if any(k in curr_l for k in ["explain", "meaning", "details"]):
        return f"Explain {subject}."

    if any(k in curr_l for k in ["example", "examples"]):
        return f"Give examples related to {subject}."

    if any(k in curr_l for k in ["continue", "more", "next"]):
        return f"Continue explaining {subject}."

    if any(k in curr_l for k in ["line", "lines", "points"]):
        return f"Give a few key points about {subject}."

    # Safe generic fallback
    return f"{curr.strip()} regarding {subject}."


def _resolve_followup(
    message: str,
    last_user_message: Optional[str]
) -> tuple[str, bool]:

    if not last_user_message:
        return message, False

    if not _is_potential_followup(message):
        return message, False

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
            "MESSAGE_CLASSIFICATION | followup=%s | normalized_message=%s",
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