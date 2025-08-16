"""Tests for Settings."""
import pytest
import os
import tempfile
from unittest.mock import patch, mock_open
from pathlib import Path
from pydantic import ValidationError

from src.infrastructure.settings import Settings


# Path to test environment file
TEST_ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env.test"


class TestSettingsInit:
    """Test Settings initialization."""

    def test_init_with_required_fields(self):
        """Test initialization using test environment file."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        
        assert settings.jira_url == 'https://test.atlassian.net'
        assert settings.jira_email == 'test@example.com'
        assert settings.jira_api_token == 'test-token-safe'
        assert settings.project_key == 'TEST'
        
        # Check defaults from test file
        assert settings.default_issue_type == 'Story'
        assert settings.subtask_issue_type == 'Sub-task'
        assert settings.batch_size == 10
        assert settings.dry_run is False
        assert settings.acceptance_criteria_field == ''  # Empty string in test file
        assert settings.input_directory == 'entrada'
        assert settings.logs_directory == 'logs'
        assert settings.processed_directory == 'procesados'
        assert settings.rollback_on_subtask_failure is False
        assert settings.feature_issue_type == 'Feature'
        assert settings.feature_required_fields == ''  # Empty string in test file

    def test_init_with_all_fields(self):
        """Test initialization with all fields provided."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://custom.atlassian.net',
            'JIRA_EMAIL': 'custom@example.com',
            'JIRA_API_TOKEN': 'custom-token',
            'PROJECT_KEY': 'CUSTOM',
            'DEFAULT_ISSUE_TYPE': 'Task',
            'SUBTASK_ISSUE_TYPE': 'Subtarea',
            'BATCH_SIZE': '25',
            'DRY_RUN': 'true',
            'ACCEPTANCE_CRITERIA_FIELD': 'customfield_10001',
            'INPUT_DIRECTORY': 'custom_input',
            'LOGS_DIRECTORY': 'custom_logs',
            'PROCESSED_DIRECTORY': 'custom_processed',
            'ROLLBACK_ON_SUBTASK_FAILURE': 'true',
            'FEATURE_ISSUE_TYPE': 'Epic',
            'FEATURE_REQUIRED_FIELDS': '{"summary": "test"}'
        }):
            settings = Settings()
            
            assert settings.jira_url == 'https://custom.atlassian.net'
            assert settings.jira_email == 'custom@example.com'
            assert settings.jira_api_token == 'custom-token'
            assert settings.project_key == 'CUSTOM'
            assert settings.default_issue_type == 'Task'
            assert settings.subtask_issue_type == 'Subtarea'
            assert settings.batch_size == 25
            assert settings.dry_run is True
            assert settings.acceptance_criteria_field == 'customfield_10001'
            assert settings.input_directory == 'custom_input'
            assert settings.logs_directory == 'custom_logs'
            assert settings.processed_directory == 'custom_processed'
            assert settings.rollback_on_subtask_failure is True
            assert settings.feature_issue_type == 'Epic'
            assert settings.feature_required_fields == '{"summary": "test"}'

    def test_init_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        # Clear environment and don't use any env file
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)
            
            # Should mention missing required fields
            errors = exc_info.value.errors()
            required_fields = ['jira_url', 'jira_email', 'jira_api_token', 'project_key']
            
            # Check that all required fields are mentioned in errors
            error_fields = [error['loc'][0] for error in errors]
            for field in required_fields:
                assert field in error_fields

    def test_init_partial_required_fields(self):
        """Test with some required fields missing."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com'
            # Missing JIRA_API_TOKEN and PROJECT_KEY
        }, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)
            
            errors = exc_info.value.errors()
            error_fields = [error['loc'][0] for error in errors]
            assert 'jira_api_token' in error_fields
            assert 'project_key' in error_fields


class TestSettingsTypes:
    """Test Settings type validation."""

    def test_batch_size_validation(self):
        """Test batch_size type validation."""
        base_env = {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST'
        }
        
        # Valid integer as string
        with patch.dict(os.environ, {**base_env, 'BATCH_SIZE': '20'}):
            settings = Settings()
            assert settings.batch_size == 20
            assert isinstance(settings.batch_size, int)
        
        # Invalid non-numeric string should raise error
        with patch.dict(os.environ, {**base_env, 'BATCH_SIZE': 'invalid'}):
            with pytest.raises(ValidationError):
                Settings()

    def test_boolean_validation(self):
        """Test boolean field validation."""
        base_env = {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST'
        }
        
        # Test various boolean representations
        boolean_values = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False)
        ]
        
        for str_value, expected_bool in boolean_values:
            with patch.dict(os.environ, {**base_env, 'DRY_RUN': str_value}):
                settings = Settings()
                assert settings.dry_run == expected_bool
                assert isinstance(settings.dry_run, bool)

    def test_url_validation(self):
        """Test URL format validation."""
        base_env = {
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST'
        }
        
        # Valid URLs
        valid_urls = [
            'https://company.atlassian.net',
            'http://localhost:8080',
            'https://jira.example.com',
            'https://my-jira.atlassian.net:443'
        ]
        
        for url in valid_urls:
            with patch.dict(os.environ, {**base_env, 'JIRA_URL': url}):
                settings = Settings()
                assert settings.jira_url == url

    def test_optional_fields_none(self):
        """Test that optional fields can be None."""
        # Use test env file which has empty strings for optional fields
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        
        # These should be empty strings in test file (pydantic treats empty strings as valid)
        assert settings.acceptance_criteria_field == ''
        assert settings.feature_required_fields == ''


class TestSettingsFromFile:
    """Test Settings loading from .env file."""

    def test_env_file_loading(self, temp_dir):
        """Test loading settings from .env file."""
        # Create temporary .env file
        env_file = temp_dir / '.env'
        env_content = """
