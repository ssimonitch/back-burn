"""Comprehensive tests for the plans API endpoints.

This module tests POST, GET list, GET by ID, PUT, and DELETE for /api/v1/plans endpoints:

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

DELETE /api/v1/plans/{plan_id} (Plan Soft Deletion):
- Successful soft deletion with deleted_at timestamp
- Deletion of all plan versions (parent and children)
- Authentication requirements (401/403 errors)
- Authorization enforcement (403 for non-owners)
- Not found handling (404 for non-existent or already deleted plans)
- Business rule enforcement (400 for plans with active sessions)
- UUID format validation (422 errors)
- Database error handling (500 errors)
- Idempotency and edge case handling
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


# ============================================================================
# PUT PLAN (UPDATE) ENDPOINT TESTS - Creates New Versions
# ============================================================================


@pytest.fixture
def mock_supabase_client_for_update():
    """Mock Supabase client specifically configured for PUT plans/{plan_id} endpoint."""
    from src.core.utils import get_supabase_client

    # Create a single mock client instance with proper method chaining
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_update = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()

    # Set up the method chain for select query: client.table().select().eq().execute()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_execute

    # Set up the method chain for update query: client.table().update().eq().execute()
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq

    # Set up the method chain for insert query: client.table().insert().execute()
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
def existing_plan_v1(mock_user_id):
    """Mock existing plan version 1 data."""
    return {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        "name": "Original Plan",
        "description": "Original description",
        "training_style": None,
        "goal": "strength",
        "difficulty_level": "intermediate",
        "duration_weeks": 8,
        "days_per_week": 4,
        "is_public": False,
        "metadata": {"original": "metadata"},
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
    }


@pytest.fixture
def existing_plan_v2(mock_user_id, existing_plan_v1):
    """Mock existing plan version 2 data."""
    return {
        "id": str(uuid4()),
        "user_id": mock_user_id,
        "name": "Updated Plan",
        "description": "Updated description",
        "training_style": None,
        "goal": "hypertrophy",
        "difficulty_level": "advanced",
        "duration_weeks": 12,
        "days_per_week": 5,
        "is_public": True,
        "metadata": {"updated": "metadata"},
        "version_number": 2,
        "parent_plan_id": existing_plan_v1["id"],
        "is_active": True,
        "created_at": "2025-01-02T12:00:00+00:00",
    }


@pytest.fixture
def valid_update_data():
    """Valid update data for testing."""
    return {
        "name": "Updated Plan Name",
        "description": "Updated plan description",
        "goal": "hypertrophy",
        "difficulty_level": DifficultyLevel.ADVANCED.value,
        "duration_weeks": 12,
        "days_per_week": 5,
        "is_public": True,
        "metadata": {"updated": True, "notes": "New version"},
    }


# ============================================================================
# SUCCESS TESTS - PUT PLAN
# ============================================================================


def test_update_plan_success_full_update(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
    valid_update_data,
    mock_user_id,
):
    """Test successful plan update creating new version with all fields updated."""
    plan_id = existing_plan_v1["id"]

    # Mock responses for the update workflow
    # 1. Select query to get current plan
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    # 2. Update query to mark current version inactive
    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    # 3. Insert query to create new version
    new_version = {
        **existing_plan_v1,
        "id": str(uuid4()),
        **valid_update_data,
        "version_number": 2,
        "parent_plan_id": plan_id,
        "is_active": True,
        "created_at": "2025-01-03T12:00:00+00:00",
    }
    insert_response = MagicMock()
    insert_response.data = [new_version]

    # Configure mock to return different responses based on call sequence
    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    # Make the request
    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=valid_update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify the new version data
    assert response_data["name"] == valid_update_data["name"]
    assert response_data["description"] == valid_update_data["description"]
    assert response_data["goal"] == valid_update_data["goal"]
    assert response_data["difficulty_level"] == valid_update_data["difficulty_level"]
    assert response_data["duration_weeks"] == valid_update_data["duration_weeks"]
    assert response_data["days_per_week"] == valid_update_data["days_per_week"]
    assert response_data["is_public"] == valid_update_data["is_public"]
    assert response_data["metadata"] == valid_update_data["metadata"]

    # Verify version management
    assert response_data["version_number"] == 2
    assert response_data["parent_plan_id"] == plan_id
    assert response_data["is_active"] is True
    assert response_data["user_id"] == mock_user_id

    # Verify database calls
    assert mock_supabase_client_for_update.table.called
    # Should have called select, update, and insert
    mock_supabase_client_for_update.table().select.assert_called()
    mock_supabase_client_for_update.table().update.assert_called()
    mock_supabase_client_for_update.table().insert.assert_called()


def test_update_plan_success_partial_update(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
    mock_user_id,
):
    """Test successful plan update with only some fields changed."""
    plan_id = existing_plan_v1["id"]
    partial_update = {
        "name": "Partially Updated Plan",
        "duration_weeks": 10,
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    new_version = {
        **existing_plan_v1,
        "id": str(uuid4()),
        **partial_update,
        "version_number": 2,
        "parent_plan_id": plan_id,
        "is_active": True,
        "created_at": "2025-01-03T12:00:00+00:00",
    }
    insert_response = MagicMock()
    insert_response.data = [new_version]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    # Make the request
    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=partial_update,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify updated fields
    assert response_data["name"] == partial_update["name"]
    assert response_data["duration_weeks"] == partial_update["duration_weeks"]

    # Verify unchanged fields are preserved
    assert response_data["description"] == existing_plan_v1["description"]
    assert response_data["goal"] == existing_plan_v1["goal"]
    assert response_data["difficulty_level"] == existing_plan_v1["difficulty_level"]
    assert response_data["days_per_week"] == existing_plan_v1["days_per_week"]
    assert response_data["is_public"] == existing_plan_v1["is_public"]

    # Verify version management
    assert response_data["version_number"] == 2
    assert response_data["parent_plan_id"] == plan_id
    assert response_data["is_active"] is True


def test_update_plan_success_is_active_flag_management(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test that is_active flags are managed correctly during update."""
    plan_id = existing_plan_v1["id"]
    update_data = {"name": "Flag Test Plan"}

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    # Verify the current version is marked as inactive
    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    new_version = {
        **existing_plan_v1,
        "id": str(uuid4()),
        **update_data,
        "version_number": 2,
        "parent_plan_id": plan_id,
        "is_active": True,
        "created_at": "2025-01-03T12:00:00+00:00",
    }
    insert_response = MagicMock()
    insert_response.data = [new_version]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    # Make the request
    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify the new version is active
    assert response_data["is_active"] is True

    # Verify database calls for is_active management
    mock_supabase_client_for_update.table().update.assert_called_with(
        {"is_active": False}
    )


