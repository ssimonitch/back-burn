"""Tests for the SupabaseWorkoutsRepository implementation."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from src.repositories.workouts import SupabaseWorkoutsRepository


@pytest.fixture
def mock_client():
    """Create a mock Supabase client."""
    return MagicMock()


@pytest.fixture
def repo(mock_client):
    """Create a repository instance with mock client."""
    return SupabaseWorkoutsRepository(mock_client)


def test_create_with_sets(repo, mock_client):
    """Test creating a workout with sets."""
    # Arrange
    user_id = str(uuid4())
    workout_id = str(uuid4())
    exercise_id = str(uuid4())

    workout_data = {
        "plan_id": uuid4(),
        "notes": "Great workout",
        "mood": "good",
        "overall_rpe": 7,
        "pre_workout_energy": 8,
        "post_workout_energy": 6,
        "workout_type": "strength",
        "training_phase": "accumulation",
        "stress_before": "low",
        "stress_after": "low",
        "sleep_quality": "good",
        "sets": [
            {
                "exercise_id": exercise_id,
                "set_number": 1,
                "weight": 100,
                "reps": 10,
                "set_type": "working",
                "rest_period": 90,
                "rpe": 8,
            }
        ],
    }

    # Mock the database responses
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": workout_id,
            "user_id": user_id,
            "started_at": datetime.now(UTC).isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
        }
    ]

    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        {
            "total_volume": 1000.0,
            "total_sets": 1,
            "completed_at": datetime.now(UTC).isoformat(),
        }
    ]

    # Act
    result = repo.create_with_sets(user_id, workout_data)

    # Assert
    assert result["id"] == workout_id
    assert result["user_id"] == user_id
    assert result["stress_before"] == "low"
    assert result["stress_after"] == "low"
    assert result["sleep_quality"] == "good"

    # Verify the correct calls were made
    assert (
        mock_client.table.call_count >= 3
    )  # workout_sessions insert, sets insert, workout_sessions update


def test_list_workouts(repo, mock_client):
    """Test listing workouts with filtering."""
    # Arrange
    user_id = str(uuid4())
    workout_id = str(uuid4())

    mock_response = Mock()
    mock_response.data = [
        {
            "id": workout_id,
            "user_id": user_id,
            "started_at": datetime.now(UTC).isoformat(),
            "completed_at": datetime.now(UTC).isoformat(),
            "total_volume": 5000.0,
            "total_sets": 20,
            "metadata": {
                "stress_before": "medium",
                "stress_after": "low",
            },
            "plans": {"name": "Power Plan"},
        }
    ]
    mock_response.count = 1

    mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_response

    # Act
    workouts, total = repo.list(
        user_id=user_id,
        limit=10,
        offset=0,
        start_date=None,
        end_date=None,
        plan_id=None,
    )

    # Assert
    assert len(workouts) == 1
    assert total == 1
    assert workouts[0]["id"] == workout_id
    assert workouts[0]["plan_name"] == "Power Plan"
    assert workouts[0]["stress_before"] == "medium"
    assert workouts[0]["stress_after"] == "low"
    assert "duration_minutes" in workouts[0]


def test_get_with_sets(repo, mock_client):
    """Test getting a workout with all its sets."""
    # Arrange
    user_id = str(uuid4())
    workout_id = uuid4()
    set_id = str(uuid4())

    # Mock workout response
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": str(workout_id),
            "user_id": user_id,
            "started_at": datetime.now(UTC).isoformat(),
            "completed_at": datetime.now(UTC).isoformat(),
            "total_volume": 1000.0,
            "metadata": {"sleep_quality": "excellent"},
            "plans": {"name": "Strength Plan"},
        }
    ]

    # Mock sets response (with chained .order() calls)
    mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.order.return_value.execute.return_value.data = [
        {
            "id": set_id,
            "workout_session_id": str(workout_id),
            "set_number": 1,
            "weight": 100,
            "reps": 10,
            "volume_load": 1000.0,
            "set_type": "working",
            "reps_in_reserve": 2,
            "rest_taken_seconds": 90,
            "exercises": {"name": "Bench Press"},
        }
    ]

    # Act
    result = repo.get_with_sets(workout_id, user_id)

    # Assert
    assert result is not None
    assert result["id"] == str(workout_id)
    assert result["plan_name"] == "Strength Plan"
    assert result["sleep_quality"] == "excellent"
    assert len(result["sets"]) == 1
    assert result["sets"][0]["exercise_name"] == "Bench Press"
    assert result["sets"][0]["rest_period"] == 90  # Mapped from rest_taken_seconds
    assert result["sets"][0]["rir"] == 2  # Mapped from reps_in_reserve
    assert "metrics" in result
    assert result["metrics"]["effective_volume"] == 1000.0


def test_delete_workout(repo, mock_client):
    """Test deleting a workout."""
    # Arrange
    workout_id = uuid4()

    mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = [
        {"id": str(workout_id)}
    ]

    # Act
    result = repo.delete(workout_id)

    # Assert
    assert result is True
    mock_client.table.assert_called_with("workout_sessions")


def test_verify_plan_access(repo, mock_client):
    """Test verifying plan access."""
    # Arrange
    plan_id = uuid4()
    user_id = str(uuid4())

    mock_client.table.return_value.select.return_value.eq.return_value.or_.return_value.execute.return_value.data = [
        {"id": str(plan_id), "deleted_at": None}
    ]

    # Act
    result = repo.verify_plan_access(plan_id, user_id)

    # Assert
    assert result is True
    mock_client.table.assert_called_with("plans")


def test_increment_affinity_score(repo, mock_client):
    """Test incrementing affinity score."""
    # Arrange
    user_id = str(uuid4())

    mock_client.rpc.return_value.execute.return_value.data = [1]

    # Act - should not raise
    repo.increment_affinity_score(user_id)

    # Assert
    mock_client.rpc.assert_called_once_with(
        "increment_affinity_score",
        {"p_user_id": user_id, "p_points": 1},
    )


def test_increment_affinity_score_handles_errors(repo, mock_client):
    """Test that affinity score errors don't break workout creation."""
    # Arrange
    user_id = str(uuid4())

    # Make RPC call fail
    mock_client.rpc.side_effect = Exception("Database error")

    # Act - should not raise
    repo.increment_affinity_score(user_id)

    # Assert - function completes without raising
    assert True  # If we get here, the test passed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
