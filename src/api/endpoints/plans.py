"""
Plans API endpoints for workout plan management.

This module provides RESTful endpoints for creating, reading, updating,
and managing workout plans. Plans are versioned and immutable - updates
create new versions rather than modifying existing plans.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.auth import JWTPayload, optional_auth, require_auth
from src.core.utils import get_supabase_client
from src.models.plan import (
    PlanCreateModel,
    PlanListResponseModel,
    PlanResponseModel,
)
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

        # TODO: Remove this once training_style column is added to plans table
        # Temporarily remove training_style from the dict as the column doesn't exist yet
        if "training_style" in plan_dict:
            plan_dict.pop("training_style")

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


@router.get(
    "/",
    response_model=PlanListResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Get user's workout plans",
    responses={
        200: {
            "description": "List of plans retrieved successfully",
            "model": PlanListResponseModel,
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
                                "loc": ["query", "limit"],
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
                "application/json": {"example": {"detail": "Failed to retrieve plans"}}
            },
        },
    },
)
async def get_plans(
    limit: int = Query(
        default=20,
        gt=0,
        le=100,
        description="Maximum number of plans to return (1-100)",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of plans to skip for pagination",
    ),
    # TODO: Re-enable once training_style column is added to plans table
    # from src.models.enums import TrainingStyle
    # from typing import Optional
    # training_style: Optional[TrainingStyle] = Query(
    #     default=None,
    #     description="Filter plans by training style",
    # ),
    jwt_payload: JWTPayload = Depends(require_auth),
    supabase: Client = Depends(get_supabase_client),
) -> PlanListResponseModel:
    """
    Retrieve a paginated list of the authenticated user's workout plans.

    Returns a paginated list of plans filtered by the authenticated user's ID (via RLS).
    Plans are sorted by updated_at DESC to show most recently modified plans first.
    If no plans exist for the user, returns an empty array.

    Args:
        limit: Maximum number of plans to return (1-100, default: 20)
        offset: Number of plans to skip for pagination (default: 0)
        jwt_payload: The authenticated user's JWT payload
        supabase: The Supabase client instance

    Returns:
        PlanListResponseModel containing the plans array and pagination metadata

    Raises:
        HTTPException: If plan retrieval fails due to database errors
    """
    try:
        # Build the base query for the user's plans
        # RLS policies ensure we only get plans for the authenticated user
        query = supabase.table("plans").select("*", count="exact")

        # TODO: Re-enable training_style filter once column is added to plans table
        # Apply training style filter if provided
        # if training_style:
        #     query = query.eq("training_style", training_style.value)

        # Apply sorting by created_at DESC (most recent first)
        # Note: Plans are immutable - new versions are created instead of updates
        query = query.order("created_at", desc=True)

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        # Execute the query
        response = query.execute()

        # Extract the plans and total count
        plans = response.data if response.data else []
        total_count = response.count if response.count is not None else 0

        # Calculate pagination metadata
        page = (offset // limit) + 1
        has_next = (offset + limit) < total_count

        # Convert plan data to response models
        plan_models = [PlanResponseModel(**plan) for plan in plans]

        # Return the paginated response
        return PlanListResponseModel(
            plans=plan_models,
            total_count=total_count,
            page=page,
            page_size=limit,
            has_next=has_next,
        )

    except ValueError as ve:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception:
        # Handle unexpected errors
        # Log the error in production
        # logger.error(f"Failed to retrieve plans: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans due to an internal error",
        )


@router.get(
    "/{plan_id}",
    response_model=PlanResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Get a specific workout plan by ID",
    responses={
        200: {
            "description": "Plan retrieved successfully",
            "model": PlanResponseModel,
        },
        404: {
            "description": "Plan not found or access denied",
            "content": {"application/json": {"example": {"detail": "Plan not found"}}},
        },
        422: {
            "description": "Invalid plan ID format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["path", "plan_id"],
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
                "application/json": {"example": {"detail": "Failed to retrieve plan"}}
            },
        },
    },
)
async def get_plan_by_id(
    plan_id: UUID,
    jwt_payload: JWTPayload | None = Depends(optional_auth),
    supabase: Client = Depends(get_supabase_client),
) -> PlanResponseModel:
    """
    Retrieve a specific workout plan by its ID.

    Returns the detailed plan data for the specified plan_id. Access is controlled
    by RLS policies - users can only access their own plans unless the plan is public.
    Public plans (is_public=true) can be viewed by anyone, including unauthenticated users.

    Args:
        plan_id: The UUID of the plan to retrieve
        jwt_payload: Optional JWT payload - required for private plans, optional for public
        supabase: The Supabase client instance

    Returns:
        PlanResponseModel containing the plan details

    Raises:
        HTTPException:
            - 404 if plan doesn't exist or user lacks permission
            - 500 if retrieval fails due to database errors
    """
    try:
        # Build the query for retrieving the plan
        query = supabase.table("plans").select("*").eq("id", plan_id)

        # Execute the query without .single() first to handle no results gracefully
        response = query.execute()

        # Check if we got any data back
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # Get the first (and should be only) plan
        plan = response.data[0]

        # For unauthenticated users, verify the plan is public
        if not jwt_payload and not plan.get("is_public", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # For authenticated users, verify they own the plan or it's public
        if jwt_payload:
            is_owner = str(plan.get("user_id")) == str(jwt_payload.user_id)
            is_public = plan.get("is_public", False)

            if not is_owner and not is_public:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan not found",
                )

        # Return the plan data
        return PlanResponseModel(**plan)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as ve:
        # Handle validation errors (e.g., invalid UUID format)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception:
        # Handle unexpected errors
        # Log the error in production
        # logger.error(f"Failed to retrieve plan {plan_id}: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan due to an internal error",
        )
