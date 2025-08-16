"""Tests for FeatureManager."""
import pytest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.infrastructure.jira.feature_manager import FeatureManager
from src.infrastructure.settings import Settings

# Use test environment file
TEST_ENV_FILE = Path(__file__).parent.parent.parent.parent.parent / ".env.test"


class TestFeatureManagerInit:
    """Test FeatureManager initialization."""

    def test_init_with_settings_and_session(self):
        """Test proper initialization with settings and session."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        
        manager = FeatureManager(settings, session)
        
        assert manager.settings == settings
        assert manager.session == session
        assert manager.base_url == settings.jira_url.rstrip('/')
        assert manager._feature_cache == {}
        assert manager._epic_name_field_id is None
        assert manager._jira_key_pattern is not None

    def test_init_base_url_stripping(self):
        """Test that trailing slashes are stripped from base URL."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.jira_url = "https://test.atlassian.net///"
        session = Mock(spec=requests.Session)
        
        manager = FeatureManager(settings, session)
        
        assert manager.base_url == "https://test.atlassian.net"


class TestIsJiraKey:
    """Test is_jira_key method."""

    def test_is_jira_key_valid_keys(self):
        """Test valid Jira keys."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        valid_keys = [
            "TEST-123",
            "PROJ-1", 
            "ABC-999",
            "A-1",
            "ABC123-789"
        ]
        
        for key in valid_keys:
            assert manager.is_jira_key(key) is True
        
        # This should be invalid due to multiple dashes
        assert manager.is_jira_key("MY-PROJECT-456") is False

    def test_is_jira_key_invalid_keys(self):
        """Test invalid Jira keys."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        invalid_keys = [
            "test-123",  # lowercase
            "TEST",      # no number
            "123-TEST",  # number first
            "TEST-",     # no number after dash
            "-123",      # no letters
            "TEST 123",  # space instead of dash
            "TEST-ABC",  # letters after dash
            "",          # empty
            None,        # None
            "Feature description", # regular text
            "A feature about something" # regular description
        ]
        
        for key in invalid_keys:
            assert manager.is_jira_key(key) is False

    def test_is_jira_key_whitespace_handling(self):
        """Test handling of whitespace in keys."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Valid with whitespace
        assert manager.is_jira_key("  TEST-123  ") is True
        
        # Invalid with internal whitespace
        assert manager.is_jira_key("TEST - 123") is False
        assert manager.is_jira_key("TEST-1 23") is False


class TestNormalizeDescription:
    """Test _normalize_description method."""

    def test_normalize_description_basic(self):
        """Test basic description normalization."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Test basic normalization
        assert manager._normalize_description("Feature Description") == "feature description"
        assert manager._normalize_description("  Multiple   Spaces  ") == "multiple spaces"
        assert manager._normalize_description("") == ""
        assert manager._normalize_description(None) == ""

    def test_normalize_description_accents(self):
        """Test accent removal."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        test_cases = [
            ("Función con acentos", "funcion con acentos"),
            ("Niño especial", "nino especial"),
            ("Configuración", "configuracion"),
            ("Público", "publico"),
            ("Integración", "integracion")
        ]
        
        for input_text, expected in test_cases:
            assert manager._normalize_description(input_text) == expected

    def test_normalize_description_punctuation(self):
        """Test punctuation removal."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        test_cases = [
            ("Feature description.", "feature description"),
            ("Feature description!", "feature description"),
            ("Feature description?", "feature description"),
            ("Feature: description;", "feature description"),
            ("Feature description...", "feature description"),
            ("Feature (description)", "feature description"),
            ("Feature-description", "feature-description"),  # Keep dashes
        ]
        
        for input_text, expected in test_cases:
            assert manager._normalize_description(input_text) == expected

    def test_normalize_description_special_characters(self):
        """Test special character handling."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        test_cases = [
            ("Feature@description", "featuredescription"),
            ("Feature#1", "feature1"),
            ("Feature$description", "featuredescription"),
            ("Feature%done", "featuredone"),
            ("Feature&more", "featuremore"),
            ("Feature-description", "feature-description"),  # Dashes preserved
            ("Feature_description", "feature_description"),  # Underscores preserved
        ]
        
        for input_text, expected in test_cases:
            assert manager._normalize_description(input_text) == expected


class TestValidateFeatureType:
    """Test validate_feature_type method."""

    def test_validate_feature_type_success(self):
        """Test successful feature type validation."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Mock issue types including Feature
        mock_issue_types = [
            {"id": "1", "name": "Story", "subtask": False},
            {"id": "2", "name": "Feature", "subtask": False},
            {"id": "3", "name": "Sub-task", "subtask": True}
        ]
        
        with patch.object(manager, '_get_issue_types', return_value=mock_issue_types):
            result = manager.validate_feature_type()
            
            assert result is True

    def test_validate_feature_type_not_found(self):
        """Test feature type validation when type not found."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Mock issue types without Feature
        mock_issue_types = [
            {"id": "1", "name": "Story", "subtask": False},
            {"id": "2", "name": "Task", "subtask": False},
            {"id": "3", "name": "Sub-task", "subtask": True}
        ]
        
        with patch.object(manager, '_get_issue_types', return_value=mock_issue_types):
            with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
                result = manager.validate_feature_type()
                
                assert result is False
                mock_logger.error.assert_called_once()

    def test_validate_feature_type_custom_type(self):
        """Test validation with custom feature type."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.feature_issue_type = "Epic"
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        mock_issue_types = [
            {"id": "1", "name": "Story", "subtask": False},
            {"id": "2", "name": "Epic", "subtask": False},
            {"id": "3", "name": "Sub-task", "subtask": True}
        ]
        
        with patch.object(manager, '_get_issue_types', return_value=mock_issue_types):
            result = manager.validate_feature_type()
            
            assert result is True

    def test_validate_feature_type_exception(self):
        """Test feature type validation with exception."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        with patch.object(manager, '_get_issue_types', side_effect=Exception("API Error")):
            with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
                result = manager.validate_feature_type()
                
                assert result is False
                mock_logger.error.assert_called_with("Error validando tipo de feature: %s", "API Error")


class TestGetRequiredFieldsForFeature:
    """Test get_required_fields_for_feature method."""

    def test_get_required_fields_success(self):
        """Test successful retrieval of required fields."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Mock createmeta response
        mock_response = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [{
                    "fields": {
                        "project": {"required": True},
                        "summary": {"required": True},
                        "issuetype": {"required": True},
                        "description": {"required": True},
                        "customfield_10002": {
                            "name": "Epic Name",
                            "required": False
                        },
                        "customfield_10001": {
                            "name": "Story Points",
                            "required": True,
                            "allowedValues": [
                                {"id": "1", "value": "1"},
                                {"id": "2", "value": "2"}
                            ]
                        }
                    }
                }]
            }]
        }
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response
        
        result = manager.get_required_fields_for_feature()
        
        # Should return the custom required field with default value
        assert "customfield_10001" in result
        assert result["customfield_10001"]["id"] == "1"
        
        # Should detect Epic Name field
        assert manager._epic_name_field_id == "customfield_10002"

    def test_get_required_fields_no_projects(self):
        """Test handling when no projects are returned."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        mock_response = Mock()
        mock_response.json.return_value = {"projects": []}
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response
        
        with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
            result = manager.get_required_fields_for_feature()
            
            assert result == {}
            mock_logger.warning.assert_called_once()

    def test_get_required_fields_http_error(self):
        """Test handling of HTTP errors."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        session.get.side_effect = requests.exceptions.HTTPError("400 Bad Request")
        
        with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
            result = manager.get_required_fields_for_feature()
            
            assert result == {}
            mock_logger.error.assert_called_once()


