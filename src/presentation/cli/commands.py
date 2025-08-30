"""Comandos de la CLI separados del main."""
import json
import logging
import sys
from pathlib import Path

import click
import requests
from pydantic import ValidationError

from src.infrastructure.settings import Settings
from src.infrastructure.jira.metadata_detector import JiraMetadataDetector


def safe_init_settings():
    """Inicializa Settings con manejo de errores apropiado."""
    try:
        return Settings()
    except ValidationError as e:
        missing_fields = []
        for error in e.errors():
            if error['type'] == 'missing':
                field_name = error['loc'][0]
                env_var = field_name.upper()
                missing_fields.append((field_name, env_var))

        click.echo("[ERROR] Configuracion faltante.", err=True)

        # Preguntar si desea configurar interactivamente
        if click.confirm("¿Desea configurar los valores manualmente ahora?"):
            return _configure_interactively(missing_fields)

        click.echo("Por favor configure las siguientes variables de entorno:", err=True)
        for _, env_var in missing_fields:
            click.echo(f"  - {env_var}", err=True)
        click.echo("\nO cree un archivo .env con estas variables.", err=True)
        click.echo("Ejemplo: cp .env.example .env && nano .env", err=True)
        sys.exit(1)


def _configure_interactively(missing_fields):
    """Configura valores de forma interactiva y crea archivo .env."""
    click.echo("\n=== Configuración Interactiva ===")

    env_values = {}
    field_descriptions = {
        'jira_url': 'URL de Jira (ej: https://company.atlassian.net)',
        'jira_email': 'Email del usuario de Jira',
        'jira_api_token': 'API Token de Jira',
        'project_key': 'Clave del proyecto en Jira (ej: PROJ)'
    }

    # Primero obtener los campos básicos de conexión
    basic_fields = ['jira_url', 'jira_email', 'jira_api_token', 'project_key']
    for field_name, env_var in missing_fields:
        if field_name not in basic_fields:
            continue
            
        description = field_descriptions.get(field_name, f"Valor para {field_name}")

        if field_name == 'jira_api_token':
            # Para API token usar hide_input para ocultar el valor
            value = click.prompt(f"{description}", hide_input=True, type=str)
        else:
            value = click.prompt(f"{description}", type=str)

        env_values[env_var] = value

    # Intentar conectar con Jira para obtener configuración automática
    jira_config = _detect_jira_configuration(env_values)
    if jira_config:
        env_values.update(jira_config)
        click.echo("\n✓ Configuración automática desde Jira completada")
    else:
        click.echo("\n⚠ No se pudo conectar con Jira para configuración automática")
        click.echo("Se usarán valores por defecto")

    # Crear archivo .env con los valores proporcionados
    _create_env_file(env_values)

    click.echo("\n✓ Archivo .env creado exitosamente")
    click.echo("Reiniciando configuración...")

    try:
        return Settings()
    except ValidationError:
        click.echo("[ERROR] Error al cargar la nueva configuración.", err=True)
        sys.exit(1)


