"""Entidad UserStory del dominio."""
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class UserStory(BaseModel):
    """Entidad de dominio para una historia de usuario."""
    titulo: str = Field(
        ..., min_length=1, max_length=255,
        description="Título de la historia de usuario")
    descripcion: str = Field(
        ..., min_length=1, description="Descripción detallada de la historia")
    criterio_aceptacion: str = Field(
        ..., min_length=1, description="Criterios de aceptación")
    subtareas: Optional[List[str]] = Field(
        default=None, description="Lista de subtareas separadas por ;")
    parent: Optional[str] = Field(
        default=None, description="Key del Epic o Feature padre")

    @validator('subtareas', pre=True)
    def parse_subtareas(cls, v):  # pylint: disable=no-self-argument
        """Procesa el campo subtareas dividiéndolo por ; y \n.

        Args:
            v: Valor del campo subtareas

        Returns:
            Lista de subtareas o None
        """
        if v is None or v == '':
            return None
        if isinstance(v, str):
            # Permitir separadores: ';' y salto de línea '\n'
            # Primero dividir por ';', luego por '\n' en cada parte
            tasks = []
            for part in v.split(';'):
                for task in part.split('\n'):
                    if task.strip():
                        tasks.append(task.strip())
            return tasks if tasks else None
        return v
