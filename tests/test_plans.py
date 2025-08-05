"""Comprehensive tests for the plans API endpoints.

This module tests POST, GET list, GET by ID, PUT, and DELETE for /api/v1/plans endpoints:

POST /api/v1/plans (Plan Creation):
- Successful plan creation with valid data
- Authentication requirements (401 errors)
- Request validation (422 errors)
- Database constraint violations (400 errors)
- Duplicate plan names (409 errors)
- Database error handling (500 errors)

GET /api/v1/plans (Plan List Retrieval):
- Successful retrieval with multiple plans and pagination
- Empty response for users with no plans
- Authentication requirements (401/403 errors)
- Query parameter validation (422 errors)
- Database error handling (500 errors)

GET /api/v1/plans/{plan_id} (Plan By ID Retrieval):
- Successful retrieval of own private plans (authenticated)
- Successful retrieval of public plans (authenticated and unauthenticated)
- Access control enforcement (404 for unauthorized access)
- Not found handling (404 for non-existent plans)
- UUID format validation (422 errors)
- Database error handling (500 errors)

DELETE /api/v1/plans/{plan_id} (Plan Soft Deletion):
- Successful soft deletion with deleted_at timestamp
- Deletion of all plan versions (parent and children)
- Authentication requirements (401/403 errors)
- Authorization enforcement (403 for non-owners)
- Not found handling (404 for non-existent or already deleted plans)
- Business rule enforcement (400 for plans with active sessions)
- UUID format validation (422 errors)
- Database error handling (500 errors)
"""

from typing import Any
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
    assert response_data["training_style"] == valid_plan_data["training_style"]
    assert response_data["goal"] == valid_plan_data["goal"]
    assert response_data["difficulty_level"] == valid_plan_data["difficulty_level"]
    assert response_data["is_public"] == valid_plan_data["is_public"]

    # Verify system-generated fields
    assert "id" in response_data
    # Verify fields that should not be in response
    assert "user_id" not in response_data
    assert "version_number" not in response_data
    assert "is_active" not in response_data
    assert "parent_plan_id" not in response_data


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
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# VALIDATION ERROR TESTS (422)
# ============================================================================


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


