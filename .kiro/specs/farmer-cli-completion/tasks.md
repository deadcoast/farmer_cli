# Implementation Plan: Farmer CLI Completion

## Overview

This implementation plan breaks down the Farmer CLI completion into discrete, incremental tasks. Each task builds on previous work, ensuring no orphaned code. The plan prioritizes core video downloading functionality first, then enhances existing features, and finally establishes comprehensive test coverage.

## Tasks

- [x] 1. Set up testing infrastructure and base utilities
  - [x] 1.1 Create tests directory structure with conftest.py and fixtures
    - Create `tests/`, `tests/unit/`, `tests/property/`, `tests/integration/`
    - Set up pytest configuration in pyproject.toml
    - Create shared fixtures for database, temp files, mock services
    - *Requirements: 9.1, 9.2*
  - [x] 1.2 Implement URL validation utilities (utils/url_utils.py)
    - Create `is_valid_url()` function with regex validation
    - Create `is_supported_platform()` to check against supported sites
    - Create `extract_video_id()` for URL parsing
    - *Requirements: 1.2, 1.6*
  - [x] 1.3 Write property tests for URL validation
    - **Property 12: Invalid URL Error Handling**
    - **Validates: Requirements 1.2**
  - [x] 1.4 Implement filename template utility (utils/filename_template.py)
    - Create `FilenameTemplate` class with variable substitution
    - Implement `render()` method for generating filenames
    - Implement `validate()` method for template validation
    - Sanitize output to remove invalid filesystem characters
    - *Requirements: 6.2*
  - [x] 1.5 Write property tests for filename templating
    - **Property 14: Filename Template Rendering**
    - **Validates: Requirements 6.2**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Implement yt-dlp wrapper service
  - [x] 3.1 Create data classes for video information (services/ytdlp_wrapper.py)
    - Define `DownloadStatus` enum
    - Define `VideoFormat` dataclass with format_id, resolution, codec, filesize
    - Define `VideoInfo` dataclass with url, title, uploader, formats
    - Define `DownloadProgress` dataclass for progress tracking
    - *Requirements: 2.2*
  - [x] 3.2 Write property tests for format information completeness
    - **Property 6: Format Information Completeness**
    - **Validates: Requirements 2.2**
  - [x] 3.3 Implement YtdlpWrapper.extract_info() method
    - Wrap yt-dlp's extract_info with proper error handling
    - Convert yt-dlp dict to VideoInfo dataclass
    - Handle network errors and invalid URLs gracefully
    - *Requirements: 1.1, 1.2*
  - [x] 3.4 Implement YtdlpWrapper.get_formats() method
    - Extract available formats from video info
    - Filter and sort formats by quality
    - Support audio-only format filtering
    - *Requirements: 2.1, 2.4*
  - [x] 3.5 Implement YtdlpWrapper.download() method
    - Configure yt-dlp options for download
    - Implement progress callback integration
    - Handle download interruption and resumption
    - Verify file integrity after download
    - *Requirements: 1.1, 1.3, 1.4, 1.5*
  - [x] 3.6 Implement YtdlpWrapper.extract_playlist() method
    - Extract all video entries from playlist URL
    - Handle pagination for large playlists
    - Return list of VideoInfo objects
    - *Requirements: 3.1*

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement database models for downloads
  - [x] 5.1 Create QueueItem model (models/download.py)
    - Define SQLAlchemy model with all required fields
    - Add indexes for status and position columns
    - Implement validation for status transitions
    - *Requirements: 4.1, 4.2*
  - [x] 5.2 Create DownloadHistory model (models/history.py)
    - Define SQLAlchemy model with all required fields
    - Add index on url column for duplicate detection
    - Add index on downloaded_at for sorting
    - *Requirements: 5.1, 5.2*
  - [x] 5.3 Write property tests for history entry completeness
    - **Property 7: History Entry Completeness**
    - **Validates: Requirements 5.2**
  - [x] 5.4 Write property tests for queue item completeness
    - **Property 8: Queue Item Completeness**
    - **Validates: Requirements 4.2**
  - [x] 5.5 Update database initialization to create new tables
    - Add migration for new tables
    - Update DatabaseManager.initialize() method
    - *Requirements: 11.3*

