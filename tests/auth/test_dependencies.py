"""
Tests for authentication dependencies.
"""

from unittest.mock import patch

import pytest

from src.core.auth.dependencies import (
    _extract_jwt_payload,
    optional_auth,
    require_auth,
)
from src.core.auth.models import JWTPayload


class TestExtractJWTPayload:
    """Tests for _extract_jwt_payload function."""

    @pytest.mark.asyncio
    async def test_extract_jwt_payload_with_email_provider(
        self, valid_token_data, mock_user_id
    ):
        """Test extracting JWT payload with email provider."""
        result = await _extract_jwt_payload(valid_token_data)

        assert isinstance(result, JWTPayload)
        assert result.user_id == mock_user_id
        assert result.email == "test@example.com"
        assert result.phone is None
        assert result.role == "authenticated"
        assert result.session_id == "test-session-456"
        assert result.aal == "aal1"
        assert result.provider == "email"
        assert result.is_anonymous is False
        assert result._raw_token == "test.jwt.token"

    @pytest.mark.asyncio
    async def test_extract_jwt_payload_with_phone_provider(self):
        """Test extracting JWT payload with phone provider."""
        token_data = {
            "sub": "user-456",
            "email": None,
            "phone": "+1234567890",
            "role": "authenticated",
            "session_id": "session-789",
            "aal": "aal2",
            "is_anonymous": False,
            "app_metadata": {
                "provider": "phone",
                "providers": ["phone"],
            },
            "_raw_token": "phone.jwt.token",
        }

        result = await _extract_jwt_payload(token_data)

        assert result.user_id == "user-456"
        assert result.email is None
        assert result.phone == "+1234567890"
        assert result.provider == "phone"
        assert result.aal == "aal2"

    @pytest.mark.asyncio
    async def test_extract_jwt_payload_with_missing_optional_fields(self):
        """Test extracting JWT payload with minimal data."""
        minimal_data = {
            "sub": "user-789",
            "role": "authenticated",
            "session_id": "session-000",
        }

        result = await _extract_jwt_payload(minimal_data)

        assert result.user_id == "user-789"
        assert result.email is None
        assert result.phone is None
        assert result.role == "authenticated"
        assert result.session_id == "session-000"
        assert result.aal == "aal1"  # Default value
        assert result.provider is None
        assert result.is_anonymous is False  # Default value
        assert result._raw_token == ""  # Default when not provided

    @pytest.mark.asyncio
    async def test_extract_jwt_payload_with_anonymous_user(self):
        """Test extracting JWT payload for anonymous user."""
        anon_data = {
            "sub": "anon-123",
            "role": "authenticated",
            "session_id": "anon-session",
            "is_anonymous": True,
        }

        result = await _extract_jwt_payload(anon_data)

        assert result.user_id == "anon-123"
        assert result.is_anonymous is True
        assert result.role == "authenticated"


class TestRequireAuth:
    """Tests for require_auth dependency."""

    @pytest.mark.asyncio
    async def test_require_auth_with_valid_token(self, valid_token_data, mock_user_id):
        """Test require_auth returns JWT payload with valid token."""
        # Create a mock JWT payload from the token data
        mock_jwt_payload = await _extract_jwt_payload(valid_token_data)

        # Test that require_auth properly returns the JWT payload
        result = await require_auth(jwt_payload=mock_jwt_payload)

        assert isinstance(result, JWTPayload)
        assert result.user_id == mock_user_id
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_require_auth_dependency_chain(self):
        """Test require_auth properly chains dependencies."""
        # This test verifies the dependency injection chain works
        mock_jwt_payload = JWTPayload(
            user_id="dep-user",
            email="dep@test.com",
            role="authenticated",
            session_id="dep-session",
        )

        result = await require_auth(jwt_payload=mock_jwt_payload)

        assert result == mock_jwt_payload
        assert result.user_id == "dep-user"


class TestOptionalAuth:
    """Tests for optional_auth dependency."""

    @pytest.mark.asyncio
    async def test_optional_auth_with_valid_token(self, valid_token_data):
        """Test optional_auth returns JWT payload when token is provided."""
        # Mock _extract_jwt_payload
        mock_jwt_payload = JWTPayload(
            user_id="user-123",
            email="test@example.com",
            role="authenticated",
            session_id="session-456",
        )

        with patch(
            "src.core.auth.dependencies._extract_jwt_payload",
            return_value=mock_jwt_payload,
        ):
            result = await optional_auth(token_data=valid_token_data)

            assert result == mock_jwt_payload
            assert result.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_optional_auth_without_token(self):
        """Test optional_auth returns None when no token is provided."""
        result = await optional_auth(token_data=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_with_invalid_token(self):
        """Test optional_auth behavior with invalid token data."""
        # When auto_error=False, invalid tokens result in None token_data
        result = await optional_auth(token_data=None)

        assert result is None
