"""
Workout repository protocol and implementation.

This module defines the repository pattern for workout data access,
following the project's thin repository layer approach.
"""

from datetime import date
from typing import Any, Protocol
from uuid import UUID


class WorkoutsRepository(Protocol):
    """Protocol defining the workout repository interface.

    Repositories return raw dicts; endpoints construct Pydantic models.
    This keeps the API contract centralized at the endpoint layer.
    """

    async def create_with_sets(
        self, user_id: str, workout_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a workout session with its associated sets.

        Args:
            user_id: The user creating the workout
            workout_data: The workout data including sets array

        Returns:
            Raw dict of created workout with calculated fields
        """
        ...

    async def list(
        self,
        user_id: str,
        limit: int,
        offset: int,
        start_date: date | None = None,
        end_date: date | None = None,
        plan_id: UUID | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """List workout sessions with filtering and pagination.

        Args:
            user_id: The user whose workouts to retrieve
            limit: Maximum number of workouts to return
            offset: Number of workouts to skip
            start_date: Optional filter for workout start date
            end_date: Optional filter for workout end date
            plan_id: Optional filter for specific plan

        Returns:
            Tuple of (workouts list, total count)
        """
        ...

    async def get_with_sets(
        self, workout_id: UUID, user_id: str
    ) -> dict[str, Any] | None:
        """Get a workout session with all its sets.

        Args:
            workout_id: The workout to retrieve
            user_id: The user requesting the workout (for access control)

        Returns:
            Raw dict of workout with sets array, or None if not found
        """
        ...

    async def get_basic(self, workout_id: UUID) -> dict[str, Any] | None:
        """Get basic workout info without sets.

        Args:
            workout_id: The workout to retrieve

        Returns:
            Raw dict of workout basic info, or None if not found
        """
        ...

    async def delete(self, workout_id: UUID) -> bool:
        """Delete a workout session and its sets.

        Args:
            workout_id: The workout to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        ...

    async def verify_plan_access(self, plan_id: UUID, user_id: str) -> bool:
        """Verify user has access to a plan.

        Args:
            plan_id: The plan to check
            user_id: The user to verify access for

        Returns:
            True if user has access, False otherwise
        """
        ...

    async def increment_affinity_score(self, user_id: str) -> None:
        """Increment user's affinity score after workout completion.

        Sprint 7 requirement: Update affinity score on workout logging.

        Args:
            user_id: The user whose score to increment
        """
        ...


class SupabaseWorkoutsRepository:
    """Supabase implementation of the workouts repository.

    This is a stub implementation that will be completed during
    Sprint 4 implementation phase.
    """

    def __init__(self, client):
        """Initialize with Supabase client."""
        self.client = client

    async def create_with_sets(
        self, user_id: str, workout_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a workout session with its associated sets."""
        # Implementation will be added during Sprint 4
        raise NotImplementedError("Sprint 4 implementation pending")

    async def list(
        self,
        user_id: str,
        limit: int,
        offset: int,
        start_date: date | None = None,
        end_date: date | None = None,
        plan_id: UUID | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """List workout sessions with filtering and pagination."""
        # Implementation will be added during Sprint 4
        raise NotImplementedError("Sprint 4 implementation pending")

    async def get_with_sets(
        self, workout_id: UUID, user_id: str
    ) -> dict[str, Any] | None:
        """Get a workout session with all its sets."""
        # Implementation will be added during Sprint 4
        raise NotImplementedError("Sprint 4 implementation pending")

    async def get_basic(self, workout_id: UUID) -> dict[str, Any] | None:
        """Get basic workout info without sets."""
        # Implementation will be added during Sprint 4
        raise NotImplementedError("Sprint 4 implementation pending")

    async def delete(self, workout_id: UUID) -> bool:
        """Delete a workout session and its sets."""
        # Implementation will be added during Sprint 4
        raise NotImplementedError("Sprint 4 implementation pending")

    async def verify_plan_access(self, plan_id: UUID, user_id: str) -> bool:
        """Verify user has access to a plan."""
        # Implementation will be added during Sprint 4
        raise NotImplementedError("Sprint 4 implementation pending")

    async def increment_affinity_score(self, user_id: str) -> None:
        """Increment user's affinity score after workout completion."""
        # Implementation will be added during Sprint 4
        raise NotImplementedError("Sprint 4 implementation pending")
