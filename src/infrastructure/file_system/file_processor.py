"""Procesador de archivos CSV/Excel para historias de usuario."""

import logging
from pathlib import Path
from typing import Iterator

import pandas as pd

from src.domain.entities.user_story import UserStory

logger = logging.getLogger(__name__)


class FileProcessor:
    """Procesador de archivos Excel y CSV para historias de usuario."""

    REQUIRED_COLUMNS = ["titulo", "descripcion", "criterio_aceptacion"]
    OPTIONAL_COLUMNS = ["subtareas", "parent"]

    def __init__(self):
        """Inicializa el procesador con extensiones soportadas."""
        self.supported_extensions = [".csv", ".xlsx", ".xls"]

    def validate_file(self, file_path: str) -> None:
        """Valida que el archivo existe y tiene extensión soportada.

        Args:
            file_path: Ruta del archivo a validar

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si la extensión no es soportada
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe")

        if path.suffix.lower() not in self.supported_extensions:
            raise ValueError(
                f"Extensión no soportada. Use: "
                f"{', '.join(self.supported_extensions)}"
            )

    def read_file(self, file_path: str) -> pd.DataFrame:
        """Lee archivo Excel o CSV y retorna DataFrame.

        Args:
            file_path: Ruta del archivo a leer

        Returns:
            DataFrame con los datos del archivo

        Raises:
            Exception: Si hay error al leer el archivo
        """
        self.validate_file(file_path)
        path = Path(file_path)

        try:
            if path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path, encoding="utf-8")
            else:  # Excel files
                df = pd.read_excel(file_path)

            logger.info("Archivo leído exitosamente: %d filas encontradas", len(df))
            return df

        except Exception as e:
            logger.error("Error al leer archivo %s: %s", file_path, str(e))
            raise

    def validate_columns(self, df: pd.DataFrame) -> None:
        """Valida que el DataFrame tenga las columnas requeridas.

        Args:
            df: DataFrame a validar

        Raises:
            ValueError: Si faltan columnas requeridas
        """
        missing_columns = [
            col for col in self.REQUIRED_COLUMNS if col not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Columnas requeridas faltantes: " f"{', '.join(missing_columns)}"
            )

        logger.info("Validación de columnas exitosa")

    def process_file(self, file_path: str) -> Iterator[UserStory]:
        """Procesa archivo y genera historias de usuario validadas.

        Args:
            file_path: Ruta del archivo a procesar

        Yields:
            UserStory: Historias de usuario validadas

        Raises:
            ValueError: Si hay error en alguna fila
        """
        df = self.read_file(file_path)
        self.validate_columns(df)

        # Rellenar columnas opcionales faltantes con None
        for col in self.OPTIONAL_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Limpiar datos
        df = df.fillna("")
        df = df.replace("", None)

        for index, row in df.iterrows():
            try:
                story = UserStory(
                    titulo=row["titulo"],
                    descripcion=row["descripcion"],
                    criterio_aceptacion=row["criterio_aceptacion"],
                    subtareas=row.get("subtareas"),
                    parent=row.get("parent"),
                )
                yield story

            except Exception as e:
                logger.error("Error en fila %d: %s", index + 2, str(e))
                raise ValueError(f"Error en fila {index + 2}: {str(e)}")

    def preview_file(self, file_path: str, rows: int = 5) -> pd.DataFrame:
        """Muestra preview del archivo para validación.

        Args:
            file_path: Ruta del archivo
            rows: Número de filas a mostrar

        Returns:
            DataFrame con las primeras filas
        """
        df = self.read_file(file_path)
        return df.head(rows)
