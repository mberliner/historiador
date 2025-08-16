"""Tests for OutputFormatter."""
import pytest
import io
import contextlib
from unittest.mock import Mock, patch

from src.presentation.formatters.output_formatter import OutputFormatter
from src.domain.entities.batch_result import BatchResult
from src.domain.entities.process_result import ProcessResult
from src.domain.entities.feature_result import FeatureResult


class TestOutputFormatter:
    """Test OutputFormatter basic methods."""

    def test_init(self):
        """Test formatter initialization."""
        formatter = OutputFormatter()
        assert formatter is not None

    def test_print_error(self):
        """Test error message printing."""
        formatter = OutputFormatter()
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_error("Test error message")
            
            mock_echo.assert_called_once_with("[ERROR] Test error message", err=True)

    def test_print_success(self):
        """Test success message printing."""
        formatter = OutputFormatter()
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_success("Test success message")
            
            mock_echo.assert_called_once_with("[OK] Test success message")

    def test_print_warning(self):
        """Test warning message printing."""
        formatter = OutputFormatter()
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_warning("Test warning message")
            
            mock_echo.assert_called_once_with("[WARNING] Test warning message")

    def test_print_info(self):
        """Test info message printing."""
        formatter = OutputFormatter()
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_info("Test info message")
            
            mock_echo.assert_called_once_with("Test info message")


class TestFileHeaderPrinting:
    """Test file header printing methods."""

    def test_print_file_header(self):
        """Test file header printing."""
        formatter = OutputFormatter()
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_file_header(1, 3, "test_file.csv")
            
            expected_calls = [
                (("\n" + "="*60,), {}),
                (("PROCESANDO ARCHIVO 1/3: test_file.csv",), {}),
                (("="*60,), {})
            ]
            
            assert mock_echo.call_count == 3
            actual_calls = mock_echo.call_args_list
            for i, (expected_call, actual_call) in enumerate(zip(expected_calls, actual_calls)):
                assert actual_call[0] == expected_call[0], f"Call {i+1} args mismatch"

    def test_print_file_header_different_values(self):
        """Test file header with different values."""
        formatter = OutputFormatter()
        
        test_cases = [
            (1, 1, "single.xlsx"),
            (5, 10, "large_batch.csv"),
            (99, 100, "almost_done.xlsx")
        ]
        
        for file_index, total_files, file_name in test_cases:
            with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
                formatter.print_file_header(file_index, total_files, file_name)
                
                # Check that the file info is in one of the calls
                calls_text = " ".join([str(call[0][0]) for call in mock_echo.call_args_list])
                assert f"ARCHIVO {file_index}/{total_files}: {file_name}" in calls_text


