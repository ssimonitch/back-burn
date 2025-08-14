# API Documentation

This document provides detailed information about the Slow Burn backend API endpoints.

When running locally with `uv run poe dev`, these endpoints are available at `http://localhost:8000`.

## Authentication

All API endpoints (except public endpoints) require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Authentication Model

- Global Bearer auth is required for all endpoints unless explicitly disabled per operation in the OpenAPI schema
- Public endpoints (no auth required): `/`, `/health`, `/api/v1/auth/public`
- Protected endpoints: All plan and workout endpoints require authentication

## Using the OpenAPI Contract

The `openapi.json` at the repo root is the single source of truth for request/response shapes, authentication, and pagination.

### Common Commands

```bash
uv run poe generate-openapi   # Generate schema from code
uv run poe verify-openapi     # Verify schema is current
uv run poe publish-openapi    # Copy schema to ../frontend/openapi.json
```

### Client Generation

You can generate a typed client from the schema. Example (TypeScript):

```bash
npx openapi-typescript-codegen --input ../backend/openapi.json --output src/generated --client axios
```

## Workout Endpoints

### POST /api/v1/workouts

Create a new workout session with associated sets.

**Request Body:**
```json
{
  "plan_id": "123e4567-e89b-12d3-a456-426614174000",  // Optional
  "started_at": "2025-02-13T10:00:00Z",
  "completed_at": "2025-02-13T11:30:00Z",
  "workout_type": "strength",
  "training_phase": "intensification",
  "overall_rpe": 8,
  "notes": "Felt strong today",
  "metadata": {
    "mood_before": 4,
    "mood_after": 5,
    "pre_workout_energy": 7,
    "post_workout_energy": 6,
    "stress_before": 3,
    "stress_after": 2,
    "sleep_quality": 4
  },
  "sets": [
    {
      "exercise_id": "456e7890-e89b-12d3-a456-426614174000",
      "set_number": 1,
      "set_type": "warmup",
      "weight": 135.0,
      "reps": 10,
      "rest_taken_seconds": 120,
      "tempo": "2-0-2-0",
      "form_quality": 5,
      "rpe": 6,
      "reps_in_reserve": 4,
      "notes": "Easy warmup"
    },
    {
      "exercise_id": "456e7890-e89b-12d3-a456-426614174000",
      "set_number": 2,
      "set_type": "working",
      "weight": 225.0,
      "reps": 5,
      "rest_taken_seconds": 180,
      "form_quality": 4,
      "rpe": 8,
      "reps_in_reserve": 2,
      "intensity_percentage": 85,
      "reached_failure": false
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": "789a0123-e89b-12d3-a456-426614174000",
  "user_id": "user_123",
  "plan_id": "123e4567-e89b-12d3-a456-426614174000",
  "started_at": "2025-02-13T10:00:00Z",
  "completed_at": "2025-02-13T11:30:00Z",
  "workout_type": "strength",
  "training_phase": "intensification",
  "overall_rpe": 8,
  "total_sets": 2,
  "total_volume": 2475.0,
  "notes": "Felt strong today",
  "metadata": {...},
  "created_at": "2025-02-13T11:31:00Z",
  "updated_at": "2025-02-13T11:31:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data (empty sets, duplicate set numbers, invalid tempo format)
- `404 Not Found`: Referenced plan not found or deleted
- `422 Unprocessable Entity`: Validation error (invalid UUID, out-of-range values)

### GET /api/v1/workouts

Retrieve a paginated list of workout sessions.

**Query Parameters:**
- `page` (integer, default: 1): Page number (1-indexed)
- `per_page` (integer, default: 20, max: 100): Items per page
- `date_from` (date, optional): Filter workouts from this date
- `date_to` (date, optional): Filter workouts until this date
- `plan_id` (UUID, optional): Filter by plan ID
- `workout_type` (enum, optional): Filter by workout type
- `training_phase` (enum, optional): Filter by training phase

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "789a0123-e89b-12d3-a456-426614174000",
      "plan_id": "123e4567-e89b-12d3-a456-426614174000",
      "plan_name": "Upper/Lower Split",
      "started_at": "2025-02-13T10:00:00Z",
      "completed_at": "2025-02-13T11:30:00Z",
      "workout_type": "strength",
      "training_phase": "intensification",
      "overall_rpe": 8,
      "total_sets": 10,
      "total_volume": 15750.0,
      "effective_volume": 12600.0,
      "working_sets_count": 8,
      "notes": "Felt strong today",
      "created_at": "2025-02-13T11:31:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### GET /api/v1/workouts/{workout_id}

Retrieve detailed workout session with all sets.

**Response (200 OK):**
```json
{
  "id": "789a0123-e89b-12d3-a456-426614174000",
  "user_id": "user_123",
  "plan_id": "123e4567-e89b-12d3-a456-426614174000",
  "plan_name": "Upper/Lower Split",
  "started_at": "2025-02-13T10:00:00Z",
  "completed_at": "2025-02-13T11:30:00Z",
  "workout_type": "strength",
  "training_phase": "intensification",
  "overall_rpe": 8,
  "total_sets": 10,
  "total_volume": 15750.0,
  "notes": "Felt strong today",
  "metadata": {...},
  "metrics": {
    "total_volume": 15750.0,
    "effective_volume": 12600.0,
    "working_sets_ratio": 0.8,
    "average_rpe": 7.5,
    "duration_minutes": 90
  },
  "sets": [
    {
      "id": "set_123",
      "exercise_id": "456e7890-e89b-12d3-a456-426614174000",
      "exercise_name": "Barbell Back Squat",
      "set_number": 1,
      "set_type": "working",
      "weight": 225.0,
      "reps": 5,
      "volume_load": 1125.0,
      "rest_taken_seconds": 180,
      "tempo": "2-0-2-0",
      "form_quality": 4,
      "rpe": 8,
      "reps_in_reserve": 2,
      "intensity_percentage": 85,
      "reached_failure": false,
      "notes": "Good depth"
    }
  ],
  "created_at": "2025-02-13T11:31:00Z",
  "updated_at": "2025-02-13T11:31:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Workout not found or access denied

### DELETE /api/v1/workouts/{workout_id}

Delete a workout session and all associated sets.

**Response (204 No Content):** Success, no body

**Error Responses:**
- `403 Forbidden`: User does not own this workout
- `404 Not Found`: Workout not found

## Plan Endpoints

### POST /api/v1/plans

Create a new workout plan.

**Request Body:**
```json
{
  "name": "Upper/Lower Split",
  "description": "A 4-day upper/lower split focusing on compound movements",
  "training_style": "powerlifting",
  "difficulty_level": "intermediate",
  "duration_weeks": 8,
  "days_per_week": 4,
  "is_public": false,
  "tags": ["strength", "hypertrophy"],
  "metadata": {
    "goal": "Increase squat and bench press",
    "equipment_needed": ["barbell", "dumbbells", "rack"]
  }
}
```

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user_123",
  "name": "Upper/Lower Split",
  "description": "A 4-day upper/lower split focusing on compound movements",
  "training_style": "powerlifting",
  "difficulty_level": "intermediate",
  "duration_weeks": 8,
  "days_per_week": 4,
  "is_public": false,
  "is_active": true,
  "version_number": 1,
  "tags": ["strength", "hypertrophy"],
  "metadata": {...},
  "created_at": "2025-02-13T10:00:00Z",
  "updated_at": "2025-02-13T10:00:00Z"
}
```

### GET /api/v1/plans

Retrieve a paginated list of plans.

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `per_page` (integer, default: 20, max: 100): Items per page
- `training_style` (enum, optional): Filter by training style
- `difficulty_level` (enum, optional): Filter by difficulty
- `days_per_week` (integer, optional): Filter by training frequency
- `include_public` (boolean, default: false): Include public plans from other users

### GET /api/v1/plans/{plan_id}

Retrieve a specific plan by ID.

**Note:** Public plans can be accessed without authentication.

### PUT /api/v1/plans/{plan_id}

Update a plan (creates a new version).

### DELETE /api/v1/plans/{plan_id}

Soft delete a plan.

## Common Response Formats

### Pagination

All list endpoints return paginated responses with this structure:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

### Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200 OK`: Success
- `201 Created`: Resource created successfully
- `204 No Content`: Success with no response body (e.g., DELETE)
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Validation Rules

