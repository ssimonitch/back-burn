"""
Application settings configuration using pydantic-settings.
"""

import os
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


class AppEnvironment(StrEnum):
    development = "development"
    shadow = "shadow"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    app_env: AppEnvironment = Field(..., description="Environment name")

    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous key")
    supabase_service_key: str | None = Field(
        None, description="Supabase service key for admin operations"
    )

    # Google Gemini Configuration
    google_api_key: str | None = Field(None, description="Google API key for Gemini")

    # API Configuration
    api_host: str = Field("localhost", description="API host")
    api_port: int = Field(8000, description="API port")
    frontend_url: str = Field(
        "http://localhost:3000", description="Frontend URL for CORS"
    )

    # Security Configuration
    jwt_algorithm: str = Field(
        "ES256", description="JWT algorithm (ES256 for production, HS256 for local)"
    )
    jwt_secret: str | None = Field(
        None, description="JWT secret for HS256 algorithm (local development)"
    )
    jwt_audience: str = Field("authenticated", description="JWT audience")

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnvironment.production


class AppEnvSetting(BaseSettings):
    """Internal settings class intended to bootstrap the .env file loading with validation."""

    app_env: AppEnvironment = AppEnvironment.development


@lru_cache
def get_settings() -> Settings:
    stage = AppEnvSetting().app_env

    root = Path(__file__).parent.parent.parent
    env_files = [
        str(root / file)
        for file in [
            f".env.{stage}.secrets.local",
            f".env.{stage}.local",
            f".env.{stage}",
            ".env.local",
            ".env",
        ]
    ]

    for env_file in filter(os.path.exists, env_files):
        load_dotenv(env_file)

    return Settings()


settings = get_settings()
