"""Tests for FeatureResult entity."""
import pytest

from src.domain.entities.feature_result import FeatureResult


class TestFeatureResultValidation:
    """Test FeatureResult validation and creation."""

    def test_new_feature_creation(self):
        """Test creating result for a newly created feature."""
        result = FeatureResult(
            feature_key="PROJ-200",
            was_created=True,
            original_text="Sistema de Autenticación"
        )
        
        assert result.feature_key == "PROJ-200"
        assert result.was_created is True
        assert result.original_text == "Sistema de Autenticación"

    def test_existing_feature_usage(self):
        """Test creating result for an existing feature."""
        result = FeatureResult(
            feature_key="PROJ-100",
            was_created=False,
            original_text="PROJ-100"
        )
        
        assert result.feature_key == "PROJ-100"
        assert result.was_created is False
        assert result.original_text == "PROJ-100"

    def test_all_fields_required(self):
        """Test that all fields are required."""
        from pydantic import ValidationError
        
        # Test missing feature_key
        with pytest.raises(ValidationError):
            FeatureResult(
                was_created=True,
                original_text="Test"
            )
        
        # Test missing was_created
        with pytest.raises(ValidationError):
            FeatureResult(
                feature_key="PROJ-100",
                original_text="Test"
            )
        
        # Test missing original_text
        with pytest.raises(ValidationError):
            FeatureResult(
                feature_key="PROJ-100",
                was_created=True
            )


class TestFeatureResultScenarios:
    """Test different feature result scenarios."""

    def test_feature_from_jira_key(self):
        """Test feature result when parent was existing Jira key."""
        result = FeatureResult(
            feature_key="EPIC-456",
            was_created=False,
            original_text="EPIC-456"
        )
        
        assert result.feature_key == "EPIC-456"
        assert result.was_created is False
        assert result.original_text == "EPIC-456"
        # Original text same as feature key indicates existing issue

    def test_feature_from_description(self):
        """Test feature result when parent was description."""
        result = FeatureResult(
            feature_key="PROJ-300",
            was_created=True,
            original_text="Implementar sistema de notificaciones push"
        )
        
        assert result.feature_key == "PROJ-300"
        assert result.was_created is True
        assert result.original_text != result.feature_key
        # Original text different from key indicates description was provided

    def test_feature_reused_from_cache(self):
        """Test feature result when feature was reused from cache."""
        result = FeatureResult(
            feature_key="PROJ-250",
            was_created=False,  # Not created in this batch, but existed in cache
            original_text="Sistema de reportes avanzados"
        )
        
        assert result.feature_key == "PROJ-250"
        assert result.was_created is False
        assert "reportes" in result.original_text

    def test_feature_found_in_jira(self):
        """Test feature result when similar feature was found in Jira."""
        result = FeatureResult(
            feature_key="PROJ-150",
            was_created=False,  # Found existing, not created
            original_text="sistema de autenticacion"  # Normalized description
        )
        
        assert result.feature_key == "PROJ-150"
        assert result.was_created is False
        assert result.original_text.islower()  # Normalized


class TestFeatureResultDataTypes:
    """Test feature result with different data types."""

    def test_feature_key_formats(self):
        """Test different valid feature key formats."""
        key_formats = [
            "PROJ-123",
            "EPIC-456", 
            "FEATURE-789",
            "A-1",
            "PROJECT123-999"
        ]
        
        for key in key_formats:
            result = FeatureResult(
                feature_key=key,
                was_created=True,
                original_text="Test feature"
            )
            assert result.feature_key == key

    def test_boolean_was_created_values(self):
        """Test explicit boolean values for was_created."""
        # Test True
        result_true = FeatureResult(
            feature_key="PROJ-100",
            was_created=True,
            original_text="New feature"
        )
        assert result_true.was_created is True
        
        # Test False
        result_false = FeatureResult(
            feature_key="PROJ-100", 
            was_created=False,
            original_text="Existing feature"
        )
        assert result_false.was_created is False

    def test_original_text_variations(self):
        """Test different original text variations."""
        text_variations = [
            "Simple text",
            "Text with números 123",
            "Texto con acentos áéíóú",
            "Text with special chars: !@#$%",
            "Multi\nline\ntext",
            "   Text with spaces   ",
            ""  # Empty string
        ]
        
        for text in text_variations:
            result = FeatureResult(
                feature_key="PROJ-100",
                was_created=True,
                original_text=text
            )
            assert result.original_text == text