- [x] 6. Implement download manager service
  - [x] 6.1 Implement DownloadManager.add_to_queue() method
    - Create QueueItem with generated UUID
    - Persist to database
    - Return created item
    - *Requirements: 4.1*
  - [x] 6.2 Implement DownloadManager.get_queue() method
    - Query all queue items ordered by position
    - Return list of QueueItem objects
    - *Requirements: 4.2*
  - [x] 6.3 Implement queue manipulation methods (pause, resume, cancel, reorder)
    - Implement pause_download() with status update
    - Implement resume_download() with status update
    - Implement cancel_download() with cleanup
    - Implement reorder_queue() with position updates
    - *Requirements: 4.3*
  - [x] 6.4 Implement DownloadManager.check_duplicate() method
    - Query history by URL
    - Return matching HistoryEntry or None
    - *Requirements: 5.3*
  - [x] 6.5 Write property tests for duplicate detection
    - **Property 13: Duplicate Detection Accuracy**
    - **Validates: Requirements 5.3**
  - [x] 6.6 Implement DownloadManager.get_history() method
    - Query history with optional search filter
    - Support pagination with limit/offset
    - Check file existence for each entry
    - *Requirements: 5.2, 5.6*
  - [x] 6.7 Implement concurrent download management
    - Track active downloads count
    - Implement set_max_concurrent() with validation (1-5)
    - Auto-start next queued item on completion
    - *Requirements: 4.5, 4.6*
  - [x] 6.8 Write property tests for concurrent download limit
    - **Property 19: Concurrent Download Limit**
    - **Validates: Requirements 4.5**
  - [x] 6.9 Implement queue persistence and restoration
    - Save queue state to database on changes
    - Restore queue on application startup
    - *Requirements: 4.4*
  - [x] 6.10 Write property tests for queue persistence round-trip
    - **Property 4: Queue Persistence Round-Trip**
    - **Validates: Requirements 4.4**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement format selector service
  - [x] 8.1 Create FormatSelector class (services/format_selector.py)
    - Implement get_available_formats() using YtdlpWrapper
    - Implement get_best_format() with quality ranking
    - Implement get_audio_formats() filter
    - *Requirements: 2.1, 2.4, 2.5*
  - [x] 8.2 Implement format preference persistence
    - Implement set_default_format() saving to preferences
    - Implement get_default_format() loading from preferences
    - *Requirements: 2.6*

- [x] 9. Implement playlist handler service
  - [x] 9.1 Create PlaylistHandler class (services/playlist_handler.py)
    - Implement enumerate_playlist() using YtdlpWrapper
    - Implement get_range() for selective downloading
    - *Requirements: 3.1, 3.5*
  - [x] 9.2 Implement batch download functionality
    - Implement download_batch() with concurrent downloads
    - Track successes and failures separately
    - Generate summary report
    - *Requirements: 3.3, 3.4, 3.6*
  - [x] 9.3 Write property tests for batch failure isolation
    - **Property 20: Batch Failure Isolation**
    - **Validates: Requirements 3.4**

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement video downloader feature
  - [x] 11.1 Create VideoDownloaderFeature class (features/video_downloader.py)
    - Inherit from BaseFeature
    - Wire up YtdlpWrapper, DownloadManager, FormatSelector
    - Implement execute() method with submenu
    - *Requirements: 1.1*
  - [x] 11.2 Implement single video download workflow
    - Prompt for URL input with validation
    - Check for duplicates and warn user
    - Display format options and get selection
    - Start download with progress display
    - Record to history on completion
    - *Requirements: 1.1, 2.1, 2.3, 5.1, 5.3*
  - [x] 11.3 Implement playlist download workflow
    - Detect playlist URLs automatically
    - Display video list with selection options
    - Support range selection
    - Queue selected videos for download
    - *Requirements: 3.1, 3.2, 3.5*
  - [x] 11.4 Implement download queue management UI
    - Display queue with status and progress
    - Provide pause/resume/cancel options
    - Allow reordering
    - *Requirements: 4.2, 4.3*
  - [x] 11.5 Implement download history UI
    - Display history with search
    - Show file existence status
    - Allow clearing history
    - *Requirements: 5.2, 5.4, 5.6*
  - [x] 11.6 Create download progress UI component (ui/download_ui.py)
    - Create progress bar with speed and ETA
    - Support multiple concurrent progress displays
    - Handle download completion/failure states
    - *Requirements: 1.3*

