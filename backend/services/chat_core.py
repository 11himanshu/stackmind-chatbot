import json
import re
import os
from pathlib import Path
from typing import Generator, Optional, Tuple, List

from sqlalchemy.orm import Session

from core.logger import get_logger
from services.tool_router import ToolRouter
from repositories.conversation_repo import get_conversation, create_conversation
from repositories.message_repo import fetch_history, save_messages
from tools.safety import post_process_response
from files.files_models import UploadedFile

# DOCUMENT INTELLIGENCE
from document_intelligence.pipelines.ingest_pipeline import IngestPipeline
from document_intelligence.cache.index_cache import DocumentIndexCache

logger = get_logger(__name__)

# ----------------------------------------------------
# FOLLOW-UP SIGNAL CONFIG
# ----------------------------------------------------

FOLLOWUP_PRONOUNS = {
    "it", "this", "that", "they", "them", "those", "above", "below"
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
    r"\bexcel\b",
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


def _resolve_followup(
    *,
    message: str,
    last_user_message: Optional[str]
) -> Tuple[str, bool]:

    normalized = message.strip()
    is_followup = False

    if last_user_message and _is_potential_followup(normalized):
        is_followup = True

    return normalized, is_followup


# ----------------------------------------------------
# FILE RESOLUTION
# ----------------------------------------------------

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads")).resolve()

def _resolve_attached_files(
    *,
    db: Session,
    user_id: int,
    file_ids: List[str]
) -> List[dict]:

    if not file_ids:
        return []

    records = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.file_id.in_(file_ids),
            UploadedFile.user_id == user_id
        )
        .all()
    )

    resolved = []
    for r in records:
        resolved.append({
            "file_id": r.file_id,
            "filename": r.original_filename,
            "mime_type": r.mime_type,
            "size_bytes": r.size_bytes,
            "path": str(UPLOAD_DIR / r.storage_path),
        })

    logger.info("FILES_RESOLVED | count=%d", len(resolved))
    return resolved


# ----------------------------------------------------
# CORE CHAT FLOW
# ----------------------------------------------------

def process_chat_stream_core(
    *,
    db: Session,
    user_id: int,
    message: str,
    conversation_id: int | None,
    attached_files: List[str] | None = None
) -> Generator[str, None, None]:

    try:
        # --------------------------------------------
        # Conversation bootstrap
        # --------------------------------------------

        conversation = None
        if conversation_id is not None:
            conversation = get_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id
            )

        if conversation is None:
            conversation = create_conversation(
                db=db,
                user_id=user_id
            )

        history = fetch_history(
            db=db,
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

        # --------------------------------------------
        # DOCUMENT INGEST / RESTORE
        # --------------------------------------------

        ingest = IngestPipeline()
        cache = DocumentIndexCache()
        document_index = None

        resolved_files = _resolve_attached_files(
            db=db,
            user_id=user_id,
            file_ids=attached_files or []
        )

        # Case 1: New document attached
        for f in resolved_files:
            if f["filename"].lower().endswith(".pdf"):
                doc_id = f["file_id"]

                if not cache.exists(doc_id):
                    document_index = ingest.ingest(
                        document_id=doc_id,
                        file_path=f["path"],
                    )
                else:
                    document_index = cache.get(doc_id)

                # 🔐 store conversation → document mapping in cache
                cache.set_active_document(conversation.id, doc_id)

                logger.info(
                    "CHAT_ACTIVE_DOCUMENT_SET | conversation_id=%s | document_id=%s",
                    conversation.id,
                    doc_id,
                )
                break

        # Case 2: Follow-up without attachment
        if document_index is None:
            active_doc_id = cache.get_active_document(conversation.id)

            if active_doc_id:
                logger.info(
                    "CHAT_ACTIVE_DOCUMENT_RESTORED | conversation_id=%s | document_id=%s",
                    conversation.id,
                    active_doc_id,
                )

                if cache.exists(active_doc_id):
                    document_index = cache.get(active_doc_id)

        # --------------------------------------------
        # FINAL ROUTING LOGS
        # --------------------------------------------

        logger.info(
            "CHAT_DOC_CONTEXT_CHECK | attached_files=%d | is_followup=%s | conversation_id=%s",
            len(attached_files or []),
            is_followup,
            conversation.id,
        )

        logger.info(
            "CHAT_MODE_SELECTED | mode=%s | document_id=%s",
            "document" if document_index else "chat",
            document_index.document_id if document_index else None,
        )

        # --------------------------------------------
        # TOOL ROUTER
        # --------------------------------------------

        stream = ToolRouter.stream_response(
            message=normalized_message,
            conversation_history=conversation_history,
            document_index=document_index
        )

        yield f'__META__{json.dumps({"conversation_id": conversation.id})}\n'

        assistant_full_response = ""

        for chunk in stream:
            if not chunk:
                continue

            if chunk.lstrip().startswith("__META__"):
                yield chunk
                continue

            assistant_full_response += chunk
            yield chunk

        assistant_full_response = post_process_response(assistant_full_response)

        save_messages(
            db=db,
            conversation_id=conversation.id,
            user_message=message,
            assistant_message=assistant_full_response,
            assistant_meta={
                "files": [
                    {"file_id": f["file_id"], "filename": f["filename"]}
                    for f in resolved_files
                ]
            } if resolved_files else None
        )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("CHAT_STREAM_CORE_FAILED")
        raise