"""Tests para el detector de metadatos de Jira."""
import pytest
import json
from unittest.mock import Mock, MagicMock
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


class TestFindIssueTypeId:
    """Tests para el método _find_issue_type_id"""

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


class TestDetectStoryRequiredFieldsWithAlias:
    """Tests para detect_story_required_fields con manejo de alias"""

    def test_detect_story_required_fields_alias_not_found(self, detector, mock_session):
        """Test cuando el alias no se encuentra en el proyecto."""
        # Arrange - Primera llamada no encuentra el tipo
        find_response = Mock()
        find_response.raise_for_status = Mock()
        find_response.json.return_value = {
            "projects": [{
                "issuetypes": [
                    {"id": "11", "name": "Bug"},
                    {"id": "12", "name": "Task"}
                ]
            }]
        }
        mock_session.get.return_value = find_response

        # Act
        result = detector.detect_story_required_fields("Story")

        # Assert
        assert result == {}
        # Solo debe hacer una llamada (_find_issue_type_id)
        assert mock_session.get.call_count == 1