class TestStoryResultPrinting:
    """Test story result printing methods."""

    def test_print_story_result_success_basic(self):
        """Test printing successful story result."""
        formatter = OutputFormatter()
        
        result = ProcessResult(
            success=True,
            jira_key="TEST-123",
            row_number=1,
            subtasks_created=0,
            subtasks_failed=0
        )
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_story_result(result, "Test Story Title")
            
            mock_echo.assert_called_once_with("[OK] Fila 1: TEST-123 - Test Story Title")

    def test_print_story_result_success_with_feature_created(self):
        """Test printing successful result with created feature."""
        formatter = OutputFormatter()
        
        feature_info = FeatureResult(
            feature_key="TEST-100",
            was_created=True,
            original_text="New Feature Description"
        )
        
        result = ProcessResult(
            success=True,
            jira_key="TEST-123",
            row_number=2,
            subtasks_created=0,
            subtasks_failed=0,
            feature_info=feature_info
        )
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_story_result(result, "Test Story with Feature")
            
            assert mock_echo.call_count == 2
            calls = [call[0][0] for call in mock_echo.call_args_list]
            assert "[OK] Fila 2: TEST-123 - Test Story with Feature" in calls
            assert "    + Feature creada: TEST-100" in calls

    def test_print_story_result_success_with_existing_parent(self):
        """Test printing successful result with existing parent."""
        formatter = OutputFormatter()
        
        feature_info = FeatureResult(
            feature_key="TEST-EXISTING",
            was_created=False,
            original_text="TEST-EXISTING"
        )
        
        result = ProcessResult(
            success=True,
            jira_key="TEST-123",
            row_number=3,
            subtasks_created=0,
            subtasks_failed=0,
            feature_info=feature_info
        )
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_story_result(result, "Test Story with Parent")
            
            assert mock_echo.call_count == 2
            calls = [call[0][0] for call in mock_echo.call_args_list]
            assert "[OK] Fila 3: TEST-123 - Test Story with Parent" in calls
            assert "    = Parent utilizado: TEST-EXISTING" in calls

    def test_print_story_result_success_with_subtasks(self):
        """Test printing successful result with subtasks."""
        formatter = OutputFormatter()
        
        result = ProcessResult(
            success=True,
            jira_key="TEST-123",
            row_number=4,
            subtasks_created=3,
            subtasks_failed=1
        )
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_story_result(result, "Test Story with Subtasks")
            
            assert mock_echo.call_count == 3
            calls = [call[0][0] for call in mock_echo.call_args_list]
            assert "[OK] Fila 4: TEST-123 - Test Story with Subtasks" in calls
            assert "    + 3 subtarea(s) creada(s)" in calls
            
            # Check that failed subtasks are printed with err=True
            failed_call = None
            for call in mock_echo.call_args_list:
                if "subtarea(s) fallaron" in str(call[0][0]):
                    failed_call = call
                    break
            
            assert failed_call is not None
            assert failed_call[1].get('err') is True

    def test_print_story_result_failure(self):
        """Test printing failed story result."""
        formatter = OutputFormatter()
        
        result = ProcessResult(
            success=False,
            error_message="Parent key TEST-999 does not exist",
            row_number=5
        )
        
        with patch.object(formatter, 'print_error') as mock_print_error:
            formatter.print_story_result(result, "Failed Story")
            
            mock_print_error.assert_called_once_with("Fila 5: Parent key TEST-999 does not exist")


class TestBatchSummaryPrinting:
    """Test batch summary printing methods."""

    def test_print_batch_summary(self):
        """Test printing batch summary."""
        formatter = OutputFormatter()
        
        batch_result = BatchResult(
            total_processed=10,
            successful=8,
            failed=2,
            results=[]
        )
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_batch_summary("test_file.csv", batch_result)
            
            expected_calls = [
                "\nRESUMEN DE test_file.csv:",
                "Total procesadas: 10",
                "Exitosas: 8",
                "Fallidas: 2"
            ]
            
            assert mock_echo.call_count == len(expected_calls)
            actual_calls = [call[0][0] for call in mock_echo.call_args_list]
            
            for expected, actual in zip(expected_calls, actual_calls):
                assert actual == expected

    def test_print_batch_errors(self):
        """Test printing batch errors."""
        formatter = OutputFormatter()
        
        results = [
            ProcessResult(success=True, jira_key="TEST-123", row_number=1),
            ProcessResult(success=False, error_message="Error 1", row_number=2),
            ProcessResult(success=False, error_message="Error 2", row_number=3),
            ProcessResult(success=True, jira_key="TEST-124", row_number=4)
        ]
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_batch_errors(results)
            
            expected_calls = [
                "Errores encontrados:",
                "  Fila 2: Error 1",
                "  Fila 3: Error 2"
            ]
            
            assert mock_echo.call_count == len(expected_calls)
            actual_calls = [call[0][0] for call in mock_echo.call_args_list]
            
            for expected, actual in zip(expected_calls, actual_calls):
                assert actual == expected

    def test_print_batch_errors_no_errors(self):
        """Test printing batch errors when no errors exist."""
        formatter = OutputFormatter()
        
        results = [
            ProcessResult(success=True, jira_key="TEST-123", row_number=1),
            ProcessResult(success=True, jira_key="TEST-124", row_number=2)
        ]
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_batch_errors(results)
            
            mock_echo.assert_not_called()

    def test_print_subtask_errors(self):
        """Test printing subtask errors."""
        formatter = OutputFormatter()
        
        results = [
            ProcessResult(
                success=True, 
                jira_key="TEST-123", 
                row_number=1,
                subtask_errors=["Subtask error 1", "Subtask error 2"]
            ),
            ProcessResult(success=True, jira_key="TEST-124", row_number=2),
            ProcessResult(
                success=True, 
                jira_key="TEST-125", 
                row_number=3,
                subtask_errors=["Another subtask error"]
            )
        ]
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_subtask_errors(results)
            
            expected_calls = [
                "Errores de subtareas en fila 1 (TEST-123):",
                "  • Subtask error 1",
                "  • Subtask error 2",
                "Errores de subtareas en fila 3 (TEST-125):",
                "  • Another subtask error"
            ]
            
            assert mock_echo.call_count == len(expected_calls)
            actual_calls = [call[0][0] for call in mock_echo.call_args_list]
            
            for expected, actual in zip(expected_calls, actual_calls):
                assert actual == expected

    def test_print_general_summary(self):
        """Test printing general summary."""
        formatter = OutputFormatter()
        
        overall_result = BatchResult(
            total_processed=25,
            successful=20,
            failed=5,
            results=[]
        )
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            formatter.print_general_summary(3, overall_result)
            
            expected_calls = [
                "\n" + "="*60,
                "RESUMEN GENERAL",
                "="*60,
                "Archivos procesados: 3",
                "Total historias procesadas: 25",
                "Total exitosas: 20",
                "Total fallidas: 5"
            ]
            
            assert mock_echo.call_count == len(expected_calls)
            actual_calls = [call[0][0] for call in mock_echo.call_args_list]
            
            for expected, actual in zip(expected_calls, actual_calls):
                assert actual == expected


