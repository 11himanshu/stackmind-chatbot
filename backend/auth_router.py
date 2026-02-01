from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from schemas import UserRegister, UserLogin, AuthResponse
from dependencies import get_db
from auth_functions import (
    register_user,
    authenticate_user,
    create_access_token
)

# =========================================================
# Auth Router
# ---------------------------------------------------------
# Responsibilities:
# - User registration
# - User login
# - JWT token issuance
#
# IMPORTANT:
# - JWT is returned to frontend
# - Frontend stores token in localStorage
# - All protected routes rely on this token
# =========================================================

auth_router = APIRouter(prefix="/auth", tags=["auth"])


# =========================================================
# Register Endpoint
# ---------------------------------------------------------
# - Creates a new user
# - Immediately issues a JWT
# - Returns token + user info
# =========================================================
@auth_router.post("/register", response_model=AuthResponse)
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user and return JWT.
    """

    # Attempt to create user
    db_user = register_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # 🔐 Create JWT token for new user
    token = create_access_token(db_user.id)

    # ✅ Return token + user info
    return AuthResponse(
        user_id=db_user.id,
        username=db_user.username,
        token=token,
        message="registered"
    )


# =========================================================
# Login Endpoint
# ---------------------------------------------------------
# - Verifies username + password
# - Issues JWT if valid
# - Returns token + user info
# =========================================================
@auth_router.post("/login", response_model=AuthResponse)
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT.
    """

    # Validate credentials
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    # 🔐 Create JWT token
    token = create_access_token(db_user.id)

    # ✅ Return token + user info
    return AuthResponse(
        user_id=db_user.id,
        username=db_user.username,
        token=token,
        message="logged_in"
    )