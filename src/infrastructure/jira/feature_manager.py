"""Gestor de features/parents para historias de usuario."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from src.infrastructure.jira import utils as jira_utils
from src.infrastructure.settings import Settings

logger = logging.getLogger(__name__)


class FeatureManager:
    """Gestor responsable de la creación y gestión de features como parents de historias."""

    def __init__(self, settings: Settings, jira_session: requests.Session):
        self.settings = settings
        self.session = jira_session
        self.base_url = settings.jira_url.rstrip("/")
        # Cache para evitar crear features duplicadas en el mismo lote
        self._feature_cache: Dict[str, str] = (
            {}
        )  # normalized_description -> feature_key
        # Pattern para detectar keys de Jira (ej: PROJ-123)
        self._jira_key_pattern = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
        # Campo Epic Name (se detecta automáticamente)
        self._epic_name_field_id: Optional[str] = None

    def is_jira_key(self, text: str) -> bool:
        """Determina si el texto es una key de Jira válida.

        Args:
            text: Texto a evaluar

        Returns:
            True si es una key de Jira, False si es descripción de feature
        """
        if not text or not isinstance(text, str):
            return False
        return bool(self._jira_key_pattern.match(text.strip()))

    def _normalize_description(self, description: str) -> str:
        """Normaliza una descripción para comparaciones consistentes.

        Args:
            description: Descripción original

        Returns:
            Descripción normalizada
        """
        if not description:
            return ""

        # Convertir a minúsculas y limpiar espacios
        normalized = description.strip().lower()

        # Remover acentos y caracteres especiales comunes
        replacements = {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "ü": "u",
            "ñ": "n",
            "ç": "c",
        }
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)

        # Remover múltiples espacios y reemplazar con uno solo
        normalized = re.sub(r"\s+", " ", normalized)

        # Remover puntuación irrelevante al final
        normalized = re.sub(r"[.,:;!?]+$", "", normalized)

        # Remover caracteres especiales pero mantener espacios, guiones y letras/números
        normalized = re.sub(r"[^\w\s\-]", "", normalized)

        return normalized.strip()

    def validate_feature_type(self) -> bool:
        """Valida que el tipo de issue 'Feature' existe en el proyecto."""
        try:
            issue_types = self._get_issue_types()
            feature_names = [
                it["name"] for it in issue_types if not it.get("subtask", False)
            ]

            feature_type = getattr(self.settings, "feature_issue_type", "Feature")

            if feature_type in feature_names:
                return True

            logger.error(
                "Tipo de feature '%s' no encontrado. Disponibles: %s",
                feature_type,
                feature_names,
            )
            return False

        except Exception as e:
            logger.error("Error validando tipo de feature: %s", str(e))
            return False

    def get_required_fields_for_feature(self) -> Dict[str, Any]:
        """Obtiene campos obligatorios para crear features."""
        try:
            feature_type = getattr(self.settings, "feature_issue_type", "Feature")

            response = self.session.get(
                f"{self.base_url}/rest/api/3/issue/createmeta",
                params={
                    "projectKeys": self.settings.project_key,
                    "issuetypeNames": feature_type,
                    "expand": "projects.issuetypes.fields",
                },
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("projects") or len(data["projects"]) == 0:
                logger.warning(
                    "No se encontraron proyectos en createmeta para features"
                )
                return {}

            project = data["projects"][0]
            if not project.get("issuetypes") or len(project["issuetypes"]) == 0:
                logger.warning("No se encontró tipo de issue %s", feature_type)
                return {}

            issuetype = project["issuetypes"][0]
            fields = issuetype.get("fields", {})

            required_fields = {}
            epic_name_field_id = None

            for field_id, field_info in fields.items():
                field_name = field_info.get("name", field_id).lower()

                # Detectar campo Epic Name
                if "epic" in field_name and "name" in field_name:
                    epic_name_field_id = field_id
                    logger.info(
                        "Campo Epic Name detectado: %s (%s)",
                        field_info.get("name", field_id),
                        field_id,
                    )

                if field_info.get("required", False):
                    # Campos básicos ya manejados
                    if field_id in ["project", "summary", "issuetype", "description"]:
                        continue

                    field_name_display = field_info.get("name", field_id)
                    allowed_values = field_info.get("allowedValues", [])

                    logger.info(
                        "Campo obligatorio encontrado: %s (%s)",
                        field_name_display,
                        field_id,
                    )

                    # Mostrar todos los valores disponibles
                    if allowed_values and len(allowed_values) > 0:
                        logger.info("  Valores disponibles:")
                        for i, value in enumerate(
                            allowed_values[:5]
                        ):  # Mostrar máximo 5
                            value_display = value.get(
                                "value", value.get("name", str(value))
                            )
                            value_id = value.get("id", "N/A")
                            logger.info(
                                "    [%s] %s (id: %s)", i + 1, value_display, value_id
                            )

                        if len(allowed_values) > 5:
                            logger.info("    ... y %d más", len(allowed_values) - 5)

                    # Sugerir valor por defecto si hay opciones
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

                        default_display = default_value.get(
                            "value", default_value.get("name", str(default_value))
                        )
                        logger.info("  Valor sugerido por defecto: %s", default_display)

            # Guardar el Epic Name field ID para uso posterior
            if epic_name_field_id:
                self._epic_name_field_id = epic_name_field_id
            else:
                logger.warning(
                    "No se encontró campo Epic Name en el tipo de issue %s",
                    feature_type,
                )
                self._epic_name_field_id = None

            return required_fields

        except Exception as e:
            logger.error(
                "Error obteniendo campos obligatorios para features: %s", str(e)
            )
            return {}

    def validate_existing_issue(self, issue_key: str) -> bool:
        """Valida que un issue existente (Epic/Feature) existe en Jira."""
        return jira_utils.validate_issue_exists(self.session, self.base_url, issue_key)

    def _search_existing_features(self, normalized_description: str) -> Optional[str]:
        """Busca features existentes en Jira con descripción similar.

        Args:
            normalized_description: Descripción normalizada a buscar

        Returns:
            Key de la feature encontrada o None si no existe
        """
        try:
            # Generar título esperado para la búsqueda
            expected_title = self._generate_feature_title(normalized_description)

            # Buscar por título similar usando JQL
            # Escapar comillas en el título para JQL
            escaped_title = expected_title.replace('"', '\\"')

            feature_type = getattr(self.settings, "feature_issue_type", "Feature")
            jql = f'project = "{self.settings.project_key}" AND issuetype = "{feature_type}" AND summary ~ "{escaped_title}"'

            params = {
                "jql": jql,
                "maxResults": 5,  # Limitar resultados
                "fields": "key,summary,description",
            }

            response = self.session.get(
                f"{self.base_url}/rest/api/3/search", params=params
            )
            response.raise_for_status()

            data = response.json()
            issues = data.get("issues", [])

            if not issues:
                return None

            # Verificar si alguna feature tiene descripción similar
            for issue in issues:
                issue_key = issue["key"]
                issue_summary = issue["fields"].get("summary", "")
                issue_description = ""

                # Extraer descripción si existe
                desc_field = issue["fields"].get("description")
                if desc_field and isinstance(desc_field, dict):
                    issue_description = self._extract_text_from_description(desc_field)

                # Comparar descripción normalizada
                issue_normalized = self._normalize_description(issue_description)

                if issue_normalized == normalized_description:
                    logger.info(
                        "Encontrada feature existente: %s - %s",
                        issue_key,
                        issue_summary,
                    )
                    return issue_key

                # También comparar por título normalizado como fallback
                title_normalized = self._normalize_description(issue_summary)
                expected_normalized = self._normalize_description(expected_title)

                if title_normalized == expected_normalized:
                    logger.info(
                        "Encontrada feature existente por título: %s - %s",
                        issue_key,
                        issue_summary,
                    )
                    return issue_key

            return None

        except Exception as e:
            logger.warning("Error buscando features existentes: %s", str(e))
            # No fallar completamente, solo continuar sin encontrar duplicados
            return None

    def _extract_text_from_description(self, description_field: Dict) -> str:
        """Extrae texto plano de un campo de descripción de Jira."""
        try:
            if not isinstance(description_field, dict):
                return str(description_field) if description_field else ""

            content = description_field.get("content", [])
            if not content:
                return ""

            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "paragraph":
                    paragraph_content = block.get("content", [])
                    for item in paragraph_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))

            return " ".join(text_parts).strip()

        except Exception as e:
            logger.warning("Error extrayendo texto de descripción: %s", str(e))
            return ""

    def create_feature(self, description: str) -> Optional[str]:
        """Crea una nueva feature en Jira.

        Args:
            description: Descripción de la feature

        Returns:
            Key de la feature creada o None si falla
        """
        if self.settings.dry_run:
            logger.info("[DRY RUN] Creando feature: %s", description[:50] + "...")
            return "DRY-FEATURE-123"

        try:
            # Generar título a partir de la descripción
            title = self._generate_feature_title(description)

            # Preparar descripción formateada
            description_content = [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}],
                }
            ]

            # Crear payload para la feature
            feature_data = {
                "fields": {
                    "project": {"key": self.settings.project_key},
                    "summary": title,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": description_content,
                    },
                    "issuetype": {
                        "name": getattr(self.settings, "feature_issue_type", "Feature")
                    },
                }
            }

            # Agregar campos obligatorios adicionales
            additional_fields = {}

            # Primero intentar usar configuración manual
            if self.settings.feature_required_fields:
                try:
                    additional_fields = json.loads(
                        self.settings.feature_required_fields
                    )
                    logger.debug(
                        "Campos adicionales de configuración: %s", additional_fields
                    )
                except Exception as e:
                    logger.warning(
                        "Error parseando feature_required_fields: %s", str(e)
                    )

            # Si no hay configuración manual, obtener automáticamente
            if not additional_fields:
                additional_fields = self.get_required_fields_for_feature()
                logger.debug(
                    "Campos obligatorios detectados automáticamente: %s",
                    additional_fields,
                )

            # Si no se ha detectado el Epic Name aún, intentar detectarlo
            elif self._epic_name_field_id is None:
                self.get_required_fields_for_feature()  # Ejecutar para detectar Epic Name

            # Aplicar campos adicionales
            if additional_fields:
                feature_data["fields"].update(additional_fields)

            # Asignar Epic Name si se detectó el campo
            if self._epic_name_field_id:
                feature_data["fields"][self._epic_name_field_id] = title
                logger.debug(
                    "Asignando Epic Name: %s = %s", self._epic_name_field_id, title
                )

            # Crear feature
            response = self.session.post(
                f"{self.base_url}/rest/api/3/issue", data=json.dumps(feature_data)
            )
            response.raise_for_status()

            result_data = response.json()
            feature_key = result_data["key"]

            logger.info("Feature creada exitosamente: %s - %s", feature_key, title)
            return feature_key

        except requests.exceptions.HTTPError as e:
            error_msg = f"Error HTTP creando feature: {str(e)}"
            jira_utils.handle_http_error(e, logger)
            logger.error(error_msg)
            return None

        except Exception as e:
            error_msg = f"Error creando feature: {str(e)}"
            logger.error(error_msg)
            return None

    def get_or_create_parent(self, parent_text: str) -> Tuple[Optional[str], bool]:
        """Obtiene o crea el parent apropiado para una historia de usuario.

        Args:
            parent_text: Texto del parent (key existente o descripción de feature)

        Returns:
            Tupla con (parent_key, was_created)
            - parent_key: Key del parent a usar, None si falla
            - was_created: True si se creó una nueva feature, False si se usó existente
        """
        if not parent_text or not parent_text.strip():
            return None, False

        parent_text = parent_text.strip()

        # Caso 1: Es una key de Jira existente
        if self.is_jira_key(parent_text):
            if self.validate_existing_issue(parent_text):
                logger.debug("Usando parent existente: %s", parent_text)
                return parent_text, False
            else:
                # Key no existe - FALLAR en lugar de crear feature
                logger.error(
                    "Key de Jira %s no existe y no se puede crear feature con formato de key",
                    parent_text,
                )
                return None, False

        # Caso 2: Es descripción de feature (o key inexistente)
        normalized_desc = self._normalize_description(parent_text)

        # Verificar cache local primero
        if normalized_desc in self._feature_cache:
            cached_key = self._feature_cache[normalized_desc]
            logger.debug(
                "Usando feature cacheada: %s para '%s'", cached_key, parent_text[:50]
            )
            return cached_key, False

        # Buscar en Jira features existentes
        existing_key = self._search_existing_features(normalized_desc)
        if existing_key:
            # Guardar en cache para futuras referencias
            self._feature_cache[normalized_desc] = existing_key
            logger.info(
                "Reutilizando feature existente: %s para descripción: %s",
                existing_key,
                parent_text[:50] + "...",
            )
            return existing_key, False

        # Crear nueva feature
        feature_key = self.create_feature(parent_text)
        if feature_key:
            # Guardar en cache
            self._feature_cache[normalized_desc] = feature_key
            logger.info(
                "Feature creada y cacheada: %s para descripción: %s",
                feature_key,
                parent_text[:50] + "...",
            )
            return feature_key, True

        logger.error("Falló creación de feature para: %s", parent_text[:50])
        return None, False

    def _generate_feature_title(self, description: str, max_length: int = 120) -> str:
        """Genera un título para la feature basado en su descripción.

        Args:
            description: Descripción completa de la feature
            max_length: Longitud máxima del título

        Returns:
            Título generado para la feature
        """
        if not description:
            return "Feature sin título"

        # Limpiar y tomar primeras palabras
        clean_desc = description.strip()

        # Si es corto, usar completo
        if len(clean_desc) <= max_length:
            return clean_desc

        # Tomar primeras palabras hasta el límite
        words = clean_desc.split()
        title = ""
        for word in words:
            if len(title + word + " ") <= max_length - 3:  # -3 para "..."
                title += word + " "
            else:
                break

        title = title.strip()
        if title:
            return title + "..."
        else:
            # Fallback: cortar en caracteres si no hay palabras válidas
            if len(clean_desc) > max_length:
                return clean_desc[: max_length - 3] + "..."
            return clean_desc

    def _get_issue_types(self) -> List[Dict[str, Any]]:
        """Obtiene los tipos de issue disponibles en el proyecto."""
        return jira_utils.get_issue_types(
            self.session, self.base_url, self.settings.project_key
        )

    def clear_cache(self) -> None:
        """Limpia el cache de features creadas."""
        self._feature_cache.clear()
        logger.debug("Cache de features limpiado")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache de features."""
        return {
            "cached_features": len(self._feature_cache),
            "features": list(self._feature_cache.items()),
        }