class TestSpecializedPrintMethods:
    """Test specialized print methods."""

    def test_print_results_placeholder(self):
        """Test print_results method (currently a placeholder)."""
        formatter = OutputFormatter()
        
        # This method currently just passes, so we test that it doesn't crash
        formatter.print_results({"test": "data"})
        # No assertions needed since it's a placeholder

    def test_print_validation_result(self):
        """Test printing validation result."""
        formatter = OutputFormatter()
        
        result = {
            "file": "test_file.csv",
            "rows": 5,
            "preview": "Sample preview data",
            "total_stories": 10,
            "with_subtasks": 7,
            "total_subtasks": 15,
            "with_parent": 3,
            "invalid_subtasks": 2
        }
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            with patch.object(formatter, 'print_success') as mock_success:
                with patch.object(formatter, 'print_error') as mock_error:
                    formatter.print_validation_result(result)
                    
                    # Check that click.echo was called for headers and info
                    assert mock_echo.call_count > 0
                    
                    # Check success messages
                    expected_success_calls = [
                        "Archivo válido",
                        "10 historias encontradas", 
                        "Todas las filas tienen formato correcto"
                    ]
                    assert mock_success.call_count == len(expected_success_calls)
                    
                    # Check error messages for invalid subtasks
                    expected_error_calls = [
                        "Subtareas inválidas: 2",
                        "(vacías o >255 caracteres)"
                    ]
                    assert mock_error.call_count == len(expected_error_calls)

    def test_print_validation_result_no_invalid_subtasks(self):
        """Test validation result without invalid subtasks."""
        formatter = OutputFormatter()
        
        result = {
            "file": "test_file.csv",
            "rows": 5,
            "preview": "Sample preview data",
            "total_stories": 5,
            "with_subtasks": 3,
            "total_subtasks": 8,
            "with_parent": 2,
            "invalid_subtasks": 0
        }
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            with patch.object(formatter, 'print_success') as mock_success:
                with patch.object(formatter, 'print_error') as mock_error:
                    formatter.print_validation_result(result)
                    
                    # Success messages should be called
                    assert mock_success.call_count == 3
                    
                    # No error messages should be called
                    assert mock_error.call_count == 0

    def test_print_connection_result_success(self):
        """Test printing successful connection result."""
        formatter = OutputFormatter()
        
        result = {
            "connection_success": True,
            "project_valid": True,
            "project_key": "TEST"
        }
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            with patch.object(formatter, 'print_success') as mock_success:
                with patch.object(formatter, 'print_error') as mock_error:
                    formatter.print_connection_result(result)
                    
                    # Check initial message
                    mock_echo.assert_called_once_with("Probando conexión con Jira...")
                    
                    # Check success messages
                    expected_success_calls = [
                        "Conexión exitosa",
                        "Proyecto TEST encontrado"
                    ]
                    assert mock_success.call_count == len(expected_success_calls)
                    assert mock_error.call_count == 0

    def test_print_connection_result_invalid_project(self):
        """Test printing connection result with invalid project."""
        formatter = OutputFormatter()
        
        result = {
            "connection_success": True,
            "project_valid": False,
            "project_key": "INVALID"
        }
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            with patch.object(formatter, 'print_success') as mock_success:
                with patch.object(formatter, 'print_error') as mock_error:
                    formatter.print_connection_result(result)
                    
                    # Check success and error messages
                    mock_success.assert_called_once_with("Conexión exitosa")
                    mock_error.assert_called_once_with("Proyecto INVALID no encontrado")

    def test_print_connection_result_connection_failure(self):
        """Test printing failed connection result."""
        formatter = OutputFormatter()
        
        result = {
            "connection_success": False,
            "project_valid": False,
            "project_key": "TEST"
        }
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            with patch.object(formatter, 'print_success') as mock_success:
                with patch.object(formatter, 'print_error') as mock_error:
                    formatter.print_connection_result(result)
                    
                    # Only error message should be called
                    assert mock_success.call_count == 0
                    mock_error.assert_called_once_with("Error de conexión")

    def test_print_diagnose_result(self):
        """Test printing diagnose result."""
        formatter = OutputFormatter()
        
        result = {
            "project_key": "TEST",
            "feature_type": "Feature",
            "required_fields": {
                "customfield_10001": {"id": "1"},
                "customfield_10002": {"value": "High"}
            },
            "config_suggestion": '{"customfield_10001": {"id": "1"}, "customfield_10002": {"value": "High"}}',
            "current_config": {
                "feature_type": "Feature",
                "required_fields": None
            }
        }
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            with patch.object(formatter, 'print_success') as mock_success:
                formatter.print_diagnose_result(result)
                
                # Check that various sections were printed
                echo_calls = [call[0][0] for call in mock_echo.call_args_list]
                
                # Check headers and sections
                assert any("DIAGNÓSTICO DE CONFIGURACIÓN" in call for call in echo_calls)
                assert any("CAMPOS OBLIGATORIOS ENCONTRADOS" in call for call in echo_calls)
                assert any("CONFIGURACIÓN SUGERIDA" in call for call in echo_calls)
                assert any("CONFIGURACIÓN ACTUAL" in call for call in echo_calls)
                
                # Check success messages
                expected_success_calls = [
                    "Conexión con Jira exitosa",
                    "Proyecto TEST válido",
                    "Tipo de feature 'Feature' válido"
                ]
                assert mock_success.call_count == len(expected_success_calls)

    def test_print_diagnose_result_no_required_fields(self):
        """Test printing diagnose result without required fields."""
        formatter = OutputFormatter()
        
        result = {
            "project_key": "TEST",
            "feature_type": "Feature", 
            "required_fields": {},
            "config_suggestion": "",
            "current_config": {
                "feature_type": "Feature",
                "required_fields": '{"custom": "value"}'
            }
        }
        
        with patch('src.presentation.formatters.output_formatter.click.echo') as mock_echo:
            with patch.object(formatter, 'print_success') as mock_success:
                formatter.print_diagnose_result(result)
                
                # Check success messages including the "no required fields" message
                success_calls = [call[0][0] for call in mock_success.call_args_list]
                assert "No se encontraron campos obligatorios adicionales" in success_calls