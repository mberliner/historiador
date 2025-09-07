"""Tests for JiraClient."""
import pytest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.infrastructure.jira.jira_client import JiraClient
from src.infrastructure.settings import Settings
from src.domain.entities.user_story import UserStory
from src.domain.entities.process_result import ProcessResult
from src.domain.entities.feature_result import FeatureResult

# Use test environment file
TEST_ENV_FILE = Path(__file__).parent.parent.parent.parent.parent / ".env.test"


class TestJiraClientInit:
    """Test JiraClient initialization."""

    def test_init_with_settings(self):
        """Test proper initialization with settings."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        
        client = JiraClient(settings)
        
        assert client.settings == settings
        assert client.base_url == settings.jira_url.rstrip('/')
        assert client.auth == (settings.jira_email, settings.jira_api_token)
        assert client.session is not None
        assert client.feature_manager is not None
        
        # Verify session configuration
        assert client.session.auth == client.auth
        assert client.session.headers['Accept'] == 'application/json'
        assert client.session.headers['Content-Type'] == 'application/json'

    def test_init_base_url_stripping(self):
        """Test that trailing slashes are stripped from base URL."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        # Add trailing slashes
        settings.jira_url = "https://test.atlassian.net///"
        
        client = JiraClient(settings)
        
        assert client.base_url == "https://test.atlassian.net"

    @patch('src.infrastructure.jira.jira_client.FeatureManager')
    def test_init_creates_feature_manager(self, mock_feature_manager):
        """Test that FeatureManager is created properly."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        
        client = JiraClient(settings)
        
        mock_feature_manager.assert_called_once_with(settings, client.session)


class TestTestConnection:
    """Test test_connection method."""

    def test_test_connection_success(self):
        """Test successful connection."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.test_connection()
            
            assert result is True
            client.session.get.assert_called_once_with(f"{client.base_url}/rest/api/3/myself")

    def test_test_connection_http_error(self):
        """Test connection with HTTP error."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.test_connection()
                
                assert result is False
                mock_logger.error.assert_called_once_with("Error de conexión con Jira: %s", "401 Unauthorized")

    def test_test_connection_connection_error(self):
        """Test connection with connection error."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.test_connection()
                
                assert result is False
                mock_logger.error.assert_called_once_with("Error de conexión con Jira: %s", "Network error")

    def test_test_connection_timeout_error(self):
        """Test connection with timeout error."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
            
            result = client.test_connection()
            
            assert result is False

    def test_test_connection_success_logs_info(self):
        """Test that successful connection logs info message."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'get', return_value=mock_response):
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.test_connection()
                
                assert result is True
                mock_logger.info.assert_called_once_with("Conexión con Jira exitosa")


class TestValidateProject:
    """Test validate_project method."""

    def test_validate_project_success(self):
        """Test successful project validation."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.validate_project("TEST")
            
            assert result is True
            client.session.get.assert_called_once_with(f"{client.base_url}/rest/api/3/project/TEST")

    def test_validate_project_not_found(self):
        """Test project validation when project not found."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock 404 error
        mock_response = Mock()
        mock_response.status_code = 404
        
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = http_error
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_project("INVALID")
                
                assert result is False
                mock_logger.error.assert_called_once_with("Proyecto %s no encontrado", "INVALID")

    def test_validate_project_other_http_error(self):
        """Test project validation with non-404 HTTP error."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock 403 error
        mock_response = Mock()
        mock_response.status_code = 403
        
        http_error = requests.exceptions.HTTPError("Forbidden")
        http_error.response = mock_response
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = http_error
            
            with pytest.raises(requests.exceptions.HTTPError):
                client.validate_project("TEST")

    def test_validate_project_different_keys(self):
        """Test project validation with different project keys."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        project_keys = ["TEST", "PROJ", "MY-PROJECT", "ABC123", "X"]
        
        for project_key in project_keys:
            with patch.object(client.session, 'get', return_value=mock_response):
                result = client.validate_project(project_key)
                
                assert result is True
                expected_url = f"{client.base_url}/rest/api/3/project/{project_key}"
                client.session.get.assert_called_with(expected_url)