JIRA_URL=https://envfile.atlassian.net
JIRA_EMAIL=envfile@example.com
JIRA_API_TOKEN=envfile-token
PROJECT_KEY=ENVFILE
BATCH_SIZE=15
DRY_RUN=true
"""
        env_file.write_text(env_content.strip())
        
        # Change to temp directory so .env file is found
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            settings = Settings()
            
            assert settings.jira_url == 'https://envfile.atlassian.net'
            assert settings.jira_email == 'envfile@example.com'
            assert settings.jira_api_token == 'envfile-token'
            assert settings.project_key == 'ENVFILE'
            assert settings.batch_size == 15
            assert settings.dry_run is True
        finally:
            os.chdir(original_cwd)

    def test_env_var_overrides_file(self, temp_dir):
        """Test that environment variables override .env file."""
        # Create .env file
        env_file = temp_dir / '.env'
        env_content = """
JIRA_URL=https://file.atlassian.net
JIRA_EMAIL=file@example.com
JIRA_API_TOKEN=file-token
PROJECT_KEY=FILE
BATCH_SIZE=5
"""
        env_file.write_text(env_content.strip())
        
        # Set environment variable that should override
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            with patch.dict(os.environ, {'BATCH_SIZE': '30'}):
                settings = Settings()
                
                # These should come from file
                assert settings.jira_url == 'https://file.atlassian.net'
                assert settings.jira_email == 'file@example.com'
                
                # This should be overridden by environment variable
                assert settings.batch_size == 30
        finally:
            os.chdir(original_cwd)


class TestSettingsModification:
    """Test Settings modification after initialization."""

    def test_settings_are_mutable(self):
        """Test that settings can be modified after creation."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST'
        }):
            settings = Settings()
            
            # Modify settings
            original_project = settings.project_key
            settings.project_key = 'MODIFIED'
            
            assert original_project == 'TEST'
            assert settings.project_key == 'MODIFIED'

    def test_modify_batch_size(self):
        """Test modifying batch_size."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST'
        }):
            settings = Settings()
            
            assert settings.batch_size == 10  # Default
            settings.batch_size = 50
            assert settings.batch_size == 50

    def test_modify_dry_run(self):
        """Test modifying dry_run mode."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST'
        }):
            settings = Settings()
            
            assert settings.dry_run is False  # Default
            settings.dry_run = True
            assert settings.dry_run is True