- [x] 12. Implement output configuration
  - [x] 12.1 Add download settings to preferences
    - Default download directory
    - Filename template
    - Conflict resolution preference
    - Subdirectory organization preference
    - *Requirements: 6.1, 6.2, 6.4*
  - [x] 12.2 Implement directory validation
    - Validate path exists and is writable
    - Auto-create subdirectories as needed
    - *Requirements: 6.5, 6.6*
  - [x] 12.3 Write property tests for directory validation
    - **Property 15: Directory Validation**
    - **Validates: Requirements 6.5**
  - [x] 12.4 Implement filename conflict resolution
    - Detect existing files
    - Offer rename/overwrite/skip options
    - *Requirements: 6.3*

- [x] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Enhance user management feature
  - [x] 14.1 Implement user update functionality
    - Add update_user() method to UserManagementFeature
    - Create UI for editing user name and preferences
    - *Requirements: 7.2*
  - [x] 14.2 Implement user deletion with confirmation
    - Add delete_user() method with confirmation prompt
    - Handle cascade deletion of related data
    - *Requirements: 7.3*
  - [x] 14.3 Implement user pagination
    - Add pagination to list_users() method
    - Update UI to show page navigation
    - *Requirements: 7.4*
  - [x] 14.4 Implement user search
    - Add search_users() method with name matching
    - Update UI with search input
    - *Requirements: 7.5*
  - [x] 14.5 Write property tests for user name validation
    - **Property 16: User Name Validation**
    - **Validates: Requirements 7.1**
  - [x] 14.6 Write property tests for user serialization round-trip
    - **Property 1: User Serialization Round-Trip**
    - **Validates: Requirements 7.6**

- [x] 15. Enhance preferences service
  - [x] 15.1 Add preference validation
    - Implement type checking for preference values
    - Implement range validation where applicable
    - *Requirements: 8.4*
  - [x] 15.2 Write property tests for preference validation
    - **Property 17: Preference Value Validation**
    - **Validates: Requirements 8.4**
  - [x] 15.3 Implement corruption recovery
    - Detect corrupted preferences file
    - Reset to defaults and notify user
    - *Requirements: 8.5*
  - [x] 15.4 Write property tests for preferences round-trip
    - **Property 2: Preferences Round-Trip**
    - **Validates: Requirements 8.6**

- [x] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Enhance export service
  - [x] 17.1 Add JSON export format
    - Implement export_to_json() method
    - Support field selection
    - *Requirements: 12.1, 12.2*
  - [x] 17.2 Implement download history export
    - Add export_history() method
    - Support all three formats (CSV, JSON, PDF)
    - *Requirements: 12.3*
  - [x] 17.3 Implement data import functionality
    - Add import_data() method for JSON format
    - Validate imported data structure
    - *Requirements: 12.6*
  - [x] 17.4 Write property tests for export/import round-trip
    - **Property 3: Export/Import Round-Trip**
    - **Validates: Requirements 12.6**
  - [x] 17.5 Add export completion reporting
    - Report file location and size after export
    - *Requirements: 12.4*

- [x] 18. Implement CLI interface
  - [x] 18.1 Create Click-based CLI (cli.py)
    - Set up Click group with version and help
    - Implement --quiet flag for minimal output
    - *Requirements: 13.4, 13.5*
  - [x] 18.2 Implement download command
    - Add `download` command with URL argument
    - Add --format option for format selection
    - Add --output option for output path
    - *Requirements: 13.1, 13.2, 13.3*
  - [x] 18.3 Update __main__.py for CLI integration
    - Route to CLI or interactive mode based on arguments
    - Handle argument parsing errors gracefully
    - *Requirements: 13.6*
  - [x] 18.4 Write property tests for CLI argument handling
    - **Property 18: CLI Invalid Argument Handling**
    - **Validates: Requirements 13.6**

