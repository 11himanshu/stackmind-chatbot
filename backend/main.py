from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logger import get_logger
from db import Base, engine
from router import router
from auth_router import auth_router


logger = get_logger(__name__)

# ---------------------------------------------------------
# Environment loading
# ---------------------------------------------------------
try:
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
    logger.info("ENV_LOADED | Environment variables loaded successfully")
except Exception as e:
    logger.exception("ENV_LOAD_FAILED | Failed to load environment variables")
    raise


# ---------------------------------------------------------
# Database initialization
# ---------------------------------------------------------
try:
    logger.debug("DB_INIT_START | Ensuring database tables")
    Base.metadata.create_all(bind=engine)
    logger.info("DB_INIT_SUCCESS | Database tables ensured")
except Exception as e:
    logger.exception("DB_INIT_FAILED | Database initialization failed")
    raise


# ---------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------
try:
    app = FastAPI(
        title="Chatbot API",
        description="A basic FastAPI chatbot outer layer with auth",
        version="1.1.0",
    )
    logger.info("APP_INIT_SUCCESS | FastAPI app created")
except Exception as e:
    logger.exception("APP_INIT_FAILED | Failed to initialize FastAPI app")
    raise


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # tighten later
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS_ENABLED | CORS middleware added")
except Exception as e:
    logger.exception("CORS_FAILED | Failed to configure CORS")
    raise


# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------
try:
    app.include_router(router)
    logger.info("ROUTER_ATTACHED | Main router included")

    app.include_router(auth_router)
    logger.info("ROUTER_ATTACHED | Auth router included")

except Exception as e:
    logger.exception("ROUTER_ATTACH_FAILED | Failed to attach routers")
    raise