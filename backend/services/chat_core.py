import json
import re
from typing import Generator, Optional, Tuple
from sqlalchemy.orm import Session

from core.logger import get_logger
from services.tool_router import ToolRouter
from repositories.conversation_repo import get_conversation, create_conversation
from repositories.message_repo import fetch_history, save_messages
from tools.safety import post_process_response

logger = get_logger(__name__)

# ----------------------------------------------------
# FOLLOW-UP SIGNAL CONFIG (STRICT)
# ----------------------------------------------------

FOLLOWUP_PRONOUNS = {
    "it", "this", "that", "they", "them", "those", "he", "she", "above", "below"
}

FOLLOWUP_PHRASES = {
    "tell me more",
    "continue",
    "go on",
    "what about that",
    "explain that",
    "more on this",
    "next",
}

HARD_NEW_QUERY_PATTERNS = [
    r"https?://",
    r"\bcode\b",
    r"\bpython\b",
    r"\bjava\b",
    r"\bapi\b",
    r"\berror\b",
    r"\btable\b",
    r"\bexcel\b",
    r"\bfile\b",
]

# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------

def _get_last_user_message(history: list[dict]) -> Optional[str]:
    for msg in reversed(history):
        if msg["role"] == "user" and msg["message"].strip():
            return msg["message"]
    return None


def _contains_hard_new_query_signal(message: str) -> bool:
    msg = message.lower()
    return any(re.search(p, msg) for p in HARD_NEW_QUERY_PATTERNS)


def _is_potential_followup(message: str) -> bool:
    msg = message.lower().strip()

    if _contains_hard_new_query_signal(msg):
        return False

    if any(p in msg for p in FOLLOWUP_PHRASES):
        return True

    if any(re.search(rf"\b{p}\b", msg) for p in FOLLOWUP_PRONOUNS):
        return True

    return False


def _are_domains_compatible(prev: str, curr: str) -> bool:
    prev_l = prev.lower()
    curr_l = curr.lower()

    DOMAIN_KEYWORDS = {
        "politics": ["prime minister", "president", "government", "minister"],
        "weather": ["weather", "temperature", "rain"],
        "tech": ["code", "api", "bug", "python", "java"],
        "media": ["video", "youtube", "song", "movie"],
    }

    def detect_domain(text: str) -> Optional[str]:
        for domain, keys in DOMAIN_KEYWORDS.items():
            if any(k in text for k in keys):
                return domain
        return None

    prev_domain = detect_domain(prev_l)
    curr_domain = detect_domain(curr_l)

    if prev_domain and curr_domain and prev_domain != curr_domain:
        return False

    return True


# ----------------------------------------------------
# SUBJECT EXTRACTION
# ----------------------------------------------------

def _extract_subject(question: str) -> str:
    q = question.strip().rstrip("?")
    q = re.sub(
        r"^(who|what|when|where|why|how|tell me|explain)\s+",
        "",
        q,
        flags=re.IGNORECASE
    )
    return q.strip()


# ----------------------------------------------------
# FOLLOW-UP NORMALIZATION
# ----------------------------------------------------

def _normalize_followup(prev: str, curr: str) -> str:
    subject = _extract_subject(prev)
    curr_l = curr.lower()

    if any(k in curr_l for k in ["who", "when", "where", "why", "how"]):
        return f"{curr.strip()} about {subject}?"

    if any(k in curr_l for k in ["explain", "meaning", "details"]):
        return f"Explain {subject}."

    if any(k in curr_l for k in ["example", "examples"]):
        return f"Give examples related to {subject}."

    if any(k in curr_l for k in ["continue", "more"]):
        return f"Continue explaining {subject}."

    return f"{curr.strip()} (context: {subject})."


def _resolve_followup(
    message: str,
    last_user_message: Optional[str]
) -> Tuple[str, bool]:

    if not last_user_message:
        return message, False

    if not _is_potential_followup(message):
        return message, False

    if not _are_domains_compatible(last_user_message, message):
        logger.info(
            "FOLLOWUP_REJECTED | domain_mismatch | prev=%s | curr=%s",
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
            # ✅ FIX: keyword-only argument
            conversation = create_conversation(
                db,
                user_id=user_id
            )

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

        # ------------------------------------------------
        # TOOL ROUTER (STREAMING)
        # ------------------------------------------------
        stream = ToolRouter.stream_response(
            message=normalized_message,
            conversation_history=conversation_history
        )

        # Emit conversation id once
        yield f'__META__{json.dumps({"conversation_id": conversation.id})}\n'

        assistant_full_response = ""
        assistant_images: list[dict] = []

        for chunk in stream:
            if not chunk:
                continue

            stripped = chunk.lstrip()

            # ---------------- META FRAME ----------------
            if stripped.startswith("__META__"):
                yield chunk

                try:
                    meta = json.loads(stripped[len("__META__"):])

                    # Only collect assistant images
                    if isinstance(meta, dict) and "images" in meta:
                        assistant_images = meta["images"]

                except Exception:
                    logger.warning("META_PARSE_FAILED | chunk=%s", stripped)

                continue

            # ---------------- TEXT CHUNK ----------------
            assistant_full_response += chunk
            yield chunk

        save_messages(
            db,
            conversation_id=conversation.id,
            user_message=message,
            assistant_message=assistant_full_response,
            assistant_meta={
                "images": assistant_images
            } if assistant_images else None
        )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("CHAT_STREAM_CORE_FAILED")
        raise