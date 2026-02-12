from pydantic import BaseModel
from typing import Optional, List


# =========================================================
# Chat schemas
# =========================================================

class ChatMessage(BaseModel):
    message: str
    # 🔥 FIX:
    # conversation_id MUST be int
    # Backend, DB, and frontend all use integers
    conversation_id: Optional[int] = None

    # ✅ NEW (optional, backward compatible)
    attached_files: Optional[List[str]] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    message: str


# =========================================================
# Auth request schemas
# =========================================================

class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


# =========================================================
# Auth response schema (CRITICAL)
# ---------------------------------------------------------
# This MUST match what auth_router returns
# Otherwise FastAPI will DROP fields silently
# =========================================================

class AuthResponse(BaseModel):
    user_id: int
    username: str
    token: str
    message: str