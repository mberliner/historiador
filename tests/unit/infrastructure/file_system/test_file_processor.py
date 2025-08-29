"""Tests for FileProcessor."""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, mock_open
import tempfile
import os

from src.infrastructure.file_system.file_processor import FileProcessor
from src.domain.entities.user_story import UserStory
from tests.fixtures.sample_data import SAMPLE_STORIES, create_sample_csv


class TestFileProcessorInit:
    """Test FileProcessor initialization."""

    def test_init(self):
        """Test proper initialization."""
        processor = FileProcessor()
        
        assert processor.supported_extensions == ['.csv', '.xlsx', '.xls']
        assert processor.REQUIRED_COLUMNS == ['titulo', 'descripcion', 'criterio_aceptacion']
        assert processor.OPTIONAL_COLUMNS == ['subtareas', 'parent']


class TestValidateFile:
    """Test validate_file method."""

    def test_validate_file_exists_csv(self, temp_dir):
        """Test validation of existing CSV file."""
        processor = FileProcessor()
        test_file = temp_dir / "test.csv"
        test_file.touch()
        
        # Should not raise any exception
        processor.validate_file(str(test_file))

    def test_validate_file_exists_xlsx(self, temp_dir):
        """Test validation of existing Excel file."""
        processor = FileProcessor()
        test_file = temp_dir / "test.xlsx"
        test_file.touch()
        
        # Should not raise any exception
        processor.validate_file(str(test_file))

    def test_validate_file_exists_xls(self, temp_dir):
        """Test validation of existing Excel file (old format)."""
        processor = FileProcessor()
        test_file = temp_dir / "test.xls"
        test_file.touch()
        
        # Should not raise any exception
        processor.validate_file(str(test_file))

    def test_validate_file_not_exists(self):
        """Test validation of non-existent file."""
        processor = FileProcessor()
        
        with pytest.raises(FileNotFoundError, match="El archivo nonexistent.csv no existe"):
            processor.validate_file("nonexistent.csv")

    def test_validate_file_unsupported_extension(self, temp_dir):
        """Test validation of file with unsupported extension."""
        processor = FileProcessor()
        test_file = temp_dir / "test.txt"
        test_file.touch()
        
        with pytest.raises(ValueError, match="Extensión no soportada.*csv.*xlsx.*xls"):
            processor.validate_file(str(test_file))

    def test_validate_file_case_insensitive_extensions(self, temp_dir):
        """Test that extension validation is case insensitive."""
        processor = FileProcessor()
        
        # Test uppercase extensions
        for ext in ['.CSV', '.XLSX', '.XLS']:
            test_file = temp_dir / f"test{ext}"
            test_file.touch()
            # Should not raise any exception
            processor.validate_file(str(test_file))

    def test_validate_file_mixed_case_extensions(self, temp_dir):
        """Test mixed case extensions."""
        processor = FileProcessor()
        
        # Test mixed case extensions
        for ext in ['.Csv', '.XlSx', '.xLs']:
            test_file = temp_dir / f"test{ext}"
            test_file.touch()
            # Should not raise any exception
            processor.validate_file(str(test_file))


