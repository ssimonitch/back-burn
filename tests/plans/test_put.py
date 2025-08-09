from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from main import app
from src.models.enums import TrainingStyle

client = TestClient(app)


class TestPlanUpdate:
    """Tests for PUT /api/v1/plans/{plan_id}."""

    def test_update_plan_success_full_update(
        self, mock_auth_dependency, mock_plans_repo, mock_user_id
    ):
        plan_id = str(uuid4())

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

        updated_plan = {
            "id": str(uuid4()),
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

        mock_plans_repo.get_raw.return_value = existing_plan
        mock_plans_repo.mark_inactive.return_value = True
        mock_plans_repo.insert_plan.return_value = updated_plan

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

    def test_update_plan_not_found(self, mock_auth_dependency, mock_plans_repo):
        plan_id = str(uuid4())
        mock_plans_repo.get_raw.return_value = None

        update_data = {"name": "Updated Plan"}
        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json=update_data,
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_plan_unauthenticated(self):
        plan_id = str(uuid4())
        update_data = {"name": "Updated Plan"}
        response = client.put(f"/api/v1/plans/{plan_id}", json=update_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_plan_validation_errors(self, mock_auth_dependency, mock_plans_repo):
        plan_id = str(uuid4())
        update_data = {"name": ""}
        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json=update_data,
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_plan_no_changes_provided(
        self, mock_auth_dependency, mock_plans_repo, mock_user_id
    ):
        plan_id = str(uuid4())

        existing_plan = {
            "id": plan_id,
            "user_id": mock_user_id,
            "name": "Original Plan",
            "is_active": True,
        }
        mock_plans_repo.get_raw.return_value = existing_plan
        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json={},
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No changes provided" in response.json()["detail"]

    def test_update_plan_inactive_version(
        self, mock_auth_dependency, mock_plans_repo, mock_user_id
    ):
        plan_id = str(uuid4())
        existing_plan = {
            "id": plan_id,
            "user_id": mock_user_id,
            "name": "Original Plan",
            "is_active": False,
        }
        mock_plans_repo.get_raw.return_value = existing_plan
        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json={"name": "Updated"},
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "inactive plan version" in response.json()["detail"].lower()

    def test_update_plan_wrong_owner(
        self, mock_auth_dependency, mock_plans_repo, mock_user_id
    ):
        plan_id = str(uuid4())
        existing_plan = {
            "id": plan_id,
            "user_id": str(uuid4()),
            "name": "Original Plan",
            "is_active": True,
        }
        mock_plans_repo.get_raw.return_value = existing_plan
        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json={"name": "Updated"},
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "permission" in response.json()["detail"].lower()

    def test_update_plan_error_scenarios(
        self,
        mock_auth_dependency,
        mock_plans_repo,
        mock_user_id,
    ):
        plan_id = str(uuid4())
        existing_plan = {
            "id": plan_id,
            "user_id": mock_user_id,
            "name": "Original Plan",
            "training_style": TrainingStyle.POWERBUILDING.value,
            "version_number": 1,
            "is_active": True,
        }

        # update_fails
        mock_plans_repo.get_raw.return_value = existing_plan
        mock_plans_repo.mark_inactive.return_value = False
        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json={"name": "Updated Plan"},
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to update current plan version" in response.json()["detail"]

        # insert_fails
        mock_plans_repo.get_raw.return_value = existing_plan
        mock_plans_repo.mark_inactive.return_value = True
        mock_plans_repo.insert_plan.return_value = None
        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json={"name": "Updated Plan"},
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create new plan version" in response.json()["detail"]

        # version_conflict
        mock_plans_repo.get_raw.return_value = existing_plan
        mock_plans_repo.mark_inactive.return_value = True
        mock_plans_repo.insert_plan.side_effect = __import__(
            "postgrest.exceptions"
        ).exceptions.APIError({"code": "23505", "message": "duplicate key"})
        response = client.put(
            f"/api/v1/plans/{plan_id}",
            json={"name": "Updated Plan"},
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "newer version" in response.json()["detail"]
