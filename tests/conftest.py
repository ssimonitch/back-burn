"""Shared test fixtures and configuration for all tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app
from src.core.auth.models import JWTPayload
from src.models.enums import DifficultyLevel, TrainingStyle


@pytest.fixture
def client():
    """Create a test client for API testing."""
    return TestClient(app)


@pytest.fixture
def mock_user_id():
    """Generate a consistent test user ID."""
    return str(uuid4())


@pytest.fixture
def mock_settings():
    """Mock Supabase settings for testing."""
    return {
        "supabase_url": "https://test-project.supabase.co",
        "supabase_anon_key": "test-anon-key",
    }


@pytest.fixture
def mock_jwt_payload(mock_user_id):
    """Create a mock JWT payload for testing."""
    return JWTPayload(
        user_id=mock_user_id,
        email="test@example.com",
        role="authenticated",
        session_id="test-session-123",
        aal="aal1",
        provider="email",
        is_anonymous=False,
    )


@pytest.fixture
def valid_token_data(mock_user_id):
    """Create valid JWT token data for authentication testing."""
    return {
        "sub": mock_user_id,
        "email": "test@example.com",
        "phone": None,
        "role": "authenticated",
        "session_id": "test-session-456",
        "aal": "aal1",
        "is_anonymous": False,
        "app_metadata": {
            "provider": "email",
            "providers": ["email"],
        },
        "_raw_token": "test.jwt.token",
    }


@pytest.fixture
def phone_token_data():
    """Create JWT token data for phone authentication testing."""
    return {
        "sub": "user-phone-123",
        "email": None,
        "phone": "+1234567890",
        "role": "authenticated",
        "session_id": "phone-session-456",
        "aal": "aal2",
        "is_anonymous": False,
        "app_metadata": {
            "provider": "phone",
            "providers": ["phone"],
        },
        "_raw_token": "phone.jwt.token",
    }


@pytest.fixture
def anonymous_token_data():
    """Create JWT token data for anonymous user testing."""
    return {
        "sub": "anon-123",
        "role": "authenticated",
        "session_id": "anon-session",
        "is_anonymous": True,
        "app_metadata": {
            "provider": "anonymous",
            "providers": ["anonymous"],
        },
        "_raw_token": "anon.jwt.token",
    }


@pytest.fixture
def valid_jwt_with_timestamps(mock_settings, mock_user_id):
    """Create a valid JWT payload with proper timestamps for verification testing."""
    now = datetime.now(UTC)
    return {
        "sub": mock_user_id,
        "email": "test@example.com",
        "phone": None,
        "role": "authenticated",
        "session_id": "session-456",
        "aal": "aal1",
        "is_anonymous": False,
        "iss": f"{mock_settings['supabase_url']}/auth/v1",
        "aud": "authenticated",
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
        "app_metadata": {
            "provider": "email",
            "providers": ["email"],
        },
        "user_metadata": {
            "name": "Test User",
        },
    }


@pytest.fixture
def mock_auth_dependency(mock_jwt_payload):
    """Mock JWT authentication dependency by overriding the FastAPI dependency."""
    from src.core.auth.dependencies import require_auth

    def mock_require_auth():
        return mock_jwt_payload

    # Override the dependency in the FastAPI app
    app.dependency_overrides[require_auth] = mock_require_auth

    yield mock_require_auth

    # Clean up the override after the test
    app.dependency_overrides.clear()


@pytest.fixture
def mock_optional_auth_dependency():
    """Mock optional JWT authentication dependency."""
    from src.core.auth.dependencies import optional_auth

    def mock_optional_auth_with_user(user_payload):
        """Return a function that returns the given user payload."""

        def _mock():
            return user_payload

        return _mock

    def mock_optional_auth_anonymous():
        """Return a function that returns None (anonymous user)."""

        def _mock():
            return None

        return _mock

    # Return utilities for test setup
    return {
        "with_user": mock_optional_auth_with_user,
        "anonymous": mock_optional_auth_anonymous,
        "dependency": optional_auth,
    }


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client with proper table method chaining."""
    from src.core.utils import get_supabase_client

    # Create a single comprehensive mock
    mock_client = MagicMock()

    # Override the dependency to return the same instance
    def mock_get_supabase_client():
        return mock_client

    app.dependency_overrides[get_supabase_client] = mock_get_supabase_client

    yield mock_client

    # Clean up the override after the test
    if get_supabase_client in app.dependency_overrides:
        del app.dependency_overrides[get_supabase_client]


@pytest.fixture
def valid_plan_data():
    """Valid plan creation data for testing."""
    return {
        "name": "Upper/Lower Split",
        "description": "A 4-day upper/lower split focusing on compound movements",
        "training_style": TrainingStyle.POWERBUILDING.value,
        "goal": "strength",
        "difficulty_level": DifficultyLevel.INTERMEDIATE.value,
        "duration_weeks": 8,
        "days_per_week": 4,
        "is_public": False,
        "metadata": {"periodization": "linear"},
    }


@pytest.fixture
def minimal_plan_data():
    """Minimal valid plan creation data (only required fields)."""
    return {
        "name": "Minimal Plan",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
    }


@pytest.fixture
def created_plan_response(mock_user_id, valid_plan_data):
    """Mock database response for successful plan creation."""
    plan_id = str(uuid4())
    return {
        "id": plan_id,
        "user_id": mock_user_id,
        **valid_plan_data,
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }


@pytest.fixture
def mock_plans_list(mock_user_id):
    """Mock database response for multiple plans."""
    return [
        {
            "id": str(uuid4()),
            "user_id": mock_user_id,
            "name": "Plan 1",
            "description": None,
            "training_style": TrainingStyle.POWERBUILDING.value,
            "goal": None,
            "difficulty_level": None,
            "duration_weeks": None,
            "days_per_week": None,
            "created_at": "2025-01-02T12:00:00+00:00",
            "version_number": 1,
            "is_active": True,
            "is_public": False,
            "metadata": {},
        },
        {
            "id": str(uuid4()),
            "user_id": mock_user_id,
            "name": "Plan 2",
            "description": None,
            "training_style": TrainingStyle.BODYBUILDING.value,
            "goal": None,
            "difficulty_level": None,
            "duration_weeks": None,
            "days_per_week": None,
            "created_at": "2025-01-01T12:00:00+00:00",
            "version_number": 1,
            "is_active": True,
            "is_public": False,
            "metadata": {},
        },
    ]


@pytest.fixture
def mock_private_plan(mock_user_id):
    """Mock database response for a private plan."""
    plan_id = str(uuid4())
    return {
        "id": plan_id,
        "user_id": mock_user_id,
        "name": "My Private Plan",
        "description": None,
        "training_style": TrainingStyle.POWERBUILDING.value,
        "goal": None,
        "difficulty_level": None,
        "duration_weeks": None,
        "days_per_week": None,
        "is_public": False,
        "version_number": 1,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
        "metadata": {},
    }


@pytest.fixture
def mock_public_plan():
    """Mock database response for a public plan."""
    plan_id = str(uuid4())
    return {
        "id": plan_id,
        "user_id": str(uuid4()),
        "name": "Public Plan",
        "description": None,
        "training_style": TrainingStyle.BODYBUILDING.value,
        "goal": None,
        "difficulty_level": None,
        "duration_weeks": None,
        "days_per_week": None,
        "is_public": True,
        "version_number": 1,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
        "metadata": {},
    }
