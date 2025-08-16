"""Tests for ProcessFilesUseCase."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from src.application.use_cases.process_files import ProcessFilesUseCase
from src.domain.entities.batch_result import BatchResult
from src.domain.entities.process_result import ProcessResult
from src.domain.entities.user_story import UserStory
from tests.fixtures.sample_data import SAMPLE_STORIES, create_sample_csv


class TestProcessFilesUseCaseInit:
    """Test ProcessFilesUseCase initialization."""

    def test_init_with_settings(self, sample_settings):
        """Test proper initialization with settings."""
        use_case = ProcessFilesUseCase(sample_settings)
        
        assert use_case.settings == sample_settings
        assert use_case.file_processor is not None
        assert use_case.jira_client is not None

    @patch('src.application.use_cases.process_files.JiraClient')
    @patch('src.application.use_cases.process_files.FileProcessor')
    def test_init_creates_dependencies(self, mock_file_processor, mock_jira_client, sample_settings):
        """Test that dependencies are created properly."""
        use_case = ProcessFilesUseCase(sample_settings)
        
        mock_file_processor.assert_called_once()
        mock_jira_client.assert_called_once_with(sample_settings)


class TestFindInputFiles:
    """Test find_input_files method."""

    def test_find_input_files_empty_directory(self, sample_settings, temp_dir):
        """Test finding files in empty directory."""
        sample_settings.input_directory = str(temp_dir / "empty")
        use_case = ProcessFilesUseCase(sample_settings)
        
        files = use_case.find_input_files()
        
        assert files == []
        assert Path(sample_settings.input_directory).exists()

    def test_find_input_files_nonexistent_directory(self, sample_settings, temp_dir):
        """Test finding files when directory doesn't exist."""
        sample_settings.input_directory = str(temp_dir / "nonexistent")
        use_case = ProcessFilesUseCase(sample_settings)
        
        files = use_case.find_input_files()
        
        assert files == []
        assert Path(sample_settings.input_directory).exists()

    def test_find_input_files_with_csv_files(self, sample_settings, temp_dir):
        """Test finding CSV files."""
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        sample_settings.input_directory = str(input_dir)
        
        # Create test files
        (input_dir / "test1.csv").touch()
        (input_dir / "test2.csv").touch()
        (input_dir / "not_supported.txt").touch()
        
        use_case = ProcessFilesUseCase(sample_settings)
        files = use_case.find_input_files()
        
        assert len(files) == 2
        assert all(f.endswith('.csv') for f in files)
        assert str(input_dir / "test1.csv") in files
        assert str(input_dir / "test2.csv") in files

    def test_find_input_files_with_excel_files(self, sample_settings, temp_dir):
        """Test finding Excel files."""
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        sample_settings.input_directory = str(input_dir)
        
        # Create test files
        (input_dir / "test1.xlsx").touch()
        (input_dir / "test2.xls").touch()
        (input_dir / "test3.csv").touch()
        
        use_case = ProcessFilesUseCase(sample_settings)
        files = use_case.find_input_files()
        
        assert len(files) == 3
        assert any(f.endswith('.xlsx') for f in files)
        assert any(f.endswith('.xls') for f in files)
        assert any(f.endswith('.csv') for f in files)

    def test_find_input_files_sorted_order(self, sample_settings, temp_dir):
        """Test that files are returned in sorted order."""
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        sample_settings.input_directory = str(input_dir)
        
        # Create files in non-alphabetical order
        (input_dir / "c_file.csv").touch()
        (input_dir / "a_file.csv").touch()
        (input_dir / "b_file.csv").touch()
        
        use_case = ProcessFilesUseCase(sample_settings)
        files = use_case.find_input_files()
        
        assert len(files) == 3
        # Check if sorted (compare just filenames)
        filenames = [Path(f).name for f in files]
        assert filenames == sorted(filenames)


