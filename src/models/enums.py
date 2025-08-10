"""
Enumerations for model field validation.

This module defines strongly-typed enums for categorical fields,
providing type safety and automatic validation in Pydantic models.
"""

from enum import StrEnum


class TrainingStyle(StrEnum):
    """Training styles matching the database training_styles reference table.

    These values are seeded in the database and should remain synchronized
    with supabase/seeds/01_reference_seed.sql.
    """

    POWERLIFTING = "powerlifting"
    BODYBUILDING = "bodybuilding"
    POWERBUILDING = "powerbuilding"
    GENERAL_FITNESS = "general_fitness"
    ATHLETIC_PERFORMANCE = "athletic_performance"


class DifficultyLevel(StrEnum):
    """Workout plan difficulty levels.

    Used to categorize plans by required experience and fitness level.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class MoodRating(StrEnum):
    """Mood rating scale for wellness tracking.

    Used before and after workout sessions.
    """

    VERY_BAD = "very_bad"
    BAD = "bad"
    NEUTRAL = "neutral"
    GOOD = "good"
    VERY_GOOD = "very_good"


class WellnessRating(StrEnum):
    """General wellness rating scale.

    Used for energy, stress, and sleep quality tracking.
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FormQuality(StrEnum):
    """Form quality rating for exercise execution.

    Tracks technique quality during sets.
    """

    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class WorkoutType(StrEnum):
    """Workout type categorizing the primary training stimulus.

    Used to track the focus of each workout session for periodization.
    """

    STRENGTH = "strength"
    HYPERTROPHY = "hypertrophy"
    POWER = "power"
    ENDURANCE = "endurance"
    MIXED = "mixed"
    TECHNIQUE = "technique"
    DELOAD = "deload"


class TrainingPhase(StrEnum):
    """Training phase within a periodization cycle.

    Tracks the current phase for proper progression and volume management.
    """

    ACCUMULATION = "accumulation"
    INTENSIFICATION = "intensification"
    REALIZATION = "realization"
    DELOAD = "deload"
    TESTING = "testing"


class SetType(StrEnum):
    """Set classification for volume calculations.

    Critical for accurate volume tracking and progressive overload.
    Only 'working' sets count toward effective training volume.
    """

    WORKING = "working"
    WARMUP = "warmup"
    BACKOFF = "backoff"
    DROP = "drop"
    CLUSTER = "cluster"
    REST_PAUSE = "rest_pause"
    AMRAP = "amrap"


class FailureType(StrEnum):
    """Type of failure reached during set execution.

    Helps differentiate between true muscular failure and other limiting factors.
    """

    MUSCULAR = "muscular"
    FORM = "form"
    CARDIOVASCULAR = "cardiovascular"
    MOTIVATION = "motivation"


class RangeOfMotionQuality(StrEnum):
    """Range of motion quality assessment.

    Tracks movement quality and mobility improvements over time.
    """

    FULL = "full"
    PARTIAL = "partial"
    LIMITED = "limited"
    ASSISTED = "assisted"


class AssistanceType(StrEnum):
    """Type of assistance used during set execution.

    Documents when external help or equipment assistance was used.
    """

    NONE = "none"
    SPOTTER = "spotter"
    MACHINE_ASSIST = "machine_assist"
    BAND_ASSIST = "band_assist"
