from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from schemas import UserRegister, UserLogin, AuthResponse
from dependencies import get_db
from auth_functions import register_user, authenticate_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=AuthResponse)
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    created = register_user(db, user.username, user.password)
    if not created:
        raise HTTPException(status_code=400, detail="Username already exists")

    return AuthResponse(
        username=user.username,
        message="registered"
    )


@auth_router.post("/login", response_model=AuthResponse)
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthResponse(
        username=db_user.username,
        message="logged_in"
    )