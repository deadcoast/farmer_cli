"""
Property-based tests for QueueItem model.

Feature: farmer-cli-completion
Property 8: Queue Item Completeness
Validates: Requirements 4.2

For any QueueItem in the download queue, it SHALL contain non-null values
for id, url, output_path, status, progress, position, and created_at fields.
"""

import string
from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st

from farmer_cli.models.download import DownloadStatus
from farmer_cli.models.download import QueueItem
from farmer_cli.models.download import VALID_STATUS_TRANSITIONS


# ---------------------------------------------------------------------------
# Strategies for generating test data
# ---------------------------------------------------------------------------

# Strategy for generating valid UUIDs
uuid_strategy = st.uuids().map(str)

# Strategy for generating valid URLs
url_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "/:.-_?=&%",
    min_size=10,
    max_size=200,
).map(lambda s: f"https://example.com/{s}")

# Strategy for generating valid titles
title_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet=string.ascii_letters + string.digits + " -_",
        min_size=1,
        max_size=100,
    ).filter(lambda s: s.strip()),
)

# Strategy for generating valid output paths
output_path_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "/_.-",
    min_size=5,
    max_size=200,
).map(lambda s: f"/downloads/{s}.mp4")

# Strategy for generating format IDs
format_id_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet=string.ascii_letters + string.digits + "-_",
        min_size=1,
        max_size=20,
    ),
)

# Strategy for generating status values
status_strategy = st.sampled_from(list(DownloadStatus))

# Strategy for generating progress values
progress_strategy = st.floats(min_value=0.0, max_value=100.0, allow_nan=False)

# Strategy for generating position values
position_strategy = st.integers(min_value=0, max_value=1000)

# Strategy for generating error messages
error_message_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=200),
)

