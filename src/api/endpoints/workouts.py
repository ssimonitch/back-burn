"""
Workout API endpoints for workout session management.

This module provides RESTful endpoints for creating, reading, and managing
workout sessions and their associated sets. Workouts track exercise performance,
wellness metrics, and training progress.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from src.core.auth import JWTPayload, require_auth
from src.core.di import get_workouts_repository
from src.models.enums import TrainingPhase, WorkoutType
from src.models.workout import (
    EnhancedPaginatedWorkoutResponse,
    WorkoutCreateModel,
    WorkoutDetailResponseModel,
    WorkoutResponseModel,
    WorkoutSummaryModel,
)
from src.repositories.workouts import WorkoutsRepository

router = APIRouter(prefix="/api/v1/workouts", tags=["workouts"])


@router.post(
    "/",
    response_model=WorkoutResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Log a new workout session",
    responses={
        201: {
            "description": "Workout session created successfully",
            "model": WorkoutResponseModel,
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_sets": {
                            "summary": "No sets provided",
                            "value": {
                                "detail": "Workout must contain at least one set"
                            },
                        },
                        "invalid_rpe": {
                            "summary": "Invalid RPE value",
                            "value": {"detail": "RPE must be between 1 and 10"},
                        },
                        "invalid_tempo": {
                            "summary": "Invalid tempo format",
                            "value": {
                                "detail": "Tempo must be in format X-X-X-X (e.g., 2-0-2-0)"
                            },
                        },
                        "duplicate_set_number": {
                            "summary": "Duplicate set number for exercise",
                            "value": {
                                "detail": "Duplicate set_number 2 for exercise_id 123e4567-e89b-12d3-a456-426614174000. Each exercise must have unique set numbers starting from 1."
                            },
                        },
                    }
                }
            },
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        404: {
            "description": "Referenced plan not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Plan not found or access denied"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "sets", 0, "weight"],
                                "msg": "ensure this value is greater than or equal to 0",
                                "type": "value_error.number.not_ge",
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to create workout session"}
                }
            },
        },
    },
)
async def create_workout(
    workout_data: WorkoutCreateModel,
    jwt_payload: JWTPayload = Depends(require_auth),
    repo: WorkoutsRepository = Depends(get_workouts_repository),
) -> WorkoutResponseModel:
    """
    Create a new workout session with associated sets.

    Creates a new workout session for the authenticated user with comprehensive
    powerbuilding performance tracking. Each workout must contain at least one set.

    Supports detailed tracking of:
    - Performance metrics: weight, reps, RIR, RPE, tempo, form quality
    - Wellness indicators: mood, energy levels, stress, sleep quality
    - Training context: workout type, training phase, overall session RPE
    - Advanced metrics: intensity percentage, 1RM estimates, failure tracking
    - Equipment variations and assistance types

    The workout will automatically:
    - Calculate volume_load for each set (weight * reps)
    - Distinguish between working sets and warm-up sets for effective volume
    - Set order_in_workout for sets based on submission order
    - Track timestamps for session start and completion
    - Update user's affinity score upon successful logging

    Args:
        workout_data: The workout creation data including sets
        jwt_payload: The authenticated user's JWT payload
        repo: The workouts repository instance

    Returns:
        The created workout session with all database-generated fields

    Raises:
        HTTPException: If workout creation fails due to validation or database errors
    """
    try:
        # Validate at least one set is provided
        if not workout_data.sets or len(workout_data.sets) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workout must contain at least one set",
            )

        # Task 9a: Validate set_number uniqueness per exercise_id
        # For each exercise, ensure set_numbers are unique (already ≥1 via Field constraint)
        exercise_set_numbers: dict[UUID, set[int]] = {}
        for idx, workout_set in enumerate(workout_data.sets):
            exercise_id = workout_set.exercise_id
            set_number = workout_set.set_number

            if exercise_id not in exercise_set_numbers:
                exercise_set_numbers[exercise_id] = set()

            if set_number in exercise_set_numbers[exercise_id]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Duplicate set_number {set_number} for exercise_id {exercise_id}. "
                        f"Each exercise must have unique set numbers starting from 1."
                    ),
                )

            exercise_set_numbers[exercise_id].add(set_number)

        # If plan_id is provided, verify it exists and user has access
        if workout_data.plan_id:
            plan_access = repo.verify_plan_access(
                workout_data.plan_id, jwt_payload.user_id
            )
            if plan_access == "deleted":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan has been deleted and cannot be used for new workouts",
                )
            elif not plan_access:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan not found or access denied",
                )

        # Create workout session with sets via repository
        created_workout = repo.create_with_sets(
            jwt_payload.user_id, workout_data.model_dump()
        )

        # Update user's affinity score (Sprint 7 requirement)
        repo.increment_affinity_score(jwt_payload.user_id)

        return WorkoutResponseModel(**created_workout)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as ve:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except ValueError as ve:
        # Handle other validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        # Handle unexpected errors
        error_message = str(e)

        # Check for specific database constraint violations
        if "foreign key violation" in error_message.lower():
            if "exercise" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid exercise ID in one or more sets",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reference in workout data",
                )
        elif "check constraint" in error_message.lower():
            # Extract specific constraint that failed
            if "rpe" in error_message or "session_rpe" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RPE must be between 1 and 10",
                )
            elif "rir" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RIR must be between 0 and 10",
                )
            elif "weight" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Weight must be non-negative",
                )
            elif "reps" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reps must be non-negative",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validation error: {error_message}",
                )
        else:
            # Log the error in production
            # logger.error(f"Failed to create workout: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create workout session due to an internal error",
            )


@router.get(
    "/",
    response_model=EnhancedPaginatedWorkoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's workout sessions",
    responses={
        200: {
            "description": "List of workout sessions retrieved successfully",
            "model": EnhancedPaginatedWorkoutResponse,
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "per_page"],
                                "msg": "ensure this value is greater than 0",
                                "type": "value_error.number.not_gt",
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to retrieve workouts"}
                }
            },
        },
    },
)
async def get_workouts(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number (1-indexed)",
    ),
    per_page: int = Query(
        default=20,
        gt=0,
        le=100,
        description="Number of items per page (1-100)",
    ),
    start_date: date | None = Query(
        default=None,
        alias="date_from",
        description="Filter workouts from this date (inclusive)",
    ),
    end_date: date | None = Query(
        default=None,
        alias="date_to",
        description="Filter workouts until this date (inclusive)",
    ),
    plan_id: UUID | None = Query(
        default=None,
        description="Filter workouts by plan ID",
    ),
    workout_type: WorkoutType | None = Query(
        default=None,
        description="Filter by workout type (strength/hypertrophy/power/conditioning)",
    ),
    training_phase: TrainingPhase | None = Query(
        default=None,
        description="Filter by training phase (accumulation/intensification/realization/deload)",
    ),
    jwt_payload: JWTPayload = Depends(require_auth),
    repo: WorkoutsRepository = Depends(get_workouts_repository),
) -> EnhancedPaginatedWorkoutResponse:
    """
    Retrieve a paginated list of the authenticated user's workout sessions.

    Returns a paginated list of workout sessions filtered by the authenticated user's ID.
    Workouts are sorted by started_at DESC to show most recent workouts first.
    Each workout includes summary statistics like total sets and volume, with
    distinction between working sets and total sets for volume calculations.

    Filtering options:
    - Date range: Filter by workout date using date_from and date_to
    - Plan: Filter by specific workout plan using plan_id
    - Workout type: Filter by training stimulus (strength/hypertrophy/power/conditioning)
    - Training phase: Filter by periodization phase (accumulation/intensification/realization/deload)

    Args:
        page: Page number (1-indexed)
        per_page: Number of items per page (1-100)
        start_date: Optional start date filter (inclusive)
        end_date: Optional end date filter (inclusive)
        plan_id: Optional plan ID filter
        workout_type: Optional workout type filter
        training_phase: Optional training phase filter
        jwt_payload: The authenticated user's JWT payload
        repo: The workouts repository instance

    Returns:
        EnhancedPaginatedWorkoutResponse containing the workouts array and pagination metadata

    Raises:
        HTTPException: If workout retrieval fails due to database errors
    """
    try:
        # Validate date range if both provided
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before or equal to end_date",
            )

        # Calculate offset from page and per_page
        offset = (page - 1) * per_page

        # Retrieve workouts via repository
        workouts, total_count = repo.list(
            user_id=jwt_payload.user_id,
            limit=per_page,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            plan_id=plan_id,
            workout_type=workout_type.value if workout_type else None,
            training_phase=training_phase.value if training_phase else None,
        )

        # Convert workout data to response models
        workout_models = [WorkoutSummaryModel(**workout) for workout in workouts]

        # Return the paginated response
        return EnhancedPaginatedWorkoutResponse(
            items=workout_models,
            total=total_count,
            page=page,
            per_page=per_page,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as ve:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except ValueError as ve:
        # Handle other validation errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception:
        # Handle unexpected errors
        # Log the error in production
        # logger.error(f"Failed to retrieve workouts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workouts due to an internal error",
        )


@router.get(
    "/{workout_id}",
    response_model=WorkoutDetailResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Get a specific workout session by ID",
    responses={
        200: {
            "description": "Workout session retrieved successfully",
            "model": WorkoutDetailResponseModel,
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        404: {
            "description": "Workout not found or access denied",
            "content": {
                "application/json": {"example": {"detail": "Workout not found"}}
            },
        },
        422: {
            "description": "Invalid workout ID format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["path", "workout_id"],
                                "msg": "value is not a valid uuid",
                                "type": "type_error.uuid",
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to retrieve workout"}
                }
            },
        },
    },
)
async def get_workout_by_id(
    workout_id: UUID,
    jwt_payload: JWTPayload = Depends(require_auth),
    repo: WorkoutsRepository = Depends(get_workouts_repository),
) -> WorkoutDetailResponseModel:
    """
    Retrieve a specific workout session with all its sets.

    Returns the detailed workout data for the specified workout_id, including
    all sets performed, exercise information, and wellness metrics. Access is
    restricted to the workout owner via RLS policies.

    The response includes:
    - Full workout session details
    - All sets with exercise names and performance metrics
    - Calculated statistics (total volume, duration)
    - Wellness tracking data

    Args:
        workout_id: The UUID of the workout to retrieve
        jwt_payload: The authenticated user's JWT payload
        repo: The workouts repository instance

    Returns:
        WorkoutDetailResponseModel containing the workout details with all sets

    Raises:
        HTTPException:
            - 404 if workout doesn't exist or user lacks permission
            - 500 if retrieval fails due to database errors
    """
    try:
        # Retrieve workout with sets via repository
        workout = repo.get_with_sets(workout_id, jwt_payload.user_id)

        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found",
            )

        # Return the workout data
        return WorkoutDetailResponseModel(**workout)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as ve:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except ValueError as ve:
        # Handle other validation errors (e.g., invalid UUID format)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception:
        # Handle unexpected errors
        # Log the error in production
        # logger.error(f"Failed to retrieve workout {workout_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workout due to an internal error",
        )


@router.delete(
    "/{workout_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workout session",
    responses={
        204: {
            "description": "Workout deleted successfully",
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        403: {
            "description": "User does not own this workout",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to delete this workout"
                    }
                }
            },
        },
        404: {
            "description": "Workout not found",
            "content": {
                "application/json": {"example": {"detail": "Workout not found"}}
            },
        },
        422: {
            "description": "Invalid workout ID format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["path", "workout_id"],
                                "msg": "value is not a valid uuid",
                                "type": "type_error.uuid",
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {"example": {"detail": "Failed to delete workout"}}
            },
        },
    },
)
async def delete_workout(
    workout_id: UUID,
    jwt_payload: JWTPayload = Depends(require_auth),
    repo: WorkoutsRepository = Depends(get_workouts_repository),
) -> None:
    """
    Delete a workout session and all associated sets.

    Performs a hard delete of the workout session and all its associated sets.
    Only the workout owner can delete their workouts. This operation is
    permanent and cannot be undone.

    Args:
        workout_id: The UUID of the workout to delete
        jwt_payload: The authenticated user's JWT payload
        repo: The workouts repository instance

    Returns:
        None (204 No Content on success)

    Raises:
        HTTPException:
            - 403 if user doesn't own the workout
            - 404 if workout doesn't exist
            - 500 if deletion fails due to database errors
    """
    try:
        # Check if workout exists and user owns it
        workout = repo.get_basic(workout_id)

        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found",
            )

        # Verify the user owns this workout
        if str(workout.get("user_id")) != str(jwt_payload.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this workout",
            )

        # Delete the workout (sets will cascade delete)
        success = repo.delete(workout_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete workout",
            )

        # Return 204 No Content on successful deletion
        return None

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as ve:
        # Handle Pydantic validation errors (e.g., invalid UUID format)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except ValueError as ve:
        # Handle other validation errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception:
        # Handle unexpected errors
        # Log the error in production
        # logger.error(f"Failed to delete workout {workout_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workout due to an internal error",
        )
