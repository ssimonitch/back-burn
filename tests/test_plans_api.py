"""Comprehensive tests for the plans API endpoints.

This module consolidates all tests for POST, GET list, GET by ID, PUT, and DELETE
for /api/v1/plans endpoints with optimized structure and parameterization.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from postgrest.exceptions import APIError

from main import app
from src.models.enums import TrainingStyle

# Test client setup
client = TestClient(app)


class TestPlanCreation:
    """Tests for POST /api/v1/plans/ endpoint."""

    def test_create_plan_success_full_data(
        self,
        mock_auth_dependency,
        mock_supabase_client,
        valid_plan_data,
        created_plan_response,
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
        self,
        mock_auth_dependency,
        mock_supabase_client,
        minimal_plan_data,
        mock_user_id,
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

    @pytest.mark.parametrize(
        "auth_header,expected_status",
        [
            (None, status.HTTP_403_FORBIDDEN),
            ({"Authorization": "Bearer invalid-token"}, status.HTTP_401_UNAUTHORIZED),
        ],
    )
    def test_create_plan_authentication_errors(
        self, valid_plan_data, auth_header, expected_status
    ):
        """Test plan creation authentication requirements."""
        headers = auth_header if auth_header is not None else {}
        response = client.post("/api/v1/plans/", json=valid_plan_data, headers=headers)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "invalid_data,expected_field",
        [
            # Missing required fields
            ({"name": "Test Plan"}, "training_style"),
            # Invalid enum values
            (
                {"name": "Test Plan", "training_style": "invalid_style"},
                "training_style",
            ),
            (
                {
                    "name": "Test Plan",
                    "training_style": TrainingStyle.GENERAL_FITNESS.value,
                    "difficulty_level": "expert",
                },
                "difficulty_level",
            ),
            # Field constraints
            (
                {"name": "", "training_style": TrainingStyle.GENERAL_FITNESS.value},
                "name",
            ),
            (
                {
                    "name": "x" * 101,
                    "training_style": TrainingStyle.GENERAL_FITNESS.value,
                },
                "name",
            ),
            (
                {
                    "name": "Test Plan",
                    "training_style": TrainingStyle.GENERAL_FITNESS.value,
                    "duration_weeks": 0,
                },
                "duration_weeks",
            ),
        ],
    )
    def test_create_plan_validation_errors(
        self, mock_auth_dependency, mock_supabase_client, invalid_data, expected_field
    ):
        """Test plan creation validation errors."""
        response = client.post(
            "/api/v1/plans/",
            json=invalid_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_detail = response.json()["detail"]
        assert any(expected_field in str(error).lower() for error in error_detail)

    @pytest.mark.parametrize(
        "error_config,expected_status,expected_message",
        [
            # Duplicate name
            (
                {
                    "side_effect": APIError(
                        {
                            "code": "23505",
                            "message": "duplicate key value violates unique constraint",
                        }
                    )
                },
                status.HTTP_409_CONFLICT,
                None,
            ),
            # Database errors
            (
                {
                    "side_effect": APIError(
                        {"code": "08003", "message": "connection does not exist"}
                    )
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                None,
            ),
            # Check constraints
            (
                {
                    "side_effect": Exception(
                        "new row for relation violates check constraint difficulty_level_check"
                    )
                },
                status.HTTP_400_BAD_REQUEST,
                "Invalid difficulty level",
            ),
            (
                {
                    "side_effect": Exception(
                        "new row for relation violates check constraint duration_weeks_check"
                    )
                },
                status.HTTP_400_BAD_REQUEST,
                "Duration weeks must be greater than 0",
            ),
            (
                {
                    "side_effect": Exception(
                        "new row for relation violates check constraint days_per_week_check"
                    )
                },
                status.HTTP_400_BAD_REQUEST,
                "Days per week must be between 1 and 7",
            ),
            # Foreign key violation
            (
                {"side_effect": Exception("foreign key violation")},
                status.HTTP_400_BAD_REQUEST,
                "Invalid reference",
            ),
            # Generic exception
            (
                {"side_effect": Exception("Unexpected database error")},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "internal error",
            ),
        ],
    )
    def test_create_plan_database_errors(
        self,
        mock_auth_dependency,
        mock_supabase_client,
        valid_plan_data,
        error_config,
        expected_status,
        expected_message,
    ):
        """Test plan creation database error handling."""
        mock_supabase_client.table().insert().execute.configure_mock(**error_config)

        response = client.post(
            "/api/v1/plans/",
            json=valid_plan_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == expected_status
        if expected_message:
            assert expected_message in response.json()["detail"]

    def test_create_plan_no_data_returned(
        self, mock_auth_dependency, mock_supabase_client, valid_plan_data
    ):
        """Test plan creation when database returns no data."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase_client.table().insert().execute.return_value = mock_response

        response = client.post(
            "/api/v1/plans/",
            json=valid_plan_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "no data returned" in response.json()["detail"]

    def test_create_plan_value_error(
        self, mock_auth_dependency, mock_supabase_client, valid_plan_data
    ):
        """Test plan creation with value error during processing."""
        mock_response = MagicMock()
        mock_response.data = [{"invalid": "data"}]  # Missing required fields
        mock_supabase_client.table().insert().execute.return_value = mock_response

        response = client.post(
            "/api/v1/plans/",
            json=valid_plan_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPlanRetrieval:
    """Tests for GET /api/v1/plans/ and GET /api/v1/plans/{plan_id} endpoints."""

    def test_get_plans_success_with_multiple_plans(
        self, mock_auth_dependency, mock_supabase_client, mock_plans_list
    ):
        """Test successful retrieval of multiple plans with pagination."""
        mock_response = MagicMock()
        mock_response.data = mock_plans_list
        mock_response.count = len(mock_plans_list)
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

    def test_get_plans_success_empty_response(
        self, mock_auth_dependency, mock_supabase_client
    ):
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

    def test_get_plans_unauthenticated(self):
        """Test plans retrieval without authentication."""
        response = client.get("/api/v1/plans/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "query_params,expected_status",
        [
            ("?limit=0", status.HTTP_422_UNPROCESSABLE_ENTITY),
            ("?offset=-1", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ],
    )
    def test_get_plans_validation_errors(
        self, mock_auth_dependency, mock_supabase_client, query_params, expected_status
    ):
        """Test plans retrieval with invalid query parameters."""
        response = client.get(
            f"/api/v1/plans/{query_params}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == expected_status

    def test_get_plan_by_id_success_own_private_plan(
        self, mock_jwt_payload, mock_supabase_client, mock_private_plan
    ):
        """Test successful retrieval of user's own private plan."""
        from src.core.auth import optional_auth

        app.dependency_overrides[optional_auth] = lambda: mock_jwt_payload

        plan_id = mock_private_plan["id"]
        mock_response = MagicMock()
        mock_response.data = [mock_private_plan]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_response

        response = client.get(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == plan_id
        assert response_data["name"] == mock_private_plan["name"]

        # Clean up
        if optional_auth in app.dependency_overrides:
            del app.dependency_overrides[optional_auth]

    def test_get_plan_by_id_success_public_plan_unauthenticated(self, mock_public_plan):
        """Test successful retrieval of public plan without authentication."""
        from src.core.auth import optional_auth
        from src.core.utils import get_supabase_client

        # Mock optional auth to return None (unauthenticated)
        app.dependency_overrides[optional_auth] = lambda: None

        # Setup mock client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [mock_public_plan]
        mock_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_response
        app.dependency_overrides[get_supabase_client] = lambda: mock_client

        plan_id = mock_public_plan["id"]
        response = client.get(f"/api/v1/plans/{plan_id}")

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["name"] == "Public Plan"

        # Clean up
        if optional_auth in app.dependency_overrides:
            del app.dependency_overrides[optional_auth]
        if get_supabase_client in app.dependency_overrides:
            del app.dependency_overrides[get_supabase_client]

    @pytest.mark.parametrize(
        "scenario,setup_func,expected_status",
        [
            (
                "non_existent_plan",
                lambda mock_client: mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.configure_mock(
                    data=[]
                ),
                status.HTTP_404_NOT_FOUND,
            ),
            ("unauthenticated_private_plan", None, status.HTTP_404_NOT_FOUND),
            ("private_plan_wrong_owner", None, status.HTTP_404_NOT_FOUND),
        ],
    )
    def test_get_plan_by_id_access_denied_scenarios(
        self,
        mock_auth_dependency,
        mock_supabase_client,
        scenario,
        setup_func,
        expected_status,
    ):
        """Test various access denied scenarios for plan retrieval."""
        plan_id = str(uuid4())

        if scenario == "non_existent_plan":
            setup_func(mock_supabase_client)
        elif scenario == "unauthenticated_private_plan":
            from src.core.auth import optional_auth

            app.dependency_overrides[optional_auth] = lambda: None
            mock_plan = {"id": plan_id, "user_id": str(uuid4()), "is_public": False}
            mock_response = MagicMock()
            mock_response.data = [mock_plan]
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_response
        elif scenario == "private_plan_wrong_owner":
            other_user_id = str(uuid4())
            mock_plan = {"id": plan_id, "user_id": other_user_id, "is_public": False}
            mock_response = MagicMock()
            mock_response.data = [mock_plan]
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_response

        response = client.get(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == expected_status

        # Clean up optional_auth if used
        from src.core.auth import optional_auth

        if optional_auth in app.dependency_overrides:
            del app.dependency_overrides[optional_auth]

    def test_get_plan_by_id_invalid_uuid(self, mock_auth_dependency):
        """Test plan retrieval with invalid UUID format."""
        response = client.get(
            "/api/v1/plans/invalid-uuid",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPlanUpdate:
    """Tests for PUT /api/v1/plans/{plan_id} endpoint."""

    def test_update_plan_success_full_update(
        self, mock_auth_dependency, mock_supabase_client, mock_user_id
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
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = insert_response

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

    def test_update_plan_not_found(self, mock_auth_dependency, mock_supabase_client):
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

    def test_update_plan_unauthenticated(self):
        """Test plan update without authentication."""
        plan_id = str(uuid4())
        update_data = {"name": "Updated Plan"}

        response = client.put(f"/api/v1/plans/{plan_id}", json=update_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_plan_validation_errors(
        self, mock_auth_dependency, mock_supabase_client
    ):
        """Test plan update with validation errors."""
        plan_id = str(uuid4())
        update_data = {"name": ""}

        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json=update_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        "error_scenario,mock_setup,expected_status,expected_message",
        [
            (
                "update_fails",
                lambda mock_client, existing_plan: (
                    mock_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.__setattr__(
                        "data", [existing_plan]
                    ),
                    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.__setattr__(
                        "data", []
                    ),
                ),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Failed to update current plan version",
            ),
            (
                "insert_fails",
                lambda mock_client, existing_plan: (
                    mock_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.__setattr__(
                        "data", [existing_plan]
                    ),
                    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.__setattr__(
                        "data", [{"id": existing_plan["id"]}]
                    ),
                    mock_client.table.return_value.insert.return_value.execute.return_value.__setattr__(
                        "data", []
                    ),
                ),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Failed to create new plan version",
            ),
            (
                "version_conflict",
                lambda mock_client, existing_plan: (
                    mock_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.__setattr__(
                        "data", [existing_plan]
                    ),
                    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.__setattr__(
                        "data", [{"id": existing_plan["id"]}]
                    ),
                    mock_client.table.return_value.insert.return_value.execute.__setattr__(
                        "side_effect",
                        APIError({"code": "23505", "message": "duplicate key"}),
                    ),
                ),
                status.HTTP_409_CONFLICT,
                "newer version",
            ),
        ],
    )
    def test_update_plan_error_scenarios(
        self,
        mock_auth_dependency,
        mock_supabase_client,
        mock_user_id,
        error_scenario,
        mock_setup,
        expected_status,
        expected_message,
    ):
        """Test various error scenarios during plan update."""
        plan_id = str(uuid4())
        existing_plan = {
            "id": plan_id,
            "user_id": mock_user_id,
            "name": "Original Plan",
            "training_style": TrainingStyle.POWERBUILDING.value,
            "version_number": 1,
            "is_active": True,
        }

        mock_setup(mock_supabase_client, existing_plan)

        update_data = {"name": "Updated Plan"}
        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json=update_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == expected_status
        assert expected_message in response.json()["detail"]


class TestPlanDeletion:
    """Tests for DELETE /api/v1/plans/{plan_id} endpoint."""

    def test_delete_plan_success(
        self, mock_auth_dependency, mock_supabase_client, mock_user_id
    ):
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
        update_response.data = [
            {"id": plan_id, "deleted_at": "2025-01-01T12:00:00+00:00"}
        ]

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = select_response
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = sessions_response
        mock_supabase_client.table.return_value.update.return_value.or_.return_value.execute.return_value = update_response

        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.parametrize(
        "scenario,plan_data,expected_status,expected_message",
        [
            # Plan not found
            ("not_found", None, status.HTTP_404_NOT_FOUND, None),
            # Plan already deleted
            (
                "already_deleted",
                {
                    "id": "plan-id",
                    "user_id": "user-id",
                    "deleted_at": "2025-01-01T12:00:00+00:00",
                },
                status.HTTP_404_NOT_FOUND,
                None,
            ),
            # Wrong owner
            (
                "wrong_owner",
                {"id": "plan-id", "user_id": "other-user-id", "deleted_at": None},
                status.HTTP_403_FORBIDDEN,
                "permission",
            ),
            # Has active sessions
            (
                "has_sessions",
                {"id": "plan-id", "user_id": "user-id", "deleted_at": None},
                status.HTTP_400_BAD_REQUEST,
                None,
            ),
        ],
    )
    def test_delete_plan_error_scenarios(
        self,
        mock_auth_dependency,
        mock_supabase_client,
        mock_user_id,
        scenario,
        plan_data,
        expected_status,
        expected_message,
    ):
        """Test various error scenarios during plan deletion."""
        plan_id = str(uuid4())

        if scenario == "not_found":
            mock_response = MagicMock()
            mock_response.data = []
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        else:
            # Update plan_data with actual IDs
            if plan_data:
                plan_data["id"] = plan_id
                if plan_data["user_id"] == "user-id":
                    plan_data["user_id"] = mock_user_id
                elif plan_data["user_id"] == "other-user-id":
                    plan_data["user_id"] = str(uuid4())  # Different user

            mock_response = MagicMock()
            mock_response.data = [plan_data] if plan_data else []
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

            if scenario == "has_sessions":
                sessions_response = MagicMock()
                sessions_response.count = 2  # Has active sessions
                mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = sessions_response

        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == expected_status
        if expected_message:
            assert expected_message in response.json()["detail"]

    def test_delete_plan_unauthenticated(self):
        """Test plan deletion without authentication."""
        plan_id = str(uuid4())
        response = client.delete(f"/api/v1/plans/{plan_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_plan_invalid_uuid(self, mock_auth_dependency):
        """Test plan deletion with invalid UUID format."""
        response = client.delete(
            "/api/v1/plans/invalid-uuid",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_plan_update_fails(
        self, mock_auth_dependency, mock_supabase_client, mock_user_id
    ):
        """Test delete plan when update operation fails."""
        plan_id = str(uuid4())

        existing_plan = {
            "id": plan_id,
            "user_id": mock_user_id,
            "deleted_at": None,
        }

        # Mock responses
        select_response = MagicMock()
        select_response.data = [existing_plan]

        sessions_response = MagicMock()
        sessions_response.count = 0

        delete_response = MagicMock()
        delete_response.data = []  # No data returned on delete

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = select_response
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = sessions_response
        mock_supabase_client.table.return_value.update.return_value.or_.return_value.execute.return_value = delete_response

        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to delete plan" in response.json()["detail"]


class TestPlanAPIEdgeCases:
    """Additional edge case tests for comprehensive coverage."""

    def test_get_plans_value_error_in_model(
        self, mock_auth_dependency, mock_supabase_client
    ):
        """Test get plans with invalid data causing ValueError in model creation."""
        # Mock response with invalid data that will cause ValueError
        mock_response = MagicMock()
        mock_response.data = [{"invalid": "data"}]  # Missing required fields
        mock_response.count = 1
        mock_supabase_client.table.return_value.select.return_value.is_.return_value.order.return_value.range.return_value.execute.return_value = mock_response

        response = client.get(
            "/api/v1/plans/",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_plan_by_id_value_error(self, mock_jwt_payload, mock_supabase_client):
        """Test get plan by ID with ValueError in model creation."""
        from src.core.auth import optional_auth

        app.dependency_overrides[optional_auth] = lambda: mock_jwt_payload

        plan_id = str(uuid4())

        # Mock response with data that passes auth checks but fails model validation
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": plan_id,
                "user_id": mock_jwt_payload.user_id,
                "is_public": False,
                # Missing required fields like name, training_style, etc.
            }
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_response

        response = client.get(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Clean up
        if optional_auth in app.dependency_overrides:
            del app.dependency_overrides[optional_auth]

    @pytest.mark.parametrize(
        "endpoint_config",
        [
            ("GET", "/api/v1/plans/", "get_plans_generic_exception"),
            (
                "GET",
                f"/api/v1/plans/{uuid4()}",
                "get_plan_by_id_generic_exception",
            ),  # Use valid UUID
            (
                "DELETE",
                f"/api/v1/plans/{uuid4()}",
                "delete_plan_generic_exception",
            ),  # Use valid UUID
        ],
    )
    def test_generic_exceptions(
        self, mock_auth_dependency, mock_supabase_client, endpoint_config
    ):
        """Test generic exception handling across endpoints."""
        method, endpoint, test_name = endpoint_config

        # Configure generic exception
        if "get_plans" in test_name:
            mock_supabase_client.table.return_value.select.return_value.is_.return_value.order.return_value.range.return_value.execute.side_effect = Exception(
                "Unexpected error"
            )
        elif "get_plan_by_id" in test_name:
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.side_effect = Exception(
                "Unexpected error"
            )
        elif "delete_plan" in test_name:
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception(
                "Unexpected error"
            )

        if method == "GET":
            response = client.get(
                endpoint, headers={"Authorization": "Bearer mock-token"}
            )
        elif method == "DELETE":
            response = client.delete(
                endpoint, headers={"Authorization": "Bearer mock-token"}
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "internal error" in response.json()["detail"]
