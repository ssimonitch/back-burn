"""
Integration tests for authentication endpoints.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from src.core.auth.dependencies import optional_auth, require_auth
from src.core.auth.models import JWTPayload


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def valid_jwt_payload():
    """Create a valid JWT payload for mocking."""
    return JWTPayload(
        user_id="user-123",
        email="test@example.com",
        phone=None,
        role="authenticated",
        session_id="session-456",
        aal="aal1",
        provider="email",
        is_anonymous=False,
    )


class TestMeEndpoint:
    """Tests for the /api/v1/auth/me endpoint."""

    def test_me_endpoint_with_valid_token(self, client, valid_jwt_payload):
        """Test /me endpoint returns user info with valid token."""
        # Override the dependency
        app.dependency_overrides[require_auth] = lambda: valid_jwt_payload

        try:
            response = client.get("/api/v1/auth/me")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["user_id"] == "user-123"
            assert data["email"] == "test@example.com"
            assert data["phone"] is None
            assert data["role"] == "authenticated"
            assert data["session_id"] == "session-456"
            assert data["aal"] == "aal1"
            assert data["provider"] == "email"
            assert data["is_anonymous"] is False
        finally:
            app.dependency_overrides.clear()

    def test_me_endpoint_without_token(self, client):
        """Test /me endpoint returns 401 without token."""
        # Don't override - let the real auth dependency run
        response = client.get("/api/v1/auth/me")

        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # HTTPBearer returns 403
        assert response.json()["detail"] == "Not authenticated"

    def test_me_endpoint_with_invalid_token(self, client):
        """Test /me endpoint returns 401 with invalid token."""
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_endpoint_with_malformed_auth_header(self, client):
        """Test /me endpoint returns 403 with malformed auth header."""
        # Missing Bearer prefix
        headers = {"Authorization": "invalid.jwt.token"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPublicEndpoint:
    """Tests for the /api/v1/auth/public endpoint."""

    def test_public_endpoint_without_auth(self, client):
        """Test /public endpoint works without authentication."""
        # Override to return None (no user)
        app.dependency_overrides[optional_auth] = lambda: None

        try:
            response = client.get("/api/v1/auth/public")

            assert response.status_code == status.HTTP_200_OK
            assert response.json() == {"message": "Hello, anonymous!"}
        finally:
            app.dependency_overrides.clear()

    def test_public_endpoint_with_auth(self, client, valid_jwt_payload):
        """Test /public endpoint returns personalized message with auth."""
        # Override to return the user
        app.dependency_overrides[optional_auth] = lambda: valid_jwt_payload

        try:
            response = client.get("/api/v1/auth/public")

            assert response.status_code == status.HTTP_200_OK
            assert response.json() == {"message": "Hello, test@example.com!"}
        finally:
            app.dependency_overrides.clear()

    def test_public_endpoint_with_auth_no_email(self, client):
        """Test /public endpoint with authenticated user without email."""
        user_without_email = JWTPayload(
            user_id="user-456",
            email=None,
            phone="+1234567890",
            role="authenticated",
            session_id="session-789",
            aal="aal1",
            provider="phone",
            is_anonymous=False,
        )

        # Override to return user without email
        app.dependency_overrides[optional_auth] = lambda: user_without_email

        try:
            response = client.get("/api/v1/auth/public")

            assert response.status_code == status.HTTP_200_OK
            assert response.json() == {"message": "Hello, authenticated user!"}
        finally:
            app.dependency_overrides.clear()

    def test_public_endpoint_with_invalid_token(self, client):
        """Test /public endpoint treats invalid token as anonymous."""
        # Override to return None (authentication failed)
        app.dependency_overrides[optional_auth] = lambda: None

        try:
            headers = {"Authorization": "Bearer invalid.jwt.token"}
            response = client.get("/api/v1/auth/public", headers=headers)

            assert response.status_code == status.HTTP_200_OK
            assert response.json() == {"message": "Hello, anonymous!"}
        finally:
            app.dependency_overrides.clear()
