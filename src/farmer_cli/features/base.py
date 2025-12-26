"""
Base feature class for Farmer CLI.

This module provides the abstract base class for all features
in the application.
"""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Optional

from ..ui.console import console


class BaseFeature(ABC):
    """
    Abstract base class for all features.

    All features should inherit from this class and implement
    the required methods.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize the feature.

        Args:
            name: Feature name
            description: Feature description
        """
        self.name = name
        self.description = description
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize the feature.

        This method is called once before the feature is first used.
        Override this method to perform any initialization tasks.
        """
        self._initialized = True

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """
        Execute the feature.

        This is the main entry point for the feature functionality.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Feature-specific return value
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleanup the feature.

        This method is called when the feature is no longer needed.
        Override this method to perform any cleanup tasks.
        """
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """
        Make the feature callable.

        This ensures the feature is initialized before execution.
        """
        if not self._initialized:
            self.initialize()

        try:
            return self.execute(*args, **kwargs)
        except Exception as e:
            console.print(f"[bold red]Error in {self.name}: {e}[/bold red]")
            raise

    def __str__(self) -> str:
        """String representation of the feature."""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"{self.__class__.__name__}(name='{self.name}', description='{self.description}')"