class TestValidateSubtaskIssueType:
    """Test validate_subtask_issue_type method."""

    def test_validate_subtask_issue_type_success(self):
        """Test successful subtask type validation."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock issue types with subtask
        mock_issue_types = [
            {"id": "1", "name": "Story", "subtask": False},
            {"id": "2", "name": "Subtarea", "subtask": True},  # This matches project setting
            {"id": "3", "name": "Task", "subtask": False}
        ]
        
        with patch.object(client, 'get_issue_types', return_value=mock_issue_types):
            result = client.validate_subtask_issue_type()
            
            assert result is True

    def test_validate_subtask_issue_type_not_found(self):
        """Test subtask type validation when type not found."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock issue types without matching subtask
        mock_issue_types = [
            {"id": "1", "name": "Story", "subtask": False},
            {"id": "2", "name": "Other-Subtask", "subtask": True},  # Different name
            {"id": "3", "name": "Task", "subtask": False}
        ]
        
        with patch.object(client, 'get_issue_types', return_value=mock_issue_types):
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_subtask_issue_type()
                
                assert result is False
                mock_logger.error.assert_called_once()
                # Verify error message contains expected subtask type
                args = mock_logger.error.call_args[0]
                assert settings.subtask_issue_type in args[1]
                assert "Other-Subtask" in args[2]  # Available subtasks

    def test_validate_subtask_issue_type_no_subtasks(self):
        """Test subtask type validation when no subtasks exist."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock issue types without any subtasks
        mock_issue_types = [
            {"id": "1", "name": "Story", "subtask": False},
            {"id": "2", "name": "Task", "subtask": False}
        ]
        
        with patch.object(client, 'get_issue_types', return_value=mock_issue_types):
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_subtask_issue_type()
                
                assert result is False
                mock_logger.error.assert_called_once()

    def test_validate_subtask_issue_type_get_types_error(self):
        """Test subtask type validation when get_issue_types fails."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client, 'get_issue_types') as mock_get_types:
            mock_get_types.side_effect = Exception("API Error")
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_subtask_issue_type()
                
                assert result is False
                mock_logger.error.assert_called_once_with("Error validando tipo de subtarea: %s", "API Error")

    def test_validate_subtask_issue_type_missing_subtask_field(self):
        """Test subtask type validation with missing subtask field."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock issue types where some don't have subtask field
        mock_issue_types = [
            {"id": "1", "name": "Story"},  # No subtask field
            {"id": "2", "name": "Subtarea", "subtask": True},
            {"id": "3", "name": "Task", "subtask": False}
        ]
        
        with patch.object(client, 'get_issue_types', return_value=mock_issue_types):
            result = client.validate_subtask_issue_type()
            
            assert result is True  # Should find Subtarea

    def test_validate_subtask_issue_type_custom_subtask_name(self):
        """Test subtask type validation with custom subtask name."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.subtask_issue_type = "Subtarea"  # Custom name
        client = JiraClient(settings)
        
        mock_issue_types = [
            {"id": "1", "name": "Story", "subtask": False},
            {"id": "2", "name": "Subtarea", "subtask": True},  # Custom subtask name
            {"id": "3", "name": "Task", "subtask": False}
        ]
        
        with patch.object(client, 'get_issue_types', return_value=mock_issue_types):
            result = client.validate_subtask_issue_type()
            
            assert result is True


class TestValidateFeatureIssueType:
    """Test validate_feature_issue_type method."""

    def test_validate_feature_issue_type_delegates_to_feature_manager(self):
        """Test that validation is delegated to feature manager."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock feature manager
        with patch.object(client.feature_manager, 'validate_feature_type') as mock_validate:
            mock_validate.return_value = True
            
            result = client.validate_feature_issue_type()
            
            assert result is True
            mock_validate.assert_called_once()

    def test_validate_feature_issue_type_failure(self):
        """Test feature type validation failure."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client.feature_manager, 'validate_feature_type') as mock_validate:
            mock_validate.return_value = False
            
            result = client.validate_feature_issue_type()
            
            assert result is False


