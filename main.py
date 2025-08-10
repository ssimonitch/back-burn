import tomllib
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from jose import JWTError

from src.api.endpoints import auth, plans, workouts
from src.core.auth import jwt_exception_handler
from src.core.settings import settings


def _get_project_version() -> str:
    """Read project version from pyproject.toml, fallback to default."""
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        # main.py is at repo root; ensure correct path resolution
        if not pyproject_path.exists():
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version", "0.1.0")
    except Exception:
        return "0.1.0"


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

### Current Sprint: 4 (Workout Logging)
For more details, see the [project documentation](https://github.com/yourusername/slow-burn).
    """,
    version=_get_project_version(),
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
            "description": "Workout session logging and tracking",
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
)

# Add exception handlers
app.add_exception_handler(JWTError, jwt_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(plans.router)
app.include_router(workouts.router)


def custom_openapi() -> dict[str, Any]:
    """Customize OpenAPI schema: add servers, set global security, and mark public endpoint as unauthenticated."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add servers block for tooling/codegen
    server_url = f"http://{settings.api_host}:{settings.api_port}"
    schema["servers"] = [
        {"url": server_url, "description": "Default API server"},
    ]

    # Ensure security schemes exist and set global security requirement
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["security"] = [{"SupabaseJWTBearer": []}]

    # Make /api/v1/auth/public explicitly unauthenticated
    try:
        public_get = schema["paths"]["/api/v1/auth/public"]["get"]
        public_get["security"] = []
    except Exception:
        # If path not present, ignore
        pass

    # Also allow unauthenticated access for root and health endpoints
    for path in ["/", "/health"]:
        try:
            for method in list(schema["paths"][path].keys()):
                if method.lower() in {"get", "post", "put", "delete", "patch"}:
                    schema["paths"][path][method]["security"] = []
        except Exception:
            pass

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[assignment]


@app.get("/")
async def root() -> dict[str, Any]:
    return {"message": "Hello World", "app": "Slow Burn AI Fitness Companion"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
