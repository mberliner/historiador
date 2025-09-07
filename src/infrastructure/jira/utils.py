"""Utilidades compartidas para interacción con Jira."""

import json
import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)


def get_issue_types(
    session: requests.Session, base_url: str, project_key: str
) -> List[Dict[str, Any]]:
    """Obtiene los tipos de issue disponibles para un proyecto.

    Args:
        session: Sesión de requests configurada
        base_url: URL base de Jira
        project_key: Key del proyecto

    Returns:
        Lista de tipos de issue disponibles
    """
    try:
        url = f"{base_url}/rest/api/3/issue/createmeta"
        params = f"projectKeys={project_key}&expand=projects.issuetypes"
        response = session.get(f"{url}?{params}")
        response.raise_for_status()
        data = response.json()

        # Extraer tipos de issue del proyecto
        if data.get("projects") and len(data["projects"]) > 0:
            return data["projects"][0].get("issuetypes", [])

        logger.warning("No se encontraron proyectos en createmeta")
        return []

    except Exception as e:
        logger.error("Error obteniendo tipos de issue: %s", str(e))
        return []


def handle_http_error(e: Exception, logger_instance: logging.Logger) -> None:
    """Maneja errores HTTP de Jira de forma consistente.

    Args:
        e: Excepción capturada
        logger_instance: Logger a usar para el error
    """
    if hasattr(e, "response") and e.response is not None:
        try:
            error_details = e.response.json()
            logger_instance.error(
                "Detalles del error: %s", json.dumps(error_details, indent=2)
            )
        except Exception:
            logger_instance.error(
                "Error HTTP %s: %s", e.response.status_code, e.response.text
            )
    else:
        logger_instance.error("Error de conexión: %s", str(e))


def validate_issue_exists(
    session: requests.Session, base_url: str, issue_key: str
) -> bool:
    """Valida que un issue existe en Jira.

    Args:
        session: Sesión de requests configurada
        base_url: URL base de Jira
        issue_key: Key del issue a validar

    Returns:
        True si el issue existe, False en caso contrario
    """
    if not issue_key:
        return True

    try:
        response = session.get(f"{base_url}/rest/api/3/issue/{issue_key}")
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.error("Issue %s no encontrado", issue_key)
            return False
        raise
