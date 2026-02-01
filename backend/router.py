from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from models.conversations import Conversation
from models.message import Message

from schemas import ChatMessage, HealthResponse
from functions import (
    process_chat_stream,
    list_user_conversations,
    get_conversation_history,
    delete_conversation
)
from dependencies import get_db, get_current_user_id

router = APIRouter()

# ============================================================
# Health endpoints (NO AUTH)
# ============================================================

@router.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="ok",
        message="Chatbot API is running"
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        message="Service is healthy"
    )


# ============================================================
# CHAT ENDPOINT (STREAMING + DB SAVE)
# ------------------------------------------------------------
# ✔ ONE endpoint
# ✔ ONE LLM call
# ✔ Streams response
# ✔ Saves messages AFTER stream completes
# ✔ Creates conversation ONLY if conversation_id is None
# ============================================================

@router.post("/chat")
async def chat(
    chat_message: ChatMessage,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Streaming chat endpoint.

    FLOW:
    1. Validate user via JWT
    2. Create / reuse conversation
    3. Stream LLM response to client
    4. Persist user + assistant messages after streaming

    This is the ONLY chat endpoint used by frontend.
    """

    try:
        conversation_id = (
            int(chat_message.conversation_id)
            if chat_message.conversation_id
            else None
        )

        stream = process_chat_stream(
            db=db,
            user_id=user_id,
            message=chat_message.message,
            conversation_id=conversation_id
        )

        return StreamingResponse(
            stream,
            media_type="text/plain"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# CONVERSATION HISTORY (AUTH REQUIRED)
# ------------------------------------------------------------
# Used when:
# - User clicks a conversation in sidebar
# - Page refresh
# ============================================================

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    messages = get_conversation_history(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id
    )

    if not messages:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "conversation_id": conversation_id,
        "messages": messages
    }


# ============================================================
# LIST CONVERSATIONS (SIDEBAR)
# ============================================================

@router.get("/conversations")
async def list_conversations(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    conversations = list_user_conversations(
        db=db,
        user_id=user_id
    )

    return conversations or []


@router.delete("/conversations/{conversation_id}", tags=["conversations"])
async def delete_conversation_endpoint(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    deleted = delete_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {"status": "success"}