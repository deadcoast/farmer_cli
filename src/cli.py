import asyncio
import atexit
import csv
import json
import logging
import platform
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

import requests
from dotenv import load_dotenv
from fuzzywuzzy import process
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text as SQLText
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import custom modules
from config.settings import settings
from exceptions import APIError
from exceptions import ConfigurationError
from exceptions import DatabaseError
from exceptions import FarmerCLIError
from exceptions import FileOperationError
from exceptions import NetworkError
from themes import DOUBLE_LINE
from themes import HELP_TEXTS
from themes import THEMES


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename=str(settings.log_file),
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.log_level)
)
logger = logging.getLogger(__name__)

# Initialize Rich console
PREFERENCES_FILE = Path("preferences.json")
console = Console()
prompt_session: PromptSession = PromptSession(history=InMemoryHistory())
bindings = KeyBindings()

# Database setup
engine = create_engine(f"sqlite:///{settings.database_path}", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Define menu options
menu_options = ["Option One", "Option Two", "Option Three", "Option Four", "Exit"]
current_selection = 0
current_theme = settings.default_theme

# Theme and constants are imported from themes module


class User(Base):  # type: ignore
    """User model for storing user information."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    preferences = Column(SQLText)


def initialize_db() -> None:
    """
    Initialize the database with required tables.

    Raises:
        DatabaseError: If database initialization fails
    """
    try:
        logger.info("Initializing database...")
        conn = sqlite3.connect(str(settings.database_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                preferences TEXT
            )
        """
        )
        conn.commit()
        conn.close()
        console.print("[bold green]Database initialized successfully.[/bold green]")
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        error_msg = f"Database initialization failed: {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg) from e


def add_user(name: str, preferences: str) -> None:
    """
    Add a new user to the database.

    Args:
        name: User name
        preferences: User preferences in JSON format

    Raises:
        DatabaseError: If user cannot be added
    """
    try:
        user = User(name=name, preferences=preferences)
        session.add(user)
        session.commit()
        console.print("[bold green]User added successfully![/bold green]")
        logger.info(f"Added user: {name}")
    except Exception as e:
        session.rollback()
        error_msg = f"Failed to add user: {e}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logger.error(error_msg)
        raise DatabaseError(error_msg) from e


# Themes and border definitions are imported from themes module

def select_theme() -> None:
    """
    Allow user to select a UI theme.

    The selected theme is saved to preferences.
    """
    global current_theme
    console.clear()
    console.print("[bold magenta]Select a Theme[/bold magenta]")
    for idx, theme in enumerate(THEMES.keys(), 1):
        console.print(f"[{idx}] {theme.capitalize()}")
    choice = Prompt.ask("Enter the number of your choice", choices=[str(i) for i in range(1, len(THEMES) + 1)])
    selected_theme = list(THEMES.keys())[int(choice) - 1]
    current_theme = selected_theme
    console.print(
        f"Theme changed to [bold {THEMES[selected_theme]['highlight_style']}]{selected_theme.capitalize()}[/bold].",
        style="bold green",
    )
    # Save preference
    preferences = load_preferences()
    preferences["theme"] = selected_theme
    save_preferences(preferences)
    sleep(2)


def display_code_snippet() -> None:
    """
    Display a syntax-highlighted code snippet.
    """
    console.clear()
    code = """
def greet(name: str) -> None:
    print(f"Hello, {name}!")

greet("World")
"""
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)
    Prompt.ask("Press Enter to return to the main menu")


def display_system_info() -> None:
    """
    Display system information.
    """
    console.clear()
    info = f"""
    [bold green]System Information[/bold green]

    System: {platform.system()}
    Node Name: {platform.node()}
    Release: {platform.release()}
    Version: {platform.version()}
    Machine: {platform.machine()}
    Processor: {platform.processor() or 'N/A'}
    Python Version: {sys.version.split()[0]}
    """
    console.print(Align.center(info))
    Prompt.ask("Press Enter to return to the main menu")


