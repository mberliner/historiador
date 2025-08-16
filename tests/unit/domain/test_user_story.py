"""Tests for UserStory entity."""
import pytest
from pydantic import ValidationError

from src.domain.entities.user_story import UserStory


class TestUserStoryValidation:
    """Test UserStory validation rules."""

    def test_valid_user_story_creation(self):
        """Test creating a valid user story."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria"
        )
        
        assert story.titulo == "Test Story"
        assert story.descripcion == "Test description"
        assert story.criterio_aceptacion == "Test criteria"
        assert story.subtareas is None
        assert story.parent is None

    def test_titulo_required(self):
        """Test that titulo is required."""
        with pytest.raises(ValidationError) as exc_info:
            UserStory(
                titulo="",
                descripcion="Test description",
                criterio_aceptacion="Test criteria"
            )
        
        assert "titulo" in str(exc_info.value)

    def test_titulo_max_length(self):
        """Test titulo maximum length validation."""
        long_title = "x" * 256  # Exceeds 255 character limit
        
        with pytest.raises(ValidationError) as exc_info:
            UserStory(
                titulo=long_title,
                descripcion="Test description", 
                criterio_aceptacion="Test criteria"
            )
        
        assert "titulo" in str(exc_info.value)

    def test_titulo_valid_max_length(self):
        """Test titulo at maximum valid length."""
        max_title = "x" * 255  # Exactly at limit
        
        story = UserStory(
            titulo=max_title,
            descripcion="Test description",
            criterio_aceptacion="Test criteria"
        )
        
        assert len(story.titulo) == 255

    def test_descripcion_required(self):
        """Test that descripcion is required."""
        with pytest.raises(ValidationError) as exc_info:
            UserStory(
                titulo="Test Story",
                descripcion="",
                criterio_aceptacion="Test criteria"
            )
        
        assert "descripcion" in str(exc_info.value)

    def test_criterio_aceptacion_required(self):
        """Test that criterio_aceptacion is required."""
        with pytest.raises(ValidationError) as exc_info:
            UserStory(
                titulo="Test Story",
                descripcion="Test description",
                criterio_aceptacion=""
            )
        
        assert "criterio_aceptacion" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        with pytest.raises(ValidationError):
            UserStory()


class TestSubtareasParser:
    """Test subtareas parsing functionality."""

    def test_subtareas_none(self):
        """Test subtareas as None."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description", 
            criterio_aceptacion="Test criteria",
            subtareas=None
        )
        
        assert story.subtareas is None

    def test_subtareas_empty_string(self):
        """Test subtareas as empty string."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria", 
            subtareas=""
        )
        
        assert story.subtareas is None

    def test_subtareas_single_task(self):
        """Test subtareas with single task."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas="Single task"
        )
        
        assert story.subtareas == ["Single task"]

    def test_subtareas_semicolon_separated(self):
        """Test subtareas separated by semicolon."""
        story = UserStory(
            titulo="Test Story", 
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas="Task 1;Task 2;Task 3"
        )
        
        assert story.subtareas == ["Task 1", "Task 2", "Task 3"]

    def test_subtareas_newline_separated(self):
        """Test subtareas separated by newlines."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas="Task 1\nTask 2\nTask 3"
        )
        
        assert story.subtareas == ["Task 1", "Task 2", "Task 3"]

    def test_subtareas_mixed_separators(self):
        """Test subtareas with mixed separators."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description", 
            criterio_aceptacion="Test criteria",
            subtareas="Task 1;Task 2\nTask 3;Task 4"
        )
        
        assert story.subtareas == ["Task 1", "Task 2", "Task 3", "Task 4"]

    def test_subtareas_with_extra_whitespace(self):
        """Test subtareas parsing with extra whitespace."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas="  Task 1  ;  Task 2  \n  Task 3  "
        )
        
        assert story.subtareas == ["Task 1", "Task 2", "Task 3"]

    def test_subtareas_with_empty_parts(self):
        """Test subtareas parsing with empty parts."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria", 
            subtareas="Task 1;;Task 2;\n;Task 3"
        )
        
        assert story.subtareas == ["Task 1", "Task 2", "Task 3"]

    def test_subtareas_only_separators(self):
        """Test subtareas with only separators."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas=";;;\n\n;"
        )
        
        assert story.subtareas is None

    def test_subtareas_already_list(self):
        """Test subtareas when already a list."""
        task_list = ["Task 1", "Task 2", "Task 3"]
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas=task_list
        )
        
        assert story.subtareas == task_list


class TestParentField:
    """Test parent field functionality."""

    def test_parent_none(self):
        """Test parent as None."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            parent=None
        )
        
        assert story.parent is None

    def test_parent_jira_key(self):
        """Test parent as Jira key."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description", 
            criterio_aceptacion="Test criteria",
            parent="PROJ-123"
        )
        
        assert story.parent == "PROJ-123"

    def test_parent_description(self):
        """Test parent as feature description."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            parent="Sistema de Autenticación"
        )
        
        assert story.parent == "Sistema de Autenticación"

    def test_parent_empty_string(self):
        """Test parent as empty string."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            parent=""
        )
        
        # Empty string should be converted to None by Pydantic
        assert story.parent == ""


class TestUserStoryComplexScenarios:
    """Test complex scenarios and edge cases."""

    def test_full_user_story_with_all_fields(self):
        """Test complete user story with all fields."""
        story = UserStory(
            titulo="Complete Story",
            descripcion="Complete description with detailed requirements",
            criterio_aceptacion="Complete acceptance criteria;Second criteria;Third criteria",
            subtareas="Setup environment;Implement feature;Write tests;Deploy",
            parent="EPIC-456"
        )
        
        assert story.titulo == "Complete Story"
        assert "detailed requirements" in story.descripcion
        assert story.criterio_aceptacion.count(";") == 2
        assert len(story.subtareas) == 4
        assert story.parent == "EPIC-456"

    def test_story_with_unicode_characters(self):
        """Test story with unicode characters."""
        story = UserStory(
            titulo="História com acentos e ñ",
            descripcion="Descripción con caracteres especiales: áéíóú ñç",
            criterio_aceptacion="Critério de aceitação",
            subtareas="Tarefa 1;Tarefa 2",
            parent="Módulo de Autenticação"
        )
        
        assert "ñ" in story.titulo
        assert "áéíóú" in story.descripcion
        assert "ção" in story.criterio_aceptacion
        assert len(story.subtareas) == 2

    def test_story_serialization(self):
        """Test story can be serialized to dict."""
        story = UserStory(
            titulo="Test Story",
            descripcion="Test description",
            criterio_aceptacion="Test criteria",
            subtareas="Task 1;Task 2",
            parent="TEST-100"
        )
        
        story_dict = story.model_dump()
        
        assert story_dict["titulo"] == "Test Story"
        assert story_dict["subtareas"] == ["Task 1", "Task 2"]
        assert story_dict["parent"] == "TEST-100"

    def test_story_from_dict(self):
        """Test creating story from dictionary."""
        story_data = {
            "titulo": "From Dict Story",
            "descripcion": "Created from dictionary",
            "criterio_aceptacion": "Dict criteria",
            "subtareas": ["Dict Task 1", "Dict Task 2"],
            "parent": "DICT-200"
        }
        
        story = UserStory(**story_data)
        
        assert story.titulo == "From Dict Story"
        assert story.subtareas == ["Dict Task 1", "Dict Task 2"]
        assert story.parent == "DICT-200"