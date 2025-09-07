"""Tests para el detector de metadatos de Jira."""
import pytest
import json
from unittest.mock import Mock, MagicMock, patch
import requests

from src.infrastructure.jira.metadata_detector import JiraMetadataDetector


@pytest.fixture
def mock_session():
    """Sesión mock para pruebas."""
    session = Mock(spec=requests.Session)
    return session


@pytest.fixture
def detector(mock_session):
    """Instancia del detector para pruebas."""
    return JiraMetadataDetector(mock_session, "https://test.atlassian.net", "TEST")


class TestJiraMetadataDetector:
    """Tests para JiraMetadataDetector."""

    def test_get_available_issue_types_success(self, detector, mock_session):
        """Test obtención exitosa de tipos de issue."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"name": "Story", "subtask": False},
                    {"name": "Feature", "subtask": False},
                    {"name": "Subtarea", "subtask": True},
                    {"name": "Sub-task", "subtask": True}
                ]
            }]
        }
        mock_session.get.return_value = mock_response

        # Act
        result = detector.get_available_issue_types()

        # Assert
        assert result["standard"] == ["Story", "Feature"]
        assert result["subtasks"] == ["Subtarea", "Sub-task"]
        assert result["all"] == ["Story", "Feature", "Subtarea", "Sub-task"]

    def test_get_available_issue_types_no_projects(self, detector, mock_session):
        """Test cuando no hay proyectos en la respuesta."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"projects": []}
        mock_session.get.return_value = mock_response

        # Act
        result = detector.get_available_issue_types()

        # Assert
        assert result == {"standard": [], "subtasks": [], "all": []}

    def test_get_available_issue_types_error(self, detector, mock_session):
        """Test manejo de errores en obtención de tipos."""
        # Arrange
        mock_session.get.side_effect = requests.RequestException("Connection error")

        # Act
        result = detector.get_available_issue_types()

        # Assert
        assert result == {"standard": [], "subtasks": [], "all": []}

    def test_detect_acceptance_criteria_fields_success(self, detector, mock_session):
        """Test detección exitosa de campos de criterios."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [{
                    "fields": {
                        "customfield_10001": {
                            "name": "Acceptance Criteria",
                            "schema": {"type": "string"}
                        },
                        "customfield_10002": {
                            "name": "Criterios de Aceptación",
                            "schema": {"type": "doc"}
                        },
                        "customfield_10003": {
                            "name": "Regular Field",
                            "schema": {"type": "string"}
                        },
                        "summary": {
                            "name": "Summary",
                            "schema": {"type": "string"}
                        }
                    }
                }]
            }]
        }
        mock_session.get.return_value = mock_response

        # Act
        result = detector.detect_acceptance_criteria_fields()

        # Assert
        assert len(result) == 2
        # El orden real depende de la lógica de relevancia (acceptance > criterios)
        assert result[0]["id"] == "customfield_10001"  # "acceptance" tiene mayor score
        assert result[0]["name"] == "Acceptance Criteria"
        assert result[1]["id"] == "customfield_10002"  # "criterios" tiene menor score
        assert result[1]["name"] == "Criterios de Aceptación"

    def test_detect_feature_required_fields_success(self, detector, mock_session):
        """Test detección de campos obligatorios para Features."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [{
                    "fields": {
                        "project": {"required": True, "name": "Project"},
                        "summary": {"required": True, "name": "Summary"},
                        "issuetype": {"required": True, "name": "Issue Type"},
                        "description": {"required": True, "name": "Description"},
                        "customfield_11493": {
                            "required": True,
                            "name": "Backlog",
                            "allowedValues": [
                                {"id": "54672", "value": "Product Backlog"}
                            ]
                        },
                        "customfield_10004": {
                            "name": "Epic Name",
                            "required": False
                        },
                        "customfield_10005": {
                            "required": True,
                            "name": "Priority Field",
                            "allowedValues": [
                                {"value": "High"},
                                {"value": "Medium"}
                            ]
                        }
                    }
                }]
            }]
        }
        mock_session.get.return_value = mock_response

        # Act
        required_fields, epic_name_field = detector.detect_feature_required_fields("Feature")

        # Assert
        assert epic_name_field == "customfield_10004"
        assert len(required_fields) == 2
        assert required_fields["customfield_11493"] == {"id": "54672"}
        assert required_fields["customfield_10005"] == {"value": "High"}

    def test_detect_feature_required_fields_no_epic_field(self, detector, mock_session):
        """Test cuando no hay campo Epic Name."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [{
                    "fields": {
                        "customfield_11493": {
                            "required": True,
                            "name": "Backlog",
                            "allowedValues": [{"id": "54672", "value": "Product Backlog"}]
                        }
                    }
                }]
            }]
        }
        mock_session.get.return_value = mock_response

        # Act
        required_fields, epic_name_field = detector.detect_feature_required_fields("Feature")

        # Assert
        assert epic_name_field is None
        assert len(required_fields) == 1

    def test_suggest_optimal_types_with_standard_names(self, detector):
        """Test sugerencia de tipos con nombres estándar."""
        # Arrange
        detector.get_available_issue_types = Mock(return_value={
            "standard": ["Story", "Feature", "Epic"],
            "subtasks": ["Subtarea", "Sub-task"],
            "all": ["Story", "Feature", "Epic", "Subtarea", "Sub-task"]
        })

        # Act
        result = detector.suggest_optimal_types()

        # Assert
        assert result["default_issue_type"] == "Story"
        assert result["subtask_issue_type"] == "Subtarea"
        assert result["feature_issue_type"] == "Feature"

    def test_suggest_optimal_types_with_spanish_names(self, detector):
        """Test sugerencia con nombres en español."""
        # Arrange
        detector.get_available_issue_types = Mock(return_value={
            "standard": ["Historia", "Funcionalidad", "Épica"],
            "subtasks": ["Sub-tarea"],
            "all": ["Historia", "Funcionalidad", "Épica", "Sub-tarea"]
        })

        # Act
        result = detector.suggest_optimal_types()

        # Assert
        assert result["default_issue_type"] == "Historia"
        assert result["subtask_issue_type"] == "Sub-tarea"
        assert result["feature_issue_type"] == "Funcionalidad"

    def test_suggest_optimal_types_fallback_to_first(self, detector):
        """Test fallback a primer tipo disponible cuando no hay matches."""
        # Arrange
        detector.get_available_issue_types = Mock(return_value={
            "standard": ["Custom Task", "Custom Parent"],
            "subtasks": ["Custom Sub"],
            "all": ["Custom Task", "Custom Parent", "Custom Sub"]
        })

        # Act
        result = detector.suggest_optimal_types()

        # Assert
        assert result["default_issue_type"] == "Custom Task"
        assert result["subtask_issue_type"] == "Custom Sub"
        # La lógica busca "parent" en el nombre, encuentra "Custom Parent"
        assert result["feature_issue_type"] == "Custom Parent"

    def test_filter_criteria_fields_with_various_names(self, detector):
        """Test filtrado de campos con varios nombres."""
        # Arrange
        fields = {
            "customfield_10001": {
                "name": "Acceptance Criteria",
                "schema": {"type": "string"}
            },
            "customfield_10002": {
                "name": "Test Conditions",
                "schema": {"type": "doc"}
            },
            "customfield_10003": {
                "name": "Requirements",
                "schema": {"type": "string"}
            },
            "customfield_10004": {
                "name": "Priority",
                "schema": {"type": "string"}
            },
            "summary": {
                "name": "Summary",
                "schema": {"type": "string"}
            }
        }

        # Act
        result = detector._filter_criteria_fields(fields)

        # Assert
        assert len(result) == 3
        # Verificar que están los campos correctos (sin importar orden exacto)
        field_names = [field["name"] for field in result]
        assert "Acceptance Criteria" in field_names
        assert "Requirements" in field_names  
        assert "Test Conditions" in field_names
        # El más relevante debería ser "Acceptance Criteria" (score 10)
        assert result[0]["name"] == "Acceptance Criteria"

    def test_filter_criteria_fields_no_matches(self, detector):
        """Test cuando no hay campos que coincidan."""
        # Arrange
        fields = {
            "customfield_10001": {
                "name": "Priority",
                "schema": {"type": "string"}
            },
            "summary": {
                "name": "Summary",
                "schema": {"type": "string"}
            }
        }

        # Act
        result = detector._filter_criteria_fields(fields)

        # Assert
        assert len(result) == 0

    def test_get_fields_for_issue_type_success(self, detector, mock_session):
        """Test obtención exitosa de campos para tipo de issue."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [{
                    "fields": {
                        "customfield_10001": {"name": "Test Field"}
                    }
                }]
            }]
        }
        mock_session.get.return_value = mock_response

        # Act
        result = detector._get_fields_for_issue_type("Story")

        # Assert
        assert result is not None
        assert "customfield_10001" in result
        assert result["customfield_10001"]["name"] == "Test Field"

    def test_get_fields_for_issue_type_error(self, detector, mock_session):
        """Test manejo de errores al obtener campos."""
        # Arrange
        mock_session.get.side_effect = requests.RequestException("Network error")

        # Act
        result = detector._get_fields_for_issue_type("Story")

        # Assert
        assert result is None

    def test_get_fields_for_issue_type_no_projects(self, detector, mock_session):
        """Test _get_fields_for_issue_type when no projects found."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"projects": []}
        mock_session.get.return_value = mock_response
        
        result = detector._get_fields_for_issue_type("Story")
        assert result is None

    def test_get_fields_for_issue_type_no_issuetypes(self, detector, mock_session):
        """Test _get_fields_for_issue_type when no issuetypes found."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{"issuetypes": []}]
        }
        mock_session.get.return_value = mock_response
        
        result = detector._get_fields_for_issue_type("Story")
        assert result is None

    def test_filter_criteria_fields_type_filtering(self, detector):
        """Test that _filter_criteria_fields correctly filters by field type."""
        fields = {
            "customfield_10001": {
                "name": "Acceptance Criteria",
                "schema": {"type": "string"}  # Valid type
            },
            "customfield_10002": {
                "name": "Test Requirements",
                "schema": {"type": "doc"}  # Valid type
            },
            "customfield_10003": {
                "name": "Criteria Field",
                "schema": {"type": "option"}  # Invalid type
            },
            "summary": {  # Non-custom field (should be excluded)
                "name": "Summary",
                "schema": {"type": "string"}
            }
        }
        
        result = detector._filter_criteria_fields(fields)
        
        # Should only include the valid custom fields
        assert len(result) == 2
        names = [field["name"] for field in result]
        assert "Acceptance Criteria" in names
        assert "Test Requirements" in names
        assert "Criteria Field" not in names  # Invalid type
        assert "Summary" not in names  # Not a custom field


