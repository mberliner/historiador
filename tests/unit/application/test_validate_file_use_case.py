"""Tests for ValidateFileUseCase."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import pandas as pd

from src.application.use_cases.validate_file import ValidateFileUseCase
from src.domain.entities.user_story import UserStory
from tests.fixtures.sample_data import SAMPLE_STORIES, create_sample_csv


class TestValidateFileUseCaseInit:
    """Test ValidateFileUseCase initialization."""

    def test_init(self):
        """Test proper initialization."""
        use_case = ValidateFileUseCase()
        
        assert use_case.file_processor is not None

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_init_creates_file_processor(self, mock_file_processor):
        """Test that FileProcessor is created properly."""
        use_case = ValidateFileUseCase()
        
        mock_file_processor.assert_called_once()


class TestExecuteMethod:
    """Test execute method with various scenarios."""

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_with_valid_csv(self, mock_file_processor):
        """Test validating a CSV file with valid stories."""
        # Setup mock FileProcessor
        mock_fp_instance = Mock()
        
        # Mock preview_file to return a DataFrame
        preview_df = pd.DataFrame([
            ['Historia 1', 'Descripción 1', 'Subtarea 1', 'Criterio 1', ''],
            ['Historia 2', 'Descripción 2', '', 'Criterio 2', 'PROJ-123']
        ], columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        
        # Mock process_file to return user stories
        stories = [
            UserStory(titulo="Historia 1", descripcion="Descripción 1", 
                     criterio_aceptacion="Criterio 1", subtareas=["Subtarea 1"]),
            UserStory(titulo="Historia 2", descripcion="Descripción 2", 
                     criterio_aceptacion="Criterio 2", parent="PROJ-123")
        ]
        mock_fp_instance.process_file.return_value = iter(stories)
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        result = use_case.execute("test.csv", 5)
        
        # Verify result structure
        assert result['file'] == "test.csv"
        assert result['rows'] == 5
        assert 'preview' in result
        assert result['total_stories'] == 2
        assert result['with_subtasks'] == 1
        assert result['total_subtasks'] == 1
        assert result['with_parent'] == 1
        assert result['invalid_subtasks'] == 0
        
        # Verify mock calls
        mock_fp_instance.preview_file.assert_called_once_with("test.csv", 5)
        mock_fp_instance.process_file.assert_called_once_with("test.csv")

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_with_empty_file(self, mock_file_processor):
        """Test validating an empty file."""
        mock_fp_instance = Mock()
        
        # Empty preview
        preview_df = pd.DataFrame(columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        
        # No stories
        mock_fp_instance.process_file.return_value = iter([])
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        result = use_case.execute("empty.csv")
        
        assert result['total_stories'] == 0
        assert result['with_subtasks'] == 0
        assert result['total_subtasks'] == 0
        assert result['with_parent'] == 0
        assert result['invalid_subtasks'] == 0

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_with_invalid_subtasks(self, mock_file_processor):
        """Test validating file with invalid subtasks."""
        mock_fp_instance = Mock()
        
        preview_df = pd.DataFrame([
            ['Historia 1', 'Descripción 1', 'Subtarea válida;', 'Criterio 1', ''],
            ['Historia 2', 'Descripción 2', 'x' * 300, 'Criterio 2', '']  # Too long
        ], columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        
        # Stories with invalid subtasks
        stories = [
            UserStory(titulo="Historia 1", descripcion="Descripción 1", 
                     criterio_aceptacion="Criterio 1", 
                     subtareas=["Subtarea válida", ""]),  # Empty subtask
            UserStory(titulo="Historia 2", descripcion="Descripción 2", 
                     criterio_aceptacion="Criterio 2", 
                     subtareas=["x" * 300])  # Too long subtask
        ]
        mock_fp_instance.process_file.return_value = iter(stories)
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        result = use_case.execute("invalid.csv")
        
        assert result['total_stories'] == 2
        assert result['with_subtasks'] == 2
        assert result['total_subtasks'] == 3
        assert result['invalid_subtasks'] == 2  # One empty, one too long

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_with_multiple_subtasks(self, mock_file_processor):
        """Test validating file with multiple subtasks per story."""
        mock_fp_instance = Mock()
        
        preview_df = pd.DataFrame([
            ['Historia 1', 'Descripción 1', 'Sub1;Sub2;Sub3', 'Criterio 1', '']
        ], columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        
        stories = [
            UserStory(titulo="Historia 1", descripcion="Descripción 1", 
                     criterio_aceptacion="Criterio 1", 
                     subtareas=["Sub1", "Sub2", "Sub3"])
        ]
        mock_fp_instance.process_file.return_value = iter(stories)
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        result = use_case.execute("multi.csv")
        
        assert result['total_stories'] == 1
        assert result['with_subtasks'] == 1
        assert result['total_subtasks'] == 3
        assert result['invalid_subtasks'] == 0

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_with_mixed_parents(self, mock_file_processor):
        """Test validating file with different types of parents."""
        mock_fp_instance = Mock()
        
        preview_df = pd.DataFrame([
            ['Historia 1', 'Descripción 1', '', 'Criterio 1', 'PROJ-123'],
            ['Historia 2', 'Descripción 2', '', 'Criterio 2', 'Nueva Feature'],
            ['Historia 3', 'Descripción 3', '', 'Criterio 3', '']
        ], columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        
        stories = [
            UserStory(titulo="Historia 1", descripcion="Descripción 1", 
                     criterio_aceptacion="Criterio 1", parent="PROJ-123"),
            UserStory(titulo="Historia 2", descripcion="Descripción 2", 
                     criterio_aceptacion="Criterio 2", parent="Nueva Feature"),
            UserStory(titulo="Historia 3", descripcion="Descripción 3", 
                     criterio_aceptacion="Criterio 3")
        ]
        mock_fp_instance.process_file.return_value = iter(stories)
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        result = use_case.execute("parents.csv")
        
        assert result['total_stories'] == 3
        assert result['with_parent'] == 2
        assert result['with_subtasks'] == 0

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_with_custom_preview_rows(self, mock_file_processor):
        """Test validating with custom preview rows."""
        mock_fp_instance = Mock()
        
        preview_df = pd.DataFrame([
            ['Historia 1', 'Descripción 1', '', 'Criterio 1', '']
        ], columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        
        stories = [
            UserStory(titulo="Historia 1", descripcion="Descripción 1", 
                     criterio_aceptacion="Criterio 1")
        ]
        mock_fp_instance.process_file.return_value = iter(stories)
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        result = use_case.execute("test.csv", 10)
        
        assert result['rows'] == 10
        mock_fp_instance.preview_file.assert_called_once_with("test.csv", 10)

    def test_execute_with_real_file(self, temp_dir):
        """Test validating a real CSV file."""
        # Create a real CSV file
        test_file = temp_dir / "real_test.csv"
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        use_case = ValidateFileUseCase()
        result = use_case.execute(str(test_file))
        
        # Verify basic structure
        assert 'file' in result
        assert 'preview' in result
        assert 'total_stories' in result
        assert result['total_stories'] > 0


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_file_not_found(self, mock_file_processor):
        """Test handling of file not found error."""
        mock_fp_instance = Mock()
        mock_fp_instance.preview_file.side_effect = FileNotFoundError("File not found")
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        
        with pytest.raises(FileNotFoundError):
            use_case.execute("nonexistent.csv")

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_invalid_file_format(self, mock_file_processor):
        """Test handling of invalid file format error."""
        mock_fp_instance = Mock()
        mock_fp_instance.preview_file.side_effect = ValueError("Invalid format")
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        
        with pytest.raises(ValueError):
            use_case.execute("invalid.txt")

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_processing_error(self, mock_file_processor):
        """Test handling of processing error."""
        mock_fp_instance = Mock()
        
        # Preview works but processing fails
        preview_df = pd.DataFrame([
            ['Historia 1', 'Descripción 1', '', 'Criterio 1', '']
        ], columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        mock_fp_instance.process_file.side_effect = ValueError("Processing error")
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        
        with pytest.raises(ValueError):
            use_case.execute("bad_data.csv")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_with_none_values(self, mock_file_processor):
        """Test validating file with None values in subtasks/parent."""
        mock_fp_instance = Mock()
        
        preview_df = pd.DataFrame([
            ['Historia 1', 'Descripción 1', None, 'Criterio 1', None]
        ], columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        
        # UserStory with None values (should be converted to empty)
        stories = [
            UserStory(titulo="Historia 1", descripcion="Descripción 1", 
                     criterio_aceptacion="Criterio 1")
        ]
        mock_fp_instance.process_file.return_value = iter(stories)
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        result = use_case.execute("none_values.csv")
        
        assert result['total_stories'] == 1
        assert result['with_subtasks'] == 0
        assert result['with_parent'] == 0

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_with_zero_preview_rows(self, mock_file_processor):
        """Test validating with zero preview rows."""
        mock_fp_instance = Mock()
        
        # Empty preview
        preview_df = pd.DataFrame(columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        
        stories = [
            UserStory(titulo="Historia 1", descripcion="Descripción 1", 
                     criterio_aceptacion="Criterio 1")
        ]
        mock_fp_instance.process_file.return_value = iter(stories)
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        result = use_case.execute("test.csv", 0)
        
        assert result['rows'] == 0
        assert result['total_stories'] == 1  # Still processes all stories
        mock_fp_instance.preview_file.assert_called_once_with("test.csv", 0)

    @patch('src.application.use_cases.validate_file.FileProcessor')
    def test_execute_large_file_stats(self, mock_file_processor):
        """Test statistics calculation with large number of stories."""
        mock_fp_instance = Mock()
        
        # Large preview
        preview_df = pd.DataFrame([[f'Historia {i}', f'Desc {i}', '', f'Crit {i}', ''] 
                                  for i in range(100)], 
                                columns=['titulo', 'descripcion', 'subtareas', 'criterio_aceptacion', 'parent'])
        mock_fp_instance.preview_file.return_value = preview_df
        
        # Create many stories with different combinations
        stories = []
        for i in range(1000):
            story = UserStory(titulo=f"Historia {i}", descripcion=f"Desc {i}", 
                            criterio_aceptacion=f"Crit {i}")
            if i % 3 == 0:  # Every 3rd has subtasks
                story.subtareas = [f"Sub {i}-1", f"Sub {i}-2"]
            if i % 5 == 0:  # Every 5th has parent
                story.parent = f"PROJ-{i}"
            stories.append(story)
        
        mock_fp_instance.process_file.return_value = iter(stories)
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ValidateFileUseCase()
        result = use_case.execute("large.csv")
        
        assert result['total_stories'] == 1000
        assert result['with_subtasks'] == 334  # Stories 0, 3, 6, 9, ..., 999
        assert result['total_subtasks'] == 334 * 2  # Each has 2 subtasks
        assert result['with_parent'] == 200  # Stories 0, 5, 10, ..., 995
        assert result['invalid_subtasks'] == 0