"""Caso de uso para validar archivos."""

from typing import Any, Dict

from src.infrastructure.file_system.file_processor import FileProcessor


class ValidateFileUseCase:
    """Caso de uso para validar archivos sin crear issues."""

    def __init__(self):
        self.file_processor = FileProcessor()

    def execute(self, file_path: str, preview_rows: int = 5) -> Dict[str, Any]:
        """Ejecuta la validación del archivo."""
        # Mostrar preview
        df = self.file_processor.preview_file(file_path, preview_rows)

        # Procesar todas las filas para validar datos
        stories = list(self.file_processor.process_file(file_path))

        # Calcular estadísticas
        with_subtasks = sum(1 for s in stories if s.subtareas)
        with_parent = sum(1 for s in stories if s.parent)
        total_subtasks = sum(len(s.subtareas) if s.subtareas else 0 for s in stories)

        # Validar subtareas
        invalid_subtasks = 0
        for story in stories:
            if story.subtareas:
                invalid_subtasks += sum(
                    1 for s in story.subtareas if not s.strip() or len(s.strip()) > 255
                )

        return {
            "file": file_path,
            "rows": preview_rows,
            "preview": df.to_string(index=False),
            "total_stories": len(stories),
            "with_subtasks": with_subtasks,
            "total_subtasks": total_subtasks,
            "with_parent": with_parent,
            "invalid_subtasks": invalid_subtasks,
        }
