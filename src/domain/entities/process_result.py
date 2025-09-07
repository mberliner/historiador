"""Entidad ProcessResult del dominio."""

from typing import List, Optional

from pydantic import BaseModel

from src.domain.entities.feature_result import FeatureResult


class ProcessResult(BaseModel):
    """Resultado del procesamiento de una historia de usuario."""

    success: bool
    jira_key: Optional[str] = None
    error_message: Optional[str] = None
    row_number: Optional[int] = None
    subtasks_created: int = 0
    subtasks_failed: int = 0
    subtask_errors: Optional[List[str]] = None
    feature_info: Optional[FeatureResult] = None
