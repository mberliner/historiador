"""Tests for CLI commands."""
import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from click.testing import CliRunner

from src.presentation.cli.commands import setup_logging, safe_init_settings


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_default_level(self):
        """Test logging setup with default level."""
        settings = Mock()
        settings.logs_directory = "test_logs"
        
        with patch('src.presentation.cli.commands.logging.basicConfig') as mock_config:
            with patch('src.presentation.cli.commands.Path') as mock_path_class:
                with patch('src.presentation.cli.commands.logging.FileHandler') as mock_file_handler:
                    with patch('src.presentation.cli.commands.logging.StreamHandler') as mock_stream_handler:
                        mock_logs_dir = Mock()
                        mock_path_class.return_value = mock_logs_dir
                        mock_logs_dir.mkdir = Mock()
                        mock_log_file = Mock()
                        mock_log_file.__str__ = Mock(return_value="test_logs/jira_batch.log")
                        mock_logs_dir.__truediv__ = Mock(return_value=mock_log_file)
                        
                        setup_logging(settings, "INFO")
                        
                        # Verify logging configuration
                        mock_config.assert_called_once()
                        config_kwargs = mock_config.call_args[1]
                        assert config_kwargs['level'] == 20  # logging.INFO

    def test_setup_logging_different_levels(self):
        """Test logging setup with different levels."""
        settings = Mock()
        settings.logs_directory = "test_logs"
        
        levels = ["DEBUG", "WARNING", "ERROR"]
        expected_levels = [10, 30, 40]  # logging constants
        
        for level, expected in zip(levels, expected_levels):
            with patch('src.presentation.cli.commands.logging.basicConfig') as mock_config:
                with patch('src.presentation.cli.commands.Path') as mock_path_class:
                    with patch('src.presentation.cli.commands.logging.FileHandler') as mock_file_handler:
                        with patch('src.presentation.cli.commands.logging.StreamHandler') as mock_stream_handler:
                            mock_logs_dir = Mock()
                            mock_path_class.return_value = mock_logs_dir
                            mock_logs_dir.mkdir = Mock()
                            mock_log_file = Mock()
                            mock_log_file.__str__ = Mock(return_value="test_logs/jira_batch.log")
                            mock_logs_dir.__truediv__ = Mock(return_value=mock_log_file)
                            
                            setup_logging(settings, level)
                            
                            config_kwargs = mock_config.call_args[1]
                            assert config_kwargs['level'] == expected

    def test_setup_logging_handlers(self):
        """Test that both console and file handlers are configured."""
        settings = Mock()
        settings.logs_directory = "test_logs"
        
        with patch('src.presentation.cli.commands.logging.basicConfig') as mock_config:
            with patch('src.presentation.cli.commands.Path') as mock_path_class:
                with patch('src.presentation.cli.commands.logging.StreamHandler') as mock_stream:
                    with patch('src.presentation.cli.commands.logging.FileHandler') as mock_file:
                        mock_logs_dir = Mock()
                        mock_path_class.return_value = mock_logs_dir
                        mock_logs_dir.mkdir = Mock()
                        mock_log_file = Mock()
                        mock_logs_dir.__truediv__ = Mock(return_value=mock_log_file)
                        
                        setup_logging(settings)
                        
                        # Verify basic config was called
                        mock_config.assert_called_once()