- [x] 19. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 20. Implement error handling and logging
  - [x] 20.1 Create logging configuration (core/logging_config.py)
    - Configure console handler for user-friendly messages
    - Configure file handler with full stack traces
    - Support configurable log levels
    - *Requirements: 10.2, 10.3*
  - [x] 20.2 Implement user-friendly error messages
    - Create error message templates for common errors
    - Add troubleshooting suggestions for network errors
    - *Requirements: 10.1, 10.4*
  - [x] 20.3 Write property tests for error message user-friendliness
    - **Property 9: Error Message User-Friendliness**
    - **Validates: Requirements 10.1**
  - [x] 20.4 Write property tests for error logging completeness
    - **Property 10: Error Logging Completeness**
    - **Validates: Requirements 10.2**
  - [x] 20.5 Add log viewer to UI
    - Create feature to view recent log entries
    - Support filtering by log level
    - *Requirements: 10.6*

- [x] 21. Enhance database reliability
  - [x] 21.1 Implement database backup and restore
    - Add backup_database() method
    - Add restore_database() method
    - *Requirements: 11.5*
  - [x] 21.2 Add startup integrity validation
    - Check table existence and schema
    - Validate foreign key constraints
    - *Requirements: 11.4*
  - [x] 21.3 Write property tests for database rollback
    - **Property 11: Database Rollback on Failure**
    - **Validates: Requirements 11.2**
  - [x] 21.4 Write property tests for database consistency
    - **Property 5: Database Consistency Invariant**
    - **Validates: Requirements 11.6**

- [x] 22. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 23. Wire up features and update main menu
  - [x] 23.1 Register VideoDownloaderFeature in app.py
    - Add to features dictionary
    - Update menu options and actions
    - *Requirements: 1.1*
  - [x] 23.2 Update constants.py with new menu options
    - Add video download menu options
    - Add download settings options
    - *Requirements: 1.1*
  - [x] 23.3 Update README.md with new features
    - Document video downloading functionality
    - Document CLI arguments
    - Update feature list
    - *Requirements: N/A (documentation)*

- [x] 24. Integration testing
  - [x] 24.1 Write integration tests for download workflow
    - Test complete download flow from URL to file
    - Test queue management workflow
    - Test history tracking
    - *Requirements: 9.4*
  - [x] 24.2 Write integration tests for user workflow
    - Test complete CRUD operations
    - Test export/import cycle
    - *Requirements: 9.4*
  - [x] 24.3 Write integration tests for CLI interface
    - Test all CLI commands and options
    - Test error handling for invalid inputs
    - *Requirements: 9.4*

