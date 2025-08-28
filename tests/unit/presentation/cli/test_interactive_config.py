"""Tests para configuración interactiva."""
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest
from click.testing import CliRunner

from src.presentation.cli.commands import safe_init_settings, _configure_interactively, _create_env_file
from src.infrastructure.settings import Settings
from pydantic import ValidationError


class TestInteractiveConfiguration:
    """Tests para configuración interactiva."""

    def test_safe_init_settings_with_valid_env(self):
        """Test que Settings se inicializa correctamente con .env válido."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@test.com',
            'JIRA_API_TOKEN': 'token123',
            'PROJECT_KEY': 'TEST'
        }):
            settings = safe_init_settings()
            assert isinstance(settings, Settings)
            assert settings.jira_url == 'https://test.atlassian.net'


    @patch('click.prompt')
    @patch('click.echo')
    @patch('src.presentation.cli.commands._create_env_file')
    def test_configure_interactively(self, mock_create_env, mock_echo, mock_prompt):
        """Test configuración interactiva completa."""
        missing_fields = [
            ('jira_url', 'JIRA_URL'),
            ('jira_email', 'JIRA_EMAIL'), 
            ('jira_api_token', 'JIRA_API_TOKEN'),
            ('project_key', 'PROJECT_KEY')
        ]
        
        mock_prompt.side_effect = [
            'https://test.atlassian.net',
            'test@test.com',
            'secret_token',
            'TEST'
        ]
        
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@test.com',
            'JIRA_API_TOKEN': 'secret_token',
            'PROJECT_KEY': 'TEST'
        }):
            result = _configure_interactively(missing_fields)
        
        assert isinstance(result, Settings)
        mock_create_env.assert_called_once()

    @patch('click.prompt')
    @patch('click.echo')
    @patch('src.presentation.cli.commands._create_env_file')
    def test_configure_interactively_with_optional_field(self, mock_create_env, mock_echo, mock_prompt):
        """Test configuración interactiva con campo opcional."""
        missing_fields = [
            ('jira_url', 'JIRA_URL'),
            ('acceptance_criteria_field', 'ACCEPTANCE_CRITERIA_FIELD')
        ]
        
        mock_prompt.side_effect = [
            'https://test.atlassian.net',
            ''  # Campo opcional vacío
        ]
        
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@test.com',
            'JIRA_API_TOKEN': 'token',
            'PROJECT_KEY': 'TEST'
        }):
            _configure_interactively(missing_fields)
        
        # Verificar que el campo opcional no se pasó a _create_env_file
        call_args = mock_create_env.call_args[0][0]
        assert 'ACCEPTANCE_CRITERIA_FIELD' not in call_args

    def test_create_env_file_basic(self):
        """Test creación básica de archivo .env."""
        env_values = {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@test.com', 
            'JIRA_API_TOKEN': 'token123',
            'PROJECT_KEY': 'TEST'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                _create_env_file(env_values)
                
                env_file = Path('.env')
                assert env_file.exists()
                
                content = env_file.read_text()
                assert 'JIRA_URL=https://test.atlassian.net' in content
                assert 'JIRA_EMAIL=test@test.com' in content
                assert 'PROJECT_KEY=TEST' in content
                assert 'DEFAULT_ISSUE_TYPE=Story' in content
                
            finally:
                os.chdir(original_cwd)

    def test_create_env_file_with_optional_field(self):
        """Test creación de archivo .env con campo opcional."""
        env_values = {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@test.com',
            'JIRA_API_TOKEN': 'token123', 
            'PROJECT_KEY': 'TEST',
            'ACCEPTANCE_CRITERIA_FIELD': 'customfield_10001'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                _create_env_file(env_values)
                
                content = Path('.env').read_text()
                assert 'ACCEPTANCE_CRITERIA_FIELD=customfield_10001' in content
                
            finally:
                os.chdir(original_cwd)

    @patch('click.prompt')
    def test_interactive_api_token_hidden(self, mock_prompt):
        """Test que el API token se solicita con hide_input=True."""
        missing_fields = [('jira_api_token', 'JIRA_API_TOKEN')]
        
        mock_prompt.return_value = 'secret_token'
        
        with patch('src.presentation.cli.commands._create_env_file'), \
             patch.dict(os.environ, {
                 'JIRA_URL': 'https://test.atlassian.net',
                 'JIRA_EMAIL': 'test@test.com',
                 'JIRA_API_TOKEN': 'secret_token',
                 'PROJECT_KEY': 'TEST'
             }):
            _configure_interactively(missing_fields)
        
        mock_prompt.assert_called_once_with('API Token de Jira', hide_input=True, type=str)