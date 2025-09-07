"""Tests for CLI commands."""
import pytest
import sys
import logging
import json
import requests
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from click.testing import CliRunner
from pydantic import ValidationError

from src.presentation.cli.commands import (
    setup_logging, 
    safe_init_settings
)
from src.infrastructure.settings import Settings


class TestSafeInitSettings:
    """Test safe_init_settings function."""

    @patch('src.presentation.cli.commands.Settings')
    def test_safe_init_settings_success(self, mock_settings_class):
        """Test successful settings initialization."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings
        
        result = safe_init_settings()
        
        assert result == mock_settings
        mock_settings_class.assert_called_once()

    @patch('src.presentation.cli.commands.Settings')
    @patch('src.presentation.cli.commands.click.confirm')
    @patch('src.presentation.cli.commands.click.echo')
    @patch('src.presentation.cli.commands.sys.exit')
    def test_safe_init_settings_validation_error_interactive_no(self, mock_exit, mock_echo, mock_confirm, mock_settings_class):
        """Test ValidationError with interactive configuration rejection."""
        # Create a ValidationError with missing fields
        validation_error = ValidationError.from_exception_data('ValidationError', [
            {'type': 'missing', 'loc': ('jira_url',), 'msg': 'Field required'}
        ])
        
        mock_settings_class.side_effect = validation_error
        mock_confirm.return_value = False
        
        safe_init_settings()
        
        mock_echo.assert_any_call("[ERROR] Configuracion faltante.", err=True)
        mock_exit.assert_called_once_with(1)

    @patch('src.presentation.cli.commands.sys.exit')
    @patch('src.presentation.cli.commands.click.echo')
    @patch('src.presentation.cli.commands.click.confirm')
    @patch('src.presentation.cli.commands.Settings')
    def test_safe_init_settings_validation_error_non_missing(self, mock_settings_class, mock_confirm, mock_echo, mock_exit):
        """Test ValidationError with non-missing error types."""
        # Create a ValidationError with non-missing error type 
        validation_error = ValidationError.from_exception_data('ValidationError', [
            {'type': 'string_type', 'loc': ('project_key',), 'msg': 'Input should be a valid string'}
        ])
        
        mock_settings_class.side_effect = validation_error
        mock_confirm.return_value = False  # User declines interactive config
        
        safe_init_settings()
        
        # Should still handle as missing fields scenario and exit
        mock_echo.assert_any_call("[ERROR] Configuracion faltante.", err=True)
        mock_exit.assert_called_once_with(1)


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

    def test_setup_logging_creates_directory(self):
        """Test that logs directory is created."""
        settings = Mock()
        settings.logs_directory = "test_logs"
        
        with patch('src.presentation.cli.commands.logging.basicConfig'):
            with patch('src.presentation.cli.commands.Path') as mock_path_class:
                with patch('src.presentation.cli.commands.logging.FileHandler'):
                    with patch('src.presentation.cli.commands.logging.StreamHandler'):
                        mock_logs_dir = Mock()
                        mock_path_class.return_value = mock_logs_dir
                        mock_log_file = Mock()
                        mock_log_file.__str__ = Mock(return_value="test_logs/jira_batch.log")
                        mock_logs_dir.__truediv__ = Mock(return_value=mock_log_file)
                        
                        setup_logging(settings, "INFO")
                        
                        # Verify directory creation
                        mock_path_class.assert_called_once_with("test_logs")
                        mock_logs_dir.mkdir.assert_called_once_with(exist_ok=True)

    def test_setup_logging_log_file_path(self):
        """Test that log file path is correctly constructed."""
        settings = Mock()
        settings.logs_directory = "custom_logs"
        
        with patch('src.presentation.cli.commands.logging.basicConfig'):
            with patch('src.presentation.cli.commands.Path') as mock_path_class:
                with patch('src.presentation.cli.commands.logging.FileHandler') as mock_file_handler:
                    mock_logs_dir = Mock()
                    mock_path_class.return_value = mock_logs_dir
                    mock_log_file = Mock()
                    mock_log_file.__str__ = Mock(return_value="custom_logs/jira_batch.log")
                    mock_logs_dir.__truediv__ = Mock(return_value=mock_log_file)
                    
                    setup_logging(settings, "DEBUG")
                    
                    # Verify log file path construction
                    mock_logs_dir.__truediv__.assert_called_once_with("jira_batch.log")

    def test_setup_logging_silences_external_loggers(self):
        """Test that external loggers are silenced."""
        settings = Mock()
        settings.logs_directory = "test_logs"
        
        with patch('src.presentation.cli.commands.logging.basicConfig'):
            with patch('src.presentation.cli.commands.Path') as mock_path_class:
                with patch('src.presentation.cli.commands.logging.FileHandler'):
                    with patch('src.presentation.cli.commands.logging.getLogger') as mock_get_logger:
                        mock_logs_dir = Mock()
                        mock_path_class.return_value = mock_logs_dir
                        mock_log_file = Mock()
                        mock_log_file.__str__ = Mock(return_value="test_logs/jira_batch.log")
                        mock_logs_dir.__truediv__ = Mock(return_value=mock_log_file)
                        
                        mock_urllib3_logger = Mock()
                        mock_requests_logger = Mock()
                        
                        def get_logger_side_effect(name):
                            if name == "urllib3":
                                return mock_urllib3_logger
                            elif name == "requests":
                                return mock_requests_logger
                            return Mock()
                        
                        mock_get_logger.side_effect = get_logger_side_effect
                        
                        setup_logging(settings, "INFO")
                        
                        # Verify external loggers are silenced
                        mock_urllib3_logger.setLevel.assert_called_once_with(30)  # WARNING
                        mock_requests_logger.setLevel.assert_called_once_with(30)  # WARNING