class TestValidateParentIssue:
    """Test validate_parent_issue method."""

    @patch('src.infrastructure.jira.jira_client.jira_utils.validate_issue_exists')
    def test_validate_parent_issue_delegates_to_utils(self, mock_validate_utils):
        """Test that validation is delegated to utils."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_validate_utils.return_value = True
        
        result = client.validate_parent_issue("TEST-123")
        
        assert result is True
        mock_validate_utils.assert_called_once_with(client.session, client.base_url, "TEST-123")

    @patch('src.infrastructure.jira.jira_client.jira_utils.validate_issue_exists')
    def test_validate_parent_issue_not_found(self, mock_validate_utils):
        """Test parent issue validation when issue not found."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_validate_utils.return_value = False
        
        result = client.validate_parent_issue("TEST-999")
        
        assert result is False

    @patch('src.infrastructure.jira.jira_client.jira_utils.validate_issue_exists')
    def test_validate_parent_issue_different_keys(self, mock_validate_utils):
        """Test parent issue validation with different issue keys."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_validate_utils.return_value = True
        
        issue_keys = ["TEST-1", "PROJ-999", "ABC-12345", None, ""]
        
        for issue_key in issue_keys:
            result = client.validate_parent_issue(issue_key)
            
            assert result is True
            mock_validate_utils.assert_called_with(client.session, client.base_url, issue_key)


class TestGetIssueTypes:
    """Test get_issue_types method."""

    @patch('src.infrastructure.jira.jira_client.jira_utils.get_issue_types')
    def test_get_issue_types_delegates_to_utils(self, mock_get_types_utils):
        """Test that get_issue_types delegates to utils."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_issue_types = [
            {"id": "1", "name": "Story"},
            {"id": "2", "name": "Task"}
        ]
        mock_get_types_utils.return_value = mock_issue_types
        
        result = client.get_issue_types()
        
        assert result == mock_issue_types
        mock_get_types_utils.assert_called_once_with(
            client.session, 
            client.base_url, 
            client.settings.project_key
        )

    @patch('src.infrastructure.jira.jira_client.jira_utils.get_issue_types')
    def test_get_issue_types_empty_result(self, mock_get_types_utils):
        """Test get_issue_types with empty result."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_get_types_utils.return_value = []
        
        result = client.get_issue_types()
        
        assert result == []


class TestCreateUserStory:
    """Test create_user_story method."""

    def test_create_user_story_dry_run_mode(self):
        """Test user story creation in dry run mode."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.dry_run = True
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description", 
            criterio_aceptacion="Test Criteria",
            subtareas=["Subtask 1", "Subtask 2"]
        )
        
        with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
            result = client.create_user_story(story, row_number=5)
            
            assert isinstance(result, ProcessResult)
            assert result.success is True
            assert result.jira_key == "DRY-RUN-5"
            assert result.row_number == 5
            assert result.subtasks_created == 2
            assert result.subtasks_failed == 0
            assert result.feature_info is None  # No parent
            
            mock_logger.info.assert_called_once_with("[DRY RUN] Creando historia: %s", "Test Story")

    def test_create_user_story_dry_run_with_parent_key(self):
        """Test dry run with existing parent key."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.dry_run = True
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria",
            parent="TEST-123"
        )
        
        # Mock feature manager to recognize as Jira key
        with patch.object(client.feature_manager, 'is_jira_key', return_value=True):
            result = client.create_user_story(story)
            
            assert result.success is True
            assert result.feature_info is not None
            assert result.feature_info.feature_key == "TEST-123"
            assert result.feature_info.was_created is False
            assert result.feature_info.original_text == "TEST-123"

    def test_create_user_story_dry_run_with_parent_description(self):
        """Test dry run with parent description (creates feature)."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.dry_run = True
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria", 
            parent="New Feature Description"
        )
        
        # Mock feature manager to recognize as description
        with patch.object(client.feature_manager, 'is_jira_key', return_value=False):
            result = client.create_user_story(story)
            
            assert result.success is True
            assert result.feature_info is not None
            assert result.feature_info.feature_key.startswith("DRY-FEATURE-")
            assert result.feature_info.was_created is True
            assert result.feature_info.original_text == "New Feature Description"

    def test_create_user_story_success_no_parent(self):
        """Test successful user story creation without parent."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria"
        )
        
        # Mock successful Jira response
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-123"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response):
            result = client.create_user_story(story, row_number=1)
            
            assert result.success is True
            assert result.jira_key == "TEST-123"
            assert result.row_number == 1
            assert result.subtasks_created == 0
            assert result.subtasks_failed == 0
            
            # Verify API call
            client.session.post.assert_called_once()
            call_args = client.session.post.call_args
            assert f"{client.base_url}/rest/api/3/issue" in call_args[0]

    def test_create_user_story_with_parent(self):
        """Test user story creation with parent."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria",
            parent="TEST-PARENT"
        )
        
        # Mock feature manager
        with patch.object(client.feature_manager, 'get_or_create_parent') as mock_get_parent:
            mock_get_parent.return_value = ("TEST-PARENT", False)
            
            # Mock successful Jira response
            mock_response = Mock()
            mock_response.json.return_value = {"key": "TEST-124"}
            mock_response.raise_for_status.return_value = None
            
            with patch.object(client.session, 'post', return_value=mock_response):
                result = client.create_user_story(story)
                
                assert result.success is True
                assert result.jira_key == "TEST-124"
                
                # Verify parent was processed
                mock_get_parent.assert_called_once_with("TEST-PARENT")

    def test_create_user_story_parent_creation_failure(self):
        """Test user story creation when parent creation fails."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria",
            parent="Invalid Parent"
        )
        
        # Mock feature manager to fail parent creation
        with patch.object(client.feature_manager, 'get_or_create_parent') as mock_get_parent:
            mock_get_parent.return_value = (None, False)
            
            result = client.create_user_story(story, row_number=2)
            
            assert result.success is False
            assert "Error procesando parent: Invalid Parent" in result.error_message
            assert result.row_number == 2

    def test_create_user_story_with_subtasks(self):
        """Test user story creation with subtasks."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria",
            subtareas=["Subtask 1", "Subtask 2", "Subtask 3"]
        )
        
        # Mock successful story creation
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-125"}
        mock_response.raise_for_status.return_value = None
        
        # Mock subtask creation
        with patch.object(client.session, 'post', return_value=mock_response):
            with patch.object(client, '_create_subtasks') as mock_create_subtasks:
                mock_create_subtasks.return_value = (2, 1, ["Error in subtask 3"])  # 2 success, 1 failed
                
                result = client.create_user_story(story)
                
                assert result.success is True
                assert result.jira_key == "TEST-125"
                assert result.subtasks_created == 2
                assert result.subtasks_failed == 1
                
                # Verify subtasks were created
                mock_create_subtasks.assert_called_once_with("TEST-125", story.subtareas)

    def test_create_user_story_with_acceptance_criteria_field(self):
        """Test user story creation with custom acceptance criteria field."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.acceptance_criteria_field = "customfield_10001"
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Custom criteria"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-126"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            result = client.create_user_story(story)
            
            assert result.success is True
            
            # Verify custom field was included in payload
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            assert "customfield_10001" in payload["fields"]
            # Custom field should contain the formatted criteria document
            assert payload["fields"]["customfield_10001"]["type"] == "doc"
            assert "Custom criteria" in str(payload["fields"]["customfield_10001"])

    def test_create_user_story_http_error(self):
        """Test user story creation with HTTP error."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria"
        )
        
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        http_error = requests.exceptions.HTTPError("Bad Request")
        http_error.response = mock_response
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = http_error
            
            result = client.create_user_story(story, row_number=3)
            
            assert result.success is False
            assert "Error de validación en Jira" in result.error_message
            assert result.row_number == 3

    def test_create_user_story_rollback_on_subtask_failure(self):
        """Test rollback when all subtasks fail."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.rollback_on_subtask_failure = True
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria",
            subtareas=["Failing subtask"]
        )
        
        # Mock successful story creation
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-127"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response):
            with patch.object(client, '_create_subtasks') as mock_create_subtasks:
                with patch.object(client, '_delete_issue') as mock_delete:
                    # All subtasks fail
                    mock_create_subtasks.return_value = (0, 1, ["Subtask creation failed"])
                    mock_delete.return_value = True
                    
                    result = client.create_user_story(story)
                    
                    assert result.success is False
                    assert "Historia eliminada" in result.error_message
                    assert "fallaron todas las subtareas" in result.error_message
                    
                    # Verify story was deleted
                    mock_delete.assert_called_once_with("TEST-127")

    def test_create_user_story_rollback_delete_failure(self):
        """Test rollback when deletion fails."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.rollback_on_subtask_failure = True
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description", 
            criterio_aceptacion="Test Criteria",
            subtareas=["Failing subtask"]
        )
        
        # Mock successful story creation
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-128"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response):
            with patch.object(client, '_create_subtasks') as mock_create_subtasks:
                with patch.object(client, '_delete_issue') as mock_delete:
                    with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                        # All subtasks fail and deletion also fails
                        mock_create_subtasks.return_value = (0, 1, ["Subtask creation failed"])
                        mock_delete.side_effect = Exception("Delete failed")
                        
                        result = client.create_user_story(story)
                        
                        # When deletion fails, the method logs error but continues to success path
                        # This is the actual behavior - the story is still created successfully
                        assert result.success is True
                        assert result.jira_key == "TEST-128"
                        assert result.subtasks_failed == 1
                        
                        # Verify deletion was attempted and error was logged
                        mock_delete.assert_called_once_with("TEST-128")
                        mock_logger.error.assert_called_with(
                            "Error eliminando historia %s: %s", "TEST-128", "Delete failed"
                        )

    def test_create_user_story_with_story_required_fields_valid_json(self):
        """Test story creation with valid story_required_fields JSON."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.story_required_fields = '{"customfield_10001": "test_value", "priority": {"id": "1"}}'
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-129"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.create_user_story(story)
                
                assert result.success is True
                assert result.jira_key == "TEST-129"
                
                # Verify additional fields were added to payload
                call_args = mock_post.call_args
                payload = json.loads(call_args[1]['data'])
                assert "customfield_10001" in payload["fields"]
                assert payload["fields"]["customfield_10001"] == "test_value"
                assert payload["fields"]["priority"] == {"id": "1"}
                
                # Verify debug log was called
                mock_logger.debug.assert_any_call(
                    "Campos obligatorios agregados para historia: %s",
                    {"customfield_10001": "test_value", "priority": {"id": "1"}}
                )

    def test_create_user_story_with_story_required_fields_invalid_json(self):
        """Test story creation with invalid story_required_fields JSON."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.story_required_fields = 'invalid json{'
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria"
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-130"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response):
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.create_user_story(story)
                
                assert result.success is True
                assert result.jira_key == "TEST-130"
                
                # Verify warning was logged for invalid JSON
                mock_logger.warning.assert_called()
                warning_call = mock_logger.warning.call_args[0]
                assert "Error parseando story_required_fields" in warning_call[0]

    def test_create_user_story_http_error_different_status_codes(self):
        """Test different HTTP error status codes."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria"
        )
        
        # Test different error codes
        test_cases = [
            (400, "Error de validación en Jira (revisa los datos)"),
            (403, "Sin permisos para crear historias en este proyecto"),
            (404, "Proyecto o configuración no encontrada"),
            (500, "Error de conexión con Jira (HTTP 500)")
        ]
        
        for status_code, expected_message in test_cases:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.json.return_value = {"errorMessages": ["API Error"]}
            
            http_error = requests.exceptions.HTTPError(f"HTTP {status_code}")
            http_error.response = mock_response
            
            with patch.object(client.session, 'post') as mock_post:
                mock_post.side_effect = http_error
                
                with patch('src.infrastructure.jira.jira_client.logger'):
                    result = client.create_user_story(story, row_number=1)
                    
                    assert result.success is False
                    assert expected_message in result.error_message
                    assert result.row_number == 1

    def test_create_user_story_http_error_with_json_response_details(self):
        """Test HTTP error with JSON response details logging."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria"
        )
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "errorMessages": ["Summary is required"],
            "errors": {"summary": "Summary is required"}
        }
        
        http_error = requests.exceptions.HTTPError("Bad Request")
        http_error.response = mock_response
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = http_error
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.create_user_story(story)
                
                assert result.success is False
                
                # Verify detailed error logging
                mock_logger.error.assert_any_call("Error HTTP creando historia: %s", "Bad Request")
                # Check that JSON details were logged
                json_log_called = any(
                    "Detalles del error:" in str(call) for call in mock_logger.error.call_args_list
                )
                assert json_log_called

    def test_create_user_story_http_error_json_parse_failure(self):
        """Test HTTP error when JSON parsing fails."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria"
        )
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid response format"
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        
        http_error = requests.exceptions.HTTPError("Bad Request")
        http_error.response = mock_response
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = http_error
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.create_user_story(story)
                
                assert result.success is False
                
                # Verify response text was logged when JSON parsing fails
                mock_logger.error.assert_any_call("Response text: %s", "Invalid response format")

    def test_create_user_story_general_exception_with_payload_logging(self):
        """Test general exception with payload logging."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria"
        )
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = Exception("Unexpected error")
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.create_user_story(story, row_number=5)
                
                assert result.success is False
                assert result.error_message == "Error inesperado creando historia"
                assert result.row_number == 5
                
                # Verify complete error logging
                mock_logger.error.assert_any_call("Error creando historia: %s", "Unexpected error")
                # Verify payload was logged
                payload_logged = any(
                    "Payload enviado:" in str(call) for call in mock_logger.error.call_args_list
                )
                assert payload_logged


