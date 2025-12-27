"""Unit tests for async_tasks.py module."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock


class TestAsyncTaskManager:
    """Tests for AsyncTaskManager class."""

    def test_init(self):
        """Test AsyncTaskManager initialization."""
        from src.farmer_cli.services.async_tasks import AsyncTaskManager

        manager = AsyncTaskManager()

        assert manager.running_tasks == {}

    def test_cancel_task_not_found(self):
        """Test cancel_task returns False for non-existent task."""
        from src.farmer_cli.services.async_tasks import AsyncTaskManager

        manager = AsyncTaskManager()

        result = manager.cancel_task("nonexistent")

        assert result is False

    def test_cancel_task_success(self):
        """Test cancel_task cancels running task."""
        from src.farmer_cli.services.async_tasks import AsyncTaskManager

        manager = AsyncTaskManager()
        mock_task = MagicMock()
        mock_task.done.return_value = False
        manager.running_tasks["test_task"] = mock_task

        result = manager.cancel_task("test_task")

        assert result is True
        mock_task.cancel.assert_called_once()

    def test_cancel_task_already_done(self):
        """Test cancel_task returns False for completed task."""
        from src.farmer_cli.services.async_tasks import AsyncTaskManager

        manager = AsyncTaskManager()
        mock_task = MagicMock()
        mock_task.done.return_value = True
        manager.running_tasks["test_task"] = mock_task

        result = manager.cancel_task("test_task")

        assert result is False

    def test_cancel_all_tasks(self):
        """Test cancel_all_tasks cancels all running tasks."""
        from src.farmer_cli.services.async_tasks import AsyncTaskManager

        manager = AsyncTaskManager()

        mock_task1 = MagicMock()
        mock_task1.done.return_value = False
        mock_task2 = MagicMock()
        mock_task2.done.return_value = False
        mock_task3 = MagicMock()
        mock_task3.done.return_value = True  # Already done

        manager.running_tasks = {
            "task1": mock_task1,
            "task2": mock_task2,
            "task3": mock_task3,
        }

        cancelled = manager.cancel_all_tasks()

        assert cancelled == 2
        mock_task1.cancel.assert_called_once()
        mock_task2.cancel.assert_called_once()
        mock_task3.cancel.assert_not_called()
        assert manager.running_tasks == {}

    def test_run_with_progress_with_live_sync(self):
        """Test run_with_progress with live display using event loop."""
        from src.farmer_cli.services.async_tasks import AsyncTaskManager

        manager = AsyncTaskManager()
        mock_live = MagicMock()

        async def sample_task():
            return "result"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                manager.run_with_progress(sample_task, "Test Task", live=mock_live)
            )
        finally:
            loop.close()

        assert result == "result"

    def test_run_with_progress_handles_error_sync(self):
        """Test run_with_progress handles errors using event loop."""
        from src.farmer_cli.services.async_tasks import AsyncTaskManager

        manager = AsyncTaskManager()
        mock_live = MagicMock()

        async def failing_task():
            raise ValueError("test error")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            with pytest.raises(ValueError, match="test error"):
                loop.run_until_complete(
                    manager.run_with_progress(failing_task, "Test Task", live=mock_live)
                )
        finally:
            loop.close()

    def test_gather_with_timeout_sync(self):
        """Test gather_with_timeout using event loop."""
        from src.farmer_cli.services.async_tasks import AsyncTaskManager

        manager = AsyncTaskManager()

        async def run_gather():
            async def task1():
                return 1

            async def task2():
                return 2

            return await manager.gather_with_timeout(
                asyncio.create_task(task1()),
                asyncio.create_task(task2())
            )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_gather())
        finally:
            loop.close()

        assert results == [1, 2]


class TestExampleAsyncTask:
    """Tests for example_async_task function."""

    def test_example_async_task_sync(self):
        """Test example_async_task completes using event loop."""
        from src.farmer_cli.services.async_tasks import example_async_task

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(example_async_task(duration=0))
        finally:
            loop.close()

        assert "completed" in result.lower()
        assert "0" in result