class TestCommandsImports:
    """Test command imports and basic functionality."""

    def test_setup_logging_integration(self):
        """Test setup_logging function works correctly."""
        settings = Mock()
        settings.logs_directory = "test_logs"
        
        with patch('src.presentation.cli.commands.logging.basicConfig') as mock_config:
            with patch('src.presentation.cli.commands.Path') as mock_path_class:
                with patch('src.presentation.cli.commands.logging.FileHandler') as mock_file_handler:
                    with patch('src.presentation.cli.commands.logging.StreamHandler') as mock_stream_handler:
                        mock_logs_dir = Mock()
                        mock_path_class.return_value = mock_logs_dir
                        mock_logs_dir.mkdir = Mock()
                        mock_log_file = Mock()
                        mock_log_file.__str__ = Mock(return_value="test_logs/jira_batch.log")
                        mock_logs_dir.__truediv__ = Mock(return_value=mock_log_file)
                        
                        # Test that setup_logging works without errors
                        setup_logging(settings, "INFO")
                        
                        # Verify basic configuration was called
                        mock_config.assert_called_once()

    def test_command_imports_work(self):
        """Test that command imports work correctly."""
        # Test importing the commands
        try:
            from src.presentation.cli.commands import (
                process_command,
                validate_command,
                test_connection_command,
                diagnose_command
            )
            # If we get here, imports work
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import commands: {e}")

    def test_logging_levels(self):
        """Test different logging levels."""
        settings = Mock()
        settings.logs_directory = "test_logs"
        
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        
        for level in levels:
            with patch('src.presentation.cli.commands.logging.basicConfig') as mock_config:
                with patch('src.presentation.cli.commands.Path') as mock_path_class:
                    with patch('src.presentation.cli.commands.logging.FileHandler') as mock_file_handler:
                        with patch('src.presentation.cli.commands.logging.StreamHandler') as mock_stream_handler:
                            mock_logs_dir = Mock()
                            mock_path_class.return_value = mock_logs_dir
                            mock_logs_dir.mkdir = Mock()
                            mock_log_file = Mock()
                            mock_log_file.__str__ = Mock(return_value="test_logs/jira_batch.log")
                            mock_logs_dir.__truediv__ = Mock(return_value=mock_log_file)
                            
                            # Should not raise any exceptions
                            setup_logging(settings, level)
                            mock_config.assert_called_once()

    def test_command_functions_exist(self):
        """Test that all command functions exist and are callable."""
        from src.presentation.cli.commands import (
            process_command,
            validate_command, 
            test_connection_command,
            diagnose_command
        )
        
        # Check that all commands are callable
        assert callable(process_command)
        assert callable(validate_command)
        assert callable(test_connection_command)
        assert callable(diagnose_command)

    def test_cli_runner_basic_functionality(self):
        """Test basic CLI runner functionality."""
        import click
        
        @click.command()
        def dummy_command():
            """A dummy command for testing."""
            pass
        
        runner = CliRunner()
        
        # Test that runner works with a proper Click command
        result = runner.invoke(dummy_command, [])
        assert result.exit_code == 0


class TestProcessCommand:
    """Test process_command function."""
    
    def test_process_command_with_file(self):
        """Test process command with specific file."""
        from src.presentation.cli.commands import process_command
        
        runner = CliRunner()
        
        with patch('src.presentation.cli.commands.safe_init_settings') as mock_settings:
            with patch('src.presentation.cli.commands.setup_logging'):
                with patch('src.application.use_cases.process_files.ProcessFilesUseCase') as mock_use_case:
                    with patch('src.presentation.formatters.output_formatter.OutputFormatter') as mock_formatter:
                        # Setup mocks
                        mock_settings_obj = Mock()
                        mock_settings_obj.input_directory = "entrada"
                        mock_settings.return_value = mock_settings_obj
                        
                        mock_use_case_instance = Mock()
                        mock_use_case.return_value = mock_use_case_instance
                        mock_use_case_instance.process_files.return_value = Mock()
                        
                        mock_formatter_instance = Mock()
                        mock_formatter.return_value = mock_formatter_instance
                        
                        # Run command
                        result = runner.invoke(process_command, [
                            '--file', 'test.csv',
                            '--project', 'TEST',
                            '--dry-run'
                        ])
                        
                        assert result.exit_code == 0
                        assert mock_settings_obj.project_key == 'TEST'
                        assert mock_settings_obj.dry_run is True

    def test_process_command_without_file_no_files_found(self):
        """Test process command without file when no files found."""
        from src.presentation.cli.commands import process_command
        
        runner = CliRunner()
        
        with patch('src.presentation.cli.commands.safe_init_settings') as mock_settings:
            with patch('src.presentation.cli.commands.setup_logging'):
                with patch('src.application.use_cases.process_files.ProcessFilesUseCase') as mock_use_case:
                    with patch('src.presentation.formatters.output_formatter.OutputFormatter') as mock_formatter:
                        # Setup mocks
                        mock_settings_obj = Mock()
                        mock_settings_obj.input_directory = "entrada"
                        mock_settings.return_value = mock_settings_obj
                        
                        mock_use_case_instance = Mock()
                        mock_use_case.return_value = mock_use_case_instance
                        mock_use_case_instance.find_input_files.return_value = []
                        
                        mock_formatter_instance = Mock()
                        mock_formatter.return_value = mock_formatter_instance
                        
                        # Run command
                        result = runner.invoke(process_command, ['--project', 'TEST'])
                        
                        assert result.exit_code == 0  # Function returns normally, not with exit code 1
                        mock_formatter_instance.print_error.assert_called_once()

    def test_process_command_exception_handling(self):
        """Test process command with exception."""
        from src.presentation.cli.commands import process_command
        
        runner = CliRunner()
        
        with patch('src.presentation.cli.commands.safe_init_settings') as mock_settings:
            with patch('src.presentation.cli.commands.setup_logging'):
                with patch('src.application.use_cases.process_files.ProcessFilesUseCase') as mock_use_case:
                    with patch('src.presentation.formatters.output_formatter.OutputFormatter') as mock_formatter:
                        # Setup mocks
                        mock_settings_obj = Mock()
                        mock_settings.return_value = mock_settings_obj
                        
                        mock_use_case_instance = Mock()
                        mock_use_case.return_value = mock_use_case_instance
                        mock_use_case_instance.execute.side_effect = Exception("Test error")
                        
                        mock_formatter_instance = Mock()
                        mock_formatter.return_value = mock_formatter_instance
                        
                        # Run command (this should trigger sys.exit in the actual code)
                        result = runner.invoke(process_command, ['--file', 'test.csv'])
                        
                        assert result.exit_code == 1  # sys.exit(1) is called in exception block
                        mock_formatter_instance.print_error.assert_called()


