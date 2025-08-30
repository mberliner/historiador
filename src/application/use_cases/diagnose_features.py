"""Caso de uso para diagnosticar configuración de features y historias."""
import json
import logging
from typing import Dict, Any, Optional

from src.infrastructure.settings import Settings
from src.infrastructure.jira.jira_client import JiraClient
from src.infrastructure.jira.metadata_detector import JiraMetadataDetector

logger = logging.getLogger(__name__)


class DiagnoseFeaturesUseCase:
    """Caso de uso para diagnosticar configuración y campos obligatorios para features y historias."""

    def execute(self, project_key: Optional[str] = None) -> Dict[str, Any]:
        """Ejecuta el diagnóstico completo de features y historias."""
        settings = Settings()
        if project_key:
            settings.project_key = project_key

        logger.info("Iniciando diagnóstico completo para proyecto: %s", settings.project_key)
        logger.debug("Configuración actual: DEFAULT_ISSUE_TYPE=%s, FEATURE_ISSUE_TYPE=%s", 
                    settings.default_issue_type, settings.feature_issue_type)

        # 1. Probar conexión primero
        logger.debug("Paso 1: Probando conexión con Jira en %s", settings.jira_url)
        jira_client = JiraClient(settings)
        if not jira_client.test_connection():
            logger.debug("Falla conexión: URL=%s, EMAIL=%s", settings.jira_url, settings.jira_email)
            raise Exception("Error de conexión con Jira. Verifica JIRA_URL, JIRA_EMAIL y JIRA_API_TOKEN")
        logger.debug("Conexión exitosa con Jira")

        # 2. Validar que el proyecto existe
        logger.debug("Paso 2: Validando existencia del proyecto %s", settings.project_key)
        if not jira_client.validate_project(settings.project_key):
            logger.debug("Proyecto %s no encontrado", settings.project_key)
            raise Exception(f"Proyecto '{settings.project_key}' no encontrado. Verifica PROJECT_KEY en tu configuración")
        logger.debug("Proyecto %s validado correctamente", settings.project_key)

        # 3. Validar tipos de issue configurados (solo si el proyecto existe)
        logger.debug("Paso 3: Validando tipo de historia '%s'", settings.default_issue_type)
        if not jira_client.validate_issue_type(settings.default_issue_type):
            logger.debug("Tipo de historia %s no válido en proyecto %s", 
                        settings.default_issue_type, settings.project_key)
            raise Exception(f"Tipo de historia '{settings.default_issue_type}' no válido en el proyecto '{settings.project_key}'. Verifica DEFAULT_ISSUE_TYPE")
        logger.debug("Tipo de historia %s validado", settings.default_issue_type)

        logger.debug("Paso 4: Validando tipo de feature '%s'", settings.feature_issue_type)
        if not jira_client.validate_feature_issue_type():
            logger.debug("Tipo de feature %s no válido en proyecto %s", 
                        settings.feature_issue_type, settings.project_key)
            raise Exception(f"Tipo de feature '{settings.feature_issue_type}' no válido en el proyecto. Verifica FEATURE_ISSUE_TYPE")
        logger.debug("Tipo de feature %s validado", settings.feature_issue_type)

        # Crear detector de metadata usando la sesión del jira_client
        logger.debug("Paso 5: Creando detector de metadatos")
        detector = JiraMetadataDetector(
            session=jira_client.session,
            base_url=settings.jira_url,
            project_key=settings.project_key
        )

        # Obtener campos obligatorios para features
        logger.debug("Paso 6: Detectando campos obligatorios para features")
        feature_required_fields = jira_client.feature_manager.get_required_fields_for_feature()
        logger.debug("Features: %d campos obligatorios detectados", len(feature_required_fields))
        feature_config_suggestion = json.dumps(feature_required_fields) if feature_required_fields else None

        # Obtener campos obligatorios para historias
        logger.debug("Paso 7: Detectando campos obligatorios para historias (%s)", settings.default_issue_type)
        story_required_fields = detector.detect_story_required_fields(settings.default_issue_type)
        logger.debug("Historias: %d campos obligatorios detectados", len(story_required_fields))
        story_config_suggestion = json.dumps(story_required_fields) if story_required_fields else None

        logger.debug("Diagnóstico completado. Features: %d campos, Historias: %d campos", 
                    len(feature_required_fields), len(story_required_fields))

        return {
            'project_key': settings.project_key,
            'story_type': settings.default_issue_type,
            'feature_type': settings.feature_issue_type,
            'story_required_fields': story_required_fields,
            'story_config_suggestion': story_config_suggestion,
            'feature_required_fields': feature_required_fields,
            'feature_config_suggestion': feature_config_suggestion,
            'current_config': {
                'story_type': settings.default_issue_type,
                'story_required_fields': settings.story_required_fields,
                'feature_type': settings.feature_issue_type,
                'feature_required_fields': settings.feature_required_fields
            }
        }