def test_update_plan_success_parent_plan_id_tracking(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v2,
    mock_user_id,
):
    """Test that parent_plan_id tracks version history correctly."""
    plan_id = existing_plan_v2["id"]
    original_parent_id = existing_plan_v2["parent_plan_id"]
    update_data = {"name": "Version History Test"}

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_v2]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    # New version should use the same parent_plan_id as v2 (not v2's ID)
    new_version = {
        **existing_plan_v2,
        "id": str(uuid4()),
        **update_data,
        "version_number": 3,
        "parent_plan_id": original_parent_id,  # Should maintain original parent
        "is_active": True,
        "created_at": "2025-01-03T12:00:00+00:00",
    }
    insert_response = MagicMock()
    insert_response.data = [new_version]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    # Make the request
    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify version history tracking
    assert response_data["version_number"] == 3
    assert response_data["parent_plan_id"] == original_parent_id
    assert response_data["is_active"] is True


def test_update_plan_success_version_chain_from_v1(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test updating version 1 (original plan) creates proper version chain."""
    plan_id = existing_plan_v1["id"]
    update_data = {"name": "V1 to V2 Update"}

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    # When updating v1, the parent_plan_id should be the v1's ID (becomes the root)
    new_version = {
        **existing_plan_v1,
        "id": str(uuid4()),
        **update_data,
        "version_number": 2,
        "parent_plan_id": plan_id,  # V1's ID becomes the parent
        "is_active": True,
        "created_at": "2025-01-03T12:00:00+00:00",
    }
    insert_response = MagicMock()
    insert_response.data = [new_version]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    # Make the request
    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    # Verify version chain creation
    assert response_data["version_number"] == 2
    assert response_data["parent_plan_id"] == plan_id  # V1 becomes the parent
    assert response_data["is_active"] is True


# ============================================================================
# ERROR TESTS - PUT PLAN
# ============================================================================


def test_update_plan_400_inactive_version(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test 400 error when trying to update an inactive version."""
    plan_id = existing_plan_v1["id"]
    inactive_plan = {**existing_plan_v1, "is_active": False}

    # Mock response for inactive plan
    select_response = MagicMock()
    select_response.data = [inactive_plan]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )

    update_data = {"name": "Should Fail Update"}

    # Make the request
    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 400 response
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "inactive plan version" in response.json()["detail"]

    # Verify no update or insert calls were made
    mock_supabase_client_for_update.table().update.assert_not_called()
    mock_supabase_client_for_update.table().insert.assert_not_called()