class TestValidateExistingIssue:
    """Test validate_existing_issue method."""

    @patch('src.infrastructure.jira.feature_manager.jira_utils.validate_issue_exists')
    def test_validate_existing_issue_delegates(self, mock_validate):
        """Test that validation is delegated to utils."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        mock_validate.return_value = True
        
        result = manager.validate_existing_issue("TEST-123")
        
        assert result is True
        mock_validate.assert_called_once_with(session, manager.base_url, "TEST-123")


class TestSearchExistingFeatures:
    """Test _search_existing_features method."""

    def test_search_existing_features_found_by_description(self):
        """Test finding existing feature by description."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Mock search response
        mock_response = Mock()
        mock_response.json.return_value = {
            "issues": [{
                "key": "TEST-100",
                "fields": {
                    "summary": "User Authentication Feature",
                    "description": {
                        "type": "doc",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "user authentication system"}]
                        }]
                    }
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response
        
        with patch.object(manager, '_generate_feature_title', return_value="User Authentication..."):
            result = manager._search_existing_features("user authentication system")
            
            assert result == "TEST-100"

    def test_search_existing_features_not_found(self):
        """Test when no existing features are found."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        mock_response = Mock()
        mock_response.json.return_value = {"issues": []}
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response
        
        with patch.object(manager, '_generate_feature_title', return_value="New Feature..."):
            result = manager._search_existing_features("new feature description")
            
            assert result is None

    def test_search_existing_features_http_error(self):
        """Test handling of HTTP errors in search."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        session.get.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        
        with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
            with patch.object(manager, '_generate_feature_title', return_value="Feature..."):
                result = manager._search_existing_features("feature description")
                
                assert result is None
                mock_logger.warning.assert_called_once()


