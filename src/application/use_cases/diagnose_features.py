"""Caso de uso para diagnosticar configuración de features."""
import json
import logging
from typing import Dict, Any, Optional

from src.infrastructure.settings import Settings
from src.infrastructure.jira.jira_client import JiraClient

logger = logging.getLogger(__name__)


class DiagnoseFeaturesUseCase:
    """Caso de uso para diagnosticar configuración y campos obligatorios para features."""

    def execute(self, project_key: Optional[str] = None) -> Dict[str, Any]:
        """Ejecuta el diagnóstico de features."""
        settings = Settings()
        if project_key:
            settings.project_key = project_key

        logger.info("Iniciando diagnóstico de features para proyecto: %s", settings.project_key)

        # Probar conexión
        jira_client = JiraClient(settings)
        if not jira_client.test_connection():
            raise Exception("Error de conexión con Jira")

        # Validar proyecto
        if not jira_client.validate_project(settings.project_key):
            raise Exception(f"Proyecto {settings.project_key} no encontrado")

        # Validar tipo de feature
        if not jira_client.validate_feature_issue_type():
            raise Exception(f"Tipo de feature '{settings.feature_issue_type}' no válido")

        # Obtener campos obligatorios
        required_fields = jira_client.feature_manager.get_required_fields_for_feature()
        config_suggestion = json.dumps(required_fields) if required_fields else None

        return {
            'project_key': settings.project_key,
            'feature_type': settings.feature_issue_type,
            'required_fields': required_fields,
            'config_suggestion': config_suggestion,
            'current_config': {
                'feature_type': settings.feature_issue_type,
                'required_fields': settings.feature_required_fields
            }
        }
