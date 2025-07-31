"""
Authentication module for Supabase integration.

This module implements JWT validation using JWKS public key verification
with automatic fallback to Supabase API validation.
"""

# Export all public APIs to maintain backward compatibility
# For internal testing access
from .dependencies import (
    _extract_jwt_payload,
    get_mfa_user,
    optional_auth,
    require_auth,
    require_full_user,
)
from .errors import AuthError, AuthErrorCode, jwt_exception_handler
from .jwt_bearer import SupabaseJWTBearer
from .models import JWTPayload, SupabaseUser

__all__ = [
    # Models
    "JWTPayload",
    "SupabaseUser",
    # Errors
    "AuthErrorCode",
    "AuthError",
    "jwt_exception_handler",
    # Dependencies
    "require_auth",
    "optional_auth",
    "get_mfa_user",
    "require_full_user",
    # JWT Bearer
    "SupabaseJWTBearer",
    # Internal (for tests)
    "_extract_jwt_payload",
]
