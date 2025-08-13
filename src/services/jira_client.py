import requests
import json
import logging
from typing import Optional, Dict, Any, List
from src.models.jira_models import UserStory, ProcessResult
from src.config.settings import Settings

logger = logging.getLogger(__name__)


class JiraClient:
    """Cliente para interactuar con la API de Jira."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.jira_url.rstrip('/')
        self.auth = (settings.jira_email, settings.jira_api_token)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self) -> bool:
        """Prueba la conexión con Jira."""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/3/myself")
            response.raise_for_status()
            logger.info("Conexión con Jira exitosa")
            return True
        except Exception as e:
            logger.error(f"Error de conexión con Jira: {str(e)}")
            return False
    
    def validate_project(self, project_key: str) -> bool:
        """Valida que el proyecto existe en Jira."""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/3/project/{project_key}")
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Proyecto {project_key} no encontrado")
                return False
            raise
    
    def validate_subtask_issue_type(self, project_key: str) -> bool:
        """Valida que el tipo de issue 'Sub-task' existe en el proyecto."""
        try:
            issue_types = self.get_issue_types()
            subtask_names = [it["name"] for it in issue_types if it.get("subtask", False)]
            
            if self.settings.subtask_issue_type in subtask_names:
                return True
            else:
                logger.error(f"Tipo de subtarea '{self.settings.subtask_issue_type}' no encontrado. Disponibles: {subtask_names}")
                return False
                
        except Exception as e:
            logger.error(f"Error validando tipo de subtarea: {str(e)}")
            return False
    
    def validate_parent_issue(self, issue_key: str) -> bool:
        """Valida que el issue padre (Epic/Feature) existe."""
        if not issue_key:
            return True
        
        try:
            response = self.session.get(f"{self.base_url}/rest/api/3/issue/{issue_key}")
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Issue padre {issue_key} no encontrado")
                return False
            raise
    
    def create_user_story(self, story: UserStory, row_number: int = None) -> ProcessResult:
        """Crea una historia de usuario en Jira."""
        if self.settings.dry_run:
            logger.info(f"[DRY RUN] Creando historia: {story.titulo}")
            return ProcessResult(
                success=True,
                jira_key="DRY-RUN-123",
                row_number=row_number
            )
        
        try:
            # Validar parent si existe
            if story.parent and not self.validate_parent_issue(story.parent):
                return ProcessResult(
                    success=False,
                    error_message=f"Issue padre {story.parent} no existe",
                    row_number=row_number
                )
            
            # Preparar descripción con criterios de aceptación si no hay campo personalizado
            description_content = [{
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": story.descripcion}
                ]
            }]
            
            # Si no hay campo personalizado para criterios, agregarlos a la descripción
            if not self.settings.acceptance_criteria_field and story.criterio_aceptacion:
                # Agregar separador
                description_content.append({
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "\n--- Criterios de Aceptación ---"}
                    ]
                })
                
                # Dividir criterios por ';' y crear lista formateada
                criterios = [criterio.strip() for criterio in story.criterio_aceptacion.split(';') if criterio.strip()]
                
                if criterios and len(criterios) > 1:
                    # Múltiples criterios separados por ';'
                    for criterio in criterios:
                        description_content.append({
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": f"• {criterio}"}
                            ]
                        })
                else:
                    # Un solo criterio o sin separador ';'
                    description_content.append({
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": story.criterio_aceptacion}
                        ]
                    })
            
            # Crear payload para la historia
            issue_data = {
                "fields": {
                    "project": {"key": self.settings.project_key},
                    "summary": story.titulo,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": description_content
                    },
                    "issuetype": {"name": self.settings.default_issue_type}
                }
            }
            
            # Agregar criterios de aceptación al campo personalizado si está configurado
            if self.settings.acceptance_criteria_field:
                # Dividir criterios por ';' y crear una lista formateada
                criterios = [criterio.strip() for criterio in story.criterio_aceptacion.split(';') if criterio.strip()]
                
                # Crear contenido con cada criterio en un párrafo separado
                content_paragraphs = []
                for i, criterio in enumerate(criterios, 1):
                    content_paragraphs.append({
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": f"• {criterio}"}
                        ]
                    })
                
                # Si no hay criterios separados por ';', usar el texto completo
                if not content_paragraphs:
                    content_paragraphs = [{
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": story.criterio_aceptacion}
                        ]
                    }]
                
                issue_data["fields"][self.settings.acceptance_criteria_field] = {
                    "type": "doc",
                    "version": 1,
                    "content": content_paragraphs
                }
            
            # Vincular con parent si existe
            if story.parent:
                issue_data["fields"]["parent"] = {"key": story.parent}
            
            # Crear historia
            response = self.session.post(
                f"{self.base_url}/rest/api/3/issue",
                data=json.dumps(issue_data)
            )
            response.raise_for_status()
            
            result_data = response.json()
            story_key = result_data["key"]
            
            logger.info(f"Historia creada exitosamente: {story_key}")
            
            # Crear subtareas si existen
            subtasks_created = 0
            subtasks_failed = 0
            subtask_errors = []
            
            if story.subtareas:
                subtasks_created, subtasks_failed, subtask_errors = self._create_subtasks(story_key, story.subtareas)
                
                # Rollback si está habilitado y fallaron todas las subtareas
                if (self.settings.rollback_on_subtask_failure and 
                    subtasks_failed > 0 and 
                    subtasks_created == 0 and 
                    len(story.subtareas) > 0):
                    
                    try:
                        self._delete_issue(story_key)
                        logger.warning(f"Historia {story_key} eliminada debido a fallo completo en subtareas")
                        return ProcessResult(
                            success=False,
                            error_message=f"Historia eliminada: fallaron todas las subtareas ({subtasks_failed}/{len(story.subtareas)})",
                            row_number=row_number,
                            subtasks_created=0,
                            subtasks_failed=subtasks_failed,
                            subtask_errors=subtask_errors
                        )
                    except Exception as e:
                        logger.error(f"Error eliminando historia {story_key}: {str(e)}")
            
            return ProcessResult(
                success=True,
                jira_key=story_key,
                row_number=row_number,
                subtasks_created=subtasks_created,
                subtasks_failed=subtasks_failed,
                subtask_errors=subtask_errors if subtask_errors else None
            )
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Error HTTP creando historia: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Detalles del error: {json.dumps(error_details, indent=2)}")
                    logger.error(f"Payload enviado: {json.dumps(issue_data, indent=2)}")
                    error_msg += f" - Detalles: {error_details}"
                except:
                    logger.error(f"Response text: {e.response.text}")
                    logger.error(f"Payload enviado: {json.dumps(issue_data, indent=2)}")
            logger.error(error_msg)
            return ProcessResult(
                success=False,
                error_message=error_msg,
                row_number=row_number
            )
        except Exception as e:
            error_msg = f"Error creando historia: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Payload enviado: {json.dumps(issue_data, indent=2)}")
            return ProcessResult(
                success=False,
                error_message=error_msg,
                row_number=row_number
            )
    
    def _create_subtasks(self, parent_key: str, subtasks: List[str]) -> tuple[int, int, List[str]]:
        """Crea subtareas para una historia de usuario.
        
        Returns:
            tuple: (subtasks_created, subtasks_failed, error_messages)
        """
        created = 0
        failed = 0
        errors = []
        
        # Validar subtareas antes de crearlas
        valid_subtasks = [s.strip() for s in subtasks if s.strip() and len(s.strip()) <= 255]
        invalid_subtasks = [s for s in subtasks if not s.strip() or len(s.strip()) > 255]
        
        # Reportar subtareas inválidas
        for invalid in invalid_subtasks:
            error_msg = f"Subtarea inválida (vacía o >255 caracteres): '{invalid}'"
            errors.append(error_msg)
            logger.warning(error_msg)
            failed += 1
        
        for subtask_summary in valid_subtasks:
            try:
                subtask_data = {
                    "fields": {
                        "project": {"key": self.settings.project_key},
                        "summary": subtask_summary,
                        "issuetype": {"name": self.settings.subtask_issue_type},
                        "parent": {"key": parent_key}
                    }
                }
                
                response = self.session.post(
                    f"{self.base_url}/rest/api/3/issue",
                    data=json.dumps(subtask_data)
                )
                response.raise_for_status()
                
                result_data = response.json()
                logger.info(f"Subtarea creada: {result_data['key']} para {parent_key}")
                created += 1
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"Error HTTP creando subtarea '{subtask_summary}': {str(e)}"
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_details = e.response.json()
                        error_msg += f" - {error_details}"
                    except:
                        pass
                errors.append(error_msg)
                logger.error(error_msg)
                failed += 1
                
            except Exception as e:
                error_msg = f"Error creando subtarea '{subtask_summary}': {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                failed += 1
        
        return created, failed, errors
    
    def _delete_issue(self, issue_key: str) -> bool:
        """Elimina un issue de Jira."""
        try:
            response = self.session.delete(f"{self.base_url}/rest/api/3/issue/{issue_key}")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error eliminando issue {issue_key}: {str(e)}")
            return False
    
    def get_issue_types(self) -> List[Dict[str, Any]]:
        """Obtiene los tipos de issue disponibles en el proyecto."""
        try:
            # Usar el endpoint correcto para obtener metadata del proyecto
            response = self.session.get(
                f"{self.base_url}/rest/api/3/issue/createmeta?projectKeys={self.settings.project_key}&expand=projects.issuetypes"
            )
            response.raise_for_status()
            data = response.json()
            
            # Extraer tipos de issue del proyecto
            if data.get("projects") and len(data["projects"]) > 0:
                return data["projects"][0].get("issuetypes", [])
            else:
                logger.warning("No se encontraron proyectos en createmeta")
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo tipos de issue: {str(e)}")
            return []