"""Dependency injection providers for repositories and services."""

from fastapi import Depends

from src.core.utils import get_supabase_client
from src.repositories.plans import PlansRepository, SupabasePlansRepository
from src.repositories.workouts import SupabaseWorkoutsRepository, WorkoutsRepository


def get_plans_repository(
    client=Depends(get_supabase_client),
) -> PlansRepository:
    return SupabasePlansRepository(client)


def get_workouts_repository(
    client=Depends(get_supabase_client),
) -> WorkoutsRepository:
    return SupabaseWorkoutsRepository(client)
