"""Entidad FeatureResult del dominio."""
from pydantic import BaseModel


class FeatureResult(BaseModel):
    """Resultado del procesamiento de una feature/parent."""
    feature_key: str
    was_created: bool
    original_text: str