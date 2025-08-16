"""Tests for Jira utils."""
import json
import pytest
import requests
from unittest.mock import Mock, patch
import logging

from src.infrastructure.jira.utils import (
    get_issue_types,
    handle_http_error, 
    validate_issue_exists
)


class TestGetIssueTypes:
    """Test get_issue_types function."""

    def test_get_issue_types_success(self):
        """Test successful retrieval of issue types."""
        # Mock session and response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Story", "description": "User story"},
                    {"id": "2", "name": "Task", "description": "Task"},
                    {"id": "3", "name": "Sub-task", "description": "Subtask"}
                ]
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        result = get_issue_types(mock_session, "https://test.atlassian.net", "TEST")
        
        # Verify result
        assert len(result) == 3
        assert result[0]["name"] == "Story"
        assert result[1]["name"] == "Task"
        assert result[2]["name"] == "Sub-task"
        
        # Verify API call
        expected_url = "https://test.atlassian.net/rest/api/3/issue/createmeta?projectKeys=TEST&expand=projects.issuetypes"
        mock_session.get.assert_called_once_with(expected_url)

    def test_get_issue_types_empty_projects(self):
        """Test handling when no projects are returned."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"projects": []}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        with patch('src.infrastructure.jira.utils.logger') as mock_logger:
            result = get_issue_types(mock_session, "https://test.atlassian.net", "TEST")
            
            assert result == []
            mock_logger.warning.assert_called_once_with("No se encontraron proyectos en createmeta")

    def test_get_issue_types_no_projects_key(self):
        """Test handling when projects key is missing."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {}  # No projects key
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        with patch('src.infrastructure.jira.utils.logger') as mock_logger:
            result = get_issue_types(mock_session, "https://test.atlassian.net", "TEST")
            
            assert result == []
            mock_logger.warning.assert_called_once_with("No se encontraron proyectos en createmeta")

    def test_get_issue_types_no_issuetypes(self):
        """Test handling when project has no issuetypes."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "projects": [{}]  # No issuetypes key
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        result = get_issue_types(mock_session, "https://test.atlassian.net", "TEST")
        
        assert result == []

    def test_get_issue_types_http_error(self):
        """Test handling of HTTP errors."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        with patch('src.infrastructure.jira.utils.logger') as mock_logger:
            result = get_issue_types(mock_session, "https://test.atlassian.net", "INVALID")
            
            assert result == []
            mock_logger.error.assert_called_once_with("Error obteniendo tipos de issue: %s", "404 Not Found")

    def test_get_issue_types_connection_error(self):
        """Test handling of connection errors."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with patch('src.infrastructure.jira.utils.logger') as mock_logger:
            result = get_issue_types(mock_session, "https://test.atlassian.net", "TEST")
            
            assert result == []
            mock_logger.error.assert_called_once_with("Error obteniendo tipos de issue: %s", "Connection failed")

    def test_get_issue_types_json_decode_error(self):
        """Test handling of JSON decode errors."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_session.get.return_value = mock_response
        
        with patch('src.infrastructure.jira.utils.logger') as mock_logger:
            result = get_issue_types(mock_session, "https://test.atlassian.net", "TEST")
            
            assert result == []
            mock_logger.error.assert_called_once()

    def test_get_issue_types_different_project_keys(self):
        """Test with different project keys."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [{"id": "1", "name": "Story"}]
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        # Test various project keys
        project_keys = ["TEST", "PROJ", "MY-PROJECT", "A", "VERY-LONG-PROJECT-KEY"]
        
        for project_key in project_keys:
            result = get_issue_types(mock_session, "https://test.atlassian.net", project_key)
            
            assert len(result) == 1
            expected_url = f"https://test.atlassian.net/rest/api/3/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes"
            mock_session.get.assert_called_with(expected_url)

    def test_get_issue_types_complex_response(self):
        """Test with complex issue types response."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {
                        "id": "10001",
                        "name": "Story",
                        "description": "A user story",
                        "iconUrl": "https://icon.url",
                        "subtask": False,
                        "fields": {"summary": {"required": True}}
                    },
                    {
                        "id": "10002", 
                        "name": "Sub-task",
                        "description": "A subtask",
                        "subtask": True,
                        "fields": {"summary": {"required": True}, "parent": {"required": True}}
                    }
                ]
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        result = get_issue_types(mock_session, "https://test.atlassian.net", "TEST")
        
        assert len(result) == 2
        assert result[0]["subtask"] is False
        assert result[1]["subtask"] is True
        assert "fields" in result[0]
        assert "fields" in result[1]


