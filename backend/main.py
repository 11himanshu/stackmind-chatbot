print("=== MAIN.PY STARTING ===", flush=True)

from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------
# Load environment variables EARLY
# ---------------------------------------------------------
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

print("=== ENV LOADED ===", flush=True)

# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import Base, engine          # 🔥 REQUIRED FOR TABLE CREATION
from router import router
from auth_router import auth_router

print("=== IMPORTS DONE ===", flush=True)

# ---------------------------------------------------------
# 🔥 CREATE DATABASE TABLES (CRITICAL FIX)
# This creates tables ONLY if they do not already exist
# Safe for production
# ---------------------------------------------------------
Base.metadata.create_all(bind=engine)

print("=== DATABASE TABLES ENSURED ===", flush=True)

# ---------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------
app = FastAPI(
    title="Chatbot API",
    description="A basic FastAPI chatbot outer layer with auth",
    version="1.1.0",
)

print("=== FASTAPI APP CREATED ===", flush=True)

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # OK for now (lock later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("=== CORS ADDED ===", flush=True)

# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------
app.include_router(router)
print("=== ROUTER INCLUDED ===", flush=True)

app.include_router(auth_router)
print("=== AUTH ROUTER INCLUDED ===", flush=True)