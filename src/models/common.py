"""
Common Pydantic models shared across the application.

This module contains generic, reusable models that can be used
by multiple API endpoints to avoid duplication.
"""

from pydantic import BaseModel


class PaginatedResponse[T](BaseModel):
    """
    Generic paginated response model for list endpoints.

    This model provides a standard structure for paginated API responses,
    including metadata about the current page and total items available.
    """

    items: list[T]
    total: int
    page: int
    per_page: int

    @property
    def has_next(self) -> bool:
        """Check if there are more pages available after the current one."""
        return self.page * self.per_page < self.total