def _detect_jira_configuration(env_values):
    """Detecta configuración automáticamente desde Jira."""
    try:
        # Crear sesión de prueba
        session = requests.Session()
        session.auth = (env_values.get('JIRA_EMAIL', ''), env_values.get('JIRA_API_TOKEN', ''))
        session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

        base_url = env_values.get('JIRA_URL', '').rstrip('/')
        project_key = env_values.get('PROJECT_KEY', '')

        # Probar conexión primero
        response = session.get(f"{base_url}/rest/api/3/myself", timeout=10)
        if response.status_code != 200:
            return None

        # Validar proyecto
        response = session.get(f"{base_url}/rest/api/3/project/{project_key}", timeout=10)
        if response.status_code != 200:
            return None

        click.echo(f"\n🔍 Analizando configuración de proyecto {project_key}...")

        # Inicializar detector
        detector = JiraMetadataDetector(session, base_url, project_key)
        
        # Detectar tipos de issue óptimos
        type_suggestions = detector.suggest_optimal_types()
        click.echo(f"✓ Tipos de issue detectados: {type_suggestions['default_issue_type']}, {type_suggestions['subtask_issue_type']}, {type_suggestions['feature_issue_type']}")

        # Detectar campos de criterios de aceptación
        criteria_fields = detector.detect_acceptance_criteria_fields()
        selected_criteria_field = None
        if criteria_fields:
            click.echo(f"✓ {len(criteria_fields)} campo(s) de criterios encontrado(s)")
            if len(criteria_fields) == 1:
                selected_criteria_field = criteria_fields[0]['id']
                click.echo(f"  → Usando: {criteria_fields[0]['name']} ({selected_criteria_field})")
            else:
                click.echo("  Campos disponibles:")
                for i, field in enumerate(criteria_fields[:3]):
                    click.echo(f"    [{i+1}] {field['name']} ({field['id']})")
                choice = click.prompt("Seleccione campo de criterios (1 para el primero, 0 para ninguno)", 
                                    type=int, default=1)
                if 0 < choice <= len(criteria_fields):
                    selected_criteria_field = criteria_fields[choice-1]['id']

        # Detectar campos obligatorios para Features
        feature_required, _ = detector.detect_feature_required_fields(
            type_suggestions['feature_issue_type']
        )
        
        config = {
            'DEFAULT_ISSUE_TYPE': type_suggestions['default_issue_type'],
            'SUBTASK_ISSUE_TYPE': type_suggestions['subtask_issue_type'],
            'FEATURE_ISSUE_TYPE': type_suggestions['feature_issue_type']
        }

        if selected_criteria_field:
            config['ACCEPTANCE_CRITERIA_FIELD'] = selected_criteria_field

        if feature_required:
            config['FEATURE_REQUIRED_FIELDS'] = json.dumps(feature_required)
            click.echo(f"✓ {len(feature_required)} campo(s) obligatorio(s) detectado(s) para Features")
            
            # Mostrar información de los campos obligatorios detectados
            for field_id, field_value in list(feature_required.items())[:2]:  # Mostrar máximo 2
                if isinstance(field_value, dict) and 'id' in field_value:
                    click.echo(f"  → Campo {field_id}: id={field_value['id']}")

        return config

    except Exception as e:
        logging.debug("Error detectando configuración de Jira: %s", str(e))
        return None


def _create_env_file(env_values):
    """Crea archivo .env con los valores proporcionados."""
    env_content = [
        "# Configuración de Jira (generada automáticamente)",
        f"JIRA_URL={env_values.get('JIRA_URL', '')}",
        f"JIRA_EMAIL={env_values.get('JIRA_EMAIL', '')}",
        f"JIRA_API_TOKEN={env_values.get('JIRA_API_TOKEN', '')}",
        f"PROJECT_KEY={env_values.get('PROJECT_KEY', '')}",
    ]

    # Agregar campo de criterios si fue detectado
    if 'ACCEPTANCE_CRITERIA_FIELD' in env_values:
        env_content.append(f"ACCEPTANCE_CRITERIA_FIELD={env_values['ACCEPTANCE_CRITERIA_FIELD']}")

    env_content.extend([
        "",
        "# Configuración de tipos de issues (detectados automáticamente)",
        f"DEFAULT_ISSUE_TYPE={env_values.get('DEFAULT_ISSUE_TYPE', 'Story')}",
        f"SUBTASK_ISSUE_TYPE={env_values.get('SUBTASK_ISSUE_TYPE', 'Subtarea')}",
        f"FEATURE_ISSUE_TYPE={env_values.get('FEATURE_ISSUE_TYPE', 'Feature')}",
    ])

    # Agregar campos obligatorios de Features si fueron detectados
    if 'FEATURE_REQUIRED_FIELDS' in env_values:
        env_content.extend([
            "# Campos obligatorios para Features (detectados automáticamente)",
            f"FEATURE_REQUIRED_FIELDS={env_values['FEATURE_REQUIRED_FIELDS']}"
        ])

    env_content.extend([
        "",
        "# Configuración de la aplicación",
        "BATCH_SIZE=10",
        "DRY_RUN=false",
        "ROLLBACK_ON_SUBTASK_FAILURE=true",
        "",
        "# Configuración de directorios",
        "INPUT_DIRECTORY=entrada",
        "LOGS_DIRECTORY=logs",
        "PROCESSED_DIRECTORY=procesados"
    ])

    with open('.env', 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_content) + '\n')