class TestFeatureResultSerialization:
    """Test FeatureResult serialization."""

    def test_feature_result_serialization(self):
        """Test feature result can be serialized to dict."""
        result = FeatureResult(
            feature_key="PROJ-400",
            was_created=True,
            original_text="Sistema de gestión de usuarios"
        )
        
        result_dict = result.model_dump()
        
        assert result_dict["feature_key"] == "PROJ-400"
        assert result_dict["was_created"] is True
        assert result_dict["original_text"] == "Sistema de gestión de usuarios"

    def test_feature_result_from_dict(self):
        """Test creating feature result from dictionary."""
        result_data = {
            "feature_key": "PROJ-500",
            "was_created": False,
            "original_text": "PROJ-500"
        }
        
        result = FeatureResult(**result_data)
        
        assert result.feature_key == "PROJ-500"
        assert result.was_created is False
        assert result.original_text == "PROJ-500"

    def test_nested_serialization(self):
        """Test feature result serialization when nested in other objects."""
        # This would typically be tested with ProcessResult containing FeatureResult
        result = FeatureResult(
            feature_key="PROJ-600",
            was_created=True,
            original_text="Feature description"
        )
        
        # Simulate being part of a larger structure
        container = {
            "main_result": "success",
            "feature_info": result.model_dump()
        }
        
        assert container["feature_info"]["feature_key"] == "PROJ-600"
        assert container["feature_info"]["was_created"] is True


class TestFeatureResultComparison:
    """Test feature result comparison and equality."""

    def test_feature_result_equality(self):
        """Test that identical feature results are equal."""
        result1 = FeatureResult(
            feature_key="PROJ-100",
            was_created=True,
            original_text="Test feature"
        )
        
        result2 = FeatureResult(
            feature_key="PROJ-100", 
            was_created=True,
            original_text="Test feature"
        )
        
        # Pydantic models should be equal if all fields match
        assert result1.model_dump() == result2.model_dump()

    def test_feature_result_inequality(self):
        """Test that different feature results are not equal."""
        result1 = FeatureResult(
            feature_key="PROJ-100",
            was_created=True,
            original_text="Test feature"
        )
        
        result2 = FeatureResult(
            feature_key="PROJ-200",  # Different key
            was_created=True,
            original_text="Test feature"
        )
        
        assert result1.model_dump() != result2.model_dump()

    def test_feature_result_partial_differences(self):
        """Test feature results with partial differences."""
        base_data = {
            "feature_key": "PROJ-100",
            "was_created": True, 
            "original_text": "Test feature"
        }
        
        # Test different was_created
        result_created = FeatureResult(**base_data)
        result_existing = FeatureResult(**{**base_data, "was_created": False})
        
        assert result_created.was_created != result_existing.was_created
        assert result_created.feature_key == result_existing.feature_key
        
        # Test different original_text
        result_different_text = FeatureResult(**{**base_data, "original_text": "Different text"})
        
        assert result_created.original_text != result_different_text.original_text
        assert result_created.feature_key == result_different_text.feature_key


class TestFeatureResultEdgeCases:
    """Test edge cases for FeatureResult."""

    def test_empty_strings(self):
        """Test feature result with empty strings."""
        result = FeatureResult(
            feature_key="",  # Empty key
            was_created=True,
            original_text=""  # Empty original text
        )
        
        assert result.feature_key == ""
        assert result.original_text == ""

    def test_very_long_strings(self):
        """Test feature result with very long strings."""
        long_key = "PROJ-" + "X" * 1000
        long_text = "Very long description: " + "X" * 10000
        
        result = FeatureResult(
            feature_key=long_key,
            was_created=True,
            original_text=long_text
        )
        
        assert len(result.feature_key) > 1000
        assert len(result.original_text) > 10000

    def test_unicode_content(self):
        """Test feature result with unicode content."""
        result = FeatureResult(
            feature_key="PROJ-🚀",
            was_created=True,
            original_text="Sistema de 🔐 autenticación con 🌟 características especiales"
        )
        
        assert "🚀" in result.feature_key
        assert "🔐" in result.original_text
        assert "🌟" in result.original_text