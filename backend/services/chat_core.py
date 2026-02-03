import json
from typing import Generator
from sqlalchemy.orm import Session

from core.logger import get_logger
from services.tool_router import ToolRouter
from repositories.conversation_repo import get_conversation, create_conversation
from repositories.message_repo import fetch_history, save_messages
from tools.safety import post_process_response


logger = get_logger(__name__)


def process_chat_stream_core(
    *,
    db: Session,
    user_id: int,
    message: str,
    conversation_id: int | None
) -> Generator[str, None, None]:
    """
    Core streaming chat flow.

    Guarantees:
    - One conversation per session
    - Metadata emitted once
    - Streaming response
    - Messages persisted after stream completes
    """

    try:
        # ----------------------------------------------------
        # Resolve conversation
        # ----------------------------------------------------
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

        # ----------------------------------------------------
        # Emit metadata (frontend strips this)
        # ----------------------------------------------------
        yield f'__META__{json.dumps({"conversation_id": conversation.id})}\n'

        # ----------------------------------------------------
        # Fetch history for context
        # ----------------------------------------------------
        history = fetch_history(
            db,
            conversation_id=conversation.id,
            user_id=user_id
        )

        conversation_history = [
            {"role": m.role, "message": m.message}
            for m in history
        ]

        # ----------------------------------------------------
        # Route + stream response
        # ----------------------------------------------------
        assistant_full_response = ""

        stream = ToolRouter.stream_response(
            message=message,
            conversation_history=conversation_history
        )

        for chunk in stream:
            assistant_full_response += chunk
            yield chunk

        # ----------------------------------------------------
        # Safety / post-processing
        # ----------------------------------------------------
        assistant_full_response = post_process_response(
            assistant_full_response
        )

        # ----------------------------------------------------
        # Persist messages
        # ----------------------------------------------------
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