"""Interfaz para repositorio de Jira."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from src.domain.entities.user_story import UserStory
from src.domain.entities.process_result import ProcessResult


class JiraRepository(ABC):
    """Interfaz para interactuar con sistemas de gestión de issues."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Prueba la conexión con el sistema."""
        pass

    @abstractmethod
    def validate_project(self, project_key: str) -> bool:
        """Valida que el proyecto existe."""
        pass

    @abstractmethod
    def validate_subtask_issue_type(self, project_key: str) -> bool:
        """Valida que el tipo de subtarea existe."""
        pass

    @abstractmethod
    def validate_feature_issue_type(self) -> bool:
        """Valida que el tipo de feature existe."""
        pass

    @abstractmethod
    def validate_parent_issue(self, issue_key: str) -> bool:
        """Valida que el issue padre existe."""
        pass

    @abstractmethod
    def create_user_story(self, story: UserStory, row_number: int = None) -> ProcessResult:
        """Crea una historia de usuario."""
        pass

    @abstractmethod
    def get_issue_types(self) -> List[Dict[str, Any]]:
        """Obtiene los tipos de issue disponibles."""
        pass