### Workout Validation
- **Sets**: At least one set required per workout
- **Set Numbers**: Must be unique per exercise_id, starting from 1
- **RPE**: Range 1-10 (Rate of Perceived Exertion)
- **RIR**: Range 0-10 (Reps in Reserve)
- **Form Quality**: Range 1-5 (integer scale)
- **Weight**: Non-negative decimal
- **Reps**: Non-negative integer
- **Tempo**: Format "X-X-X-X" (e.g., "2-0-2-0")
- **Intensity Percentage**: Range 0-200

### Plan Validation
- **Name**: Required, 1-100 characters
- **Duration**: 1-52 weeks
- **Days per Week**: 1-7 days
- **Tags**: Maximum 10 tags

## Enums

### WorkoutType
- `strength`: Heavy lifting, low reps
- `hypertrophy`: Moderate weight, moderate reps
- `power`: Explosive movements
- `endurance`: Light weight, high reps
- `mixed`: Combination of types
- `technique`: Form practice
- `deload`: Recovery week

### TrainingPhase
- `accumulation`: Volume focus
- `intensification`: Intensity focus
- `realization`: Peaking phase
- `deload`: Recovery phase
- `testing`: Max testing phase

### SetType
- `working`: Main working sets
- `warmup`: Warm-up sets
- `backoff`: Reduced weight sets
- `drop`: Drop sets
- `cluster`: Cluster sets
- `rest_pause`: Rest-pause sets
- `amrap`: As Many Reps As Possible

### TrainingStyle
- `powerlifting`: Focus on squat, bench, deadlift
- `bodybuilding`: Aesthetic focus
- `powerbuilding`: Combination of power and aesthetics
- `crossfit`: Varied functional fitness
- `weightlifting`: Olympic lifts
- `general`: General fitness

### DifficultyLevel
- `beginner`: New to training
- `intermediate`: 1-3 years experience
- `advanced`: 3+ years experience
- `elite`: Competitive level

## Rate Limiting

Currently no rate limiting is implemented. This will be added in future versions.

## Versioning

API version is included in the URL path: `/api/v1/`

Breaking changes will increment the version number.