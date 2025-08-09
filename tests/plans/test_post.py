from unittest.mock import MagicMock

import pytest
from fastapi import status

from main import app


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
        from fastapi.testclient import TestClient

        client = TestClient(app)
        # Use repository mock for clarity
        from tests.conftest import get_plans_repository  # type: ignore

        # Backward compatibility: allow existing supabase mock, but prefer repo
        # Override via fixture if provided

        # Simulate repository create success
        app.dependency_overrides[get_plans_repository] = lambda: MagicMock(
            create=lambda user_id, payload: created_plan_response
        )

        # Make the request
        from fastapi.testclient import TestClient

        client = TestClient(app)
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
        from uuid import uuid4

        from fastapi.testclient import TestClient

        client = TestClient(app)

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

        # Mock repository create
        from src.core.di import get_plans_repository

        app.dependency_overrides[get_plans_repository] = lambda: MagicMock(
            create=lambda user_id, payload: created_plan
        )

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
        from fastapi.testclient import TestClient

        client = TestClient(app)
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
                    "training_style": "general_fitness",
                    "difficulty_level": "expert",
                },
                "difficulty_level",
            ),
            # Field constraints
            (
                {"name": "", "training_style": "general_fitness"},
                "name",
            ),
            (
                {
                    "name": "x" * 101,
                    "training_style": "general_fitness",
                },
                "name",
            ),
            (
                {
                    "name": "Test Plan",
                    "training_style": "general_fitness",
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
        from fastapi.testclient import TestClient

        client = TestClient(app)
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
                    "side_effect": __import__(
                        "postgrest.exceptions"
                    ).exceptions.APIError(
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
                    "side_effect": __import__(
                        "postgrest.exceptions"
                    ).exceptions.APIError(
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
        mock_plans_repo,
        valid_plan_data,
        error_config,
        expected_status,
        expected_message,
    ):
        """Test plan creation database error handling."""
        from fastapi.testclient import TestClient

        client = TestClient(app)
        # Configure repo to raise
        if "side_effect" in error_config:
            mock_plans_repo.create.side_effect = error_config["side_effect"]

        response = client.post(
            "/api/v1/plans/",
            json=valid_plan_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == expected_status
        if expected_message:
            assert expected_message in response.json()["detail"]

    def test_create_plan_no_data_returned(
        self, mock_auth_dependency, mock_plans_repo, valid_plan_data
    ):
        """Test plan creation when database returns no data."""
        from fastapi.testclient import TestClient

        client = TestClient(app)
        mock_plans_repo.create.side_effect = RuntimeError(
            "Failed to create plan - no data returned"
        )

        response = client.post(
            "/api/v1/plans/",
            json=valid_plan_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "no data returned" in response.json()["detail"]

    def test_create_plan_value_error(
        self, mock_auth_dependency, mock_plans_repo, valid_plan_data
    ):
        """Test plan creation with value error during processing."""
        from fastapi.testclient import TestClient

        client = TestClient(app)
        # Return invalid shape to trigger model validation error
        mock_plans_repo.create.return_value = {"invalid": "data"}

        response = client.post(
            "/api/v1/plans/",
            json=valid_plan_data,
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
