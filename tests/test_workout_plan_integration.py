"""Integration tests for workout-plan access logic."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.repositories.workouts import SupabaseWorkoutsRepository


class TestPlanAccessVerification:
    """Test cases for verifying plan access logic with various scenarios."""

    @pytest.fixture
    def repo(self, mock_supabase_client):
        """Create a repository instance with mocked client."""
        return SupabaseWorkoutsRepository(mock_supabase_client)

    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mock Supabase client."""
        return Mock()

    def test_deleted_public_plan_not_accessible(self, repo, mock_supabase_client):
        """Verify that a deleted public plan cannot be accessed by anyone."""
        # Arrange
        plan_id = uuid4()
        other_user_id = str(uuid4())  # Testing as non-owner

        # Mock response - deleted public plan
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.or_.return_value.execute.return_value.data = []

        # Act - Try to access as different user
        result = repo.verify_plan_access(plan_id, other_user_id)

        # Assert - Should not be accessible
        assert result is False

        # Verify the query was constructed correctly
        mock_supabase_client.table.assert_called_with("plans")
        mock_supabase_client.table.return_value.select.assert_called_with("id")
        mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with(
            "id", str(plan_id)
        )
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.assert_called_with(
            "deleted_at", "null"
        )

    def test_public_plan_accessible_to_non_owner(self, repo, mock_supabase_client):
        """Verify that a public plan can be accessed by users who don't own it."""
        # Arrange
        plan_id = uuid4()
        other_user_id = str(uuid4())  # Non-owner accessing public plan

        # Mock response - public plan exists and is not deleted
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.or_.return_value.execute.return_value.data = [
            {"id": str(plan_id)}
        ]

        # Act - Access as different user
        result = repo.verify_plan_access(plan_id, other_user_id)

        # Assert - Should be accessible
        assert result is True

        # Verify OR clause includes both user_id and is_public checks
        or_call = mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.or_.call_args
        assert f"user_id.eq.{other_user_id}" in or_call[0][0]
        assert "is_public.eq.true" in or_call[0][0]

    def test_private_plan_only_accessible_to_owner(self, repo, mock_supabase_client):
        """Verify that a private plan can only be accessed by its owner."""
        # Arrange
        plan_id = uuid4()
        owner_id = str(uuid4())
        other_user_id = str(uuid4())

        # Test 1: Owner can access their private plan
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.or_.return_value.execute.return_value.data = [
            {"id": str(plan_id)}
        ]

        result_owner = repo.verify_plan_access(plan_id, owner_id)
        assert result_owner is True

        # Test 2: Non-owner cannot access private plan
        # Mock empty response for non-owner
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.or_.return_value.execute.return_value.data = []

        result_other = repo.verify_plan_access(plan_id, other_user_id)
        assert result_other is False

    def test_deleted_private_plan_not_accessible_to_owner(
        self, repo, mock_supabase_client
    ):
        """Verify that a deleted private plan cannot be accessed even by owner."""
        # Arrange
        plan_id = uuid4()
        owner_id = str(uuid4())

        # Mock response - no results (plan is deleted)
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.or_.return_value.execute.return_value.data = []

        # Act - Try to access as owner
        result = repo.verify_plan_access(plan_id, owner_id)

        # Assert - Should not be accessible even to owner
        assert result is False

        # Verify deleted_at check is applied
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.assert_called_with(
            "deleted_at", "null"
        )

    def test_nonexistent_plan_not_accessible(self, repo, mock_supabase_client):
        """Verify that a non-existent plan cannot be accessed."""
        # Arrange
        plan_id = uuid4()
        user_id = str(uuid4())

        # Mock response - empty (plan doesn't exist)
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.is_.return_value.or_.return_value.execute.return_value.data = []

        # Act
        result = repo.verify_plan_access(plan_id, user_id)

        # Assert
        assert result is False

    def test_plan_access_query_structure(self, repo, mock_supabase_client):
        """Verify the complete query structure for plan access."""
        # Arrange
        plan_id = uuid4()
        user_id = str(uuid4())

        # Mock the chain to track all calls
        mock_chain = Mock()
        mock_supabase_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.is_.return_value = mock_chain
        mock_chain.or_.return_value = mock_chain
        mock_chain.execute.return_value.data = [{"id": str(plan_id)}]

        # Act
        result = repo.verify_plan_access(plan_id, user_id)

        # Assert - Verify the complete chain of calls
        assert result is True

        # Check each part of the query
        mock_supabase_client.table.assert_called_once_with("plans")
        mock_chain.select.assert_called_once_with("id")
        mock_chain.eq.assert_called_once_with("id", str(plan_id))
        mock_chain.is_.assert_called_once_with("deleted_at", "null")

        # Check the OR clause structure
        or_call = mock_chain.or_.call_args[0][0]
        assert f"user_id.eq.{user_id}" in or_call
        assert "is_public.eq.true" in or_call
        assert "," in or_call  # Comma separator between conditions
