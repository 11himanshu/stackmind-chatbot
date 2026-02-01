import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from dotenv import load_dotenv
import os

load_dotenv()

from models.users import User

logger = logging.getLogger(__name__)

# =========================================================
# Password hashing (bcrypt-safe, Python 3.13 safe)
# =========================================================
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def _normalize_password(password: str) -> bytes:
    """
    bcrypt has a strict 72-byte limit.
    We MUST normalize passwords to avoid runtime crashes.
    This is standard practice and does NOT weaken security.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes


def hash_password(password: str) -> str:
    logger.info("Hashing password")
    password_bytes = _normalize_password(password)
    return pwd_context.hash(password_bytes)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.info("Verifying password")
    password_bytes = _normalize_password(plain_password)
    return pwd_context.verify(password_bytes, hashed_password)

# =========================================================
# JWT config
# =========================================================
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in environment variables")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# =========================================================
# JWT helpers
# =========================================================
def create_access_token(user_id: int) -> str:
    """
    Create JWT access token.
    Stores user_id inside token payload.
    """
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# =========================================================
# User registration
# =========================================================
def register_user(db: Session, username: str, password: str):
    """
    Register a new user.
    Returns User object or None if username exists.
    """
    logger.info(f"Attempting to register user: {username}")

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        logger.info(f"Registration failed: username exists -> {username}")
        return None

    user = User(
        username=username,
        password_hash=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User registered successfully: {username}")
    return user

# =========================================================
# User authentication
# =========================================================
def authenticate_user(db: Session, username: str, password: str):
    """
    Authenticate user.
    Returns User object if valid, else None.
    """
    logger.info(f"Authenticating user: {username}")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.info(f"Authentication failed: user not found -> {username}")
        return None

    if not verify_password(password, user.password_hash):
        logger.info(f"Authentication failed: invalid password -> {username}")
        return None

    logger.info(f"Authentication successful: {username}")
    return user