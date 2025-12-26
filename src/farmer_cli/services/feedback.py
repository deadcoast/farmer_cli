"""
Feedback service for Farmer CLI.

This module handles user feedback collection and storage.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.constants import FEEDBACK_FILE
from ..ui.console import console
from ..ui.prompts import multiline_prompt


logger = logging.getLogger(__name__)


class FeedbackService:
    """
    Service for managing user feedback.

    Handles collecting, storing, and retrieving user feedback.
    """

    def __init__(self, feedback_file: Optional[Path] = None):
        """
        Initialize the feedback service.

        Args:
            feedback_file: Path to feedback file (defaults to FEEDBACK_FILE)
        """
        self.feedback_file = feedback_file or FEEDBACK_FILE

    def submit(self, feedback: str, user: Optional[str] = None) -> bool:
        """
        Submit user feedback.

        Args:
            feedback: Feedback text
            user: Optional username

        Returns:
            True if successful
        """
        try:
            # Ensure directory exists
            self.feedback_file.parent.mkdir(parents=True, exist_ok=True)

            # Format feedback entry
            timestamp = datetime.now().isoformat()
            entry = f"\n[{timestamp}]"
            if user:
                entry += f" User: {user}"
            entry += f"\n{feedback}\n{'=' * 60}\n"

            # Append to file
            with open(self.feedback_file, "a", encoding="utf-8") as f:
                f.write(entry)

            logger.info(f"Feedback submitted: {feedback[:50]}...")
            return True

        except IOError as e:
            logger.error(f"Failed to save feedback: {e}")
            return False

    def get_all(self) -> str:
        """
        Get all feedback.

        Returns:
            All feedback as string
        """
        if not self.feedback_file.exists():
            return "No feedback yet."

        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                return f.read()
        except IOError as e:
            logger.error(f"Failed to read feedback: {e}")
            return "Error reading feedback."

    def clear(self) -> bool:
        """
        Clear all feedback.

        Returns:
            True if successful
        """
        try:
            if self.feedback_file.exists():
                self.feedback_file.unlink()
            return True
        except OSError as e:
            logger.error(f"Failed to clear feedback: {e}")
            return False


# Global feedback service instance
_feedback_service: Optional[FeedbackService] = None


def get_feedback_service() -> FeedbackService:
    """Get the global feedback service instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service


def submit_feedback() -> None:
    """Interactive feedback submission."""
    console.clear()
    console.print("[bold magenta]Submit Feedback[/bold magenta]\n")

    console.print("We appreciate your feedback! Please share your thoughts, suggestions, or report any issues.\n")

    feedback = multiline_prompt("Your feedback", exit_message="Press Ctrl+D when finished")

    if not feedback.strip():
        console.print("[bold yellow]No feedback provided.[/bold yellow]")
        return

    service = get_feedback_service()
    if service.submit(feedback):
        console.print("\n[bold green]✓ Thank you for your feedback![/bold green]")
        console.print("Your feedback has been recorded and will help improve the application.")
    else:
        console.print("\n[bold red]Failed to save feedback. Please try again later.[/bold red]")

    console.input("\nPress Enter to continue...")
