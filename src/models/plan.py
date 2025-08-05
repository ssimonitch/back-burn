"""
Pydantic models for workout plan operations.

This module defines the data models for creating, updating, and responding
with workout plan data. It enforces validation rules and provides type safety
for plan-related API operations.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .enums import DifficultyLevel, TrainingStyle

# Shared base configuration
base_config = ConfigDict(
    validate_assignment=True,
    extra="forbid",
    use_enum_values=True,
    str_strip_whitespace=True,
)


# Input models
class PlanCreateModel(BaseModel):
    """Model for creating a new workout plan."""

    model_config = base_config

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    training_style: TrainingStyle
    goal: str | None = Field(None, max_length=200)
    difficulty_level: DifficultyLevel | None = None
    duration_weeks: int | None = Field(None, gt=0, le=52)
    days_per_week: int | None = Field(None, ge=1, le=7)
    is_public: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlanUpdateModel(BaseModel):
    """Model for updating an existing workout plan."""

    model_config = base_config

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)
    training_style: TrainingStyle | None = None
    goal: str | None = Field(None, max_length=200)
    difficulty_level: DifficultyLevel | None = None
    duration_weeks: int | None = Field(None, gt=0, le=52)
    days_per_week: int | None = Field(None, ge=1, le=7)
    is_public: bool | None = None
    metadata: dict[str, Any] | None = None


# Response models
class PlanResponseModel(BaseModel):
    """Model for workout plan API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    training_style: str
    goal: str | None
    difficulty_level: str | None
    duration_weeks: int | None
    days_per_week: int | None
    is_public: bool
    metadata: dict[str, Any]
    created_at: datetime


# Generic pagination (can be reused across the app)
class PaginatedResponse[T](BaseModel):
    """Generic paginated response model."""

    items: list[T]
    total: int
    page: int
    per_page: int

    @property
    def has_next(self) -> bool:
        return self.page * self.per_page < self.total


# Type alias for plan pagination
PlanListResponseModel = PaginatedResponse[PlanResponseModel]
