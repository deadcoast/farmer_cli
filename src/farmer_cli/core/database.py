"""
Database management and initialization.

This module handles all database-related operations including initialization,
session management, connection handling, backup/restore, and integrity validation
for the Farmer CLI application.
"""

import logging
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from exceptions import DatabaseError


logger = logging.getLogger(__name__)


# Expected table schemas for integrity validation
EXPECTED_TABLES = {
    "users": {
        "columns": ["id", "name", "preferences", "created_at", "updated_at"],
        "required_columns": ["id", "name"],
    },
    "download_queue": {
        "columns": [
            "id", "url", "title", "format_id", "output_path", "status",
            "progress", "position", "error_message", "created_at", "updated_at"
        ],
        "required_columns": ["id", "url", "output_path", "status", "progress", "position"],
    },
    "download_history": {
        "columns": [
            "id", "url", "title", "file_path", "file_size", "format_id",
            "duration", "uploader", "downloaded_at", "status", "thumbnail_url",
            "description", "created_at", "updated_at"
        ],
        "required_columns": ["id", "url", "title", "file_path", "status"],
    },
}


class DatabaseManager:
    """
    Manages database connections and operations.

    This class provides a centralized way to handle database initialization,
    session management, and cleanup operations.
    """

    def __init__(self, database_path: Optional[Path] = None):
        """
        Initialize the database manager.

        Args:
            database_path: Path to the database file (defaults to settings)
        """
        self.database_path = database_path or settings.database_path
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    @property
    def engine(self) -> Engine:
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = create_engine(f"sqlite:///{self.database_path}", echo=False, future=True)
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        return self._session_factory

    def initialize(self) -> None:
        """
        Initialize the database with required tables.

        Raises:
            DatabaseError: If initialization fails
        """
        try:
            logger.info(f"Initializing database at {self.database_path}")

            # Ensure directory exists
            self.database_path.parent.mkdir(parents=True, exist_ok=True)

            # Create tables using raw SQL for initial setup
            with sqlite3.connect(str(self.database_path)) as conn:
                cursor = conn.cursor()

                # Users table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        preferences TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Add trigger for updated_at on users
                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS update_users_timestamp
                    AFTER UPDATE ON users
                    BEGIN
                        UPDATE users SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = NEW.id;
                    END
                """
                )

                # Download queue table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS download_queue (
                        id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        title TEXT,
                        format_id TEXT,
                        output_path TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        progress REAL NOT NULL DEFAULT 0.0,
                        position INTEGER NOT NULL,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Add indexes for download_queue
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS ix_download_queue_status
                    ON download_queue (status)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS ix_download_queue_position
                    ON download_queue (position)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS ix_download_queue_status_position
                    ON download_queue (status, position)
                """
                )

                # Add trigger for updated_at on download_queue
                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS update_download_queue_timestamp
                    AFTER UPDATE ON download_queue
                    BEGIN
                        UPDATE download_queue SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = NEW.id;
                    END
                """
                )

                # Download history table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS download_history (
                        id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        title TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        format_id TEXT,
                        duration INTEGER,
                        uploader TEXT,
                        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT NOT NULL DEFAULT 'completed',
                        thumbnail_url TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Add indexes for download_history
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS ix_download_history_url
                    ON download_history (url)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS ix_download_history_downloaded_at
                    ON download_history (downloaded_at)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS ix_download_history_status
                    ON download_history (status)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS ix_download_history_title
                    ON download_history (title)
                """
                )

                # Add trigger for updated_at on download_history
                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS update_download_history_timestamp
                    AFTER UPDATE ON download_history
                    BEGIN
                        UPDATE download_history SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = NEW.id;
                    END
                """
                )

                conn.commit()

            # Import models to register them with SQLAlchemy
            from ..models import DownloadHistory  # noqa: F401  # type: ignore[import]
            from ..models import QueueItem  # noqa: F401  # type: ignore[import]
            from ..models import User  # noqa: F401  # type: ignore[import]

            # Create all tables using SQLAlchemy
            from ..models.base import Base

            Base.metadata.create_all(self.engine)

            logger.info("Database initialized successfully")

        except Exception as e:
            error_msg = f"Database initialization failed: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for database operations.

        Yields:
            Session: Database session

        Example:
            with db_manager.session_scope() as session:
                user = User(name="John")
                session.add(user)
                # Automatically commits on success, rolls back on error
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close the database connection."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None

    def backup_database(self, backup_path: Optional[Path] = None) -> Path:
        """
        Create a backup of the database.

        Parameters
        ----------
        backup_path : Path | None
            Path for the backup file. If None, creates a timestamped backup
            in the same directory as the database.

        Returns
        -------
        Path
            Path to the created backup file.

        Raises
        ------
        DatabaseError
            If backup fails.
        """
        try:
            if not self.database_path.exists():
                raise DatabaseError(f"Database file does not exist: {self.database_path}")

            # Generate backup path if not provided
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{self.database_path.stem}_backup_{timestamp}.db"
                backup_path = self.database_path.parent / backup_name

            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Close any existing connections to ensure data is flushed
            if self._engine:
                self._engine.dispose()
                self._engine = None
                self._session_factory = None

            # Use SQLite backup API for safe backup
            with sqlite3.connect(str(self.database_path)) as source_conn:
                with sqlite3.connect(str(backup_path)) as backup_conn:
                    source_conn.backup(backup_conn)

            logger.info(f"Database backed up to {backup_path}")
            return backup_path

        except sqlite3.Error as e:
            error_msg = f"Database backup failed: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        except OSError as e:
            error_msg = f"File operation failed during backup: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def restore_database(self, backup_path: Path) -> None:
        """
        Restore the database from a backup.

        Parameters
        ----------
        backup_path : Path
            Path to the backup file to restore from.

        Raises
        ------
        DatabaseError
            If restore fails or backup file doesn't exist.
        """
        try:
            if not backup_path.exists():
                raise DatabaseError(f"Backup file does not exist: {backup_path}")

            # Validate backup file is a valid SQLite database
            if not self._is_valid_sqlite_file(backup_path):
                raise DatabaseError(f"Invalid SQLite database file: {backup_path}")

            # Close any existing connections
            if self._engine:
                self._engine.dispose()
                self._engine = None
                self._session_factory = None

            # Ensure database directory exists
            self.database_path.parent.mkdir(parents=True, exist_ok=True)

            # Create a temporary backup of current database if it exists
            temp_backup = None
            if self.database_path.exists():
                temp_backup = self.database_path.with_suffix(".db.tmp")
                shutil.copy2(self.database_path, temp_backup)

            try:
                # Restore from backup using SQLite backup API
                with sqlite3.connect(str(backup_path)) as source_conn:
                    with sqlite3.connect(str(self.database_path)) as dest_conn:
                        source_conn.backup(dest_conn)

                # Remove temporary backup on success
                if temp_backup and temp_backup.exists():
                    temp_backup.unlink()

                logger.info(f"Database restored from {backup_path}")

            except Exception as e:
                # Restore original database on failure
                if temp_backup and temp_backup.exists():
                    shutil.copy2(temp_backup, self.database_path)
                    temp_backup.unlink()
                raise e

        except sqlite3.Error as e:
            error_msg = f"Database restore failed: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        except OSError as e:
            error_msg = f"File operation failed during restore: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _is_valid_sqlite_file(self, file_path: Path) -> bool:
        """
        Check if a file is a valid SQLite database.

        Parameters
        ----------
        file_path : Path
            Path to the file to check.

        Returns
        -------
        bool
            True if the file is a valid SQLite database.
        """
        try:
            with sqlite3.connect(str(file_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                return True
        except sqlite3.Error:
            return False

    def validate_integrity(self) -> tuple[bool, list[str]]:
        """
        Validate database integrity on startup.

        Checks table existence, schema validity, and foreign key constraints.

        Returns
        -------
        tuple[bool, list[str]]
            A tuple of (is_valid, list_of_issues).
            is_valid is True if database passes all checks.
            list_of_issues contains descriptions of any problems found.

        Raises
        ------
        DatabaseError
            If database file doesn't exist or can't be accessed.
        """
        issues: list[str] = []

        try:
            if not self.database_path.exists():
                return False, ["Database file does not exist"]

            # Check SQLite integrity
            with sqlite3.connect(str(self.database_path)) as conn:
                cursor = conn.cursor()

                # Run SQLite integrity check
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()
                if integrity_result[0] != "ok":
                    issues.append(f"SQLite integrity check failed: {integrity_result[0]}")

                # Check foreign key constraints
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                if fk_violations:
                    issues.append(
                        f"Foreign key constraint violations: {len(fk_violations)} found"
                    )

            # Check table existence and schema using SQLAlchemy
            inspector = inspect(self.engine)
            existing_tables = set(inspector.get_table_names())

            for table_name, schema_info in EXPECTED_TABLES.items():
                if table_name not in existing_tables:
                    issues.append(f"Missing table: {table_name}")
                    continue

                # Check required columns exist
                columns = {col["name"] for col in inspector.get_columns(table_name)}
                for required_col in schema_info["required_columns"]:
                    if required_col not in columns:
                        issues.append(
                            f"Missing required column '{required_col}' in table '{table_name}'"
                        )

            is_valid = len(issues) == 0
            if is_valid:
                logger.info("Database integrity validation passed")
            else:
                logger.warning(f"Database integrity issues found: {issues}")

            return is_valid, issues

        except sqlite3.Error as e:
            error_msg = f"Database integrity check failed: {e}"
            logger.error(error_msg)
            return False, [error_msg]
        except Exception as e:
            error_msg = f"Unexpected error during integrity check: {e}"
            logger.error(error_msg)
            return False, [error_msg]

    def repair_database(self) -> bool:
        """
        Attempt to repair database issues.

        This method tries to fix common issues like missing tables
        by re-initializing the database schema.

        Returns
        -------
        bool
            True if repair was successful.

        Raises
        ------
        DatabaseError
            If repair fails.
        """
        try:
            logger.info("Attempting database repair...")

            # Re-initialize to create any missing tables
            self.initialize()

            # Validate again
            is_valid, issues = self.validate_integrity()

            if is_valid:
                logger.info("Database repair successful")
                return True
            else:
                logger.warning(f"Database repair incomplete, remaining issues: {issues}")
                return False

        except Exception as e:
            error_msg = f"Database repair failed: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.

    Returns:
        DatabaseManager: The database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Get a database session using the global database manager.

    Yields:
        Session: Database session

    Example:
        with get_session() as session:
            users = session.query(User).all()
    """
    db_manager = get_database_manager()
    with db_manager.session_scope() as session:
        yield session
