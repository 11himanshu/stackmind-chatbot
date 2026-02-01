from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os

from db import SessionLocal

# =========================================================
# Database dependency
# =========================================================
def get_db():
    """
    Provides a SQLAlchemy session.
    Ensures session is always closed after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================================================
# Auth / JWT dependency
# =========================================================

# Must match your login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# 🔐 JWT configuration (must match token creation)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. "
        "Make sure it exists in your environment or .env file."
    )

def get_current_user_id(
    token: str = Depends(oauth2_scheme)
) -> int:
    """
    Validate JWT and extract user_id.

    Flow:
    - Read Authorization: Bearer <token>
    - Decode JWT
    - Extract user_id
    - Reject invalid or expired tokens
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        return user_id

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )