"""
Download manager service for managing download queue and history.

This module provides the DownloadManager class for managing download operations,
including queue management, history tracking, and concurrent download control.

Feature: farmer-cli-completion
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.6
"""

import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..exceptions import DatabaseError
from ..exceptions import QueueError
from ..models.download import DownloadStatus
from ..models.download import QueueItem
from ..models.history import DownloadHistory


logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """
    Data class representing a download history entry.

    Attributes:
        id: Unique identifier for the history entry
        url: URL of the downloaded video
        title: Title of the downloaded video
        file_path: Path where the file was saved
        file_size: Size of the downloaded file in bytes
        downloaded_at: Timestamp when download completed
        status: Status of the download
        file_exists: Whether the downloaded file still exists
        format_id: Format ID used for download
        duration: Duration of the video in seconds
        uploader: Name of the video uploader/channel
    """

    id: str
    url: str
    title: str
    file_path: str
    file_size: int | None
    downloaded_at: datetime
    status: str
    file_exists: bool = False
    format_id: str | None = None
    duration: int | None = None
    uploader: str | None = None

    @classmethod
    def from_model(cls, model: DownloadHistory) -> "HistoryEntry":
        """
        Create a HistoryEntry from a DownloadHistory model.

        Args:
            model: DownloadHistory SQLAlchemy model instance

        Returns:
            HistoryEntry data class instance
        """
        return cls(
            id=model.id,
            url=model.url,
            title=model.title,
            file_path=model.file_path,
            file_size=model.file_size,
            downloaded_at=model.downloaded_at,
            status=model.status,
            file_exists=model.file_exists,
            format_id=model.format_id,
            duration=model.duration,
            uploader=model.uploader,
        )


