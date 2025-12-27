"""
Application constants and configuration values.

This module defines all the constants used throughout the Farmer CLI application,
including menu options, default values, and configuration parameters.
"""

from pathlib import Path


# Application metadata
APP_NAME = "Farmer CLI"
APP_VERSION = "0.2.0"
APP_DESCRIPTION = "A powerful CLI application with Rich UI for video downloading"

# File paths
PREFERENCES_FILE = Path("preferences.json")
FEEDBACK_FILE = Path("feedback.txt")

# Menu configuration
MENU_OPTIONS = [
    "Video Downloader",
    "Data Processing",
    "User Management",
    "Configuration",
    "System Tools",
    "Exit",
]

# Menu option mappings
MENU_ACTIONS = {
    "1": "video_downloader",
    "2": "data_processing",
    "3": "user_management",
    "4": "configuration",
    "5": "system_tools",
    "0": "exit",
}

# Submenu options
DATA_PROCESSING_OPTIONS = [
    ("1", "Display Code Snippet"),
    ("2", "Show System Info"),
    ("3", "Display Sample Table"),
    ("4", "Simulate Progress"),
    ("0", "Return to Main Menu"),
]

CONFIGURATION_OPTIONS = [
    ("1", "Select Theme"),
    ("2", "Theme Showcase"),
    ("3", "Display Current Time"),
    ("4", "Search Help"),
    ("0", "Return to Main Menu"),
]

SYSTEM_TOOLS_OPTIONS = [
    ("1", "List Files"),
    ("2", "Check Weather"),
    ("3", "Export Help to PDF"),
    ("4", "Submit Feedback"),
    ("5", "View Logs"),
    ("0", "Return to Main Menu"),
]

USER_MANAGEMENT_OPTIONS = [
    ("1", "Add User"),
    ("2", "List Users"),
    ("3", "Update User"),
    ("4", "Delete User"),
    ("5", "Search Users"),
    ("6", "Export Users to CSV"),
    ("0", "Return to Main Menu"),
]

VIDEO_DOWNLOADER_OPTIONS = [
    ("1", "Download Single Video"),
    ("2", "Download Playlist"),
    ("3", "View Download Queue"),
    ("4", "View Download History"),
    ("5", "Settings"),
    ("0", "Return to Main Menu"),
]

DOWNLOAD_SETTINGS_OPTIONS = [
    ("1", "Change Download Directory"),
    ("2", "Set Default Format"),
    ("3", "Set Max Concurrent Downloads"),
    ("0", "Return"),
]

# Pagination configuration
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Theme configuration
DEFAULT_THEME = "default"

# UI Configuration
FRAME_WIDTH = 60
PROGRESS_REFRESH_RATE = 10
TYPING_EFFECT_DELAY = 1  # seconds

# Network timeouts
API_TIMEOUT = 10  # seconds

# Export file names
PDF_EXPORT_FILE = "help.pdf"
CSV_EXPORT_FILE = "users_export.csv"
HTML_TEMP_FILE = "help.html"
