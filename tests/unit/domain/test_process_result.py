"""Tests for ProcessResult entity."""
import pytest

from src.domain.entities.process_result import ProcessResult
from src.domain.entities.feature_result import FeatureResult


class TestProcessResultValidation:
    """Test ProcessResult validation and creation."""

    def test_successful_result_minimal(self):
        """Test creating a minimal successful result."""
        result = ProcessResult(success=True)
        
        assert result.success is True
        assert result.jira_key is None
        assert result.error_message is None
        assert result.row_number is None
        assert result.subtasks_created == 0
        assert result.subtasks_failed == 0
        assert result.subtask_errors is None
        assert result.feature_info is None

    def test_successful_result_complete(self):
        """Test creating a complete successful result."""
        feature_info = FeatureResult(
            feature_key="PROJ-200",
            was_created=True,
            original_text="New Feature"
        )
        
        result = ProcessResult(
            success=True,
            jira_key="PROJ-123",
            row_number=5,
            subtasks_created=3,
            subtasks_failed=1,
            subtask_errors=["Error in subtask 4"],
            feature_info=feature_info
        )
        
        assert result.success is True
        assert result.jira_key == "PROJ-123"
        assert result.row_number == 5
        assert result.subtasks_created == 3
        assert result.subtasks_failed == 1
        assert len(result.subtask_errors) == 1
        assert result.feature_info.feature_key == "PROJ-200"

    def test_failed_result_minimal(self):
        """Test creating a minimal failed result."""
        result = ProcessResult(
            success=False,
            error_message="Something went wrong"
        )
        
        assert result.success is False
        assert result.error_message == "Something went wrong"
        assert result.jira_key is None
        assert result.subtasks_created == 0
        assert result.subtasks_failed == 0

    def test_failed_result_with_row(self):
        """Test creating a failed result with row information."""
        result = ProcessResult(
            success=False,
            error_message="Validation failed",
            row_number=10,
            subtasks_failed=2,
            subtask_errors=["Error 1", "Error 2"]
        )
        
        assert result.success is False
        assert result.error_message == "Validation failed"
        assert result.row_number == 10
        assert result.subtasks_failed == 2
        assert len(result.subtask_errors) == 2


class TestProcessResultSubtasks:
    """Test subtask-related functionality."""

    def test_no_subtasks(self):
        """Test result with no subtasks."""
        result = ProcessResult(success=True, jira_key="PROJ-123")
        
        assert result.subtasks_created == 0
        assert result.subtasks_failed == 0
        assert result.subtask_errors is None

    def test_all_subtasks_successful(self):
        """Test result with all subtasks successful."""
        result = ProcessResult(
            success=True,
            jira_key="PROJ-123",
            subtasks_created=5,
            subtasks_failed=0
        )
        
        assert result.subtasks_created == 5
        assert result.subtasks_failed == 0

    def test_mixed_subtask_results(self):
        """Test result with mixed subtask outcomes."""
        result = ProcessResult(
            success=True,
            jira_key="PROJ-123", 
            subtasks_created=3,
            subtasks_failed=2,
            subtask_errors=["Error in subtask 1", "Error in subtask 2"]
        )
        
        assert result.subtasks_created == 3
        assert result.subtasks_failed == 2
        assert len(result.subtask_errors) == 2

    def test_all_subtasks_failed(self):
        """Test result with all subtasks failed."""
        result = ProcessResult(
            success=False,  # Story might be deleted due to rollback
            subtasks_created=0,
            subtasks_failed=4,
            subtask_errors=["Error 1", "Error 2", "Error 3", "Error 4"],
            error_message="All subtasks failed, story rolled back"
        )
        
        assert result.subtasks_created == 0
        assert result.subtasks_failed == 4
        assert len(result.subtask_errors) == 4
        assert "rolled back" in result.error_message

    def test_subtask_counts_consistency(self):
        """Test that subtask counts are consistent."""
        # Test various combinations to ensure they make sense
        combinations = [
            (0, 0),  # No subtasks
            (5, 0),  # All successful
            (0, 3),  # All failed
            (2, 1),  # Mixed
        ]
        
        for created, failed in combinations:
            result = ProcessResult(
                success=True,
                subtasks_created=created,
                subtasks_failed=failed
            )
            
            assert result.subtasks_created == created
            assert result.subtasks_failed == failed
            assert result.subtasks_created >= 0
            assert result.subtasks_failed >= 0


