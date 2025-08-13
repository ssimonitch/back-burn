"""
Service layer for workout metrics calculations.

This module provides business logic for calculating workout-level metrics
from sets data. Focuses on MVP metrics only: total_sets, total_volume,
and effective_volume (working sets only).
"""

from typing import TypedDict


class SetData(TypedDict, total=False):
    """Type definition for set data used in metrics calculations."""

    weight: float | int
    reps: float | int
    set_type: str
    volume_load: float  # Pre-calculated volume from DB


class SessionMetrics(TypedDict):
    """Type definition for calculated session metrics."""

    total_sets: int
    total_volume: float


class DetailMetrics(TypedDict):
    """Type definition for detailed workout metrics."""

    effective_volume: float
    total_volume: float
    working_sets_ratio: float


class WorkoutMetricsService:
    """Service for calculating workout metrics from sets data."""

    @staticmethod
    def calculate_session_metrics(sets: list[dict]) -> SessionMetrics:
        """
        Calculate metrics for a workout session at creation time.

        Args:
            sets: List of set data dictionaries with weight and reps

        Returns:
            SessionMetrics with total_sets and total_volume
        """
        total_volume = 0.0
        total_sets = len(sets)

        for set_data in sets:
            # Calculate volume for this set
            weight = float(set_data.get("weight", 0))
            reps = float(set_data.get("reps", 0))  # Allow fractional reps
            volume = weight * reps
            total_volume += volume

        return {
            "total_sets": total_sets,
            "total_volume": total_volume,
        }

    @staticmethod
    def calculate_detail_metrics(sets: list[dict]) -> DetailMetrics:
        """
        Calculate detailed metrics for workout retrieval.

        Distinguishes between working sets and warmup sets for
        effective volume calculation.

        Args:
            sets: List of set data from database with volume_load and set_type

        Returns:
            DetailMetrics with effective_volume, total_volume, and ratio
        """
        effective_volume = 0.0
        total_volume = 0.0

        for set_data in sets:
            # Use pre-calculated volume_load from DB if available,
            # otherwise calculate from weight * reps
            if "volume_load" in set_data:
                volume = float(set_data.get("volume_load", 0))
            else:
                weight = float(set_data.get("weight", 0))
                reps = float(set_data.get("reps", 0))  # Allow fractional reps
                volume = weight * reps

            total_volume += volume

            # Only include working sets in effective volume
            set_type = str(set_data.get("set_type", "")).lower().strip()
            if set_type == "working":
                effective_volume += volume

        # Calculate working sets ratio (quality indicator)
        working_sets_ratio = 0.0
        if total_volume > 0:
            working_sets_ratio = effective_volume / total_volume

        return {
            "effective_volume": effective_volume,
            "total_volume": total_volume,
            "working_sets_ratio": working_sets_ratio,
        }
