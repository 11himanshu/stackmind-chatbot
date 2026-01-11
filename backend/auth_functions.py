import logging
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models.users import User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    logger.info("Hashing password")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.info("Verifying password")
    return pwd_context.verify(plain_password, hashed_password)


def register_user(db: Session, username: str, password: str) -> bool:
    """
    Register a new user in DB.
    Returns False if username already exists.
    """
    logger.info(f"Attempting to register user: {username}")

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        logger.info(f"Registration failed: username already exists -> {username}")
        return False

    user = User(
        username=username,
        password_hash=hash_password(password)
    )

    db.add(user)
    db.commit()

    logger.info(f"User registered successfully: {username}")
    return True


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