"""Comprehensive tests for the plans API endpoints.

This module tests the POST /api/v1/plans endpoint functionality including:
- Successful plan creation with valid data
- Authentication requirements (401 errors)
- Request validation (422 errors)
- Database constraint violations (400 errors)
- Duplicate plan names (409 errors)
- Database error handling (500 errors)
- Edge cases and boundary values
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from src.core.auth.models import JWTPayload
from src.models.enums import DifficultyLevel, TrainingStyle

# Test client setup
client = TestClient(app)


@pytest.fixture
def mock_user_id():
    """Generate a consistent test user ID."""
    return str(uuid4())


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
def mock_auth_dependency(mock_jwt_payload):
    """Mock JWT authentication dependency by overriding the FastAPI dependency."""

    from src.core.auth import require_auth

    # Override the dependency in the FastAPI app
    def mock_require_auth():
        return mock_jwt_payload

    # Patch the app's dependency override
    app.dependency_overrides[require_auth] = mock_require_auth

    yield mock_require_auth

    # Clean up the override after the test
    if require_auth in app.dependency_overrides:
        del app.dependency_overrides[require_auth]


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client with proper table method chaining."""
    from src.core.utils import get_supabase_client

    # Create a single mock client instance
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()

    # Set up the method chain: client.table().insert().execute()
    mock_client.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute

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


# ============================================================================
# SUCCESS TESTS
# ============================================================================


def test_create_plan_success_full_data(
    mock_auth_dependency, mock_supabase_client, valid_plan_data, created_plan_response
):
    """Test successful plan creation with all fields provided."""
    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [created_plan_response]
    mock_supabase_client.table().insert().execute.return_value = mock_response

    # Make the request
    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()

    # Verify response structure and data
    assert response_data["name"] == valid_plan_data["name"]
    assert response_data["description"] == valid_plan_data["description"]
    assert response_data["training_style"] == valid_plan_data["training_style"]
    assert response_data["goal"] == valid_plan_data["goal"]
    assert response_data["difficulty_level"] == valid_plan_data["difficulty_level"]
    assert response_data["duration_weeks"] == valid_plan_data["duration_weeks"]
    assert response_data["days_per_week"] == valid_plan_data["days_per_week"]
    assert response_data["is_public"] == valid_plan_data["is_public"]
    assert response_data["metadata"] == valid_plan_data["metadata"]

    # Verify system-generated fields
    assert "id" in response_data
    assert "user_id" in response_data
    assert response_data["version_number"] == 1
    assert response_data["parent_plan_id"] is None
    assert response_data["is_active"] is True
    assert "created_at" in response_data

    # Verify database insertion was called
    assert mock_supabase_client.table.called
    assert mock_supabase_client.table().insert.called
    assert mock_supabase_client.table().insert().execute.called


