from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestPlanAPIEdgeCases:
    """Additional edge case tests for comprehensive coverage."""

    def test_get_plans_value_error_in_model(
        self, mock_auth_dependency, mock_plans_repo
    ):
        # Invalid data triggers ValueError in model creation
        mock_plans_repo.list.return_value = ([{"invalid": "data"}], 1)

        response = client.get(
            "/api/v1/plans/",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_plan_by_id_value_error(self, mock_jwt_payload, mock_plans_repo):
        from src.core.auth import optional_auth

        app.dependency_overrides[optional_auth] = lambda: mock_jwt_payload
        plan_id = str(uuid4())
        # Missing required fields to force model validation failure
        mock_plans_repo.get_raw.return_value = {
            "id": plan_id,
            "user_id": mock_jwt_payload.user_id,
            "is_public": False,
        }
        response = client.get(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        if optional_auth in app.dependency_overrides:
            del app.dependency_overrides[optional_auth]

    def test_generic_exceptions(self, mock_auth_dependency, mock_plans_repo):
        # get_plans
        mock_plans_repo.list.side_effect = Exception("Unexpected error")
        response = client.get(
            "/api/v1/plans/",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "internal error" in response.json()["detail"]
        mock_plans_repo.list.side_effect = None

        # get_plan_by_id
        mock_plans_repo.get_raw.side_effect = Exception("Unexpected error")
        response = client.get(
            f"/api/v1/plans/{uuid4()}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "internal error" in response.json()["detail"]
        mock_plans_repo.get_raw.side_effect = None

        # delete_plan
        mock_plans_repo.get_raw.side_effect = Exception("Unexpected error")
        response = client.delete(
            f"/api/v1/plans/{uuid4()}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "internal error" in response.json()["detail"]
        mock_plans_repo.get_raw.side_effect = None