class TestMetadataDetectorMethods:
    """Tests for various metadata detector methods."""

    def test_initialization_url_stripping(self, mock_session):
        """Test that base_url is properly stripped of trailing slashes."""
        test_urls = [
            ("https://test.atlassian.net/", "https://test.atlassian.net"),
            ("https://test.atlassian.net//", "https://test.atlassian.net"),
            ("https://test.atlassian.net", "https://test.atlassian.net"),
        ]
        
        for input_url, expected_url in test_urls:
            detector = JiraMetadataDetector(mock_session, input_url, "TEST")
            assert detector.base_url == expected_url
            assert detector.project_key == "TEST"
            assert detector.session == mock_session

    def test_suggest_optimal_types_container_keywords(self):
        """Test optimal type suggestions with container keywords."""
        detector = JiraMetadataDetector(Mock(), "https://test.atlassian.net", "TEST")
        
        detector.get_available_issue_types = Mock(return_value={
            "standard": ["Task", "Theme Container", "Parent Issue"],
            "subtasks": ["Subtarea"],
            "all": ["Task", "Theme Container", "Parent Issue", "Subtarea"]
        })
        
        result = detector.suggest_optimal_types()
        
        assert result["default_issue_type"] == "Task"
        assert result["subtask_issue_type"] == "Subtarea"
        # Should find "Theme Container" because it appears first and contains "theme"
        assert result["feature_issue_type"] == "Theme Container"

    def test_suggest_optimal_types_fallback_to_default(self):
        """Test fallback when no feature matches found."""
        detector = JiraMetadataDetector(Mock(), "https://test.atlassian.net", "TEST")
        
        detector.get_available_issue_types = Mock(return_value={
            "standard": ["Task", "Bug"],  # No feature-like names
            "subtasks": ["Subtarea"],
            "all": ["Task", "Bug", "Subtarea"]
        })
        
        result = detector.suggest_optimal_types()
        
        assert result["default_issue_type"] == "Task"
        assert result["subtask_issue_type"] == "Subtarea"
        # Should fallback to default_issue_type
        assert result["feature_issue_type"] == "Task"