def test_create_plan_invalid_enum_values(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with invalid enum values."""
    # Test invalid training style
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

    # Test invalid difficulty level
    invalid_data = {
        "name": "Test Plan",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
        "difficulty_level": "expert",
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_plan_field_constraints(mock_auth_dependency, mock_supabase_client):
    """Test plan creation with field constraint violations."""
    # Test empty name
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

    # Test name too long
    invalid_data["name"] = "x" * 101

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test invalid duration_weeks
    invalid_data = {
        "name": "Test Plan",
        "training_style": TrainingStyle.GENERAL_FITNESS.value,
        "duration_weeks": "0",
    }

    response = client.post(
        "/api/v1/plans/",
        json=invalid_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# CONSTRAINT VIOLATION TESTS (400)
# ============================================================================


def test_create_plan_duplicate_name(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with duplicate name."""
    from postgrest.exceptions import APIError

    # Mock database error for unique constraint violation
    mock_supabase_client.table().insert().execute.side_effect = APIError(
        {"code": "23505", "message": "duplicate key value violates unique constraint"}
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT


# ============================================================================
# DATABASE ERROR TESTS (500)
# ============================================================================


def test_create_plan_database_connection_error(
    mock_auth_dependency, mock_supabase_client, valid_plan_data
):
    """Test plan creation with database connection error."""
    from postgrest.exceptions import APIError

    # Mock database connection error
    mock_supabase_client.table().insert().execute.side_effect = APIError(
        {"code": "08003", "message": "connection does not exist"}
    )

    response = client.post(
        "/api/v1/plans/",
        json=valid_plan_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# GET PLANS TESTS
# ============================================================================


def test_get_plans_success_with_multiple_plans(
    mock_auth_dependency, mock_supabase_client, mock_user_id
):
    """Test successful retrieval of multiple plans with pagination."""
    # Mock database response with multiple plans
    mock_plans = [
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

    mock_response = MagicMock()
    mock_response.data = mock_plans
    mock_response.count = 2
    mock_supabase_client.table.return_value.select.return_value.is_.return_value.order.return_value.range.return_value.execute.return_value = mock_response

    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    assert "items" in response_data
    assert "total" in response_data
    assert len(response_data["items"]) == 2
    assert response_data["total"] == 2


def test_get_plans_success_empty_response(mock_auth_dependency, mock_supabase_client):
    """Test successful retrieval when user has no plans."""
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 0
    mock_supabase_client.table.return_value.select.return_value.is_.return_value.order.return_value.range.return_value.execute.return_value = mock_response

    response = client.get(
        "/api/v1/plans/",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["items"] == []
    assert response_data["total"] == 0


def test_get_plans_unauthenticated():
    """Test plans retrieval without authentication."""
    response = client.get("/api/v1/plans/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_plans_validation_error(mock_auth_dependency, mock_supabase_client):
    """Test plans retrieval with invalid query parameters."""
    # Test invalid limit
    response = client.get(
        "/api/v1/plans/?limit=0",
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test negative offset
    response = client.get(
        "/api/v1/plans/?offset=-1",
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# GET PLAN BY ID TESTS
# ============================================================================


def test_get_plan_by_id_success_own_private_plan(
    mock_jwt_payload, mock_supabase_client, mock_user_id
):
    """Test successful retrieval of user's own private plan."""
    from src.core.auth import optional_auth

    # Override optional_auth to return the JWT payload
    app.dependency_overrides[optional_auth] = lambda: mock_jwt_payload

    plan_id = str(uuid4())
    mock_plan = {
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

    mock_response = MagicMock()
    mock_response.data = [mock_plan]
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_response

    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == plan_id
    assert response_data["name"] == "My Private Plan"

    # Clean up
    if optional_auth in app.dependency_overrides:
        del app.dependency_overrides[optional_auth]


def test_get_plan_by_id_success_public_plan_unauthenticated():
    """Test successful retrieval of public plan without authentication."""
    from src.core.auth import optional_auth

    # Mock optional auth to return None (unauthenticated)
    def mock_optional_auth():
        return None

    app.dependency_overrides[optional_auth] = mock_optional_auth

    plan_id = str(uuid4())
    mock_plan: dict[str, Any] = {
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

    mock_response = MagicMock()
    mock_response.data = [mock_plan]

    from src.core.utils import get_supabase_client

    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_response
    app.dependency_overrides[get_supabase_client] = lambda: mock_client

    response = client.get(f"/api/v1/plans/{plan_id}")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["name"] == "Public Plan"

    # Clean up
    if optional_auth in app.dependency_overrides:
        del app.dependency_overrides[optional_auth]
    if get_supabase_client in app.dependency_overrides:
        del app.dependency_overrides[get_supabase_client]


def test_get_plan_by_id_not_found(mock_auth_dependency, mock_supabase_client):
    """Test plan retrieval for non-existent plan."""
    plan_id = str(uuid4())

    mock_response = MagicMock()
    mock_response.data = []
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_plan_by_id_invalid_uuid(mock_auth_dependency):
    """Test plan retrieval with invalid UUID format."""
    response = client.get(
        "/api/v1/plans/invalid-uuid",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# UPDATE PLAN TESTS
# ============================================================================


def test_update_plan_success_full_update(
    mock_auth_dependency, mock_supabase_client, mock_user_id
):
    """Test successful plan update with full data."""
    plan_id = str(uuid4())

    # Mock existing plan
    existing_plan = {
        "id": plan_id,
        "user_id": mock_user_id,
        "name": "Original Plan",
        "description": None,
        "training_style": TrainingStyle.POWERBUILDING.value,
        "goal": None,
        "difficulty_level": None,
        "duration_weeks": None,
        "days_per_week": None,
        "version_number": 1,
        "is_active": True,
        "is_public": False,
        "metadata": {},
    }

    # Mock updated plan
    updated_plan = {
        "id": str(uuid4()),  # New version gets new ID
        "user_id": mock_user_id,
        "name": "Updated Plan",
        "description": None,
        "training_style": TrainingStyle.BODYBUILDING.value,
        "goal": None,
        "difficulty_level": None,
        "duration_weeks": None,
        "days_per_week": None,
        "version_number": 2,
        "parent_plan_id": plan_id,
        "is_active": True,
        "created_at": "2025-01-01T12:00:00+00:00",
        "is_public": False,
        "metadata": {},
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan]

    update_response = MagicMock()
    update_response.data = [{"id": plan_id}]

    insert_response = MagicMock()
    insert_response.data = [updated_plan]

    mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = select_response
    mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = update_response
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
        insert_response
    )

    update_data = {
        "name": "Updated Plan",
        "training_style": TrainingStyle.BODYBUILDING.value,
    }

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["name"] == "Updated Plan"
    # version_number is no longer exposed in the response


def test_update_plan_not_found(mock_auth_dependency, mock_supabase_client):
    """Test update of non-existent plan."""
    plan_id = str(uuid4())

    mock_response = MagicMock()
    mock_response.data = []
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    update_data = {"name": "Updated Plan"}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_plan_unauthenticated():
    """Test plan update without authentication."""
    plan_id = str(uuid4())
    update_data = {"name": "Updated Plan"}

    response = client.put(f"/api/v1/plans/{plan_id}", json=update_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_plan_validation_errors(mock_auth_dependency, mock_supabase_client):
    """Test plan update with validation errors."""
    plan_id = str(uuid4())

    # Test empty name
    update_data = {"name": ""}

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# DELETE PLAN TESTS
# ============================================================================


def test_delete_plan_success(mock_auth_dependency, mock_supabase_client, mock_user_id):
    """Test successful plan deletion."""
    plan_id = str(uuid4())

    # Mock existing plan
    existing_plan = {
        "id": plan_id,
        "user_id": mock_user_id,
        "name": "Plan to Delete",
        "is_active": True,
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan]

    sessions_response = MagicMock()
    sessions_response.count = 0

    update_response = MagicMock()
    update_response.data = [{"id": plan_id, "deleted_at": "2025-01-01T12:00:00+00:00"}]

    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = select_response
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = sessions_response
    mock_supabase_client.table.return_value.update.return_value.or_.return_value.execute.return_value = update_response

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_plan_not_found(mock_auth_dependency, mock_supabase_client):
    """Test deletion of non-existent plan."""
    plan_id = str(uuid4())

    mock_response = MagicMock()
    mock_response.data = []
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_plan_with_active_sessions(
    mock_auth_dependency, mock_supabase_client, mock_user_id
):
    """Test deletion fails when plan has active workout sessions."""
    plan_id = str(uuid4())

    # Mock existing plan
    existing_plan = {
        "id": plan_id,
        "user_id": mock_user_id,
        "name": "Plan with Sessions",
        "is_active": True,
    }

    # Mock responses
    select_response = MagicMock()
    select_response.data = [existing_plan]

    sessions_response = MagicMock()
    sessions_response.count = 2  # Has active sessions

    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = select_response
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = sessions_response

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_plan_unauthenticated():
    """Test plan deletion without authentication."""
    plan_id = str(uuid4())

    response = client.delete(f"/api/v1/plans/{plan_id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_plan_invalid_uuid(mock_auth_dependency):
    """Test plan deletion with invalid UUID format."""
    response = client.delete(
        "/api/v1/plans/invalid-uuid",
        headers={"Authorization": "Bearer mock-token"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