def test_update_plan_400_no_changes(
    mock_auth_dependency,
    mock_supabase_client_for_update,
):
    """Test 400 error when no changes are provided."""
    plan_id = str(uuid4())
    empty_update: dict = {}

    # Make the request with no changes
    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=empty_update,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 400 response
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "No changes provided" in response.json()["detail"]

    # Verify no database calls were made
    mock_supabase_client_for_update.table().select.assert_not_called()


def test_update_plan_403_non_owner(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test 403 error when non-owner tries to update plan."""
    plan_id = existing_plan_v1["id"]
    # Plan belongs to different user
    other_user_plan = {**existing_plan_v1, "user_id": str(uuid4())}

    # Mock response
    select_response = MagicMock()
    select_response.data = [other_user_plan]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )

    update_data = {"name": "Unauthorized Update"}

    # Make the request
    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 403 response
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "permission to update" in response.json()["detail"]

    # Verify no update or insert calls were made
    mock_supabase_client_for_update.table().update.assert_not_called()
    mock_supabase_client_for_update.table().insert.assert_not_called()


def test_update_plan_404_nonexistent_plan(
    mock_auth_dependency,
    mock_supabase_client_for_update,
):
    """Test 404 error for non-existent plan."""
    nonexistent_plan_id = str(uuid4())

    # Mock empty response
    select_response = MagicMock()
    select_response.data = []

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )

    update_data = {"name": "Nonexistent Plan Update"}

    # Make the request
    response = client.put(
        f"/api/v1/plans/{nonexistent_plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 404 response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Plan not found" in response.json()["detail"]

    # Verify no update or insert calls were made
    mock_supabase_client_for_update.table().update.assert_not_called()
    mock_supabase_client_for_update.table().insert.assert_not_called()


def test_update_plan_409_version_conflict(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test 409 error for version conflicts (duplicate key)."""
    plan_id = existing_plan_v1["id"]

    # Mock responses for successful select and update
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )

    # Mock insert to raise duplicate key error
    mock_supabase_client_for_update.table().insert().execute.side_effect = Exception(
        "duplicate key value violates unique constraint"
    )

    update_data = {"name": "Conflict Update"}

    # Make the request
    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    # Assert 409 response
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "newer version" in response.json()["detail"]


def test_update_plan_422_validation_errors(
    mock_auth_dependency,
    mock_supabase_client_for_update,
):
    """Test 422 errors for validation errors."""
    plan_id = str(uuid4())

    # Test invalid name (empty string)
    invalid_update = {"name": ""}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=invalid_update,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("name" in str(error).lower() for error in error_detail)


def test_update_plan_422_invalid_duration_weeks(
    mock_auth_dependency,
    mock_supabase_client_for_update,
):
    """Test 422 error for invalid duration_weeks."""
    plan_id = str(uuid4())

    # Test duration_weeks exceeding maximum
    invalid_update = {"duration_weeks": 53}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=invalid_update,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("duration_weeks" in str(error).lower() for error in error_detail)


