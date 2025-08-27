"""Comandos de la CLI separados del main."""
import logging
import sys
from pathlib import Path

import click
from pydantic import ValidationError

from src.infrastructure.settings import Settings


def safe_init_settings():
    """Inicializa Settings con manejo de errores apropiado."""
    try:
        return Settings()
    except ValidationError as e:
        missing_fields = []
        for error in e.errors():
            if error['type'] == 'missing':
                field_name = error['loc'][0]
                # Convertir de snake_case a UPPER_CASE para variables de entorno
                env_var = field_name.upper()
                missing_fields.append(env_var)

        click.echo("[ERROR] Configuracion faltante.", err=True)
        click.echo("Por favor configure las siguientes variables de entorno:", err=True)
        for field in missing_fields:
            click.echo(f"  - {field}", err=True)
        click.echo("\nO cree un archivo .env con estas variables.", err=True)
        click.echo("Ejemplo: cp .env.example .env && nano .env", err=True)
        sys.exit(1)


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
    """Diagnostica configuración y campos obligatorios para features."""
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
