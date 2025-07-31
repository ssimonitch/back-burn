"""
FastAPI authentication dependencies.
"""

from typing import Any

from fastapi import Depends, HTTPException, status

from src.core.settings import settings
from src.core.utils import get_supabase_client
from supabase import Client

from .jwt_bearer import SupabaseJWTBearer
from .models import JWTPayload, SupabaseUser

# Initialize JWT Bearer with settings
_jwt_bearer = SupabaseJWTBearer(
    supabase_url=settings.supabase_url,
    supabase_anon_key=settings.supabase_anon_key,
    jwt_algorithm=settings.jwt_algorithm,
    jwt_secret=settings.jwt_secret,
)


async def _extract_jwt_payload(
    token_data: dict[str, Any] = Depends(_jwt_bearer),
) -> JWTPayload:
    """Extract JWT payload from validated token."""
    # Extract provider from app_metadata
    app_metadata = token_data.get("app_metadata", {})
    provider = app_metadata.get("provider")

    jwt_payload = JWTPayload(
        user_id=token_data["sub"],  # JWTPayload uses alias="sub" for user_id
        email=token_data.get("email"),
        phone=token_data.get("phone"),
        role=token_data.get("role", "authenticated"),
        session_id=token_data.get(
            "session_id", ""
        ),  # Provide default for required field
        aal=token_data.get("aal", "aal1"),
        provider=provider,
        is_anonymous=token_data.get("is_anonymous", False),
    )

    # Set the private attribute with the raw token
    jwt_payload._raw_token = token_data.get("_raw_token", "")

    return jwt_payload


# Reusable dependencies
async def require_auth(
    jwt_payload: JWTPayload = Depends(_extract_jwt_payload),
) -> JWTPayload:
    """Require authenticated user - returns JWT payload."""
    return jwt_payload


async def optional_auth(
    token_data: dict[str, Any] | None = Depends(
        SupabaseJWTBearer(
            supabase_url=settings.supabase_url,
            supabase_anon_key=settings.supabase_anon_key,
            jwt_algorithm=settings.jwt_algorithm,
            jwt_secret=settings.jwt_secret,
            auto_error=False,
        )
    ),
) -> JWTPayload | None:
    """Optional authentication - returns JWT payload or None if not authenticated."""
    if token_data:
        return await _extract_jwt_payload(token_data)
    return None


async def get_mfa_user(
    jwt_payload: JWTPayload = Depends(_extract_jwt_payload),
) -> JWTPayload:
    """Ensure user has completed MFA (aal2)."""
    if jwt_payload.aal != "aal2":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Multi-factor authentication required",
        )
    return jwt_payload


# Full user profile dependency
async def require_full_user(
    jwt_payload: JWTPayload = Depends(require_auth),
    supabase: Client = Depends(get_supabase_client),
) -> SupabaseUser:
    """
    Get full user profile from Supabase Auth API.

    This makes an API call to Supabase, so use sparingly.
    Prefer using require_auth for most endpoints.
    """
    if not jwt_payload._raw_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token not available for user lookup",
        )

    try:
        # Get user from Supabase Auth API
        response = supabase.auth.get_user(jwt_payload._raw_token)

        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Convert Supabase user to our model
        user_data = (
            response.user.model_dump()
            if hasattr(response.user, "model_dump")
            else response.user.dict()
        )
        return SupabaseUser(**user_data)

    except Exception as e:
        # Log the error in production
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to fetch user profile: {str(e)}",
        )