class TestExtractTextFromDescription:
    """Test _extract_text_from_description method."""

    def test_extract_text_from_description_valid(self):
        """Test extracting text from valid description field."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        description_field = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "First paragraph."},
                        {"type": "text", "text": " Second part."}
                    ]
                },
                {
                    "type": "paragraph", 
                    "content": [
                        {"type": "text", "text": "Second paragraph."}
                    ]
                }
            ]
        }
        
        result = manager._extract_text_from_description(description_field)
        
        # The method joins all text content and then paragraphs with spaces
        assert result == "First paragraph.  Second part. Second paragraph."

    def test_extract_text_from_description_empty(self):
        """Test extracting from empty or None description."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        assert manager._extract_text_from_description(None) == ""
        assert manager._extract_text_from_description({}) == ""
        assert manager._extract_text_from_description({"content": []}) == ""

    def test_extract_text_from_description_simple_string(self):
        """Test extracting from simple string description."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        result = manager._extract_text_from_description("Simple string description")
        
        assert result == "Simple string description"


class TestCreateFeature:
    """Test create_feature method."""

    def test_create_feature_dry_run(self):
        """Test feature creation in dry run mode."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        settings.dry_run = True
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
            result = manager.create_feature("Test feature description")
            
            assert result == "DRY-FEATURE-123"
            mock_logger.info.assert_called_once()

    def test_create_feature_success(self):
        """Test successful feature creation."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-200"}
        mock_response.raise_for_status.return_value = None
        session.post.return_value = mock_response
        
        with patch.object(manager, '_generate_feature_title', return_value="Test Feature..."):
            with patch.object(manager, 'get_required_fields_for_feature', return_value={}):
                result = manager.create_feature("Test feature description")
                
                assert result == "TEST-200"
                session.post.assert_called_once()

    def test_create_feature_with_required_fields(self):
        """Test feature creation with required fields."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-201"}
        mock_response.raise_for_status.return_value = None
        session.post.return_value = mock_response
        
        required_fields = {"customfield_10001": {"id": "1"}}
        
        with patch.object(manager, '_generate_feature_title', return_value="Test Feature..."):
            with patch.object(manager, 'get_required_fields_for_feature', return_value=required_fields):
                result = manager.create_feature("Test feature description")
                
                assert result == "TEST-201"
                
                # Verify required fields were included
                call_args = session.post.call_args
                payload = json.loads(call_args[1]['data'])
                assert "customfield_10001" in payload["fields"]

    def test_create_feature_with_epic_name(self):
        """Test feature creation with Epic Name field."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        manager._epic_name_field_id = "customfield_10002"
        
        mock_response = Mock()
        mock_response.json.return_value = {"key": "TEST-202"}
        mock_response.raise_for_status.return_value = None
        session.post.return_value = mock_response
        
        with patch.object(manager, '_generate_feature_title', return_value="Test Feature..."):
            with patch.object(manager, 'get_required_fields_for_feature', return_value={}):
                result = manager.create_feature("Test feature description")
                
                assert result == "TEST-202"
                
                # Verify Epic Name was set
                call_args = session.post.call_args
                payload = json.loads(call_args[1]['data'])
                assert payload["fields"]["customfield_10002"] == "Test Feature..."

    def test_create_feature_http_error(self):
        """Test feature creation with HTTP error."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        http_error = requests.exceptions.HTTPError("400 Bad Request")
        session.post.side_effect = http_error
        
        with patch.object(manager, '_generate_feature_title', return_value="Test Feature..."):
            with patch.object(manager, 'get_required_fields_for_feature', return_value={}):
                with patch('src.infrastructure.jira.feature_manager.jira_utils.handle_http_error') as mock_handle:
                    with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
                        result = manager.create_feature("Test feature description")
                        
                        assert result is None
                        mock_handle.assert_called_once_with(http_error, mock_logger)

    def test_create_feature_general_exception(self):
        """Test feature creation with general exception."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        session.post.side_effect = Exception("Connection timeout")
        
        with patch.object(manager, '_generate_feature_title', return_value="Test Feature..."):
            with patch.object(manager, 'get_required_fields_for_feature', return_value={}):
                with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
                    result = manager.create_feature("Test feature description")
                    
                    assert result is None
                    # The actual implementation logs the full message, not with %s format
                    mock_logger.error.assert_called_with("Error creando feature: Connection timeout")


class TestGetOrCreateParent:
    """Test get_or_create_parent method."""

    def test_get_or_create_parent_empty_text(self):
        """Test with empty or None parent text."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        test_cases = [None, "", "   "]
        
        for text in test_cases:
            result, was_created = manager.get_or_create_parent(text)
            assert result is None
            assert was_created is False

    def test_get_or_create_parent_existing_jira_key(self):
        """Test with existing Jira key."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        with patch.object(manager, 'is_jira_key', return_value=True):
            with patch.object(manager, 'validate_existing_issue', return_value=True):
                result, was_created = manager.get_or_create_parent("TEST-123")
                
                assert result == "TEST-123"
                assert was_created is False

    def test_get_or_create_parent_invalid_jira_key(self):
        """Test with invalid Jira key."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        with patch.object(manager, 'is_jira_key', return_value=True):
            with patch.object(manager, 'validate_existing_issue', return_value=False):
                with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
                    result, was_created = manager.get_or_create_parent("TEST-999")
                    
                    assert result is None
                    assert was_created is False
                    mock_logger.error.assert_called_once()

    def test_get_or_create_parent_cached_feature(self):
        """Test with cached feature description."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Pre-populate cache
        normalized_desc = manager._normalize_description("User Authentication Feature")
        manager._feature_cache[normalized_desc] = "TEST-100"
        
        with patch.object(manager, 'is_jira_key', return_value=False):
            result, was_created = manager.get_or_create_parent("User Authentication Feature")
            
            assert result == "TEST-100"
            assert was_created is False

    def test_get_or_create_parent_existing_feature_found(self):
        """Test finding existing feature in Jira."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        with patch.object(manager, 'is_jira_key', return_value=False):
            with patch.object(manager, '_search_existing_features', return_value="TEST-101"):
                result, was_created = manager.get_or_create_parent("New Feature Description")
                
                assert result == "TEST-101"
                assert was_created is False
                
                # Should be cached now
                normalized = manager._normalize_description("New Feature Description")
                assert manager._feature_cache[normalized] == "TEST-101"

    def test_get_or_create_parent_create_new_feature(self):
        """Test creating new feature."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        with patch.object(manager, 'is_jira_key', return_value=False):
            with patch.object(manager, '_search_existing_features', return_value=None):
                with patch.object(manager, 'create_feature', return_value="TEST-102"):
                    result, was_created = manager.get_or_create_parent("Brand New Feature")
                        
                    assert result == "TEST-102"
                    assert was_created is True
                    
                    # Should be cached now
                    normalized = manager._normalize_description("Brand New Feature")
                    assert manager._feature_cache[normalized] == "TEST-102"

    def test_get_or_create_parent_create_feature_fails(self):
        """Test when feature creation fails."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        with patch.object(manager, 'is_jira_key', return_value=False):
            with patch.object(manager, '_search_existing_features', return_value=None):
                with patch.object(manager, 'create_feature', return_value=None):
                    with patch('src.infrastructure.jira.feature_manager.logger') as mock_logger:
                        result, was_created = manager.get_or_create_parent("Failed Feature")
                        
                        assert result is None
                        assert was_created is False
                        mock_logger.error.assert_called_once()


