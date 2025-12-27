"""Unit tests for feedback.py module."""

import pytest
from unittest.mock import patch, MagicMock


class TestFeedbackService:
    """Tests for FeedbackService class."""

    def test_init(self):
        """Test FeedbackService initialization."""
        from src.farmer_cli.services.feedback import FeedbackService

        service = FeedbackService()

        assert service is not None

    @patch("src.farmer_cli.services.feedback.console")
    def test_show_success(self, mock_console):
        """Test show_success displays success message."""
        from src.farmer_cli.services.feedback import FeedbackService

        service = FeedbackService()
        service.show_success("Operation completed")

        mock_console.print.assert_called()

    @patch("src.farmer_cli.services.feedback.console")
    def test_show_error(self, mock_console):
        """Test show_error displays error message."""
        from src.farmer_cli.services.feedback import FeedbackService

        service = FeedbackService()
        service.show_error("Operation failed")

        mock_console.print.assert_called()

    @patch("src.farmer_cli.services.feedback.console")
    def test_show_warning(self, mock_console):
        """Test show_warning displays warning message."""
        from src.farmer_cli.services.feedback import FeedbackService

        service = FeedbackService()
        service.show_warning("Warning message")

        mock_console.print.assert_called()

    @patch("src.farmer_cli.services.feedback.console")
    def test_show_info(self, mock_console):
        """Test show_info displays info message."""
        from src.farmer_cli.services.feedback import FeedbackService

        service = FeedbackService()
        service.show_info("Information message")

        mock_console.print.assert_called()

    @patch("src.farmer_cli.services.feedback.console")
    def test_show_progress(self, mock_console):
        """Test show_progress displays progress."""
        from src.farmer_cli.services.feedback import FeedbackService

        service = FeedbackService()
        service.show_progress("Processing", 50, 100)

        mock_console.print.assert_called()

    @patch("src.farmer_cli.services.feedback.console")
    def test_clear(self, mock_console):
        """Test clear clears the console."""
        from src.farmer_cli.services.feedback import FeedbackService

        service = FeedbackService()
        service.clear()

        mock_console.clear.assert_called()


class TestShowNotification:
    """Tests for show_notification function."""

    @patch("src.farmer_cli.services.feedback.console")
    def test_show_notification(self, mock_console):
        """Test show_notification displays notification."""
        from src.farmer_cli.services.feedback import show_notification

        show_notification("Test notification")

        mock_console.print.assert_called()

    @patch("src.farmer_cli.services.feedback.console")
    def test_show_notification_with_type(self, mock_console):
        """Test show_notification with notification type."""
        from src.farmer_cli.services.feedback import show_notification

        show_notification("Test notification", notification_type="success")

        mock_console.print.assert_called()


class TestShowSpinner:
    """Tests for show_spinner context manager."""

    @patch("src.farmer_cli.services.feedback.console")
    def test_show_spinner(self, mock_console):
        """Test show_spinner context manager."""
        from src.farmer_cli.services.feedback import show_spinner

        with show_spinner("Loading"):
            pass

        # Should complete without error
