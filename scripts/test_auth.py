#!/usr/bin/env python3
"""
Script to create a test user in local Supabase and get an access token.
This is useful for testing authenticated API endpoints.
"""

import json
import os
import sys
from datetime import datetime

import httpx
from pydantic import BaseModel


class AuthResponse(BaseModel):
    """Response from Supabase auth endpoints."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: int | None = None
    refresh_token: str
    user: dict


class SupabaseAuthClient:
    """Simple client for Supabase Auth API."""

    def __init__(self, supabase_url: str, anon_key: str):
        self.base_url = f"{supabase_url}/auth/v1"
        self.anon_key = anon_key
        self.headers = {
            "apikey": anon_key,
            "Content-Type": "application/json",
        }

    def sign_up(self, email: str, password: str) -> AuthResponse | None:
        """Sign up a new user."""
        try:
            response = httpx.post(
                f"{self.base_url}/signup",
                headers=self.headers,
                json={"email": email, "password": password},
            )
            response.raise_for_status()
            data = response.json()

            # Supabase returns the session in the response
            if "access_token" in data:
                return AuthResponse(**data)
            elif "session" in data and data["session"]:
                return AuthResponse(**data["session"])
            else:
                print("✓ User created but email confirmation may be required")
                print(
                    "  Check your email or use sign_in() if email confirmation is disabled"
                )
                return None

        except httpx.HTTPError as e:
            if hasattr(e, "response") and e.response.status_code == 400:
                error_data = e.response.json()
                if "User already registered" in str(error_data):
                    print("ℹ️  User already exists, trying to sign in...")
                    return self.sign_in(email, password)
            print(f"❌ Sign up failed: {e}")
            if hasattr(e, "response"):
                print(f"   Response: {e.response.text}")
            return None

    def sign_in(self, email: str, password: str) -> AuthResponse | None:
        """Sign in an existing user."""
        try:
            response = httpx.post(
                f"{self.base_url}/token?grant_type=password",
                headers=self.headers,
                json={"email": email, "password": password},
            )
            response.raise_for_status()
            data = response.json()
            return AuthResponse(**data)
        except httpx.HTTPError as e:
            print(f"❌ Sign in failed: {e}")
            if hasattr(e, "response"):
                print(f"   Response: {e.response.text}")
            return None

    def get_user(self, access_token: str) -> dict | None:
        """Get user details using access token."""
        try:
            response = httpx.get(
                f"{self.base_url}/user",
                headers={
                    **self.headers,
                    "Authorization": f"Bearer {access_token}",
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"❌ Failed to get user: {e}")
            return None


def test_api_endpoints(base_url: str, access_token: str):
    """Test the FastAPI endpoints with the access token."""
    print("\n🧪 Testing API Endpoints...")

    # Test /api/v1/auth/me (protected)
    print("\n1. Testing /api/v1/auth/me (protected endpoint):")
    try:
        response = httpx.get(
            f"{base_url}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test /api/v1/auth/public with auth
    print("\n2. Testing /api/v1/auth/public (with authentication):")
    try:
        response = httpx.get(
            f"{base_url}/api/v1/auth/public",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test /api/v1/auth/public without auth
    print("\n3. Testing /api/v1/auth/public (without authentication):")
    try:
        response = httpx.get(f"{base_url}/api/v1/auth/public")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test protected endpoint without token
    print("\n4. Testing /api/v1/auth/me without token (should fail):")
    try:
        response = httpx.get(f"{base_url}/api/v1/auth/me")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def main():
    """Main function."""
    # Try to load from settings first, then environment
    try:
        from src.core.settings import settings

        SUPABASE_URL = settings.supabase_url
        SUPABASE_ANON_KEY = settings.supabase_anon_key
    except ImportError:
        # Fallback to environment variables
        SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
        SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

    # Check if required configuration is available
    if not SUPABASE_ANON_KEY:
        print("❌ Error: SUPABASE_ANON_KEY not found in settings or environment")
        print("\n💡 Make sure you have .env.local file with required variables")
        sys.exit(1)

    # Test user credentials (can be overridden via env vars)
    test_email = os.getenv(
        "TEST_EMAIL", f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    )
    test_password = os.getenv("TEST_PASSWORD", "testpassword123")

    print("🚀 Supabase Local Auth Test Script")
    print("=" * 50)
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"FastAPI URL: {FASTAPI_URL}")
    print(f"Test Email: {test_email}")
    print("=" * 50)

    # Initialize client
    client = SupabaseAuthClient(SUPABASE_URL, SUPABASE_ANON_KEY)

    # Try to sign up
    print(f"\n📝 Attempting to sign up user: {test_email}")
    auth_response = client.sign_up(test_email, test_password)

    if not auth_response:
        # If sign up didn't return a session, try to sign in
        print("\n🔑 Attempting to sign in...")
        auth_response = client.sign_in(test_email, test_password)

    if auth_response:
        print("\n✅ Authentication successful!")
        # Only show partial token for security
        token_preview = (
            auth_response.access_token[:20] + "..." + auth_response.access_token[-10:]
        )
        print(f"   Access Token (partial): {token_preview}")
        print(f"   Token Type: {auth_response.token_type}")
        print(f"   Expires In: {auth_response.expires_in} seconds")

        # Get user details
        user = client.get_user(auth_response.access_token)
        if user:
            print("\n👤 User Details:")
            print(f"   ID: {user.get('id')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Role: {user.get('role')}")

        # Test API endpoints
        test_api_endpoints(FASTAPI_URL, auth_response.access_token)

        # Print curl examples
        print("\n📋 Example curl commands:")
        print("\n# Test protected endpoint:")
        print(f"curl -X GET '{FASTAPI_URL}/api/v1/auth/me' \\")
        print("  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'")

        print("\n# Test public endpoint with auth:")
        print(f"curl -X GET '{FASTAPI_URL}/api/v1/auth/public' \\")
        print("  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'")

        # Option to save token to file
        save_token = (
            input("\n💾 Save access token to file for testing? (y/N): ").lower().strip()
        )
        if save_token == "y":
            token_file = "test_token.txt"
            with open(token_file, "w") as f:
                f.write(auth_response.access_token)
            print(f"   ✅ Token saved to {token_file}")
            print(
                f'   📝 Use it with: curl -H "Authorization: Bearer $(cat {token_file})" ...'
            )
            print(f"   🔒 Remember to delete {token_file} when done!")

        print("\n# You can also decode the JWT at: https://jwt.io")
        print(f"\n💡 Token expires in {auth_response.expires_in // 3600} hour(s)")

    else:
        print("\n❌ Authentication failed!")
        print("   Please check that Supabase is running: supabase status")
        sys.exit(1)


if __name__ == "__main__":
    main()