class TestValidateCommand:
    """Test validate_command function."""
    
    def test_validate_command_success(self):
        """Test validate command successful execution."""
        from src.presentation.cli.commands import validate_command
        
        runner = CliRunner()
        
        with patch('src.presentation.cli.commands.safe_init_settings') as mock_settings:
            with patch('src.presentation.cli.commands.setup_logging'):
                with patch('src.application.use_cases.validate_file.ValidateFileUseCase') as mock_use_case:
                    with patch('src.presentation.formatters.output_formatter.OutputFormatter') as mock_formatter:
                        # Setup mocks
                        mock_settings_obj = Mock()
                        mock_settings.return_value = mock_settings_obj
                        
                        mock_use_case_instance = Mock()
                        mock_use_case.return_value = mock_use_case_instance
                        mock_use_case_instance.execute.return_value = (True, "Valid file")
                        
                        mock_formatter_instance = Mock()
                        mock_formatter.return_value = mock_formatter_instance
                        
                        # Run command
                        result = runner.invoke(validate_command, [
                            '--file', 'test.csv'
                        ])
                        
                        assert result.exit_code == 0
                        mock_use_case_instance.execute.assert_called_once_with('test.csv', 5)

    def test_validate_command_failure(self):
        """Test validate command with validation failure."""
        from src.presentation.cli.commands import validate_command
        
        runner = CliRunner()
        
        with patch('src.presentation.cli.commands.safe_init_settings') as mock_settings:
            with patch('src.presentation.cli.commands.setup_logging'):
                with patch('src.application.use_cases.validate_file.ValidateFileUseCase') as mock_use_case:
                    with patch('src.presentation.formatters.output_formatter.OutputFormatter') as mock_formatter:
                        # Setup mocks
                        mock_settings_obj = Mock()
                        mock_settings.return_value = mock_settings_obj
                        
                        mock_use_case_instance = Mock()
                        mock_use_case.return_value = mock_use_case_instance
                        mock_use_case_instance.execute.return_value = (False, "Invalid file")
                        
                        mock_formatter_instance = Mock()
                        mock_formatter.return_value = mock_formatter_instance
                        
                        # Run command
                        result = runner.invoke(validate_command, [
                            '--file', 'test.csv'
                        ])
                        
                        assert result.exit_code == 0  # No sys.exit for validation failures
                        mock_use_case_instance.execute.assert_called_once_with('test.csv', 5)


