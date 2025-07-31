"""
Tests for authentication error handling.
"""

import json

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError

from src.core.auth.errors import AuthError, AuthErrorCode, jwt_exception_handler


class TestAuthErrorModels:
    """Tests for authentication error models."""

    def test_auth_error_code_enum_values(self):
        """Test AuthErrorCode enum has expected values."""
        assert AuthErrorCode.INVALID_TOKEN == "invalid_token"
        assert AuthErrorCode.EXPIRED_TOKEN == "expired_token"
        assert AuthErrorCode.MISSING_TOKEN == "missing_token"
        assert AuthErrorCode.INVALID_ISSUER == "invalid_issuer"
        assert AuthErrorCode.INVALID_AUDIENCE == "invalid_audience"
        assert AuthErrorCode.INSUFFICIENT_AAL == "insufficient_aal"
        assert AuthErrorCode.ANONYMOUS_NOT_ALLOWED == "anonymous_not_allowed"

    def test_auth_error_model_serialization(self):
        """Test AuthError model serialization."""
        error = AuthError(
            error=AuthErrorCode.INVALID_TOKEN,
            error_description="The access token provided is invalid",
        )

        # Test model_dump
        data = error.model_dump()
        assert data["error"] == "invalid_token"
        assert data["error_description"] == "The access token provided is invalid"

        # Test JSON serialization
        json_data = error.model_dump_json()
        assert '"error":"invalid_token"' in json_data
        assert '"error_description":"The access token provided is invalid"' in json_data

    def test_auth_error_with_different_codes(self):
        """Test AuthError with different error codes."""
        test_cases = [
            (
                AuthErrorCode.EXPIRED_TOKEN,
                "The access token has expired",
            ),
            (
                AuthErrorCode.MISSING_TOKEN,
                "No access token was provided",
            ),
            (
                AuthErrorCode.INVALID_ISSUER,
                "Token issuer is not recognized",
            ),
            (
                AuthErrorCode.INSUFFICIENT_AAL,
                "Multi-factor authentication required",
            ),
        ]

        for error_code, description in test_cases:
            error = AuthError(error=error_code, error_description=description)
            assert error.error == error_code
            assert error.error_description == description


@pytest.mark.asyncio
class TestJWTExceptionHandler:
    """Tests for JWT exception handler."""

    async def test_jwt_exception_handler_basic(self):
        """Test JWT exception handler returns correct response."""
        mock_request = Request({"type": "http", "method": "GET", "url": "/"})
        exc = JWTError("Token signature verification failed")

        response = await jwt_exception_handler(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"

        # Check response content
        body = json.loads(
            response.body.decode()
            if isinstance(response.body, bytes)
            else response.body
        )
        assert body["error"] == "invalid_token"
        assert body["error_description"] == "Token signature verification failed"

    async def test_jwt_exception_handler_different_errors(self):
        """Test JWT exception handler with different JWT errors."""
        mock_request = Request({"type": "http", "method": "GET", "url": "/"})

        test_cases = [
            "Token has expired",
            "Invalid audience",
            "Token is missing required claim: sub",
            "Invalid token format",
        ]

        for error_message in test_cases:
            exc = JWTError(error_message)
            response = await jwt_exception_handler(mock_request, exc)

            assert response.status_code == 401
            body = json.loads(
                response.body.decode()
                if isinstance(response.body, bytes)
                else response.body
            )
            assert body["error"] == "invalid_token"
            assert body["error_description"] == error_message

    async def test_jwt_exception_handler_headers(self):
        """Test JWT exception handler sets correct headers."""
        mock_request = Request({"type": "http", "method": "GET", "url": "/"})
        exc = JWTError("Test error")

        response = await jwt_exception_handler(mock_request, exc)

        # Check WWW-Authenticate header is set
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

        # Check content-type header
        assert response.headers["content-type"] == "application/json"
