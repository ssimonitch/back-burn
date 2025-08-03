# Plans API Endpoints

## Overview

The Plans API provides endpoints for managing workout plans in the Slow Burn fitness application. Plans are versioned and immutable - updates create new versions rather than modifying existing plans.

## Endpoints

### POST /api/v1/plans
Create a new workout plan for the authenticated user.

**Authentication:** Required (JWT Bearer token)

**Request Body:**
```json
{
  "name": "Upper/Lower Split",
  "description": "A 4-day upper/lower split focusing on compound movements",
  "training_style": "powerbuilding",  // Note: Currently disabled until DB column is added
  "goal": "strength",
  "difficulty_level": "intermediate",
  "duration_weeks": 8,
  "days_per_week": 4,
  "is_public": false,
  "metadata": {
    "periodization": "linear",
    "deload_week": 4
  }
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Upper/Lower Split",
  "description": "A 4-day upper/lower split focusing on compound movements",
  "training_style": null,  // Will be populated once DB column is added
  "goal": "strength",
  "difficulty_level": "intermediate",
  "duration_weeks": 8,
  "days_per_week": 4,
  "is_public": false,
  "metadata": {
    "periodization": "linear",
    "deload_week": 4
  },
  "version_number": 1,
  "parent_plan_id": null,
  "is_active": true,
  "created_at": "2025-08-03T22:00:00Z"
}
```

### GET /api/v1/plans
Retrieve a paginated list of the authenticated user's workout plans.

**Authentication:** Required (JWT Bearer token)

**Query Parameters:**
- `limit` (integer, 1-100, default: 20): Maximum number of plans to return
- `offset` (integer, ≥0, default: 0): Number of plans to skip for pagination
- `training_style` (string, optional): Filter by training style (currently disabled)

**Response (200 OK):**
```json
{
  "plans": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Upper/Lower Split",
      "description": "A 4-day upper/lower split focusing on compound movements",
      "training_style": null,
      "goal": "strength",
      "difficulty_level": "intermediate",
      "duration_weeks": 8,
      "days_per_week": 4,
      "is_public": false,
      "metadata": {},
      "version_number": 1,
      "parent_plan_id": null,
      "is_active": true,
      "created_at": "2025-08-03T22:00:00Z"
    }
  ],
  "total_count": 5,
  "page": 1,
  "page_size": 20,
  "has_next": false
}
```

## Implementation Notes

### Current Limitations
1. **Training Style Column Missing**: The `training_style` field is defined in the API models but the database column doesn't exist yet. A migration has been created (`20250803220000_add_training_style_to_plans.sql`) to add this column.

2. **Temporary Workarounds**:
   - The `training_style` field is made optional in `PlanResponseModel`
   - The POST endpoint removes `training_style` from the data before inserting
   - The GET endpoint's `training_style` filter parameter is commented out

### To Enable Full Functionality
1. Run the migration to add the `training_style` column:
   ```bash
   supabase db reset  # For local development
   # OR
   supabase db push  # For production
   ```

2. Uncomment the following in `/src/api/endpoints/plans.py`:
   - Import statements for `Optional` and `TrainingStyle`
   - The `training_style` query parameter in `get_plans()`
   - The training style filter logic in the query builder
   - Remove the `pop("training_style")` line in `create_plan()`

3. Update `/src/models/plan.py`:
   - Make `training_style` required in `PlanResponseModel`

## Error Responses

All endpoints may return the following error responses:

- **401 Unauthorized**: Missing or invalid JWT token
- **422 Unprocessable Entity**: Invalid request data
- **500 Internal Server Error**: Database or server error

## Database Schema

The plans table uses Row Level Security (RLS) to ensure users can only access their own plans (unless marked as public). Plans are versioned, with `version_number` incrementing for each modification and `parent_plan_id` linking to the original plan.