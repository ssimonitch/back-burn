"""
Authentication utility functions.
"""

from src.core.settings import settings
from supabase import Client, create_client


# Supabase client dependency
def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return create_client(settings.supabase_url, settings.supabase_anon_key)