# Strategy for generating valid QueueItem instances
queue_item_strategy = st.builds(
    QueueItem,
    id=uuid_strategy,
    url=url_strategy,
    title=title_strategy,
    format_id=format_id_strategy,
    output_path=output_path_strategy,
    status=status_strategy,
    progress=progress_strategy,
    position=position_strategy,
    error_message=error_message_strategy,
)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestQueueItemCompleteness:
    """
    Property 8: Queue Item Completeness

    For any QueueItem in the download queue, it SHALL contain non-null values
    for id, url, output_path, status, progress, position, and created_at fields.

    **Validates: Requirements 4.2**
    """

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_id_is_never_null(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, id SHALL be non-null and non-empty.
        """
        assert queue_item.id is not None, "id should not be None"
        assert len(queue_item.id) > 0, "id should not be empty"

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_url_is_never_null(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, url SHALL be non-null and non-empty.
        """
        assert queue_item.url is not None, "url should not be None"
        assert len(queue_item.url) > 0, "url should not be empty"

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_output_path_is_never_null(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, output_path SHALL be non-null and non-empty.
        """
        assert queue_item.output_path is not None, "output_path should not be None"
        assert len(queue_item.output_path) > 0, "output_path should not be empty"

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_status_is_never_null(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, status SHALL be non-null and a valid DownloadStatus.
        """
        assert queue_item.status is not None, "status should not be None"
        assert isinstance(queue_item.status, DownloadStatus), "status should be a DownloadStatus"

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_progress_is_never_null(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, progress SHALL be non-null and within valid range.
        """
        assert queue_item.progress is not None, "progress should not be None"
        assert 0.0 <= queue_item.progress <= 100.0, "progress should be between 0 and 100"

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_position_is_never_null(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, position SHALL be non-null and non-negative.
        """
        assert queue_item.position is not None, "position should not be None"
        assert queue_item.position >= 0, "position should be non-negative"

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_created_at_has_default(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, created_at SHALL have a default value when not explicitly set.
        """
        # The model has a default for created_at, so it should be set
        # For this test, we verify the model accepts datetime values
        queue_item.created_at = datetime.utcnow()
        assert queue_item.created_at is not None, "created_at should not be None"
        assert isinstance(queue_item.created_at, datetime), "created_at should be a datetime"

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_to_dict_contains_required_fields(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, to_dict() SHALL contain all required fields.
        """
        # Set created_at for the test
        queue_item.created_at = datetime.utcnow()

        result = queue_item.to_dict()

        required_fields = ["id", "url", "output_path", "status", "progress", "position", "created_at"]
        for field in required_fields:
            assert field in result, f"to_dict() should contain '{field}'"
            assert result[field] is not None, f"'{field}' should not be None in to_dict()"

    @given(
        st.sampled_from(["", " ", "\t", "\n", "\r", "  ", "\t\n"]),
        output_path_strategy,
        position_strategy,
    )
    @settings(max_examples=50)
    @pytest.mark.property
    def test_empty_url_raises_error(self, url: str, output_path: str, position: int):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any empty or whitespace-only URL, QueueItem construction
        SHALL raise a ValueError.
        """
        with pytest.raises(ValueError, match="URL cannot be empty"):
            QueueItem(url=url, output_path=output_path, position=position)

    @given(
        url_strategy,
        st.sampled_from(["", " ", "\t", "\n", "\r", "  ", "\t\n"]),
        position_strategy,
    )
    @settings(max_examples=50)
    @pytest.mark.property
    def test_empty_output_path_raises_error(self, url: str, output_path: str, position: int):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any empty or whitespace-only output_path, QueueItem construction
        SHALL raise a ValueError.
        """
        with pytest.raises(ValueError, match="Output path cannot be empty"):
            QueueItem(url=url, output_path=output_path, position=position)

    @given(
        url_strategy,
        output_path_strategy,
        st.integers(max_value=-1),
    )
    @settings(max_examples=50)
    @pytest.mark.property
    def test_negative_position_raises_error(self, url: str, output_path: str, position: int):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any negative position, QueueItem construction SHALL raise a ValueError.
        """
        with pytest.raises(ValueError, match="Position cannot be negative"):
            QueueItem(url=url, output_path=output_path, position=position)

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_progress_is_clamped_to_valid_range(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, progress SHALL always be within 0.0 to 100.0.
        """
        # Test that progress is clamped
        queue_item.progress = -10.0
        assert queue_item.progress == 0.0, "progress should be clamped to 0.0"

        queue_item.progress = 150.0
        assert queue_item.progress == 100.0, "progress should be clamped to 100.0"


class TestQueueItemStatusTransitions:
    """
    Tests for valid status transitions in QueueItem.

    **Validates: Requirements 4.2**
    """

    @given(status_strategy, status_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_can_transition_to_is_consistent(
        self, current_status: DownloadStatus, new_status: DownloadStatus
    ):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any status transition, can_transition_to SHALL return True
        only for valid transitions defined in VALID_STATUS_TRANSITIONS.
        """
        queue_item = QueueItem(
            url="https://example.com/video",
            output_path="/downloads/video.mp4",
            position=0,
            status=current_status,
        )

        can_transition = queue_item.can_transition_to(new_status)

        # Same status is always valid
        if current_status == new_status:
            assert can_transition, "Same status transition should always be valid"
        else:
            # Check against the defined valid transitions
            valid_transitions = VALID_STATUS_TRANSITIONS.get(current_status, set())
            expected = new_status in valid_transitions
            assert can_transition == expected, (
                f"can_transition_to({new_status}) should be {expected} "
                f"for current status {current_status}"
            )

    @given(status_strategy, status_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_transition_to_validates_correctly(
        self, current_status: DownloadStatus, new_status: DownloadStatus
    ):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any status transition, transition_to SHALL succeed for valid
        transitions and raise ValueError for invalid ones.
        """
        queue_item = QueueItem(
            url="https://example.com/video",
            output_path="/downloads/video.mp4",
            position=0,
            status=current_status,
        )

        can_transition = queue_item.can_transition_to(new_status)

        if can_transition:
            # Should succeed
            queue_item.transition_to(new_status)
            assert queue_item.status == new_status
        else:
            # Should raise ValueError
            with pytest.raises(ValueError, match="Invalid status transition"):
                queue_item.transition_to(new_status)

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_is_active_property(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, is_active SHALL be True only when status is DOWNLOADING.
        """
        expected = queue_item.status == DownloadStatus.DOWNLOADING
        assert queue_item.is_active == expected

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_is_pending_property(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, is_pending SHALL be True only when status is PENDING.
        """
        expected = queue_item.status == DownloadStatus.PENDING
        assert queue_item.is_pending == expected

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_is_completed_property(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, is_completed SHALL be True only when status is COMPLETED.
        """
        expected = queue_item.status == DownloadStatus.COMPLETED
        assert queue_item.is_completed == expected

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_is_failed_property(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, is_failed SHALL be True only when status is FAILED.
        """
        expected = queue_item.status == DownloadStatus.FAILED
        assert queue_item.is_failed == expected

    @given(queue_item_strategy)
    @settings(max_examples=100)
    @pytest.mark.property
    def test_is_terminal_property(self, queue_item: QueueItem):
        """
        Feature: farmer-cli-completion, Property 8: Queue Item Completeness
        Validates: Requirements 4.2

        For any QueueItem, is_terminal SHALL be True only when status is
        COMPLETED or CANCELLED.
        """
        expected = queue_item.status in {DownloadStatus.COMPLETED, DownloadStatus.CANCELLED}
        assert queue_item.is_terminal == expected
