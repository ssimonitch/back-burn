"""
Tests for plan Pydantic models.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models import (
    PlanCreateModel,
    PlanListResponseModel,
    PlanResponseModel,
    PlanUpdateModel,
    PlanVersionResponseModel,
)


class TestPlanCreateModel:
    """Test PlanCreateModel validation."""

    def test_valid_plan_creation(self):
        """Test creating a valid plan."""
        plan_data = {
            "name": "Upper/Lower Split",
            "description": "A 4-day upper/lower split focusing on compound movements",
            "training_style": "powerlifting",
            "goal": "strength",
            "difficulty_level": "intermediate",
            "duration_weeks": 12,
            "days_per_week": 4,
            "is_public": False,
            "metadata": {"periodization": "linear"},
        }

        plan = PlanCreateModel(**plan_data)

        assert plan.name == "Upper/Lower Split"
        assert plan.training_style == "powerlifting"
        assert plan.difficulty_level == "intermediate"
        assert plan.duration_weeks == 12
        assert plan.days_per_week == 4
        assert plan.is_public is False
        assert plan.metadata == {"periodization": "linear"}

    def test_minimal_plan_creation(self):
        """Test creating a plan with only required fields."""
        plan_data = {
            "name": "Basic Plan",
            "training_style": "general_fitness",
        }

        plan = PlanCreateModel(**plan_data)

        assert plan.name == "Basic Plan"
        assert plan.training_style == "general_fitness"
        assert plan.description is None
        assert plan.goal is None
        assert plan.difficulty_level is None
        assert plan.duration_weeks is None
        assert plan.days_per_week is None
        assert plan.is_public is False
        assert plan.metadata == {}

    def test_invalid_training_style(self):
        """Test validation fails for invalid training style."""
        plan_data = {
            "name": "Invalid Plan",
            "training_style": "invalid_style",
        }

        with pytest.raises(ValidationError) as exc_info:
            PlanCreateModel(**plan_data)

        # Enum validation now shows the allowed values
        assert "powerlifting" in str(exc_info.value)
        assert "bodybuilding" in str(exc_info.value)

    def test_invalid_difficulty_level(self):
        """Test validation fails for invalid difficulty level."""
        plan_data = {
            "name": "Invalid Plan",
            "training_style": "powerlifting",
            "difficulty_level": "expert",
        }

        with pytest.raises(ValidationError) as exc_info:
            PlanCreateModel(**plan_data)

        # Enum validation now shows the allowed values
        assert "beginner" in str(exc_info.value)
        assert "intermediate" in str(exc_info.value)
        assert "advanced" in str(exc_info.value)

    def test_name_validation(self):
        """Test name validation rules."""
        # Empty name should fail
        with pytest.raises(ValidationError):
            PlanCreateModel(name="", training_style="powerlifting")

        # Whitespace-only name should fail
        with pytest.raises(ValidationError):
            PlanCreateModel(name="   ", training_style="powerlifting")

        # Valid name with whitespace should be stripped
        plan = PlanCreateModel(name="  Valid Plan  ", training_style="powerlifting")
        assert plan.name == "Valid Plan"

    def test_duration_weeks_constraints(self):
        """Test duration weeks validation."""
        # Valid duration
        plan = PlanCreateModel(
            name="Test Plan", training_style="powerlifting", duration_weeks=12
        )
        assert plan.duration_weeks == 12

        # Invalid duration (too high)
        with pytest.raises(ValidationError):
            PlanCreateModel(
                name="Test Plan", training_style="powerlifting", duration_weeks=100
            )

        # Invalid duration (zero)
        with pytest.raises(ValidationError):
            PlanCreateModel(
                name="Test Plan", training_style="powerlifting", duration_weeks=0
            )

    def test_days_per_week_constraints(self):
        """Test days per week validation."""
        # Valid days per week
        plan = PlanCreateModel(
            name="Test Plan", training_style="powerlifting", days_per_week=5
        )
        assert plan.days_per_week == 5

        # Invalid days per week (too high)
        with pytest.raises(ValidationError):
            PlanCreateModel(
                name="Test Plan", training_style="powerlifting", days_per_week=8
            )

        # Invalid days per week (zero)
        with pytest.raises(ValidationError):
            PlanCreateModel(
                name="Test Plan", training_style="powerlifting", days_per_week=0
            )


class TestPlanUpdateModel:
    """Test PlanUpdateModel validation."""

    def test_partial_update(self):
        """Test partial update with some fields."""
        update_data = {
            "name": "Updated Plan",
            "difficulty_level": "advanced",
        }

        update = PlanUpdateModel(**update_data)

        assert update.name == "Updated Plan"
        assert update.difficulty_level == "advanced"
        assert update.training_style is None
        assert update.description is None

    def test_empty_update(self):
        """Test update with no fields provided."""
        update = PlanUpdateModel()

        assert update.name is None
        assert update.training_style is None
        assert update.description is None

    def test_validation_rules_apply(self):
        """Test that validation rules still apply to update model."""
        # Invalid training style
        with pytest.raises(ValidationError):
            PlanUpdateModel(training_style="invalid")

        # Invalid difficulty level
        with pytest.raises(ValidationError):
            PlanUpdateModel(difficulty_level="expert")

        # Invalid name
        with pytest.raises(ValidationError):
            PlanUpdateModel(name="   ")


class TestPlanResponseModel:
    """Test PlanResponseModel."""

    def test_complete_response_model(self):
        """Test creating a complete response model."""
        plan_id = uuid4()
        user_id = uuid4()
        parent_id = uuid4()
        now = datetime.now()

        response_data = {
            "id": plan_id,
            "user_id": user_id,
            "name": "Test Plan",
            "description": "Test description",
            "training_style": "powerlifting",
            "goal": "strength",
            "difficulty_level": "intermediate",
            "duration_weeks": 12,
            "days_per_week": 4,
            "is_public": True,
            "metadata": {"test": "data"},
            "version_number": 2,
            "parent_plan_id": parent_id,
            "is_active": True,
            "created_at": now,
        }

        response = PlanResponseModel(**response_data)

        assert response.id == plan_id
        assert response.user_id == user_id
        assert response.name == "Test Plan"
        assert response.version_number == 2
        assert response.parent_plan_id == parent_id
        assert response.is_active is True
        assert response.created_at == now


class TestPlanListResponseModel:
    """Test PlanListResponseModel."""

    def test_plan_list_response(self):
        """Test creating a plan list response."""
        plan_id = uuid4()
        user_id = uuid4()
        now = datetime.now()

        plan_data = {
            "id": plan_id,
            "user_id": user_id,
            "name": "Test Plan",
            "description": None,
            "training_style": "general_fitness",
            "goal": None,
            "difficulty_level": None,
            "duration_weeks": None,
            "days_per_week": None,
            "is_public": False,
            "metadata": {},
            "version_number": 1,
            "parent_plan_id": None,
            "is_active": True,
            "created_at": now,
        }

        list_data = {
            "plans": [plan_data],
            "total_count": 1,
            "page": 1,
            "page_size": 10,
            "has_next": False,
        }

        list_response = PlanListResponseModel(**list_data)

        assert len(list_response.plans) == 1
        assert list_response.total_count == 1
        assert list_response.page == 1
        assert list_response.page_size == 10
        assert list_response.has_next is False


class TestPlanVersionResponseModel:
    """Test PlanVersionResponseModel."""

    def test_version_response(self):
        """Test creating a version response."""
        plan_id = uuid4()
        now = datetime.now()

        version_data = {
            "id": plan_id,
            "version_number": 3,
            "name": "Test Plan v3",
            "is_active": False,
            "created_at": now,
        }

        version = PlanVersionResponseModel(**version_data)

        assert version.id == plan_id
        assert version.version_number == 3
        assert version.name == "Test Plan v3"
        assert version.is_active is False
        assert version.created_at == now
