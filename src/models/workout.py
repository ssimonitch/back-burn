"""
Pydantic models for workout session operations.

This module defines the data models for creating, updating, and responding
with workout session and set data. It enforces validation rules and provides
type safety for workout-related API operations.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .common import PaginatedResponse
from .enums import (
    AssistanceType,
    FailureType,
    MoodRating,
    RangeOfMotionQuality,
    SetType,
    TrainingPhase,
    WellnessRating,
    WorkoutType,
)

# Shared base configuration
base_config = ConfigDict(
    validate_assignment=True,
    extra="forbid",
    use_enum_values=True,
    str_strip_whitespace=True,
)


# Input models for sets
class SetCreateModel(BaseModel):
    """Model for creating a new workout set."""

    model_config = base_config

    exercise_id: UUID
    set_type: SetType = Field(
        SetType.WORKING,
        description="Classification of set purpose - critical for volume calculations",
    )
    set_number: int = Field(
        ...,
        ge=1,
        le=50,
        description="Order of this set within the exercise (1st, 2nd, etc.)",
    )
    weight: float = Field(..., ge=0, le=1000, description="Weight in kg (max 1000kg)")
    reps: int = Field(..., ge=0, le=1000)
    rest_period: int | None = Field(
        None, ge=0, le=3600, description="Rest period in seconds"
    )
    tempo: str | None = Field(
        None,
        max_length=10,
        pattern=r"^\d{1,2}-\d{1,2}-\d{1,2}-\d{1,2}$",
        description="Tempo notation (e.g., 2-0-2-0 for eccentric-pause-concentric-pause)",
    )
    rir: int | None = Field(None, ge=0, le=10, description="Reps in Reserve (0-10)")
    rpe: int | None = Field(
        None, ge=1, le=10, description="Rate of Perceived Exertion (1-10)"
    )
    form_quality: int | None = Field(
        None,
        ge=1,
        le=5,
        description="Form quality: 1=poor, 2=fair, 3=good, 4=very good, 5=perfect",
    )
    intensity_percentage: float | None = Field(
        None,
        ge=0,
        le=200,
        description="Percentage of 1RM used (>100% for overload/assisted work)",
    )
    reached_failure: bool | None = Field(
        None, description="Whether set was taken to complete failure"
    )
    failure_type: FailureType | None = Field(
        None,
        description="Type of failure if reached (muscular/form/cardiovascular/motivation)",
    )
    estimated_1rm: float | None = Field(
        None,
        ge=0,
        le=1000,
        description="Calculated 1RM based on weight × reps (Epley formula)",
    )
    equipment_variation: str | None = Field(
        None,
        max_length=100,
        description="Specific variation (e.g., 'close_grip', 'deficit', 'paused')",
    )
    assistance_type: AssistanceType | None = Field(
        None,
        description="Type of assistance used (none/spotter/machine_assist/band_assist)",
    )
    range_of_motion_quality: RangeOfMotionQuality | None = Field(
        None, description="Range of motion quality assessment"
    )
    notes: str | None = Field(None, max_length=500)


# Input models for workout sessions
class WorkoutCreateModel(BaseModel):
    """Model for creating a new workout session."""

    model_config = base_config

    plan_id: UUID | None = Field(None, description="Optional reference to workout plan")
    notes: str | None = Field(None, max_length=2000)
    # Post-workout mood (database has single 'mood' field)
    mood: MoodRating | None = Field(None, description="Post-workout mood")
    # Energy levels (1-10 scale, not enum)
    pre_workout_energy: int | None = Field(
        None, ge=1, le=10, description="Pre-workout energy level (1-10)"
    )
    post_workout_energy: int | None = Field(
        None, ge=1, le=10, description="Post-workout energy level (1-10)"
    )
    # Wellness tracking
    stress_before: WellnessRating | None = None
    stress_after: WellnessRating | None = None
    sleep_quality: WellnessRating | None = None
    # Training context
    workout_type: WorkoutType | None = Field(
        None, description="Primary training stimulus of the session"
    )
    training_phase: TrainingPhase | None = Field(
        None, description="Current periodization phase"
    )
    overall_rpe: int | None = Field(
        None, ge=1, le=10, description="Overall session RPE (1-10)"
    )
    sets: list[SetCreateModel] = Field(
        ..., min_length=1, description="List of sets performed in this workout"
    )


# Response models for sets
class SetResponseModel(BaseModel):
    """Model for workout set API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workout_session_id: UUID
    exercise_id: UUID
    exercise_name: str | None = Field(None, description="Exercise name from join")
    set_type: SetType
    set_number: int
    order_in_workout: int
    weight: float
    reps: int
    rest_period: int | None = None
    tempo: str | None = None
    rir: int | None = None
    rpe: int | None = None
    form_quality: int | None = None
    intensity_percentage: float | None = None
    reached_failure: bool | None = None
    failure_type: FailureType | None = None
    estimated_1rm: float | None = None
    equipment_variation: str | None = None
    assistance_type: AssistanceType | None = None
    range_of_motion_quality: RangeOfMotionQuality | None = None
    volume_load: float = Field(description="Calculated as weight * reps")
    notes: str | None = None
    created_at: datetime


