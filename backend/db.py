import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

# Load .env explicitly
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

logger.info(f"Loading environment variables from: {env_path}")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.info("DATABASE_URL not found in environment")
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

logger.info("DATABASE_URL loaded successfully")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

logger.info("SQLAlchemy engine created")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

logger.info("SessionLocal configured")

Base = declarative_base()

logger.info("Declarative Base initialized")