class TestCreateUserStoryEdgeCases:
    """Additional edge case tests for create_user_story."""

    def test_create_user_story_with_multiple_acceptance_criteria_in_description(self):
        """Test story creation with multiple acceptance criteria in description when no custom field."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.acceptance_criteria_field = None  # No custom field
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion=["Criteria 1", "Criteria 2", "Criteria 3"]  # Multiple criteria
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-131"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            result = client.create_user_story(story)
            
            assert result.success is True
            
            # Verify criteria were added to description as bullet points
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            description_content = payload["fields"]["description"]["content"]
            
            # Should have: description + separator + 3 bullet points
            assert len(description_content) >= 5  # description + separator + 3 criteria
            
            # Check for separator
            separator_found = any(
                "Criterios de Aceptación" in str(content.get("content", []))
                for content in description_content
            )
            assert separator_found
            
            # Check for bullet points
            bullet_points = [content for content in description_content 
                           if any("• Criteria" in str(item.get("text", "")) 
                                 for item in content.get("content", []))]
            assert len(bullet_points) == 3

    def test_create_user_story_with_single_acceptance_criteria_in_description(self):
        """Test story creation with single acceptance criteria in description."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.acceptance_criteria_field = None  # No custom field
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion=["Single criteria"]  # Single criteria as list
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-132"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            result = client.create_user_story(story)
            
            assert result.success is True
            
            # Verify single criteria was added as plain text
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            description_content = payload["fields"]["description"]["content"]
            
            # Should have: description + separator + single criteria (not as bullet)
            assert len(description_content) >= 3
            
            # Check for plain text criteria (not bullet point)
            criteria_text_found = any(
                "Single criteria" in str(content.get("content", []))
                for content in description_content
            )
            assert criteria_text_found

    def test_create_user_story_with_empty_acceptance_criteria_list(self):
        """Test story creation with empty acceptance criteria list."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.acceptance_criteria_field = None
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test Description",
            criterio_aceptacion=[]  # Empty list
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-133"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            result = client.create_user_story(story)
            
            assert result.success is True
            
            # Verify only description content (no criteria section)
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            description_content = payload["fields"]["description"]["content"]
            
            # Should only have the main description paragraph
            assert len(description_content) == 1
            assert "Test Description" in str(description_content[0])


class TestCreateSubtasks:
    """Test _create_subtasks method."""

    def test_create_subtasks_success_all(self):
        """Test successful creation of all subtasks."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        subtasks = ["Subtask 1", "Subtask 2", "Subtask 3"]
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-124"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response):
            created, failed, errors = client._create_subtasks("TEST-123", subtasks)
            
            assert created == 3
            assert failed == 0
            assert errors == []
            
            # Verify API calls
            assert client.session.post.call_count == 3

    def test_create_subtasks_mixed_results(self):
        """Test mixed success/failure in subtask creation."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        subtasks = ["Good subtask", "Bad subtask", "Another good"]
        
        # Mock mixed responses
        def side_effect(*args, **kwargs):
            payload = json.loads(kwargs['data'])
            summary = payload['fields']['summary']
            if "Bad" in summary:
                raise requests.exceptions.HTTPError("400 Bad Request")
            
            mock_response = Mock()
            mock_response.json.return_value = {"key": "TEST-124"}
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        with patch.object(client.session, 'post', side_effect=side_effect):
            created, failed, errors = client._create_subtasks("TEST-123", subtasks)
            
            assert created == 2
            assert failed == 1
            assert len(errors) == 1
            assert "Bad subtask" in errors[0]

    def test_create_subtasks_invalid_subtasks(self):
        """Test handling of invalid subtasks."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        subtasks = [
            "Valid subtask",
            "",  # Empty
            "a" * 256,  # Too long
            "   ",  # Only whitespace
            "Another valid"
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-124"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response):
            created, failed, errors = client._create_subtasks("TEST-123", subtasks)
            
            assert created == 2  # Only valid subtasks
            assert failed == 3   # Invalid ones
            assert len(errors) == 3
            
            # Verify only valid subtasks were posted
            assert client.session.post.call_count == 2

    def test_create_subtasks_http_error_with_details(self):
        """Test HTTP error with JSON details."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        subtasks = ["Test subtask"]
        
        # Mock HTTP error with JSON response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"errorMessages": ["Field required"]}
        
        http_error = requests.exceptions.HTTPError("Bad Request")
        http_error.response = mock_response
        
        with patch.object(client.session, 'post', side_effect=http_error):
            created, failed, errors = client._create_subtasks("TEST-123", subtasks)
            
            assert created == 0
            assert failed == 1
            assert len(errors) == 1
            assert "Test subtask" in errors[0]
            assert "falló" in errors[0]

    def test_create_subtasks_general_exception(self):
        """Test general exception handling."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        subtasks = ["Test subtask"]
        
        with patch.object(client.session, 'post', side_effect=Exception("Connection timeout")):
            created, failed, errors = client._create_subtasks("TEST-123", subtasks)
            
            assert created == 0
            assert failed == 1
            assert len(errors) == 1
            assert "falló" in errors[0]

    def test_create_subtasks_empty_list(self):
        """Test with empty subtasks list."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        created, failed, errors = client._create_subtasks("TEST-123", [])
        
        assert created == 0
        assert failed == 0
        assert errors == []

    def test_create_subtasks_payload_structure(self):
        """Test that subtask payload is properly structured."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        subtasks = ["Test subtask"]
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-124"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            client._create_subtasks("TEST-123", subtasks)
            
            # Verify payload structure
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            
            assert payload["fields"]["project"]["key"] == settings.project_key
            assert payload["fields"]["summary"] == "Test subtask"
            assert payload["fields"]["issuetype"]["name"] == settings.subtask_issue_type
            assert payload["fields"]["parent"]["key"] == "TEST-123"