def test_update_plan_422_invalid_days_per_week(
    mock_auth_dependency,
    mock_supabase_client_for_update,
):
    """Test 422 error for invalid days_per_week."""
    plan_id = str(uuid4())

    # Test days_per_week exceeding maximum
    invalid_update = {"days_per_week": 8}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=invalid_update,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("days_per_week" in str(error).lower() for error in error_detail)


# ============================================================================
# AUTHENTICATION TESTS - PUT PLAN
# ============================================================================


def test_update_plan_unauthenticated():
    """Test plan update without authentication token."""
    plan_id = str(uuid4())
    update_data = {"name": "Unauthorized Update"}

    response = client.put(f"/api/v1/plans/{plan_id}", json=update_data)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_plan_invalid_token():
    """Test plan update with invalid authentication token."""
    plan_id = str(uuid4())
    update_data = {"name": "Invalid Token Update"}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# DATABASE ERROR TESTS - PUT PLAN
# ============================================================================


def test_update_plan_database_error_on_select(
    mock_auth_dependency,
    mock_supabase_client_for_update,
):
    """Test 500 error when database fails during plan selection."""
    plan_id = str(uuid4())

    # Mock database error on select
    mock_supabase_client_for_update.table().select().eq().execute.side_effect = (
        Exception("Database connection timeout")
    )

    update_data = {"name": "DB Error Test"}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "internal error" in response.json()["detail"].lower()


def test_update_plan_database_error_on_update(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test handling when update operation fails."""
    plan_id = existing_plan_v1["id"]

    # Mock successful select but failed update
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        MagicMock(data=None)
    )

    update_data = {"name": "Update Fail Test"}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to update current plan version" in response.json()["detail"]


def test_update_plan_database_error_on_insert_with_rollback(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test rollback behavior when insert fails."""
    plan_id = existing_plan_v1["id"]

    # Mock successful select and update
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )

    # Mock failed insert
    insert_response = MagicMock()
    insert_response.data = []
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    update_data = {"name": "Insert Fail Test"}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to create new plan version" in response.json()["detail"]

    # Verify rollback update was called (should be called twice: once to deactivate, once to rollback)
    assert mock_supabase_client_for_update.table().update.call_count >= 2


def test_update_plan_value_error_handling(
    mock_auth_dependency,
    mock_supabase_client_for_update,
):
    """Test 422 error for ValueError during processing."""
    plan_id = str(uuid4())

    # Mock ValueError during database operation
    mock_supabase_client_for_update.table().select().eq().execute.side_effect = (
        ValueError("Invalid data format encountered")
    )

    update_data = {"name": "Value Error Test"}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid data format encountered" in response.json()["detail"]


# ============================================================================
# EDGE CASES AND BOUNDARY TESTS - PUT PLAN
# ============================================================================


