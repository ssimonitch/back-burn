"""
Pydantic models for workout plan operations.

This module defines the data models for creating, updating, and responding
with workout plan data. It enforces validation rules and provides type safety
for plan-related API operations.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .enums import DifficultyLevel, TrainingStyle


class PlanCreateModel(BaseModel):
    """Model for creating a new workout plan."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["Upper/Lower Split", "5/3/1 Beginner", "Push/Pull/Legs"],
    )
    description: str | None = Field(
        None,
        max_length=2000,
        examples=[
            "A 4-day upper/lower split focusing on compound movements",
            "Beginner-friendly powerlifting program based on 5/3/1 methodology",
        ],
    )
    training_style: TrainingStyle = Field(
        ...,
        description="Primary training style/methodology for this plan",
    )
    goal: str | None = Field(
        None,
        max_length=200,
        examples=["strength", "hypertrophy", "weight_loss", "general_fitness", "power"],
    )
    difficulty_level: DifficultyLevel | None = Field(None)
    duration_weeks: int | None = Field(
        None,
        gt=0,
        le=52,
        examples=[4, 8, 12, 16],
    )
    days_per_week: int | None = Field(
        None,
        ge=1,
        le=7,
        examples=[3, 4, 5, 6],
    )
    is_public: bool = Field(
        False, description="Whether this plan can be discovered and used by other users"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional plan configuration like periodization, rest weeks, deload protocols",
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean the plan name."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Plan name cannot be empty or only whitespace")
        return v

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "use_enum_values": True,
        "str_strip_whitespace": True,
    }


class PlanUpdateModel(BaseModel):
    """Model for updating an existing workout plan.

    All fields are optional to support partial updates.
    Note: Updates create new versions rather than modifying existing plans.
    """

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    training_style: TrainingStyle | None = Field(None)
    goal: str | None = Field(None, max_length=200)
    difficulty_level: DifficultyLevel | None = Field(None)
    duration_weeks: int | None = Field(None, gt=0, le=52)
    days_per_week: int | None = Field(None, ge=1, le=7)
    is_public: bool | None = Field(None)
    metadata: dict[str, Any] | None = Field(None)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate and clean the plan name."""
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Plan name cannot be empty or only whitespace")
        return v

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "use_enum_values": True,
        "str_strip_whitespace": True,
    }


class PlanResponseModel(BaseModel):
    """Model for workout plan API responses.

    Represents the complete plan data as stored in the database,
    including system-generated fields like IDs and timestamps.
    """

    id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    # TODO: Make required once training_style column is added to plans table
    training_style: str | None = Field(
        None, description="Primary training style/methodology for this plan"
    )
    goal: str | None = None
    difficulty_level: str | None = None
    duration_weeks: int | None = None
    days_per_week: int | None = None
    is_public: bool = Field(
        ..., description="Whether this plan can be discovered and used by other users"
    )
    metadata: dict[str, Any] = Field(
        ..., description="Additional plan configuration like periodization, rest weeks"
    )
    version_number: int = Field(
        ..., description="Version number for this plan iteration"
    )
    parent_plan_id: UUID | None = Field(
        None, description="References the original plan this version derives from"
    )
    is_active: bool = Field(
        ..., description="Whether this is the current active version of the plan"
    )
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class PlanListResponseModel(BaseModel):
    """Model for paginated plan list responses."""

    plans: list[PlanResponseModel]
    total_count: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    has_next: bool

    model_config = {"validate_assignment": True}


class PlanVersionResponseModel(BaseModel):
    """Model for plan version history responses."""

    id: UUID
    version_number: int = Field(
        ..., description="Version number for this plan iteration"
    )
    name: str
    is_active: bool = Field(
        ..., description="Whether this is the current active version"
    )
    created_at: datetime

    model_config = {"from_attributes": True, "validate_assignment": True}
