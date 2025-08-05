"""
Tests for JWT Bearer authentication.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.core.auth.dependencies import _extract_jwt_payload
from src.core.auth.jwt_bearer import SupabaseJWTBearer
from src.core.auth.models import JWTPayload


@pytest.fixture
def jwt_bearer(mock_settings):
    """Create a SupabaseJWTBearer instance for testing."""
    return SupabaseJWTBearer(
        supabase_url=mock_settings["supabase_url"],
        supabase_anon_key=mock_settings["supabase_anon_key"],
    )


@pytest.mark.asyncio
async def test_verify_jwt_with_valid_token(jwt_bearer, valid_jwt_with_timestamps):
    """Test JWT verification with a valid token."""
    # Mock the JWKS response
    mock_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }

    # Mock the JWT decoding
    with patch.object(jwt_bearer, "get_jwks", return_value=mock_jwks) as mock_get_jwks:
        with patch(
            "src.core.auth.jwt_bearer.jwt.get_unverified_header",
            return_value={"kid": "test-kid", "alg": "RS256"},
        ):
            with patch(
                "src.core.auth.jwt_bearer.jwt.decode",
                return_value=valid_jwt_with_timestamps,
            ):
                with patch(
                    "src.core.auth.jwt_bearer.jwk.construct", return_value=Mock()
                ):
                    result = await jwt_bearer.verify_jwt("valid.jwt.token")

                    assert result == valid_jwt_with_timestamps
                    mock_get_jwks.assert_called_once()


@pytest.mark.asyncio
async def test_verify_jwt_with_invalid_issuer(jwt_bearer, valid_jwt_with_timestamps):
    """Test JWT verification with invalid issuer."""
    # Modify payload with invalid issuer
    invalid_payload = valid_jwt_with_timestamps.copy()
    invalid_payload["iss"] = "https://wrong-project.supabase.co/auth/v1"

    mock_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }

    with patch.object(jwt_bearer, "get_jwks", return_value=mock_jwks):
        with patch(
            "src.core.auth.jwt_bearer.jwt.get_unverified_header",
            return_value={"kid": "test-kid", "alg": "RS256"},
        ):
            with patch(
                "src.core.auth.jwt_bearer.jwt.decode", return_value=invalid_payload
            ):
                with patch(
                    "src.core.auth.jwt_bearer.jwk.construct", return_value=Mock()
                ):
                    # Should fall back to API validation when JWKS validation fails
                    with patch.object(
                        jwt_bearer, "_verify_with_api", return_value=None
                    ):
                        result = await jwt_bearer.verify_jwt("invalid.jwt.token")
                        assert result is None


@pytest.mark.asyncio
async def test_verify_jwt_with_expired_token(jwt_bearer, valid_jwt_with_timestamps):
    """Test JWT verification with expired token."""
    # Modify payload to be expired
    expired_payload = valid_jwt_with_timestamps.copy()
    expired_payload["exp"] = int((datetime.now(UTC) - timedelta(hours=1)).timestamp())

    mock_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }

    from jose import JWTError

    with patch.object(jwt_bearer, "get_jwks", return_value=mock_jwks):
        with patch(
            "src.core.auth.jwt_bearer.jwt.get_unverified_header",
            return_value={"kid": "test-kid", "alg": "RS256"},
        ):
            with patch(
                "src.core.auth.jwt_bearer.jwt.decode",
                side_effect=JWTError("Token has expired"),
            ):
                with patch(
                    "src.core.auth.jwt_bearer.jwk.construct", return_value=Mock()
                ):
                    # Should fall back to API validation
                    with patch.object(
                        jwt_bearer, "_verify_with_api", return_value=None
                    ):
                        result = await jwt_bearer.verify_jwt("expired.jwt.token")
                        assert result is None


@pytest.mark.asyncio
async def test_extract_jwt_payload(valid_jwt_with_timestamps):
    """Test _extract_jwt_payload function."""
    jwt_payload = await _extract_jwt_payload(valid_jwt_with_timestamps)

    assert isinstance(jwt_payload, JWTPayload)
    assert jwt_payload.user_id == valid_jwt_with_timestamps["sub"]
    assert jwt_payload.email == "test@example.com"
    assert jwt_payload.phone is None
    assert jwt_payload.role == "authenticated"
    assert jwt_payload.session_id == "session-456"
    assert jwt_payload.aal == "aal1"
    assert jwt_payload.provider == "email"
    assert jwt_payload.is_anonymous is False


@pytest.mark.asyncio
async def test_jwks_caching(jwt_bearer):
    """Test that JWKS responses are cached."""
    mock_response = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }

    # Mock _fetch_jwks to avoid real HTTP calls
    call_count = 0

    async def mock_fetch_jwks():
        nonlocal call_count
        call_count += 1
        return mock_response

    with patch.object(jwt_bearer, "_fetch_jwks", side_effect=mock_fetch_jwks):
        # First call should fetch
        result1 = await jwt_bearer.get_jwks()
        assert result1 == mock_response
        assert call_count == 1

        # Second call should use cache
        result2 = await jwt_bearer.get_jwks()
        assert result2 == mock_response
        assert call_count == 1  # Still 1, not 2

        # Force refresh should fetch again
        result3 = await jwt_bearer.get_jwks(force_refresh=True)
        assert result3 == mock_response
        assert call_count == 2


@pytest.mark.asyncio
async def test_key_rotation_handling(jwt_bearer):
    """Test handling of key rotation (kid not found)."""
    # Initial JWKS without our key
    initial_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "old-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "old-modulus",
                "e": "AQAB",
            }
        ]
    }

    # Updated JWKS with our key
    updated_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "new-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "new-modulus",
                "e": "AQAB",
            }
        ]
    }

    valid_payload = {
        "sub": "user-123",
        "role": "authenticated",
        "iss": f"{jwt_bearer.supabase_url}/auth/v1",
        "aud": "authenticated",
        "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
        "session_id": "session-456",
        "aal": "aal1",
    }

    call_count = 0

    async def mock_get_jwks(force_refresh=False):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return initial_jwks
        return updated_jwks

    with patch.object(jwt_bearer, "get_jwks", side_effect=mock_get_jwks):
        with patch(
            "src.core.auth.jwt_bearer.jwt.get_unverified_header",
            return_value={"kid": "new-kid", "alg": "RS256"},
        ):
            with patch(
                "src.core.auth.jwt_bearer.jwt.decode", return_value=valid_payload
            ):
                with patch(
                    "src.core.auth.jwt_bearer.jwk.construct", return_value=Mock()
                ):
                    result = await jwt_bearer._verify_with_jwks("test.jwt.token")

                    # Should have called get_jwks twice (initial + refresh)
                    assert call_count == 2
                    assert result == valid_payload


@pytest.mark.asyncio
async def test_missing_authorization_header(jwt_bearer):
    """Test handling of missing Authorization header."""
    mock_request = Mock()
    mock_request.headers = {}

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await jwt_bearer(mock_request)

    assert (
        exc_info.value.status_code == 403
    )  # HTTPBearer returns 403 for missing header
    assert exc_info.value.detail == "Not authenticated"


@pytest.mark.asyncio
async def test_invalid_bearer_scheme(jwt_bearer):
    """Test handling of invalid authentication scheme."""
    mock_request = Mock()
    mock_request.headers = {
        "Authorization": "Basic dXNlcjpwYXNz"
    }  # Basic auth instead of Bearer

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await jwt_bearer(mock_request)

    assert (
        exc_info.value.status_code == 403
    )  # HTTPBearer returns 403 for invalid scheme
    assert exc_info.value.detail == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_verify_jwt_with_malformed_token(jwt_bearer):
    """Test JWT verification with malformed token."""
    malformed_token = "not.a.jwt"

    from jose import JWTError

    with patch(
        "src.core.auth.jwt_bearer.jwt.get_unverified_header",
        side_effect=JWTError("Invalid token"),
    ):
        # Should fall back to API validation
        with patch.object(jwt_bearer, "_verify_with_api", return_value=None):
            result = await jwt_bearer.verify_jwt(malformed_token)
            assert result is None


@pytest.mark.asyncio
async def test_verify_jwt_with_invalid_audience(jwt_bearer, valid_jwt_with_timestamps):
    """Test JWT verification with invalid audience claim."""
    # Modify payload with invalid audience
    invalid_payload = valid_jwt_with_timestamps.copy()
    invalid_payload["aud"] = "wrong-audience"

    mock_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }

    from jose import JWTError

    with patch.object(jwt_bearer, "get_jwks", return_value=mock_jwks):
        with patch(
            "src.core.auth.jwt_bearer.jwt.get_unverified_header",
            return_value={"kid": "test-kid", "alg": "RS256"},
        ):
            with patch("src.core.auth.jwt_bearer.jwk.construct", return_value=Mock()):
                with patch(
                    "src.core.auth.jwt_bearer.jwt.decode",
                    side_effect=JWTError("Invalid audience"),
                ):
                    # Should fall back to API validation
                    with patch.object(
                        jwt_bearer, "_verify_with_api", return_value=None
                    ):
                        result = await jwt_bearer.verify_jwt(
                            "token.with.wrong.audience"
                        )
                        assert result is None


@pytest.mark.asyncio
async def test_verify_jwt_with_invalid_role(jwt_bearer, valid_jwt_with_timestamps):
    """Test JWT verification with invalid role claim."""
    # Modify payload with invalid role
    invalid_payload = valid_jwt_with_timestamps.copy()
    invalid_payload["role"] = "superadmin"  # Invalid role

    mock_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }

    with patch.object(jwt_bearer, "get_jwks", return_value=mock_jwks):
        with patch(
            "src.core.auth.jwt_bearer.jwt.get_unverified_header",
            return_value={"kid": "test-kid", "alg": "RS256"},
        ):
            with patch(
                "src.core.auth.jwt_bearer.jwt.decode", return_value=invalid_payload
            ):
                with patch(
                    "src.core.auth.jwt_bearer.jwk.construct", return_value=Mock()
                ):
                    # Should fall back to API validation due to invalid role
                    with patch.object(
                        jwt_bearer, "_verify_with_api", return_value=None
                    ):
                        result = await jwt_bearer.verify_jwt("token.with.invalid.role")
                        assert result is None


@pytest.mark.asyncio
async def test_verify_jwt_with_anonymous_user(jwt_bearer, valid_jwt_with_timestamps):
    """Test JWT verification rejects anonymous users when authenticated is required."""
    # Modify payload to be anonymous
    anon_payload = valid_jwt_with_timestamps.copy()
    anon_payload["is_anonymous"] = True
    anon_payload["role"] = (
        "authenticated"  # Still authenticated role but anonymous flag
    )

    mock_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }

    with patch.object(jwt_bearer, "get_jwks", return_value=mock_jwks):
        with patch(
            "src.core.auth.jwt_bearer.jwt.get_unverified_header",
            return_value={"kid": "test-kid", "alg": "RS256"},
        ):
            with patch(
                "src.core.auth.jwt_bearer.jwt.decode", return_value=anon_payload
            ):
                with patch(
                    "src.core.auth.jwt_bearer.jwk.construct", return_value=Mock()
                ):
                    # Should fall back to API validation due to anonymous user
                    with patch.object(
                        jwt_bearer, "_verify_with_api", return_value=None
                    ):
                        result = await jwt_bearer.verify_jwt("anonymous.user.token")
                        assert result is None


@pytest.mark.asyncio
async def test_verify_jwt_with_missing_required_claims(
    jwt_bearer, valid_jwt_with_timestamps
):
    """Test JWT verification with missing required claims."""
    # Remove required claims
    invalid_payload = valid_jwt_with_timestamps.copy()
    del invalid_payload["sub"]  # Missing subject claim

    mock_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB",
            }
        ]
    }

    from jose import JWTError

    with patch.object(jwt_bearer, "get_jwks", return_value=mock_jwks):
        with patch(
            "src.core.auth.jwt_bearer.jwt.get_unverified_header",
            return_value={"kid": "test-kid", "alg": "RS256"},
        ):
            with patch("src.core.auth.jwt_bearer.jwk.construct", return_value=Mock()):
                with patch(
                    "src.core.auth.jwt_bearer.jwt.decode",
                    side_effect=JWTError("Token is missing required claim: sub"),
                ):
                    # Should fall back to API validation
                    with patch.object(
                        jwt_bearer, "_verify_with_api", return_value=None
                    ):
                        result = await jwt_bearer.verify_jwt("token.missing.sub")
                        assert result is None
