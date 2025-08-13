"""
Tests for WorkoutMetricsService.

Tests the business logic for calculating workout metrics including
edge cases like zero-volume sets and workouts with no working sets.
"""

import pytest

from src.services.workout_metrics import WorkoutMetricsService


class TestWorkoutMetricsService:
    """Test suite for WorkoutMetricsService."""

    def test_calculate_session_metrics_basic(self):
        """Test basic session metrics calculation."""
        sets = [
            {"weight": 100, "reps": 10, "set_type": "working"},
            {"weight": 80, "reps": 12, "set_type": "working"},
            {"weight": 60, "reps": 15, "set_type": "warmup"},
        ]

        metrics = WorkoutMetricsService.calculate_session_metrics(sets)

        assert metrics["total_sets"] == 3
        assert metrics["total_volume"] == 2860.0  # (100*10) + (80*12) + (60*15)

    def test_calculate_session_metrics_zero_volume(self):
        """Test session metrics with zero-volume sets (bodyweight or failed sets)."""
        sets = [
            {"weight": 0, "reps": 10, "set_type": "working"},  # Bodyweight
            {"weight": 100, "reps": 0, "set_type": "working"},  # Failed rep
            {"weight": 0, "reps": 0, "set_type": "warmup"},  # Empty set
        ]

        metrics = WorkoutMetricsService.calculate_session_metrics(sets)

        assert metrics["total_sets"] == 3
        assert metrics["total_volume"] == 0.0

    def test_calculate_session_metrics_empty_list(self):
        """Test session metrics with empty sets list."""
        metrics = WorkoutMetricsService.calculate_session_metrics([])

        assert metrics["total_sets"] == 0
        assert metrics["total_volume"] == 0.0

    def test_calculate_session_metrics_missing_fields(self):
        """Test session metrics with missing weight/reps fields."""
        sets: list[dict] = [
            {"set_type": "working"},  # Missing weight and reps
            {"weight": 50, "set_type": "working"},  # Missing reps
            {"reps": 10, "set_type": "working"},  # Missing weight
        ]

        metrics = WorkoutMetricsService.calculate_session_metrics(sets)

        assert metrics["total_sets"] == 3
        assert metrics["total_volume"] == 0.0  # All default to 0

    def test_calculate_detail_metrics_mixed_sets(self):
        """Test detail metrics with mixed warmup and working sets."""
        sets = [
            {"volume_load": 500, "set_type": "warmup"},
            {"volume_load": 600, "set_type": "warmup"},
            {"volume_load": 1000, "set_type": "working"},
            {"volume_load": 1100, "set_type": "working"},
            {"volume_load": 1200, "set_type": "working"},
        ]

        metrics = WorkoutMetricsService.calculate_detail_metrics(sets)

        assert metrics["total_volume"] == 4400.0
        assert metrics["effective_volume"] == 3300.0  # Only working sets
        assert metrics["working_sets_ratio"] == pytest.approx(0.75)  # 3300/4400

    def test_calculate_detail_metrics_all_warmups(self):
        """Test detail metrics with only warmup sets (no working sets)."""
        sets = [
            {"volume_load": 500, "set_type": "warmup"},
            {"volume_load": 600, "set_type": "warmup"},
            {"volume_load": 700, "set_type": "warmup"},
        ]

        metrics = WorkoutMetricsService.calculate_detail_metrics(sets)

        assert metrics["total_volume"] == 1800.0
        assert metrics["effective_volume"] == 0.0
        assert metrics["working_sets_ratio"] == 0.0

    def test_calculate_detail_metrics_all_working(self):
        """Test detail metrics with only working sets."""
        sets = [
            {"volume_load": 1000, "set_type": "working"},
            {"volume_load": 1100, "set_type": "working"},
            {"volume_load": 1200, "set_type": "working"},
        ]

        metrics = WorkoutMetricsService.calculate_detail_metrics(sets)

        assert metrics["total_volume"] == 3300.0
        assert metrics["effective_volume"] == 3300.0
        assert metrics["working_sets_ratio"] == 1.0

    def test_calculate_detail_metrics_fallback_calculation(self):
        """Test detail metrics falls back to weight*reps when volume_load missing."""
        sets = [
            {"weight": 100, "reps": 10, "set_type": "working"},  # No volume_load
            {"volume_load": 1100, "set_type": "working"},  # Has volume_load
            {"weight": 80, "reps": 12, "set_type": "warmup"},  # No volume_load
        ]

        metrics = WorkoutMetricsService.calculate_detail_metrics(sets)

        assert metrics["total_volume"] == 3060.0  # 1000 + 1100 + 960
        assert metrics["effective_volume"] == 2100.0  # 1000 + 1100 (working only)
        assert metrics["working_sets_ratio"] == pytest.approx(0.686, rel=1e-2)

    def test_calculate_detail_metrics_zero_total_volume(self):
        """Test detail metrics handles zero total volume gracefully."""
        sets = [
            {"volume_load": 0, "set_type": "working"},
            {"volume_load": 0, "set_type": "warmup"},
        ]

        metrics = WorkoutMetricsService.calculate_detail_metrics(sets)

        assert metrics["total_volume"] == 0.0
        assert metrics["effective_volume"] == 0.0
        assert metrics["working_sets_ratio"] == 0.0  # Avoid division by zero

    def test_calculate_detail_metrics_unknown_set_types(self):
        """Test detail metrics with unknown set types (not warmup or working)."""
        sets: list[dict] = [
            {"volume_load": 1000, "set_type": "working"},
            {"volume_load": 500, "set_type": "dropset"},  # Unknown type
            {"volume_load": 600, "set_type": "cluster"},  # Unknown type
            {"volume_load": 700, "set_type": None},  # None type
        ]

        metrics = WorkoutMetricsService.calculate_detail_metrics(sets)

        assert metrics["total_volume"] == 2800.0
        assert metrics["effective_volume"] == 1000.0  # Only "working" counted
        assert metrics["working_sets_ratio"] == pytest.approx(0.357, rel=1e-2)

    def test_set_type_normalization(self):
        """Test that set type normalization handles case and whitespace correctly."""
        sets = [
            {"weight": 100, "reps": 10, "set_type": "WORKING"},  # Uppercase
            {"weight": 100, "reps": 10, "set_type": " working "},  # Whitespace
            {"weight": 100, "reps": 10, "set_type": "Working"},  # Mixed case
            {"weight": 100, "reps": 10, "set_type": "warmup"},  # Not working
        ]

        metrics = WorkoutMetricsService.calculate_detail_metrics(sets)

        # All three "working" variations should be counted
        assert metrics["total_volume"] == 4000.0  # All sets
        assert metrics["effective_volume"] == 3000.0  # Only working sets
        assert metrics["working_sets_ratio"] == 0.75  # 3 of 4 are working

    def test_calculate_detail_metrics_float_values(self):
        """Test detail metrics handles float weight and reps correctly."""
        sets = [
            {"weight": 102.5, "reps": 8.5, "set_type": "working"},  # Fractional reps
            {"weight": 77.5, "reps": 10, "set_type": "working"},
        ]

        metrics = WorkoutMetricsService.calculate_detail_metrics(sets)

        expected_volume = (102.5 * 8.5) + (77.5 * 10)  # 871.25 + 775 = 1646.25
        assert metrics["total_volume"] == pytest.approx(expected_volume)
        assert metrics["effective_volume"] == pytest.approx(expected_volume)
        assert metrics["working_sets_ratio"] == 1.0