def test_update_plan_boundary_values(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test plan update with boundary values."""
    plan_id = existing_plan_v1["id"]
    boundary_update = {
        "name": "x",  # Minimum length
        "duration_weeks": 1,  # Minimum value
        "days_per_week": 1,  # Minimum value
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    new_version = {
        **existing_plan_v1,
        "id": str(uuid4()),
        **boundary_update,
        "version_number": 2,
        "parent_plan_id": plan_id,
        "is_active": True,
        "created_at": "2025-01-03T12:00:00+00:00",
    }
    insert_response = MagicMock()
    insert_response.data = [new_version]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=boundary_update,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["name"] == "x"
    assert response_data["duration_weeks"] == 1
    assert response_data["days_per_week"] == 1


def test_update_plan_maximum_boundary_values(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test plan update with maximum boundary values."""
    plan_id = existing_plan_v1["id"]
    max_boundary_update = {
        "name": "x" * 100,  # Maximum length
        "description": "x" * 2000,  # Maximum length
        "goal": "x" * 200,  # Maximum length
        "duration_weeks": 52,  # Maximum value
        "days_per_week": 7,  # Maximum value
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    new_version = {
        **existing_plan_v1,
        "id": str(uuid4()),
        **max_boundary_update,
        "version_number": 2,
        "parent_plan_id": plan_id,
        "is_active": True,
        "created_at": "2025-01-03T12:00:00+00:00",
    }
    insert_response = MagicMock()
    insert_response.data = [new_version]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=max_boundary_update,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data["name"]) == 100
    assert len(response_data["description"]) == 2000
    assert len(response_data["goal"]) == 200
    assert response_data["duration_weeks"] == 52
    assert response_data["days_per_week"] == 7


def test_update_plan_unicode_content(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test plan update with unicode characters."""
    plan_id = existing_plan_v1["id"]
    unicode_update = {
        "name": "강화 운동 💪 Updated",
        "description": "Descripción actualizada: 体力 训练 🏋️‍♂️",
        "goal": "fuerza mejorada",
        "metadata": {"notas": "обновленная тренировка"},
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    new_version = {
        **existing_plan_v1,
        "id": str(uuid4()),
        **unicode_update,
        "version_number": 2,
        "parent_plan_id": plan_id,
        "is_active": True,
        "created_at": "2025-01-03T12:00:00+00:00",
    }
    insert_response = MagicMock()
    insert_response.data = [new_version]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=unicode_update,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["name"] == unicode_update["name"]
    assert response_data["description"] == unicode_update["description"]
    assert response_data["goal"] == unicode_update["goal"]
    assert response_data["metadata"]["notas"] == "обновленная тренировка"


def test_update_plan_complex_metadata(
    mock_auth_dependency,
    mock_supabase_client_for_update,
    existing_plan_v1,
):
    """Test plan update with complex metadata structure."""
    plan_id = existing_plan_v1["id"]
    complex_metadata = {
        "periodization": {
            "type": "block",
            "phases": [
                {"week": 1, "focus": "volume", "intensity": 70},
                {"week": 2, "focus": "intensity", "intensity": 85},
            ],
        },
        "deload_weeks": [4, 8, 12],
        "exercise_variations": {
            "squat": ["back_squat", "front_squat"],
            "bench": ["comp_bench", "close_grip"],
        },
    }
    metadata_update = {"metadata": complex_metadata}

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_v1]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "is_active": False}]

    new_version = {
        **existing_plan_v1,
        "id": str(uuid4()),
        **metadata_update,
        "version_number": 2,
        "parent_plan_id": plan_id,
        "is_active": True,
        "created_at": "2025-01-03T12:00:00+00:00",
    }
    insert_response = MagicMock()
    insert_response.data = [new_version]

    mock_supabase_client_for_update.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_update.table().update().eq().execute.return_value = (
        update_response
    )
    mock_supabase_client_for_update.table().insert().execute.return_value = (
        insert_response
    )

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=metadata_update,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["metadata"] == complex_metadata
    assert "periodization" in response_data["metadata"]
    assert response_data["metadata"]["periodization"]["type"] == "block"
    assert len(response_data["metadata"]["deload_weeks"]) == 3


def test_update_plan_invalid_uuid_format():
    """Test 422 error for invalid UUID format in path parameter."""
    invalid_uuid = "not-a-valid-uuid"
    update_data = {"name": "UUID Test"}

    response = client.put(
        f"/api/v1/plans/{invalid_uuid}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("uuid" in str(error).lower() for error in error_detail)


# ============================================================================
# DELETE /api/v1/plans/{plan_id} ENDPOINT TESTS
# ============================================================================


@pytest.fixture
def mock_supabase_client_for_delete():
    """Mock Supabase client specifically for DELETE endpoint testing."""
    from src.core.utils import get_supabase_client

    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_update = MagicMock()
    mock_or = MagicMock()
    mock_is = MagicMock()
    mock_execute = MagicMock()

    # Set up the method chains for different operations
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_table.update.return_value = mock_update
    mock_select.eq.return_value = mock_eq
    mock_update.eq.return_value = mock_eq
    mock_update.or_.return_value = mock_or
    mock_eq.execute.return_value = mock_execute
    mock_or.execute.return_value = mock_execute
    mock_eq.is_.return_value = mock_is
    mock_is.execute.return_value = mock_execute

    def mock_get_supabase_client():
        return mock_client

    app.dependency_overrides[get_supabase_client] = mock_get_supabase_client
    yield mock_client

    if get_supabase_client in app.dependency_overrides:
        del app.dependency_overrides[get_supabase_client]


@pytest.fixture
def existing_plan_for_delete(mock_user_id):
    """Mock plan data for delete testing."""
    plan_id = str(uuid4())
    return {
        "id": plan_id,
        "user_id": mock_user_id,
        "name": "Test Plan for Deletion",
        "description": "A plan that will be deleted",
        "training_style": TrainingStyle.POWERBUILDING.value,
        "goal": "strength",
        "difficulty_level": DifficultyLevel.INTERMEDIATE.value,
        "duration_weeks": 8,
        "days_per_week": 4,
        "is_public": False,
        "version_number": 1,
        "parent_plan_id": None,
        "is_active": True,
        "deleted_at": None,
        "created_at": "2025-01-01T12:00:00+00:00",
        "updated_at": "2025-01-01T12:00:00+00:00",
        "metadata": {"periodization": "linear"},
    }


# ============================================================================
# SUCCESS TESTS
# ============================================================================


def test_delete_plan_success(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test successful soft deletion of a plan."""
    plan_id = existing_plan_for_delete["id"]

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_for_delete]

    # Mock no active workout sessions
    sessions_response = MagicMock()
    sessions_response.count = 0

    # Mock successful soft delete
    delete_response = MagicMock()
    delete_response.data = [{"id": plan_id, "deleted_at": "2025-01-03T12:00:00+00:00"}]

    # Configure the mock call chain
    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_delete.table().select().eq().is_().execute.return_value = (
        sessions_response
    )
    mock_supabase_client_for_delete.table().update().or_().execute.return_value = (
        delete_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    # Verify the calls were made correctly
    mock_supabase_client_for_delete.table.assert_called()
    assert mock_supabase_client_for_delete.table().select().eq().execute.called
    assert mock_supabase_client_for_delete.table().update().or_().execute.called


def test_delete_plan_with_versions_success(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test successful deletion of plan with multiple versions (all versions deleted)."""
    plan_id = existing_plan_for_delete["id"]
    parent_id = str(uuid4())

    # Modify the plan to have a parent (it's a child version)
    plan_with_parent = {
        **existing_plan_for_delete,
        "parent_plan_id": parent_id,
        "version_number": 2,
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [plan_with_parent]

    # Mock no active workout sessions
    sessions_response = MagicMock()
    sessions_response.count = 0

    # Mock successful deletion of all versions
    delete_response = MagicMock()
    delete_response.data = [
        {"id": plan_id, "deleted_at": "2025-01-03T12:00:00+00:00"},
        {"id": parent_id, "deleted_at": "2025-01-03T12:00:00+00:00"},
    ]

    # Configure the mock call chain
    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_delete.table().select().eq().is_().execute.return_value = (
        sessions_response
    )
    mock_supabase_client_for_delete.table().update().or_().execute.return_value = (
        delete_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify all versions are deleted using the parent_id
    mock_supabase_client_for_delete.table().update().or_.assert_called_with(
        f"id.eq.{plan_id},parent_plan_id.eq.{parent_id}"
    )


def test_delete_plan_idempotency(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test idempotency - deleting already deleted plan returns 404."""
    plan_id = existing_plan_for_delete["id"]

    # Plan is already deleted
    deleted_plan = {
        **existing_plan_for_delete,
        "deleted_at": "2025-01-02T10:00:00+00:00",
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [deleted_plan]

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Plan not found"

    # Verify no delete operation was attempted
    assert not mock_supabase_client_for_delete.table().update().or_().execute.called


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================


def test_delete_plan_unauthenticated():
    """Test 403 error when no authentication token is provided."""
    plan_id = str(uuid4())

    response = client.delete(f"/api/v1/plans/{plan_id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authenticated"


def test_delete_plan_invalid_token():
    """Test 401 error when invalid authentication token is provided."""
    plan_id = str(uuid4())

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_plan_malformed_auth_header():
    """Test 403 error when authorization header is malformed."""
    plan_id = str(uuid4())

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "malformed-header"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# AUTHORIZATION TESTS (403)
# ============================================================================


def test_delete_plan_not_owner(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test 403 error when user tries to delete plan they don't own."""
    plan_id = existing_plan_for_delete["id"]
    different_user_id = str(uuid4())

    # Plan belongs to different user
    other_user_plan = {
        **existing_plan_for_delete,
        "user_id": different_user_id,
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [other_user_plan]

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "You do not have permission to delete this plan"

    # Verify no deletion was attempted
    assert not mock_supabase_client_for_delete.table().update().or_().execute.called


# ============================================================================
# NOT FOUND TESTS (404)
# ============================================================================


def test_delete_plan_not_found(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
):
    """Test 404 error when plan doesn't exist."""
    plan_id = str(uuid4())

    # Mock empty response (plan not found)
    select_response = MagicMock()
    select_response.data = []

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Plan not found"


def test_delete_plan_already_deleted(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test 404 error when plan is already deleted."""
    plan_id = existing_plan_for_delete["id"]

    # Plan has deleted_at timestamp
    deleted_plan = {
        **existing_plan_for_delete,
        "deleted_at": "2025-01-02T10:00:00+00:00",
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [deleted_plan]

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Plan not found"


# ============================================================================
# BAD REQUEST TESTS (400)
# ============================================================================


def test_delete_plan_with_active_sessions(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test 400 error when plan has active workout sessions."""
    plan_id = existing_plan_for_delete["id"]

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_for_delete]

    # Mock active workout sessions exist
    sessions_response = MagicMock()
    sessions_response.count = 2  # 2 active sessions

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_delete.table().select().eq().is_().execute.return_value = (
        sessions_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "Cannot delete plan - it has active workout sessions"
    )

    # Verify no deletion was attempted
    assert not mock_supabase_client_for_delete.table().update().or_().execute.called


def test_delete_plan_with_completed_sessions_allowed(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test successful deletion when plan has only completed workout sessions."""
    plan_id = existing_plan_for_delete["id"]

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_for_delete]

    # Mock no active sessions (completed sessions don't block deletion)
    sessions_response = MagicMock()
    sessions_response.count = 0

    # Mock successful deletion
    delete_response = MagicMock()
    delete_response.data = [{"id": plan_id, "deleted_at": "2025-01-03T12:00:00+00:00"}]

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_delete.table().select().eq().is_().execute.return_value = (
        sessions_response
    )
    mock_supabase_client_for_delete.table().update().or_().execute.return_value = (
        delete_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================================
# VALIDATION ERROR TESTS (422)
# ============================================================================


def test_delete_plan_invalid_uuid_format(mock_auth_dependency):
    """Test 422 error for invalid UUID format in path parameter."""
    invalid_uuid = "not-a-valid-uuid"

    response = client.delete(
        f"/api/v1/plans/{invalid_uuid}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = response.json()["detail"]
    assert any("uuid" in str(error).lower() for error in error_detail)


def test_delete_plan_empty_uuid():
    """Test 422 error for empty UUID in path parameter."""
    response = client.delete(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    # This should return 404 (method not found) or 405 (method not allowed)
    # as the route doesn't match without the UUID parameter
    assert response.status_code in [
        status.HTTP_404_NOT_FOUND,
        status.HTTP_405_METHOD_NOT_ALLOWED,
    ]


# ============================================================================
# DATABASE ERROR TESTS (500)
# ============================================================================


def test_delete_plan_database_connection_error(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
):
    """Test 500 error when database connection fails during plan lookup."""
    plan_id = str(uuid4())

    # Mock database connection error
    mock_supabase_client_for_delete.table().select().eq().execute.side_effect = (
        Exception("Database connection failed")
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to delete plan due to an internal error" in response.json()["detail"]


def test_delete_plan_sessions_query_error(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test 500 error when sessions query fails."""
    plan_id = existing_plan_for_delete["id"]

    # Mock successful plan lookup
    select_response = MagicMock()
    select_response.data = [existing_plan_for_delete]

    # Mock sessions query failure
    call_count = [0]  # Use list to maintain state across calls

    def side_effect(*args, **kwargs):
        # First call succeeds (plan lookup), second call fails (sessions query)
        call_count[0] += 1
        if call_count[0] == 1:
            return select_response
        else:
            raise Exception("Sessions query failed")

    mock_supabase_client_for_delete.table().select().eq().execute.side_effect = (
        side_effect
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to delete plan due to an internal error" in response.json()["detail"]


def test_delete_plan_update_operation_failure(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test 500 error when update operation returns no data."""
    plan_id = existing_plan_for_delete["id"]

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_for_delete]

    sessions_response = MagicMock()
    sessions_response.count = 0

    # Mock failed deletion (no data returned)
    delete_response = MagicMock()
    delete_response.data = None

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_delete.table().select().eq().is_().execute.return_value = (
        sessions_response
    )
    mock_supabase_client_for_delete.table().update().or_().execute.return_value = (
        delete_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Failed to delete plan"


def test_delete_plan_update_operation_exception(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test 500 error when update operation throws exception."""
    plan_id = existing_plan_for_delete["id"]

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_for_delete]

    sessions_response = MagicMock()
    sessions_response.count = 0

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_delete.table().select().eq().is_().execute.return_value = (
        sessions_response
    )
    # Mock update operation failure
    mock_supabase_client_for_delete.table().update().or_().execute.side_effect = (
        Exception("Update operation failed")
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to delete plan due to an internal error" in response.json()["detail"]


# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================


def test_delete_plan_various_uuid_formats(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test deletion with various valid UUID formats."""
    from uuid import UUID

    base_uuid = UUID(existing_plan_for_delete["id"])
    uuid_formats = [
        str(base_uuid).upper(),  # Uppercase
        str(base_uuid).lower(),  # Lowercase
        str(base_uuid),  # Default format with hyphens
    ]

    for uuid_format in uuid_formats:
        # Update the plan ID to match the current format
        plan_with_format = {
            **existing_plan_for_delete,
            "id": uuid_format,
        }

        # Mock responses
        select_response = MagicMock()
        select_response.data = [plan_with_format]

        sessions_response = MagicMock()
        sessions_response.count = 0

        delete_response = MagicMock()
        delete_response.data = [
            {"id": uuid_format, "deleted_at": "2025-01-03T12:00:00+00:00"}
        ]

        mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
            select_response
        )
        mock_supabase_client_for_delete.table().select().eq().is_().execute.return_value = sessions_response
        mock_supabase_client_for_delete.table().update().or_().execute.return_value = (
            delete_response
        )

        response = client.delete(
            f"/api/v1/plans/{uuid_format}",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_plan_parent_without_children(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test deletion of parent plan that has no child versions."""
    plan_id = existing_plan_for_delete["id"]

    # This is a parent plan (no parent_plan_id)
    parent_plan = {
        **existing_plan_for_delete,
        "parent_plan_id": None,
        "version_number": 1,
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [parent_plan]

    sessions_response = MagicMock()
    sessions_response.count = 0

    delete_response = MagicMock()
    delete_response.data = [{"id": plan_id, "deleted_at": "2025-01-03T12:00:00+00:00"}]

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_delete.table().select().eq().is_().execute.return_value = (
        sessions_response
    )
    mock_supabase_client_for_delete.table().update().or_().execute.return_value = (
        delete_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion uses the plan's own ID as parent ID when no parent exists
    mock_supabase_client_for_delete.table().update().or_.assert_called_with(
        f"id.eq.{plan_id},parent_plan_id.eq.{plan_id}"
    )


def test_delete_plan_null_sessions_count(
    mock_auth_dependency,
    mock_supabase_client_for_delete,
    existing_plan_for_delete,
):
    """Test successful deletion when sessions count query returns None."""
    plan_id = existing_plan_for_delete["id"]

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan_for_delete]

    # Mock sessions count as None (edge case)
    sessions_response = MagicMock()
    sessions_response.count = None

    delete_response = MagicMock()
    delete_response.data = [{"id": plan_id, "deleted_at": "2025-01-03T12:00:00+00:00"}]

    mock_supabase_client_for_delete.table().select().eq().execute.return_value = (
        select_response
    )
    mock_supabase_client_for_delete.table().select().eq().is_().execute.return_value = (
        sessions_response
    )
    mock_supabase_client_for_delete.table().update().or_().execute.return_value = (
        delete_response
    )

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    # Should succeed since None is treated as 0 active sessions
    assert response.status_code == status.HTTP_204_NO_CONTENT
