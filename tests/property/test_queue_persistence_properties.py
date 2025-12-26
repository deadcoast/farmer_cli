"""
Property-based tests for queue persistence round-trip in DownloadManager.

Feature: farmer-cli-completion
Property 4: Queue Persistence Round-Trip
Validates: Requirements 4.4

For any download queue state, persisting to database then loading on restart
SHALL restore the exact queue with all items, positions, and statuses preserved.
"""

import string
import uuid
from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st

from farmer_cli.models.download import DownloadStatus
from farmer_cli.models.download import QueueItem
from farmer_cli.services.download_manager import DownloadManager


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid URLs with unique suffix
url_strategy = st.uuids().map(lambda u: f"https://example.com/video/{u}")

# Strategy for generating valid titles
title_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet=string.ascii_letters + string.digits + " -_",
        min_size=1,
        max_size=100,
    ).filter(lambda s: s.strip()),
)

# Strategy for generating valid output paths with unique suffix
output_path_strategy = st.uuids().map(lambda u: f"/downloads/{u}.mp4")

# Strategy for generating format IDs
format_id_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet=string.ascii_letters + string.digits + "-_",
        min_size=1,
        max_size=20,
    ),
)

# Strategy for generating non-terminal statuses (can be restored)
restorable_status_strategy = st.sampled_from([
    DownloadStatus.PENDING,
    DownloadStatus.DOWNLOADING,
    DownloadStatus.PAUSED,
    DownloadStatus.FAILED,
])

# Strategy for generating progress values
progress_strategy = st.floats(min_value=0.0, max_value=100.0, allow_nan=False)

# Strategy for generating number of queue items
num_items_strategy = st.integers(min_value=1, max_value=10)


# ---------------------------------------------------------------------------
# Helper function to clean database
# ---------------------------------------------------------------------------

