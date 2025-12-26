"""
Decorators for Farmer CLI.

This module provides utility decorators for various purposes including
timing, retrying, caching, and logging.
"""

import functools
import logging
import time
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import TypeVar

from ..ui.console import console
from ..ui.prompts import confirm_prompt


logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def timer(func: F) -> F:
    """
    Decorator to time function execution.

    Args:
        func: Function to time

    Returns:
        Wrapped function
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            elapsed = end_time - start_time
            logger.debug(f"{func.__name__} took {elapsed:.4f} seconds")

    return wrapper  # type: ignore


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function execution on failure.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Backoff multiplier for delay

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Optional[Exception] = None

            def call_once() -> tuple[bool, Any, Optional[Exception]]:
                try:
                    return True, func(*args, **kwargs), None
                except Exception as e:
                    return False, None, e

            for attempt in range(max_attempts):
                ok, result, error = call_once()
                if ok:
                    return result
                last_exception = error
                if attempt < max_attempts - 1:
                    logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {error}")
                    time.sleep(current_delay)
                    current_delay *= backoff
                else:
                    logger.error(f"{func.__name__} failed after {max_attempts} attempts: {error}")

            if last_exception is not None:
                raise last_exception

        return wrapper  # type: ignore

    return decorator


def cached(ttl: Optional[float] = None):
    """
    Simple caching decorator with optional TTL.

    Args:
        ttl: Time to live in seconds (None for no expiration)

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        cache: Dict[str, Any] = {}
        cache_time: Dict[str, float] = {}

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key from arguments
            key = str(args) + str(sorted(kwargs.items()))

            # Check if cached value exists and is valid
            if key in cache and (ttl is None or time.time() - cache_time[key] < ttl):
                logger.debug(f"Cache hit for {func.__name__}")
                return cache[key]

            # Call function and cache result
            result = func(*args, **kwargs)
            cache[key] = result
            cache_time[key] = time.time()

            return result

        # Add cache clear method
        wrapper.clear_cache = lambda: (cache.clear(), cache_time.clear())  # type: ignore

        return wrapper  # type: ignore

    return decorator


def require_confirmation(message: str = "Are you sure you want to proceed?"):
    """
    Decorator to require user confirmation before executing function.

    Args:
        message: Confirmation message

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if confirm_prompt(message):
                return func(*args, **kwargs)
            console.print("[bold yellow]Operation cancelled by user.[/bold yellow]")
            return None

        return wrapper  # type: ignore

    return decorator


def log_execution(level: int = logging.INFO, log_args: bool = True, log_result: bool = False):
    """
    Decorator to log function execution.

    Args:
        level: Logging level
        log_args: Whether to log arguments
        log_result: Whether to log result

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Log function call
            msg = f"Calling {func.__name__}"
            if log_args:
                msg += f" with args={args}, kwargs={kwargs}"
            logger.log(level, msg)

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Log result if requested
                if log_result:
                    logger.log(level, f"{func.__name__} returned: {result}")

                return result

            except Exception as e:
                logger.error(f"{func.__name__} raised exception: {e}")
                raise

        return wrapper  # type: ignore

    return decorator
