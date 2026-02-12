from sqlalchemy.orm import Session

from core.logger import get_logger
from functions import process_chat_stream


logger = get_logger(__name__)


class ChatService:
    """
    Chat orchestration service.

    This is the boundary between:
    - API layer (routers)
    - LLM / tools / persistence logic

    For now, it delegates to process_chat_stream.
    Later, process_chat_stream will be decomposed and absorbed here.
    """

    @staticmethod
    def stream_chat(
        *,
        db: Session,
        user_id: int,
        message: str,
        conversation_id: int | None,
        attached_files: list[str] | None = None
    ):
        logger.info(
            "CHAT_SERVICE_START | user_id=%s | conversation_id=%s | attached_files=%s",
            user_id,
            conversation_id,
            attached_files
        )

        try:
            stream = process_chat_stream(
                db=db,
                user_id=user_id,
                message=message,
                conversation_id=conversation_id,
                attached_files=attached_files
            )

            logger.debug(
                "CHAT_SERVICE_STREAM_READY | user_id=%s | conversation_id=%s",
                user_id,
                conversation_id
            )

            return stream

        except Exception:
            logger.exception(
                "CHAT_SERVICE_FAILED | user_id=%s | conversation_id=%s",
                user_id,
                conversation_id
            )
            raise