from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError

from src.api.endpoints import auth, plans
from src.core.auth import jwt_exception_handler
from src.core.settings import settings

app = FastAPI(
    title="Slow Burn API",
    description="""
## AI Fitness Companion Backend API

The Slow Burn API provides a comprehensive backend for an AI-powered fitness companion application.
Users develop a deepening relationship with an AI companion as they log workouts and achieve their fitness goals.

### Key Features:
- 🔐 **JWT Authentication** via Supabase
- 💪 **Workout Plan Management** with versioning support
- 🏋️ **Exercise Library** (coming in Sprint 5)
- 🤖 **AI Chat Integration** with Google Gemini (coming in Sprint 6)
- 📈 **Progress Tracking** and affinity scoring

### Current Sprint: 3 (Plan Creation)
For more details, see the [project documentation](https://github.com/yourusername/slow-burn).
    """,
    version="0.1.0",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication endpoints for JWT validation",
        },
        {
            "name": "plans",
            "description": "Workout plan CRUD operations with immutable versioning",
        },
        {
            "name": "workouts",
            "description": "Workout session logging and tracking (coming in Sprint 4)",
        },
        {
            "name": "exercises",
            "description": "Exercise library and search (coming in Sprint 5)",
        },
        {
            "name": "chat",
            "description": "AI companion chat interface (coming in Sprint 6)",
        },
    ],
    docs_url="/docs",
    redoc_url="/redoc",
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