class DownloadManager:
    """
    Manages download queue and history.

    This class provides methods for adding downloads to a queue, managing
    queue state, tracking download history, and controlling concurrent downloads.

    Attributes:
        session_factory: Callable that returns a database session
        max_concurrent: Maximum number of concurrent downloads (1-5)
        default_output_path: Default directory for downloads
    """

    MIN_CONCURRENT = 1
    MAX_CONCURRENT = 5
    DEFAULT_CONCURRENT = 3

    def __init__(
        self,
        session_factory: Callable[[], Session],
        default_output_path: str | Path | None = None,
        max_concurrent: int = DEFAULT_CONCURRENT,
    ) -> None:
        """
        Initialize the download manager.

        Args:
            session_factory: Callable that returns a database session
            default_output_path: Default directory for downloads
            max_concurrent: Maximum concurrent downloads (1-5)
        """
        self._session_factory = session_factory
        self._default_output_path = Path(default_output_path) if default_output_path else Path.cwd() / "downloads"
        self._max_concurrent = self._validate_concurrent(max_concurrent)
        self._active_downloads: dict[str, bool] = {}
        self._lock = threading.Lock()
        self._on_download_complete: Callable[[str], None] | None = None

    def _validate_concurrent(self, value: int) -> int:
        """Validate and clamp concurrent download limit."""
        if value < self.MIN_CONCURRENT:
            return self.MIN_CONCURRENT
        if value > self.MAX_CONCURRENT:
            return self.MAX_CONCURRENT
        return value

    def _get_session(self) -> Session:
        """Get a database session."""
        return self._session_factory()

    def _get_next_position(self, session: Session) -> int:
        """
        Get the next available position in the queue.

        Args:
            session: Database session

        Returns:
            Next available position number
        """
        max_position = session.query(func.max(QueueItem.position)).scalar()
        return (max_position or 0) + 1

    def add_to_queue(
        self,
        url: str,
        output_path: str | Path | None = None,
        format_id: str | None = None,
        title: str | None = None,
    ) -> QueueItem:
        """
        Add a download to the queue.

        Creates a new QueueItem with a generated UUID and persists it to the database.
        The item is added at the end of the queue with PENDING status.

        Args:
            url: URL of the video to download
            output_path: Output path for the download (uses default if not specified)
            format_id: Optional format ID for the download
            title: Optional title for the video

        Returns:
            Created QueueItem instance

        Raises:
            QueueError: If the item cannot be added to the queue
            ValueError: If the URL is empty or invalid
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        url = url.strip()

        # Determine output path
        if output_path:
            resolved_output_path = str(Path(output_path))
        else:
            resolved_output_path = str(self._default_output_path)

        session = self._get_session()
        try:
            # Get next position
            position = self._get_next_position(session)

            # Create queue item
            queue_item = QueueItem(
                id=str(uuid.uuid4()),
                url=url,
                title=title,
                format_id=format_id,
                output_path=resolved_output_path,
                status=DownloadStatus.PENDING,
                progress=0.0,
                position=position,
                error_message=None,
            )

            # Set timestamps
            now = datetime.utcnow()
            queue_item.created_at = now
            queue_item.updated_at = now

            session.add(queue_item)
            session.commit()

            logger.info(f"Added download to queue: {queue_item.id} - {url[:50]}...")
            return queue_item

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to add download to queue: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def get_queue(self, include_completed: bool = False) -> list[QueueItem]:
        """
        Get all items in the download queue.

        Returns queue items ordered by position (lower position = higher priority).

        Args:
            include_completed: Whether to include completed/cancelled items

        Returns:
            List of QueueItem objects ordered by position

        Raises:
            QueueError: If the queue cannot be retrieved
        """
        session = self._get_session()
        try:
            query = session.query(QueueItem)

            if not include_completed:
                # Exclude terminal states
                query = query.filter(
                    QueueItem.status.notin_(
                        [
                            DownloadStatus.COMPLETED,
                            DownloadStatus.CANCELLED,
                        ]
                    )
                )

            items = query.order_by(QueueItem.position).all()

            # Detach from session to allow use after session closes
            for item in items:
                session.expunge(item)

            return items

        except Exception as e:
            error_msg = f"Failed to retrieve download queue: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def get_queue_item(self, item_id: str) -> QueueItem | None:
        """
        Get a specific queue item by ID.

        Args:
            item_id: UUID of the queue item

        Returns:
            QueueItem if found, None otherwise

        Raises:
            QueueError: If the query fails
        """
        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()
            if item:
                session.expunge(item)
            return item
        except Exception as e:
            error_msg = f"Failed to retrieve queue item {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def pause_download(self, item_id: str) -> bool:
        """
        Pause a download.

        Transitions the download status from DOWNLOADING to PAUSED.

        Args:
            item_id: UUID of the queue item to pause

        Returns:
            True if paused successfully, False if item not found or cannot be paused

        Raises:
            QueueError: If the operation fails
        """
        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                logger.warning(f"Queue item not found: {item_id}")
                return False

            if not item.can_transition_to(DownloadStatus.PAUSED):
                logger.warning(f"Cannot pause item {item_id}: current status is {item.status.value}")
                return False

            item.transition_to(DownloadStatus.PAUSED)
            item.updated_at = datetime.utcnow()
            session.commit()

            # Update active downloads tracking
            with self._lock:
                if item_id in self._active_downloads:
                    del self._active_downloads[item_id]

            logger.info(f"Paused download: {item_id}")
            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to pause download {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def resume_download(self, item_id: str) -> bool:
        """
        Resume a paused download.

        Transitions the download status from PAUSED to DOWNLOADING.

        Args:
            item_id: UUID of the queue item to resume

        Returns:
            True if resumed successfully, False if item not found or cannot be resumed

        Raises:
            QueueError: If the operation fails
        """
        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                logger.warning(f"Queue item not found: {item_id}")
                return False

            if not item.can_transition_to(DownloadStatus.DOWNLOADING):
                logger.warning(f"Cannot resume item {item_id}: current status is {item.status.value}")
                return False

            item.transition_to(DownloadStatus.DOWNLOADING)
            item.updated_at = datetime.utcnow()
            session.commit()

            # Update active downloads tracking
            with self._lock:
                self._active_downloads[item_id] = True

            logger.info(f"Resumed download: {item_id}")
            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to resume download {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def cancel_download(self, item_id: str, cleanup: bool = True) -> bool:
        """
        Cancel a download.

        Transitions the download status to CANCELLED and optionally removes
        any partially downloaded files.

        Args:
            item_id: UUID of the queue item to cancel
            cleanup: Whether to remove partial files

        Returns:
            True if cancelled successfully, False if item not found or cannot be cancelled

        Raises:
            QueueError: If the operation fails
        """
        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                logger.warning(f"Queue item not found: {item_id}")
                return False

            if not item.can_transition_to(DownloadStatus.CANCELLED):
                logger.warning(f"Cannot cancel item {item_id}: current status is {item.status.value}")
                return False

            # Store output path before transition for cleanup
            output_path = item.output_path

            item.transition_to(DownloadStatus.CANCELLED)
            item.updated_at = datetime.utcnow()
            session.commit()

            # Update active downloads tracking
            with self._lock:
                if item_id in self._active_downloads:
                    del self._active_downloads[item_id]

            # Cleanup partial files if requested
            if cleanup and output_path:
                self._cleanup_partial_files(output_path)

            logger.info(f"Cancelled download: {item_id}")
            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to cancel download {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def _cleanup_partial_files(self, output_path: str) -> None:
        """
        Clean up partial download files.

        Args:
            output_path: Path to check for partial files
        """
        try:
            path = Path(output_path)
            # Check for common partial file patterns
            partial_patterns = [
                path.with_suffix(path.suffix + ".part"),
                path.with_suffix(".part"),
                path.with_name(path.name + ".ytdl"),
            ]

            for partial_path in partial_patterns:
                if partial_path.exists():
                    partial_path.unlink()
                    logger.debug(f"Removed partial file: {partial_path}")

        except Exception as e:
            logger.warning(f"Failed to cleanup partial files: {e}")

    def reorder_queue(self, item_id: str, new_position: int) -> bool:
        """
        Move a queue item to a new position.

        Reorders the queue by moving the specified item to the new position
        and adjusting other items' positions accordingly.

        Args:
            item_id: UUID of the queue item to move
            new_position: New position for the item (0-indexed)

        Returns:
            True if reordered successfully, False if item not found

        Raises:
            QueueError: If the operation fails
            ValueError: If new_position is negative
        """
        if new_position < 0:
            raise ValueError("Position cannot be negative")

        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                logger.warning(f"Queue item not found: {item_id}")
                return False

            old_position = item.position

            if old_position == new_position:
                return True  # No change needed

            # Get all non-terminal items ordered by position
            all_items = (
                session.query(QueueItem)
                .filter(
                    QueueItem.status.notin_(
                        [
                            DownloadStatus.COMPLETED,
                            DownloadStatus.CANCELLED,
                        ]
                    )
                )
                .order_by(QueueItem.position)
                .all()
            )

            # Clamp new_position to valid range
            max_position = len(all_items) - 1
            new_position = min(new_position, max_position)

            # Reorder items
            if old_position < new_position:
                # Moving down: shift items between old and new position up
                for other_item in all_items:
                    if old_position < other_item.position <= new_position:
                        other_item.position -= 1
                        other_item.updated_at = datetime.utcnow()
            else:
                # Moving up: shift items between new and old position down
                for other_item in all_items:
                    if new_position <= other_item.position < old_position:
                        other_item.position += 1
                        other_item.updated_at = datetime.utcnow()

            item.position = new_position
            item.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"Reordered item {item_id} from position {old_position} to {new_position}")
            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to reorder queue item {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def remove_from_queue(self, item_id: str) -> bool:
        """
        Remove an item from the queue entirely.

        Args:
            item_id: UUID of the queue item to remove

        Returns:
            True if removed successfully, False if item not found

        Raises:
            QueueError: If the operation fails
        """
        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                logger.warning(f"Queue item not found: {item_id}")
                return False

            removed_position = item.position
            session.delete(item)

            # Update positions of items after the removed one
            items_after = session.query(QueueItem).filter(QueueItem.position > removed_position).all()
            for other_item in items_after:
                other_item.position -= 1
                other_item.updated_at = datetime.utcnow()

            session.commit()

            # Update active downloads tracking
            with self._lock:
                if item_id in self._active_downloads:
                    del self._active_downloads[item_id]

            logger.info(f"Removed item from queue: {item_id}")
            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to remove queue item {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def check_duplicate(self, url: str) -> HistoryEntry | None:
        """
        Check if a URL was previously downloaded.

        Queries the download history to find any matching entries for the given URL.

        Args:
            url: URL to check for duplicates

        Returns:
            HistoryEntry if URL was previously downloaded, None otherwise

        Raises:
            DatabaseError: If the query fails
        """
        if not url or not url.strip():
            return None

        url = url.strip()

        session = self._get_session()
        try:
            history_item = (
                session.query(DownloadHistory)
                .filter(DownloadHistory.url == url)
                .order_by(DownloadHistory.downloaded_at.desc())
                .first()
            )

            if history_item:
                return HistoryEntry.from_model(history_item)

            return None

        except Exception as e:
            error_msg = f"Failed to check for duplicate: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        finally:
            session.close()

    def add_to_history(
        self,
        url: str,
        title: str,
        file_path: str,
        file_size: int | None = None,
        format_id: str | None = None,
        duration: int | None = None,
        uploader: str | None = None,
        status: str = "completed",
    ) -> HistoryEntry:
        """
        Add a completed download to history.

        Args:
            url: URL of the downloaded video
            title: Title of the video
            file_path: Path where the file was saved
            file_size: Size of the file in bytes
            format_id: Format ID used for download
            duration: Duration of the video in seconds
            uploader: Name of the uploader/channel
            status: Status of the download

        Returns:
            Created HistoryEntry

        Raises:
            DatabaseError: If the entry cannot be added
        """
        session = self._get_session()
        try:
            history_item = DownloadHistory(
                id=str(uuid.uuid4()),
                url=url,
                title=title,
                file_path=file_path,
                file_size=file_size,
                format_id=format_id,
                duration=duration,
                uploader=uploader,
                downloaded_at=datetime.utcnow(),
                status=status,
            )

            session.add(history_item)
            session.commit()

            logger.info(f"Added to history: {history_item.id} - {title[:50]}...")
            return HistoryEntry.from_model(history_item)

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to add to history: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        finally:
            session.close()

    def get_history(
        self,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[HistoryEntry]:
        """
        Get download history with optional search filter.

        Queries the download history with support for searching by title or URL,
        and pagination. Also checks file existence for each entry.

        Args:
            search: Optional search term to filter by title or URL
            limit: Maximum number of entries to return
            offset: Number of entries to skip (for pagination)

        Returns:
            List of HistoryEntry objects

        Raises:
            DatabaseError: If the query fails
        """
        session = self._get_session()
        try:
            query = session.query(DownloadHistory)

            # Apply search filter if provided
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (DownloadHistory.title.ilike(search_term))
                    | (DownloadHistory.url.ilike(search_term))
                    | (DownloadHistory.uploader.ilike(search_term))
                )

            # Order by download date (most recent first)
            query = query.order_by(DownloadHistory.downloaded_at.desc())

            # Apply pagination
            query = query.offset(offset).limit(limit)

            history_items = query.all()

            # Convert to HistoryEntry objects (file_exists is computed property)
            entries = [HistoryEntry.from_model(item) for item in history_items]

            return entries

        except Exception as e:
            error_msg = f"Failed to retrieve download history: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        finally:
            session.close()

    def get_history_count(self, search: str | None = None) -> int:
        """
        Get total count of history entries.

        Args:
            search: Optional search term to filter by title or URL

        Returns:
            Total count of matching history entries

        Raises:
            DatabaseError: If the query fails
        """
        session = self._get_session()
        try:
            query = session.query(func.count(DownloadHistory.id))

            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (DownloadHistory.title.ilike(search_term))
                    | (DownloadHistory.url.ilike(search_term))
                    | (DownloadHistory.uploader.ilike(search_term))
                )

            return query.scalar() or 0

        except Exception as e:
            error_msg = f"Failed to count history entries: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        finally:
            session.close()

    def clear_history(self) -> int:
        """
        Clear all download history.

        Returns:
            Number of entries deleted

        Raises:
            DatabaseError: If the operation fails
        """
        session = self._get_session()
        try:
            count = session.query(DownloadHistory).delete()
            session.commit()
            logger.info(f"Cleared {count} history entries")
            return count
        except Exception as e:
            session.rollback()
            error_msg = f"Failed to clear history: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        finally:
            session.close()

    def remove_from_history(self, entry_id: str) -> bool:
        """
        Remove a specific entry from history.

        Args:
            entry_id: UUID of the history entry to remove

        Returns:
            True if removed successfully, False if not found

        Raises:
            DatabaseError: If the operation fails
        """
        session = self._get_session()
        try:
            entry = session.query(DownloadHistory).filter(DownloadHistory.id == entry_id).first()

            if not entry:
                return False

            session.delete(entry)
            session.commit()
            logger.info(f"Removed history entry: {entry_id}")
            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to remove history entry {entry_id}: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        finally:
            session.close()

    @property
    def max_concurrent(self) -> int:
        """Get the maximum concurrent downloads limit."""
        return self._max_concurrent

    def set_max_concurrent(self, count: int) -> None:
        """
        Set maximum concurrent downloads.

        Args:
            count: Maximum number of concurrent downloads (1-5)

        Raises:
            ValueError: If count is outside valid range
        """
        if count < self.MIN_CONCURRENT or count > self.MAX_CONCURRENT:
            raise ValueError(f"Concurrent downloads must be between {self.MIN_CONCURRENT} and {self.MAX_CONCURRENT}")

        self._max_concurrent = count
        logger.info(f"Set max concurrent downloads to {count}")

    def get_active_download_count(self) -> int:
        """
        Get the number of currently active downloads.

        Returns:
            Number of active downloads
        """
        with self._lock:
            return len(self._active_downloads)

    def can_start_download(self) -> bool:
        """
        Check if a new download can be started.

        Returns:
            True if under the concurrent limit, False otherwise
        """
        return self.get_active_download_count() < self._max_concurrent

    def start_download(self, item_id: str) -> bool:
        """
        Mark a download as started (active).

        Transitions the item from PENDING to DOWNLOADING and tracks it
        as an active download.

        Args:
            item_id: UUID of the queue item to start

        Returns:
            True if started successfully, False otherwise

        Raises:
            QueueError: If the operation fails
        """
        if not self.can_start_download():
            logger.warning(f"Cannot start download {item_id}: concurrent limit reached")
            return False

        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                logger.warning(f"Queue item not found: {item_id}")
                return False

            if not item.can_transition_to(DownloadStatus.DOWNLOADING):
                logger.warning(f"Cannot start item {item_id}: current status is {item.status.value}")
                return False

            item.transition_to(DownloadStatus.DOWNLOADING)
            item.updated_at = datetime.utcnow()
            session.commit()

            with self._lock:
                self._active_downloads[item_id] = True

            logger.info(f"Started download: {item_id}")
            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to start download {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def complete_download(
        self,
        item_id: str,
        file_path: str,
        file_size: int | None = None,
    ) -> bool:
        """
        Mark a download as completed and add to history.

        Transitions the item to COMPLETED status, removes from active tracking,
        and creates a history entry.

        Args:
            item_id: UUID of the queue item
            file_path: Path to the downloaded file
            file_size: Size of the downloaded file

        Returns:
            True if completed successfully, False otherwise

        Raises:
            QueueError: If the operation fails
        """
        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                logger.warning(f"Queue item not found: {item_id}")
                return False

            if not item.can_transition_to(DownloadStatus.COMPLETED):
                logger.warning(f"Cannot complete item {item_id}: current status is {item.status.value}")
                return False

            # Update queue item
            item.transition_to(DownloadStatus.COMPLETED)
            item.progress = 100.0
            item.updated_at = datetime.utcnow()

            # Create history entry
            history_item = DownloadHistory(
                id=str(uuid.uuid4()),
                url=item.url,
                title=item.title or "Unknown",
                file_path=file_path,
                file_size=file_size,
                format_id=item.format_id,
                downloaded_at=datetime.utcnow(),
                status="completed",
            )
            session.add(history_item)

            session.commit()

            # Update active downloads tracking
            with self._lock:
                if item_id in self._active_downloads:
                    del self._active_downloads[item_id]

            logger.info(f"Completed download: {item_id}")

            # Trigger auto-start of next queued item
            self._auto_start_next()

            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to complete download {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def fail_download(self, item_id: str, error_message: str) -> bool:
        """
        Mark a download as failed.

        Transitions the item to FAILED status and records the error message.

        Args:
            item_id: UUID of the queue item
            error_message: Error message describing the failure

        Returns:
            True if marked as failed successfully, False otherwise

        Raises:
            QueueError: If the operation fails
        """
        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                logger.warning(f"Queue item not found: {item_id}")
                return False

            if not item.can_transition_to(DownloadStatus.FAILED):
                logger.warning(f"Cannot fail item {item_id}: current status is {item.status.value}")
                return False

            item.transition_to(DownloadStatus.FAILED)
            item.error_message = error_message
            item.updated_at = datetime.utcnow()
            session.commit()

            # Update active downloads tracking
            with self._lock:
                if item_id in self._active_downloads:
                    del self._active_downloads[item_id]

            logger.info(f"Failed download: {item_id} - {error_message}")

            # Trigger auto-start of next queued item
            self._auto_start_next()

            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to mark download as failed {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def _auto_start_next(self) -> None:
        """
        Automatically start the next queued item if under concurrent limit.

        This is called after a download completes or fails to keep the
        download pipeline full.
        """
        if not self.can_start_download():
            return

        session = self._get_session()
        try:
            # Find next pending item
            next_item = (
                session.query(QueueItem)
                .filter(QueueItem.status == DownloadStatus.PENDING)
                .order_by(QueueItem.position)
                .first()
            )

            if next_item:
                # Start the download (this will be handled by the download executor)
                if self._on_download_complete:
                    self._on_download_complete(next_item.id)

        except Exception as e:
            logger.warning(f"Failed to auto-start next download: {e}")
        finally:
            session.close()

    def set_on_download_complete_callback(
        self,
        callback: Callable[[str], None] | None,
    ) -> None:
        """
        Set callback for when a download slot becomes available.

        Args:
            callback: Function to call with the next item ID to start
        """
        self._on_download_complete = callback

    def update_progress(self, item_id: str, progress: float) -> bool:
        """
        Update the progress of a download.

        Args:
            item_id: UUID of the queue item
            progress: Progress percentage (0-100)

        Returns:
            True if updated successfully, False otherwise
        """
        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                return False

            item.progress = max(0.0, min(100.0, progress))
            item.updated_at = datetime.utcnow()
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            logger.warning(f"Failed to update progress for {item_id}: {e}")
            return False
        finally:
            session.close()

    def restore_queue(self) -> list[QueueItem]:
        """
        Restore queue state on application startup.

        Loads all non-terminal queue items from the database and resets
        any items that were in DOWNLOADING state (interrupted downloads)
        back to PENDING.

        Returns:
            List of restored QueueItem objects

        Raises:
            QueueError: If restoration fails
        """
        session = self._get_session()
        try:
            # Get all non-terminal items
            items = (
                session.query(QueueItem)
                .filter(
                    QueueItem.status.notin_(
                        [
                            DownloadStatus.COMPLETED,
                            DownloadStatus.CANCELLED,
                        ]
                    )
                )
                .order_by(QueueItem.position)
                .all()
            )

            # Reset any DOWNLOADING items to PENDING (interrupted downloads)
            for item in items:
                if item.status == DownloadStatus.DOWNLOADING:
                    item.status = DownloadStatus.PENDING
                    item.updated_at = datetime.utcnow()
                    logger.info(f"Reset interrupted download to pending: {item.id}")

            session.commit()

            # Detach from session
            for item in items:
                session.expunge(item)

            logger.info(f"Restored {len(items)} queue items")
            return items

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to restore queue: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def get_queue_state(self) -> dict:
        """
        Get the current queue state as a dictionary.

        Returns:
            Dictionary containing queue state information
        """
        session = self._get_session()
        try:
            # Count items by status
            status_counts = {}
            for status in DownloadStatus:
                count = session.query(func.count(QueueItem.id)).filter(QueueItem.status == status).scalar()
                status_counts[status.value] = count or 0

            total = sum(status_counts.values())

            return {
                "total_items": total,
                "status_counts": status_counts,
                "active_downloads": self.get_active_download_count(),
                "max_concurrent": self._max_concurrent,
                "can_start_more": self.can_start_download(),
            }

        except Exception as e:
            logger.error(f"Failed to get queue state: {e}")
            return {
                "total_items": 0,
                "status_counts": {},
                "active_downloads": 0,
                "max_concurrent": self._max_concurrent,
                "can_start_more": True,
            }
        finally:
            session.close()

    def retry_failed(self, item_id: str) -> bool:
        """
        Retry a failed download.

        Resets a FAILED item back to PENDING status.

        Args:
            item_id: UUID of the failed queue item

        Returns:
            True if reset successfully, False otherwise

        Raises:
            QueueError: If the operation fails
        """
        session = self._get_session()
        try:
            item = session.query(QueueItem).filter(QueueItem.id == item_id).first()

            if not item:
                logger.warning(f"Queue item not found: {item_id}")
                return False

            if item.status != DownloadStatus.FAILED:
                logger.warning(f"Cannot retry item {item_id}: status is {item.status.value}")
                return False

            # Reset to pending
            item.status = DownloadStatus.PENDING
            item.progress = 0.0
            item.error_message = None
            item.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"Reset failed download for retry: {item_id}")
            return True

        except Exception as e:
            session.rollback()
            error_msg = f"Failed to retry download {item_id}: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()

    def clear_completed(self) -> int:
        """
        Remove all completed and cancelled items from the queue.

        Returns:
            Number of items removed

        Raises:
            QueueError: If the operation fails
        """
        session = self._get_session()
        try:
            count = (
                session.query(QueueItem)
                .filter(
                    QueueItem.status.in_(
                        [
                            DownloadStatus.COMPLETED,
                            DownloadStatus.CANCELLED,
                        ]
                    )
                )
                .delete(synchronize_session=False)
            )
            session.commit()
            logger.info(f"Cleared {count} completed/cancelled items from queue")
            return count
        except Exception as e:
            session.rollback()
            error_msg = f"Failed to clear completed items: {e}"
            logger.error(error_msg)
            raise QueueError(error_msg) from e
        finally:
            session.close()
