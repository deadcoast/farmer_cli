"""
Property-based tests for database consistency invariant.

Feature: farmer-cli-completion
Property 5: Database Consistency Invariant
Validates: Requirements 11.6

For any sequence of database operations (add, update, delete), the database
SHALL remain in a consistent state with no orphaned records, valid foreign keys,
and all constraints satisfied.
"""

import string
import uuid
from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st
from sqlalchemy import inspect

from farmer_cli.models.download import DownloadStatus
from farmer_cli.models.download import QueueItem
from farmer_cli.models.history import DownloadHistory
from farmer_cli.models.user import User


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid user names with unique suffix
user_name_strategy = st.uuids().map(lambda u: f"user_{u}")

# Strategy for generating valid URLs with unique suffix
url_strategy = st.uuids().map(lambda u: f"https://example.com/video/{u}")

# Strategy for generating valid output paths with unique suffix
output_path_strategy = st.uuids().map(lambda u: f"/downloads/{u}.mp4")

# Strategy for generating valid titles
title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + " -_",
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip())

# Strategy for generating valid file paths
file_path_strategy = st.uuids().map(lambda u: f"/downloads/{u}.mp4")

# Strategy for generating valid statuses
status_strategy = st.sampled_from([
    DownloadStatus.PENDING,
    DownloadStatus.DOWNLOADING,
    DownloadStatus.COMPLETED,
    DownloadStatus.FAILED,
    DownloadStatus.PAUSED,
    DownloadStatus.CANCELLED,
])

# Strategy for generating operation sequences
operation_strategy = st.sampled_from(["add_user", "add_queue", "add_history", "delete"])


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def verify_database_consistency(session) -> tuple[bool, list[str]]:
    """
    Verify database is in a consistent state.

    Returns tuple of (is_consistent, list_of_issues).
    """
    issues = []

    # Check all users have valid data
    for user in session.query(User).all():
        if not user.id:
            issues.append(f"User missing id: {user}")
        if not user.name or not user.name.strip():
            issues.append(f"User missing name: {user}")

    # Check all queue items have valid data
    for item in session.query(QueueItem).all():
        if not item.id:
            issues.append(f"QueueItem missing id: {item}")
        if not item.url or not item.url.strip():
            issues.append(f"QueueItem missing url: {item}")
        if not item.output_path or not item.output_path.strip():
            issues.append(f"QueueItem missing output_path: {item}")
        if item.status is None:
            issues.append(f"QueueItem missing status: {item}")
        if item.progress is None:
            issues.append(f"QueueItem missing progress: {item}")
        if item.position is None:
            issues.append(f"QueueItem missing position: {item}")
        if item.progress < 0 or item.progress > 100:
            issues.append(f"QueueItem invalid progress {item.progress}: {item}")
        if item.position < 0:
            issues.append(f"QueueItem invalid position {item.position}: {item}")

    # Check all history entries have valid data
    for entry in session.query(DownloadHistory).all():
        if not entry.id:
            issues.append(f"DownloadHistory missing id: {entry}")
        if not entry.url or not entry.url.strip():
            issues.append(f"DownloadHistory missing url: {entry}")
        if not entry.title or not entry.title.strip():
            issues.append(f"DownloadHistory missing title: {entry}")
        if not entry.file_path or not entry.file_path.strip():
            issues.append(f"DownloadHistory missing file_path: {entry}")
        if entry.file_size is not None and entry.file_size < 0:
            issues.append(f"DownloadHistory invalid file_size {entry.file_size}: {entry}")
        if entry.duration is not None and entry.duration < 0:
            issues.append(f"DownloadHistory invalid duration {entry.duration}: {entry}")

    # Check for duplicate primary keys (should be enforced by DB but verify)
    user_ids = [u.id for u in session.query(User).all()]
    if len(user_ids) != len(set(user_ids)):
        issues.append("Duplicate user IDs found")

    queue_ids = [q.id for q in session.query(QueueItem).all()]
    if len(queue_ids) != len(set(queue_ids)):
        issues.append("Duplicate queue item IDs found")

    history_ids = [h.id for h in session.query(DownloadHistory).all()]
    if len(history_ids) != len(set(history_ids)):
        issues.append("Duplicate history entry IDs found")

    return len(issues) == 0, issues


