print("=== MAIN.PY STARTING ===", flush=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router
from auth_router import auth_router

print("=== IMPORTS DONE ===", flush=True)

app = FastAPI(
    title="Chatbot API",
    description="A basic FastAPI chatbot outer layer with auth",
    version="1.1.0",
)

print("=== FASTAPI APP CREATED ===", flush=True)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("=== CORS ADDED ===", flush=True)

# Include routers
app.include_router(router)
print("=== ROUTER INCLUDED ===", flush=True)

app.include_router(auth_router)
print("=== AUTH ROUTER INCLUDED ===", flush=True)