# Migration Guide: From Monolithic to Modular

This guide explains how the Farmer CLI has been refactored from a monolithic `cli_legacy.py` file into a modular architecture.

## Overview of Changes

### Before (Monolithic)

- Single file: `cli_legacy.py` (~1100 lines)
- All functionality mixed together
- Difficult to maintain and test
- Circular dependencies
- Hard to add new features

### After (Modular)

- Organized into logical modules
- Clear separation of concerns
- Easy to test individual components
- No circular dependencies
- Simple to extend with new features

## Module Mapping

Here's where the old functionality has been moved:

### Core Application Logic

- `main()` → `core/app.py` (FarmerCLI class)
- Database initialization → `core/database.py`
- Constants → `core/constants.py`

### UI Components

- Console setup → `ui/console.py`
- Menu display → `ui/menu.py`
- `create_frame()`, tables → `ui/widgets.py`
- Layouts → `ui/layouts.py`
- Input prompts → `ui/prompts.py`

### Features

- `display_code_snippet()`, `display_system_info()` → `features/data_processing.py`
- `add_user()`, `manage_users()` → `features/user_manager.py`
- `select_theme()`, time display → `features/configuration.py`
- `list_files()` → `features/file_browser.py`
- `fetch_weather()` → `features/weather.py`
- Export functions → `features/export.py`
- Help functions → `features/help_system.py`

### Services

- Preferences handling → `services/preferences.py`
- Feedback → `services/feedback.py`
- Async tasks → `services/async_tasks.py`

### Models

- User class → `models/user.py`
- Base model → `models/base.py`

### Utilities

- Cleanup → `utils/cleanup.py`
- Decorators → `utils/decorators.py`
- Validators → `utils/validators.py`

## Key Improvements

### 1. Database Management

```python
# Old way
engine = create_engine(f"sqlite:///{DATABASE_FILE}", echo=False)
session = Session()

# New way
with get_session() as session:
    # Database operations
    # Automatic commit/rollback
```

### 2. Feature Organization

```python
# Old way - everything in one file
def submenu_option_one():
    # Mixed UI and logic

# New way - separate feature classes
class DataProcessingFeature(BaseFeature):
    def execute(self):
        # Feature-specific logic
```

### 3. Error Handling

```python
# Old way
try:
    # code
except Exception as e:
    print(f"Error: {e}")

# New way - specific exceptions
try:
    # code
except DatabaseError as e:
    # Handle database errors
except NetworkError as e:
    # Handle network errors
```

### 4. Configuration

```python
# Old way - global variables
current_theme = "default"

# New way - centralized settings
from config.settings import settings
theme = settings.default_theme
```

## Running the Refactored Application

### Entry Points

```bash
# Old way
python src/cli_legacy.py

# New way
python -m farmer_cli
# or
python src/farmer_cli/__main__.py
```

### Import Changes

```python
# Old imports (in one file)
from rich.console import Console
console = Console()

# New imports (from modules)
from farmer_cli.ui.console import console
from farmer_cli.features import UserManagementFeature
```

## Adding New Features

### Old Way

1. Add functions to cli_legacy.py
2. Update menu handling
3. Risk breaking existing code

### New Way

1. Create new feature in `features/`
2. Inherit from `BaseFeature`
3. Register in `app.py`
4. No impact on existing features

Example:

```python
# features/my_feature.py
from .base import BaseFeature

class MyFeature(BaseFeature):
    def __init__(self):
        super().__init__("My Feature", "Description")
    
    def execute(self):
        # Feature logic
```

## Testing

### Legacy

- Hard to test individual functions
- Mock entire application state
- Tests are fragile

### Current Implementation

- Test individual modules
- Mock specific dependencies
- Robust test structure

Example:

```python
# Test a specific feature
def test_user_management():
    feature = UserManagementFeature()
    with mock_database():
        feature.execute()
```

## Configuration Files

### Moved/Updated Files

- Settings now in `config/settings.py`
- Environment variables in `.env`
- Constants in `core/constants.py`

### New Structure Benefits

- Type-safe configuration with Pydantic
- Environment variable validation
- Centralized configuration management

## Best Practices Going Forward

1. **Keep modules focused** - Each module should have a single responsibility
2. **Use dependency injection** - Pass dependencies rather than importing globally
3. **Follow the base classes** - Extend BaseFeature for new features
4. **Handle errors appropriately** - Use custom exceptions for better error handling
5. **Document your code** - Add docstrings to all public functions and classes

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're using the new module paths
   - Run from the project root directory

2. **Database Errors**
   - The database schema remains the same
   - Use context managers for sessions

3. **Missing Dependencies**
   - Check requirements.txt for new dependencies
   - Install with: `pip install -r requirements.txt`

## Summary

The refactoring maintains all original functionality while providing:

- Better organization
- Easier maintenance
- Improved testability
- Clear extension points
- Better error handling
- Type safety

The modular structure makes the codebase more professional and maintainable for future development.