- [x] 25. Unit tests for coverage target (80%)
  - Current coverage: ~35%. Need to add unit tests for low-coverage modules.
  - [x] 25.1 Write unit tests for ytdlp_wrapper.py (currently 40%)
    - Test extract_info with mocked yt-dlp responses
    - Test download method with progress callbacks
    - Test error handling for network failures
    - Test is_playlist() and get_playlist_info() methods
    - *Requirements: 9.1, 9.3*
  - [x] 25.2 Write unit tests for download_manager.py (currently 60%)
    - Test all queue manipulation methods
    - Test history management methods
    - Test concurrent download tracking
    - Test add_to_history() method
    - Test get_history_count() method
    - *Requirements: 9.1, 9.3*
  - [x] 25.3 Write unit tests for format_selector.py (currently 16%)
    - Test get_available_formats with various inputs
    - Test get_best_format ranking logic
    - Test audio format filtering
    - Test get_video_formats() method
    - Test get_best_audio_format() method
    - Test get_formats_by_resolution() method
    - Test _filter_by_resolution() method
    - Test _sort_formats() and _sort_audio_formats() methods
    - Test set_default_format() and get_default_format()
    - Test get_format_for_download() method
    - *Requirements: 9.1, 9.3*
  - [x] 25.4 Write unit tests for playlist_handler.py (currently 54%)
    - Test enumerate_playlist with mocked responses
    - Test get_range boundary conditions
    - Test batch download result aggregation
    - Test download_playlist() convenience method
    - *Requirements: 9.1, 9.3*
  - [x] 25.5 Write unit tests for video_downloader.py feature (currently 10%)
    - Test menu navigation logic
    - Test URL validation integration
    - Test format selection workflow
    - Test _download_single_video() method
    - Test _download_playlist() method
    - Test _handle_playlist_download() method
    - Test _view_download_queue() method
    - Test _view_download_history() method
    - Test _settings_menu() method
    - *Requirements: 9.1, 9.3*
  - [x] 25.6 Write unit tests for user_manager.py feature (currently 10%)
    - Test add_user validation
    - Test update_user logic
    - Test delete_user with confirmation
    - Test pagination logic
    - Test search_users() method
    - *Requirements: 9.1, 9.3*
  - [x] 25.7 Write unit tests for export.py service (currently 16%)
    - Test CSV export formatting
    - Test JSON export structure
    - Test field selection filtering
    - Test PDF export (if implemented)
    - Test export_history() method
    - *Requirements: 9.1, 9.3*
  - [x] 25.8 Write unit tests for cli.py (currently 41%)
    - Test download command execution paths
    - Test interactive command routing
    - Test quiet mode output suppression
    - Test version and help flags
    - *Requirements: 9.1, 9.3*
  - [x] 25.9 Write unit tests for database.py (currently 35%)
    - Test backup and restore methods
    - Test integrity validation
    - Test migration handling
    - Test get_session() function
    - *Requirements: 9.1, 9.3*
  - [x] 25.10 Write unit tests for output_config.py (currently 0%)
    - Test OutputSettings dataclass methods
    - Test OutputConfigService.get_settings() and save_settings()
    - Test set_download_directory() with validation
    - Test set_filename_template() with validation
    - Test set_conflict_resolution() and set_subdirectory_organization()
    - Test validate_directory() static method
    - Test ensure_directory() static method
    - Test get_output_path() method
    - Test _get_subdirectory() method
    - Test _sanitize_dirname() static method
    - Test resolve_conflict() method
    - Test _get_unique_path() static method
    - *Requirements: 9.1, 9.3*
  - [x] 25.11 Write unit tests for conflict_resolver.py (currently 0%)
    - Test detect_conflict() function
    - Test resolve_conflict() function with all resolution types
    - Test get_unique_path() function
    - Test get_conflict_options() function
    - Test suggest_resolution() function
    - Test ConflictResolver class methods
    - *Requirements: 9.1, 9.3*

- [x] 26. Additional unit tests for remaining low-coverage modules
  - [x] 26.1 Write unit tests for __main__.py (currently 0%)
    - Test main() function routing logic
    - Test keyboard interrupt handling
    - Test SystemExit handling
    - *Requirements: 9.1, 9.3*
  - [x] 26.2 Write unit tests for ui/download_ui.py (currently 13%)
    - Test create_download_progress() function
    - Test create_multi_download_progress() function
    - Test display_download_queue() function
    - Test display_download_history() function
    - Test display_video_info_panel() function
    - Test display_format_selection() function
    - Test display_batch_progress() function
    - Test display_download_complete() function
    - Test display_download_failed() function
    - Test _get_status_style() helper
    - Test _format_filesize() helper
    - *Requirements: 9.1, 9.3*
  - [x] 26.3 Write unit tests for ui/prompts.py (currently 16%)
    - Test text_prompt() with validation
    - Test confirm_prompt() function
    - Test choice_prompt() function
    - Test int_prompt() with min/max validation
    - Test password_prompt() with confirmation
    - Test autocomplete_prompt() function
    - Test multiline_prompt() function
    - *Requirements: 9.1, 9.3*
  - [x] 26.4 Write unit tests for ui/menu.py (currently 28%)
    - Test MenuManager.display_main_menu() method
    - Test MenuManager.display_submenu() method
    - Test menu stack operations (push_menu, pop_menu, clear_stack)
    - *Requirements: 9.1, 9.3*
  - [x] 26.5 Write unit tests for ui/console.py (currently 40%)
    - Test console initialization
    - Test get_prompt_session() function
    - *Requirements: 9.1, 9.3*
  - [x] 26.6 Write unit tests for utils/validators.py (currently 22%)
    - Test validate_json() function
    - Test validate_email() function
    - Test validate_path() function
    - Test validate_positive_int() function
    - Test validate_port() function
    - Test validate_url() function
    - Test validate_version() function
    - Test validate_non_empty() function
    - Test validate_choice() function
    - Test validate_range() function
    - *Requirements: 9.1, 9.3*
  - [x] 26.7 Write unit tests for utils/url_utils.py (currently 53%)
    - Test is_valid_url() with edge cases
    - Test is_supported_platform() for all platforms
    - Test extract_video_id() for YouTube, Vimeo, direct URLs
    - Test get_supported_platforms() function
    - Test get_platform_domains() function
    - *Requirements: 9.1, 9.3*
  - [x] 26.8 Write unit tests for features/log_viewer.py (currently 12%)
    - Test LogViewerFeature.execute() method
    - Test log filtering by level
    - Test log display formatting
    - *Requirements: 9.1, 9.3*
  - [x] 26.9 Write unit tests for core/app.py (currently 25%)
    - Test App initialization
    - Test feature registration
    - Test menu action handling
    - *Requirements: 9.1, 9.3*

