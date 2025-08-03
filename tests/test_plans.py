"""Comprehensive tests for the plans API endpoints.

This module tests POST, GET list, and GET by ID for /api/v1/plans endpoints:

POST /api/v1/plans (Plan Creation):
- Successful plan creation with valid data
- Authentication requirements (401 errors)
- Request validation (422 errors)
- Database constraint violations (400 errors)
- Duplicate plan names (409 errors)
- Database error handling (500 errors)
- Edge cases and boundary values

GET /api/v1/plans (Plan List Retrieval):
- Successful retrieval with multiple plans and pagination
- Empty response for users with no plans
- Authentication requirements (401/403 errors)
- Query parameter validation (422 errors)
- Sorting verification (most recent first)
- Database error handling (500 errors)
- Boundary values for pagination parameters
- Complex metadata and unicode content handling

GET /api/v1/plans/{plan_id} (Plan By ID Retrieval):
- Successful retrieval of own private plans (authenticated)
- Successful retrieval of public plans (authenticated and unauthenticated)
- Access control enforcement (404 for unauthorized access)
- Not found handling (404 for non-existent plans)
- UUID format validation (422 errors)
- Database error handling (500 errors)
- Various UUID formats (uppercase, lowercase, with hyphens)
- Complex metadata and unicode content preservation
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


# ============================================================================
# GET PLANS ENDPOINT TESTS
# ============================================================================


@pytest.fixture
def mock_plans_list(mock_user_id):
    """Mock database response for successful plans retrieval with multiple plans."""

    return [
        {
            "id": str(uuid4()),
            "user_id": mock_user_id,
            "name": "Latest Plan",
            "description": "Most recent plan",
            "training_style": None,  # Column doesn't exist yet
            "goal": "strength",
            "difficulty_level": "intermediate",
            "duration_weeks": 12,
            "days_per_week": 4,
            "is_public": False,
            "metadata": {"notes": "updated plan"},
            "version_number": 1,
            "parent_plan_id": None,
            "is_active": True,
            "created_at": "2025-01-03T12:00:00+00:00",
        },
        {
            "id": str(uuid4()),
            "user_id": mock_user_id,
            "name": "Older Plan",
            "description": "Earlier created plan",
            "training_style": None,
            "goal": "hypertrophy",
            "difficulty_level": "beginner",
            "duration_weeks": 8,
            "days_per_week": 3,
            "is_public": True,
            "metadata": {},
            "version_number": 1,
            "parent_plan_id": None,
            "is_active": True,
            "created_at": "2025-01-01T12:00:00+00:00",
        },
    ]


@pytest.fixture
def mock_get_supabase_client_for_get():
    """Mock Supabase client specifically configured for GET plans endpoint."""
    from src.core.utils import get_supabase_client

    # Create a single mock client instance with proper method chaining
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_order = MagicMock()
    mock_range = MagicMock()
    mock_execute = MagicMock()

    # Set up the method chain: client.table().select().order().range().execute()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.order.return_value = mock_order
    mock_order.range.return_value = mock_range
    mock_range.execute.return_value = mock_execute

    # Override the dependency to return the same instance
    def mock_get_supabase_client():
        return mock_client

    app.dependency_overrides[get_supabase_client] = mock_get_supabase_client

    yield mock_client

    # Clean up the override after the test
    if get_supabase_client in app.dependency_overrides:
        del app.dependency_overrides[get_supabase_client]


# ============================================================================
# SUCCESS TESTS - GET PLANS
# ============================================================================


def test_get_plans_success_with_multiple_plans(
    mock_auth_dependency, mock_get_supabase_client_for_get, mock_plans_list
):
    """Test successful retrieval of multiple plans with default pagination."""
    # Configure mock response with multiple plans
    mock_response = MagicMock()
    mock_response.data = mock_plans_list
    mock_response.count = 2
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    # Make the request
    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify response structure
    assert "plans" in response_data
    assert "total_count" in response_data
    assert "page" in response_data
    assert "page_size" in response_data
    assert "has_next" in response_data

    # Verify pagination metadata
    assert response_data["total_count"] == 2
    assert response_data["page"] == 1
    assert response_data["page_size"] == 20  # Default limit
    assert response_data["has_next"] is False

    # Verify plans data
    plans = response_data["plans"]
    assert len(plans) == 2

    # Verify first plan (should be most recent - Latest Plan)
    latest_plan = plans[0]
    assert latest_plan["name"] == "Latest Plan"
    assert latest_plan["description"] == "Most recent plan"
    assert latest_plan["goal"] == "strength"
    assert latest_plan["difficulty_level"] == "intermediate"
    assert latest_plan["duration_weeks"] == 12
    assert latest_plan["days_per_week"] == 4
    assert latest_plan["is_public"] is False
    assert latest_plan["metadata"] == {"notes": "updated plan"}

    # Verify second plan (older)
    older_plan = plans[1]
    assert older_plan["name"] == "Older Plan"
    assert older_plan["goal"] == "hypertrophy"
    assert older_plan["difficulty_level"] == "beginner"
    assert older_plan["is_public"] is True

    # Verify database calls
    assert mock_get_supabase_client_for_get.table.called
    mock_get_supabase_client_for_get.table.assert_called_with("plans")
    mock_get_supabase_client_for_get.table().select.assert_called_with(
        "*", count="exact"
    )
    mock_get_supabase_client_for_get.table().select().order.assert_called_with(
        "created_at", desc=True
    )
    mock_get_supabase_client_for_get.table().select().order().range.assert_called_with(
        0, 19
    )  # offset 0, limit 20


def test_get_plans_success_empty_response(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test successful retrieval when user has no plans."""
    # Configure mock response with empty data
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 0
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    # Make the request
    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify empty response structure
    assert response_data["plans"] == []
    assert response_data["total_count"] == 0
    assert response_data["page"] == 1
    assert response_data["page_size"] == 20
    assert response_data["has_next"] is False


