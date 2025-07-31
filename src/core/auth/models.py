"""
Authentication data models.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, PrivateAttr


class JWTPayload(BaseModel):
    """JWT token payload data - extracted from validated JWT."""

    user_id: str = Field(..., alias="sub")
    email: str | None = None
    phone: str | None = None
    role: str = "authenticated"
    session_id: str
    aal: str = "aal1"  # Authentication Assurance Level
    provider: str | None = None
    is_anonymous: bool = False

    # Store the raw token for use with Supabase API calls
    _raw_token: str = PrivateAttr(default="")

    model_config = {"populate_by_name": True}


class SupabaseUser(BaseModel):
    """Full user profile from Supabase Auth - requires API call."""

    id: str
    email: str | None = None
    phone: str | None = None
    email_confirmed_at: datetime | None = None
    phone_confirmed_at: datetime | None = None
    last_sign_in_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    app_metadata: dict[str, Any] = Field(default_factory=dict)
    user_metadata: dict[str, Any] = Field(default_factory=dict)
    identities: list[dict[str, Any]] = Field(default_factory=list)
    factors: list[dict[str, Any]] = Field(default_factory=list)
    aud: str = "authenticated"
    role: str = "authenticated"
    aal: str | None = None
    amr: list[dict[str, Any]] = Field(default_factory=list)
    session_id: str | None = None
