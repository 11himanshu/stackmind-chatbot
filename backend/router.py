from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from schemas import ChatMessage, ChatResponse, HealthResponse
from functions import (
    list_user_conversations,
    process_chat_message,
    get_conversation_history,
    delete_conversation
)
from dependencies import get_db
from llm_service import get_llm_response_stream

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(status="ok", message="Chatbot API is running")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", message="Service is healthy")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_message: ChatMessage,
    db: Session = Depends(get_db)
):
    try:
        user_id = 1  # TEMP until auth middleware

        conversation_id = (
            int(chat_message.conversation_id)
            if chat_message.conversation_id
            else None
        )

        bot_response, new_conversation_id = process_chat_message(
            db=db,
            user_id=user_id,
            message=chat_message.message,
            conversation_id=conversation_id
        )

        return ChatResponse(
            response=bot_response,
            conversation_id=str(new_conversation_id)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔥 STREAMING ENDPOINT
@router.post("/chat/stream")
async def chat_stream(
    chat_message: ChatMessage,
    db: Session = Depends(get_db)
):
    try:
        user_id = 1  # TEMP until auth middleware

        conversation_id = (
            int(chat_message.conversation_id)
            if chat_message.conversation_id
            else None
        )

        conversation_history = []
        if conversation_id:
            conversation_history = get_conversation_history(
                db=db,
                user_id=user_id,
                conversation_id=conversation_id
            )

        stream = get_llm_response_stream(
            message=chat_message.message,
            conversation_history=conversation_history
        )

        return StreamingResponse(
            stream,
            media_type="text/plain"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    messages = get_conversation_history(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id
    )

    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "messages": messages
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    deleted = delete_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "success"}

@router.get("/conversations")
async def list_conversations(
    user_id: int,
    db: Session = Depends(get_db)
):
    conversations = list_user_conversations(db=db, user_id=user_id)
    return conversations or []
