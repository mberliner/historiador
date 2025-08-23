"""Caso de uso para probar conexión con Jira."""
from typing import Dict, Any

from src.infrastructure.settings import Settings
from src.infrastructure.jira.jira_client import JiraClient


class TestConnectionUseCase:
    """Caso de uso para probar la conexión con Jira."""

    def execute(self) -> Dict[str, Any]:
        """Ejecuta la prueba de conexión."""
        settings = Settings()
        jira_client = JiraClient(settings)

        connection_success = jira_client.test_connection()
        project_valid = False

        if connection_success:
            project_valid = jira_client.validate_project(settings.project_key)

        return {
            'connection_success': connection_success,
            'project_valid': project_valid,
            'project_key': settings.project_key
        }
