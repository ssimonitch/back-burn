# GET /api/v1/plans/{plan_id} - Endpoint Examples

## Overview
This endpoint retrieves a specific workout plan by its unique ID. It supports both authenticated and public access.

## Access Control
- **Authenticated users**: Can access their own plans and any public plans
- **Unauthenticated users**: Can only access public plans (where `is_public=true`)
- Returns 404 for non-existent plans or unauthorized access

## Request Examples

### 1. Get a Private Plan (Authenticated)
```bash
curl -X GET "http://localhost:8000/api/v1/plans/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### 2. Get a Public Plan (No Authentication Required)
```bash
curl -X GET "http://localhost:8000/api/v1/plans/123e4567-e89b-12d3-a456-426614174000"
```

## Response Examples

### Success Response (200 OK)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "987fcdeb-51a2-43d1-9012-345678901234",
  "name": "5/3/1 Beginner",
  "description": "A beginner-friendly powerlifting program based on Jim Wendler's 5/3/1 methodology",
  "training_style": "powerlifting",
  "goal": "strength",
  "difficulty_level": "beginner",
  "duration_weeks": 12,
  "days_per_week": 4,
  "is_public": false,
  "metadata": {
    "periodization": "linear",
    "deload_week": 4,
    "accessories": "BBB"
  },
  "version_number": 1,
  "parent_plan_id": null,
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Error Responses

#### Plan Not Found (404)
```json
{
  "detail": "Plan not found"
}
```

#### Invalid UUID Format (422)
```json
{
  "detail": [
    {
      "loc": ["path", "plan_id"],
      "msg": "value is not a valid uuid",
      "type": "type_error.uuid"
    }
  ]
}
```

#### Internal Server Error (500)
```json
{
  "detail": "Failed to retrieve plan due to an internal error"
}
```

## Usage Notes

1. **Public Plans**: Plans marked as `is_public=true` can be viewed by anyone, making them suitable for sharing workout templates
2. **Private Plans**: Default state for plans (`is_public=false`), only accessible by the owner
3. **UUID Format**: The plan_id must be a valid UUID v4 format
4. **RLS Policies**: Supabase Row Level Security policies automatically enforce access control

## Integration Example

```python
import httpx
from uuid import UUID

async def get_plan_details(plan_id: UUID, auth_token: str = None):
    """Fetch plan details from the API."""
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/v1/plans/{plan_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print("Plan not found or access denied")
        else:
            print(f"Error: {response.json()}")
```