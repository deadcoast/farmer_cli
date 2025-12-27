"""
Property-based tests for database rollback on failure.

Feature: farmer-cli-completion
Property 11: Database Rollback on Failure
Validates: Requirements 11.2

For any database operation that raises an exception, the database state
SHALL be unchanged from before the operation began.
"""

import string
import uuid
from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st
from sqlalchemy.exc import IntegrityError

from farmer_cli.models.download import DownloadStatus
from farmer_cli.models.download import QueueItem
from farmer_cli.models.history import DownloadHistory
from farmer_cli.models.user import User


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid user names
user_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " -_",
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip())

# Strategy for generating valid URLs
url_strategy = st.uuids().map(lambda u: f"https://example.com/video/{u}")

# Strategy for generating valid output paths
output_path_strategy = st.uuids().map(lambda u: f"/downloads/{u}.mp4")

# Strategy for generating valid titles
title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " -_",
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip())


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def count_users(session) -> int:
    """Count total users in database."""
    return session.query(User).count()


def count_queue_items(session) -> int:
    """Count total queue items in database."""
    return session.query(QueueItem).count()


def count_history_entries(session) -> int:
    """Count total history entries in database."""
    return session.query(DownloadHistory).count()


def get_all_user_names(session) -> set[str]:
    """Get all user names in database."""
    return {user.name for user in session.query(User).all()}


