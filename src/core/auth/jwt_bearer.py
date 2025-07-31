"""
JWT Bearer authentication for Supabase tokens.
"""

from typing import Any

import httpx
from cachetools import TTLCache
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwk, jwt


class SupabaseJWTBearer(HTTPBearer):
    """
    Custom JWT Bearer authentication for Supabase tokens.
    Supports both ES256 (JWKS) and HS256 (shared secret) algorithms.
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_anon_key: str,
        jwt_algorithm: str = "ES256",
        jwt_secret: str | None = None,
        auto_error: bool = True,
        verify_exp: bool = True,
        verify_aud: bool = True,
        audience: str = "authenticated",
    ):
        super().__init__(auto_error=auto_error)
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_anon_key = supabase_anon_key
        self.jwt_algorithm = jwt_algorithm
        self.jwt_secret = jwt_secret
        self.jwks_url = f"{self.supabase_url}/auth/v1/.well-known/jwks.json"
        self.verify_exp = verify_exp
        self.verify_aud = verify_aud
        self.audience = audience

        # TTL cache for JWKS - 10 minutes matching Supabase edge cache
        # maxsize=1 because we only cache one JWKS response per project
        self._jwks_cache = TTLCache(maxsize=1, ttl=600)

        # Validate configuration
        if jwt_algorithm == "HS256" and not jwt_secret:
            raise ValueError("JWT_SECRET is required when using HS256 algorithm")
        elif jwt_algorithm in ["ES256", "RS256"] and not supabase_url:
            raise ValueError(
                "SUPABASE_URL is required when using asymmetric algorithms"
            )

    async def __call__(self, request: Request) -> dict[str, Any] | None:  # type: ignore[override]
        credentials = await super().__call__(request)

        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization header missing",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        if credentials.scheme != "Bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        # Validate and decode the JWT
        token_data = await self.verify_jwt(credentials.credentials)

        if not token_data:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        # Add the raw token to the data for later use
        token_data["_raw_token"] = credentials.credentials
        return token_data

    async def get_jwks(self, force_refresh: bool = False) -> dict[str, Any]:
        """
        Get JWKS from cache or fetch if needed.

        Args:
            force_refresh: If True, clear cache and fetch fresh JWKS

        Returns:
            JWKS data from Supabase
        """
        if force_refresh:
            # Clear cache to force a fresh fetch
            self._jwks_cache.clear()

        # Check cache first
        cache_key = "jwks"
        if cache_key in self._jwks_cache and not force_refresh:
            return self._jwks_cache[cache_key]

        # Fetch and cache
        result = await self._fetch_jwks()
        self._jwks_cache[cache_key] = result
        return result

    async def _fetch_jwks(self) -> dict[str, Any]:
        """
        Fetch JWKS from Supabase.

        Returns:
            JWKS data from Supabase

        Raises:
            httpx.HTTPStatusError: If the JWKS endpoint returns an error
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url)
            response.raise_for_status()
            return response.json()

    async def verify_jwt(self, token: str) -> dict[str, Any] | None:
        """
        Verify JWT using algorithm-specific validation.
        Falls back to Supabase API validation if primary method fails.
        """
        try:
            # Get the algorithm from the JWT header
            header = jwt.get_unverified_header(token)
            token_algorithm = header.get("alg")

            if token_algorithm == "HS256" and self.jwt_secret:
                # Use shared secret validation for HS256
                return await self._verify_with_shared_secret(token)
            elif token_algorithm in ["ES256", "RS256"]:
                # Use JWKS validation for asymmetric algorithms
                return await self._verify_with_jwks(token)
            else:
                # Unsupported algorithm or missing configuration
                raise JWTError(
                    f"Unsupported or unconfigured algorithm: {token_algorithm}"
                )
        except Exception:
            # Fallback to API validation
            return await self._verify_with_api(token)

    async def _verify_with_shared_secret(self, token: str) -> dict[str, Any]:
        """
        Verify JWT using shared secret (HS256).

        Args:
            token: JWT token to verify

        Returns:
            Decoded JWT payload

        Raises:
            JWTError: If token validation fails
        """
        if not self.jwt_secret:
            raise JWTError("JWT secret not configured for HS256 validation")

        # Decode and verify the token with shared secret
        options = {
            "verify_signature": True,
            "verify_exp": self.verify_exp,
            "verify_aud": self.verify_aud,
            "require": ["exp", "iat", "sub"],
        }

        payload = jwt.decode(
            token,
            self.jwt_secret,
            algorithms=["HS256"],
            audience=self.audience if self.verify_aud else None,
            options=options,
        )

        # Additional Supabase-specific validations
        self._validate_supabase_claims(payload)

        return payload

    async def _verify_with_jwks(
        self, token: str, retry_on_kid_not_found: bool = True
    ) -> dict[str, Any]:
        """
        Verify JWT using JWKS public keys (ES256/RS256).

        Args:
            token: JWT token to verify
            retry_on_kid_not_found: Whether to retry with fresh JWKS if kid not found

        Returns:
            Decoded JWT payload

        Raises:
            JWTError: If token validation fails
        """
        # Decode header to get kid and algorithm
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        algorithm = header.get("alg")

        if not kid:
            raise JWTError("Token missing kid header")

        # Get JWKS (from cache or fresh)
        jwks_data = await self.get_jwks()

        # Find the key with matching kid
        key_data = None
        for key in jwks_data.get("keys", []):
            if key.get("kid") == kid:
                key_data = key
                break

        if not key_data:
            # Key not found - might be due to key rotation
            if retry_on_kid_not_found:
                # Force refresh JWKS and retry once
                jwks_data = await self.get_jwks(force_refresh=True)

                # Try to find the key again
                for key in jwks_data.get("keys", []):
                    if key.get("kid") == kid:
                        key_data = key
                        break

                if key_data:
                    # Found the key after refresh - continue with validation
                    pass
                else:
                    raise JWTError(
                        f"Unable to find key with kid: {kid} even after refresh"
                    )
            else:
                raise JWTError(f"Unable to find key with kid: {kid}")

        # Construct the public key
        public_key = jwk.construct(key_data)

        # Decode and verify the token
        options = {
            "verify_signature": True,
            "verify_exp": self.verify_exp,
            "verify_aud": self.verify_aud,
            "require": ["exp", "iat", "sub"],
        }

        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[algorithm] if algorithm else ["ES256", "RS256"],
                audience=self.audience if self.verify_aud else None,
                options=options,
            )
        except JWTError as e:
            # If verification fails and we haven't retried yet, it might be a stale key
            if retry_on_kid_not_found and "Signature verification failed" in str(e):
                # Force refresh and retry
                return await self._verify_with_jwks(token, retry_on_kid_not_found=False)
            raise

        # Additional Supabase-specific validations
        self._validate_supabase_claims(payload)

        return payload

    async def _verify_with_api(self, token: str) -> dict[str, Any] | None:
        """Fallback: Verify JWT using Supabase Auth API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": self.supabase_anon_key,
                },
            )

            if response.status_code == 200:
                # Token is valid, decode it without verification
                # since Supabase already validated it
                return jwt.decode(token, options={"verify_signature": False})

            return None

    def _validate_supabase_claims(self, payload: dict[str, Any]) -> None:
        """Validate Supabase-specific JWT claims."""
        # Check issuer
        expected_iss = f"{self.supabase_url}/auth/v1"
        if payload.get("iss") != expected_iss:
            raise JWTError(f"Invalid issuer. Expected: {expected_iss}")

        # Check role
        if payload.get("role") not in ["authenticated", "anon"]:
            raise JWTError("Invalid role claim")

        # Check if user is anonymous when we expect authenticated
        if self.audience == "authenticated" and payload.get("is_anonymous", False):
            raise JWTError("Anonymous users not allowed")
