"""Tests for the workout API endpoints."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import status


class TestCreateWorkout:
    """Tests for POST /api/v1/workouts endpoint."""

    def test_create_workout_success(
        self, client, mock_auth_dependency, mock_jwt_payload, mock_workouts_repo
    ):
        """Test successful workout creation."""
        # Arrange
        workout_id = str(uuid4())
        exercise_id = str(uuid4())

        mock_workouts_repo.verify_plan_access.return_value = True
        mock_workouts_repo.create_with_sets.return_value = {
            "id": workout_id,
            "user_id": mock_jwt_payload.user_id,
            "plan_id": None,
            "started_at": datetime.now(UTC).isoformat(),
            "completed_at": datetime.now(UTC).isoformat(),
            "total_sets": 3,
            "total_volume": 3000.0,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "notes": "Great workout",
            "mood": "good",
            "overall_rpe": 7,
            "pre_workout_energy": 8,
            "post_workout_energy": 6,
            "workout_type": "strength",
            "training_phase": "accumulation",
            "stress_before": "low",
            "stress_after": "low",
            "sleep_quality": "high",
        }
        mock_workouts_repo.increment_affinity_score.return_value = None

        # Act
        response = client.post(
            "/api/v1/workouts",
            json={
                "sets": [
                    {
                        "exercise_id": exercise_id,
                        "set_number": 1,
                        "weight": 100,
                        "reps": 10,
                        "set_type": "working",
                        "rpe": 8,
                        "rir": 2,
                        "tempo": "2-0-2-0",
                        "form_quality": 4,
                    },
                    {
                        "exercise_id": exercise_id,
                        "set_number": 2,
                        "weight": 100,
                        "reps": 10,
                        "set_type": "working",
                        "rpe": 9,
                        "rir": 1,
                    },
                    {
                        "exercise_id": exercise_id,
                        "set_number": 3,
                        "weight": 100,
                        "reps": 10,
                        "set_type": "working",
                        "rpe": 10,
                        "rir": 0,
                        "reached_failure": True,
                        "failure_type": "muscular",
                    },
                ],
                "notes": "Great workout",
                "mood": "good",
                "overall_rpe": 7,
                "pre_workout_energy": 8,
                "post_workout_energy": 6,
                "workout_type": "strength",
                "training_phase": "accumulation",
                "stress_before": "low",
                "stress_after": "low",
                "sleep_quality": "high",
            },
        )

        # Assert
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error: {response.json()}")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == workout_id
        assert data["total_sets"] == 3
        assert data["total_volume"] == 3000.0
        assert mock_workouts_repo.increment_affinity_score.called

    def test_create_workout_no_sets(
        self, client, mock_auth_dependency, mock_jwt_payload, mock_workouts_repo
    ):
        """Test workout creation fails without sets."""
        # Act
        response = client.post(
            "/api/v1/workouts",
            json={
                "sets": [],
                "notes": "No sets",
            },
        )

        # Assert
        # Pydantic validation catches this before it reaches our code
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "at least 1 item" in str(response.json()["detail"]).lower()

    def test_create_workout_with_plan(
        self, client, mock_auth_dependency, mock_jwt_payload, mock_workouts_repo
    ):
        """Test workout creation with plan reference."""
        # Arrange
        plan_id = str(uuid4())
        exercise_id = str(uuid4())

        mock_workouts_repo.verify_plan_access.return_value = True
        mock_workouts_repo.create_with_sets.return_value = {
            "id": str(uuid4()),
            "user_id": mock_jwt_payload.user_id,
            "plan_id": plan_id,
            "started_at": datetime.now(UTC).isoformat(),
            "completed_at": datetime.now(UTC).isoformat(),
            "total_sets": 1,
            "total_volume": 1000.0,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            # Required fields that can be None
            "notes": None,
            "mood": None,
            "pre_workout_energy": None,
            "post_workout_energy": None,
            "stress_before": None,
            "stress_after": None,
            "sleep_quality": None,
            "workout_type": None,
            "training_phase": None,
            "overall_rpe": None,
        }
        mock_workouts_repo.increment_affinity_score.return_value = None

        # Act
        response = client.post(
            "/api/v1/workouts",
            json={
                "plan_id": plan_id,
                "sets": [
                    {
                        "exercise_id": exercise_id,
                        "set_number": 1,
                        "weight": 100,
                        "reps": 10,
                        "set_type": "working",
                    }
                ],
            },
        )

        # Assert
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response: {response.json()}")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["plan_id"] == plan_id
        # Verify_plan_access is called with UUID object
        call_args = mock_workouts_repo.verify_plan_access.call_args
        assert str(call_args[0][0]) == plan_id

    def test_create_workout_plan_not_found(
        self, client, mock_auth_dependency, mock_jwt_payload, mock_workouts_repo
    ):
        """Test workout creation fails with invalid plan."""
        # Arrange
        plan_id = str(uuid4())
        mock_workouts_repo.verify_plan_access.return_value = False

        # Act
        response = client.post(
            "/api/v1/workouts",
            json={
                "plan_id": plan_id,
                "sets": [
                    {
                        "exercise_id": str(uuid4()),
                        "set_number": 1,
                        "weight": 100,
                        "reps": 10,
                        "set_type": "working",
                    }
                ],
            },
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Plan not found" in response.json()["detail"]


class TestListWorkouts:
    """Tests for GET /api/v1/workouts endpoint."""

    def test_list_workouts_success(
        self, client, mock_auth_dependency, mock_jwt_payload, mock_workouts_repo
    ):
        """Test successful workout listing."""
        # Arrange
        mock_workouts_repo.list.return_value = (
            [
                {
                    "id": str(uuid4()),
                    "plan_id": None,
                    "plan_name": None,
                    "started_at": datetime.now(UTC).isoformat(),
                    "completed_at": datetime.now(UTC).isoformat(),
                    "workout_type": "strength",
                    "training_phase": "accumulation",
                    "overall_rpe": 7,
                    "total_sets": 12,
                    "total_volume": 5000.0,
                    "duration_minutes": 45,
                    "primary_exercises": ["Squat", "Bench Press"],
                }
            ],
            1,
        )

        # Act
        response = client.get("/api/v1/workouts")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_list_workouts_with_filters(
        self, client, mock_auth_dependency, mock_jwt_payload, mock_workouts_repo
    ):
        """Test workout listing with filters."""
        # Arrange
        mock_workouts_repo.list.return_value = ([], 0)

        # Act
        response = client.get(
            "/api/v1/workouts",
            params={
                "workout_type": "hypertrophy",
                "training_phase": "intensification",
                "date_from": "2025-01-01",
                "date_to": "2025-01-31",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        mock_workouts_repo.list.assert_called_once()
        call_kwargs = mock_workouts_repo.list.call_args.kwargs
        assert call_kwargs["workout_type"] == "hypertrophy"
        assert call_kwargs["training_phase"] == "intensification"

    def test_list_workouts_pagination(
        self, client, mock_auth_dependency, mock_jwt_payload, mock_workouts_repo
    ):
        """Test workout listing with pagination."""
        # Arrange
        mock_workouts_repo.list.return_value = ([], 100)

        # Act
        response = client.get(
            "/api/v1/workouts",
            params={"page": 2, "per_page": 50},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 50
        assert data["total"] == 100
        # Check offset calculation
        mock_workouts_repo.list.assert_called_once()
        call_kwargs = mock_workouts_repo.list.call_args.kwargs
        assert call_kwargs["offset"] == 50  # (page 2 - 1) * 50

    def test_list_workouts_invalid_date_range(
        self, client, mock_auth_dependency, mock_jwt_payload, mock_workouts_repo
    ):
        """Test workout listing with invalid date range."""
        # Act
        response = client.get(
            "/api/v1/workouts",
            params={
                "date_from": "2025-01-31",
                "date_to": "2025-01-01",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "start_date must be before" in response.json()["detail"]
