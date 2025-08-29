"""Detector de metadatos de Jira para configuración automática."""
import logging
from typing import Dict, Any, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class JiraMetadataDetector:
    """Detector de metadatos para configuración automática de Jira."""

    def __init__(self, session: requests.Session, base_url: str, project_key: str):
        self.session = session
        self.base_url = base_url.rstrip('/')
        self.project_key = project_key

    def get_available_issue_types(self) -> Dict[str, List[str]]:
        """Obtiene los tipos de issue disponibles categorizados.

        Returns:
            Dict con 'standard', 'subtasks', y 'all' como keys
        """
        try:
            url = f"{self.base_url}/rest/api/3/issue/createmeta"
            params = f"projectKeys={self.project_key}&expand=projects.issuetypes"
            response = self.session.get(f"{url}?{params}")
            response.raise_for_status()
            data = response.json()

            if not data.get("projects") or len(data["projects"]) == 0:
                logger.warning("No se encontraron proyectos en createmeta")
                return {"standard": [], "subtasks": [], "all": []}

            issue_types = data["projects"][0].get("issuetypes", [])

            standard_types = []
            subtask_types = []
            all_types = []

            for issue_type in issue_types:
                name = issue_type.get("name", "")
                all_types.append(name)

                if issue_type.get("subtask", False):
                    subtask_types.append(name)
                else:
                    standard_types.append(name)

            return {
                "standard": standard_types,
                "subtasks": subtask_types,
                "all": all_types
            }

        except Exception as e:
            logger.error("Error obteniendo tipos de issue: %s", str(e))
            return {"standard": [], "subtasks": [], "all": []}

    def detect_acceptance_criteria_fields(self) -> List[Dict[str, str]]:
        """Detecta campos personalizados que podrían ser para criterios de aceptación.

        Returns:
            Lista de candidatos con 'id', 'name', 'type'
        """
        try:
            # Obtener metadatos de creación para Story o tipo similar
            story_types = ["Story", "Historia", "Historia de Usuario", "User Story"]

            for issue_type in story_types:
                fields = self._get_fields_for_issue_type(issue_type)
                if fields:
                    candidates = self._filter_criteria_fields(fields)
                    if candidates:
                        return candidates

            # Si no encuentra tipos específicos, usar el primer tipo estándar
            issue_types = self.get_available_issue_types()
            if issue_types["standard"]:
                first_type = issue_types["standard"][0]
                fields = self._get_fields_for_issue_type(first_type)
                return self._filter_criteria_fields(fields) if fields else []

            return []

        except Exception as e:
            logger.error("Error detectando campos de criterios: %s", str(e))
            return []

    def detect_feature_required_fields(
            self, feature_type: str = "Feature"
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Detecta campos obligatorios para Features y Epic Name field.

        Args:
            feature_type: Tipo de issue para Features

        Returns:
            Tupla con (required_fields_dict, epic_name_field_id)
        """
        try:
            response = self.session.get(
                f"{self.base_url}/rest/api/3/issue/createmeta",
                params={
                    'projectKeys': self.project_key,
                    'issuetypeNames': feature_type,
                    'expand': 'projects.issuetypes.fields'
                }
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("projects") or len(data["projects"]) == 0:
                logger.warning("No se encontraron proyectos en createmeta para %s", feature_type)
                return {}, None

            project = data["projects"][0]
            if not project.get("issuetypes") or len(project["issuetypes"]) == 0:
                logger.warning("No se encontró tipo de issue %s", feature_type)
                return {}, None

            issuetype = project["issuetypes"][0]
            fields = issuetype.get("fields", {})

            required_fields = {}
            epic_name_field_id = None

            for field_id, field_info in fields.items():
                field_name = field_info.get("name", field_id).lower()

                # Detectar campo Epic Name
                if "epic" in field_name and "name" in field_name:
                    epic_name_field_id = field_id
                    logger.debug("Campo Epic Name detectado: %s (%s)",
                               field_info.get("name", field_id), field_id)

                # Procesar campos obligatorios
                if field_info.get("required", False):
                    # Excluir campos básicos que ya se manejan
                    if field_id in ["project", "summary", "issuetype", "description"]:
                        continue

                    allowed_values = field_info.get("allowedValues", [])

                    # Si hay valores permitidos, usar el primero como default
                    if allowed_values and len(allowed_values) > 0:
                        default_value = allowed_values[0]
                        if "id" in default_value:
                            required_fields[field_id] = {"id": default_value["id"]}
                        elif "value" in default_value:
                            required_fields[field_id] = {"value": default_value["value"]}
                        else:
                            required_fields[field_id] = default_value

                        logger.debug(
                            "Campo obligatorio: %s -> valor por defecto: %s",
                            field_info.get("name", field_id),
                            default_value.get(
                                "value", default_value.get("name", str(default_value))
                            )
                        )

            return required_fields, epic_name_field_id

        except Exception as e:
            logger.error("Error detectando campos obligatorios para %s: %s", feature_type, str(e))
            return {}, None

    def suggest_optimal_types(self) -> Dict[str, str]:
        """Sugiere tipos de issue óptimos basado en lo disponible en el proyecto.

        Returns:
            Dict con sugerencias para default_issue_type, subtask_issue_type, feature_issue_type
        """
        issue_types = self.get_available_issue_types()

        suggestions = {
            "default_issue_type": "Story",
            "subtask_issue_type": "Subtarea",
            "feature_issue_type": "Feature"
        }

        # Buscar Story o equivalente
        story_candidates = ["Story", "Historia", "Historia de Usuario", "User Story"]
        for candidate in story_candidates:
            if candidate in issue_types["standard"]:
                suggestions["default_issue_type"] = candidate
                break
        else:
            # Si no encuentra, usar el primer tipo estándar disponible
            if issue_types["standard"]:
                suggestions["default_issue_type"] = issue_types["standard"][0]

        # Buscar subtarea
        subtask_candidates = ["Subtarea", "Sub-task", "Subtask", "Sub-tarea"]
        for candidate in subtask_candidates:
            if candidate in issue_types["subtasks"]:
                suggestions["subtask_issue_type"] = candidate
                break
        else:
            # Usar el primer tipo de subtarea disponible
            if issue_types["subtasks"]:
                suggestions["subtask_issue_type"] = issue_types["subtasks"][0]

        # Buscar Feature o Epic
        feature_candidates = ["Feature", "Epic", "Funcionalidad", "Épica"]
        for candidate in feature_candidates:
            if candidate in issue_types["standard"]:
                suggestions["feature_issue_type"] = candidate
                break
        else:
            # Si no encuentra, buscar algo que suene a contenedor
            for issue_type in issue_types["standard"]:
                container_words = ["parent", "container", "theme", "initiative"]
                if any(word in issue_type.lower() for word in container_words):
                    suggestions["feature_issue_type"] = issue_type
                    break
            else:
                # Fallback: usar Story o el primer tipo estándar
                suggestions["feature_issue_type"] = suggestions["default_issue_type"]

        return suggestions

    def _get_fields_for_issue_type(self, issue_type: str) -> Optional[Dict[str, Any]]:
        """Obtiene campos disponibles para un tipo de issue específico."""
        try:
            response = self.session.get(
                f"{self.base_url}/rest/api/3/issue/createmeta",
                params={
                    'projectKeys': self.project_key,
                    'issuetypeNames': issue_type,
                    'expand': 'projects.issuetypes.fields'
                }
            )
            response.raise_for_status()
            data = response.json()

            if (data.get("projects") and len(data["projects"]) > 0 and
                data["projects"][0].get("issuetypes") and
                len(data["projects"][0]["issuetypes"]) > 0):

                return data["projects"][0]["issuetypes"][0].get("fields", {})

            return None

        except Exception as e:
            logger.warning("Error obteniendo campos para %s: %s", issue_type, str(e))
            return None

    def _filter_criteria_fields(self, fields: Dict[str, Any]) -> List[Dict[str, str]]:
        """Filtra campos que podrían ser para criterios de aceptación."""
        candidates = []

        # Palabras clave que indican criterios de aceptación
        criteria_keywords = [
            "criteria", "criterio", "criterios", "acceptance", "aceptacion", "aceptación",
            "condition", "condicion", "condición", "requirement", "requisito", "test"
        ]

        for field_id, field_info in fields.items():
            # Solo campos personalizados (customfield_*)
            if not field_id.startswith("customfield_"):
                continue

            field_name = field_info.get("name", "").lower()
            field_type = field_info.get("schema", {}).get("type", "")

            # Filtrar por tipo de campo (text, rich text)
            valid_types = ["string", "any", "doc", "textarea"]  # Tipos que pueden contener texto
            if field_type not in valid_types:
                continue

            # Buscar palabras clave en el nombre
            if any(keyword in field_name for keyword in criteria_keywords):
                candidates.append({
                    "id": field_id,
                    "name": field_info.get("name", field_id),
                    "type": field_type
                })

        # Ordenar por relevancia (criterios específicos primero)
        def relevance_score(field):
            name = field["name"].lower()
            score = 0
            if "acceptance" in name or "aceptacion" in name or "aceptación" in name:
                score += 10
            if "criteria" in name or "criterio" in name:
                score += 8
            if "condition" in name or "condicion" in name or "condición" in name:
                score += 5
            return score

        candidates.sort(key=relevance_score, reverse=True)
        return candidates[:5]  # Máximo 5 candidatos
