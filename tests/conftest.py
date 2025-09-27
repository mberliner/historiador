"""Pytest configuration and shared fixtures."""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import responses

from src.infrastructure.settings import Settings
from src.domain.entities.user_story import UserStory
from tests.fixtures.sample_data import SAMPLE_STORIES, create_sample_csv
from tests.fixtures.jira_responses import (
    SAMPLE_PROJECT_RESPONSE,
    SAMPLE_ISSUE_TYPES_RESPONSE, 
    SAMPLE_CREATE_ISSUE_RESPONSE,
    SAMPLE_MYSELF_RESPONSE
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_settings(temp_dir):
    """Create sample settings for testing."""
    return Settings(
        jira_url="https://test.atlassian.net",
        jira_email="test@example.com", 
        jira_api_token="test-token",
        project_key="TEST",
        default_issue_type="Story",
        subtask_issue_type="Subtarea",
        feature_issue_type="Feature",
        dry_run=False,
        input_directory=str(temp_dir / "entrada"),
        logs_directory=str(temp_dir / "logs"),
        processed_directory=str(temp_dir / "procesados"),
        rollback_on_subtask_failure=False,
        acceptance_criteria_field=None,
        feature_required_fields=None
    )


@pytest.fixture
def sample_user_story():
    """Create a sample user story for testing."""
    return UserStory(
        titulo="Test Story",
        descripcion="Test description",
        criterio_aceptacion="Test criteria",
        subtareas=["Subtask 1", "Subtask 2"],
        parent="TEST-100"
    )


@pytest.fixture 
def sample_csv_file(temp_dir):
    """Create a sample CSV file for testing."""
    file_path = temp_dir / "test_stories.csv"
    create_sample_csv(SAMPLE_STORIES, str(file_path))
    return str(file_path)


@pytest.fixture
def mock_jira_session():
    """Create a mock Jira session."""
    session = Mock()
    session.auth = ("test@example.com", "test-token")
    session.headers = {"Accept": "application/json", "Content-Type": "application/json"}
    return session


@pytest.fixture
def mock_jira_responses():
    """Setup mock responses for Jira API calls."""
    with responses.RequestsMock() as rsps:
        # Mock authentication test
        rsps.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/myself",
            json=SAMPLE_MYSELF_RESPONSE,
            status=200
        )
        
        # Mock project validation
        rsps.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/project/TEST",
            json=SAMPLE_PROJECT_RESPONSE,
            status=200
        )
        
        # Mock issue types
        rsps.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/createmeta",
            json=SAMPLE_ISSUE_TYPES_RESPONSE,
            status=200
        )
        
        # Mock issue creation
        rsps.add(
            responses.POST,
            "https://test.atlassian.net/rest/api/3/issue",
            json=SAMPLE_CREATE_ISSUE_RESPONSE,
            status=201
        )
        
        yield rsps


@pytest.fixture
def mock_file_processor():
    """Create a mock file processor."""
    processor = Mock()
    processor.supported_extensions = ['.csv', '.xlsx', '.xls']
    processor.REQUIRED_COLUMNS = ['titulo', 'descripcion', 'criterio_aceptacion']
    processor.OPTIONAL_COLUMNS = ['subtareas', 'parent']
    return processor


@pytest.fixture
def mock_feature_manager():
    """Create a mock feature manager."""
    manager = Mock()
    manager.is_jira_key.return_value = False
    manager.get_or_create_parent.return_value = ("TEST-200", True)
    manager.validate_feature_type.return_value = True
    return manager


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")


# Markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "jira_api: Tests requiring Jira API mocking")