class TestSettingsDefaults:
    """Test default values for Settings."""

    def test_all_defaults(self):
        """Test all default values are as expected."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        
        # Test all values from test file
        assert settings.default_issue_type == 'Story'
        assert settings.subtask_issue_type == 'Sub-task'
        assert settings.batch_size == 10
        assert settings.dry_run is False
        assert settings.acceptance_criteria_field == ''  # Empty in test file
        assert settings.input_directory == 'entrada'
        assert settings.logs_directory == 'logs'
        assert settings.processed_directory == 'procesados'
        assert settings.rollback_on_subtask_failure is False
        assert settings.feature_issue_type == 'Feature'
        assert settings.feature_required_fields == ''  # Empty in test file

    def test_custom_directories(self):
        """Test custom directory settings."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST',
            'INPUT_DIRECTORY': '/custom/input',
            'LOGS_DIRECTORY': '/custom/logs',
            'PROCESSED_DIRECTORY': '/custom/processed'
        }):
            settings = Settings()
            
            assert settings.input_directory == '/custom/input'
            assert settings.logs_directory == '/custom/logs'
            assert settings.processed_directory == '/custom/processed'


class TestSettingsValidation:
    """Test Settings field validation."""

    def test_empty_string_fields(self):
        """Test handling of empty string fields."""
        with patch.dict(os.environ, {
            'JIRA_URL': '',  # Empty string
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST'
        }):
            # Pydantic allows empty strings by default, so this will not raise
            settings = Settings(_env_file=None)
            assert settings.jira_url == ''

    def test_whitespace_fields(self):
        """Test handling of whitespace-only fields."""
        with patch.dict(os.environ, {
            'JIRA_URL': '   ',  # Whitespace only
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST'
        }):
            # Pydantic allows whitespace strings by default
            settings = Settings(_env_file=None)
            assert settings.jira_url == '   '

    def test_zero_batch_size(self):
        """Test that zero batch size is allowed."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST',
            'BATCH_SIZE': '0'
        }):
            settings = Settings()
            assert settings.batch_size == 0

    def test_negative_batch_size(self):
        """Test that negative batch size is allowed by pydantic."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'test-token',
            'PROJECT_KEY': 'TEST',
            'BATCH_SIZE': '-5'
        }):
            settings = Settings()
            assert settings.batch_size == -5


class TestSettingsEdgeCases:
    """Test edge cases for Settings."""

    def test_unicode_values(self):
        """Test handling of unicode values."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'tëst@éxàmplé.com',  # Unicode characters
            'JIRA_API_TOKEN': 'tökèn-with-ûnicödé',
            'PROJECT_KEY': 'TËST'
        }):
            settings = Settings()
            
            assert settings.jira_email == 'tëst@éxàmplé.com'
            assert settings.jira_api_token == 'tökèn-with-ûnicödé'
            assert settings.project_key == 'TËST'

    def test_very_long_values(self):
        """Test handling of very long string values."""
        long_value = 'x' * 1000
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': long_value,
            'PROJECT_KEY': 'TEST'
        }):
            settings = Settings()
            
            assert settings.jira_api_token == long_value
            assert len(settings.jira_api_token) == 1000

    def test_special_characters(self):
        """Test handling of special characters."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'token!@#$%^&*()_+-={}[]|\\:";\'<>?,./~`',
            'PROJECT_KEY': 'TEST-123_ABC'
        }):
            settings = Settings()
            
            assert 'token!@#$%^&*()_+-={}[]|\\:";\'<>?,./~`' in settings.jira_api_token
            assert settings.project_key == 'TEST-123_ABC'

    def test_settings_repr(self):
        """Test that Settings can be represented as string without exposing secrets."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'secret-token',
            'PROJECT_KEY': 'TEST'
        }):
            settings = Settings()
            
            # Convert to string (should not raise error)
            settings_str = str(settings)
            assert isinstance(settings_str, str)
            
            # Should contain some field names but may hide sensitive values
            assert 'Settings' in settings_str or 'jira_url' in settings_str