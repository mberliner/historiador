"""Interfaz para gestor de features."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple

from src.domain.entities.feature_result import FeatureResult


class FeatureManagerInterface(ABC):
    """Interfaz para gestión de features/parents."""

    @abstractmethod
    def is_jira_key(self, text: str) -> bool:
        """Determina si el texto es una key de Jira válida."""
        pass

    @abstractmethod
    def validate_feature_type(self) -> bool:
        """Valida que el tipo de feature existe."""
        pass

    @abstractmethod
    def get_required_fields_for_feature(self) -> Dict[str, Any]:
        """Obtiene campos obligatorios para crear features."""
        pass

    @abstractmethod
    def process_parent(self, parent_text: str, project_key: str) -> Tuple[Optional[str], Optional[FeatureResult]]:
        """Procesa el campo parent y retorna la key a usar y info de feature si se creó."""
        pass

    @abstractmethod
    def find_existing_feature(self, description: str, project_key: str) -> Optional[str]:
        """Busca feature existente por descripción."""
        pass

    @abstractmethod
    def create_feature(self, description: str, project_key: str) -> str:
        """Crea una nueva feature."""
        pass
