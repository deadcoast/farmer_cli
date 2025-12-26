"""
Database management and initialization.

This module handles all database-related operations including initialization,
session management, and connection handling for the Farmer CLI application.
"""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from typing import Optional

from config.settings import settings
from exceptions import DatabaseError
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker


logger = logging.getLogger(__name__)


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

                # Add trigger for updated_at
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

                conn.commit()

            # Import models to register them with SQLAlchemy
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