def clean_queue(session):
    """Clean all queue items from the database."""
    session.query(QueueItem).delete()
    session.commit()


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestQueuePersistenceRoundTrip:
    """
    Property 4: Queue Persistence Round-Trip

    For any download queue state, persisting to database then loading on restart
    SHALL restore the exact queue with all items, positions, and statuses preserved.

    **Validates: Requirements 4.4**
    """

    @given(
        url=url_strategy,
        title=title_strategy,
        output_path=output_path_strategy,
        format_id=format_id_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_add_to_queue_persists_item(
        self,
        db_session,
        url: str,
        title: str | None,
        output_path: str,
        format_id: str | None,
    ):
        """
        Feature: farmer-cli-completion, Property 4: Queue Persistence Round-Trip
        Validates: Requirements 4.4

        For any queue item added, it SHALL be persisted to the database.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)

        # Add item to queue
        item = manager.add_to_queue(
            url=url,
            output_path=output_path,
            format_id=format_id,
            title=title,
        )

        # Verify item was persisted
        persisted_item = db_session.query(QueueItem).filter(QueueItem.id == item.id).first()

        assert persisted_item is not None, "Item should be persisted to database"
        assert persisted_item.url == url, "URL should be preserved"
        assert persisted_item.output_path == output_path, "Output path should be preserved"
        assert persisted_item.format_id == format_id, "Format ID should be preserved"
        assert persisted_item.title == title, "Title should be preserved"
        assert persisted_item.status == DownloadStatus.PENDING, "Status should be PENDING"

    @given(num_items=num_items_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_queue_positions_are_preserved(
        self,
        db_session,
        num_items: int,
    ):
        """
        Feature: farmer-cli-completion, Property 4: Queue Persistence Round-Trip
        Validates: Requirements 4.4

        For any number of queue items, positions SHALL be preserved after restoration.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)

        # Add multiple items
        added_items = []
        for i in range(num_items):
            item = manager.add_to_queue(
                url=f"https://example.com/video{uuid.uuid4()}",
                output_path=f"/downloads/video{uuid.uuid4()}.mp4",
                title=f"Video {i}",
            )
            added_items.append(item)

        # Restore queue
        restored_items = manager.restore_queue()

        # Verify positions are preserved
        assert len(restored_items) == num_items, "All items should be restored"

        for i, restored in enumerate(restored_items):
            assert restored.position == i + 1, f"Position {i + 1} should be preserved"

    @given(
        url=url_strategy,
        output_path=output_path_strategy,
        status=restorable_status_strategy,
        progress=progress_strategy,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_queue_item_fields_are_preserved(
        self,
        db_session,
        url: str,
        output_path: str,
        status: DownloadStatus,
        progress: float,
    ):
        """
        Feature: farmer-cli-completion, Property 4: Queue Persistence Round-Trip
        Validates: Requirements 4.4

        For any queue item, all fields SHALL be preserved after restoration.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        # Create item directly in database with specific status
        item_id = str(uuid.uuid4())
        item = QueueItem(
            id=item_id,
            url=url,
            output_path=output_path,
            status=status,
            progress=progress,
            position=1,
        )
        item.created_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        db_session.add(item)
        db_session.commit()

        # Create new manager and restore
        manager = DownloadManager(session_factory=lambda: db_session)
        restored_items = manager.restore_queue()

        # Find our item
        restored = next((i for i in restored_items if i.id == item_id), None)

        assert restored is not None, "Item should be restored"
        assert restored.url == url, "URL should be preserved"
        assert restored.output_path == output_path, "Output path should be preserved"
        # Note: DOWNLOADING items are reset to PENDING
        if status == DownloadStatus.DOWNLOADING:
            assert restored.status == DownloadStatus.PENDING, (
                "DOWNLOADING items should be reset to PENDING"
            )
        else:
            assert restored.status == status, "Status should be preserved"

    @given(num_items=num_items_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_downloading_items_reset_to_pending_on_restore(
        self,
        db_session,
        num_items: int,
    ):
        """
        Feature: farmer-cli-completion, Property 4: Queue Persistence Round-Trip
        Validates: Requirements 4.4

        For any DOWNLOADING items, restore_queue SHALL reset them to PENDING.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        # Create items with DOWNLOADING status
        item_ids = []
        for i in range(num_items):
            item = QueueItem(
                id=str(uuid.uuid4()),
                url=f"https://example.com/video{uuid.uuid4()}",
                output_path=f"/downloads/video{uuid.uuid4()}.mp4",
                status=DownloadStatus.DOWNLOADING,
                progress=50.0,
                position=i,
            )
            item.created_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            db_session.add(item)
            item_ids.append(item.id)

        db_session.commit()

        # Restore queue
        manager = DownloadManager(session_factory=lambda: db_session)
        restored_items = manager.restore_queue()

        # Verify all DOWNLOADING items are reset to PENDING
        for restored in restored_items:
            assert restored.status == DownloadStatus.PENDING, (
                "DOWNLOADING items should be reset to PENDING on restore"
            )

    @pytest.mark.property
    def test_completed_items_not_restored(self, db_session):
        """
        Feature: farmer-cli-completion, Property 4: Queue Persistence Round-Trip
        Validates: Requirements 4.4

        COMPLETED items SHALL NOT be included in restored queue.
        """
        # Clean database before test
        clean_queue(db_session)

        # Create completed item
        completed_item = QueueItem(
            id=str(uuid.uuid4()),
            url="https://example.com/completed",
            output_path="/downloads/completed.mp4",
            status=DownloadStatus.COMPLETED,
            progress=100.0,
            position=1,
        )
        completed_item.created_at = datetime.utcnow()
        completed_item.updated_at = datetime.utcnow()
        db_session.add(completed_item)

        # Create pending item
        pending_item = QueueItem(
            id=str(uuid.uuid4()),
            url="https://example.com/pending",
            output_path="/downloads/pending.mp4",
            status=DownloadStatus.PENDING,
            progress=0.0,
            position=2,
        )
        pending_item.created_at = datetime.utcnow()
        pending_item.updated_at = datetime.utcnow()
        db_session.add(pending_item)

        db_session.commit()

        # Restore queue
        manager = DownloadManager(session_factory=lambda: db_session)
        restored_items = manager.restore_queue()

        # Verify only pending item is restored
        assert len(restored_items) == 1, "Only non-terminal items should be restored"
        assert restored_items[0].id == pending_item.id, "Pending item should be restored"

    @pytest.mark.property
    def test_cancelled_items_not_restored(self, db_session):
        """
        Feature: farmer-cli-completion, Property 4: Queue Persistence Round-Trip
        Validates: Requirements 4.4

        CANCELLED items SHALL NOT be included in restored queue.
        """
        # Clean database before test
        clean_queue(db_session)

        # Create cancelled item
        cancelled_item = QueueItem(
            id=str(uuid.uuid4()),
            url="https://example.com/cancelled",
            output_path="/downloads/cancelled.mp4",
            status=DownloadStatus.CANCELLED,
            progress=0.0,
            position=1,
        )
        cancelled_item.created_at = datetime.utcnow()
        cancelled_item.updated_at = datetime.utcnow()
        db_session.add(cancelled_item)

        # Create pending item
        pending_item = QueueItem(
            id=str(uuid.uuid4()),
            url="https://example.com/pending",
            output_path="/downloads/pending.mp4",
            status=DownloadStatus.PENDING,
            progress=0.0,
            position=2,
        )
        pending_item.created_at = datetime.utcnow()
        pending_item.updated_at = datetime.utcnow()
        db_session.add(pending_item)

        db_session.commit()

        # Restore queue
        manager = DownloadManager(session_factory=lambda: db_session)
        restored_items = manager.restore_queue()

        # Verify only pending item is restored
        assert len(restored_items) == 1, "Only non-terminal items should be restored"
        assert restored_items[0].id == pending_item.id, "Pending item should be restored"

    @given(num_items=num_items_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_queue_order_preserved_after_restore(
        self,
        db_session,
        num_items: int,
    ):
        """
        Feature: farmer-cli-completion, Property 4: Queue Persistence Round-Trip
        Validates: Requirements 4.4

        For any queue, the order of items SHALL be preserved after restoration.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)

        # Add items in order
        original_urls = []
        for i in range(num_items):
            url = f"https://example.com/video{uuid.uuid4()}"
            manager.add_to_queue(
                url=url,
                output_path=f"/downloads/video{uuid.uuid4()}.mp4",
            )
            original_urls.append(url)

        # Restore queue
        restored_items = manager.restore_queue()

        # Verify order is preserved
        restored_urls = [item.url for item in restored_items]
        assert restored_urls == original_urls, "Queue order should be preserved"

    @given(
        url=url_strategy,
        output_path=output_path_strategy,
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_failed_items_preserved_with_error_message(
        self,
        db_session,
        url: str,
        output_path: str,
    ):
        """
        Feature: farmer-cli-completion, Property 4: Queue Persistence Round-Trip
        Validates: Requirements 4.4

        For FAILED items, error_message SHALL be preserved after restoration.
        """
        # Clean database before each iteration
        clean_queue(db_session)

        error_message = "Test error message"

        # Create failed item with error message
        item = QueueItem(
            id=str(uuid.uuid4()),
            url=url,
            output_path=output_path,
            status=DownloadStatus.FAILED,
            progress=0.0,
            position=1,
            error_message=error_message,
        )
        item.created_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        db_session.add(item)
        db_session.commit()

        # Restore queue
        manager = DownloadManager(session_factory=lambda: db_session)
        restored_items = manager.restore_queue()

        # Verify error message is preserved
        assert len(restored_items) == 1
        assert restored_items[0].error_message == error_message, (
            "Error message should be preserved"
        )

    @pytest.mark.property
    def test_empty_queue_restores_empty(self, db_session):
        """
        Feature: farmer-cli-completion, Property 4: Queue Persistence Round-Trip
        Validates: Requirements 4.4

        For an empty queue, restore_queue SHALL return an empty list.
        """
        # Clean database before test
        clean_queue(db_session)

        manager = DownloadManager(session_factory=lambda: db_session)

        restored_items = manager.restore_queue()

        assert restored_items == [], "Empty queue should restore as empty list"
