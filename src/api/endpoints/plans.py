"""
Plans API endpoints for workout plan management.

This module provides RESTful endpoints for creating, reading, updating,
and managing workout plans. Plans are versioned and immutable - updates
create new versions rather than modifying existing plans.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.auth import JWTPayload, require_auth
from src.core.utils import get_supabase_client
from src.models.plan import PlanCreateModel, PlanResponseModel
from supabase import Client

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])


@router.post(
    "/",
    response_model=PlanResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workout plan",
    responses={
        201: {
            "description": "Plan created successfully",
            "model": PlanResponseModel,
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Plan name cannot be empty or only whitespace"
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
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "training_style"],
                                "msg": "Invalid training style",
                                "type": "value_error",
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {"example": {"detail": "Failed to create plan"}}
            },
        },
    },
)
async def create_plan(
    plan_data: PlanCreateModel,
    jwt_payload: JWTPayload = Depends(require_auth),
    supabase: Client = Depends(get_supabase_client),
) -> PlanResponseModel:
    """
    Create a new workout plan.

    Creates a new workout plan for the authenticated user with the provided details.
    The plan will be assigned a unique ID and version number 1.

    Args:
        plan_data: The plan creation data
        jwt_payload: The authenticated user's JWT payload
        supabase: The Supabase client instance

    Returns:
        The created plan with all database-generated fields

    Raises:
        HTTPException: If plan creation fails due to validation or database errors
    """
    try:
        # Prepare the plan data for database insertion
        plan_dict = plan_data.model_dump()

        # Add user_id from the JWT payload
        plan_dict["user_id"] = jwt_payload.user_id

        # Ensure version_number is set for new plans
        plan_dict["version_number"] = 1
        plan_dict["is_active"] = True

        # Convert training_style enum to string value if needed
        # (Pydantic with use_enum_values=True should handle this automatically)

        # Insert the plan into the database
        response = supabase.table("plans").insert(plan_dict).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create plan - no data returned",
            )

        # Return the created plan
        created_plan = response.data[0]
        return PlanResponseModel(**created_plan)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as ve:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        # Handle unexpected errors
        error_message = str(e)

        # Check for specific database constraint violations
        if "duplicate key" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A plan with this name and version already exists for this user",
            )
        elif "foreign key violation" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reference in plan data",
            )
        elif "check constraint" in error_message.lower():
            # Extract the specific constraint that failed if possible
            if "difficulty_level" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid difficulty level. Must be one of: beginner, intermediate, advanced",
                )
            elif "duration_weeks" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Duration weeks must be greater than 0",
                )
            elif "days_per_week" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Days per week must be between 1 and 7",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validation error: {error_message}",
                )
        else:
            # Log the error in production
            # logger.error(f"Failed to create plan: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create plan due to an internal error",
            )