class TestHandleHttpError:
    """Test handle_http_error function."""

    def test_handle_http_error_with_json_response(self):
        """Test handling HTTP error with JSON response."""
        # Create mock exception with response
        mock_response = Mock()
        mock_response.json.return_value = {
            "errorMessages": ["Field 'summary' is required"],
            "errors": {"summary": "Summary is required"}
        }
        
        mock_exception = Mock()
        mock_exception.response = mock_response
        
        mock_logger = Mock()
        
        handle_http_error(mock_exception, mock_logger)
        
        # Verify JSON details were logged
        mock_logger.error.assert_called_once()
        args = mock_logger.error.call_args[0]
        assert "Detalles del error" in args[0]
        assert '"errorMessages"' in args[1]  # JSON content should be in the logged string

    def test_handle_http_error_with_text_response(self):
        """Test handling HTTP error with text response."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("No JSON")  # JSON parsing fails
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Invalid field"
        
        mock_exception = Mock()
        mock_exception.response = mock_response
        
        mock_logger = Mock()
        
        handle_http_error(mock_exception, mock_logger)
        
        # Verify text response was logged
        mock_logger.error.assert_called_once_with(
            "Error HTTP %s: %s", 
            400, 
            "Bad Request: Invalid field"
        )

    def test_handle_http_error_no_response(self):
        """Test handling error without response attribute."""
        mock_exception = Mock(spec=[])  # No response attribute
        mock_exception.response = None
        
        mock_logger = Mock()
        
        handle_http_error(mock_exception, mock_logger)
        
        # Verify connection error was logged
        mock_logger.error.assert_called_once_with(
            "Error de conexión: %s", 
            str(mock_exception)
        )

    def test_handle_http_error_no_response_attribute(self):
        """Test handling error without response attribute at all."""
        mock_exception = Exception("Connection timeout")
        
        mock_logger = Mock()
        
        handle_http_error(mock_exception, mock_logger)
        
        # Verify connection error was logged
        mock_logger.error.assert_called_once_with(
            "Error de conexión: %s", 
            "Connection timeout"
        )

    def test_handle_http_error_json_parse_exception(self):
        """Test when JSON parsing itself raises an exception."""
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_exception = Mock()
        mock_exception.response = mock_response
        
        mock_logger = Mock()
        
        handle_http_error(mock_exception, mock_logger)
        
        # Should fall back to text logging
        mock_logger.error.assert_called_once_with(
            "Error HTTP %s: %s", 
            500, 
            "Internal Server Error"
        )

    def test_handle_http_error_complex_json(self):
        """Test with complex JSON error response."""
        complex_json = {
            "errorMessages": [
                "The issue type selected is invalid.",
                "Field 'project' is required."
            ],
            "errors": {
                "project": "Project is required",
                "issuetype": "Issue type is invalid",
                "customfield_10001": "Custom field error"
            },
            "warningMessages": ["This is a warning"],
            "httpStatusCode": 400
        }
        
        mock_response = Mock()
        mock_response.json.return_value = complex_json
        
        mock_exception = Mock()
        mock_exception.response = mock_response
        
        mock_logger = Mock()
        
        handle_http_error(mock_exception, mock_logger)
        
        # Verify complex JSON was logged
        mock_logger.error.assert_called_once()
        args = mock_logger.error.call_args[0]
        logged_json = args[1]
        
        # Verify all complex fields are present
        assert '"errorMessages"' in logged_json
        assert '"errors"' in logged_json
        assert '"warningMessages"' in logged_json
        assert '"httpStatusCode"' in logged_json


class TestValidateIssueExists:
    """Test validate_issue_exists function."""

    def test_validate_issue_exists_success(self):
        """Test successful issue validation."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        result = validate_issue_exists(mock_session, "https://test.atlassian.net", "TEST-123")
        
        assert result is True
        mock_session.get.assert_called_once_with("https://test.atlassian.net/rest/api/3/issue/TEST-123")

    def test_validate_issue_exists_not_found(self):
        """Test issue not found (404)."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        
        mock_session.get.side_effect = http_error
        
        with patch('src.infrastructure.jira.utils.logger') as mock_logger:
            result = validate_issue_exists(mock_session, "https://test.atlassian.net", "TEST-999")
            
            assert result is False
            mock_logger.error.assert_called_once_with("Issue %s no encontrado", "TEST-999")

    def test_validate_issue_exists_empty_key(self):
        """Test with empty issue key."""
        mock_session = Mock()
        
        result = validate_issue_exists(mock_session, "https://test.atlassian.net", "")
        
        assert result is True  # Empty key is considered valid
        mock_session.get.assert_not_called()

    def test_validate_issue_exists_none_key(self):
        """Test with None issue key."""
        mock_session = Mock()
        
        result = validate_issue_exists(mock_session, "https://test.atlassian.net", None)
        
        assert result is True  # None key is considered valid
        mock_session.get.assert_not_called()

    def test_validate_issue_exists_http_error_not_404(self):
        """Test HTTP error other than 404."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 403
        
        http_error = requests.exceptions.HTTPError("Forbidden")
        http_error.response = mock_response
        
        mock_session.get.side_effect = http_error
        
        with pytest.raises(requests.exceptions.HTTPError):
            validate_issue_exists(mock_session, "https://test.atlassian.net", "TEST-123")

    def test_validate_issue_exists_connection_error(self):
        """Test connection error."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(requests.exceptions.ConnectionError):
            validate_issue_exists(mock_session, "https://test.atlassian.net", "TEST-123")

    def test_validate_issue_exists_different_issue_keys(self):
        """Test with different issue key formats."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        issue_keys = [
            "TEST-1",
            "PROJECT-999", 
            "ABC-12345",
            "MY-PROJ-1",
            "A-1"
        ]
        
        for issue_key in issue_keys:
            result = validate_issue_exists(mock_session, "https://test.atlassian.net", issue_key)
            
            assert result is True
            expected_url = f"https://test.atlassian.net/rest/api/3/issue/{issue_key}"
            mock_session.get.assert_called_with(expected_url)

    def test_validate_issue_exists_different_base_urls(self):
        """Test with different base URLs."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        base_urls = [
            "https://test.atlassian.net",
            "https://company.atlassian.net", 
            "http://localhost:8080",
            "https://jira.example.com"
        ]
        
        for base_url in base_urls:
            result = validate_issue_exists(mock_session, base_url, "TEST-123")
            
            assert result is True
            expected_url = f"{base_url}/rest/api/3/issue/TEST-123"
            mock_session.get.assert_called_with(expected_url)


class TestUtilsIntegration:
    """Integration tests for utils functions."""

    def test_utils_with_real_session_structure(self):
        """Test utils functions with realistic session mock."""
        # Create a more realistic session mock
        session = Mock(spec=requests.Session)
        
        # Test get_issue_types
        mock_response = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "key": "TEST",
                "issuetypes": [
                    {"id": "1", "name": "Story"},
                    {"id": "2", "name": "Task"}
                ]
            }]
        }
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response
        
        issue_types = get_issue_types(session, "https://test.atlassian.net", "TEST")
        assert len(issue_types) == 2
        
        # Test validate_issue_exists
        session.reset_mock()
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response
        
        exists = validate_issue_exists(session, "https://test.atlassian.net", "TEST-1")
        assert exists is True

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across functions."""
        mock_logger = Mock()
        
        # Test different types of exceptions
        exceptions = [
            requests.exceptions.HTTPError("HTTP Error"),
            requests.exceptions.ConnectionError("Connection Error"),
            requests.exceptions.Timeout("Timeout Error"),
            Exception("Generic Error")
        ]
        
        for exc in exceptions:
            handle_http_error(exc, mock_logger)
        
        # Should have logged all errors
        assert mock_logger.error.call_count == len(exceptions)