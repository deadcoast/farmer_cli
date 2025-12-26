"""
Async task management for Farmer CLI.

This module provides utilities for managing asynchronous operations
within the application.
"""

import asyncio
import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

from rich.live import Live
from rich.progress import Progress

from ..ui.console import console


logger = logging.getLogger(__name__)


class AsyncTaskManager:
    """
    Manages asynchronous tasks within the application.

    Provides utilities for running async operations with progress
    tracking and proper error handling.
    """

    def __init__(self):
        """Initialize the async task manager."""
        self.running_tasks: Dict[str, asyncio.Task] = {}

    async def run_with_progress(
        self,
        task_func: Callable,
        task_name: str = "Processing",
        total: Optional[int] = None,
        live: Optional[Live] = None,
    ) -> Any:
        """
        Run an async task with progress tracking.

        Args:
            task_func: Async function to run
            task_name: Name for progress display
            total: Total steps for progress (None for indeterminate)
            live: Optional Live instance for progress display

        Returns:
            Result from the task function
        """
        if live:
            # Update existing live display
            try:
                return await task_func()
            except Exception as e:
                logger.error(f"Error in async task {task_name}: {e}")
                raise
        else:
            # Create new progress display
            with Progress(console=console) as progress:
                task_id = progress.add_task(task_name, total=total)

                try:
                    if current_task := asyncio.current_task():
                        self.running_tasks[task_name] = current_task

                    # Run the task
                    result = await task_func()

                    # Mark complete
                    progress.update(task_id, completed=total or 100)

                    return result

                except Exception as e:
                    logger.error(f"Error in async task {task_name}: {e}")
                    raise
                finally:
                    # Clean up task reference
                    self.running_tasks.pop(task_name, None)

    def cancel_task(self, task_name: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_name: Name of the task to cancel

        Returns:
            True if task was cancelled, False if not found
        """
        task = self.running_tasks.get(task_name)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled task: {task_name}")
            return True
        return False

    def cancel_all_tasks(self) -> int:
        """
        Cancel all running tasks.

        Returns:
            Number of tasks cancelled
        """
        cancelled = 0
        for task_name, task in list(self.running_tasks.items()):
            if not task.done():
                task.cancel()
                cancelled += 1
                logger.info(f"Cancelled task: {task_name}")

        self.running_tasks.clear()
        return cancelled

    async def gather_with_timeout(self, *tasks: asyncio.Task, timeout: Optional[float] = None) -> list:
        """
        Gather multiple tasks with optional timeout.

        Args:
            *tasks: Tasks to gather
            timeout: Optional timeout in seconds

        Returns:
            List of task results

        Raises:
            asyncio.TimeoutError: If timeout is exceeded
        """
        if timeout:
            return await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
        else:
            return await asyncio.gather(*tasks, return_exceptions=True)


# Example async task for demonstration
async def example_async_task(duration: int = 3) -> str:
    """
    Example async task that simulates work.

    Args:
        duration: Duration to simulate work

    Returns:
        Completion message
    """
    await asyncio.sleep(duration)
    return f"Task completed after {duration} seconds"