def test_create_plan_success_minimal_data(
    mock_auth_dependency, mock_supabase_client, minimal_plan_data, mock_user_id
):
    """Test successful plan creation with only required fields."""
    created_plan = {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        **minimal_plan_data,
        "description": None,
        "goal": None,
        "difficulty_level": None,
        "duration_weeks": None,
        "days_per_week": None,
        "is_public": False,
        "metadata": {},
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    mock_response = MagicMock()
    mock_response.data = [created_plan]
    mock_supabase_client.table().insert().execute.return_value = mock_response

    response = client.post(
        "/api/v1/plans/",
        json=minimal_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["name"] == minimal_plan_data["name"]
    assert response_data["training_style"] == minimal_plan_data["training_style"]
    assert response_data["description"] is None
    assert response_data["is_public"] is False


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================


def test_create_plan_unauthenticated(valid_plan_data):
    """Test plan creation without authentication token."""
    response = client.post("/api/v1/plans/", json=valid_plan_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_plan_invalid_token(valid_plan_data):
    """Test plan creation with invalid authentication token."""
    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer invalid-token"},
    )
    # Invalid tokens return 401 Unauthorized, not 403 Forbidden
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_plan_malformed_auth_header(valid_plan_data):
    """Test plan creation with malformed authorization header."""
    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "InvalidFormat token"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# VALIDATION ERROR TESTS (422)
# ============================================================================


def test_create_plan_empty_name(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with empty name."""
    invalid_data = {
        "name": "",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "name" in response.text.lower()


def test_create_plan_whitespace_only_name(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with whitespace-only name."""
    invalid_data = {
        "name": "   ",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_plan_missing_required_fields(
    mock_auth_dependency, mock_supabase_client
):
    """Test plan creation with missing required fields."""
    # Missing training_style (required field)
    invalid_data = {
        "name": "Test Plan",
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("training_style" in str(error).lower() for error in error_detail)


def test_create_plan_invalid_training_style(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with invalid training style."""
    invalid_data = {
        "name": "Test Plan",
        "training_style": "invalid_style",
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("training_style" in str(error).lower() for error in error_detail)


def test_create_plan_invalid_difficulty_level(
    mock_auth_dependency, mock_supabase_client
):
    """Test plan creation with invalid difficulty level."""
    invalid_data = {
        "name": "Test Plan",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
        "difficulty_level": "expert",  # Not a valid difficulty level
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_plan_name_too_long(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with name exceeding maximum length."""
    invalid_data = {
        "name": "x" * 101,  # Exceeds 100 character limit
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_plan_description_too_long(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with description exceeding maximum length."""
    invalid_data = {
        "name": "Test Plan",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
        "description": "x" * 2001,  # Exceeds 2000 character limit
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_plan_invalid_duration_weeks(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with invalid duration_weeks values."""
    # Test zero weeks
    invalid_data = {
        "name": "Test Plan",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
        "duration_weeks": 0,
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test exceeding maximum weeks
    invalid_data["duration_weeks"] = 53

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_plan_invalid_days_per_week(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with invalid days_per_week values."""
    # Test zero days
    invalid_data = {
        "name": "Test Plan",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
        "days_per_week": 0,
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test exceeding maximum days
    invalid_data["days_per_week"] = 8

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_plan_extra_fields_forbidden(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with extra fields (should be forbidden)."""
    invalid_data = {
        "name": "Test Plan",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
        "invalid_extra_field": "should not be allowed",
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("extra" in str(error).lower() for error in error_detail)


# ============================================================================
# CONSTRAINT VIOLATION TESTS (400)
# ============================================================================


def test_create_plan_check_constraint_difficulty(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with invalid difficulty level constraint."""
    mock_supabase_client.table().insert().execute.side_effect = Exception(
        "check constraint violation: difficulty_level must be valid"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "difficulty level" in response.json()["detail"].lower()


def test_create_plan_check_constraint_duration(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with duration weeks constraint violation."""
    mock_supabase_client.table().insert().execute.side_effect = Exception(
        "check constraint violation: duration_weeks must be positive"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "duration weeks" in response.json()["detail"].lower()


def test_create_plan_check_constraint_days_per_week(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with days per week constraint violation."""
    mock_supabase_client.table().insert().execute.side_effect = Exception(
        "check constraint violation: days_per_week invalid range"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "days per week" in response.json()["detail"].lower()


def test_create_plan_foreign_key_violation(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with foreign key constraint violation."""
    mock_supabase_client.table().insert().execute.side_effect = Exception(
        "foreign key violation: invalid user reference"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid reference" in response.json()["detail"].lower()


def test_create_plan_generic_check_constraint(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with generic check constraint violation."""
    mock_supabase_client.table().insert().execute.side_effect = Exception(
        "check constraint violation: some_field validation failed"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "validation error" in response.json()["detail"].lower()


# ============================================================================
# DUPLICATE NAME TESTS (409)
# ============================================================================


def test_create_plan_duplicate_name(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with duplicate name for same user."""
    mock_supabase_client.table().insert().execute.side_effect = Exception(
        "duplicate key value violates unique constraint"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"]


def test_create_plan_duplicate_name_and_version(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with duplicate name and version."""
    mock_supabase_client.table().insert().execute.side_effect = Exception(
        "duplicate key value violates unique constraint plans_user_id_name_version_key"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    response_data = response.json()
    assert "already exists" in response_data["detail"]
    assert "version" in response_data["detail"]


# ============================================================================
# DATABASE ERROR TESTS (500)
# ============================================================================


def test_create_plan_database_connection_error(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with database connection error."""
    mock_supabase_client.table().insert().execute.side_effect = Exception(
        "Database connection timeout"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "internal error" in response.json()["detail"].lower()


def test_create_plan_no_data_returned(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation when database returns no data."""
    mock_response = MagicMock()
    mock_response.data = []  # Empty data array
    mock_supabase_client.table().insert().execute.return_value = mock_response

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "no data returned" in response.json()["detail"]


def test_create_plan_none_data_returned(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation when database returns None data."""
    mock_response = MagicMock()
    mock_response.data = None
    mock_supabase_client.table().insert().execute.return_value = mock_response

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "no data returned" in response.json()["detail"]


def test_create_plan_generic_database_error(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with generic database error."""
    mock_supabase_client.table().insert().execute.side_effect = Exception(
        "Unexpected database error occurred"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "internal error" in response.json()["detail"].lower()


def test_create_plan_value_error_handling(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with ValueError from data processing."""
    # Mock a ValueError being raised during data processing
    mock_supabase_client.table().insert().execute.side_effect = ValueError(
        "Invalid data format encountered"
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid data format encountered" in response.json()["detail"]


# ============================================================================
# EDGE CASES AND BOUNDARY VALUE TESTS
# ============================================================================


def test_create_plan_boundary_values(
    mock_auth_dependency, mock_supabase_client, mock_user_id
):
    """Test plan creation with boundary values."""
    boundary_data = {
        "name": "x",  # Minimum length (1 character)
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
        "duration_weeks": 1,  # Minimum value
        "days_per_week": 1,  # Minimum value
    }

    created_plan = {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        **boundary_data,
        "description": None,
        "goal": None,
        "difficulty_level": None,
        "is_public": False,
        "metadata": {},
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    mock_response = MagicMock()
    mock_response.data = [created_plan]
    mock_supabase_client.table().insert().execute.return_value = mock_response

    response = client.post(
        "/api/v1/plans/",
        json=boundary_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["name"] == "x"
    assert response_data["duration_weeks"] == 1
    assert response_data["days_per_week"] == 1


def test_create_plan_maximum_boundary_values(
    mock_auth_dependency, mock_supabase_client, mock_user_id
):
    """Test plan creation with maximum boundary values."""
    boundary_data = {
        "name": "x" * 100,  # Maximum length
        "description": "x" * 2000,  # Maximum length
        "goal": "x" * 200,  # Maximum length
        "training_style": TrainingStyle.POWERLIFTING.value,
        "difficulty_level": DifficultyLevel.ADVANCED.value,
        "duration_weeks": 52,  # Maximum value
        "days_per_week": 7,  # Maximum value
        "is_public": True,
        "metadata": {"key1": "value1", "key2": {"nested": "data"}},
    }

    created_plan = {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        **boundary_data,
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    mock_response = MagicMock()
    mock_response.data = [created_plan]
    mock_supabase_client.table().insert().execute.return_value = mock_response

    response = client.post(
        "/api/v1/plans/",
        json=boundary_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert len(response_data["name"]) == 100
    assert len(response_data["description"]) == 2000
    assert response_data["duration_weeks"] == 52
    assert response_data["days_per_week"] == 7
    assert response_data["is_public"] is True


def test_create_plan_unicode_characters(
    mock_auth_dependency, mock_supabase_client, mock_user_id
):
    """Test plan creation with unicode characters."""
    unicode_data = {
        "name": "강화 운동 💪 Plan",  # Korean + emoji
        "description": "Descripción con acentos y símbolos: 体力 训练 🏋️‍♂️",
        "training_style": TrainingStyle.BODYBUILDING.value,
        "goal": "fuerza y músculo",
    }

    created_plan = {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        **unicode_data,
        "difficulty_level": None,
        "duration_weeks": None,
        "days_per_week": None,
        "is_public": False,
        "metadata": {},
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    mock_response = MagicMock()
    mock_response.data = [created_plan]
    mock_supabase_client.table().insert().execute.return_value = mock_response

    response = client.post(
        "/api/v1/plans/",
        json=unicode_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["name"] == unicode_data["name"]
    assert response_data["description"] == unicode_data["description"]
    assert response_data["goal"] == unicode_data["goal"]


def test_create_plan_complex_metadata(
    mock_auth_dependency, mock_supabase_client, mock_user_id
):
    """Test plan creation with complex metadata structure."""
    complex_metadata = {
        "periodization": {
            "type": "linear",
            "phases": [
                {"week": 1, "intensity": 70, "volume": 100},
                {"week": 2, "intensity": 75, "volume": 95},
            ],
        },
        "deload_protocol": {
            "frequency": "every_4_weeks",
            "intensity_reduction": 0.4,
        },
        "progression": {
            "method": "double_progression",
            "rep_ranges": {"lower": 6, "upper": 10},
        },
        "rest_periods": [120, 180, 240],
        "tags": ["beginner-friendly", "home-gym", "time-efficient"],
    }

    plan_data = {
        "name": "Complex Metadata Plan",
        "training_style": TrainingStyle.POWERBUILDING.value,
        "metadata": complex_metadata,
    }

    created_plan = {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        **plan_data,
        "description": None,
        "goal": None,
        "difficulty_level": None,
        "duration_weeks": None,
        "days_per_week": None,
        "is_public": False,
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    mock_response = MagicMock()
    mock_response.data = [created_plan]
    mock_supabase_client.table().insert().execute.return_value = mock_response

    response = client.post(
        "/api/v1/plans/",
        json=plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["metadata"] == complex_metadata
    assert "periodization" in response_data["metadata"]
    assert "phases" in response_data["metadata"]["periodization"]


def test_create_plan_all_training_styles(
    mock_auth_dependency, mock_supabase_client, mock_user_id
):
    """Test plan creation with all valid training styles."""
    training_styles = [
        TrainingStyle.POWERLIFTING,
        TrainingStyle.BODYBUILDING,
        TrainingStyle.POWERBUILDING,
        TrainingStyle.GENERAL_FITNESS,
        TrainingStyle.ATHLETIC_PERFORMANCE,
    ]

    for training_style in training_styles:
        plan_data = {
            "name": f"{training_style.value.title()} Plan",
            "training_style": training_style.value,
        }

        created_plan = {
            "id": str(uuid4()),
            "user_id": mock_user_id,
            **plan_data,
            "description": None,
            "goal": None,
            "difficulty_level": None,
            "duration_weeks": None,
            "days_per_week": None,
            "is_public": False,
            "metadata": {},
            "version_number": 1,
            "parent_plan_id": None,
            "is_active": True,
            "created_at": "2025-01-01T12:00:00+00:00",
        }

        mock_response = MagicMock()
        mock_response.data = [created_plan]
        mock_supabase_client.table().insert().execute.return_value = mock_response

        response = client.post(
            "/api/v1/plans/",
            json=plan_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["training_style"] == training_style.value


def test_create_plan_all_difficulty_levels(
    mock_auth_dependency, mock_supabase_client, mock_user_id
):
    """Test plan creation with all valid difficulty levels."""
    difficulty_levels = [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED,
    ]

    for difficulty_level in difficulty_levels:
        plan_data = {
            "name": f"{difficulty_level.value.title()} Plan",
            "training_style": TrainingStyle.GENERAL_FITNESS.value,
            "difficulty_level": difficulty_level.value,
        }

        created_plan = {
            "id": str(uuid4()),
            "user_id": mock_user_id,
            **plan_data,
            "description": None,
            "goal": None,
            "duration_weeks": None,
            "days_per_week": None,
            "is_public": False,
            "metadata": {},
            "version_number": 1,
            "parent_plan_id": None,
            "is_active": True,
            "created_at": "2025-01-01T12:00:00+00:00",
        }

        mock_response = MagicMock()
        mock_response.data = [created_plan]
        mock_supabase_client.table().insert().execute.return_value = mock_response

        response = client.post(
            "/api/v1/plans/",
            json=plan_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["difficulty_level"] == difficulty_level.value
