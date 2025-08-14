"""
Workout repository protocol and implementation.

This module defines the repository pattern for workout data access,
following the project's thin repository layer approach.
"""

from datetime import UTC, date, datetime
from typing import Any, Protocol, TypedDict
from uuid import UUID

from src.services.workout_metrics import WorkoutMetricsService
from supabase import Client


class DBWorkoutRow(TypedDict, total=False):
    """Dictionary shape returned by the database for a workout session row.

    This intentionally mirrors the raw DB payload. Endpoints remain responsible
    for constructing Pydantic response models and filtering fields as needed.
    """

    id: str
    user_id: str
    plan_id: str | None
    plan_name: str | None  # From join
    started_at: str
    completed_at: str | None
    notes: str | None
    mood: str | None
    overall_rpe: int | None
    pre_workout_energy: int | None
    post_workout_energy: int | None
    workout_type: str | None
    training_phase: str | None
    total_volume: float
    total_sets: int
    metadata: dict[str, Any]
    created_at: str
    updated_at: str | None
    # Calculated fields
    duration_minutes: int | None
    primary_exercises: list[str]
    # Wellness fields from metadata
    stress_before: str | None
    stress_after: str | None
    sleep_quality: str | None


class DBSetRow(TypedDict, total=False):
    """Dictionary shape returned by the database for a set row.

    Includes all performance tracking fields and calculated metrics.
    """

    id: str
    workout_session_id: str
    exercise_id: str
    exercise_name: str | None  # From join
    set_number: int
    order_in_workout: int
    weight: float
    reps: int
    rest_taken_seconds: int | None
    rest_period: int | None  # Mapped from rest_taken_seconds
    rpe: int | None
    volume_load: float
    tempo: str | None
    range_of_motion_quality: str | None
    form_quality: int | None
    estimated_1rm: float | None
    intensity_percentage: float | None
    set_type: str
    reps_in_reserve: int | None
    rir: int | None  # Mapped from reps_in_reserve
    reached_failure: bool | None
    failure_type: str | None
    equipment_variation: str | None
    assistance_type: str | None
    notes: str | None
    technique_cues: list[str] | None
    created_at: str
    updated_at: str | None