class TestMoveFileToProcessed:
    """Test move_file_to_processed method."""

    def test_move_file_to_processed_success(self, sample_settings, temp_dir):
        """Test successful file move."""
        # Setup directories
        input_dir = temp_dir / "input"
        processed_dir = temp_dir / "processed"
        input_dir.mkdir()
        
        sample_settings.processed_directory = str(processed_dir)
        
        # Create source file
        source_file = input_dir / "test.csv"
        source_file.write_text("test content")
        
        use_case = ProcessFilesUseCase(sample_settings)
        use_case.move_file_to_processed(str(source_file))
        
        # Verify file moved
        assert not source_file.exists()
        assert (processed_dir / "test.csv").exists()
        assert (processed_dir / "test.csv").read_text() == "test content"

    def test_move_file_creates_processed_directory(self, sample_settings, temp_dir):
        """Test that processed directory is created if it doesn't exist."""
        input_dir = temp_dir / "input"
        processed_dir = temp_dir / "processed"
        input_dir.mkdir()
        
        sample_settings.processed_directory = str(processed_dir)
        
        source_file = input_dir / "test.csv"
        source_file.write_text("test content")
        
        # Ensure processed directory doesn't exist
        assert not processed_dir.exists()
        
        use_case = ProcessFilesUseCase(sample_settings)
        use_case.move_file_to_processed(str(source_file))
        
        # Verify directory created and file moved
        assert processed_dir.exists()
        assert (processed_dir / "test.csv").exists()

    def test_move_file_handles_duplicate_names(self, sample_settings, temp_dir):
        """Test moving file when destination already exists - creates timestamped file."""
        input_dir = temp_dir / "input"
        processed_dir = temp_dir / "processed"
        input_dir.mkdir()
        processed_dir.mkdir()
        
        sample_settings.processed_directory = str(processed_dir)
        
        # Create source and existing destination
        source_file = input_dir / "test.csv"
        dest_file = processed_dir / "test.csv"
        source_file.write_text("new content")
        dest_file.write_text("old content")
        
        use_case = ProcessFilesUseCase(sample_settings)
        use_case.move_file_to_processed(str(source_file))
        
        # Verify source file was moved
        assert not source_file.exists()
        
        # Verify original destination file is preserved
        assert dest_file.exists()
        assert dest_file.read_text() == "old content"
        
        # Verify new file was created with timestamp
        timestamped_files = list(processed_dir.glob("test_*.csv"))
        assert len(timestamped_files) == 1
        assert timestamped_files[0].read_text() == "new content"


class TestProcessSingleFile:
    """Test process_single_file method."""

    @patch('src.application.use_cases.process_files.JiraClient')
    @patch('src.application.use_cases.process_files.FileProcessor')
    def test_process_single_file_success(self, mock_file_processor, mock_jira_client, sample_settings):
        """Test successful single file processing."""
        # Setup mocks
        mock_fp_instance = Mock()
        mock_fp_instance.process_file.return_value = [
            UserStory(titulo="Test 1", descripcion="Desc 1", criterio_aceptacion="Crit 1"),
            UserStory(titulo="Test 2", descripcion="Desc 2", criterio_aceptacion="Crit 2")
        ]
        mock_file_processor.return_value = mock_fp_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.create_user_story.side_effect = [
            ProcessResult(success=True, jira_key="PROJ-1", row_number=1),
            ProcessResult(success=True, jira_key="PROJ-2", row_number=2)
        ]
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        result = use_case.process_single_file("test.csv")
        
        assert isinstance(result, BatchResult)
        assert result.total_processed == 2
        assert result.successful == 2
        assert result.failed == 0
        assert len(result.results) == 2

    @patch('src.application.use_cases.process_files.JiraClient')
    @patch('src.application.use_cases.process_files.FileProcessor')
    def test_process_single_file_with_failures(self, mock_file_processor, mock_jira_client, sample_settings):
        """Test single file processing with some failures."""
        # Setup mocks
        mock_fp_instance = Mock()
        mock_fp_instance.process_file.return_value = [
            UserStory(titulo="Test 1", descripcion="Desc 1", criterio_aceptacion="Crit 1"),
            UserStory(titulo="Test 2", descripcion="Desc 2", criterio_aceptacion="Crit 2")
        ]
        mock_file_processor.return_value = mock_fp_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.create_user_story.side_effect = [
            ProcessResult(success=True, jira_key="PROJ-1", row_number=1),
            ProcessResult(success=False, error_message="Error", row_number=2)
        ]
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        result = use_case.process_single_file("test.csv")
        
        assert result.total_processed == 2
        assert result.successful == 1
        assert result.failed == 1

    @patch('src.application.use_cases.process_files.JiraClient')
    @patch('src.application.use_cases.process_files.FileProcessor')
    def test_process_single_file_validation_error(self, mock_file_processor, mock_jira_client, sample_settings):
        """Test single file processing with validation error."""
        mock_fp_instance = Mock()
        mock_fp_instance.process_file.side_effect = ValueError("Invalid file format")
        mock_file_processor.return_value = mock_fp_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        
        with pytest.raises(ValueError):
            use_case.process_single_file("invalid.csv")

    @patch('src.application.use_cases.process_files.JiraClient')
    @patch('src.application.use_cases.process_files.FileProcessor')
    def test_process_single_file_batch_processing(self, mock_file_processor, mock_jira_client, sample_settings):
        """Test single file processing with batch size."""
        sample_settings.batch_size = 2
        
        # Create 5 stories to test batching
        stories = [
            UserStory(titulo=f"Test {i}", descripcion=f"Desc {i}", criterio_aceptacion=f"Crit {i}")
            for i in range(1, 6)
        ]
        
        mock_fp_instance = Mock()
        mock_fp_instance.process_file.return_value = stories
        mock_file_processor.return_value = mock_fp_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.create_user_story.return_value = ProcessResult(success=True, jira_key="PROJ-X")
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        result = use_case.process_single_file("test.csv")
        
        assert result.total_processed == 5
        # Verify create_user_story was called 5 times (once for each story)
        assert mock_jc_instance.create_user_story.call_count == 5


