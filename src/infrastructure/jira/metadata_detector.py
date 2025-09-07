"""Detector de metadatos de Jira para configuración automática."""

import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class JiraMetadataDetector:
    """Detector de metadatos para configuración automática de Jira."""

    def __init__(self, session: requests.Session, base_url: str, project_key: str):
        self.session = session
        self.base_url = base_url.rstrip("/")
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
                "all": all_types,
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
                    "projectKeys": self.project_key,
                    "issuetypeNames": feature_type,
                    "expand": "projects.issuetypes.fields",
                },
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("projects") or len(data["projects"]) == 0:
                logger.warning(
                    "No se encontraron proyectos en createmeta para %s", feature_type
                )
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
                    logger.debug(
                        "Campo Epic Name detectado: %s (%s)",
                        field_info.get("name", field_id),
                        field_id,
                    )

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
                            required_fields[field_id] = {
                                "value": default_value["value"]
                            }
                        else:
                            required_fields[field_id] = default_value

                        logger.debug(
                            "Campo obligatorio: %s -> valor por defecto: %s",
                            field_info.get("name", field_id),
                            default_value.get(
                                "value", default_value.get("name", str(default_value))
                            ),
                        )

            return required_fields, epic_name_field_id

        except Exception as e:
            logger.error(
                "Error detectando campos obligatorios para %s: %s", feature_type, str(e)
            )
            return {}, None

    def detect_story_required_fields(self, story_type: str = "Story") -> Dict[str, Any]:
        """Detecta campos obligatorios para historias de usuario.

        Args:
            story_type: Tipo de issue para historias de usuario

        Returns:
            Dict con campos obligatorios requeridos
        """
        logger.debug(
            "Iniciando detección de campos obligatorios para tipo: %s", story_type
        )

        # Primero intentar encontrar el ID real del tipo de issue usando la misma lógica
        # que validate_issue_type para manejar alias como Story/Historia
        issue_type_id = self._find_issue_type_id(story_type)
        if not issue_type_id:
            logger.warning(
                "No se encontró el tipo de issue '%s' en el proyecto %s",
                story_type,
                self.project_key,
            )
            return {}

        logger.debug(
            "ID del tipo de issue encontrado: %s para tipo '%s'",
            issue_type_id,
            story_type,
        )

        try:
            url = f"{self.base_url}/rest/api/3/issue/createmeta"
            params = {
                "projectKeys": self.project_key,
                "issuetypeIds": issue_type_id,  # Usar ID en lugar de nombre
                "expand": "projects.issuetypes.fields",
            }
            logger.debug("Consultando API: %s con params: %s", url, params)

            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            logger.debug(
                "Respuesta API recibida: %d proyectos encontrados",
                len(data.get("projects", [])),
            )

            if not data.get("projects") or len(data["projects"]) == 0:
                logger.warning(
                    "No se encontraron proyectos en createmeta para %s", story_type
                )
                return {}

            project = data["projects"][0]
            logger.debug(
                "Proyecto encontrado: %s (id: %s)",
                project.get("name", "N/A"),
                project.get("id", "N/A"),
            )

            if not project.get("issuetypes") or len(project["issuetypes"]) == 0:
                logger.warning("No se encontró tipo de issue %s", story_type)
                return {}

            issuetype = project["issuetypes"][0]
            logger.debug(
                "Tipo de issue encontrado: %s (id: %s)",
                issuetype.get("name", "N/A"),
                issuetype.get("id", "N/A"),
            )

            fields = issuetype.get("fields", {})
            logger.debug(
                "Analizando %d campos disponibles para %s", len(fields), story_type
            )

            required_fields = {}

            for field_id, field_info in fields.items():
                field_name = field_info.get("name", field_id)
                is_required = field_info.get("required", False)
                logger.debug(
                    "Campo %s (%s): obligatorio=%s", field_name, field_id, is_required
                )

                # Solo campos obligatorios, excluyendo los básicos que ya manejamos
                if is_required:
                    field_name_lower = field_name.lower()

                    # Excluir campos básicos que ya se manejan
                    if field_name_lower in [
                        "summary",
                        "description",
                        "project",
                        "issuetype",
                    ]:
                        logger.debug("Excluyendo campo básico: %s", field_name)
                        continue

                    # Obtener valor por defecto si existe
                    schema = field_info.get("schema", {})
                    allowed_values = field_info.get("allowedValues")
                    schema_type = schema.get("type", "string")

                    logger.debug(
                        "Procesando campo obligatorio %s: schema_type=%s, allowed_values=%s",
                        field_name,
                        schema_type,
                        len(allowed_values) if allowed_values else 0,
                    )

                    if allowed_values and len(allowed_values) > 0:
                        # Campo con valores predefinidos - usar el primero como default
                        default_value = allowed_values[0]
                        logger.debug(
                            "Campo %s tiene %d valores permitidos, usando: %s",
                            field_name,
                            len(allowed_values),
                            default_value,
                        )

                        if "id" in default_value:
                            required_fields[field_id] = {"id": default_value["id"]}
                        elif "value" in default_value:
                            required_fields[field_id] = {
                                "value": default_value["value"]
                            }
                        else:
                            required_fields[field_id] = default_value
                    else:
                        # Campo de texto libre - depende del schema type
                        logger.debug(
                            "Campo %s es de texto libre, tipo: %s",
                            field_name,
                            schema_type,
                        )
                        if schema_type == "string":
                            required_fields[field_id] = "default_value"
                        elif schema_type == "number":
                            required_fields[field_id] = 0
                        else:
                            required_fields[field_id] = "default_value"

            logger.debug(
                "Detección completada para %s: %d campos obligatorios encontrados",
                story_type,
                len(required_fields),
            )
            return required_fields

        except Exception as e:
            logger.error(
                "Error detectando campos obligatorios para historias %s: %s",
                story_type,
                str(e),
            )
            logger.debug("Excepción completa:", exc_info=True)
            return {}

    def _find_issue_type_id(self, issue_type_name: str) -> Optional[str]:
        """Encuentra el ID de un tipo de issue por nombre, manejando alias.

        Usa la misma lógica que validate_issue_type en jira_client.py para manejar
        casos donde el usuario especifica "Story" pero Jira tiene "Historia".

        Args:
            issue_type_name: Nombre del tipo de issue a buscar

        Returns:
            ID del tipo de issue o None si no se encuentra
        """
        logger.debug("Buscando ID para tipo de issue: %s", issue_type_name)
        try:
            url = f"{self.base_url}/rest/api/3/issue/createmeta"
            params = {"projectKeys": self.project_key, "expand": "projects.issuetypes"}
            logger.debug("Consultando todos los tipos disponibles: %s", url)

            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("projects") or len(data["projects"]) == 0:
                logger.debug("No se encontraron proyectos")
                return None

            project = data["projects"][0]
            all_issuetypes = project.get("issuetypes", [])
            logger.debug(
                "Proyecto encontrado con %d tipos de issue", len(all_issuetypes)
            )

            # Buscar el tipo de issue por nombre (insensible a mayúsculas)
            issue_type_lower = issue_type_name.lower()
            for issuetype in all_issuetypes:
                available_name = issuetype.get("name", "")
                issue_type_id = issuetype.get("id", "")
                logger.debug(
                    "Comparando '%s' con '%s' (id: %s)",
                    issue_type_name,
                    available_name,
                    issue_type_id,
                )

                if available_name.lower() == issue_type_lower:
                    logger.debug(
                        "Tipo de issue encontrado: %s -> id: %s",
                        available_name,
                        issue_type_id,
                    )
                    return issue_type_id

            # Si no se encuentra, mostrar tipos disponibles no-subtarea
            available_names = [
                it.get("name", "")
                for it in all_issuetypes
                if not it.get("subtask", False)
            ]
            logger.warning(
                "Tipo de issue '%s' no encontrado. Tipos estándar disponibles: %s",
                issue_type_name,
                available_names,
            )
            return None

        except Exception as e:
            logger.error(
                "Error buscando ID de tipo de issue %s: %s", issue_type_name, str(e)
            )
            return None

    def suggest_optimal_types(self) -> Dict[str, str]:
        """Sugiere tipos de issue óptimos basado en lo disponible en el proyecto.

        Returns:
            Dict con sugerencias para default_issue_type, subtask_issue_type, feature_issue_type
        """
        issue_types = self.get_available_issue_types()

        suggestions = {
            "default_issue_type": "Story",
            "subtask_issue_type": "Subtarea",
            "feature_issue_type": "Feature",
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
                    "projectKeys": self.project_key,
                    "issuetypeNames": issue_type,
                    "expand": "projects.issuetypes.fields",
                },
            )
            response.raise_for_status()
            data = response.json()

            if (
                data.get("projects")
                and len(data["projects"]) > 0
                and data["projects"][0].get("issuetypes")
                and len(data["projects"][0]["issuetypes"]) > 0
            ):

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
            "criteria",
            "criterio",
            "criterios",
            "acceptance",
            "aceptacion",
            "aceptación",
            "condition",
            "condicion",
            "condición",
            "requirement",
            "requisito",
            "test",
        ]

        for field_id, field_info in fields.items():
            # Solo campos personalizados (customfield_*)
            if not field_id.startswith("customfield_"):
                continue

            field_name = field_info.get("name", "").lower()
            field_type = field_info.get("schema", {}).get("type", "")

            # Filtrar por tipo de campo (text, rich text)
            valid_types = [
                "string",
                "any",
                "doc",
                "textarea",
            ]  # Tipos que pueden contener texto
            if field_type not in valid_types:
                continue

            # Buscar palabras clave en el nombre
            if any(keyword in field_name for keyword in criteria_keywords):
                candidates.append(
                    {
                        "id": field_id,
                        "name": field_info.get("name", field_id),
                        "type": field_type,
                    }
                )

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
