# Authentication Module

This module implements JWT validation for Supabase authentication tokens using a hybrid caching approach.

## Key Features

- **JWKS Public Key Validation**: Primary method using Supabase's JWKS endpoint
- **Automatic Key Rotation Handling**: Detects and handles Supabase's periodic key rotations
- **TTL-based Caching**: 10-minute cache for JWKS responses to improve performance
- **API Fallback**: Falls back to Supabase API validation if JWKS fails
- **Thread-Safe**: Built-in thread safety from cachetools

## Usage

### Protected Endpoints

```python
from fastapi import Depends
from src.core.auth import UserContext, require_auth

@app.get("/api/v1/profile")
async def get_profile(user: UserContext = Depends(require_auth)):
    return {"user_id": user.user_id, "email": user.email}
```

### Optional Authentication

```python
from src.core.auth import optional_auth

@app.get("/api/v1/public")
async def public_endpoint(user: Optional[UserContext] = Depends(optional_auth)):
    if user:
        return {"message": f"Hello, {user.email}!"}
    return {"message": "Hello, anonymous!"}
```

### MFA-Required Endpoints

```python
from src.core.auth import get_mfa_user

@app.post("/api/v1/sensitive-action")
async def sensitive_action(user: UserContext = Depends(get_mfa_user)):
    # Only users with AAL2 (MFA) can access
    return {"status": "Action completed"}
```

## Configuration

Set the following environment variables:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key

## Security Notes

1. The module validates:
   - JWT signature using public keys
   - Token expiration
   - Issuer (must match your Supabase project)
   - Audience (defaults to "authenticated")
   - Required claims (sub, exp, iat)

2. Key rotation is handled automatically:
   - If a key is not found, JWKS is refreshed once
   - If signature verification fails, JWKS is refreshed once
   - This prevents infinite loops while handling rotations

3. Anonymous users are rejected when `audience="authenticated"`