from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestPlanDeletion:
    """Tests for DELETE /api/v1/plans/{plan_id}."""

    def test_delete_plan_success(
        self, mock_auth_dependency, mock_plans_repo, mock_user_id
    ):
        plan_id = str(uuid4())
        existing_plan = {
            "id": plan_id,
            "user_id": mock_user_id,
            "name": "Plan to Delete",
            "is_active": True,
        }
        mock_plans_repo.get_raw.return_value = existing_plan
        mock_plans_repo.count_active_sessions.return_value = 0
        mock_plans_repo.soft_delete_cascade.return_value = True

        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_plan_error_scenarios(
        self,
        mock_auth_dependency,
        mock_plans_repo,
        mock_user_id,
    ):
        plan_id = str(uuid4())

        # not_found
        mock_plans_repo.get_raw.return_value = None
        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # already_deleted
        plan_data = {
            "id": plan_id,
            "user_id": mock_user_id,
            "deleted_at": "2025-01-01T12:00:00+00:00",
        }
        mock_plans_repo.get_raw.return_value = plan_data
        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # wrong_owner
        plan_data = {"id": plan_id, "user_id": str(uuid4()), "deleted_at": None}
        mock_plans_repo.get_raw.return_value = plan_data
        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "permission" in response.json()["detail"].lower()

        # has_sessions
        plan_data = {"id": plan_id, "user_id": mock_user_id, "deleted_at": None}
        mock_plans_repo.get_raw.return_value = plan_data
        mock_plans_repo.count_active_sessions.return_value = 2
        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_plan_unauthenticated(self):
        plan_id = str(uuid4())
        response = client.delete(f"/api/v1/plans/{plan_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_plan_invalid_uuid(self, mock_auth_dependency):
        response = client.delete(
            "/api/v1/plans/invalid-uuid",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_plan_update_fails(
        self, mock_auth_dependency, mock_plans_repo, mock_user_id
    ):
        plan_id = str(uuid4())
        existing_plan = {
            "id": plan_id,
            "user_id": mock_user_id,
            "deleted_at": None,
        }
        mock_plans_repo.get_raw.return_value = existing_plan
        mock_plans_repo.count_active_sessions.return_value = 0
        mock_plans_repo.soft_delete_cascade.return_value = False

        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to delete plan" in response.json()["detail"]
