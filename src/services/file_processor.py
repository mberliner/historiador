import pandas as pd
from pathlib import Path
from typing import List, Iterator
from src.models.jira_models import UserStory
import logging

logger = logging.getLogger(__name__)


class FileProcessor:
    """Procesador de archivos Excel y CSV para historias de usuario."""
    
    REQUIRED_COLUMNS = ['titulo', 'descripcion', 'criterio_aceptacion']
    OPTIONAL_COLUMNS = ['subtareas', 'parent']
    
    def __init__(self):
        self.supported_extensions = ['.csv', '.xlsx', '.xls']
    
    def validate_file(self, file_path: str) -> None:
        """Valida que el archivo existe y tiene extensión soportada."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe")
        
        if path.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"Extensión no soportada. Use: {', '.join(self.supported_extensions)}")
    
    def read_file(self, file_path: str) -> pd.DataFrame:
        """Lee archivo Excel o CSV y retorna DataFrame."""
        self.validate_file(file_path)
        path = Path(file_path)
        
        try:
            if path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            else:  # Excel files
                df = pd.read_excel(file_path)
            
            logger.info(f"Archivo leído exitosamente: {len(df)} filas encontradas")
            return df
            
        except Exception as e:
            logger.error(f"Error al leer archivo {file_path}: {str(e)}")
            raise
    
    def validate_columns(self, df: pd.DataFrame) -> None:
        """Valida que el DataFrame tenga las columnas requeridas."""
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Columnas requeridas faltantes: {', '.join(missing_columns)}")
        
        logger.info("Validación de columnas exitosa")
    
    def process_file(self, file_path: str) -> Iterator[UserStory]:
        """Procesa archivo y genera historias de usuario validadas."""
        df = self.read_file(file_path)
        self.validate_columns(df)
        
        # Rellenar columnas opcionales faltantes con None
        for col in self.OPTIONAL_COLUMNS:
            if col not in df.columns:
                df[col] = None
        
        # Limpiar datos
        df = df.fillna('')
        df = df.replace('', None)
        
        for index, row in df.iterrows():
            try:
                story = UserStory(
                    titulo=row['titulo'],
                    descripcion=row['descripcion'],
                    criterio_aceptacion=row['criterio_aceptacion'],
                    subtareas=row.get('subtareas'),
                    parent=row.get('parent')
                )
                yield story
                
            except Exception as e:
                logger.error(f"Error en fila {index + 2}: {str(e)}")
                raise ValueError(f"Error en fila {index + 2}: {str(e)}")
    
    def preview_file(self, file_path: str, rows: int = 5) -> pd.DataFrame:
        """Muestra preview del archivo para validación."""
        df = self.read_file(file_path)
        return df.head(rows)