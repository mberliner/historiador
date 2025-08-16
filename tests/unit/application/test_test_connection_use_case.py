"""Tests for TestConnectionUseCase."""
import pytest
from unittest.mock import Mock, patch

from src.application.use_cases.test_connection import TestConnectionUseCase


class TestTestConnectionUseCaseInit:
    """Test TestConnectionUseCase initialization."""

    def test_init(self):
        """Test proper initialization."""
        use_case = TestConnectionUseCase()
        
        # No instance variables to test, just ensure it initializes


class TestExecuteMethod:
    """Test execute method with various scenarios."""

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_successful_connection_and_project(self, mock_settings, mock_jira_client):
        """Test successful connection and project validation."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = TestConnectionUseCase()
        result = use_case.execute()
        
        # Verify result
        assert result['connection_success'] is True
        assert result['project_valid'] is True
        assert result['project_key'] == "TEST"
        
        # Verify mock calls
        mock_settings.assert_called_once()
        mock_jira_client.assert_called_once_with(mock_settings_instance)
        mock_jc_instance.test_connection.assert_called_once()
        mock_jc_instance.validate_project.assert_called_once_with("TEST")

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_connection_fails(self, mock_settings, mock_jira_client):
        """Test when connection fails."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = False
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = TestConnectionUseCase()
        result = use_case.execute()
        
        # Verify result
        assert result['connection_success'] is False
        assert result['project_valid'] is False  # Should not be validated if connection fails
        assert result['project_key'] == "TEST"
        
        # Verify mock calls
        mock_jc_instance.test_connection.assert_called_once()
        mock_jc_instance.validate_project.assert_not_called()  # Should not be called if connection fails

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_connection_success_project_invalid(self, mock_settings, mock_jira_client):
        """Test when connection succeeds but project validation fails."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "INVALID"
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = False
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = TestConnectionUseCase()
        result = use_case.execute()
        
        # Verify result
        assert result['connection_success'] is True
        assert result['project_valid'] is False
        assert result['project_key'] == "INVALID"
        
        # Verify mock calls
        mock_jc_instance.test_connection.assert_called_once()
        mock_jc_instance.validate_project.assert_called_once_with("INVALID")

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_with_different_project_keys(self, mock_settings, mock_jira_client):
        """Test with different project keys."""
        test_cases = [
            "PROJ",
            "MYPROJECT",
            "TEST-123",
            "A",
            "VERY-LONG-PROJECT-KEY"
        ]
        
        for project_key in test_cases:
            # Setup mocks
            mock_settings_instance = Mock()
            mock_settings_instance.project_key = project_key
            mock_settings.return_value = mock_settings_instance
            
            mock_jc_instance = Mock()
            mock_jc_instance.test_connection.return_value = True
            mock_jc_instance.validate_project.return_value = True
            mock_jira_client.return_value = mock_jc_instance
            
            use_case = TestConnectionUseCase()
            result = use_case.execute()
            
            assert result['project_key'] == project_key
            mock_jc_instance.validate_project.assert_called_with(project_key)
            
            # Reset mocks for next iteration
            mock_settings.reset_mock()
            mock_jira_client.reset_mock()

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_result_structure(self, mock_settings, mock_jira_client):
        """Test that result has correct structure."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = TestConnectionUseCase()
        result = use_case.execute()
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'connection_success' in result
        assert 'project_valid' in result
        assert 'project_key' in result
        assert len(result) == 3  # Should have exactly these 3 keys
        
        # Verify types
        assert isinstance(result['connection_success'], bool)
        assert isinstance(result['project_valid'], bool)
        assert isinstance(result['project_key'], str)


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_settings_creation_error(self, mock_settings, mock_jira_client):
        """Test handling of settings creation error."""
        mock_settings.side_effect = Exception("Settings error")
        
        use_case = TestConnectionUseCase()
        
        with pytest.raises(Exception, match="Settings error"):
            use_case.execute()

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_jira_client_creation_error(self, mock_settings, mock_jira_client):
        """Test handling of JiraClient creation error."""
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings.return_value = mock_settings_instance
        
        mock_jira_client.side_effect = Exception("JiraClient error")
        
        use_case = TestConnectionUseCase()
        
        with pytest.raises(Exception, match="JiraClient error"):
            use_case.execute()

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_connection_test_error(self, mock_settings, mock_jira_client):
        """Test handling of connection test error."""
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.side_effect = Exception("Connection error")
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = TestConnectionUseCase()
        
        with pytest.raises(Exception, match="Connection error"):
            use_case.execute()

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_project_validation_error(self, mock_settings, mock_jira_client):
        """Test handling of project validation error."""
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.side_effect = Exception("Project validation error")
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = TestConnectionUseCase()
        
        with pytest.raises(Exception, match="Project validation error"):
            use_case.execute()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_empty_project_key(self, mock_settings, mock_jira_client):
        """Test with empty project key."""
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = ""
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = False  # Empty key should be invalid
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = TestConnectionUseCase()
        result = use_case.execute()
        
        assert result['project_key'] == ""
        assert result['connection_success'] is True
        assert result['project_valid'] is False
        mock_jc_instance.validate_project.assert_called_once_with("")

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_none_project_key(self, mock_settings, mock_jira_client):
        """Test with None project key."""
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = None
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = False
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = TestConnectionUseCase()
        result = use_case.execute()
        
        assert result['project_key'] is None
        assert result['connection_success'] is True
        assert result['project_valid'] is False
        mock_jc_instance.validate_project.assert_called_once_with(None)

    @patch('src.application.use_cases.test_connection.JiraClient')
    @patch('src.application.use_cases.test_connection.Settings')
    def test_execute_multiple_calls_independence(self, mock_settings, mock_jira_client):
        """Test that multiple calls are independent."""
        # First call - success
        mock_settings_instance1 = Mock()
        mock_settings_instance1.project_key = "TEST1"
        
        mock_jc_instance1 = Mock()
        mock_jc_instance1.test_connection.return_value = True
        mock_jc_instance1.validate_project.return_value = True
        
        # Second call - failure
        mock_settings_instance2 = Mock()
        mock_settings_instance2.project_key = "TEST2"
        
        mock_jc_instance2 = Mock()
        mock_jc_instance2.test_connection.return_value = False
        
        mock_settings.side_effect = [mock_settings_instance1, mock_settings_instance2]
        mock_jira_client.side_effect = [mock_jc_instance1, mock_jc_instance2]
        
        use_case = TestConnectionUseCase()
        
        # First call
        result1 = use_case.execute()
        assert result1['connection_success'] is True
        assert result1['project_valid'] is True
        assert result1['project_key'] == "TEST1"
        
        # Second call
        result2 = use_case.execute()
        assert result2['connection_success'] is False
        assert result2['project_valid'] is False
        assert result2['project_key'] == "TEST2"