class TestReadFile:
    """Test read_file method."""

    @patch('pandas.read_csv')
    def test_read_csv_file_success(self, mock_read_csv, temp_dir):
        """Test successful CSV file reading."""
        processor = FileProcessor()
        test_file = temp_dir / "test.csv"
        test_file.touch()
        
        # Mock successful read
        mock_df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        mock_read_csv.return_value = mock_df
        
        result = processor.read_file(str(test_file))
        
        assert result.equals(mock_df)
        mock_read_csv.assert_called_once_with(str(test_file), encoding='utf-8')

    @patch('pandas.read_excel')
    def test_read_excel_file_success(self, mock_read_excel, temp_dir):
        """Test successful Excel file reading."""
        processor = FileProcessor()
        test_file = temp_dir / "test.xlsx"
        test_file.touch()
        
        # Mock successful read
        mock_df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        mock_read_excel.return_value = mock_df
        
        result = processor.read_file(str(test_file))
        
        assert result.equals(mock_df)
        mock_read_excel.assert_called_once_with(str(test_file))

    @patch('pandas.read_excel')
    def test_read_xls_file_success(self, mock_read_excel, temp_dir):
        """Test successful XLS file reading."""
        processor = FileProcessor()
        test_file = temp_dir / "test.xls"
        test_file.touch()
        
        # Mock successful read
        mock_df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        mock_read_excel.return_value = mock_df
        
        result = processor.read_file(str(test_file))
        
        assert result.equals(mock_df)
        mock_read_excel.assert_called_once_with(str(test_file))

    def test_read_file_not_exists(self):
        """Test reading non-existent file."""
        processor = FileProcessor()
        
        with pytest.raises(FileNotFoundError):
            processor.read_file("nonexistent.csv")

    @patch('pandas.read_csv')
    def test_read_csv_file_pandas_error(self, mock_read_csv, temp_dir):
        """Test handling of pandas read error."""
        processor = FileProcessor()
        test_file = temp_dir / "test.csv"
        test_file.touch()
        
        # Mock pandas error
        mock_read_csv.side_effect = pd.errors.EmptyDataError("No data")
        
        with pytest.raises(pd.errors.EmptyDataError):
            processor.read_file(str(test_file))

    @patch('pandas.read_excel')
    def test_read_excel_file_pandas_error(self, mock_read_excel, temp_dir):
        """Test handling of pandas Excel read error."""
        processor = FileProcessor()
        test_file = temp_dir / "test.xlsx"
        test_file.touch()
        
        # Mock pandas error
        mock_read_excel.side_effect = ValueError("Invalid Excel file")
        
        with pytest.raises(ValueError):
            processor.read_file(str(test_file))

    def test_read_file_real_csv(self, temp_dir):
        """Test reading a real CSV file."""
        processor = FileProcessor()
        test_file = temp_dir / "real_test.csv"
        
        # Create a real CSV file
        create_sample_csv(SAMPLE_STORIES[:2], str(test_file))
        
        result = processor.read_file(str(test_file))
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'titulo' in result.columns
        assert 'descripcion' in result.columns


class TestValidateColumns:
    """Test validate_columns method."""

    def test_validate_columns_success(self):
        """Test successful column validation."""
        processor = FileProcessor()
        df = pd.DataFrame({
            'titulo': ['Title 1'],
            'descripcion': ['Description 1'],
            'criterio_aceptacion': ['Criteria 1'],
            'subtareas': ['Subtask 1'],
            'parent': ['Parent 1']
        })
        
        # Should not raise any exception
        processor.validate_columns(df)

    def test_validate_columns_minimal_required(self):
        """Test validation with only required columns."""
        processor = FileProcessor()
        df = pd.DataFrame({
            'titulo': ['Title 1'],
            'descripcion': ['Description 1'],
            'criterio_aceptacion': ['Criteria 1']
        })
        
        # Should not raise any exception
        processor.validate_columns(df)

    def test_validate_columns_missing_one_required(self):
        """Test validation with one missing required column."""
        processor = FileProcessor()
        df = pd.DataFrame({
            'titulo': ['Title 1'],
            'descripcion': ['Description 1']
            # Missing 'criterio_aceptacion'
        })
        
        with pytest.raises(ValueError, match="Columnas requeridas faltantes: criterio_aceptacion"):
            processor.validate_columns(df)

    def test_validate_columns_missing_multiple_required(self):
        """Test validation with multiple missing required columns."""
        processor = FileProcessor()
        df = pd.DataFrame({
            'titulo': ['Title 1']
            # Missing 'descripcion' and 'criterio_aceptacion'
        })
        
        with pytest.raises(ValueError, match="Columnas requeridas faltantes"):
            processor.validate_columns(df)

    def test_validate_columns_missing_all_required(self):
        """Test validation with all required columns missing."""
        processor = FileProcessor()
        df = pd.DataFrame({
            'other_col': ['Value 1']
        })
        
        with pytest.raises(ValueError, match="Columnas requeridas faltantes"):
            processor.validate_columns(df)

    def test_validate_columns_extra_columns_allowed(self):
        """Test that extra columns are allowed."""
        processor = FileProcessor()
        df = pd.DataFrame({
            'titulo': ['Title 1'],
            'descripcion': ['Description 1'],
            'criterio_aceptacion': ['Criteria 1'],
            'extra_col1': ['Extra 1'],
            'extra_col2': ['Extra 2']
        })
        
        # Should not raise any exception
        processor.validate_columns(df)


