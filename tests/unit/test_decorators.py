"""Unit tests for decorators.py module."""

import pytest
import time
import logging
from unittest.mock import patch, MagicMock


class TestTimerDecorator:
    """Tests for timer decorator."""

    def test_timer_logs_execution_time(self, caplog):
        """Test timer decorator logs execution time."""
        from src.farmer_cli.utils.decorators import timer

        @timer
        def sample_function():
            return "result"

        with caplog.at_level(logging.DEBUG):
            result = sample_function()

        assert result == "result"

    def test_timer_preserves_function_name(self):
        """Test timer preserves function name."""
        from src.farmer_cli.utils.decorators import timer

        @timer
        def sample_function():
            pass

        assert sample_function.__name__ == "sample_function"

    def test_timer_handles_exception(self):
        """Test timer handles exceptions properly."""
        from src.farmer_cli.utils.decorators import timer

        @timer
        def failing_function():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_function()


class TestRetryDecorator:
    """Tests for retry decorator."""

    def test_retry_succeeds_first_try(self):
        """Test retry succeeds on first try."""
        from src.farmer_cli.utils.decorators import retry

        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()

        assert result == "success"
        assert call_count == 1

    def test_retry_succeeds_after_failures(self):
        """Test retry succeeds after initial failures."""
        from src.farmer_cli.utils.decorators import retry

        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary error")
            return "success"

        result = eventually_succeeds()

        assert result == "success"
        assert call_count == 3

    def test_retry_fails_after_max_attempts(self):
        """Test retry raises after max attempts."""
        from src.farmer_cli.utils.decorators import retry

        @retry(max_attempts=2, delay=0.01)
        def always_fails():
            raise ValueError("permanent error")

        with pytest.raises(ValueError, match="permanent error"):
            always_fails()

    def test_retry_with_backoff(self):
        """Test retry uses backoff multiplier."""
        from src.farmer_cli.utils.decorators import retry

        call_times = []

        @retry(max_attempts=3, delay=0.01, backoff=2.0)
        def track_timing():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("error")
            return "success"

        result = track_timing()

        assert result == "success"
        assert len(call_times) == 3


class TestCachedDecorator:
    """Tests for cached decorator."""

    def test_cached_returns_cached_value(self):
        """Test cached returns cached value on second call."""
        from src.farmer_cli.utils.decorators import cached

        call_count = 0

        @cached()
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1

    def test_cached_different_args(self):
        """Test cached calls function for different args."""
        from src.farmer_cli.utils.decorators import cached

        call_count = 0

        @cached()
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count == 2

    def test_cached_with_ttl_expires(self):
        """Test cached value expires after TTL."""
        from src.farmer_cli.utils.decorators import cached

        call_count = 0

        @cached(ttl=0.01)
        def expensive_function():
            nonlocal call_count
            call_count += 1
            return "result"

        result1 = expensive_function()
        time.sleep(0.02)
        result2 = expensive_function()

        assert result1 == "result"
        assert result2 == "result"
        assert call_count == 2

    def test_cached_clear_cache(self):
        """Test cached clear_cache method."""
        from src.farmer_cli.utils.decorators import cached

        call_count = 0

        @cached()
        def expensive_function():
            nonlocal call_count
            call_count += 1
            return "result"

        expensive_function()
        expensive_function.clear_cache()
        expensive_function()

        assert call_count == 2


class TestRequireConfirmationDecorator:
    """Tests for require_confirmation decorator."""

    @patch("src.farmer_cli.utils.decorators.confirm_prompt")
    def test_require_confirmation_proceeds_on_yes(self, mock_confirm):
        """Test function executes when user confirms."""
        from src.farmer_cli.utils.decorators import require_confirmation

        mock_confirm.return_value = True

        @require_confirmation("Are you sure?")
        def protected_function():
            return "executed"

        result = protected_function()

        assert result == "executed"
        mock_confirm.assert_called_once_with("Are you sure?")

    @patch("src.farmer_cli.utils.decorators.console")
    @patch("src.farmer_cli.utils.decorators.confirm_prompt")
    def test_require_confirmation_cancels_on_no(self, mock_confirm, mock_console):
        """Test function is cancelled when user declines."""
        from src.farmer_cli.utils.decorators import require_confirmation

        mock_confirm.return_value = False

        @require_confirmation("Are you sure?")
        def protected_function():
            return "executed"

        result = protected_function()

        assert result is None
        mock_console.print.assert_called()


class TestLogExecutionDecorator:
    """Tests for log_execution decorator."""

    def test_log_execution_logs_call(self, caplog):
        """Test log_execution logs function call."""
        from src.farmer_cli.utils.decorators import log_execution

        @log_execution(level=logging.INFO, log_args=True)
        def sample_function(x, y):
            return x + y

        with caplog.at_level(logging.INFO):
            result = sample_function(1, 2)

        assert result == 3

    def test_log_execution_logs_result(self, caplog):
        """Test log_execution logs result when requested."""
        from src.farmer_cli.utils.decorators import log_execution

        @log_execution(level=logging.INFO, log_result=True)
        def sample_function():
            return "result"

        with caplog.at_level(logging.INFO):
            result = sample_function()

        assert result == "result"

    def test_log_execution_logs_exception(self, caplog):
        """Test log_execution logs exceptions."""
        from src.farmer_cli.utils.decorators import log_execution

        @log_execution(level=logging.INFO)
        def failing_function():
            raise ValueError("test error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_function()