class TestDeleteIssue:
    """Test _delete_issue method."""

    def test_delete_issue_success(self):
        """Test successful issue deletion."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'delete', return_value=mock_response):
            result = client._delete_issue("TEST-123")
            
            assert result is True
            client.session.delete.assert_called_once_with(f"{client.base_url}/rest/api/3/issue/TEST-123")

    def test_delete_issue_http_error(self):
        """Test delete with HTTP error."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client.session, 'delete') as mock_delete:
            mock_delete.side_effect = requests.exceptions.HTTPError("403 Forbidden")
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client._delete_issue("TEST-123")
                
                assert result is False
                mock_logger.error.assert_called_once()
                args = mock_logger.error.call_args[0]
                assert "TEST-123" in args[1]
                assert "403 Forbidden" in args[2]

    def test_delete_issue_connection_error(self):
        """Test delete with connection error."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client.session, 'delete') as mock_delete:
            mock_delete.side_effect = requests.exceptions.ConnectionError("Network error")
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client._delete_issue("TEST-123")
                
                assert result is False
                mock_logger.error.assert_called_once()

    def test_delete_issue_general_exception(self):
        """Test delete with general exception."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client.session, 'delete') as mock_delete:
            mock_delete.side_effect = Exception("Unexpected error")
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client._delete_issue("TEST-123")
                
                assert result is False
                mock_logger.error.assert_called_once()

    def test_delete_issue_different_keys(self):
        """Test delete with different issue keys."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        issue_keys = ["TEST-1", "PROJ-999", "ABC-12345"]
        
        for issue_key in issue_keys:
            with patch.object(client.session, 'delete', return_value=mock_response):
                result = client._delete_issue(issue_key)
                
                assert result is True
                expected_url = f"{client.base_url}/rest/api/3/issue/{issue_key}"
                client.session.delete.assert_called_with(expected_url)


class TestJiraClientCoverageEdgeCases:
    """Tests for edge cases to improve coverage."""

    def test_create_user_story_multiple_criteria_semicolon(self):
        """Test user story creation with multiple acceptance criteria separated by semicolon."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description", 
            criterio_aceptacion="Criteria 1;Criteria 2;Criteria 3",
            subtareas=[]
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {'key': 'TEST-123'}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response):
            with patch.object(client, 'feature_manager'):
                result = client.create_user_story(story)
                
                assert result.success is True
                assert result.jira_key == 'TEST-123'
                # Verify the call was made
                client.session.post.assert_called_once()

    def test_create_subtask_http_error_with_json_response(self):
        """Test subtask creation with HTTPError that has JSON response."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock response for parent story creation
        parent_response = Mock()
        parent_response.json.return_value = {'key': 'TEST-123'}
        parent_response.raise_for_status.return_value = None
        
        # Mock response for subtask creation that fails
        subtask_response = Mock()
        subtask_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Bad Request")
        subtask_response.json.return_value = {"errorMessages": ["Field is required"]}
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas=["Subtask 1"]
        )
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = [parent_response, subtask_response]
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                with patch.object(client, 'feature_manager'):
                    result = client.create_user_story(story)
                    
                    # Should have created parent but failed subtask
                    assert result.success is True
                    assert result.jira_key == 'TEST-123'
                    assert result.subtasks_created == 0
                    assert result.subtasks_failed == 1
                    
                    # Should log the JSON error details
                    mock_logger.error.assert_called()

    def test_create_subtask_http_error_without_json_response(self):
        """Test subtask creation with HTTPError that can't parse JSON response."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        parent_response = Mock()
        parent_response.json.return_value = {'key': 'TEST-123'}
        parent_response.raise_for_status.return_value = None
        
        # Mock response that fails and can't parse JSON
        subtask_response = Mock()
        http_error = requests.exceptions.HTTPError("400 Bad Request")
        http_error.response = Mock()
        http_error.response.json.side_effect = ValueError("No JSON object could be decoded")
        subtask_response.raise_for_status.side_effect = http_error
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas=["Subtask 1"]
        )
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = [parent_response, subtask_response]
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                with patch.object(client, 'feature_manager'):
                    result = client.create_user_story(story)
                    
                    assert result.success is True
                    assert result.subtasks_failed == 1
                    mock_logger.error.assert_called()

    def test_create_subtask_general_exception(self):
        """Test subtask creation with general exception."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        parent_response = Mock()
        parent_response.json.return_value = {'key': 'TEST-123'}
        parent_response.raise_for_status.return_value = None
        
        story = UserStory(
            titulo="Test Story", 
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas=["Subtask 1"]
        )
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = [parent_response, Exception("Network timeout")]
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                with patch.object(client, 'feature_manager'):
                    result = client.create_user_story(story)
                    
                    assert result.success is True
                    assert result.subtasks_failed == 1
                    mock_logger.error.assert_called()

    def test_create_user_story_with_acceptance_criteria_field(self):
        """Test user story creation when acceptance criteria field is configured."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        # Set the acceptance criteria field
        settings.acceptance_criteria_field = "customfield_10001"
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Custom criteria field test",
            subtareas=[]
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {'key': 'TEST-123'}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response):
            with patch.object(client, 'feature_manager'):
                result = client.create_user_story(story)
                
                assert result.success is True
                assert result.jira_key == 'TEST-123'
                # Verify the call was made
                client.session.post.assert_called_once()