class TestFindIssueTypeId:
    """Tests para el método _find_issue_type_id."""""

    def test_find_issue_type_id_exact_match(self, detector, mock_session):
        """Test encontrar tipo de issue con nombre exacto."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Story"},
                    {"id": "2", "name": "Bug"}
                ]
            }]
        }
        mock_session.get.return_value = mock_response

        # Act
        result = detector._find_issue_type_id("Story")

        # Assert
        assert result == "1"

    def test_find_issue_type_id_case_insensitive(self, detector, mock_session):
        """Test encontrar tipo de issue insensible a mayúsculas."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Historia"},
                    {"id": "2", "name": "Bug"}
                ]
            }]
        }
        mock_session.get.return_value = mock_response

        # Act - Buscar "story" debe encontrar "Historia"
        result = detector._find_issue_type_id("historia")

        # Assert
        assert result == "1"

    def test_find_issue_type_id_not_found(self, detector, mock_session):
        """Test cuando no se encuentra el tipo de issue."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "1", "name": "Bug"},
                    {"id": "2", "name": "Task"}
                ]
            }]
        }
        mock_session.get.return_value = mock_response

        # Act
        result = detector._find_issue_type_id("Story")

        # Assert
        assert result is None

    def test_find_issue_type_id_no_projects(self, detector, mock_session):
        """Test cuando no hay proyectos en la respuesta."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"projects": []}
        mock_session.get.return_value = mock_response

        # Act
        result = detector._find_issue_type_id("Story")

        # Assert
        assert result is None

    def test_find_issue_type_id_network_error(self, detector, mock_session):
        """Test manejo de errores de red."""
        # Arrange
        mock_session.get.side_effect = requests.RequestException("Network error")

        # Act
        result = detector._find_issue_type_id("Story")

        # Assert
        assert result is None


