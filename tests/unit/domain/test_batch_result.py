"""Tests for BatchResult entity."""
import pytest

from src.domain.entities.batch_result import BatchResult
from src.domain.entities.process_result import ProcessResult
from src.domain.entities.feature_result import FeatureResult


class TestBatchResultValidation:
    """Test BatchResult validation and creation."""

    def test_empty_batch_result(self):
        """Test creating an empty batch result."""
        result = BatchResult(
            total_processed=0,
            successful=0,
            failed=0,
            results=[]
        )
        
        assert result.total_processed == 0
        assert result.successful == 0
        assert result.failed == 0
        assert len(result.results) == 0

    def test_batch_result_with_results(self):
        """Test creating batch result with actual results."""
        results = [
            ProcessResult(success=True, jira_key="PROJ-1"),
            ProcessResult(success=True, jira_key="PROJ-2"),
            ProcessResult(success=False, error_message="Error in row 3")
        ]
        
        batch = BatchResult(
            total_processed=3,
            successful=2,
            failed=1,
            results=results
        )
        
        assert batch.total_processed == 3
        assert batch.successful == 2
        assert batch.failed == 1
        assert len(batch.results) == 3

    def test_all_successful_batch(self):
        """Test batch with all successful results."""
        results = [
            ProcessResult(success=True, jira_key="PROJ-1"),
            ProcessResult(success=True, jira_key="PROJ-2"),
            ProcessResult(success=True, jira_key="PROJ-3")
        ]
        
        batch = BatchResult(
            total_processed=3,
            successful=3,
            failed=0,
            results=results
        )
        
        assert batch.total_processed == 3
        assert batch.successful == 3
        assert batch.failed == 0
        assert all(r.success for r in batch.results)

    def test_all_failed_batch(self):
        """Test batch with all failed results."""
        results = [
            ProcessResult(success=False, error_message="Error 1"),
            ProcessResult(success=False, error_message="Error 2"),
            ProcessResult(success=False, error_message="Error 3")
        ]
        
        batch = BatchResult(
            total_processed=3,
            successful=0,
            failed=3,
            results=results
        )
        
        assert batch.total_processed == 3
        assert batch.successful == 0
        assert batch.failed == 3
        assert all(not r.success for r in batch.results)


class TestBatchResultConsistency:
    """Test consistency rules for BatchResult."""

    def test_totals_match_results_count(self):
        """Test that total_processed matches results count."""
        results = [
            ProcessResult(success=True, jira_key="PROJ-1"),
            ProcessResult(success=False, error_message="Error")
        ]
        
        batch = BatchResult(
            total_processed=2,
            successful=1,
            failed=1,
            results=results
        )
        
        assert batch.total_processed == len(batch.results)

    def test_successful_plus_failed_equals_total(self):
        """Test that successful + failed = total_processed."""
        batch = BatchResult(
            total_processed=10,
            successful=7,
            failed=3,
            results=[]  # Empty for simplicity
        )
        
        assert batch.successful + batch.failed == batch.total_processed

    def test_success_count_matches_actual_successes(self):
        """Test that successful count matches actual successful results."""
        results = [
            ProcessResult(success=True, jira_key="PROJ-1"),
            ProcessResult(success=True, jira_key="PROJ-2"), 
            ProcessResult(success=False, error_message="Error"),
            ProcessResult(success=True, jira_key="PROJ-3")
        ]
        
        actual_successes = sum(1 for r in results if r.success)
        actual_failures = sum(1 for r in results if not r.success)
        
        batch = BatchResult(
            total_processed=len(results),
            successful=actual_successes,
            failed=actual_failures,
            results=results
        )
        
        assert batch.successful == actual_successes
        assert batch.failed == actual_failures
        assert batch.total_processed == len(results)

    def test_inconsistent_counts_still_allowed(self):
        """Test that model allows inconsistent counts (validation is business logic)."""
        # Model should allow this - business logic should validate
        results = [ProcessResult(success=True, jira_key="PROJ-1")]
        
        batch = BatchResult(
            total_processed=5,  # Inconsistent with results count
            successful=3,       # Inconsistent with actual successes
            failed=2,          # Inconsistent with actual failures
            results=results
        )
        
        # Model creation should succeed
        assert batch.total_processed == 5
        assert batch.successful == 3
        assert batch.failed == 2
        assert len(batch.results) == 1