def get_all_queue_urls(session) -> set[str]:
    """Get all queue item URLs in database."""
    return {item.url for item in session.query(QueueItem).all()}


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestDatabaseRollbackOnFailure:
    """
    Property 11: Database Rollback on Failure

    For any database operation that raises an exception, the database state
    SHALL be unchanged from before the operation began.

    **Validates: Requirements 11.2**
    """

    @given(name=user_name_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_user_insert_rollback_on_duplicate(
        self,
        db_session,
        name: str,
    ):
        """
        Feature: farmer-cli-completion, Property 11: Database Rollback on Failure
        Validates: Requirements 11.2

        For any user insert that fails due to duplicate name,
        the database state SHALL be unchanged.
        """
        # Clean up any existing users with this name first
        db_session.query(User).filter(User.name == name).delete()
        db_session.commit()

        # First, add a user with the given name
        user1 = User(name=name, preferences="{}")
        db_session.add(user1)
        db_session.commit()

        # Record state before failed operation
        count_before = count_users(db_session)
        names_before = get_all_user_names(db_session)

        # Attempt to add duplicate user (should fail)
        try:
            user2 = User(name=name, preferences="{}")
            db_session.add(user2)
            db_session.commit()
            # If we get here, the constraint wasn't enforced
            pytest.fail("Expected IntegrityError for duplicate user name")
        except IntegrityError:
            db_session.rollback()

        # Verify state is unchanged
        count_after = count_users(db_session)
        names_after = get_all_user_names(db_session)

        assert count_after == count_before, "User count should be unchanged after rollback"
        assert names_after == names_before, "User names should be unchanged after rollback"

    @given(
        url=url_strategy,
        output_path=output_path_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_queue_item_rollback_on_invalid_status(
        self,
        db_session,
        url: str,
        output_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 11: Database Rollback on Failure
        Validates: Requirements 11.2

        For any queue item operation that fails due to invalid status transition,
        the database state SHALL be unchanged.
        """
        # Create a completed queue item
        item = QueueItem(
            id=str(uuid.uuid4()),
            url=url,
            output_path=output_path,
            status=DownloadStatus.COMPLETED,
            progress=100.0,
            position=1,
        )
        item.created_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        db_session.add(item)
        db_session.commit()

        # Record state before failed operation
        original_status = item.status

        # Attempt invalid status transition (COMPLETED -> DOWNLOADING)
        try:
            item.transition_to(DownloadStatus.DOWNLOADING)
            db_session.commit()
            pytest.fail("Expected ValueError for invalid status transition")
        except ValueError:
            db_session.rollback()

        # Refresh item from database
        db_session.refresh(item)

        # Verify state is unchanged
        assert item.status == original_status, "Status should be unchanged after rollback"

    @given(
        url=url_strategy,
        title=title_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_history_entry_rollback_on_validation_error(
        self,
        db_session,
        url: str,
        title: str,
    ):
        """
        Feature: farmer-cli-completion, Property 11: Database Rollback on Failure
        Validates: Requirements 11.2

        For any history entry operation that fails due to validation error,
        the database state SHALL be unchanged.
        """
        # Add a valid history entry first
        entry = DownloadHistory(
            id=str(uuid.uuid4()),
            url=url,
            title=title,
            file_path="/downloads/test.mp4",
            status="completed",
        )
        entry.downloaded_at = datetime.utcnow()
        entry.created_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()
        db_session.add(entry)
        db_session.commit()

        # Record state before failed operation
        count_before = count_history_entries(db_session)

        # Attempt to add entry with invalid data (empty title)
        try:
            invalid_entry = DownloadHistory(
                id=str(uuid.uuid4()),
                url=url,
                title="",  # Invalid: empty title
                file_path="/downloads/test2.mp4",
                status="completed",
            )
            invalid_entry.downloaded_at = datetime.utcnow()
            invalid_entry.created_at = datetime.utcnow()
            invalid_entry.updated_at = datetime.utcnow()
            db_session.add(invalid_entry)
            db_session.commit()
            pytest.fail("Expected ValueError for empty title")
        except ValueError:
            db_session.rollback()

        # Verify state is unchanged
        count_after = count_history_entries(db_session)
        assert count_after == count_before, "History count should be unchanged after rollback"

    @given(
        name1=user_name_strategy,
        name2=user_name_strategy,
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_batch_operation_rollback(
        self,
        db_session,
        name1: str,
        name2: str,
    ):
        """
        Feature: farmer-cli-completion, Property 11: Database Rollback on Failure
        Validates: Requirements 11.2

        For any batch operation where one item fails,
        all changes in the batch SHALL be rolled back.
        """
        # Ensure names are different
        if name1 == name2:
            name2 = name2 + "_different"

        # Record state before batch operation
        count_before = count_users(db_session)

        # Attempt batch insert where second item will fail
        try:
            # First user (valid)
            user1 = User(name=name1, preferences="{}")
            db_session.add(user1)

            # Second user with same name (will cause failure)
            user2 = User(name=name1, preferences="{}")  # Duplicate!
            db_session.add(user2)

            db_session.commit()
            pytest.fail("Expected IntegrityError for duplicate user name")
        except IntegrityError:
            db_session.rollback()

        # Verify state is unchanged - neither user should be added
        count_after = count_users(db_session)
        assert count_after == count_before, (
            "User count should be unchanged after batch rollback"
        )

    @given(
        url=url_strategy,
        output_path=output_path_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_queue_item_rollback_preserves_other_items(
        self,
        db_session,
        url: str,
        output_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 11: Database Rollback on Failure
        Validates: Requirements 11.2

        For any failed queue operation, existing items SHALL be preserved.
        """
        # Add an existing queue item
        existing_item = QueueItem(
            id=str(uuid.uuid4()),
            url=f"https://example.com/existing/{uuid.uuid4()}",
            output_path=f"/downloads/existing_{uuid.uuid4()}.mp4",
            status=DownloadStatus.PENDING,
            progress=0.0,
            position=1,
        )
        existing_item.created_at = datetime.utcnow()
        existing_item.updated_at = datetime.utcnow()
        db_session.add(existing_item)
        db_session.commit()

        existing_id = existing_item.id
        existing_url = existing_item.url

        # Record state before failed operation
        count_before = count_queue_items(db_session)

        # Attempt to add item with invalid data
        try:
            invalid_item = QueueItem(
                id=str(uuid.uuid4()),
                url="",  # Invalid: empty URL
                output_path=output_path,
                status=DownloadStatus.PENDING,
                progress=0.0,
                position=2,
            )
            invalid_item.created_at = datetime.utcnow()
            invalid_item.updated_at = datetime.utcnow()
            db_session.add(invalid_item)
            db_session.commit()
            pytest.fail("Expected ValueError for empty URL")
        except ValueError:
            db_session.rollback()

        # Verify existing item is preserved
        count_after = count_queue_items(db_session)
        assert count_after == count_before, "Queue count should be unchanged"

        preserved_item = db_session.query(QueueItem).filter(
            QueueItem.id == existing_id
        ).first()
        assert preserved_item is not None, "Existing item should be preserved"
        assert preserved_item.url == existing_url, "Existing item URL should be unchanged"

    @pytest.mark.property
    def test_session_scope_rollback_on_exception(self, database_manager):
        """
        Feature: farmer-cli-completion, Property 11: Database Rollback on Failure
        Validates: Requirements 11.2

        The session_scope context manager SHALL rollback on any exception.
        """
        # Record state before operation
        with database_manager.session_scope() as session:
            count_before = count_users(session)

        # Attempt operation that raises exception
        try:
            with database_manager.session_scope() as session:
                user = User(name=f"test_user_{uuid.uuid4()}", preferences="{}")
                session.add(user)
                # Raise exception before commit
                raise RuntimeError("Simulated failure")
        except RuntimeError:
            pass  # Expected

        # Verify state is unchanged
        with database_manager.session_scope() as session:
            count_after = count_users(session)

        assert count_after == count_before, (
            "User count should be unchanged after session rollback"
        )

    @given(
        url=url_strategy,
        title=title_strategy,
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_update_rollback_on_constraint_violation(
        self,
        db_session,
        url: str,
        title: str,
    ):
        """
        Feature: farmer-cli-completion, Property 11: Database Rollback on Failure
        Validates: Requirements 11.2

        For any update operation that violates constraints,
        the original values SHALL be preserved.
        """
        # Create two users with different names
        name1 = f"user1_{uuid.uuid4()}"
        name2 = f"user2_{uuid.uuid4()}"

        user1 = User(name=name1, preferences="{}")
        user2 = User(name=name2, preferences="{}")
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()

        # Record original state
        original_name = user2.name

        # Attempt to update user2's name to user1's name (duplicate)
        try:
            user2.name = name1  # This should violate unique constraint
            db_session.commit()
            pytest.fail("Expected IntegrityError for duplicate user name")
        except IntegrityError:
            db_session.rollback()

        # Refresh and verify original value is preserved
        db_session.refresh(user2)
        assert user2.name == original_name, "Original name should be preserved after rollback"