def setup_logging(settings: Settings, level: str = "INFO"):
    """Configura el sistema de logging."""
    logs_dir = Path(settings.logs_directory)
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / 'jira_batch.log'

    # Configurar logging solo para archivo, no para consola
    # La salida a consola se maneja por OutputFormatter
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), encoding='utf-8')
        ],
        force=True  # Sobrescribir configuración existente
    )

    # Silenciar logs de requests en consola para reducir ruido
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


@click.command()
@click.option('--file', '-f', help='Archivo Excel o CSV específico con las historias')
@click.option('--project', '-p', help='Key del proyecto en Jira (ej: MYPROJ)')
@click.option('--batch-size', '-b', default=10, help='Tamaño del lote de procesamiento')
@click.option('--dry-run', is_flag=True, help='Modo de prueba sin crear issues')
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
def process_command(file, project, batch_size, dry_run, log_level):
    """Procesa archivo(s) y crea historias de usuario en Jira."""
    from src.presentation.formatters.output_formatter import OutputFormatter
    from src.application.use_cases.process_files import ProcessFilesUseCase

    # Configuración
    settings = safe_init_settings()
    if project:
        settings.project_key = project
    if dry_run:
        settings.dry_run = True
    settings.batch_size = batch_size

    setup_logging(settings, log_level)

    # Inicializar casos de uso y formatter
    process_use_case = ProcessFilesUseCase(settings)
    formatter = OutputFormatter()

    try:
        if file:
            files_to_process = [file]
        else:
            files_to_process = process_use_case.find_input_files()
            if not files_to_process:
                formatter.print_error(
                    f"No se encontraron archivos CSV/Excel en {settings.input_directory}"
                )
                return

        formatter.print_info(f"Iniciando procesamiento de {len(files_to_process)} archivo(s)...")

        results = process_use_case.execute(files_to_process)
        formatter.print_results(results)

    except Exception as e:
        formatter.print_error(f"Error inesperado: {str(e)}")
        formatter.print_info("Revisa el archivo de log para más detalles técnicos")
        sys.exit(1)



@click.command()
@click.option('--file', '-f', required=True, help='Archivo Excel o CSV a validar')
@click.option('--rows', '-r', default=5, help='Número de filas a mostrar en preview')
def validate_command(file, rows):
    """Valida el formato del archivo sin crear issues."""
    from src.presentation.formatters.output_formatter import OutputFormatter
    from src.application.use_cases.validate_file import ValidateFileUseCase

    # Usar safe_init_settings para configuración interactiva
    safe_init_settings()

    validate_use_case = ValidateFileUseCase()
    formatter = OutputFormatter()

    try:
        result = validate_use_case.execute(file, rows)
        formatter.print_validation_result(result)
    except Exception as e:
        formatter.print_error(f"Error: {str(e)}")
        sys.exit(1)


@click.command()
def test_connection_command():
    """Prueba la conexión con Jira usando la configuración actual."""
    from src.presentation.formatters.output_formatter import OutputFormatter
    from src.application.use_cases.test_connection import TestConnectionUseCase

    # Usar safe_init_settings para configuración interactiva
    safe_init_settings()

    test_use_case = TestConnectionUseCase()
    formatter = OutputFormatter()

    try:
        result = test_use_case.execute()
        formatter.print_connection_result(result)
    except Exception as e:
        formatter.print_error(f"Error: {str(e)}")
        sys.exit(1)


@click.command()
@click.option('--project', '-p', help='Key del proyecto (override settings)')
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
def diagnose_command(project, log_level):
    """Diagnostica configuración y campos obligatorios para historias y features."""
    from src.presentation.formatters.output_formatter import OutputFormatter
    from src.application.use_cases.diagnose_features import DiagnoseFeaturesUseCase

    # Configurar logging
    settings = safe_init_settings()
    if project:
        settings.project_key = project
    setup_logging(settings, log_level)

    diagnose_use_case = DiagnoseFeaturesUseCase()
    formatter = OutputFormatter()

    try:
        result = diagnose_use_case.execute(project)
        formatter.print_diagnose_result(result)
    except Exception as e:
        formatter.print_error(f"Error: {str(e)}")
        sys.exit(1)