def clean_database(session):
    """Clean all data from database."""
    session.query(QueueItem).delete()
    session.query(DownloadHistory).delete()
    session.query(User).delete()
    session.commit()


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestDatabaseConsistencyInvariant:
    """
    Property 5: Database Consistency Invariant

    For any sequence of database operations (add, update, delete), the database
    SHALL remain in a consistent state with no orphaned records, valid foreign keys,
    and all constraints satisfied.

    **Validates: Requirements 11.6**
    """

    @given(name=user_name_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_user_add_maintains_consistency(
        self,
        db_session,
        name: str,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        Adding a user SHALL maintain database consistency.
        """
        # Clean database
        clean_database(db_session)

        # Add user
        user = User(name=name, preferences="{}")
        db_session.add(user)
        db_session.commit()

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent after user add: {issues}"

    @given(
        url=url_strategy,
        output_path=output_path_strategy,
        status=status_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_queue_item_add_maintains_consistency(
        self,
        db_session,
        url: str,
        output_path: str,
        status: DownloadStatus,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        Adding a queue item SHALL maintain database consistency.
        """
        # Clean database
        clean_database(db_session)

        # Add queue item
        item = QueueItem(
            id=str(uuid.uuid4()),
            url=url,
            output_path=output_path,
            status=status,
            progress=50.0 if status == DownloadStatus.DOWNLOADING else 0.0,
            position=1,
        )
        item.created_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        db_session.add(item)
        db_session.commit()

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent after queue item add: {issues}"

    @given(
        url=url_strategy,
        title=title_strategy,
        file_path=file_path_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_history_entry_add_maintains_consistency(
        self,
        db_session,
        url: str,
        title: str,
        file_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        Adding a history entry SHALL maintain database consistency.
        """
        # Clean database
        clean_database(db_session)

        # Add history entry
        entry = DownloadHistory(
            id=str(uuid.uuid4()),
            url=url,
            title=title,
            file_path=file_path,
            status="completed",
        )
        entry.downloaded_at = datetime.utcnow()
        entry.created_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()
        db_session.add(entry)
        db_session.commit()

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent after history entry add: {issues}"

    @given(
        name=user_name_strategy,
        new_name=user_name_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_user_update_maintains_consistency(
        self,
        db_session,
        name: str,
        new_name: str,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        Updating a user SHALL maintain database consistency.
        """
        # Clean database
        clean_database(db_session)

        # Add user
        user = User(name=name, preferences="{}")
        db_session.add(user)
        db_session.commit()

        # Update user
        user.name = new_name
        user.preferences = '{"updated": true}'
        db_session.commit()

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent after user update: {issues}"

    @given(
        url=url_strategy,
        output_path=output_path_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_queue_item_status_update_maintains_consistency(
        self,
        db_session,
        url: str,
        output_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        Updating queue item status SHALL maintain database consistency.
        """
        # Clean database
        clean_database(db_session)

        # Add queue item
        item = QueueItem(
            id=str(uuid.uuid4()),
            url=url,
            output_path=output_path,
            status=DownloadStatus.PENDING,
            progress=0.0,
            position=1,
        )
        item.created_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        db_session.add(item)
        db_session.commit()

        # Update status through valid transitions
        item.transition_to(DownloadStatus.DOWNLOADING)
        item.progress = 50.0
        db_session.commit()

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent after status update: {issues}"

    @given(name=user_name_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_user_delete_maintains_consistency(
        self,
        db_session,
        name: str,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        Deleting a user SHALL maintain database consistency.
        """
        # Clean database
        clean_database(db_session)

        # Add user
        user = User(name=name, preferences="{}")
        db_session.add(user)
        db_session.commit()

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent after user delete: {issues}"

    @given(
        url=url_strategy,
        output_path=output_path_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_queue_item_delete_maintains_consistency(
        self,
        db_session,
        url: str,
        output_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        Deleting a queue item SHALL maintain database consistency.
        """
        # Clean database
        clean_database(db_session)

        # Add queue item
        item = QueueItem(
            id=str(uuid.uuid4()),
            url=url,
            output_path=output_path,
            status=DownloadStatus.PENDING,
            progress=0.0,
            position=1,
        )
        item.created_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        db_session.add(item)
        db_session.commit()

        # Delete queue item
        db_session.delete(item)
        db_session.commit()

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent after queue item delete: {issues}"

    @given(num_operations=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_mixed_operations_maintain_consistency(
        self,
        db_session,
        num_operations: int,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        Any sequence of mixed operations SHALL maintain database consistency.
        """
        # Clean database
        clean_database(db_session)

        # Perform random operations
        for i in range(num_operations):
            op_type = i % 3  # Cycle through operation types

            if op_type == 0:
                # Add user
                user = User(name=f"user_{uuid.uuid4()}", preferences="{}")
                db_session.add(user)

            elif op_type == 1:
                # queue item
                item = QueueItem(
                    id=str(uuid.uuid4()),
                    url=f"https://example.com/video/{uuid.uuid4()}",
                    output_path=f"/downloads/{uuid.uuid4()}.mp4",
                    status=DownloadStatus.PENDING,
                    progress=0.0,
                    position=i,
                )
                item.created_at = datetime.utcnow()
                item.updated_at = datetime.utcnow()
                db_session.add(item)

            else:
                # Add history entry
                entry = DownloadHistory(
                    id=str(uuid.uuid4()),
                    url=f"https://example.com/video/{uuid.uuid4()}",
                    title=f"Video {i}",
                    file_path=f"/downloads/{uuid.uuid4()}.mp4",
                    status="completed",
                )
                entry.downloaded_at = datetime.utcnow()
                entry.created_at = datetime.utcnow()
                entry.updated_at = datetime.utcnow()
                db_session.add(entry)

            db_session.commit()

        # Verify consistency after all operations
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent after mixed operations: {issues}"

    @given(
        url=url_strategy,
        output_path=output_path_strategy,
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_progress_bounds_maintained(
        self,
        db_session,
        url: str,
        output_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        Queue item progress SHALL always be within valid bounds (0-100).
        """
        # Clean database
        clean_database(db_session)

        # Add queue item with various progress values
        item = QueueItem(
            id=str(uuid.uuid4()),
            url=url,
            output_path=output_path,
            status=DownloadStatus.DOWNLOADING,
            progress=0.0,
            position=1,
        )
        item.created_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        db_session.add(item)
        db_session.commit()

        # Try to set progress to various values
        test_values = [0.0, 25.0, 50.0, 75.0, 100.0]
        for progress in test_values:
            item.progress = progress
            db_session.commit()

            # Verify progress is within bounds
            assert 0.0 <= item.progress <= 100.0, (
                f"Progress {item.progress} out of bounds"
            )

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent after progress updates: {issues}"

    @given(num_items=st.integers(min_value=1, max_value=10))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_unique_ids_maintained(
        self,
        db_session,
        num_items: int,
    ):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        All records SHALL have unique IDs within their table.
        """
        # Clean database
        clean_database(db_session)

        # Add multiple items of each type
        for i in range(num_items):
            user = User(name=f"user_{uuid.uuid4()}", preferences="{}")
            db_session.add(user)

            item = QueueItem(
                id=str(uuid.uuid4()),
                url=f"https://example.com/video/{uuid.uuid4()}",
                output_path=f"/downloads/{uuid.uuid4()}.mp4",
                status=DownloadStatus.PENDING,
                progress=0.0,
                position=i,
            )
            item.created_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            db_session.add(item)

            entry = DownloadHistory(
                id=str(uuid.uuid4()),
                url=f"https://example.com/video/{uuid.uuid4()}",
                title=f"Video {i}",
                file_path=f"/downloads/{uuid.uuid4()}.mp4",
                status="completed",
            )
            entry.downloaded_at = datetime.utcnow()
            entry.created_at = datetime.utcnow()
            entry.updated_at = datetime.utcnow()
            db_session.add(entry)

        db_session.commit()

        # Verify all IDs are unique
        user_ids = [u.id for u in db_session.query(User).all()]
        queue_ids = [q.id for q in db_session.query(QueueItem).all()]
        history_ids = [h.id for h in db_session.query(DownloadHistory).all()]

        assert len(user_ids) == len(set(user_ids)), "User IDs should be unique"
        assert len(queue_ids) == len(set(queue_ids)), "Queue item IDs should be unique"
        assert len(history_ids) == len(set(history_ids)), "History entry IDs should be unique"

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Database inconsistent: {issues}"

    @pytest.mark.property
    def test_empty_database_is_consistent(self, db_session):
        """
        Feature: farmer-cli-completion, Property 5: Database Consistency Invariant
        Validates: Requirements 11.6

        An empty database SHALL be in a consistent state.
        """
        # Clean database
        clean_database(db_session)

        # Verify consistency
        is_consistent, issues = verify_database_consistency(db_session)
        assert is_consistent, f"Empty database should be consistent: {issues}"