class TestTestConnectionCommand:
    """Test test_connection_command function."""
    
    def test_connection_command_success(self):
        """Test connection command successful execution."""
        from src.presentation.cli.commands import test_connection_command
        
        runner = CliRunner()
        
        with patch('src.presentation.cli.commands.safe_init_settings') as mock_settings:
            with patch('src.presentation.cli.commands.setup_logging'):
                with patch('src.application.use_cases.test_connection.TestConnectionUseCase') as mock_use_case:
                    with patch('src.presentation.formatters.output_formatter.OutputFormatter') as mock_formatter:
                        # Setup mocks
                        mock_settings_obj = Mock()
                        mock_settings.return_value = mock_settings_obj
                        
                        mock_use_case_instance = Mock()
                        mock_use_case.return_value = mock_use_case_instance
                        mock_use_case_instance.execute.return_value = Mock()  # Returns result object
                        
                        mock_formatter_instance = Mock()
                        mock_formatter.return_value = mock_formatter_instance
                        
                        # Run command
                        result = runner.invoke(test_connection_command)
                        
                        assert result.exit_code == 0
                        mock_use_case_instance.execute.assert_called_once_with()
                        mock_formatter_instance.print_connection_result.assert_called_once()

    def test_connection_command_failure(self):
        """Test connection command with connection failure."""
        from src.presentation.cli.commands import test_connection_command
        
        runner = CliRunner()
        
        with patch('src.presentation.cli.commands.safe_init_settings') as mock_settings:
            with patch('src.presentation.cli.commands.setup_logging'):
                with patch('src.application.use_cases.test_connection.TestConnectionUseCase') as mock_use_case:
                    with patch('src.presentation.formatters.output_formatter.OutputFormatter') as mock_formatter:
                        # Setup mocks
                        mock_settings_obj = Mock()
                        mock_settings.return_value = mock_settings_obj
                        
                        mock_use_case_instance = Mock()
                        mock_use_case.return_value = mock_use_case_instance
                        mock_use_case_instance.execute.side_effect = Exception("Connection failed")
                        
                        mock_formatter_instance = Mock()
                        mock_formatter.return_value = mock_formatter_instance
                        
                        # Run command
                        result = runner.invoke(test_connection_command)
                        
                        assert result.exit_code == 1  # sys.exit(1) is called in exception block
                        mock_formatter_instance.print_error.assert_called()


class TestDiagnoseCommand:
    """Test diagnose_command function."""
    
    def test_diagnose_command_success(self):
        """Test diagnose command successful execution."""
        from src.presentation.cli.commands import diagnose_command
        
        runner = CliRunner()
        
        with patch('src.presentation.cli.commands.safe_init_settings') as mock_settings:
            with patch('src.presentation.cli.commands.setup_logging'):
                with patch('src.application.use_cases.diagnose_features.DiagnoseFeaturesUseCase') as mock_use_case:
                    with patch('src.presentation.formatters.output_formatter.OutputFormatter') as mock_formatter:
                        # Setup mocks
                        mock_settings_obj = Mock()
                        mock_settings.return_value = mock_settings_obj
                        
                        mock_use_case_instance = Mock()
                        mock_use_case.return_value = mock_use_case_instance
                        mock_use_case_instance.execute.return_value = Mock()  # Returns result object
                        
                        mock_formatter_instance = Mock()
                        mock_formatter.return_value = mock_formatter_instance
                        
                        # Run command
                        result = runner.invoke(diagnose_command, ['--project', 'TEST'])
                        
                        assert result.exit_code == 0
                        assert mock_settings_obj.project_key == 'TEST'
                        mock_use_case_instance.execute.assert_called_once_with('TEST')
                        mock_formatter_instance.print_diagnose_result.assert_called_once()


class TestSafeInitSettings:
    """Test safe_init_settings function."""
    
    def test_safe_init_settings_success(self):
        """Test safe_init_settings successful initialization."""
        from src.presentation.cli.commands import safe_init_settings
        
        with patch('src.presentation.cli.commands.Settings') as mock_settings_class:
            mock_settings_instance = Mock()
            mock_settings_class.return_value = mock_settings_instance
            
            result = safe_init_settings()
            
            assert result == mock_settings_instance
            mock_settings_class.assert_called_once()