class TestProcessResultFeatureInfo:
    """Test feature information in results."""

    def test_result_with_new_feature(self):
        """Test result with newly created feature."""
        feature_info = FeatureResult(
            feature_key="PROJ-200",
            was_created=True,
            original_text="Sistema de Autenticación"
        )
        
        result = ProcessResult(
            success=True,
            jira_key="PROJ-123",
            feature_info=feature_info
        )
        
        assert result.feature_info is not None
        assert result.feature_info.was_created is True
        assert result.feature_info.feature_key == "PROJ-200"

    def test_result_with_existing_feature(self):
        """Test result with existing feature."""
        feature_info = FeatureResult(
            feature_key="PROJ-100", 
            was_created=False,
            original_text="PROJ-100"
        )
        
        result = ProcessResult(
            success=True,
            jira_key="PROJ-123", 
            feature_info=feature_info
        )
        
        assert result.feature_info is not None
        assert result.feature_info.was_created is False
        assert result.feature_info.feature_key == "PROJ-100"

    def test_result_without_feature(self):
        """Test result without feature information."""
        result = ProcessResult(
            success=True,
            jira_key="PROJ-123"
        )
        
        assert result.feature_info is None


class TestProcessResultSerialization:
    """Test ProcessResult serialization."""

    def test_result_serialization(self):
        """Test result can be serialized to dict."""
        feature_info = FeatureResult(
            feature_key="PROJ-200",
            was_created=True, 
            original_text="New Feature"
        )
        
        result = ProcessResult(
            success=True,
            jira_key="PROJ-123",
            row_number=5,
            subtasks_created=2,
            subtasks_failed=1,
            subtask_errors=["Subtask error"],
            feature_info=feature_info
        )
        
        result_dict = result.model_dump()
        
        assert result_dict["success"] is True
        assert result_dict["jira_key"] == "PROJ-123"
        assert result_dict["subtasks_created"] == 2
        assert result_dict["feature_info"]["was_created"] is True

    def test_result_from_dict(self):
        """Test creating result from dictionary."""
        result_data = {
            "success": True,
            "jira_key": "PROJ-456",
            "row_number": 10,
            "subtasks_created": 3,
            "subtasks_failed": 0,
            "feature_info": {
                "feature_key": "PROJ-300",
                "was_created": False,
                "original_text": "PROJ-300"
            }
        }
        
        result = ProcessResult(**result_data)
        
        assert result.success is True
        assert result.jira_key == "PROJ-456"
        assert result.feature_info.feature_key == "PROJ-300"
        assert result.feature_info.was_created is False


class TestProcessResultEdgeCases:
    """Test edge cases and error conditions."""

    def test_negative_subtask_counts(self):
        """Test that negative subtask counts work (should be allowed)."""
        # Pydantic doesn't validate negative numbers by default
        result = ProcessResult(
            success=True,
            subtasks_created=-1,  # This might happen in edge cases
            subtasks_failed=0
        )
        
        # The model should accept this, business logic should handle validation
        assert result.subtasks_created == -1

    def test_large_subtask_counts(self):
        """Test with large subtask counts."""
        result = ProcessResult(
            success=True,
            subtasks_created=1000,
            subtasks_failed=500
        )
        
        assert result.subtasks_created == 1000
        assert result.subtasks_failed == 500

    def test_empty_error_list(self):
        """Test with empty error list."""
        result = ProcessResult(
            success=False,
            error_message="Failed", 
            subtask_errors=[]
        )
        
        assert result.subtask_errors == []

    def test_none_vs_empty_error_list(self):
        """Test difference between None and empty error list."""
        result_none = ProcessResult(success=True, subtask_errors=None)
        result_empty = ProcessResult(success=True, subtask_errors=[])
        
        assert result_none.subtask_errors is None
        assert result_empty.subtask_errors == []