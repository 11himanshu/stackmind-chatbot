from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.logger import get_logger
from models.conversations import Conversation
from schemas import ChatMessage, HealthResponse
from services.chat_service import ChatService
from functions import (
    list_user_conversations,
    get_conversation_history,
    delete_conversation
)
from dependencies import get_db, get_current_user_id


logger = get_logger(__name__)
router = APIRouter()


# ============================================================
# Health endpoints (NO AUTH)
# ============================================================

@router.get("/", response_model=HealthResponse)
async def root():
    logger.debug("HEALTH_ROOT_CHECK")
    return HealthResponse(
        status="ok",
        message="Chatbot API is running"
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    logger.debug("HEALTH_CHECK")
    return HealthResponse(
        status="ok",
        message="Service is healthy"
    )


# ============================================================
# CHAT ENDPOINT (STREAMING)
# ============================================================

@router.post("/chat")
async def chat(
    chat_message: ChatMessage,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    logger.info(
        "CHAT_REQUEST_RECEIVED | user_id=%s | conversation_id=%s | attached_files=%s",
        user_id,
        chat_message.conversation_id,
        chat_message.attached_files
    )

    try:
        conversation_id = (
            int(chat_message.conversation_id)
            if chat_message.conversation_id
            else None
        )

        stream = ChatService.stream_chat(
            db=db,
            user_id=user_id,
            message=chat_message.message,
            conversation_id=conversation_id,
            attached_files=chat_message.attached_files
        )

        logger.debug(
            "CHAT_STREAM_STARTED | user_id=%s | conversation_id=%s",
            user_id,
            conversation_id
        )

        return StreamingResponse(
            stream,
            media_type="text/plain"
        )

    except ValueError:
        logger.warning(
            "CHAT_VALIDATION_FAILED | user_id=%s",
            user_id
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid chat request"
        )

    except Exception:
        logger.exception(
            "CHAT_STREAM_FAILED | user_id=%s",
            user_id
        )
        raise HTTPException(
            status_code=500,
            detail="Chat processing failed"
        )


# ============================================================
# CONVERSATION HISTORY
# ============================================================

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    logger.debug(
        "CONVERSATION_FETCH | user_id=%s | conversation_id=%s",
        user_id,
        conversation_id
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
        logger.warning(
            "CONVERSATION_NOT_FOUND | user_id=%s | conversation_id=%s",
            user_id,
            conversation_id
        )
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    messages = get_conversation_history(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id
    )

    return {
        "conversation_id": conversation_id,
        "messages": messages
    }


# ============================================================
# LIST CONVERSATIONS
# ============================================================

@router.get("/conversations")
async def list_conversations(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    logger.debug(
        "CONVERSATION_LIST | user_id=%s",
        user_id
    )

    conversations = list_user_conversations(
        db=db,
        user_id=user_id
    )

    return conversations or []


# ============================================================
# DELETE CONVERSATION
# ============================================================

@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    logger.info(
        "CONVERSATION_DELETE_REQUEST | user_id=%s | conversation_id=%s",
        user_id,
        conversation_id
    )

    deleted = delete_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id
    )

    if not deleted:
        logger.warning(
            "CONVERSATION_DELETE_NOT_FOUND | user_id=%s | conversation_id=%s",
            user_id,
            conversation_id
        )
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    logger.info(
        "CONVERSATION_DELETED | user_id=%s | conversation_id=%s",
        user_id,
        conversation_id
    )

    return {"status": "success"}