class TestGenerateFeatureTitle:
    """Test _generate_feature_title method."""

    def test_generate_feature_title_short_description(self):
        """Test with short description."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        result = manager._generate_feature_title("Short description")
        assert result == "Short description"

    def test_generate_feature_title_long_description(self):
        """Test with long description."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        long_desc = "This is a very long feature description that should be truncated"
        result = manager._generate_feature_title(long_desc, max_length=30)
        
        assert result.endswith("...")
        assert len(result) <= 30

    def test_generate_feature_title_empty_description(self):
        """Test with empty description."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        result = manager._generate_feature_title("")
        assert result == "Feature sin título"

    def test_generate_feature_title_none_description(self):
        """Test with None description."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        result = manager._generate_feature_title(None)
        assert result == "Feature sin título"

    def test_generate_feature_title_word_boundary(self):
        """Test that title breaks at word boundaries."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # This should break after "word" not in the middle of "verylongword"
        desc = "Short word verylongwordthatcantfit more words"
        result = manager._generate_feature_title(desc, max_length=20)
        
        assert "Short word" in result
        assert result.endswith("...")


class TestGetIssueTypes:
    """Test _get_issue_types method."""

    @patch('src.infrastructure.jira.feature_manager.jira_utils.get_issue_types')
    def test_get_issue_types_delegates(self, mock_get_types):
        """Test that _get_issue_types delegates to utils."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        mock_issue_types = [{"id": "1", "name": "Story"}]
        mock_get_types.return_value = mock_issue_types
        
        result = manager._get_issue_types()
        
        assert result == mock_issue_types
        mock_get_types.assert_called_once_with(session, manager.base_url, settings.project_key)