def display_current_time() -> None:
    """
    Display the current date and time.
    """
    console.clear()
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"[bold yellow]Current Date and Time:[/bold yellow] {formatted_time}")
    Prompt.ask("Press Enter to return to the main menu")


def blink_cursor(text, interval=0.5):
    while True:
        console.print(Align.center(text), end="\r")
        sleep(interval)
        console.print(Align.center(" " * len(text)), end="\r")
        sleep(interval)


def display_table():
    console.clear()
    table = Table(title="Sample Data", style="bold blue")

    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="bold cyan")
    table.add_column("Description", style="dim")

    table.add_row("1", "Option One", "Description for option one.")
    table.add_row("2", "Option Two", "Description for option two.")
    table.add_row("3", "Option Three", "Description for option three.")
    table.add_row("4", "Option Four", "Description for option four.")

    console.print(table)
    Prompt.ask("Press Enter to return to the main menu")


async def async_task(live: Live) -> None:
    """
    Example async task with progress display.

    Args:
        live: Rich Live display instance
    """
    for i in range(100):
        await asyncio.sleep(0.1)
        progress = f"[bold green]{i + 1}%[/bold green] completed."
        live.update(Align.center(Text(progress, style="bold green")))
    console.print("[bold green]Async task completed![/bold green]")


def start_async_task() -> None:
    """
    Start an async task with live progress display.
    """
    async def run_with_live():
        with Live(Align.center(Text("Starting async task...", style="bold yellow")),
                  refresh_per_second=10) as live:
            await async_task(live)

    asyncio.run(run_with_live())


def display_logo() -> None:
    """
    Display the application logo.
    """
    logo = r"""
  ____   _    ____  __  __ _____ ____
 |  _ \ / \  |  _ \|  \/  | ____|  _ \
 | |_) / _ \ | |_) | |\/| |  _| | |_) |
 |  __/ ___ \|  _ <| |  | | |___|  _ <
 |_| /_/   \_\_| \_\_|  |_|_____|_| \_\
"""
    console.print(Text(logo, style="bold green"))


@bindings.add("c-s")  # Ctrl+S for searching
def _(event) -> None:
    """Handle Ctrl+S for searching."""
    fuzzy_search_menu()


@bindings.add("c-h")  # Ctrl+H for help
def _(event) -> None:
    """Handle Ctrl+H for help."""
    display_help_menu()


history = InMemoryHistory()
history.append_string("1")
history.append_string("2")
# ... populate as needed


def load_preferences() -> Dict[str, Any]:
    """
    Load user preferences from file.

    Returns:
        Dictionary of preferences
    """
    if PREFERENCES_FILE.exists():
        try:
            with open(PREFERENCES_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load preferences: {e}")
    return {}


def save_preferences(preferences: Dict[str, Any]) -> None:
    """
    Save user preferences to file.

    Args:
        preferences: Dictionary of preferences to save

    Raises:
        FileOperationError: If save fails
    """
    try:
        with open(PREFERENCES_FILE, "w") as f:
            json.dump(preferences, f, indent=4)
    except IOError as e:
        error_msg = f"Failed to save preferences: {e}"
        logger.error(error_msg)
        raise FileOperationError(error_msg) from e


def fetch_weather(city: str) -> None:
    """
    Fetch weather data for a given city.

    Args:
        city: City name to fetch weather for

    Raises:
        APIError: If weather API fails
        NetworkError: If network request fails
    """
    try:
        api_key = settings.openweather_api_key
        if not api_key:
            raise ConfigurationError("OpenWeather API key not configured. Please set OPENWEATHER_API_KEY in .env file.")

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("cod") != 200:
            error_msg = data.get('message', 'Failed to fetch weather data.')
            raise APIError(f"Weather API error: {error_msg}", status_code=data.get("cod"))

        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        console.print(f"[bold yellow]{city}[/bold yellow] Weather: {weather}, Temperature: {temp}°C")

    except requests.RequestException as e:
        error_msg = f"Network error while fetching weather: {e}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logger.error(error_msg)
        raise NetworkError(error_msg) from e
    except (ConfigurationError, APIError) as e:
        console.print(f"[bold red]{e}[/bold red]")
        logger.error(str(e))
    except Exception as e:
        error_msg = f"Unexpected error fetching weather data: {e}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logger.error(error_msg)
        raise FarmerCLIError(error_msg) from e


def display_weather_menu() -> str:
    """
    Display weather menu and fetch weather for a city.

    Returns:
        City name entered by user
    """
    console.clear()
    city = Prompt.ask("Enter city name")
    try:
        fetch_weather(city)
    except FarmerCLIError as e:
        logger.error(f"Weather fetch failed: {e}")
    Prompt.ask("Press Enter to return to the main menu")
    return city


def search_menu() -> None:
    """
    Search through menu options.
    """
    query = Prompt.ask("Enter search term")
    if results := [option for option in menu_options if query.lower() in option.lower()]:
        table = Table(title="Search Results", style="bold blue")
        table.add_column("Option", style="white")
        for option in results:
            table.add_row(option)
        console.print(table)
    else:
        console.print("[bold yellow]No matching options found.[/bold yellow]")
    Prompt.ask("Press Enter to return to the main menu")


def fuzzy_search_menu() -> None:
    """
    Perform fuzzy search through menu options.
    """
    query = Prompt.ask("Enter search term")
    # Process.extract returns list of tuples (match, score)
    matches = process.extract(query, menu_options, limit=5)

    if not matches:
        console.print("[bold yellow]No matching options found.[/bold yellow]")
    else:
        table = Table(title="Search Results", style="bold blue")
        table.add_column("Option", style="white")
        table.add_column("Score", style="dim")
        for match_tuple in matches:
            # Extract match and score from tuple (handle different tuple sizes)
            match = match_tuple[0]
            score = match_tuple[1] if len(match_tuple) > 1 else 100
            table.add_row(match, str(score))
        console.print(table)
    Prompt.ask("Press Enter to return to the main menu")


def simulate_progress() -> None:
    """
    Simulate a progress bar for demonstration.
    """
    console.clear()
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing...", total=100)
        while not progress.finished:
            progress.update(task, advance=1)
            sleep(0.05)
    console.print("Processing complete!", style="bold green")
    Prompt.ask("Press Enter to return to the main menu")


def create_layout() -> Layout:
    """
    Create the main layout for the CLI interface.

    Returns:
        Configured Layout instance
    """
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=2),  # Reduced size
        Layout(name="body", ratio=1),
        Layout(name="footer", size=1),  # Reduced size
    )

    layout["header"].update(Text("=== Interactive CLI Menu ===", style="bold blue"))
    layout["footer"].update(Text("Press Ctrl+C to exit.", style="dim"))

    return layout


def list_files() -> None:
    """
    List files in a directory.
    """
    console.clear()
    directory = Prompt.ask("Enter directory path", default=".")
    try:
        directory_path = Path(directory)
        if not directory_path.is_dir():
            console.print("[bold red]Invalid directory path.[/bold red]")
        elif files := list(directory_path.iterdir()):
            table = Table(title=f"Files in {directory}", style="bold blue")
            table.add_column("Filename", style="white")
            table.add_column("Type", style="dim")
            table.add_column("Size", style="dim")

            for file in sorted(files):
                file_type = "Dir" if file.is_dir() else "File"
                try:
                    size = file.stat().st_size if file.is_file() else "-"
                    if isinstance(size, int):
                        size = f"{size:,} bytes"
                except OSError:
                    size = "N/A"
                table.add_row(file.name, file_type, str(size))
            console.print(table)
        else:
            console.print("[bold yellow]No files found in the directory.[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error listing files: {e}[/bold red]")
        logger.error(f"Error listing files: {e}")
    Prompt.ask("Press Enter to return to the main menu")


def display_option_details(choice: str) -> None:
    """
    Display detailed information about a menu option.

    Args:
        choice: The menu option number
    """
    details = {
        "1": (
            "Option One allows you to perform action X, which includes advanced "
            "features for data processing and analysis."
        ),
        "2": (
            "Option Two helps you manage Y by providing features like user management, "
            "preferences, and system configuration."
        ),
        "3": (
            "Option Three enables configuration Z with customizable themes, layouts, "
            "and display options."
        ),
        "4": (
            "Option Four provides monitoring capabilities for system performance "
            "and application metrics."
        ),
    }
    console.print(f"[bold yellow]{details.get(choice, 'No details available.')}[/bold yellow]")


def get_terminal_width() -> int:
    """
    Get the current terminal width.

    Returns:
        Terminal width in characters
    """
    return console.size.width


def searchable_help() -> None:
    """
    Search through help documentation.
    """
    console.clear()
    console.print("[bold magenta]Search Help Documentation[/bold magenta]")
    query = Prompt.ask("Enter keyword to search in help")

    # Comprehensive help contents
    help_contents = {
        "login": "To log in, select the login option from the main menu and enter your credentials.",
        "theme": (
            "Use the theme selection option to change the application's appearance. "
            "Available themes: default, dark, light, high_contrast."
        ),
        "exit": "Select option 0 or press Ctrl+C to exit the application. You'll be asked to confirm.",
        "search": "Use Ctrl+S for fuzzy search or select the search option from the menu.",
        "help": "Press Ctrl+H to display help at any time.",
        "weather": "Check weather by selecting the weather option and entering a city name.",
        "users": "Manage users through the user management submenu.",
        "export": "Export data to CSV or PDF formats through the export options.",
    }

    results = {k: v for k, v in help_contents.items() if query.lower() in k.lower() or query.lower() in v.lower()}

    if not results:
        console.print("[bold yellow]No help topics matched your query.[/bold yellow]")
    else:
        for topic, description in results.items():
            console.print(f"[bold]{topic.capitalize()}[/bold]: {description}")
    Prompt.ask("Press Enter to return to the main menu")


# Function to create a custom frame
def create_frame(content: str, width: int = 60, border_style: str = "bold magenta") -> Text:
    """
    Creates a framed text with the specified content and style.

    :param content: The inner content of the frame.
    :param width: The total width of the frame.
    :param border_style: The style/color of the border.
    :return: A Rich Text object with a custom frame.
    """
    # Use DOUBLE_LINE characters for the frame
    tl = DOUBLE_LINE["top_left"]
    tr = DOUBLE_LINE["top_right"]
    bl = DOUBLE_LINE["bottom_left"]
    br = DOUBLE_LINE["bottom_right"]
    h = DOUBLE_LINE["horizontal"]
    v = DOUBLE_LINE["vertical"]

    # Build the top border
    top_border = f"{tl}{h * (width - 2)}{tr}"

    # Split content into lines
    content_lines = content.split("\n")

    # Build the middle content with borders
    middle = ""
    for line in content_lines:
        # Remove leading/trailing spaces and pad the line to fit the width
        padded_line = line.strip().ljust(width - 4)
        middle += f"{v}  {padded_line}  {v}\n"

    # Build the bottom border
    bottom_border = f"{bl}{h * (width - 2)}{br}"

    # Combine all parts
    full_frame = f"{top_border}\n{middle}{bottom_border}"

    return Text(full_frame, style=border_style)


def get_users() -> List[Tuple[int, str, str]]:
    """
    Retrieve all users from the database.

    Returns:
        List of user tuples (id, name, preferences)

    Raises:
        DatabaseError: If retrieval fails
    """
    try:
        with sqlite3.connect(str(settings.database_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, preferences FROM users")
            users = cursor.fetchall()
        return users
    except sqlite3.Error as e:
        error_msg = f"Failed to retrieve users: {e}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logger.error(error_msg)
        raise DatabaseError(error_msg) from e


def export_help_to_pdf() -> None:
    """
    Export help documentation to PDF.

    Raises:
        FileOperationError: If export fails
    """
    help_text = """
<!DOCTYPE html>
<html>
<head>
    <title>Farmer CLI - Help Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        h2 { color: #666; }
        .option { margin: 20px 0; padding: 10px; background: #f5f5f5; }
    </style>
</head>
<body>
    <h1>Farmer CLI - Help Documentation</h1>
    <h2>Menu Options</h2>
    <div class="option">
        <h3>Option 1 - Data Processing</h3>
        <p>Perform advanced data processing and analysis tasks.</p>
    </div>
    <div class="option">
        <h3>Option 2 - User Management</h3>
        <p>Manage users, preferences, and system configuration.</p>
    </div>
    <div class="option">
        <h3>Option 3 - Configuration</h3>
        <p>Customize themes, layouts, and display options.</p>
    </div>
    <div class="option">
        <h3>Option 4 - Monitoring</h3>
        <p>Monitor system performance and application metrics.</p>
    </div>
    <h2>Keyboard Shortcuts</h2>
    <ul>
        <li><strong>Ctrl+C</strong>: Exit application</li>
        <li><strong>Ctrl+S</strong>: Search menu</li>
        <li><strong>Ctrl+H</strong>: Display help</li>
    </ul>
</body>
</html>
"""
    if not PDFKIT_AVAILABLE:
        error_msg = "pdfkit is not installed. Please install it with: pip install pdfkit"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logger.error(error_msg)
        raise FileOperationError(error_msg)

    try:
        help_file = Path("help.html")
        pdf_file = Path("help.pdf")

        with open(help_file, "w") as f:
            f.write(help_text)

        pdfkit.from_file(str(help_file), str(pdf_file))
        console.print("[bold green]Help exported to help.pdf successfully![/bold green]")

        # Clean up HTML file
        help_file.unlink()

    except Exception as e:
        error_msg = f"Failed to export help to PDF: {e}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logger.error(error_msg)
        raise FileOperationError(error_msg) from e


def export_users_to_csv() -> None:
    """
    Export users to CSV file.

    Raises:
        FileOperationError: If export fails
    """
    try:
        users = get_users()
        if not users:
            console.print("[bold yellow]No users to export.[/bold yellow]")
            return

        csv_file = Path("users_export.csv")
        with open(csv_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ID", "Name", "Preferences"])
            for user in users:
                writer.writerow(user)
        console.print(f"[bold green]Users exported to {csv_file} successfully![/bold green]")
    except DatabaseError:
        # Already handled in get_users
        pass
    except Exception as e:
        error_msg = f"Failed to export users to CSV: {e}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        logger.error(error_msg)
        raise FileOperationError(error_msg) from e


def manage_users() -> None:
    """
    User management submenu.
    """
    while True:
        console.clear()
        console.print("[bold magenta]User Management[/bold magenta]")
        console.print("1. Add User\n2. List Users\n3. Export Users to CSV\n0. Return to Main Menu")
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "0"], default="0")

        if choice == "1":
            name = Prompt.ask("Enter user name")
            preferences = Prompt.ask("Enter user preferences (JSON format)", default="{}")
            try:
                # Validate JSON format
                json.loads(preferences)
                add_user(name, preferences)
                sleep(2)
            except json.JSONDecodeError:
                console.print("[bold red]Invalid JSON format for preferences![/bold red]")
                sleep(2)
            except DatabaseError as e:
                logger.error(f"Failed to add user: {e}")
                sleep(2)
        elif choice == "2":
            try:
                users = get_users()
                if users:
                    user_table(users)
                else:
                    console.print("[bold yellow]No users found.[/bold yellow]")
                Prompt.ask("Press Enter to return to the User Management menu")
            except DatabaseError:
                sleep(2)
        elif choice == "3":
            try:
                export_users_to_csv()
                sleep(2)
            except FileOperationError:
                sleep(2)
        elif choice == "0":
            return


def user_table(users: List[Tuple[int, str, str]]) -> None:
    """
    Display users in a formatted table.

    Args:
        users: List of user tuples (id, name, preferences)
    """
    table = Table(title="Users", style="bold blue")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="bold cyan")
    table.add_column("Preferences", style="dim")
    for user in users:
        table.add_row(str(user[0]), user[1], user[2])
    console.print(table)