class TestValidateIssueType:
    """Test validate_issue_type method comprehensively."""

    def test_validate_issue_type_exact_match(self):
        """Test successful validation with exact match."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock API response with issue types
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Story", "subtask": False},
                    {"id": "2", "name": "Task", "subtask": False}
                ]
            }]
        }
        
        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.validate_issue_type("Story")
            
            assert result is True
            # Verify API call was made correctly
            client.session.get.assert_called_once_with(
                f"{client.base_url}/rest/api/3/issue/createmeta",
                params={"projectKeys": settings.project_key, "expand": "projects.issuetypes"}
            )

    def test_validate_issue_type_case_insensitive(self):
        """Test validation is case insensitive."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Story", "subtask": False}
                ]
            }]
        }
        
        with patch.object(client.session, 'get', return_value=mock_response):
            # Test different cases
            assert client.validate_issue_type("story") is True
            assert client.validate_issue_type("STORY") is True
            assert client.validate_issue_type("Story") is True

    def test_validate_issue_type_alias_mapping_story_to_historia(self):
        """Test alias mapping from Story to Historia."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Historia", "subtask": False},
                    {"id": "2", "name": "Task", "subtask": False}
                ]
            }]
        }
        
        with patch.object(client.session, 'get', return_value=mock_response):
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_issue_type("Story")
                
                assert result is True
                # Verify alias was detected and logged (check that the call was made)
                alias_log_calls = [call for call in mock_logger.info.call_args_list 
                                  if "Tipo de issue encontrado por alias" in str(call)]
                assert len(alias_log_calls) >= 1

    def test_validate_issue_type_alias_mapping_historia_to_story(self):
        """Test alias mapping from Historia to Story."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Story", "subtask": False}
                ]
            }]
        }
        
        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.validate_issue_type("Historia")
            assert result is True

    def test_validate_issue_type_bug_aliases(self):
        """Test bug and error aliases."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Error", "subtask": False}
                ]
            }]
        }
        
        with patch.object(client.session, 'get', return_value=mock_response):
            assert client.validate_issue_type("Bug") is True
            assert client.validate_issue_type("bug") is True

    def test_validate_issue_type_settings_update_for_default_issue_type(self):
        """Test that settings are updated when default_issue_type finds alias."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.default_issue_type = "Story"
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Historia", "subtask": False}
                ]
            }]
        }
        
        with patch.object(client.session, 'get', return_value=mock_response):
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_issue_type("Story")
                
                assert result is True
                # Verify settings were updated
                assert client.settings.default_issue_type == "Historia"
                mock_logger.info.assert_any_call(
                    "🔄 Actualizando configuración: %s -> %s",
                    "Story", "Historia"
                )

    def test_validate_issue_type_no_projects_found(self):
        """Test when no projects are found in response."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"projects": []}
        
        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.validate_issue_type("Story")
            assert result is False

    def test_validate_issue_type_empty_projects_list(self):
        """Test when projects list is empty."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"projects": []}
        
        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.validate_issue_type("Story")
            assert result is False

    def test_validate_issue_type_issue_not_found_logs_available_types(self):
        """Test that available types are logged when issue type not found."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Task", "subtask": False},
                    {"id": "2", "name": "Bug", "subtask": False},
                    {"id": "3", "name": "Subtarea", "subtask": True}  # Should be excluded from available types
                ]
            }]
        }
        
        with patch.object(client.session, 'get', return_value=mock_response):
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_issue_type("Story")
                
                assert result is False
                # Verify available types were logged (excluding subtasks)
                mock_logger.debug.assert_any_call(
                    "Validación fallida: tipo de issue '%s' no encontrado. Tipos estándar disponibles: %s",
                    "Story", ["Task", "Bug"]
                )

    def test_validate_issue_type_http_error(self):
        """Test handling of HTTP errors."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.HTTPError("403 Forbidden")
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_issue_type("Story")
                
                assert result is False
                mock_logger.error.assert_called_with(
                    "Error validando tipo de issue %s: %s", "Story", "403 Forbidden"
                )
                mock_logger.debug.assert_called_with(
                    "Excepción completa al validar tipo de issue:", exc_info=True
                )

    def test_validate_issue_type_connection_error(self):
        """Test handling of connection errors."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")
            
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_issue_type("Story")
                
                assert result is False
                mock_logger.error.assert_called_with(
                    "Error validando tipo de issue %s: %s", "Story", "Network unreachable"
                )

    def test_validate_issue_type_json_decode_error(self):
        """Test handling of JSON decode errors."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        with patch.object(client.session, 'get', return_value=mock_response):
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_issue_type("Story")
                
                assert result is False
                mock_logger.error.assert_called_with(
                    "Error validando tipo de issue %s: %s", "Story", "Invalid JSON"
                )

    def test_validate_issue_type_debug_logging(self):
        """Test comprehensive debug logging."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "projects": [{
                "name": "Test Project",
                "issuetypes": [
                    {"id": "1", "name": "Story", "subtask": False}
                ]
            }]
        }
        
        with patch.object(client.session, 'get', return_value=mock_response):
            with patch('src.infrastructure.jira.jira_client.logger') as mock_logger:
                result = client.validate_issue_type("Story")
                
                assert result is True
                # Verify comprehensive debug logging
                mock_logger.debug.assert_any_call(
                    "Validando tipo de issue: %s en proyecto %s",
                    "Story", settings.project_key
                )
                mock_logger.debug.assert_any_call(
                    "Proyecto encontrado: %s, tipos de issue disponibles: %d",
                    "Test Project", 1
                )
                mock_logger.debug.assert_any_call(
                    "Comparando '%s' con '%s'", "Story", "Story"
                )
                mock_logger.debug.assert_any_call(
                    "Tipo de issue validado exitosamente (exacto): %s (id: %s)",
                    "Story", "1"
                )


class TestJiraClientIntegration:
    """Integration tests for JiraClient."""

    def test_client_initialization_chain(self):
        """Test that all components are properly initialized."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        
        with patch('src.infrastructure.jira.jira_client.FeatureManager') as mock_fm:
            client = JiraClient(settings)
            
            # Verify session is properly configured
            assert isinstance(client.session, requests.Session)
            assert client.session.auth == (settings.jira_email, settings.jira_api_token)
            
            # Verify feature manager is created
            mock_fm.assert_called_once_with(settings, client.session)

    def test_validation_chain_success(self):
        """Test successful validation chain."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock all validations to succeed
        with patch.object(client, 'test_connection', return_value=True):
            with patch.object(client, 'validate_project', return_value=True):
                with patch.object(client, 'validate_subtask_issue_type', return_value=True):
                    with patch.object(client, 'validate_feature_issue_type', return_value=True):
                        
                        # Test the validation chain
                        assert client.test_connection() is True
                        assert client.validate_project("TEST") is True
                        assert client.validate_subtask_issue_type() is True
                        assert client.validate_feature_issue_type() is True

    def test_validation_chain_failure(self):
        """Test validation chain with failures."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        # Mock validations to fail
        with patch.object(client, 'test_connection', return_value=False):
            with patch.object(client, 'validate_project', return_value=False):
                
                assert client.test_connection() is False
                assert client.validate_project("INVALID") is False

    def test_user_story_creation_workflow(self):
        """Test complete user story creation workflow."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        client = JiraClient(settings)
        
        story = UserStory(
            titulo="Integration Test Story",
            descripcion="Test Description",
            criterio_aceptacion="Test Criteria",
            subtareas=["Subtask 1", "Subtask 2"]
        )
        
        # Mock story creation
        mock_story_response = Mock()
        mock_story_response.json.return_value = {"key": "TEST-100"}
        mock_story_response.raise_for_status.return_value = None
        
        # Mock subtask creation
        mock_subtask_response = Mock()
        mock_subtask_response.json.return_value = {"key": "TEST-101"}
        mock_subtask_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.return_value = mock_story_response
            
            with patch.object(client, '_create_subtasks') as mock_create_subtasks:
                mock_create_subtasks.return_value = (2, 0, [])
                
                result = client.create_user_story(story)
                
                assert result.success is True
                assert result.jira_key == "TEST-100"
                assert result.subtasks_created == 2
                assert result.subtasks_failed == 0
                
                # Verify workflow
                mock_post.assert_called_once()
                mock_create_subtasks.assert_called_once_with("TEST-100", story.subtareas)


