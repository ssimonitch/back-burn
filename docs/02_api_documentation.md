# Plan API Documentation

This document provides detailed information about the Plan API endpoints in the Slow Burn backend.

When running locally with `uv run poe dev`, these endpoints are available at the above URLs.

## Authentication

All plan endpoints (except GET /plans/{plan_id} for public plans) require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Plan Endpoints

### POST /api/v1/plans

Create a new workout plan.

**Request Body:**
```json
{
  "name": "Upper/Lower Split",
  "description": "A 4-day upper/lower split focusing on compound movements",
  "training_style": "powerlifting",
  "goal": "strength",
  "difficulty_level": "intermediate",
  "duration_weeks": 12,
  "days_per_week": 4,
  "is_public": false,
  "metadata": {
    "periodization": "linear",
    "equipment_needed": ["barbell", "dumbbells", "rack"]
  }
}
```

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Upper/Lower Split",
  "description": "A 4-day upper/lower split focusing on compound movements",
  "training_style": "powerlifting",
  "goal": "strength",
  "difficulty_level": "intermediate",
  "duration_weeks": 12,
  "days_per_week": 4,
  "is_public": false,
  "metadata": {
    "periodization": "linear",
    "equipment_needed": ["barbell", "dumbbells", "rack"]
  },
  "created_at": "2025-02-05T12:00:00Z"
}
```

**Validation Rules:**
- `name`: Required, 1-100 characters
- `training_style`: Required, must be one of: `powerlifting`, `bodybuilding`, `powerbuilding`, `crossfit`, `calisthenics`, `general_fitness`
- `description`: Optional, max 2000 characters
- `goal`: Optional, max 200 characters
- `difficulty_level`: Optional, must be one of: `beginner`, `intermediate`, `advanced`
- `duration_weeks`: Optional, 1-52 weeks
- `days_per_week`: Optional, 1-7 days
- `is_public`: Optional, defaults to false
- `metadata`: Optional, JSON object for additional data

### GET /api/v1/plans

Get a paginated list of the authenticated user's workout plans.

**Query Parameters:**
- `limit`: Number of plans to return (1-100, default: 20)
- `offset`: Number of plans to skip for pagination (default: 0)

**Example Request:**
```
GET /api/v1/plans?limit=10&offset=20
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Upper/Lower Split",
      "description": "A 4-day upper/lower split...",
      "training_style": "powerlifting",
      "goal": "strength",
      "difficulty_level": "intermediate",
      "duration_weeks": 12,
      "days_per_week": 4,
      "is_public": false,
      "metadata": {},
      "created_at": "2025-02-05T12:00:00Z"
    }
  ],
  "total": 25,
  "page": 3,
  "per_page": 10,
  "has_next": true
}
```

### GET /api/v1/plans/{plan_id}

Get a specific workout plan by ID.

**Authentication:** Optional - required for private plans, optional for public plans

**Path Parameters:**
- `plan_id`: UUID of the plan

**Response (200 OK):**
Returns a single plan object (same structure as POST response)

**Error Responses:**
- 404: Plan not found or access denied
- 422: Invalid UUID format

### PUT /api/v1/plans/{plan_id}

Update a workout plan (creates a new version).

**Important:** Plan updates follow an immutable versioning pattern. Updates create a new version while preserving the original.

**Request Body:**
Same fields as POST, but all fields are optional. Only include fields you want to update.

```json
{
  "name": "Updated Upper/Lower Split",
  "difficulty_level": "advanced"
}
```

**Versioning Behavior:**
- Increments `version_number` automatically
- Sets `parent_plan_id` to maintain version history
- Marks current version as inactive (`is_active=false`)
- New version becomes active (`is_active=true`)

**Response (200 OK):**
Returns the newly created version with updated fields.

### DELETE /api/v1/plans/{plan_id}

Soft delete a workout plan.

**Behavior:**
- Sets `deleted_at` timestamp (soft delete)
- Deletes all versions of the plan
- Prevents deletion if plan has active workout sessions

**Response:**
- 204 No Content: Successfully deleted
- 400 Bad Request: Plan has active workout sessions
- 403 Forbidden: User doesn't own the plan
- 404 Not Found: Plan doesn't exist or already deleted

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- 400 Bad Request: Invalid request data or business rule violation
- 401 Unauthorized: Invalid or missing authentication token
- 403 Forbidden: Valid token but insufficient permissions
- 404 Not Found: Resource not found
- 409 Conflict: Resource conflict (e.g., duplicate name)
- 422 Unprocessable Entity: Validation error
- 500 Internal Server Error: Unexpected server error

**Validation Error Response (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "duration_weeks"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

## Business Rules

1. **Plan Ownership**: Users can only access their own plans unless a plan is marked as public
2. **Public Plans**: Can be viewed by anyone (including unauthenticated users)
3. **Versioning**: Updates create new versions; original plans remain unchanged
4. **Soft Delete**: Plans are marked as deleted but remain in the database
5. **Active Sessions**: Plans with active workout sessions cannot be deleted

## Rate Limiting

Currently, no rate limiting is implemented. This will be added in a future sprint.

## Examples

### Creating a Minimal Plan
```bash
curl -X POST http://localhost:8000/api/v1/plans \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Quick Workout",
    "training_style": "general_fitness"
  }'
```

### Getting Plans with Pagination
```bash
curl -X GET "http://localhost:8000/api/v1/plans?limit=5&offset=10" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Updating a Plan
```bash
curl -X PUT http://localhost:8000/api/v1/plans/$PLAN_ID \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Plan Name",
    "is_public": true
  }'
```

### Viewing a Public Plan (No Auth Required)
```bash
curl -X GET http://localhost:8000/api/v1/plans/$PUBLIC_PLAN_ID
```

## SDK Integration

For frontend integration, use the generated TypeScript types from the OpenAPI schema:

```typescript
// Example using openapi-typescript-codegen
import { PlansService } from './generated/services/PlansService';

// Create a plan
const newPlan = await PlansService.createPlan({
  name: "My Plan",
  training_style: "powerlifting"
});

// Get plans with pagination
const plans = await PlansService.getPlans({
  limit: 10,
  offset: 0
});
```

## Postman Collection

A Postman collection with all endpoints and example requests is available at:
`/docs/postman/slow-burn-plans-api.json` (to be created)

## Migration Notes for Frontend Developers

1. All timestamps are in ISO 8601 format with timezone
2. UUIDs are strings in standard format
3. Enums are sent as strings (not integers)
4. Empty arrays and objects are included in responses (not null)
5. Pagination uses `offset/limit` pattern, not cursor-based
