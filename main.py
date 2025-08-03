from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError

from src.api.endpoints import auth, plans
from src.core.auth import jwt_exception_handler
from src.core.settings import settings

app = FastAPI(
    title="Slow Burn API",
    description="Backend API for the AI Fitness Companion application",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"],
)

# Add exception handlers
app.add_exception_handler(JWTError, jwt_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(plans.router)


@app.get("/")
async def root() -> dict[str, Any]:
    return {"message": "Hello World", "app": "Slow Burn AI Fitness Companion"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
