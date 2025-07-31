"""
Authentication error handling.
"""

from enum import Enum

from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import JWTError
from pydantic import BaseModel


class AuthErrorCode(str, Enum):
    """Authentication error codes."""

    INVALID_TOKEN = "invalid_token"
    EXPIRED_TOKEN = "expired_token"
    MISSING_TOKEN = "missing_token"
    INVALID_ISSUER = "invalid_issuer"
    INVALID_AUDIENCE = "invalid_audience"
    INSUFFICIENT_AAL = "insufficient_aal"
    ANONYMOUS_NOT_ALLOWED = "anonymous_not_allowed"


class AuthError(BaseModel):
    """Authentication error response model."""

    error: AuthErrorCode
    error_description: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "invalid_token",
                "error_description": "The access token provided is invalid",
            }
        }
    }


# Exception handler for JWT errors
async def jwt_exception_handler(request: Request, exc: JWTError) -> JSONResponse:
    """Handle JWT validation errors."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=AuthError(
            error=AuthErrorCode.INVALID_TOKEN, error_description=str(exc)
        ).model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )
