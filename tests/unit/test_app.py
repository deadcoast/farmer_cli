"""
Unit tests for farmer_cli.core.app module.

Tests the FarmerCLI application class including initialization,
feature registration, and menu action handling.

Feature: farmer-cli-completion
Requirements: 9.1, 9.3
"""

from unittest.mock import MagicMock
from unittest.mock import patch


class TestFarmerCLIInit:
    """Tests for FarmerCLI initialization."""

    def test_initializes_running_false(self):
        """Test that running is initialized to False."""
        with (
            patch("farmer_cli.core.app.get_database_manager"),
            patch("farmer_cli.core.app.PreferencesService"),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()

            assert app.running is False

    def test_initializes_with_default_theme(self):
        """Test that current_theme is set from settings."""
        with (
            patch("farmer_cli.core.app.get_database_manager"),
            patch("farmer_cli.core.app.PreferencesService"),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings") as mock_settings,
        ):
            mock_settings.default_theme = "dark"
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()

            assert app.current_theme == "dark"

    def test_initializes_preferences_service(self):
        """Test that preferences service is initialized."""
        with (
            patch("farmer_cli.core.app.get_database_manager"),
            patch("farmer_cli.core.app.PreferencesService") as mock_prefs,
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()

            mock_prefs.assert_called_once()
            assert app.preferences_service is not None

    def test_initializes_menu_manager(self):
        """Test that menu manager is initialized."""
        with (
            patch("farmer_cli.core.app.get_database_manager"),
            patch("farmer_cli.core.app.PreferencesService"),
            patch("farmer_cli.core.app.MenuManager") as mock_menu,
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()

            mock_menu.assert_called_once()
            assert app.menu_manager is not None

    def test_initializes_features_dict(self):
        """Test that features dictionary is initialized."""
        with (
            patch("farmer_cli.core.app.get_database_manager"),
            patch("farmer_cli.core.app.PreferencesService"),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()

            assert isinstance(app.features, dict)
            assert "video_downloader" in app.features
            assert "data_processing" in app.features
            assert "user_management" in app.features
            assert "configuration" in app.features
            assert "system_tools" in app.features

    def test_initializes_database_manager(self):
        """Test that database manager is initialized."""
        with (
            patch("farmer_cli.core.app.get_database_manager") as mock_db,
            patch("farmer_cli.core.app.PreferencesService"),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()

            mock_db.assert_called_once()
            assert app.db_manager is not None


class TestFarmerCLIInitialize:
    """Tests for FarmerCLI.initialize method."""

    def test_initializes_database(self):
        """Test that database is initialized."""
        mock_db = MagicMock()
        mock_db.validate_integrity.return_value = (True, [])
        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {"theme": "default"}

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.console"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app.initialize()

            mock_db.initialize.assert_called_once()

    def test_validates_database_integrity(self):
        """Test that database integrity is validated."""
        mock_db = MagicMock()
        mock_db.validate_integrity.return_value = (True, [])
        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {"theme": "default"}

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.console"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app.initialize()

            mock_db.validate_integrity.assert_called_once()

    def test_loads_preferences(self):
        """Test that preferences are loaded."""
        mock_db = MagicMock()
        mock_db.validate_integrity.return_value = (True, [])
        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {"theme": "dark"}

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.console"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app.initialize()

            mock_prefs.load.assert_called()

    def test_applies_theme_from_preferences(self):
        """Test that theme is applied from preferences."""
        mock_db = MagicMock()
        mock_db.validate_integrity.return_value = (True, [])
        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {"theme": "ocean"}

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.console"),
            patch("farmer_cli.core.app.THEMES", {"ocean": {}, "default": {}}),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app.initialize()

            assert app.current_theme == "ocean"

    def test_attempts_repair_on_integrity_issues(self):
        """Test that repair is attempted when integrity issues found."""
        mock_db = MagicMock()
        mock_db.validate_integrity.return_value = (False, ["Issue 1"])
        mock_db.repair_database.return_value = True
        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {"theme": "default"}

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.console"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app.initialize()

            mock_db.repair_database.assert_called_once()


class TestHandleMenuChoice:
    """Tests for FarmerCLI._handle_menu_choice method."""

    def test_exit_choice_sets_running_false(self):
        """Test that exit choice sets running to False."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.MENU_ACTIONS", {"0": "exit"}),
            patch("farmer_cli.core.app.console"),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app.running = True

            # Mock confirm_exit to return True
            with patch.object(app, "_confirm_exit", return_value=True):
                app._handle_menu_choice("0")

            assert app.running is False

    def test_exit_choice_cancelled(self):
        """Test that exit is cancelled when not confirmed."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.MENU_ACTIONS", {"0": "exit"}),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app.running = True

            # Mock confirm_exit to return False
            with patch.object(app, "_confirm_exit", return_value=False):
                app._handle_menu_choice("0")

            assert app.running is True

    def test_feature_choice_executes_feature(self):
        """Test that feature choice executes the feature."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()
        mock_feature = MagicMock()

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature", return_value=mock_feature),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.MENU_ACTIONS", {"1": "video_downloader"}),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app._handle_menu_choice("1")

            mock_feature.execute.assert_called_once()

    def test_feature_error_handled(self):
        """Test that feature execution errors are handled."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()
        mock_feature = MagicMock()
        mock_feature.execute.side_effect = RuntimeError("Test error")

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature", return_value=mock_feature),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.MENU_ACTIONS", {"1": "video_downloader"}),
            patch("farmer_cli.core.app.console") as mock_console,
        ):
            mock_console.input.return_value = ""
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            # Should not raise
            app._handle_menu_choice("1")

            # Should print error message
            mock_console.print.assert_called()


class TestApplyTheme:
    """Tests for FarmerCLI._apply_theme method."""

    def test_applies_valid_theme(self):
        """Test that valid theme is applied."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.THEMES", {"ocean": {}, "default": {}}),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app._apply_theme("ocean")

            assert app.current_theme == "ocean"

    def test_falls_back_to_default_for_unknown_theme(self):
        """Test that unknown theme falls back to default."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.THEMES", {"default": {}}),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app._apply_theme("nonexistent")

            assert app.current_theme == "default"


class TestChangeTheme:
    """Tests for FarmerCLI.change_theme method."""

    def test_changes_theme(self):
        """Test that theme is changed."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {}

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.THEMES", {"forest": {}, "default": {}}),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app.change_theme("forest")

            assert app.current_theme == "forest"

    def test_saves_theme_preference(self):
        """Test that theme preference is saved."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {}

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.THEMES", {"forest": {}, "default": {}}),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            app.change_theme("forest")

            mock_prefs.save.assert_called()
            saved_prefs = mock_prefs.save.call_args[0][0]
            assert saved_prefs["theme"] == "forest"


class TestConfirmExit:
    """Tests for FarmerCLI._confirm_exit method."""

    def test_returns_true_on_confirmation(self):
        """Test that True is returned on confirmation."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.ui.prompts.confirm_prompt", return_value=True),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            result = app._confirm_exit()

            assert result is True

    def test_returns_false_on_cancel(self):
        """Test that False is returned on cancel."""
        mock_db = MagicMock()
        mock_prefs = MagicMock()

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager"),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.ui.prompts.confirm_prompt", return_value=False),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            result = app._confirm_exit()

            assert result is False


class TestRun:
    """Tests for FarmerCLI.run method."""

    def test_returns_zero_on_clean_exit(self):
        """Test that run returns 0 on clean exit."""
        mock_db = MagicMock()
        mock_db.validate_integrity.return_value = (True, [])
        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {"theme": "default"}
        mock_menu = MagicMock()
        # Return None to skip menu, then exit
        mock_menu.display_main_menu.side_effect = [None, "0"]

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager", return_value=mock_menu),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.console"),
            patch("farmer_cli.core.app.MENU_ACTIONS", {"0": "exit"}),
            patch("farmer_cli.ui.prompts.confirm_prompt", return_value=True),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()
            result = app.run()

            assert result == 0

    def test_sets_running_true(self):
        """Test that running is set to True during run."""
        mock_db = MagicMock()
        mock_db.validate_integrity.return_value = (True, [])
        mock_prefs = MagicMock()
        mock_prefs.load.return_value = {"theme": "default"}
        mock_menu = MagicMock()
        mock_menu.display_main_menu.return_value = "0"

        with (
            patch("farmer_cli.core.app.get_database_manager", return_value=mock_db),
            patch("farmer_cli.core.app.PreferencesService", return_value=mock_prefs),
            patch("farmer_cli.core.app.MenuManager", return_value=mock_menu),
            patch("farmer_cli.core.app.VideoDownloaderFeature"),
            patch("farmer_cli.core.app.DataProcessingFeature"),
            patch("farmer_cli.core.app.UserManagementFeature"),
            patch("farmer_cli.core.app.ConfigurationFeature"),
            patch("farmer_cli.core.app.SystemToolsFeature"),
            patch("farmer_cli.core.app.settings"),
            patch("farmer_cli.core.app.console"),
            patch("farmer_cli.core.app.MENU_ACTIONS", {"0": "exit"}),
            patch("farmer_cli.ui.prompts.confirm_prompt", return_value=True),
        ):
            from farmer_cli.core.app import FarmerCLI

            app = FarmerCLI()

            # Capture running state during execution
            running_during_loop = []

            original_handle = app._handle_menu_choice

            def capture_running(choice):
                running_during_loop.append(app.running)
                return original_handle(choice)

            app._handle_menu_choice = capture_running
            app.run()

            assert True in running_during_loop
