"""Unit tests for feedback.py module."""

import pytest
import tempfile
from pathlib import Path


class TestFeedbackService:
    """Tests for FeedbackService class."""

    def test_init(self):
        """Test FeedbackService initialization."""
        from src.farmer_cli.services.feedback import FeedbackService

        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_file = Path(tmpdir) / "feedback.txt"
            service = FeedbackService(feedback_file=feedback_file)

            assert service is not None
            assert service.feedback_file == feedback_file

    def test_submit_feedback(self):
        """Test submitting feedback."""
        from src.farmer_cli.services.feedback import FeedbackService

        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_file = Path(tmpdir) / "feedback.txt"
            service = FeedbackService(feedback_file=feedback_file)

            result = service.submit("Test feedback")

            assert result is True
            assert feedback_file.exists()

    def test_submit_feedback_with_user(self):
        """Test submitting feedback with user."""
        from src.farmer_cli.services.feedback import FeedbackService

        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_file = Path(tmpdir) / "feedback.txt"
            service = FeedbackService(feedback_file=feedback_file)

            result = service.submit("Test feedback", user="testuser")

            assert result is True
            content = feedback_file.read_text()
            assert "testuser" in content

    def test_get_all_no_feedback(self):
        """Test getting all feedback when none exists."""
        from src.farmer_cli.services.feedback import FeedbackService

        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_file = Path(tmpdir) / "feedback.txt"
            service = FeedbackService(feedback_file=feedback_file)

            result = service.get_all()

            assert "No feedback" in result

    def test_get_all_with_feedback(self):
        """Test getting all feedback."""
        from src.farmer_cli.services.feedback import FeedbackService

        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_file = Path(tmpdir) / "feedback.txt"
            service = FeedbackService(feedback_file=feedback_file)

            service.submit("Test feedback 1")
            service.submit("Test feedback 2")

            result = service.get_all()

            assert "Test feedback 1" in result
            assert "Test feedback 2" in result

    def test_clear_feedback(self):
        """Test clearing feedback."""
        from src.farmer_cli.services.feedback import FeedbackService

        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_file = Path(tmpdir) / "feedback.txt"
            service = FeedbackService(feedback_file=feedback_file)

            service.submit("Test feedback")
            assert feedback_file.exists()

            result = service.clear()

            assert result is True
            assert not feedback_file.exists()

    def test_clear_no_feedback(self):
        """Test clearing when no feedback exists."""
        from src.farmer_cli.services.feedback import FeedbackService

        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_file = Path(tmpdir) / "feedback.txt"
            service = FeedbackService(feedback_file=feedback_file)

            result = service.clear()

            assert result is True


class TestGetFeedbackService:
    """Tests for get_feedback_service function."""

    def test_get_feedback_service(self):
        """Test getting global feedback service."""
        from src.farmer_cli.services.feedback import get_feedback_service, FeedbackService

        result = get_feedback_service()

        assert result is not None
        assert isinstance(result, FeedbackService)

    def test_get_feedback_service_singleton(self):
        """Test feedback service is singleton."""
        from src.farmer_cli.services.feedback import get_feedback_service

        service1 = get_feedback_service()
        service2 = get_feedback_service()

        assert service1 is service2
