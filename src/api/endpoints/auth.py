"""
Authentication endpoints for testing JWT validation.
"""

from typing import Any

from fastapi import APIRouter, Depends

from src.core.auth import JWTPayload, optional_auth, require_auth

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/me")
async def get_current_user_info(
    jwt_payload: JWTPayload = Depends(require_auth),
) -> dict[str, Any]:
    """
    Get current authenticated user information.

    Requires a valid JWT token in the Authorization header.
    """
    return {
        "user_id": jwt_payload.user_id,
        "email": jwt_payload.email,
        "phone": jwt_payload.phone,
        "role": jwt_payload.role,
        "session_id": jwt_payload.session_id,
        "aal": jwt_payload.aal,
        "provider": jwt_payload.provider,
        "is_anonymous": jwt_payload.is_anonymous,
    }


@router.get("/public")
async def public_endpoint(
    jwt_payload: JWTPayload | None = Depends(optional_auth),
) -> dict[str, str]:
    """
    Public endpoint with optional authentication.

    Returns different messages based on authentication status.
    """
    if jwt_payload:
        return {"message": f"Hello, {jwt_payload.email or 'authenticated user'}!"}
    return {"message": "Hello, anonymous!"}