class TestProcessFile:
    """Test process_file method."""

    def test_process_file_success_minimal(self, temp_dir):
        """Test successful processing with minimal columns."""
        processor = FileProcessor()
        test_file = temp_dir / "minimal.csv"
        
        # Create CSV with only required columns
        minimal_data = [{
            'titulo': 'Historia 1',
            'descripcion': 'Descripción 1',
            'criterio_aceptacion': 'Criterio 1'
        }]
        
        create_sample_csv(minimal_data, str(test_file))
        
        stories = list(processor.process_file(str(test_file)))
        
        assert len(stories) == 1
        assert isinstance(stories[0], UserStory)
        assert stories[0].titulo == 'Historia 1'
        assert stories[0].descripcion == 'Descripción 1'
        assert stories[0].criterio_aceptacion == ['Criterio 1']
        assert stories[0].subtareas is None
        assert stories[0].parent is None

    def test_process_file_success_with_optionals(self, temp_dir):
        """Test successful processing with optional columns."""
        processor = FileProcessor()
        test_file = temp_dir / "complete.csv"
        
        create_sample_csv(SAMPLE_STORIES[:1], str(test_file))
        
        stories = list(processor.process_file(str(test_file)))
        
        assert len(stories) == 1
        story = stories[0]
        assert isinstance(story, UserStory)
        assert story.titulo == SAMPLE_STORIES[0]['titulo']
        assert story.subtareas is not None

    def test_process_file_multiple_stories(self, temp_dir):
        """Test processing multiple stories."""
        processor = FileProcessor()
        test_file = temp_dir / "multiple.csv"
        
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        stories = list(processor.process_file(str(test_file)))
        
        assert len(stories) == len(SAMPLE_STORIES)
        for i, story in enumerate(stories):
            assert isinstance(story, UserStory)
            assert story.titulo == SAMPLE_STORIES[i]['titulo']

    def test_process_file_empty_values_handling(self, temp_dir):
        """Test handling of empty values."""
        processor = FileProcessor()
        test_file = temp_dir / "empty_values.csv"
        
        # Create data with empty values
        data_with_empty = [{
            'titulo': 'Historia 1',
            'descripcion': 'Descripción 1',
            'criterio_aceptacion': 'Criterio 1',
            'subtareas': '',  # Empty string
            'parent': None   # None value
        }]
        
        create_sample_csv(data_with_empty, str(test_file))
        
        stories = list(processor.process_file(str(test_file)))
        
        assert len(stories) == 1
        story = stories[0]
        assert story.subtareas is None  # Empty string should become None
        assert story.parent is None

    def test_process_file_missing_optional_columns(self, temp_dir):
        """Test processing when optional columns are missing."""
        processor = FileProcessor()
        test_file = temp_dir / "no_optionals.csv"
        
        # Manually create CSV without optional columns
        content = "titulo,descripcion,criterio_aceptacion\n"
        content += "Historia 1,Descripción 1,Criterio 1\n"
        content += "Historia 2,Descripción 2,Criterio 2\n"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        stories = list(processor.process_file(str(test_file)))
        
        assert len(stories) == 2
        for story in stories:
            assert story.subtareas is None
            assert story.parent is None

    def test_process_file_invalid_data_in_row(self, temp_dir):
        """Test handling of invalid data in a row."""
        processor = FileProcessor()
        test_file = temp_dir / "invalid_row.csv"
        
        # Create CSV with invalid data (missing required field)
        content = "titulo,descripcion,criterio_aceptacion\n"
        content += "Historia válida,Descripción válida,Criterio válido\n"
        content += ",Descripción sin título,Criterio\n"  # Invalid: empty title
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with pytest.raises(ValueError, match="Error en fila 3"):
            list(processor.process_file(str(test_file)))

    def test_process_file_generator_behavior(self, temp_dir):
        """Test that process_file returns a generator."""
        processor = FileProcessor()
        test_file = temp_dir / "generator_test.csv"
        
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        result = processor.process_file(str(test_file))
        
        # Should be a generator, not a list
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')
        
        # Can iterate through it
        stories = []
        for story in result:
            stories.append(story)
            if len(stories) >= 2:  # Only take first 2
                break
        
        assert len(stories) == 2


