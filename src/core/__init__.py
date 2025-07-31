"""Core module for application configuration and authentication."""

from src.core.auth import (
    JWTPayload,
    SupabaseUser,
    optional_auth,
    require_auth,
    require_full_user,
)
from src.core.settings import settings
from src.core.utils import get_supabase_client

__all__ = [
    "settings",
    "JWTPayload",
    "SupabaseUser",
    "require_auth",
    "optional_auth",
    "require_full_user",
    "get_supabase_client",
]
