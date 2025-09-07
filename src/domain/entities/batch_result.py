"""Entidad BatchResult del dominio."""

from typing import Any, List, Optional

from pydantic import BaseModel

from src.domain.entities.process_result import ProcessResult


class BatchResult(BaseModel):
    """Resultado del procesamiento de un lote de historias."""

    total_processed: int
    successful: int
    failed: int
    results: List[ProcessResult]
    stories: Optional[List[Any]] = None  # Para almacenar las historias originales
