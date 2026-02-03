import os
from pathlib import Path

from sqlalchemy import create_engine
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


# ============================================================
# Database URL
# ============================================================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error(
        "DB_CONFIG_ERROR | DATABASE_URL not found in environment"
    )
    raise RuntimeError(
        "DB_CONFIG_ERROR | DATABASE_URL is not set. Check your .env file."
    )

logger.info("DB_CONFIG_OK | DATABASE_URL loaded successfully")


# ============================================================
# SQLAlchemy Engine (SUPABASE-SAFE CONFIG)
# ============================================================
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,      # auto-recover dead connections
        pool_size=5,             # safe default for Supabase
        max_overflow=10,         # prevent connection storms
        pool_recycle=1800,       # recycle every 30 min
        connect_args={
            "sslmode": "require"  # required for Supabase
        }
    )
    logger.info("DB_ENGINE_READY | SQLAlchemy engine created")
except Exception:
    logger.exception("DB_ENGINE_FAILED | Failed to create SQLAlchemy engine")
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