class TestCacheManagement:
    """Test cache management methods."""

    def test_clear_cache(self):
        """Test clearing the feature cache."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Populate cache
        manager._feature_cache["test"] = "TEST-123"
        assert len(manager._feature_cache) == 1
        
        # Clear cache
        manager.clear_cache()
        assert len(manager._feature_cache) == 0

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Empty cache
        stats = manager.get_cache_stats()
        assert stats["cached_features"] == 0
        assert stats["features"] == []
        
        # Populate cache
        manager._feature_cache["desc1"] = "TEST-123"
        manager._feature_cache["desc2"] = "TEST-124"
        
        stats = manager.get_cache_stats()
        assert stats["cached_features"] == 2
        assert len(stats["features"]) == 2


class TestFeatureManagerIntegration:
    """Integration tests for FeatureManager."""

    def test_full_workflow_new_feature(self):
        """Test complete workflow for creating a new feature."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Mock all dependencies
        with patch.object(manager, 'is_jira_key', return_value=False):
            with patch.object(manager, '_search_existing_features', return_value=None):
                with patch.object(manager, 'create_feature', return_value="TEST-300") as mock_create:
                    
                    result, was_created = manager.get_or_create_parent("Complete New Feature")
                    
                    assert result == "TEST-300"
                    assert was_created is True
                    mock_create.assert_called_once_with("Complete New Feature")
                    
                    # Verify caching
                    normalized = manager._normalize_description("Complete New Feature")
                    assert manager._feature_cache[normalized] == "TEST-300"

    def test_full_workflow_existing_jira_key(self):
        """Test complete workflow with existing Jira key."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        with patch.object(manager, 'is_jira_key', return_value=True):
            with patch.object(manager, 'validate_existing_issue', return_value=True):
                
                result, was_created = manager.get_or_create_parent("PROJ-456")
                
                assert result == "PROJ-456"
                assert was_created is False
                
                # Should not be cached (it's an existing key)
                assert len(manager._feature_cache) == 0

    def test_complex_normalization_workflow(self):
        """Test normalization in realistic workflow."""
        settings = Settings(_env_file=str(TEST_ENV_FILE))
        session = Mock(spec=requests.Session)
        manager = FeatureManager(settings, session)
        
        # Similar descriptions should be normalized to same cache key
        descriptions = [
            "User Authentication System",
            "user authentication system",
            "User Authentication System.",
            "  User Authentication System  ",
            "User Authentication System!"
        ]
        
        # Mock search to return existing feature for first call
        first_call = True
        def mock_search(normalized_desc):
            nonlocal first_call
            if first_call:
                first_call = False
                return "TEST-FOUND"
            return "TEST-FOUND"  # Should use cache for subsequent calls
        
        with patch.object(manager, 'is_jira_key', return_value=False):
            with patch.object(manager, '_search_existing_features', side_effect=mock_search) as mock_search_calls:
                
                results = []
                for desc in descriptions:
                    result, was_created = manager.get_or_create_parent(desc)
                    results.append((result, was_created))
                
                # All should return same result
                for result, was_created in results:
                    assert result == "TEST-FOUND"
                    assert was_created is False
                
                # Search should only be called once (rest from cache)
                assert mock_search_calls.call_count == 1