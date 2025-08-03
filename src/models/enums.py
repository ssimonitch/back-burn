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
