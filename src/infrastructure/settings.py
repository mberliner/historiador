"""Configuración de la aplicación usando pydantic."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación con validación de tipos."""

    jira_url: str = Field(
        ..., description="URL base de Jira (ej: https://company.atlassian.net)"
    )
    jira_email: str = Field(..., description="Email del usuario de Jira")
    jira_api_token: str = Field(..., description="API Token de Jira")
    project_key: str = Field(..., description="Key del proyecto en Jira")
    default_issue_type: str = Field(
        default="Story", description="Tipo de issue por defecto"
    )
    subtask_issue_type: str = Field(
        default="Sub-task", description="Tipo de issue para subtareas"
    )
    batch_size: int = Field(default=10, description="Tamaño del lote de procesamiento")
    dry_run: bool = Field(default=False, description="Modo de prueba sin crear issues")
    acceptance_criteria_field: Optional[str] = Field(
        default=None,
        description="ID del campo personalizado para criterios de aceptación",
    )
    input_directory: str = Field(
        default="entrada",
        description="Directorio donde se encuentran los archivos de entrada",
    )
    logs_directory: str = Field(
        default="logs", description="Directorio donde se almacenan los archivos de log"
    )
    processed_directory: str = Field(
        default="procesados",
        description="Directorio donde se mueven los archivos procesados",
    )
    rollback_on_subtask_failure: bool = Field(
        default=False, description="Eliminar historia si fallan todas las subtareas"
    )
    feature_issue_type: str = Field(
        default="Feature",
        description="Tipo de issue para features/epics creados automáticamente",
    )
    feature_required_fields: Optional[str] = Field(
        default=None,
        description="Campos obligatorios adicionales para features en formato JSON",
    )
    story_required_fields: Optional[str] = Field(
        default=None,
        description="Campos obligatorios adicionales para historias de usuario en formato JSON",
    )

    class Config:
        """Configuración de pydantic."""

        env_file = ".env"
        env_file_encoding = "utf-8"