# New model for comprehensive workout metrics
class WorkoutMetricsModel(BaseModel):
    """Model for detailed workout performance metrics."""

    model_config = ConfigDict(from_attributes=True)

    # Primary volume metrics
    effective_volume: float = Field(
        description="Total volume from working sets only (excludes warm-ups)"
    )
    total_volume: float = Field(description="Total volume including all set types")
    working_sets_ratio: float = Field(
        description="Percentage of effective volume vs total volume (quality indicator)"
    )

    # Intensity metrics
    average_intensity: float | None = Field(
        None, description="Average percentage of 1RM for working sets"
    )

    # Movement pattern breakdown
    volume_by_movement_pattern: dict[str, float] = Field(
        default_factory=dict,
        description="Volume distribution by movement pattern (push/pull/legs/core)",
    )

    # Progression tracking
    estimated_1rm_progression: dict[str, float] = Field(
        default_factory=dict, description="Estimated 1RM values by exercise_id"
    )

    # Fatigue indicators
    fatigue_index: float | None = Field(
        None,
        ge=0,
        le=1,
        description="Fatigue score based on form quality degradation (0=fresh, 1=exhausted)",
    )


# Response models for workout sessions
class WorkoutResponseModel(BaseModel):
    """Model for workout session API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    plan_id: UUID | None
    started_at: datetime
    completed_at: datetime | None
    notes: str | None
    mood: MoodRating | None = None
    pre_workout_energy: int | None = None
    post_workout_energy: int | None = None
    stress_before: WellnessRating | None = None
    stress_after: WellnessRating | None = None
    sleep_quality: WellnessRating | None = None
    workout_type: WorkoutType | None = None
    training_phase: TrainingPhase | None = None
    overall_rpe: int | None = None
    total_sets: int = Field(0, description="Total number of sets in this workout")
    total_volume: float = Field(0, description="Total volume (sum of all volume_load)")
    created_at: datetime
    updated_at: datetime | None


class WorkoutDetailResponseModel(BaseModel):
    """Model for detailed workout session with sets and metrics."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    plan_id: UUID | None
    plan_name: str | None = Field(None, description="Plan name from join")
    started_at: datetime
    completed_at: datetime | None
    notes: str | None
    mood: MoodRating | None = None
    pre_workout_energy: int | None = None
    post_workout_energy: int | None = None
    stress_before: WellnessRating | None = None
    stress_after: WellnessRating | None = None
    sleep_quality: WellnessRating | None = None
    workout_type: WorkoutType | None = None
    training_phase: TrainingPhase | None = None
    overall_rpe: int | None = None
    total_sets: int
    total_volume: float
    duration_minutes: int | None = Field(
        None, description="Calculated duration in minutes"
    )
    sets: list[SetResponseModel] = Field(
        description="All sets performed, properly ordered by exercise and set number"
    )
    metrics: WorkoutMetricsModel | None = Field(
        None,
        description="Comprehensive workout metrics including effective volume and movement patterns",
    )
    created_at: datetime
    updated_at: datetime | None


