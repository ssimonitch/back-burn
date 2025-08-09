"""
Plans repository: thin data-access layer wrapping Supabase calls.

Endpoints should depend on the repository via DI rather than calling
Supabase directly. This makes tests and future changes easier.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from supabase import Client


class PlansRepository(Protocol):
    def create(self, user_id: str, payload: dict) -> dict: ...

    def list(
        self, user_id: str, limit: int, offset: int
    ) -> tuple[Sequence[dict], int]: ...

    def get_raw(
        self, plan_id: UUID, *, include_deleted: bool = False
    ) -> dict | None: ...

    def count_active_sessions(self, plan_id: UUID) -> int: ...

    def mark_inactive(self, plan_id: UUID) -> bool: ...

    def set_active(self, plan_id: UUID, active: bool) -> bool: ...

    def insert_plan(self, plan_data: dict) -> dict | None: ...

    def soft_delete_cascade(self, plan_id: UUID, parent_id: UUID) -> bool: ...


class SupabasePlansRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    def create(self, user_id: str, payload: dict) -> dict:
        data = dict(payload)
        data["user_id"] = user_id
        data.setdefault("version_number", 1)
        data.setdefault("is_active", True)
        resp = self.client.table("plans").insert(data).execute()
        if not resp.data:
            raise RuntimeError("Failed to create plan - no data returned")
        return resp.data[0]

    def list(self, user_id: str, limit: int, offset: int) -> tuple[Sequence[dict], int]:
        q = (
            self.client.table("plans")
            .select("*", count="exact")
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        resp = q.execute()
        items = resp.data or []
        total = resp.count or 0
        return items, total

    def get_raw(self, plan_id: UUID, *, include_deleted: bool = False) -> dict | None:
        tbl = self.client.table("plans")
        q = tbl.select("*").eq("id", plan_id)
        if include_deleted:
            resp = q.execute()
        else:
            # Primary path respects soft delete flag; propagate exceptions
            resp = q.is_("deleted_at", "null").execute()
        data = getattr(resp, "data", None)
        # Treat non-list (e.g., MagicMock) or None as empty
        if not isinstance(data, list) or not data:
            return None
        return data[0]

    def count_active_sessions(self, plan_id: UUID) -> int:
        resp = (
            self.client.table("workout_sessions")
            .select("id", count="exact")
            .eq("plan_id", plan_id)
            .is_("completed_at", "null")
            .execute()
        )
        return resp.count or 0

    def mark_inactive(self, plan_id: UUID) -> bool:
        resp = (
            self.client.table("plans")
            .update({"is_active": False})
            .eq("id", plan_id)
            .execute()
        )
        return bool(resp.data)

    def set_active(self, plan_id: UUID, active: bool) -> bool:
        resp = (
            self.client.table("plans")
            .update({"is_active": active})
            .eq("id", plan_id)
            .execute()
        )
        return bool(resp.data)

    def insert_plan(self, plan_data: dict) -> dict | None:
        resp = self.client.table("plans").insert(plan_data).execute()
        if not resp.data:
            return None
        return resp.data[0]

    def soft_delete_cascade(self, plan_id: UUID, parent_id: UUID) -> bool:
        delete_timestamp = datetime.now(UTC).isoformat()
        resp = (
            self.client.table("plans")
            .update({"deleted_at": delete_timestamp})
            .or_(f"id.eq.{plan_id},parent_plan_id.eq.{parent_id}")
            .execute()
        )
        return bool(resp.data)