class TestDetectStoryRequiredFields:
    """Tests para detect_story_required_fields."""

    def test_detect_story_required_fields_success(self, detector, mock_session):
        """Test successful detection of required fields."""
        # Mock _find_issue_type_id to return an ID
        find_id_response = Mock()
        find_id_response.raise_for_status = Mock()
        find_id_response.json.return_value = {
            "projects": [{
                "issuetypes": [{"id": "10", "name": "Story"}]
            }]
        }
        
        # Mock createmeta call response
        createmeta_response = Mock()
        createmeta_response.raise_for_status = Mock()
        createmeta_response.json.return_value = {
            "projects": [{
                "name": "Test Project",
                "id": "12345",
                "issuetypes": [{
                    "name": "Story",
                    "id": "10",
                    "fields": {
                        # Basic fields (should be excluded)
                        "summary": {"name": "Summary", "required": True},
                        "description": {"name": "Description", "required": True},
                        
                        # Required custom field with allowed values (ID)
                        "customfield_10001": {
                            "name": "Priority Level",
                            "required": True,
                            "allowedValues": [{"id": "1", "value": "High"}]
                        },
                        
                        # Required custom field with allowed values (value)
                        "customfield_10002": {
                            "name": "Component",
                            "required": True,
                            "allowedValues": [{"value": "Backend"}]
                        },
                        
                        # Required string field without allowed values
                        "customfield_10003": {
                            "name": "Text Field",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        
                        # Required number field
                        "customfield_10004": {
                            "name": "Story Points",
                            "required": True,
                            "schema": {"type": "number"}
                        },
                        
                        # Non-required field (should be excluded)
                        "customfield_10005": {
                            "name": "Optional Field",
                            "required": False
                        }
                    }
                }]
            }]
        }
        
        # First call for _find_issue_type_id, second for createmeta
        mock_session.get.side_effect = [find_id_response, createmeta_response]
        
        # Act
        result = detector.detect_story_required_fields("Story")
        
        # Assert
        assert len(result) == 4  # 4 required custom fields
        assert result["customfield_10001"] == {"id": "1"}
        assert result["customfield_10002"] == {"value": "Backend"}
        assert result["customfield_10003"] == "default_value"  # String type default
        assert result["customfield_10004"] == 0  # Number type default
        
        # Verify excluded fields
        for excluded in ["summary", "description", "customfield_10005"]:
            assert excluded not in result
            
        # Verify both API calls were made
        assert mock_session.get.call_count == 2

    def test_detect_story_required_fields_type_not_found(self, detector, mock_session):
        """Test cuando el tipo no se encuentra."""
        # Arrange - Mock response without the Story type
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "11", "name": "Bug"},
                    {"id": "12", "name": "Task"}
                ]
            }]
        }
        mock_session.get.return_value = mock_response

        # Act
        result = detector.detect_story_required_fields("Story")

        # Assert
        assert result == {}
        assert mock_session.get.call_count == 1  # Only _find_issue_type_id call

    def test_detect_story_required_fields_http_error(self, detector, mock_session):
        """Test HTTP error during story required fields detection."""
        # Arrange
        mock_session.get.side_effect = requests.RequestException("Network error")
        
        # Act
        result = detector.detect_story_required_fields("Story")
        
        # Assert
        assert result == {}

    def test_detect_acceptance_criteria_fields_error(self, detector, mock_session):
        """Test error handling in acceptance criteria detection."""
        with patch.object(detector, '_get_fields_for_issue_type', side_effect=Exception("API Error")):
            result = detector.detect_acceptance_criteria_fields()
            assert result == []

    def test_detect_acceptance_criteria_fields_fallback_to_standard_type(self, detector, mock_session):
        """Test fallback to first standard type when story types not found."""
        detector.get_available_issue_types = Mock(return_value={
            "standard": ["Task"],
            "subtasks": ["Subtarea"],
            "all": ["Task", "Subtarea"]
        })
        
        # Mock fields response for Task
        task_fields = {
            "customfield_10001": {
                "name": "Acceptance Criteria",
                "schema": {"type": "string"}
            }
        }
        
        with patch.object(detector, '_get_fields_for_issue_type') as mock_get_fields:
            # Return None for story types, then return fields for Task
            mock_get_fields.side_effect = [None, None, None, None, task_fields]
            
            result = detector.detect_acceptance_criteria_fields()
            
            # Should have found criteria field from Task type
            assert len(result) == 1
            assert result[0]["name"] == "Acceptance Criteria"