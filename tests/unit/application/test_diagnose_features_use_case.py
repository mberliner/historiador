"""Tests for DiagnoseFeaturesUseCase."""
import pytest
import json
from unittest.mock import Mock, patch

from src.application.use_cases.diagnose_features import DiagnoseFeaturesUseCase


class TestDiagnoseFeaturesUseCaseInit:
    """Test DiagnoseFeaturesUseCase initialization."""

    def test_init(self):
        """Test proper initialization."""
        use_case = DiagnoseFeaturesUseCase()
        
        # No instance variables to test, just ensure it initializes


class TestExecuteMethod:
    """Test execute method with various scenarios."""

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_successful_diagnosis(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test successful feature diagnosis."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings_instance.default_issue_type = "Story"  # Nuevo campo requerido
        mock_settings_instance.feature_issue_type = "Feature"
        mock_settings_instance.feature_required_fields = {"summary": "Summary"}
        mock_settings_instance.story_required_fields = None  # Nuevo campo requerido
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings.return_value = mock_settings_instance
        
        mock_feature_manager = Mock()
        mock_feature_manager.get_required_fields_for_feature.return_value = {
            "summary": "Summary",
            "description": "Description",
            "customfield_10001": "Story Points"
        }
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_issue_type.return_value = True  # Nuevo método requerido
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.feature_manager = mock_feature_manager
        mock_jc_instance.session = Mock()  # Requerido para JiraMetadataDetector
        mock_jira_client.return_value = mock_jc_instance
        
        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {
            "customfield_10002": "Priority Field"
        }
        mock_metadata_detector.return_value = mock_detector_instance
        
        use_case = DiagnoseFeaturesUseCase()
        result = use_case.execute()
        
        # Verify result structure
        assert result['project_key'] == "TEST"
        assert result['feature_type'] == "Feature"
        assert result['story_type'] == "Story"  # Nuevo campo agregado
        assert result['feature_required_fields'] == {
            "summary": "Summary",
            "description": "Description",  
            "customfield_10001": "Story Points"
        }
        assert 'story_required_fields' in result  # Nuevo campo
        
        # Verify config suggestion is valid JSON
        assert result['feature_config_suggestion'] is not None
        parsed_feature_config = json.loads(result['feature_config_suggestion'])
        assert parsed_feature_config == result['feature_required_fields']
        
        # Verify current config
        assert result['current_config']['feature_type'] == "Feature"
        assert result['current_config']['feature_required_fields'] == {"summary": "Summary"}
        assert result['current_config']['story_type'] == "Story"
        
        # Verify mock calls
        mock_settings.assert_called_once()
        mock_jira_client.assert_called_once_with(mock_settings_instance)
        mock_jc_instance.test_connection.assert_called_once()
        mock_jc_instance.validate_project.assert_called_once_with("TEST")
        mock_jc_instance.validate_feature_issue_type.assert_called_once()
        mock_feature_manager.get_required_fields_for_feature.assert_called_once()

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_with_project_key_override(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test diagnosis with project key override."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "ORIGINAL"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.feature_issue_type = "Feature"
        mock_settings_instance.feature_required_fields = None
        mock_settings_instance.story_required_fields = None
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings.return_value = mock_settings_instance
        
        mock_feature_manager = Mock()
        mock_feature_manager.get_required_fields_for_feature.return_value = {}
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.feature_manager = mock_feature_manager
        mock_jc_instance.session = Mock()
        mock_jira_client.return_value = mock_jc_instance
        
        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance
        
        use_case = DiagnoseFeaturesUseCase()
        result = use_case.execute("OVERRIDE")
        
        # Verify project key was overridden
        assert mock_settings_instance.project_key == "OVERRIDE"
        assert result['project_key'] == "OVERRIDE"
        
        # Verify validation was called with overridden key
        mock_jc_instance.validate_project.assert_called_once_with("OVERRIDE")
        
        # Verify story and feature required fields are present
        assert 'story_required_fields' in result
        assert 'feature_required_fields' in result

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_with_no_required_fields(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test diagnosis when no required fields are found."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.feature_issue_type = "Feature"
        mock_settings_instance.feature_required_fields = None
        mock_settings_instance.story_required_fields = None
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings.return_value = mock_settings_instance
        
        mock_feature_manager = Mock()
        mock_feature_manager.get_required_fields_for_feature.return_value = {}
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.feature_manager = mock_feature_manager
        mock_jc_instance.session = Mock()
        mock_jira_client.return_value = mock_jc_instance
        
        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance
        
        use_case = DiagnoseFeaturesUseCase()
        result = use_case.execute()
        
        # Verify result when no required fields (empty dicts instead of None)
        assert result['feature_required_fields'] == {}
        assert result['story_required_fields'] == {}
        assert result['feature_config_suggestion'] is None  # Empty dict is falsy, so None
        assert result['story_config_suggestion'] is None

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_with_empty_required_fields(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test diagnosis when required fields is empty dict."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings_instance.feature_issue_type = "Feature"
        mock_settings_instance.feature_required_fields = {}
        mock_settings_instance.story_required_fields = None
        mock_settings.return_value = mock_settings_instance
        
        mock_feature_manager = Mock()
        mock_feature_manager.get_required_fields_for_feature.return_value = {}
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.feature_manager = mock_feature_manager
        mock_jc_instance.session = Mock()
        mock_jira_client.return_value = mock_jc_instance

        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance

        
        use_case = DiagnoseFeaturesUseCase()
        result = use_case.execute()
        
        # Verify result when empty required fields
        assert result['feature_required_fields'] == {}
        assert result['feature_config_suggestion'] is None  # Empty dict is falsy, so None

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_result_structure(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test that result has correct structure."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings_instance.feature_issue_type = "Story"
        mock_settings_instance.feature_required_fields = {"field1": "value1"}
        mock_settings_instance.story_required_fields = None
        mock_settings.return_value = mock_settings_instance
        
        mock_feature_manager = Mock()
        mock_feature_manager.get_required_fields_for_feature.return_value = {"field2": "value2"}
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.feature_manager = mock_feature_manager
        mock_jc_instance.session = Mock()
        mock_jira_client.return_value = mock_jc_instance

        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance

        
        use_case = DiagnoseFeaturesUseCase()
        result = use_case.execute()
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'project_key' in result
        assert 'feature_type' in result
        assert 'feature_required_fields' in result
        assert 'feature_config_suggestion' in result
        assert 'story_required_fields' in result
        assert 'story_config_suggestion' in result
        assert 'current_config' in result
        assert len(result) >= 7  # Should have at least story/feature fields
        
        # Verify current_config structure
        assert isinstance(result['current_config'], dict)
        assert 'feature_type' in result['current_config']
        assert 'feature_required_fields' in result['current_config']
        assert 'story_type' in result['current_config']
        assert 'story_required_fields' in result['current_config']
        assert len(result['current_config']) == 4


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_connection_failure(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test handling of connection failure."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = False
        mock_jira_client.return_value = mock_jc_instance

        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance

        
        use_case = DiagnoseFeaturesUseCase()
        
        with pytest.raises(Exception, match="Error de conexión con Jira"):
            use_case.execute()

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_project_not_found(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test handling of project not found."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "INVALID"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = False
        mock_jira_client.return_value = mock_jc_instance

        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance

        
        use_case = DiagnoseFeaturesUseCase()
        
        with pytest.raises(Exception, match="Proyecto 'INVALID' no encontrado"):
            use_case.execute()

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_invalid_feature_type(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test handling of invalid feature type."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings_instance.feature_issue_type = "InvalidType"
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = False
        mock_jira_client.return_value = mock_jc_instance

        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance

        
        use_case = DiagnoseFeaturesUseCase()
        
        with pytest.raises(Exception, match="Tipo de feature 'InvalidType' no válido"):
            use_case.execute()

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_settings_creation_error(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test handling of settings creation error."""
        mock_settings.side_effect = Exception("Settings error")
        
        use_case = DiagnoseFeaturesUseCase()
        
        with pytest.raises(Exception, match="Settings error"):
            use_case.execute()

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_jira_client_creation_error(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test handling of JiraClient creation error."""
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings.return_value = mock_settings_instance
        
        mock_jira_client.side_effect = Exception("JiraClient error")
        
        use_case = DiagnoseFeaturesUseCase()
        
        with pytest.raises(Exception, match="JiraClient error"):
            use_case.execute()

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_feature_manager_error(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test handling of feature manager error."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings_instance.feature_issue_type = "Feature"
        mock_settings.return_value = mock_settings_instance
        
        mock_feature_manager = Mock()
        mock_feature_manager.get_required_fields_for_feature.side_effect = Exception("Feature manager error")
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.feature_manager = mock_feature_manager
        mock_jc_instance.session = Mock()
        mock_jira_client.return_value = mock_jc_instance

        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance

        
        use_case = DiagnoseFeaturesUseCase()
        
        with pytest.raises(Exception, match="Feature manager error"):
            use_case.execute()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_with_complex_required_fields(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test diagnosis with complex required fields structure."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = "TEST"
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings_instance.feature_issue_type = "Epic"
        mock_settings_instance.feature_required_fields = {"old": "old_value"}
        mock_settings_instance.story_required_fields = None
        mock_settings.return_value = mock_settings_instance
        
        # Complex required fields with nested structures
        complex_fields = {
            "summary": "Summary",
            "customfield_10001": {
                "value": "High",
                "child": {"value": "Critical"}
            },
            "customfield_10002": ["option1", "option2"],
            "assignee": {"accountId": "123456"}
        }
        
        mock_feature_manager = Mock()
        mock_feature_manager.get_required_fields_for_feature.return_value = complex_fields
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.feature_manager = mock_feature_manager
        mock_jc_instance.session = Mock()
        mock_jira_client.return_value = mock_jc_instance

        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance

        
        use_case = DiagnoseFeaturesUseCase()
        result = use_case.execute()
        
        # Verify complex fields are preserved
        assert result['feature_required_fields'] == complex_fields
        
        # Verify JSON serialization works with complex structure
        parsed_config = json.loads(result['feature_config_suggestion'])
        assert parsed_config == complex_fields

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_multiple_calls_independence(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test that multiple calls are independent."""
        # First call setup
        mock_settings_instance1 = Mock()
        mock_settings_instance1.project_key = "PROJ1"
        mock_settings_instance1.default_issue_type = "Story"
        mock_settings_instance1.jira_url = "https://test.atlassian.net"
        mock_settings_instance1.jira_email = "test@test.com"
        mock_settings_instance1.jira_api_token = "token"
        mock_settings_instance1.feature_issue_type = "Feature"
        mock_settings_instance1.feature_required_fields = {"field1": "value1"}
        mock_settings_instance1.story_required_fields = None
        
        mock_feature_manager1 = Mock()
        mock_feature_manager1.get_required_fields_for_feature.return_value = {"req1": "val1"}
        
        mock_jc_instance1 = Mock()
        mock_jc_instance1.test_connection.return_value = True
        mock_jc_instance1.validate_project.return_value = True
        mock_jc_instance1.validate_issue_type.return_value = True
        mock_jc_instance1.validate_feature_issue_type.return_value = True
        mock_jc_instance1.feature_manager = mock_feature_manager1
        mock_jc_instance1.session = Mock()
        
        # Second call setup
        mock_settings_instance2 = Mock()
        mock_settings_instance2.project_key = "PROJ2"
        mock_settings_instance2.default_issue_type = "Story"
        mock_settings_instance2.jira_url = "https://test.atlassian.net"
        mock_settings_instance2.jira_email = "test@test.com"
        mock_settings_instance2.jira_api_token = "token"
        mock_settings_instance2.feature_issue_type = "Epic"
        mock_settings_instance2.feature_required_fields = {"field2": "value2"}
        mock_settings_instance2.story_required_fields = None
        
        mock_feature_manager2 = Mock()
        mock_feature_manager2.get_required_fields_for_feature.return_value = {"req2": "val2"}
        
        mock_jc_instance2 = Mock()
        mock_jc_instance2.test_connection.return_value = True
        mock_jc_instance2.validate_project.return_value = True
        mock_jc_instance2.validate_issue_type.return_value = True
        mock_jc_instance2.validate_feature_issue_type.return_value = True
        mock_jc_instance2.feature_manager = mock_feature_manager2
        mock_jc_instance2.session = Mock()
        
        # Setup side effects
        mock_settings.side_effect = [mock_settings_instance1, mock_settings_instance2]
        mock_jira_client.side_effect = [mock_jc_instance1, mock_jc_instance2]
        
        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance
        
        use_case = DiagnoseFeaturesUseCase()
        
        # First call
        result1 = use_case.execute()
        assert result1['project_key'] == "PROJ1"
        assert result1['feature_type'] == "Feature"
        assert result1['feature_required_fields'] == {"req1": "val1"}
        assert result1['current_config']['feature_required_fields'] == {"field1": "value1"}
        
        # Second call
        result2 = use_case.execute()
        assert result2['project_key'] == "PROJ2"
        assert result2['feature_type'] == "Epic"
        assert result2['feature_required_fields'] == {"req2": "val2"}
        assert result2['current_config']['feature_required_fields'] == {"field2": "value2"}

    @patch('src.application.use_cases.diagnose_features.JiraMetadataDetector')
    @patch('src.application.use_cases.diagnose_features.JiraClient')
    @patch('src.application.use_cases.diagnose_features.Settings')
    def test_execute_with_none_project_key(self, mock_settings, mock_jira_client, mock_metadata_detector):
        """Test diagnosis with None project key."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.project_key = None
        mock_settings_instance.default_issue_type = "Story"
        mock_settings_instance.jira_url = "https://test.atlassian.net"
        mock_settings_instance.jira_email = "test@test.com"
        mock_settings_instance.jira_api_token = "token"
        mock_settings_instance.feature_issue_type = "Feature"
        mock_settings_instance.feature_required_fields = None
        mock_settings_instance.story_required_fields = None
        mock_settings.return_value = mock_settings_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = False  # None project should be invalid
        mock_jira_client.return_value = mock_jc_instance

        # Mock JiraMetadataDetector
        mock_detector_instance = Mock()
        mock_detector_instance.detect_story_required_fields.return_value = {}
        mock_metadata_detector.return_value = mock_detector_instance

        
        use_case = DiagnoseFeaturesUseCase()
        
        with pytest.raises(Exception, match="Proyecto 'None' no encontrado"):
            use_case.execute()
            
        # Verify validation was called with None
        mock_jc_instance.validate_project.assert_called_once_with(None)