# Response model for workout summary in list view
class WorkoutSummaryModel(BaseModel):
    """Model for workout session summary in list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID | None
    plan_name: str | None
    started_at: datetime
    completed_at: datetime | None
    workout_type: WorkoutType | None = None
    training_phase: TrainingPhase | None = None
    overall_rpe: int | None = None
    total_sets: int
    total_volume: float
    duration_minutes: int | None
    primary_exercises: list[str] = Field(
        default_factory=list,
        description="Top 3 exercises by volume",
    )


# Enhanced paginated response for workout lists
class EnhancedPaginatedWorkoutResponse(PaginatedResponse[WorkoutSummaryModel]):
    """Paginated workout response with aggregate metrics."""

    aggregate_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Aggregate metrics for the current page (effective_volume, total_volume, etc.)",
    )


# Response model for workout history with aggregate statistics
class WorkoutHistoryStatsModel(BaseModel):
    """Model for aggregate workout statistics over time."""

    model_config = ConfigDict(from_attributes=True)

    # Session counts
    total_sessions: int = Field(
        description="Total number of workout sessions completed"
    )

    # Volume metrics - distinguishing effective vs total
    total_volume: float = Field(
        description="Total volume across all workouts (all sets)"
    )
    effective_volume: float = Field(description="Total volume from working sets only")
    working_sets_count: int = Field(
        description="Total number of working sets performed"
    )
    total_sets: int = Field(description="Total number of sets performed")
    total_reps: int = Field(description="Total number of reps performed")

    # Training distribution
    training_phase_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of sessions by training phase"
    )
    workout_type_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of sessions by workout type"
    )

    # Movement patterns
    movement_pattern_distribution: dict[str, float] = Field(
        default_factory=dict,
        description="Volume distribution by movement pattern (push/pull/legs)",
    )

    # Intensity metrics
    average_intensity_percentage: float | None = Field(
        None,
        description="Average training intensity as % of 1RM across all working sets",
    )

    # Session averages
    avg_session_duration: float | None = Field(
        None, description="Average workout duration in minutes"
    )
    avg_session_volume: float | None = Field(
        None, description="Average volume per session"
    )
    avg_session_rpe: float | None = Field(
        None, description="Average session RPE (1-10)"
    )

    # Frequency and consistency
    most_frequent_exercises: list[dict[str, Any]] = Field(
        default_factory=list, description="Top exercises by frequency with counts"
    )
    weekly_frequency: float | None = Field(
        None, description="Average workouts per week"
    )
    date_range: dict[str, datetime | None] = Field(
        description="First and last workout dates"
    )
    plans_used: list[dict[str, Any]] = Field(
        default_factory=list, description="Workout plans used with session counts"
    )


# Volume trend tracking models
class VolumeTrendModel(BaseModel):
    """Model for tracking volume trends over time."""

    model_config = ConfigDict(from_attributes=True)

    current_period_volume: float = Field(
        description="Volume for current period (week/month)"
    )
    previous_period_volume: float | None = Field(
        None, description="Volume for previous period for comparison"
    )
    percent_change: float | None = Field(
        None, description="Percentage change from previous period"
    )
    average_daily_volume: float | None = Field(
        None, description="Average volume per training day"
    )


class WorkoutHistoryResponseModel(BaseModel):
    """Model for workout history response with enhanced statistics and trends."""

    model_config = ConfigDict(from_attributes=True)

    statistics: WorkoutHistoryStatsModel
    recent_sessions: list[WorkoutSummaryModel] = Field(
        description="Recent workout sessions (latest first)"
    )

    # Training context
    current_training_phase: TrainingPhase | None = Field(
        None, description="Current phase in periodization cycle"
    )
    current_microcycle_position: int | None = Field(
        None, ge=1, le=4, description="Week position within current mesocycle"
    )

    # Volume trends
    volume_trends: dict[str, VolumeTrendModel] = Field(
        default_factory=dict, description="Weekly and monthly volume trends"
    )

    # Effective volume tracking
    effective_volume: float = Field(
        0, description="Total effective volume (working sets only) for period"
    )
    total_volume: float = Field(
        0, description="Total volume including all sets for period"
    )

    filters_applied: dict[str, Any] = Field(
        default_factory=dict, description="Active filters (date range, plan_id, etc.)"
    )


class ExerciseProgressModel(BaseModel):
    """Model for tracking progress on a specific exercise."""

    model_config = ConfigDict(from_attributes=True)

    exercise_id: UUID
    exercise_name: str
    first_performance: datetime = Field(
        description="Date of first recorded performance"
    )
    latest_performance: datetime = Field(description="Date of most recent performance")
    total_sets: int = Field(description="Total sets performed for this exercise")
    total_volume: float = Field(description="Total volume for this exercise")
    max_weight: float = Field(description="Heaviest weight used")
    max_reps: int = Field(description="Maximum reps in a single set")
    avg_weight: float = Field(description="Average weight across all sets")
    avg_reps: float = Field(description="Average reps per set")
    recent_sets: list[SetResponseModel] = Field(
        default_factory=list, description="Last 5 sets performed"
    )