def display_help() -> None:
    """
    Display the main help screen.
    """
    console.clear()
    help_text = f"""
[bold magenta]Help - {settings.app_name} v{settings.app_version}[/bold magenta]

This application provides an interactive menu with the following options:

[bold]1. Option One - Data Processing[/bold]
Perform advanced data processing and analysis tasks.

[bold]2. Option Two - User Management[/bold]
Manage users, preferences, and system configuration.

[bold]3. Option Three - Configuration[/bold]
Customize themes, layouts, and display options.

[bold]4. Option Four - Monitoring[/bold]
Monitor system performance and application metrics.

[bold]0. Exit[/bold]
Exit the application (with confirmation).

[bold]Keyboard Shortcuts:[/bold]
- [bold]Ctrl+C[/bold]: Exit the application
- [bold]Ctrl+S[/bold]: Search the menu
- [bold]Ctrl+H[/bold]: Display this help

[bold]Features:[/bold]
- Weather checking
- User management
- Data export (CSV/PDF)
- Theme customization
- File browsing

[bold]Support:[/bold] support@farmercli.com
"""
    console.print(Align.center(Text(help_text, style="white"), vertical="top"))
    Prompt.ask("Press Enter to return to the main menu")


# Function to display the greeting message
def display_greeting() -> None:
    """
    Display the welcome greeting.
    """
    greeting = f"Welcome to {settings.app_name} v{settings.app_version}\nPlease see options below...❚"
    styled_greeting = Text(greeting, style="bold green")
    console.print(Align.center(styled_greeting, vertical="top"))
    sleep(1)  # Simulate typing cursor effect


def submenu_option_one() -> None:
    """
    Handle Option One submenu.
    """
    console.clear()
    console.print("[bold magenta]Data Processing Menu[/bold magenta]")
    console.print("\n1. Display Code Snippet")
    console.print("2. Show System Info")
    console.print("3. Display Sample Table")
    console.print("4. Simulate Progress")
    console.print("0. Return to Main Menu")

    choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "0"])

    if choice == "1":
        display_code_snippet()
    elif choice == "2":
        display_system_info()
    elif choice == "3":
        display_table()
    elif choice == "4":
        simulate_progress()


def submenu_option_two() -> None:
    """
    Handle Option Two submenu.
    """
    manage_users()


def display_help_menu() -> None:
    """
    Display help for menu options.
    """
    console.clear()
    console.print("[bold magenta]Help - Menu Options[/bold magenta]")
    for key, desc in HELP_TEXTS.items():
        console.print(f"[bold]{key}[/bold]: {desc}")
    console.print("\n[dim]Press Ctrl+S for search, Ctrl+H for full help[/dim]")
    Prompt.ask("Press Enter to return to the main menu")


def display_menu() -> Optional[str]:
    """
    Display the main menu and get user choice.

    Returns:
        User's menu choice or None if invalid
    """
    layout = create_layout()

    title = "[bold cyan]=== Main Menu ===[/bold cyan]"
    options = [
        "[1] Data Processing",
        "[2] User Management",
        "[3] Configuration",
        "[4] System Tools",
        "[0] Exit"
    ]

    menu_content = title + "\n" + "\n".join(options)
    theme = THEMES.get(current_theme, THEMES["default"])
    frame = create_frame(
        menu_content, width=60, border_style=theme["border_style"]
    )
    layout["body"].update(Align.center(frame, vertical="top"))

    console.print(layout)

    # Prompt for user choice
    choice = Prompt.ask("Enter your choice or type 'help' for assistance")
    if choice.lower() == "help":
        display_help_menu()
        return None
    elif choice in ["1", "2", "3", "4", "0"]:
        return choice
    else:
        console.print("[bold red]Invalid choice. Please try again.[/bold red]")
        sleep(1)
        return None


