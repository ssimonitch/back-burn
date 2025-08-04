"""
Plans API endpoints for workout plan management.

This module provides RESTful endpoints for creating, reading, updating,
and managing workout plans. Plans are versioned and immutable - updates
create new versions rather than modifying existing plans.
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.auth import JWTPayload, optional_auth, require_auth
from src.core.utils import get_supabase_client
from src.models.plan import (
    PlanCreateModel,
    PlanListResponseModel,
    PlanResponseModel,
    PlanUpdateModel,
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
        # Filter out soft-deleted plans
        query = (
            supabase.table("plans").select("*", count="exact").is_("deleted_at", "null")
        )

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
        # Filter out soft-deleted plans
        query = (
            supabase.table("plans")
            .select("*")
            .eq("id", plan_id)
            .is_("deleted_at", "null")
        )

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


@router.put(
    "/{plan_id}",
    response_model=PlanResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Update a workout plan (creates new version)",
    responses={
        200: {
            "description": "Plan updated successfully (new version created)",
            "model": PlanResponseModel,
        },
        400: {
            "description": "Invalid update request",
            "content": {
                "application/json": {
                    "examples": {
                        "inactive_version": {
                            "summary": "Cannot update inactive version",
                            "value": {
                                "detail": "Cannot update an inactive plan version"
                            },
                        },
                        "no_changes": {
                            "summary": "No changes provided",
                            "value": {
                                "detail": "No changes provided in update request"
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
        403: {
            "description": "User does not own this plan",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to update this plan"
                    }
                }
            },
        },
        404: {
            "description": "Plan not found",
            "content": {"application/json": {"example": {"detail": "Plan not found"}}},
        },
        409: {
            "description": "Version conflict",
            "content": {
                "application/json": {
                    "example": {"detail": "A newer version of this plan already exists"}
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
                                "loc": ["body", "duration_weeks"],
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
                "application/json": {"example": {"detail": "Failed to update plan"}}
            },
        },
    },
)
async def update_plan(
    plan_id: UUID,
    plan_update: PlanUpdateModel,
    jwt_payload: JWTPayload = Depends(require_auth),
    supabase: Client = Depends(get_supabase_client),
) -> PlanResponseModel:
    """
    Update a workout plan by creating a new version.

    Creates a new version of the specified plan with the provided updates.
    The original plan remains unchanged (immutable versioning). Only the plan owner
    can update their plans, and only active versions can be updated.

    Version Management:
    - Increments version_number from the current version
    - Sets parent_plan_id to maintain version history
    - Marks the current version as inactive (is_active=false)
    - Marks the new version as active (is_active=true)

    Args:
        plan_id: The UUID of the plan to update
        plan_update: The partial update data
        jwt_payload: The authenticated user's JWT payload
        supabase: The Supabase client instance

    Returns:
        The newly created plan version with updated fields

    Raises:
        HTTPException:
            - 400 if trying to update an inactive version or no changes provided
            - 403 if user doesn't own the plan
            - 404 if plan doesn't exist
            - 409 if version conflict occurs
            - 500 if update fails due to database errors
    """
    try:
        # Check if any updates were provided
        update_data = plan_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes provided in update request",
            )

        # Retrieve the current plan to verify ownership and status
        # Filter out soft-deleted plans
        query = (
            supabase.table("plans")
            .select("*")
            .eq("id", plan_id)
            .is_("deleted_at", "null")
        )
        response = query.execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        current_plan = response.data[0]

        # Verify the user owns this plan
        if str(current_plan.get("user_id")) != str(jwt_payload.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this plan",
            )

        # Check if this is an active version
        if not current_plan.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update an inactive plan version",
            )

        # Determine the parent_plan_id for version tracking
        # If current plan has no parent, it's the original (v1), so it becomes the parent
        # If current plan has a parent, use that same parent for consistency
        parent_id = current_plan.get("parent_plan_id") or str(plan_id)

        # Create the new version data by merging current plan with updates
        new_version_data = {**current_plan}

        # Apply the updates
        for key, value in update_data.items():
            # Skip training_style temporarily if column doesn't exist yet
            if key == "training_style":
                # TODO: Remove this check once training_style column is added
                continue
            new_version_data[key] = value

        # Set version-specific fields
        new_version_data["id"] = None  # Let database generate new UUID
        new_version_data["version_number"] = current_plan.get("version_number", 1) + 1
        new_version_data["parent_plan_id"] = parent_id
        new_version_data["is_active"] = True
        new_version_data["created_at"] = None  # Let database set timestamp

        # Remove fields that shouldn't be in insert
        new_version_data.pop("id", None)
        new_version_data.pop("created_at", None)

        # Start a transaction-like operation
        # First, mark the current version as inactive
        update_response = (
            supabase.table("plans")
            .update({"is_active": False})
            .eq("id", plan_id)
            .execute()
        )

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update current plan version",
            )

        # TODO: Remove this once training_style column is added
        if "training_style" in new_version_data:
            new_version_data.pop("training_style")

        # Create the new version
        insert_response = supabase.table("plans").insert(new_version_data).execute()

        if not insert_response.data or len(insert_response.data) == 0:
            # Rollback: mark the original as active again
            supabase.table("plans").update({"is_active": True}).eq(
                "id", plan_id
            ).execute()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create new plan version",
            )

        # Return the newly created version
        new_version = insert_response.data[0]
        return PlanResponseModel(**new_version)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as ve:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        # Handle unexpected errors
        error_message = str(e)

        # Check for specific database constraint violations
        if "duplicate key" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A newer version of this plan already exists",
            )
        elif "foreign key violation" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reference in plan update data",
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
            # logger.error(f"Failed to update plan {plan_id}: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update plan due to an internal error",
            )


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a workout plan",
    responses={
        204: {
            "description": "Plan deleted successfully",
        },
        400: {
            "description": "Cannot delete plan with active workout sessions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete plan - it has active workout sessions"
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
        403: {
            "description": "User does not own this plan",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to delete this plan"
                    }
                }
            },
        },
        404: {
            "description": "Plan not found or already deleted",
            "content": {"application/json": {"example": {"detail": "Plan not found"}}},
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {"example": {"detail": "Failed to delete plan"}}
            },
        },
    },
)
async def delete_plan(
    plan_id: UUID,
    jwt_payload: JWTPayload = Depends(require_auth),
    supabase: Client = Depends(get_supabase_client),
) -> None:
    """
    Soft delete a workout plan.

    Performs a soft delete by setting the deleted_at timestamp. Only the plan owner
    can delete their plans. Plans with active workout sessions cannot be deleted.
    The plan and all its versions will be marked as deleted.

    Args:
        plan_id: The UUID of the plan to delete
        jwt_payload: The authenticated user's JWT payload
        supabase: The Supabase client instance

    Returns:
        None (204 No Content on success)

    Raises:
        HTTPException:
            - 400 if plan has active workout sessions
            - 403 if user doesn't own the plan
            - 404 if plan doesn't exist or is already deleted
            - 500 if deletion fails due to database errors
    """
    try:
        # Retrieve the plan to verify ownership and check if already deleted
        query = supabase.table("plans").select("*").eq("id", plan_id)
        response = query.execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        plan = response.data[0]

        # Check if plan is already deleted
        if plan.get("deleted_at") is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # Verify the user owns this plan
        if str(plan.get("user_id")) != str(jwt_payload.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this plan",
            )

        # Check for active workout sessions using this plan
        # We check for sessions that reference this plan and are not completed
        # (completed_at is NULL means the session is ongoing/active)
        sessions_query = (
            supabase.table("workout_sessions")
            .select("id", count="exact")
            .eq("plan_id", plan_id)
            .is_("completed_at", "null")
        )
        sessions_response = sessions_query.execute()

        active_sessions_count = (
            sessions_response.count if sessions_response.count is not None else 0
        )

        if active_sessions_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete plan - it has active workout sessions",
            )

        # Determine the parent_plan_id to delete all versions
        # If this plan has a parent, use that parent ID
        # If this plan has no parent, it IS the parent, so use its own ID
        parent_id = plan.get("parent_plan_id") or str(plan_id)

        # Perform the soft delete by setting deleted_at timestamp
        # Delete the specific plan and all its versions
        delete_timestamp = datetime.now(UTC).isoformat()

        # Delete all versions of this plan (including the parent)
        # We delete where id matches OR parent_plan_id matches
        delete_response = (
            supabase.table("plans")
            .update({"deleted_at": delete_timestamp})
            .or_(f"id.eq.{plan_id},parent_plan_id.eq.{parent_id}")
            .execute()
        )

        if not delete_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete plan",
            )

        # Return 204 No Content on successful deletion
        return None

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception:
        # Handle unexpected errors
        # Log the error in production
        # logger.error(f"Failed to delete plan {plan_id}: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete plan due to an internal error",
        )