class TestPreviewFile:
    """Test preview_file method."""

    def test_preview_file_default_rows(self, temp_dir):
        """Test preview with default number of rows."""
        processor = FileProcessor()
        test_file = temp_dir / "preview_test.csv"
        
        # Create file with more than 5 rows
        large_data = []
        for i in range(10):
            large_data.append({
                'titulo': f'Historia {i+1}',
                'descripcion': f'Descripción {i+1}',
                'criterio_aceptacion': f'Criterio {i+1}'
            })
        
        create_sample_csv(large_data, str(test_file))
        
        preview = processor.preview_file(str(test_file))
        
        assert isinstance(preview, pd.DataFrame)
        assert len(preview) == 5  # Default is 5 rows

    def test_preview_file_custom_rows(self, temp_dir):
        """Test preview with custom number of rows."""
        processor = FileProcessor()
        test_file = temp_dir / "preview_custom.csv"
        
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        preview = processor.preview_file(str(test_file), rows=2)
        
        assert len(preview) == 2

    def test_preview_file_more_rows_than_available(self, temp_dir):
        """Test preview when requesting more rows than available."""
        processor = FileProcessor()
        test_file = temp_dir / "preview_small.csv"
        
        create_sample_csv(SAMPLE_STORIES[:2], str(test_file))  # Only 2 rows
        
        preview = processor.preview_file(str(test_file), rows=10)
        
        assert len(preview) == 2  # Should return all available rows

    def test_preview_file_zero_rows(self, temp_dir):
        """Test preview with zero rows."""
        processor = FileProcessor()
        test_file = temp_dir / "preview_zero.csv"
        
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        preview = processor.preview_file(str(test_file), rows=0)
        
        assert len(preview) == 0
        assert isinstance(preview, pd.DataFrame)

    def test_preview_file_empty_file(self, temp_dir):
        """Test preview of empty file."""
        processor = FileProcessor()
        test_file = temp_dir / "empty_preview.csv"
        
        # Create empty CSV with headers only
        content = "titulo,descripcion,criterio_aceptacion\n"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        preview = processor.preview_file(str(test_file))
        
        assert len(preview) == 0
        assert isinstance(preview, pd.DataFrame)
        assert list(preview.columns) == ['titulo', 'descripcion', 'criterio_aceptacion']


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_process_file_file_not_found(self):
        """Test process_file with non-existent file."""
        processor = FileProcessor()
        
        with pytest.raises(FileNotFoundError):
            list(processor.process_file("nonexistent.csv"))

    def test_process_file_unsupported_extension(self, temp_dir):
        """Test process_file with unsupported extension."""
        processor = FileProcessor()
        test_file = temp_dir / "test.txt"
        test_file.touch()
        
        with pytest.raises(ValueError, match="Extensión no soportada"):
            list(processor.process_file(str(test_file)))

    def test_preview_file_file_not_found(self):
        """Test preview_file with non-existent file."""
        processor = FileProcessor()
        
        with pytest.raises(FileNotFoundError):
            processor.preview_file("nonexistent.csv")


class TestIntegration:
    """Integration tests combining multiple methods."""

    def test_full_workflow_csv(self, temp_dir):
        """Test complete workflow with CSV file."""
        processor = FileProcessor()
        test_file = temp_dir / "workflow.csv"
        
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        # 1. Validate file
        processor.validate_file(str(test_file))
        
        # 2. Preview file
        preview = processor.preview_file(str(test_file), rows=2)
        assert len(preview) == 2
        
        # 3. Read file
        df = processor.read_file(str(test_file))
        assert len(df) == len(SAMPLE_STORIES)
        
        # 4. Validate columns
        processor.validate_columns(df)
        
        # 5. Process file
        stories = list(processor.process_file(str(test_file)))
        assert len(stories) == len(SAMPLE_STORIES)
        
        for story in stories:
            assert isinstance(story, UserStory)

    def test_workflow_with_missing_optionals(self, temp_dir):
        """Test workflow with file missing optional columns."""
        processor = FileProcessor()
        test_file = temp_dir / "minimal_workflow.csv"
        
        # Create minimal CSV
        content = "titulo,descripcion,criterio_aceptacion\n"
        content += "Test Story,Test Description,Test Criteria\n"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Full workflow should work
        processor.validate_file(str(test_file))
        preview = processor.preview_file(str(test_file))
        assert 'titulo' in preview.columns
        
        stories = list(processor.process_file(str(test_file)))
        assert len(stories) == 1
        assert stories[0].titulo == "Test Story"
        assert stories[0].subtareas is None
        assert stories[0].parent is None