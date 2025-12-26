# Farmer CLI Architecture

## Overview

Farmer CLI has been refactored from a monolithic structure into a modular, maintainable architecture following the Single Responsibility Principle. The application is organized into distinct modules, each handling a specific aspect of functionality.

## Directory Structure

```text
src/farmer_cli/
├── __init__.py # Package initialization and exports
├── __main__.py # Entry point for python -m farmer_cli
├── core/ # Core application logic
│   ├── __init__.py
│   ├── app.py # Main application class
│   ├── constants.py # Application constants
│   └── database.py # Database management
├── models/ # Database models
│   ├── __init__.py
│   ├── base.py # SQLAlchemy base model
│   └── user.py # User model
├── ui/ # User interface components
│   ├── __init__.py
│   ├── console.py # Rich console setup
│   ├── menu.py # Menu system
│   ├── widgets.py # UI widgets (frames, tables, etc.)
│   ├── layouts.py # Layout management
│   └── prompts.py # Input prompts
├── features/ # Individual features
│   ├── __init__.py
│   ├── base.py # Base feature class
│   ├── data_processing.py # Data processing features
│   ├── user_manager.py # User management
│   ├── configuration.py # Configuration management
│   ├── system_tools.py # System tools
│   ├── weather.py # Weather checking
│   ├── file_browser.py # File browsing
│   ├── help_system.py # Help system
│   └── export.py # Export functionality
├── services/ # Business logic services
│   ├── __init__.py
│   ├── preferences.py # Preferences management
│   ├── feedback.py # Feedback handling
│   └── async_tasks.py # Async task management
└── utils/ # Utility functions
    ├── __init__.py
    ├── cleanup.py # Cleanup utilities
    ├── decorators.py # Custom decorators
    └── validators.py # Input validators
```

## Module Responsibilities

### Core (`core/`)

- **app.py**: Main application class, coordinates features and manages lifecycle
- **database.py**: Database initialization and session management
- **constants.py**: Central location for all application constants

### Models (`models/`)

- **base.py**: Base model with common fields (created_at, updated_at)
- **user.py**: User model with preferences management

### UI (`ui/`)

- **console.py**: Rich console configuration and global instance
- **menu.py**: Menu display and navigation logic
- **widgets.py**: Reusable UI components (frames, tables, progress bars)
- **layouts.py**: Layout creation and management
- **prompts.py**: Various input prompt utilities

### Features (`features/`)

Each feature is self-contained and inherits from `BaseFeature`:

- **data_processing.py**: Code snippets, system info, tables, progress
- **user_manager.py**: User CRUD operations
- **configuration.py**: Theme selection, settings management
- **system_tools.py**: File browser, weather, export, feedback
- **weather.py**: Weather API integration
- **file_browser.py**: Directory listing and navigation
- **help_system.py**: Help documentation and search
- **export.py**: CSV/PDF export functionality

### Services (`services/`)

- **preferences.py**: Load/save user preferences
- **feedback.py**: Handle user feedback
- **async_tasks.py**: Manage asynchronous operations

### Utils (`utils/`)

- **cleanup.py**: Application cleanup handlers
- **decorators.py**: Custom decorators for features
- **validators.py**: Input validation functions

## Key Design Patterns

### 1. Single Responsibility Principle

Each module has a single, well-defined responsibility.

### 2. Dependency Injection

Features receive dependencies through their constructors rather than creating them.

### 3. Abstract Base Classes

`BaseFeature` provides a common interface for all features.

### 4. Context Managers

Database sessions use context managers for proper resource cleanup.

### 5. Factory Pattern

`DatabaseManager` acts as a factory for database sessions.

## Data Flow

1. **Entry Point** (`__main__.py`)
   - Creates `FarmerCLI` instance
   - Registers cleanup handlers
   - Handles top-level exceptions

2. **Application** (`core/app.py`)
   - Initializes database
   - Loads preferences
   - Manages main loop
   - Coordinates features

3. **Features** (`features/*.py`)
   - Self-contained functionality
   - Use UI components for display
   - Access database through context managers
   - Handle feature-specific logic

4. **UI Components** (`ui/*.py`)
   - Handle all user interaction
   - Provide consistent styling
   - Manage layouts and widgets

## Adding New Features

To add a new feature:

1. Create a new file in `features/`
2. Inherit from `BaseFeature`
3. Implement the `execute()` method
4. Register in `features/__init__.py`
5. Add to feature dictionary in `app.py`

Example:

```python
from .base import BaseFeature

class MyNewFeature(BaseFeature):
    def __init__(self):
        super().__init__(
            name="My Feature",
            description="Description of my feature"
        )
    
    def execute(self):
        # Feature logic here
        pass
```

## Testing

The modular structure makes testing easier:

- Each module can be tested independently
- Mock dependencies can be injected
- UI and business logic are separated

## Configuration

- Environment variables: `.env` file
- Application settings: `config/settings.py`
- User preferences: `preferences.json`
- Constants: `core/constants.py`

## Error Handling

- Custom exceptions in `exceptions/`
- Each module handles its specific errors
- Errors bubble up to main application
- User-friendly error messages in UI

## Future Enhancements

The modular structure allows for easy additions:

- Plugin system for external features
- API endpoints for remote access
- GUI version using the same core logic
- Database migrations for schema updates