class TestBatchResultWithComplexResults:
    """Test BatchResult with complex ProcessResult scenarios."""

    def test_batch_with_subtasks(self):
        """Test batch containing results with subtasks."""
        results = [
            ProcessResult(
                success=True,
                jira_key="PROJ-1",
                subtasks_created=3,
                subtasks_failed=0
            ),
            ProcessResult(
                success=True,
                jira_key="PROJ-2",
                subtasks_created=2,
                subtasks_failed=1,
                subtask_errors=["Subtask error"]
            ),
            ProcessResult(
                success=False,
                error_message="Story creation failed",
                subtasks_created=0,
                subtasks_failed=2
            )
        ]
        
        batch = BatchResult(
            total_processed=3,
            successful=2,
            failed=1,
            results=results
        )
        
        # Calculate totals across all results
        total_subtasks_created = sum(r.subtasks_created for r in batch.results)
        total_subtasks_failed = sum(r.subtasks_failed for r in batch.results)
        
        assert total_subtasks_created == 5  # 3 + 2 + 0
        assert total_subtasks_failed == 3   # 0 + 1 + 2

    def test_batch_with_features(self):
        """Test batch containing results with feature information."""
        feature_info_1 = FeatureResult(
            feature_key="PROJ-100",
            was_created=True,
            original_text="New Feature 1"
        )
        
        feature_info_2 = FeatureResult(
            feature_key="PROJ-50",
            was_created=False,
            original_text="PROJ-50"
        )
        
        results = [
            ProcessResult(
                success=True,
                jira_key="PROJ-1", 
                feature_info=feature_info_1
            ),
            ProcessResult(
                success=True,
                jira_key="PROJ-2",
                feature_info=feature_info_2
            ),
            ProcessResult(
                success=True,
                jira_key="PROJ-3"  # No feature info
            )
        ]
        
        batch = BatchResult(
            total_processed=3,
            successful=3,
            failed=0,
            results=results
        )
        
        # Count results with features
        results_with_features = sum(1 for r in batch.results if r.feature_info is not None)
        new_features_created = sum(1 for r in batch.results 
                                 if r.feature_info and r.feature_info.was_created)
        
        assert results_with_features == 2
        assert new_features_created == 1

    def test_batch_with_row_numbers(self):
        """Test batch with row number tracking."""
        results = [
            ProcessResult(success=True, jira_key="PROJ-1", row_number=2),
            ProcessResult(success=False, error_message="Error", row_number=5),
            ProcessResult(success=True, jira_key="PROJ-2", row_number=7),
        ]
        
        batch = BatchResult(
            total_processed=3,
            successful=2,
            failed=1,
            results=results
        )
        
        # Find failed row numbers
        failed_rows = [r.row_number for r in batch.results if not r.success]
        successful_rows = [r.row_number for r in batch.results if r.success]
        
        assert failed_rows == [5]
        assert successful_rows == [2, 7]


class TestBatchResultSerialization:
    """Test BatchResult serialization."""

    def test_batch_serialization(self):
        """Test batch can be serialized to dict."""
        results = [
            ProcessResult(success=True, jira_key="PROJ-1"),
            ProcessResult(success=False, error_message="Error")
        ]
        
        batch = BatchResult(
            total_processed=2,
            successful=1, 
            failed=1,
            results=results
        )
        
        batch_dict = batch.model_dump()
        
        assert batch_dict["total_processed"] == 2
        assert batch_dict["successful"] == 1
        assert batch_dict["failed"] == 1
        assert len(batch_dict["results"]) == 2
        assert batch_dict["results"][0]["success"] is True
        assert batch_dict["results"][1]["success"] is False

    def test_batch_from_dict(self):
        """Test creating batch from dictionary."""
        batch_data = {
            "total_processed": 2,
            "successful": 1,
            "failed": 1,
            "results": [
                {"success": True, "jira_key": "PROJ-1"},
                {"success": False, "error_message": "Error"}
            ]
        }
        
        batch = BatchResult(**batch_data)
        
        assert batch.total_processed == 2
        assert batch.successful == 1
        assert batch.failed == 1
        assert len(batch.results) == 2
        assert batch.results[0].success is True
        assert batch.results[1].success is False


class TestBatchResultEdgeCases:
    """Test edge cases for BatchResult."""

    def test_large_batch(self):
        """Test batch with large number of results."""
        # Create 1000 results
        results = [
            ProcessResult(success=True, jira_key=f"PROJ-{i}")
            for i in range(1000)
        ]
        
        batch = BatchResult(
            total_processed=1000,
            successful=1000,
            failed=0,
            results=results
        )
        
        assert batch.total_processed == 1000
        assert len(batch.results) == 1000
        assert all(r.success for r in batch.results)

    def test_batch_with_zero_totals(self):
        """Test batch with zero counts but non-empty results."""
        # Edge case that might occur in error conditions
        results = [ProcessResult(success=True, jira_key="PROJ-1")]
        
        batch = BatchResult(
            total_processed=0,  # Inconsistent but allowed
            successful=0,
            failed=0,
            results=results
        )
        
        assert batch.total_processed == 0
        assert len(batch.results) == 1

    def test_negative_counts(self):
        """Test batch with negative counts."""
        # Edge case - model should allow, business logic should validate
        batch = BatchResult(
            total_processed=-1,
            successful=-1,
            failed=0,
            results=[]
        )
        
        assert batch.total_processed == -1
        assert batch.successful == -1