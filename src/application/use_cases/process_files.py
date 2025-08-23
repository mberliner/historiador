"""Caso de uso para procesar archivos de historias de usuario."""
import glob
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from src.infrastructure.settings import Settings
from src.infrastructure.file_system.file_processor import FileProcessor
from src.infrastructure.jira.jira_client import JiraClient
from src.domain.entities.batch_result import BatchResult
from src.domain.entities.process_result import ProcessResult

logger = logging.getLogger(__name__)


class ProcessFilesUseCase:
    """Caso de uso para procesar archivos de entrada y crear historias en Jira."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.file_processor = FileProcessor()
        self.jira_client = JiraClient(settings)

    def find_input_files(self) -> List[str]:
        """Encuentra todos los archivos CSV y Excel en el directorio de entrada."""
        input_dir = Path(self.settings.input_directory)

        if not input_dir.exists():
            input_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Directorio de entrada creado: %s", input_dir)
            return []

        patterns = ['*.csv', '*.xlsx', '*.xls']
        files = []

        for pattern in patterns:
            files.extend(glob.glob(str(input_dir / pattern)))

        return sorted(files)

    def move_file_to_processed(self, file_path: str) -> None:
        """Mueve archivo procesado al directorio de procesados."""
        processed_dir = Path(self.settings.processed_directory)
        processed_dir.mkdir(exist_ok=True)

        source_path = Path(file_path)
        dest_path = processed_dir / source_path.name

        # Si ya existe el archivo, agregar timestamp
        if dest_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stem = source_path.stem
            suffix = source_path.suffix
            dest_path = processed_dir / f"{stem}_{timestamp}{suffix}"

        shutil.move(str(source_path), str(dest_path))
        logger.info("Archivo movido a: %s", dest_path)

    def validate_prerequisites(self, files_to_process: List[str]) -> None:
        """Valida prerequisitos antes del procesamiento."""
        if not self.settings.dry_run:
            # Validar conexión
            if not self.jira_client.test_connection():
                raise Exception("No se pudo conectar a Jira")

            if not self.jira_client.validate_project(self.settings.project_key):
                raise Exception(f"Proyecto {self.settings.project_key} no encontrado")

            # Validar tipo de subtarea si hay archivos con subtareas
            has_subtasks = any(
                any(story.subtareas for story in self.file_processor.process_file(f))
                for f in files_to_process
            )

            if has_subtasks and not self.jira_client.validate_subtask_issue_type(self.settings.project_key):
                raise Exception(f"Tipo de subtarea '{self.settings.subtask_issue_type}' no válido")

            # Verificar si hay parents y validar tipo de feature
            has_parents = any(
                any(story.parent for story in self.file_processor.process_file(f))
                for f in files_to_process
            )

            if has_parents and not self.jira_client.validate_feature_issue_type():
                raise Exception(f"Tipo de feature '{self.settings.feature_issue_type}' no válido")

    def process_single_file(self, file_path: str) -> BatchResult:
        """Procesa un único archivo."""
        results: List[ProcessResult] = []
        stories = []  # Para almacenar las historias
        batch_count = 0

        for row_number, story in enumerate(self.file_processor.process_file(file_path), start=1):
            result = self.jira_client.create_user_story(story, row_number)
            results.append(result)
            stories.append(story)  # Guardar story para mostrar título después

            batch_count += 1
            if batch_count >= self.settings.batch_size:
                logger.info(f"Lote completado. Procesadas {len(results)} historias...")
                batch_count = 0

        batch_result = BatchResult(
            total_processed=len(results),
            successful=sum(1 for r in results if r.success),
            failed=sum(1 for r in results if not r.success),
            results=results
        )
        
        # Agregar stories al batch_result para poder mostrarlos después
        batch_result.stories = stories

        return batch_result

    def execute(self, files_to_process: List[str]) -> Dict[str, Any]:
        """Ejecuta el procesamiento de archivos."""
        logger.info("Proyecto: %s", self.settings.project_key)
        logger.info("Modo dry-run: %s", self.settings.dry_run)

        # Validar prerequisitos
        self.validate_prerequisites(files_to_process)

        # Procesar cada archivo
        total_files = len(files_to_process)
        overall_results = []
        file_results = []

        for file_index, current_file in enumerate(files_to_process, 1):
            logger.info("Procesando archivo %d/%d: %s", file_index, total_files, Path(current_file).name)

            try:
                batch_result = self.process_single_file(current_file)

                file_results.append({
                    'file_path': current_file,
                    'file_name': Path(current_file).name,
                    'file_index': file_index,
                    'batch_result': batch_result
                })

                overall_results.extend(batch_result.results)

                # Mover archivo a procesados solo si no es dry-run y fue exitoso
                if not self.settings.dry_run and batch_result.successful > 0:
                    self.move_file_to_processed(current_file)
                    logger.info("Archivo movido a directorio de procesados")
                elif self.settings.dry_run:
                    logger.info("Dry-run mode: archivo no movido - %s", current_file)
                else:
                    logger.warning("Archivo no movido debido a fallos: %s", current_file)

            except Exception as e:
                logger.error("Error procesando archivo %s: %s", current_file, str(e))
                file_results.append({
                    'file_path': current_file,
                    'file_name': Path(current_file).name,
                    'file_index': file_index,
                    'error': str(e)
                })

        # Resumen general
        overall_batch_result = BatchResult(
            total_processed=len(overall_results),
            successful=sum(1 for r in overall_results if r.success),
            failed=sum(1 for r in overall_results if not r.success),
            results=overall_results
        ) if overall_results else None

        return {
            'total_files': total_files,
            'file_results': file_results,
            'overall_result': overall_batch_result
        }