- [x] 27. Code quality fixes identified during review
  - [x] 27.1 Fix unused variable in __main__.py
    - Remove or use the `argv` variable (line 35)
    - *Requirements: Code quality*
  - [x] 27.2 Fix unused parameter in video_downloader.py
    - Address unused `url` parameter in _batch_progress_callback (line 746)
    - *Requirements: Code quality*
  - [x] 27.3 Fix import sorting in video_downloader.py
    - Run isort to fix import block ordering
    - *Requirements: Code quality*
  - [x] 27.4 Fix ResourceWarning in database tests
    - Ensure database connections are properly closed in test_database_rollback_properties.py
    - *Requirements: Code quality*

- [-] 28. Checkpoint - Verify 80% coverage target
  - Run full test suite with coverage
  - Verify minimum 80% code coverage achieved
  - Ensure all tests pass, ask the user if questions arise.
  - *Requirements: 9.3*

- [ ] 29. Final checkpoint - All requirements verified
  - Run full test suite
  - Confirm 80% code coverage
  - Verify all 250+ tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks including property-based tests are required for comprehensive coverage
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation order ensures no orphaned code - each feature is wired up before moving on
- Current status: 250 tests passing, ~35% coverage. Tasks 25-29 address the 80% coverage requirement.

## Coverage Summary (Current State)

| Module | Coverage | Priority |
|--------|----------|----------|
| output_config.py | 0% | HIGH |
| conflict_resolver.py | 0% | HIGH |
| __main__.py | 0% | MEDIUM |
| theme_showcase.py | 0% | LOW |
| welcome.py | 0% | LOW |
| video_downloader.py | 10% | HIGH |
| user_manager.py | 10% | HIGH |
| log_viewer.py | 12% | MEDIUM |
| download_ui.py | 13% | MEDIUM |
| file_browser.py | 14% | LOW |
| format_selector.py | 16% | HIGH |
| export.py (service) | 16% | HIGH |
| prompts.py | 16% | MEDIUM |
| export.py (feature) | 17% | MEDIUM |
| validators.py | 22% | MEDIUM |
| widgets.py | 22% | LOW |
| feedback.py | 22% | LOW |
| configuration.py | 21% | LOW |
| weather.py | 21% | LOW |
| app.py | 25% | MEDIUM |
| async_tasks.py | 25% | LOW |
| layouts.py | 25% | LOW |
| data_processing.py | 26% | LOW |
| cleanup.py | 27% | LOW |
| system_tools.py | 27% | LOW |
| menu.py | 28% | MEDIUM |
| database.py | 35% | HIGH |
| help_system.py | 35% | LOW |
| ytdlp_wrapper.py | 40% | HIGH |
| console.py | 40% | MEDIUM |
| cli.py | 41% | HIGH |
| base.py (features) | 47% | LOW |
| url_utils.py | 53% | MEDIUM |
| playlist_handler.py | 54% | HIGH |
| directory_utils.py | 55% | MEDIUM |
| download_manager.py | 60% | HIGH |
| filename_template.py | 64% | MEDIUM |
| logging_config.py | 68% | LOW |
| error_messages.py | 74% | LOW |
| preferences.py | 79% | LOW |
| exceptions.py | 84% | LOW |
| history.py | 86% | LOW |
| user.py | 87% | LOW |
| download.py | 91% | LOW |
| base.py (models) | 92% | LOW |

Priority is based on:
- HIGH: Core functionality with 0-40% coverage
- MEDIUM: Supporting functionality with 0-60% coverage
- LOW: Already has decent coverage (>60%) or non-critical features