class TestProcessFiles:
    """Test main execute method."""

    @patch('src.application.use_cases.process_files.JiraClient')
    def test_execute_no_files(self, mock_jira_client, sample_settings):
        """Test processing when no files are provided."""
        mock_jc_instance = Mock()
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        result = use_case.execute([])
        
        assert result['total_files'] == 0
        assert result['file_results'] == []
        assert result['overall_result'] is None

    @patch('src.application.use_cases.process_files.JiraClient')
    def test_execute_single_file_mode(self, mock_jira_client, sample_settings, temp_dir):
        """Test processing specific file."""
        # Setup file
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        test_file = input_dir / "test.csv"
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        # Setup mocks
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_subtask_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.create_user_story.return_value = ProcessResult(success=True, jira_key="PROJ-1")
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        result = use_case.execute([str(test_file)])
        
        assert result['total_files'] == 1
        assert len(result['file_results']) == 1
        assert result['overall_result'] is not None
        assert result['overall_result'].total_processed > 0


class TestDryRunMode:
    """Test dry run functionality."""

    @patch('src.application.use_cases.process_files.JiraClient')
    def test_dry_run_mode_no_validations(self, mock_jira_client, sample_settings, temp_dir):
        """Test that validations are skipped in dry run mode."""
        sample_settings.dry_run = True
        
        # Setup file
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        sample_settings.input_directory = str(input_dir)
        
        test_file = input_dir / "test.csv"
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        # Setup mocks - connections will fail but should be ignored in dry run
        mock_jc_instance = Mock()
        mock_jc_instance.create_user_story.return_value = ProcessResult(success=True, jira_key="DRY-RUN-123")
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        result = use_case.execute([str(test_file)])
        
        # Should succeed even without Jira validations
        assert result['total_files'] == 1
        assert result['overall_result'] is not None
        
        # Verify that no validation methods were called in dry run
        mock_jc_instance.test_connection.assert_not_called()
        mock_jc_instance.validate_project.assert_not_called()
        mock_jc_instance.validate_subtask_issue_type.assert_not_called()
        mock_jc_instance.validate_feature_issue_type.assert_not_called()


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch('src.application.use_cases.process_files.JiraClient')
    def test_execute_jira_connection_error(self, mock_jira_client, sample_settings, temp_dir):
        """Test handling of Jira connection errors."""
        # Setup file
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        test_file = input_dir / "test.csv"
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = False
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        
        with pytest.raises(Exception, match="No se pudo conectar a Jira"):
            use_case.execute([str(test_file)])

    @patch('src.application.use_cases.process_files.JiraClient')
    def test_execute_project_validation_error(self, mock_jira_client, sample_settings, temp_dir):
        """Test handling of project validation errors."""
        # Setup file
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        test_file = input_dir / "test.csv"
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = False
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        
        with pytest.raises(Exception, match="Proyecto.*no encontrado"):
            use_case.execute([str(test_file)])

    @patch('src.application.use_cases.process_files.JiraClient')
    def test_execute_subtask_validation_error(self, mock_jira_client, sample_settings, temp_dir):
        """Test handling of subtask type validation errors."""
        # Setup file with subtasks
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        test_file = input_dir / "test.csv"
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_subtask_issue_type.return_value = False
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        
        with pytest.raises(Exception, match="Tipo de subtarea.*no válido"):
            use_case.execute([str(test_file)])

    @patch('src.application.use_cases.process_files.JiraClient')
    def test_execute_feature_validation_error(self, mock_jira_client, sample_settings, temp_dir):
        """Test handling of feature type validation errors."""
        # Setup file with parents
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        test_file = input_dir / "test.csv"
        create_sample_csv(SAMPLE_STORIES, str(test_file))
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_subtask_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = False
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        
        with pytest.raises(Exception, match="Tipo de feature.*no válido"):
            use_case.execute([str(test_file)])

    @patch('src.application.use_cases.process_files.JiraClient')
    @patch('src.application.use_cases.process_files.FileProcessor')
    def test_execute_file_processing_error(self, mock_file_processor, mock_jira_client, sample_settings):
        """Test handling of file processing errors."""
        # Setup mocks so validation passes but file processing fails
        mock_fp_instance = Mock()
        mock_fp_instance.process_file.side_effect = [
            [],  # Empty list for validation checks (subtasks)
            [],  # Empty list for validation checks (parents)
            FileNotFoundError("El archivo nonexistent.csv no existe")  # Error during actual processing
        ]
        mock_file_processor.return_value = mock_fp_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_subtask_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        
        # Test with non-existent file
        result = use_case.execute(["nonexistent.csv"])
        
        # Should handle error gracefully and return error info
        assert result['total_files'] == 1
        assert len(result['file_results']) == 1
        assert 'error' in result['file_results'][0]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch('src.application.use_cases.process_files.JiraClient')
    @patch('src.application.use_cases.process_files.FileProcessor')
    def test_execute_all_stories_fail(self, mock_file_processor, mock_jira_client, sample_settings):
        """Test processing when all stories fail."""
        # Setup mocks
        mock_fp_instance = Mock()
        mock_fp_instance.process_file.return_value = [
            UserStory(titulo="Test 1", descripcion="Desc 1", criterio_aceptacion="Crit 1")
        ]
        mock_file_processor.return_value = mock_fp_instance
        
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_subtask_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.create_user_story.return_value = ProcessResult(
            success=False, 
            error_message="All failed", 
            row_number=1
        )
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        result = use_case.process_single_file("test.csv")
        
        assert result.total_processed == 1
        assert result.successful == 0
        assert result.failed == 1

    @patch('src.application.use_cases.process_files.JiraClient')
    def test_execute_large_batch_size(self, mock_jira_client, sample_settings):
        """Test processing with very large batch size."""
        sample_settings.batch_size = 1000  # Very large batch
        
        mock_jc_instance = Mock()
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        
        # Should not raise any errors
        assert use_case.settings.batch_size == 1000

    @patch('src.application.use_cases.process_files.JiraClient')
    def test_execute_multiple_files(self, mock_jira_client, sample_settings, temp_dir):
        """Test processing multiple files."""
        # Setup files
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        file1 = input_dir / "test1.csv"
        file2 = input_dir / "test2.csv"
        create_sample_csv(SAMPLE_STORIES[:1], str(file1))  # 1 story
        create_sample_csv(SAMPLE_STORIES[1:], str(file2))  # 2 stories
        
        # Setup mocks
        mock_jc_instance = Mock()
        mock_jc_instance.test_connection.return_value = True
        mock_jc_instance.validate_project.return_value = True
        mock_jc_instance.validate_subtask_issue_type.return_value = True
        mock_jc_instance.validate_feature_issue_type.return_value = True
        mock_jc_instance.create_user_story.return_value = ProcessResult(success=True, jira_key="PROJ-X")
        mock_jira_client.return_value = mock_jc_instance
        
        use_case = ProcessFilesUseCase(sample_settings)
        result = use_case.execute([str(file1), str(file2)])
        
        assert result['total_files'] == 2
        assert len(result['file_results']) == 2
        assert result['overall_result'] is not None
        assert result['overall_result'].total_processed == 3  # 1 + 2 stories