class WorkoutsRepository(Protocol):
    """Protocol defining the workout repository interface.

    Repositories return raw dicts; endpoints construct Pydantic models.
    This keeps the API contract centralized at the endpoint layer.
    """

    def create_with_sets(
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

    def list(
        self,
        user_id: str,
        limit: int,
        offset: int,
        start_date: date | None = None,
        end_date: date | None = None,
        plan_id: UUID | None = None,
        workout_type: str | None = None,
        training_phase: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """List workout sessions with filtering and pagination.

        Args:
            user_id: The user whose workouts to retrieve
            limit: Maximum number of workouts to return
            offset: Number of workouts to skip
            start_date: Optional filter for workout start date
            end_date: Optional filter for workout end date
            plan_id: Optional filter for specific plan
            workout_type: Optional filter for workout type
            training_phase: Optional filter for training phase

        Returns:
            Tuple of (workouts list, total count)
        """
        ...

    def get_with_sets(self, workout_id: UUID, user_id: str) -> dict[str, Any] | None:
        """Get a workout session with all its sets.

        Args:
            workout_id: The workout to retrieve
            user_id: The user requesting the workout (for access control)

        Returns:
            Raw dict of workout with sets array, or None if not found
        """
        ...

    def get_basic(self, workout_id: UUID) -> dict[str, Any] | None:
        """Get basic workout info without sets.

        Args:
            workout_id: The workout to retrieve

        Returns:
            Raw dict of workout basic info, or None if not found
        """
        ...

    def delete(self, workout_id: UUID) -> bool:
        """Delete a workout session and its sets.

        Args:
            workout_id: The workout to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        ...

    def verify_plan_access(self, plan_id: UUID, user_id: str) -> bool | str:
        """Verify user has access to a plan.

        Args:
            plan_id: The plan to check
            user_id: The user to verify access for

        Returns:
            True if user has access
            "deleted" if plan exists but is soft-deleted
            False if plan doesn't exist or user lacks access
        """
        ...

    def increment_affinity_score(self, user_id: str) -> None:
        """Increment user's affinity score after workout completion.

        Sprint 7 requirement: Update affinity score on workout logging.

        Args:
            user_id: The user whose score to increment
        """
        ...


class SupabaseWorkoutsRepository:
    """Supabase implementation of the workouts repository.

    Provides data access layer for workout sessions and sets,
    following the thin repository pattern.
    """

    def __init__(self, client: Client):
        """Initialize with Supabase client."""
        self.client = client

    def create_with_sets(
        self, user_id: str, workout_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a workout session with its associated sets.

        Implements transactional creation of workout session and all sets.
        Handles wellness fields in metadata and calculates aggregates.

        Note: Task 9a recommends a database unique constraint on
        (workout_session_id, exercise_id, set_number) to enforce set_number
        uniqueness at the database level. Currently enforced at API level.
        """
        try:
            # Extract sets from workout data
            sets_data = workout_data.pop("sets", [])
            if not sets_data:
                raise ValueError("Workout must contain at least one set")

            # Prepare workout session data
            session_data = {
                "user_id": user_id,
                "started_at": datetime.now(UTC).isoformat(),
                "notes": workout_data.get("notes"),
                "mood": workout_data.get("mood"),
                "overall_rpe": workout_data.get("overall_rpe"),
                "pre_workout_energy": workout_data.get("pre_workout_energy"),
                "post_workout_energy": workout_data.get("post_workout_energy"),
                "workout_type": workout_data.get("workout_type"),
                "training_phase": workout_data.get("training_phase"),
            }

            # Add plan_id if provided
            if plan_id := workout_data.get("plan_id"):
                session_data["plan_id"] = str(plan_id)

            # Handle wellness fields that aren't in DB schema via metadata
            metadata = {}
            if stress_before := workout_data.get("stress_before"):
                metadata["stress_before"] = stress_before
            if stress_after := workout_data.get("stress_after"):
                metadata["stress_after"] = stress_after
            if sleep_quality := workout_data.get("sleep_quality"):
                metadata["sleep_quality"] = sleep_quality
            if metadata:
                session_data["metadata"] = metadata

            # Create workout session
            session_response = (
                self.client.table("workout_sessions").insert(session_data).execute()
            )
            if not session_response.data:
                raise RuntimeError("Failed to create workout session")

            workout_session = session_response.data[0]
            workout_id = workout_session["id"]

            # Use service to calculate metrics
            metrics_service = WorkoutMetricsService()
            session_metrics = metrics_service.calculate_session_metrics(sets_data)
            total_volume = session_metrics["total_volume"]

            # Prepare sets data for database insertion
            sets_to_insert = []
            for set_data in sets_data:
                # Extract weight and reps for DB insertion
                weight = float(set_data.get("weight", 0))
                reps = int(set_data.get("reps", 0))  # Cast to int for DB column type

                # Map field names from API model to DB columns
                set_row = {
                    "workout_session_id": workout_id,
                    "exercise_id": str(set_data["exercise_id"]),
                    "set_number": set_data["set_number"],
                    "weight": weight,
                    "reps": reps,
                    "set_type": set_data.get("set_type", "working"),
                }

                # Add optional fields if present
                if rest_period := set_data.get("rest_period"):
                    set_row["rest_taken_seconds"] = rest_period
                if tempo := set_data.get("tempo"):
                    set_row["tempo"] = tempo
                if rir := set_data.get("rir"):
                    set_row["reps_in_reserve"] = rir
                if rpe := set_data.get("rpe"):
                    set_row["rpe"] = rpe
                if form_quality := set_data.get("form_quality"):
                    set_row["form_quality"] = form_quality
                if intensity_percentage := set_data.get("intensity_percentage"):
                    set_row["intensity_percentage"] = intensity_percentage
                if reached_failure := set_data.get("reached_failure"):
                    set_row["reached_failure"] = reached_failure
                if failure_type := set_data.get("failure_type"):
                    set_row["failure_type"] = failure_type
                if estimated_1rm := set_data.get("estimated_1rm"):
                    set_row["estimated_1rm"] = estimated_1rm
                if equipment_variation := set_data.get("equipment_variation"):
                    set_row["equipment_variation"] = equipment_variation
                if assistance_type := set_data.get("assistance_type"):
                    set_row["assistance_type"] = assistance_type
                if rom_quality := set_data.get("range_of_motion_quality"):
                    set_row["range_of_motion_quality"] = rom_quality
                if notes := set_data.get("notes"):
                    set_row["notes"] = notes

                sets_to_insert.append(set_row)

            # Insert all sets
            sets_response = self.client.table("sets").insert(sets_to_insert).execute()
            if not sets_response.data:
                # Should rollback workout session in a real transaction
                # For now, we'll try to clean up
                self.client.table("workout_sessions").delete().eq(
                    "id", workout_id
                ).execute()
                raise RuntimeError("Failed to create workout sets")

            # Update workout session with calculated totals
            update_data = {
                "total_volume": total_volume,
                "total_sets": session_metrics["total_sets"],
                "completed_at": datetime.now(UTC).isoformat(),
            }
            update_response = (
                self.client.table("workout_sessions")
                .update(update_data)
                .eq("id", workout_id)
                .execute()
            )

            if update_response.data:
                workout_session.update(update_response.data[0])

            # Add metadata fields back for response
            if metadata:
                for key, value in metadata.items():
                    workout_session[key] = value

            return workout_session

        except Exception as e:
            # Let exceptions bubble up for the endpoint to handle
            raise e

    def list(
        self,
        user_id: str,
        limit: int,
        offset: int,
        start_date: date | None = None,
        end_date: date | None = None,
        plan_id: UUID | None = None,
        workout_type: str | None = None,
        training_phase: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """List workout sessions with filtering and pagination.

        Returns workout summaries with primary exercises calculated.
        """
        try:
            # Build base query with user filter
            query = (
                self.client.table("workout_sessions")
                .select(
                    "*",
                    "plans!workout_sessions_plan_id_fkey(name)",
                    count="exact",
                )
                .eq("user_id", user_id)
            )

            # Apply optional filters
            if start_date:
                query = query.gte("started_at", start_date.isoformat())
            if end_date:
                # Add one day to include the entire end date
                end_datetime = datetime.combine(end_date, datetime.max.time()).replace(
                    tzinfo=UTC
                )
                query = query.lte("started_at", end_datetime.isoformat())
            if plan_id:
                query = query.eq("plan_id", str(plan_id))
            if workout_type:
                query = query.eq("workout_type", workout_type)
            if training_phase:
                query = query.eq("training_phase", training_phase)

            # Apply ordering and pagination
            query = query.order("started_at", desc=True).range(
                offset, offset + limit - 1
            )

            # Execute query
            response = query.execute()
            workouts = response.data or []
            total_count = response.count or 0

            # Process workouts to add calculated fields
            processed_workouts = []
            for workout in workouts:
                # Extract plan name from join
                plan_data = workout.pop("plans", None)
                if plan_data and isinstance(plan_data, dict):
                    workout["plan_name"] = plan_data.get("name")

                # Calculate duration if completed
                if workout.get("completed_at") and workout.get("started_at"):
                    started = datetime.fromisoformat(workout["started_at"])
                    completed = datetime.fromisoformat(workout["completed_at"])
                    duration = completed - started
                    workout["duration_minutes"] = int(duration.total_seconds() / 60)

                # Get top exercises for this workout (simplified for now)
                # In a full implementation, this would query sets and aggregate
                workout["primary_exercises"] = []

                # Extract wellness fields from metadata if present
                if metadata := workout.get("metadata"):
                    if isinstance(metadata, dict):
                        for key in ["stress_before", "stress_after", "sleep_quality"]:
                            if value := metadata.get(key):
                                workout[key] = value

                processed_workouts.append(workout)

            return processed_workouts, total_count

        except Exception as e:
            raise e

    def get_with_sets(self, workout_id: UUID, user_id: str) -> dict[str, Any] | None:
        """Get a workout session with all its sets.

        Returns detailed workout with all sets, exercise names, and metrics.
        """
        try:
            # Get workout session with plan name
            workout_response = (
                self.client.table("workout_sessions")
                .select("*, plans!workout_sessions_plan_id_fkey(name)")
                .eq("id", str(workout_id))
                .eq("user_id", user_id)
                .execute()
            )

            if not workout_response.data:
                return None

            workout = workout_response.data[0]

            # Extract plan name from join
            plan_data = workout.pop("plans", None)
            if plan_data and isinstance(plan_data, dict):
                workout["plan_name"] = plan_data.get("name")

            # Get all sets for this workout with exercise names
            sets_response = (
                self.client.table("sets")
                .select("*, exercises!sets_exercise_id_fkey(name)")
                .eq("workout_session_id", str(workout_id))
                .order("exercise_id")
                .order("set_number")
                .execute()
            )

            sets = sets_response.data or []

            # Process sets to add calculated fields and exercise names
            processed_sets = []
            order_in_workout = 1

            for set_data in sets:
                # Extract exercise name from join
                exercise_data = set_data.pop("exercises", None)
                if exercise_data and isinstance(exercise_data, dict):
                    set_data["exercise_name"] = exercise_data.get("name")

                # Add order_in_workout
                set_data["order_in_workout"] = order_in_workout
                order_in_workout += 1

                # Map rest_taken_seconds to rest_period for API compatibility
                if rest_seconds := set_data.get("rest_taken_seconds"):
                    set_data["rest_period"] = rest_seconds

                # Map reps_in_reserve to rir for API compatibility
                if rir := set_data.get("reps_in_reserve"):
                    set_data["rir"] = rir

                processed_sets.append(set_data)

            workout["sets"] = processed_sets

            # Calculate duration if completed
            if workout.get("completed_at") and workout.get("started_at"):
                started = datetime.fromisoformat(workout["started_at"])
                completed = datetime.fromisoformat(workout["completed_at"])
                duration = completed - started
                workout["duration_minutes"] = int(duration.total_seconds() / 60)

            # Use service to calculate detailed metrics
            metrics_service = WorkoutMetricsService()
            detail_metrics = metrics_service.calculate_detail_metrics(sets)
            workout["metrics"] = detail_metrics

            # Extract wellness fields from metadata if present
            if metadata := workout.get("metadata"):
                if isinstance(metadata, dict):
                    for key in ["stress_before", "stress_after", "sleep_quality"]:
                        if value := metadata.get(key):
                            workout[key] = value

            return workout

        except Exception as e:
            raise e

    def get_basic(self, workout_id: UUID) -> dict[str, Any] | None:
        """Get basic workout info without sets.

        Used for permission checks and basic info retrieval.
        """
        try:
            response = (
                self.client.table("workout_sessions")
                .select("*")
                .eq("id", str(workout_id))
                .execute()
            )

            if not response.data:
                return None

            workout = response.data[0]

            # Extract wellness fields from metadata if present
            if metadata := workout.get("metadata"):
                if isinstance(metadata, dict):
                    for key in ["stress_before", "stress_after", "sleep_quality"]:
                        if value := metadata.get(key):
                            workout[key] = value

            return workout

        except Exception as e:
            raise e

    def delete(self, workout_id: UUID) -> bool:
        """Delete a workout session and its sets.

        Sets are cascade deleted via foreign key constraint.
        """
        try:
            response = (
                self.client.table("workout_sessions")
                .delete()
                .eq("id", str(workout_id))
                .execute()
            )

            # Check if any row was deleted
            return bool(response.data)

        except Exception as e:
            raise e

    def verify_plan_access(self, plan_id: UUID, user_id: str) -> bool | str:
        """Verify user has access to a plan.

        User has access if they own the plan or it's public and not deleted.

        Returns:
            True if user has access
            "deleted" if plan exists but is soft-deleted
            False if plan doesn't exist or user lacks access
        """
        try:
            # First check if plan exists at all (regardless of deleted status)
            exists_response = (
                self.client.table("plans")
                .select("id, deleted_at")
                .eq("id", str(plan_id))
                .or_(f"user_id.eq.{user_id},is_public.eq.true")
                .execute()
            )

            if not exists_response.data:
                return False  # Plan doesn't exist or user lacks access

            # Check if the plan is soft-deleted
            plan = exists_response.data[0]
            if plan.get("deleted_at") is not None:
                return "deleted"  # Plan exists but is soft-deleted

            return True  # Plan exists and is accessible

        except Exception as e:
            raise e

    def increment_affinity_score(self, user_id: str) -> None:
        """Increment user's affinity score after workout completion.

        Uses the database function to atomically increment the score.
        """
        try:
            # Call the database function to increment affinity score
            response = self.client.rpc(
                "increment_affinity_score",
                {"p_user_id": user_id, "p_points": 1},
            ).execute()

            if not response.data:
                # Log but don't fail the workout creation
                # In production, this should be logged
                pass

        except Exception:
            # Don't fail workout creation if affinity score update fails
            # In production, this should be logged
            pass