def confirm_exit() -> bool:
    """
    Confirm user wants to exit.

    Returns:
        True if user confirms exit
    """
    confirm = Prompt.ask("Are you sure you want to exit? (y/n)", choices=["y", "n"], default="n")
    return confirm.lower() == "y"


def submit_feedback() -> None:
    """
    Allow user to submit feedback.
    """
    console.clear()
    console.print("[bold magenta]Submit Feedback[/bold magenta]")
    feedback = Prompt.ask("Enter your feedback")

    # Save feedback to file
    try:
        feedback_file = Path("feedback.txt")
        with open(feedback_file, "a") as f:
            f.write(f"\n[{datetime.now().isoformat()}] {feedback}\n")
        logger.info(f"Feedback received: {feedback}")
        console.print("[bold green]Thank you for your feedback![/bold green]")
    except IOError as e:
        console.print(f"[bold red]Failed to save feedback: {e}[/bold red]")
        logger.error(f"Failed to save feedback: {e}")
    sleep(2)


def cleanup() -> None:
    """
    Perform cleanup actions before exit.
    """
    console.print("\n[bold red]Cleaning up before exit...[/bold red]")
    try:
        # Save current preferences
        preferences = load_preferences()
        preferences["last_exit"] = datetime.now().isoformat()
        save_preferences(preferences)

        # Close database session
        session.close()

        logger.info("Application exited gracefully.")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def main() -> None:
    """
    Main function to run the CLI application.
    """
    global current_theme

    try:
        # Initialize database
        initialize_db()

        # Load preferences
        preferences = load_preferences()
        current_theme = preferences.get("theme", settings.default_theme)

        # Main menu loop
        while True:
            console.clear()
            display_greeting()
            choice = display_menu()

            if choice is None:
                continue

            if choice == "1":
                submenu_option_one()
            elif choice == "2":
                submenu_option_two()
            elif choice == "3":
                # Configuration menu
                console.clear()
                console.print("[bold magenta]Configuration Menu[/bold magenta]")
                console.print("\n1. Select Theme")
                console.print("2. Display Current Time")
                console.print("3. Search Help")
                console.print("0. Return to Main Menu")

                config_choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "0"])
                if config_choice == "1":
                    select_theme()
                elif config_choice == "2":
                    display_current_time()
                elif config_choice == "3":
                    searchable_help()

            elif choice == "4":
                # System tools menu
                console.clear()
                console.print("[bold magenta]System Tools[/bold magenta]")
                console.print("\n1. List Files")
                console.print("2. Check Weather")
                console.print("3. Export Help to PDF")
                console.print("4. Submit Feedback")
                console.print("0. Return to Main Menu")

                tools_choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "0"])
                if tools_choice == "1":
                    list_files()
                elif tools_choice == "2":
                    display_weather_menu()
                elif tools_choice == "3":
                    try:
                        export_help_to_pdf()
                        sleep(2)
                    except FileOperationError:
                        sleep(2)
                elif tools_choice == "4":
                    submit_feedback()

            elif choice == "0":
                if confirm_exit():
                    console.print("\n[bold green]Thank you for using Farmer CLI![/bold green]")
                    console.print("Exiting the application. Goodbye!", style="bold red")
                    break

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Interrupted by user.[/bold yellow]")
        logger.info("Application interrupted by user")
    except DatabaseError as e:
        console.print(f"\n[bold red]Database error: {e}[/bold red]")
        logger.error(f"Database error in main: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        logger.error(f"Unexpected error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    atexit.register(cleanup)  # Register cleanup once
    main()
