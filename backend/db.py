import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

from core.logger import get_logger


logger = get_logger(__name__)

# ============================================================
# Load .env explicitly (SAFE for local + production)
# ============================================================
try:
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
    logger.info("ENV_LOADED | Loaded environment variables from %s", env_path)
except Exception:
    logger.exception("ENV_LOAD_FAILED | Failed to load .env file")
    raise


def _engine_options(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
        }

    return {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 1800,
        "connect_args": {
            "sslmode": "require",
            "connect_timeout": 10,
        },
    }


def _create_checked_engine(database_url: str):
    db_engine = create_engine(database_url, **_engine_options(database_url))
    with db_engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return db_engine


PRIMARY_DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_DATABASE_URL = os.getenv("SQLITE_DATABASE_URL", "sqlite:////tmp/stackmind.db")

try:
    if PRIMARY_DATABASE_URL:
        logger.info("DB_CONFIG_OK | DATABASE_URL loaded successfully")
        try:
            engine = _create_checked_engine(PRIMARY_DATABASE_URL)
            DATABASE_URL = PRIMARY_DATABASE_URL
            logger.info("DB_ENGINE_READY | Primary database engine created")
        except Exception:
            logger.exception("DB_PRIMARY_UNAVAILABLE | Falling back to SQLite")
            engine = _create_checked_engine(SQLITE_DATABASE_URL)
            DATABASE_URL = SQLITE_DATABASE_URL
            logger.info("DB_ENGINE_READY | SQLite fallback database engine created")
    else:
        logger.warning("DB_CONFIG_MISSING | DATABASE_URL not set; using SQLite fallback")
        engine = _create_checked_engine(SQLITE_DATABASE_URL)
        DATABASE_URL = SQLITE_DATABASE_URL
        logger.info("DB_ENGINE_READY | SQLite fallback database engine created")
except Exception:
    logger.exception("DB_ENGINE_FAILED | Failed to create any database engine")
    raise


# ============================================================
# Session factory
# ============================================================
try:
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    logger.info("DB_SESSION_READY | SessionLocal configured")
except Exception:
    logger.exception("DB_SESSION_FAILED | Failed to configure SessionLocal")
    raise


# ============================================================
# Declarative Base
# ============================================================
try:
    Base = declarative_base()
    logger.debug("DB_BASE_READY | Declarative Base initialized")
except Exception:
    logger.exception("DB_BASE_FAILED | Failed to initialize Declarative Base")
    raise