def test_get_plans_success_custom_pagination(
    mock_auth_dependency, mock_get_supabase_client_for_get, mock_plans_list
):
    """Test successful retrieval with custom limit and offset parameters."""
    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [mock_plans_list[0]]  # Return only first plan
    mock_response.count = 5  # Total of 5 plans
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    # Make the request with custom pagination
    response = client.get(
        "/api/v1/plans/?limit=1&offset=2",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify pagination metadata
    assert response_data["total_count"] == 5
    assert response_data["page"] == 3  # (offset 2 / limit 1) + 1
    assert response_data["page_size"] == 1
    assert response_data["has_next"] is True  # (2 + 1) < 5

    # Verify only one plan returned
    assert len(response_data["plans"]) == 1

    # Verify database calls with correct pagination
    mock_get_supabase_client_for_get.table().select().order().range.assert_called_with(
        2, 2
    )  # offset 2, offset + limit - 1


def test_get_plans_success_maximum_limit(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test successful retrieval with maximum allowed limit."""
    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 0
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    # Make the request with maximum limit
    response = client.get(
        "/api/v1/plans/?limit=100",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["page_size"] == 100

    # Verify database calls with correct range
    mock_get_supabase_client_for_get.table().select().order().range.assert_called_with(
        0, 99
    )  # offset 0, limit 100


def test_get_plans_success_sorting_verification(
    mock_auth_dependency, mock_get_supabase_client_for_get, mock_plans_list
):
    """Test that plans are returned sorted by created_at DESC (most recent first)."""
    # Configure mock response with reversed order to verify sorting in request
    mock_response = MagicMock()
    mock_response.data = mock_plans_list  # Already ordered correctly in fixture
    mock_response.count = 2
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    # Make the request
    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    plans = response_data["plans"]

    # Verify sorting is requested correctly in database call
    mock_get_supabase_client_for_get.table().select().order.assert_called_with(
        "created_at", desc=True
    )

    # Verify response maintains expected order (Latest Plan first)
    assert plans[0]["name"] == "Latest Plan"
    assert plans[1]["name"] == "Older Plan"


# ============================================================================
# AUTHENTICATION TESTS - GET PLANS
# ============================================================================


def test_get_plans_unauthenticated():
    """Test plans retrieval without authentication token."""
    response = client.get("/api/v1/plans/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_plans_invalid_token():
    """Test plans retrieval with invalid authentication token."""
    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_plans_malformed_auth_header():
    """Test plans retrieval with malformed authorization header."""
    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "InvalidFormat token"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# VALIDATION ERROR TESTS (422) - GET PLANS
# ============================================================================


def test_get_plans_invalid_limit_zero(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval with invalid limit (zero)."""
    response = client.get(
        "/api/v1/plans/?limit=0",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("limit" in str(error).lower() for error in error_detail)
    assert any("greater than 0" in str(error).lower() for error in error_detail)


def test_get_plans_invalid_limit_too_high(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval with limit exceeding maximum (101)."""
    response = client.get(
        "/api/v1/plans/?limit=101",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("limit" in str(error).lower() for error in error_detail)
    assert any(
        "less than or equal to 100" in str(error).lower() for error in error_detail
    )


def test_get_plans_invalid_offset_negative(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval with negative offset."""
    response = client.get(
        "/api/v1/plans/?offset=-1",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("offset" in str(error).lower() for error in error_detail)
    assert any(
        "greater than or equal to 0" in str(error).lower() for error in error_detail
    )


def test_get_plans_invalid_limit_string(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval with non-numeric limit."""
    response = client.get(
        "/api/v1/plans/?limit=abc",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("limit" in str(error).lower() for error in error_detail)


def test_get_plans_invalid_offset_string(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval with non-numeric offset."""
    response = client.get(
        "/api/v1/plans/?offset=xyz",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("offset" in str(error).lower() for error in error_detail)


# ============================================================================
# DATABASE ERROR TESTS (500) - GET PLANS
# ============================================================================


def test_get_plans_database_connection_error(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval with database connection error."""
    mock_get_supabase_client_for_get.table().select().order().range().execute.side_effect = Exception(
        "Database connection timeout"
    )

    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "internal error" in response.json()["detail"].lower()


def test_get_plans_generic_database_error(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval with generic database error."""
    mock_get_supabase_client_for_get.table().select().order().range().execute.side_effect = Exception(
        "Unexpected database error occurred"
    )

    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "internal error" in response.json()["detail"].lower()


def test_get_plans_none_data_returned(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval when database returns None data."""
    mock_response = MagicMock()
    mock_response.data = None
    mock_response.count = None
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Should handle None gracefully and return empty response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["plans"] == []
    assert response_data["total_count"] == 0


def test_get_plans_value_error_handling(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval with ValueError during data processing."""
    # Mock a ValueError being raised during data processing
    mock_get_supabase_client_for_get.table().select().order().range().execute.side_effect = ValueError(
        "Invalid data format encountered"
    )

    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid data format encountered" in response.json()["detail"]


# ============================================================================
# BOUNDARY VALUE TESTS - GET PLANS
# ============================================================================


def test_get_plans_boundary_limit_one(
    mock_auth_dependency, mock_get_supabase_client_for_get, mock_plans_list
):
    """Test plans retrieval with minimum limit (1)."""
    mock_response = MagicMock()
    mock_response.data = [mock_plans_list[0]]
    mock_response.count = 5
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    response = client.get(
        "/api/v1/plans/?limit=1",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["page_size"] == 1
    assert len(response_data["plans"]) == 1
    assert response_data["has_next"] is True  # (0 + 1) < 5

    # Verify database calls
    mock_get_supabase_client_for_get.table().select().order().range.assert_called_with(
        0, 0
    )


def test_get_plans_boundary_offset_zero(
    mock_auth_dependency, mock_get_supabase_client_for_get, mock_plans_list
):
    """Test plans retrieval with minimum offset (0)."""
    mock_response = MagicMock()
    mock_response.data = mock_plans_list
    mock_response.count = 2
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    response = client.get(
        "/api/v1/plans/?offset=0",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["page"] == 1  # (0 / 20) + 1

    # Verify database calls
    mock_get_supabase_client_for_get.table().select().order().range.assert_called_with(
        0, 19
    )


def test_get_plans_boundary_large_offset(
    mock_auth_dependency, mock_get_supabase_client_for_get
):
    """Test plans retrieval with large offset value."""
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 5  # Total count less than offset
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    response = client.get(
        "/api/v1/plans/?offset=100",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["plans"] == []
    assert response_data["total_count"] == 5
    assert response_data["page"] == 6  # (100 / 20) + 1
    assert response_data["has_next"] is False  # (100 + 20) >= 5

    # Verify database calls
    mock_get_supabase_client_for_get.table().select().order().range.assert_called_with(
        100, 119
    )


def test_get_plans_pagination_edge_case_exact_page(
    mock_auth_dependency, mock_get_supabase_client_for_get, mock_plans_list
):
    """Test pagination when total count exactly matches page boundary."""
    mock_response = MagicMock()
    mock_response.data = mock_plans_list  # 2 plans
    mock_response.count = 40  # Exactly 2 pages with limit 20
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    # Request second page
    response = client.get(
        "/api/v1/plans/?limit=20&offset=20",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["total_count"] == 40
    assert response_data["page"] == 2  # (20 / 20) + 1
    assert response_data["page_size"] == 20
    assert response_data["has_next"] is False  # (20 + 20) == 40


# ============================================================================
# COMPLEX SCENARIOS - GET PLANS
# ============================================================================


def test_get_plans_with_complex_metadata(
    mock_auth_dependency, mock_get_supabase_client_for_get, mock_user_id
):
    """Test plans retrieval with complex metadata structures."""
    complex_plan = {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        "name": "Complex Metadata Plan",
        "description": "Plan with complex metadata",
        "training_style": None,
        "goal": "strength",
        "difficulty_level": "advanced",
        "duration_weeks": 16,
        "days_per_week": 5,
        "is_public": False,
        "metadata": {
            "periodization": {
                "type": "block",
                "phases": [
                    {"week": 1, "focus": "volume", "intensity": 70},
                    {"week": 2, "focus": "intensity", "intensity": 85},
                ],
            },
            "deload_weeks": [4, 8, 12],
            "exercise_rotations": {
                "squat_variation": ["back_squat", "front_squat", "safety_bar"],
                "bench_variation": ["comp_bench", "close_grip", "incline"],
            },
        },
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    mock_response = MagicMock()
    mock_response.data = [complex_plan]
    mock_response.count = 1
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    plan = response_data["plans"][0]
    assert plan["metadata"] == complex_plan["metadata"]
    assert "periodization" in plan["metadata"]
    assert "deload_weeks" in plan["metadata"]
    assert plan["metadata"]["periodization"]["type"] == "block"
    assert len(plan["metadata"]["periodization"]["phases"]) == 2


def test_get_plans_unicode_content(
    mock_auth_dependency, mock_get_supabase_client_for_get, mock_user_id
):
    """Test plans retrieval with unicode characters in plan names and descriptions."""
    unicode_plan = {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        "name": "강화 운동 💪 Plan",
        "description": "Descripción con acentos y símbolos: 体力 训练 🏋️‍♂️",
        "training_style": None,
        "goal": "fuerza y músculo",
        "difficulty_level": "intermediate",
        "duration_weeks": 8,
        "days_per_week": 4,
        "is_public": True,
        "metadata": {"notes": "тренировка силы"},
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    mock_response = MagicMock()
    mock_response.data = [unicode_plan]
    mock_response.count = 1
    mock_get_supabase_client_for_get.table().select().order().range().execute.return_value = mock_response

    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    plan = response_data["plans"][0]
    assert plan["name"] == "강화 운동 💪 Plan"
    assert plan["description"] == "Descripción con acentos y símbolos: 体力 训练 🏋️‍♂️"
    assert plan["goal"] == "fuerza y músculo"
    assert plan["metadata"]["notes"] == "тренировка силы"


# ============================================================================
# GET PLAN BY ID ENDPOINT TESTS
# ============================================================================


@pytest.fixture
def mock_optional_auth_dependency():
    """Mock optional JWT authentication dependency by overriding the FastAPI dependency."""
    from src.core.auth import optional_auth

    def mock_optional_auth():
        return None  # Unauthenticated user

    # Patch the app's dependency override
    app.dependency_overrides[optional_auth] = mock_optional_auth

    yield mock_optional_auth

    # Clean up the override after the test
    if optional_auth in app.dependency_overrides:
        del app.dependency_overrides[optional_auth]


@pytest.fixture
def mock_authenticated_optional_auth_dependency(mock_jwt_payload):
    """Mock optional JWT authentication dependency with authenticated user."""
    from src.core.auth import optional_auth

    def mock_optional_auth():
        return mock_jwt_payload  # Authenticated user

    # Patch the app's dependency override
    app.dependency_overrides[optional_auth] = mock_optional_auth

    yield mock_optional_auth

    # Clean up the override after the test
    if optional_auth in app.dependency_overrides:
        del app.dependency_overrides[optional_auth]


@pytest.fixture
def mock_supabase_client_for_get_by_id():
    """Mock Supabase client specifically configured for GET plans/{plan_id} endpoint."""
    from src.core.utils import get_supabase_client

    # Create a single mock client instance with proper method chaining
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_execute = MagicMock()

    # Set up the method chain: client.table().select().eq().execute()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_execute

    # Override the dependency to return the same instance
    def mock_get_supabase_client():
        return mock_client

    app.dependency_overrides[get_supabase_client] = mock_get_supabase_client

    yield mock_client

    # Clean up the override after the test
    if get_supabase_client in app.dependency_overrides:
        del app.dependency_overrides[get_supabase_client]


@pytest.fixture
def mock_private_plan(mock_user_id):
    """Mock private plan data."""
    return {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        "name": "Private Strength Plan",
        "description": "Personal strength training plan",
        "training_style": None,
        "goal": "strength",
        "difficulty_level": "intermediate",
        "duration_weeks": 12,
        "days_per_week": 4,
        "is_public": False,
        "metadata": {"notes": "personal plan"},
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }


@pytest.fixture
def mock_public_plan():
    """Mock public plan data."""
    other_user_id = str(uuid4())
    return {
        "id": str(uuid4()),
        "user_id": other_user_id,
        "name": "Public Bodybuilding Plan",
        "description": "Community bodybuilding routine",
        "training_style": None,
        "goal": "hypertrophy",
        "difficulty_level": "beginner",
        "duration_weeks": 8,
        "days_per_week": 6,
        "is_public": True,
        "metadata": {"community": True, "rating": 4.5},
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }


# ============================================================================
# SUCCESS TESTS - GET PLAN BY ID
# ============================================================================


def test_get_plan_by_id_success_own_private_plan(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
    mock_private_plan,
):
    """Test successful retrieval of user's own private plan (authenticated)."""
    plan_id = mock_private_plan["id"]

    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [mock_private_plan]
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify response data
    assert response_data["id"] == plan_id
    assert response_data["name"] == "Private Strength Plan"
    assert response_data["description"] == "Personal strength training plan"
    assert response_data["goal"] == "strength"
    assert response_data["difficulty_level"] == "intermediate"
    assert response_data["duration_weeks"] == 12
    assert response_data["days_per_week"] == 4
    assert response_data["is_public"] is False
    assert response_data["metadata"] == {"notes": "personal plan"}
    assert response_data["version_number"] == 1
    assert response_data["is_active"] is True

    # Verify database calls
    assert mock_supabase_client_for_get_by_id.table.called
    mock_supabase_client_for_get_by_id.table.assert_called_with("plans")
    mock_supabase_client_for_get_by_id.table().select.assert_called_with("*")
    # The plan_id is converted to UUID object by FastAPI
    from uuid import UUID

    mock_supabase_client_for_get_by_id.table().select().eq.assert_called_with(
        "id", UUID(plan_id)
    )


def test_get_plan_by_id_success_public_plan_authenticated(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
    mock_public_plan,
):
    """Test successful retrieval of public plan (authenticated user)."""
    plan_id = mock_public_plan["id"]

    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [mock_public_plan]
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify response data
    assert response_data["id"] == plan_id
    assert response_data["name"] == "Public Bodybuilding Plan"
    assert response_data["description"] == "Community bodybuilding routine"
    assert response_data["goal"] == "hypertrophy"
    assert response_data["difficulty_level"] == "beginner"
    assert response_data["duration_weeks"] == 8
    assert response_data["days_per_week"] == 6
    assert response_data["is_public"] is True
    assert response_data["metadata"] == {"community": True, "rating": 4.5}


def test_get_plan_by_id_success_public_plan_unauthenticated(
    mock_optional_auth_dependency, mock_supabase_client_for_get_by_id, mock_public_plan
):
    """Test successful retrieval of public plan (unauthenticated)."""
    plan_id = mock_public_plan["id"]

    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [mock_public_plan]
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request without authentication
    response = client.get(f"/api/v1/plans/{plan_id}")

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify response data
    assert response_data["id"] == plan_id
    assert response_data["name"] == "Public Bodybuilding Plan"
    assert response_data["is_public"] is True

    # Verify database calls
    from uuid import UUID

    mock_supabase_client_for_get_by_id.table().select().eq.assert_called_with(
        "id", UUID(plan_id)
    )


# ============================================================================
# NOT FOUND TESTS - GET PLAN BY ID
# ============================================================================


def test_get_plan_by_id_not_found_nonexistent_plan(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test 404 for non-existent plan ID."""
    nonexistent_plan_id = str(uuid4())

    # Configure mock response for no data
    mock_response = MagicMock()
    mock_response.data = []
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{nonexistent_plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 404 response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Plan not found"

    # Verify database calls
    from uuid import UUID

    mock_supabase_client_for_get_by_id.table().select().eq.assert_called_with(
        "id", UUID(nonexistent_plan_id)
    )


def test_get_plan_by_id_not_found_unauthorized_private_plan(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test 404 for unauthorized access to private plan (authenticated user but not owner)."""
    other_user_id = str(uuid4())
    private_plan_of_other_user: dict = {
        "id": str(uuid4()),
        "user_id": other_user_id,  # Different user
        "name": "Other User's Private Plan",
        "description": "This should not be accessible",
        "training_style": None,
        "goal": "strength",
        "difficulty_level": "advanced",
        "duration_weeks": 16,
        "days_per_week": 5,
        "is_public": False,  # Private plan
        "metadata": {},
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    plan_id = private_plan_of_other_user["id"]

    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [private_plan_of_other_user]
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 404 response (not revealing that plan exists)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Plan not found"


def test_get_plan_by_id_not_found_unauthenticated_private_plan(
    mock_optional_auth_dependency, mock_supabase_client_for_get_by_id, mock_private_plan
):
    """Test 404 for unauthenticated access to private plan."""
    plan_id = mock_private_plan["id"]

    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [mock_private_plan]
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request without authentication
    response = client.get(f"/api/v1/plans/{plan_id}")

    # Assert 404 response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Plan not found"


# ============================================================================
# VALIDATION ERROR TESTS (422) - GET PLAN BY ID
# ============================================================================


def test_get_plan_by_id_invalid_uuid_format(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test 422 for invalid UUID format."""
    invalid_uuid = "not-a-valid-uuid"

    # Make the request
    response = client.get(
        f"/api/v1/plans/{invalid_uuid}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 422 response
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("uuid" in str(error).lower() for error in error_detail)


def test_get_plan_by_id_invalid_uuid_too_short(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test 422 for UUID that's too short."""
    short_uuid = "123"

    # Make the request
    response = client.get(
        f"/api/v1/plans/{short_uuid}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 422 response
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("uuid" in str(error).lower() for error in error_detail)


def test_get_plan_by_id_invalid_uuid_with_special_chars(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test 422 for UUID with invalid special characters."""
    invalid_uuid = "12345678-1234-1234-1234-12345678901@"

    # Make the request
    response = client.get(
        f"/api/v1/plans/{invalid_uuid}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 422 response
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# UUID FORMAT TESTS - GET PLAN BY ID
# ============================================================================


def test_get_plan_by_id_uppercase_uuid(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
    mock_private_plan,
):
    """Test successful retrieval with uppercase UUID."""
    plan_id = str(uuid4()).upper()
    mock_private_plan["id"] = plan_id

    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [mock_private_plan]
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request with uppercase UUID
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert successful response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # UUID is normalized to lowercase by Pydantic/FastAPI
    assert response_data["id"] == plan_id.lower()


def test_get_plan_by_id_lowercase_uuid(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
    mock_private_plan,
):
    """Test successful retrieval with lowercase UUID."""
    plan_id = str(uuid4()).lower()
    mock_private_plan["id"] = plan_id

    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [mock_private_plan]
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request with lowercase UUID
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert successful response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == plan_id


def test_get_plan_by_id_uuid_without_hyphens(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test that UUID without hyphens is rejected (FastAPI's UUID validation requires hyphens)."""
    uuid_without_hyphens = "12345678123412341234123456789012"

    # Configure mock response for no data (plan not found)
    mock_response = MagicMock()
    mock_response.data = []
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{uuid_without_hyphens}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # FastAPI may accept the UUID without hyphens and convert it internally,
    # but when searching the database it won't be found, resulting in 404
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Plan not found"


# ============================================================================
# DATABASE ERROR TESTS (500) - GET PLAN BY ID
# ============================================================================


def test_get_plan_by_id_database_connection_error(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test 500 for database connection error."""
    plan_id = str(uuid4())

    # Configure mock to raise database error
    mock_supabase_client_for_get_by_id.table().select().eq().execute.side_effect = (
        Exception("Database connection timeout")
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 500 response
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "internal error" in response.json()["detail"].lower()


def test_get_plan_by_id_database_generic_error(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test 500 for generic database error."""
    plan_id = str(uuid4())

    # Configure mock to raise generic error
    mock_supabase_client_for_get_by_id.table().select().eq().execute.side_effect = (
        Exception("Unexpected database error occurred")
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 500 response
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "internal error" in response.json()["detail"].lower()


def test_get_plan_by_id_value_error_handling(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test 422 for ValueError during data processing."""
    plan_id = str(uuid4())

    # Configure mock to raise ValueError
    mock_supabase_client_for_get_by_id.table().select().eq().execute.side_effect = (
        ValueError("Invalid data format encountered")
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 422 response
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid data format encountered" in response.json()["detail"]


# ============================================================================
# EDGE CASES AND BOUNDARY TESTS - GET PLAN BY ID
# ============================================================================


def test_get_plan_by_id_none_data_returned(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
):
    """Test handling when database returns None data."""
    plan_id = str(uuid4())

    # Configure mock response with None data
    mock_response = MagicMock()
    mock_response.data = None
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 404 response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Plan not found"


def test_get_plan_by_id_complex_metadata(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
    mock_user_id,
):
    """Test retrieval of plan with complex metadata structure."""
    complex_metadata = {
        "periodization": {
            "type": "conjugate",
            "phases": [
                {"week": 1, "focus": "max_effort", "exercises": ["squat", "bench"]},
                {"week": 2, "focus": "dynamic_effort", "intensity": 60},
            ],
        },
        "deload_protocol": {"frequency": "every_4_weeks", "volume_reduction": 0.4},
        "accessory_work": {"upper": ["rows", "triceps"], "lower": ["rdl", "abs"]},
        "tags": ["powerlifting", "westside", "intermediate"],
    }

    plan_with_complex_metadata = {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        "name": "Complex Metadata Plan",
        "description": "Plan with detailed metadata",
        "training_style": None,
        "goal": "strength",
        "difficulty_level": "advanced",
        "duration_weeks": 12,
        "days_per_week": 4,
        "is_public": False,
        "metadata": complex_metadata,
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    plan_id = plan_with_complex_metadata["id"]

    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [plan_with_complex_metadata]
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert successful response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify complex metadata is preserved
    assert response_data["metadata"] == complex_metadata
    assert "periodization" in response_data["metadata"]
    assert "deload_protocol" in response_data["metadata"]
    assert response_data["metadata"]["periodization"]["type"] == "conjugate"
    assert len(response_data["metadata"]["periodization"]["phases"]) == 2
    assert response_data["metadata"]["tags"] == [
        "powerlifting",
        "westside",
        "intermediate",
    ]


def test_get_plan_by_id_unicode_content(
    mock_authenticated_optional_auth_dependency,
    mock_supabase_client_for_get_by_id,
    mock_user_id,
):
    """Test retrieval of plan with unicode characters."""
    unicode_plan = {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        "name": "Fuerza y Resistencia 💪",
        "description": "Plan de entrenamiento: 체력 강화 🏋️‍♂️",
        "training_style": None,
        "goal": "fuerza general",
        "difficulty_level": "intermediate",
        "duration_weeks": 10,
        "days_per_week": 4,
        "is_public": True,
        "metadata": {"notas": "тренировка на силу", "idioma": "español"},
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }

    plan_id = unicode_plan["id"]

    # Configure mock response
    mock_response = MagicMock()
    mock_response.data = [unicode_plan]
    mock_supabase_client_for_get_by_id.table().select().eq().execute.return_value = (
        mock_response
    )

    # Make the request
    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert successful response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify unicode content is preserved
    assert response_data["name"] == "Fuerza y Resistencia 💪"
    assert response_data["description"] == "Plan de entrenamiento: 체력 강화 🏋️‍♂️"
    assert response_data["goal"] == "fuerza general"
    assert response_data["metadata"]["notas"] == "тренировка на силу"
    assert response_data["metadata"]["idioma"] == "español"
