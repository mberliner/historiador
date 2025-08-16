"""Interfaz para repositorio de archivos."""
from abc import ABC, abstractmethod
from typing import Iterator, List
import pandas as pd

from src.domain.entities.user_story import UserStory


class FileRepository(ABC):
    """Interfaz para procesar archivos de entrada."""

    @abstractmethod
    def validate_file(self, file_path: str) -> None:
        """Valida que el archivo existe y tiene formato correcto."""
        pass

    @abstractmethod
    def read_file(self, file_path: str) -> pd.DataFrame:
        """Lee archivo y retorna DataFrame."""
        pass

    @abstractmethod
    def validate_columns(self, df: pd.DataFrame) -> None:
        """Valida que el DataFrame tenga las columnas requeridas."""
        pass

    @abstractmethod
    def process_file(self, file_path: str) -> Iterator[UserStory]:
        """Procesa archivo y genera historias de usuario."""
        pass

    @abstractmethod
    def preview_file(self, file_path: str, rows: int = 5) -> pd.DataFrame:
        """Genera preview del archivo."""
        pass

    @abstractmethod
    def find_files(self, directory: str, patterns: List[str]) -> List[str]:
        """Encuentra archivos que coincidan con los patrones."""
        pass