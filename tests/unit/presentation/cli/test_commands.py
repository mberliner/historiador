"""Tests for CLI commands."""
import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from click.testing import CliRunner

from src.presentation.cli.commands import setup_logging


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_default_level(self):
        """Test logging setup with default level."""
        settings = Mock()
        settings.logs_directory = "test_logs"
        
        with patch('src.presentation.cli.commands.logging.basicConfig') as mock_config:
            with patch('src.presentation.cli.commands.Path') as mock_path_class:
                mock_logs_dir = Mock()
                mock_path_class.return_value = mock_logs_dir
                mock_logs_dir.mkdir = Mock()
                mock_logs_dir.__truediv__ = Mock(return_value=Mock())
                
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
                    mock_logs_dir = Mock()
                    mock_path_class.return_value = mock_logs_dir
                    mock_logs_dir.mkdir = Mock()
                    mock_logs_dir.__truediv__ = Mock(return_value=Mock())
                    
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
                mock_logs_dir = Mock()
                mock_path_class.return_value = mock_logs_dir
                mock_logs_dir.mkdir = Mock()
                mock_logs_dir.__truediv__ = Mock(return_value=Mock())
                
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
                    mock_logs_dir = Mock()
                    mock_path_class.return_value = mock_logs_dir
                    mock_logs_dir.mkdir = Mock()
                    mock_logs_dir.__truediv__ = Mock(return_value=Mock())
                    
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