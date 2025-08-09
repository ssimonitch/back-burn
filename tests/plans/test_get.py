from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestPlanRetrieval:
    """Tests for GET /api/v1/plans/ and GET /api/v1/plans/{plan_id}."""

    def test_get_plans_success_with_multiple_plans(
        self, mock_auth_dependency, mock_plans_repo, mock_plans_list
    ):
        mock_plans_repo.list.return_value = (mock_plans_list, len(mock_plans_list))

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
        self, mock_auth_dependency, mock_plans_repo
    ):
        mock_plans_repo.list.return_value = ([], 0)

        response = client.get(
            "/api/v1/plans/",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["items"] == []
        assert response_data["total"] == 0

    def test_get_plans_unauthenticated(self):
        response = client.get("/api/v1/plans/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_plans_validation_errors(self, mock_auth_dependency, mock_plans_repo):
        for qp, expected in (
            ("?limit=0", status.HTTP_422_UNPROCESSABLE_ENTITY),
            ("?offset=-1", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ):
            response = client.get(
                f"/api/v1/plans/{qp}",
                headers={"Authorization": "Bearer mock-token"},
            )
            assert response.status_code == expected

    def test_get_plan_by_id_success_own_private_plan(
        self, mock_jwt_payload, mock_plans_repo, mock_private_plan
    ):
        from src.core.auth import optional_auth

        app.dependency_overrides[optional_auth] = lambda: mock_jwt_payload
        plan_id = mock_private_plan["id"]
        mock_plans_repo.get_raw.return_value = mock_private_plan

        response = client.get(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == plan_id
        assert response_data["name"] == mock_private_plan["name"]

        if optional_auth in app.dependency_overrides:
            del app.dependency_overrides[optional_auth]

    def test_get_plan_by_id_success_public_plan_unauthenticated(
        self, mock_public_plan, mock_plans_repo
    ):
        from src.core.auth import optional_auth

        app.dependency_overrides[optional_auth] = lambda: None
        mock_plans_repo.get_raw.return_value = mock_public_plan

        plan_id = mock_public_plan["id"]
        response = client.get(f"/api/v1/plans/{plan_id}")

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["name"] == "Public Plan"

        if optional_auth in app.dependency_overrides:
            del app.dependency_overrides[optional_auth]

    def test_get_plan_by_id_access_denied_scenarios(
        self, mock_auth_dependency, mock_plans_repo
    ):
        # non-existent
        plan_id = str(uuid4())
        mock_plans_repo.get_raw.return_value = None
        response = client.get(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # unauthenticated private plan
        from src.core.auth import optional_auth

        app.dependency_overrides[optional_auth] = lambda: None
        mock_plan = {"id": plan_id, "user_id": str(uuid4()), "is_public": False}
        mock_plans_repo.get_raw.return_value = mock_plan
        response = client.get(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        if optional_auth in app.dependency_overrides:
            del app.dependency_overrides[optional_auth]

        # private plan wrong owner
        other_user_id = str(uuid4())
        mock_plan = {"id": plan_id, "user_id": other_user_id, "is_public": False}
        mock_plans_repo.get_raw.return_value = mock_plan
        response = client.get(
            f"/api/v1/plans/{plan_id}",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_plan_by_id_invalid_uuid(self, mock_auth_dependency):
        response = client.get(
            "/api/v1/plans/invalid-uuid",
            headers={"Authorization": "Bearer mock-token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
