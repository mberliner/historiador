"""Aplicación principal para importar historias de usuario a Jira desde CSV/Excel."""
import glob
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List

import click

# Agregar el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position
from src.config.settings import Settings
from src.services.file_processor import FileProcessor
from src.services.jira_client import JiraClient
from src.models.jira_models import BatchResult, ProcessResult


def setup_logging(settings: Settings, level: str = "INFO"):
    """Configura el sistema de logging.

    Args:
        settings: Configuración de la aplicación
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    """
    # Crear directorio de logs si no existe
    logs_dir = Path(settings.logs_directory)
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / 'jira_batch.log'

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_file), encoding='utf-8')
        ]
    )


def move_file_to_processed(file_path: str, settings: Settings) -> None:
    """Mueve archivo procesado al directorio de procesados.

    Args:
        file_path: Ruta del archivo a mover
        settings: Configuración de la aplicación
    """
    processed_dir = Path(settings.processed_directory)
    processed_dir.mkdir(exist_ok=True)

    source_path = Path(file_path)
    dest_path = processed_dir / source_path.name

    # Si ya existe el archivo, agregar timestamp
    if dest_path.exists():
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = source_path.stem
        suffix = source_path.suffix
        dest_path = processed_dir / f"{stem}_{timestamp}{suffix}"

    shutil.move(str(source_path), str(dest_path))
    logging.getLogger(__name__).info("Archivo movido a: %s", dest_path)


def find_input_files(settings: Settings) -> List[str]:
    """Encuentra todos los archivos CSV y Excel en el directorio de entrada.

    Args:
        settings: Configuración de la aplicación

    Returns:
        Lista de rutas de archivos encontrados
    """
    input_dir = Path(settings.input_directory)

    # Crear directorio de entrada si no existe
    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)
        logging.getLogger(__name__).info("Directorio de entrada creado: %s", input_dir)
        return []

    patterns = ['*.csv', '*.xlsx', '*.xls']
    files = []

    for pattern in patterns:
        files.extend(glob.glob(str(input_dir / pattern)))

    return sorted(files)


@click.group(invoke_without_command=True)
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
@click.option('--file', '-f', help='Archivo Excel o CSV específico con las historias')
@click.option('--project', '-p', help='Key del proyecto en Jira (ej: MYPROJ)')
@click.option('--batch-size', '-b', default=10, help='Tamaño del lote de procesamiento')
@click.option('--dry-run', is_flag=True, help='Modo de prueba sin crear issues')
@click.pass_context
def cli(ctx, log_level, file, project, batch_size, dry_run):
    """Jira Batch Importer - Crea historias de usuario desde archivos Excel/CSV.

    Args:
        ctx: Contexto de click
        log_level: Nivel de logging
        file: Archivo específico a procesar
        project: Clave del proyecto en Jira
        batch_size: Tamaño del lote de procesamiento
        dry_run: Modo de prueba sin crear issues
    """
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level

    # Si no se especifica comando, ejecutar process por defecto
    if ctx.invoked_subcommand is None:
        ctx.invoke(process, file=file, project=project, batch_size=batch_size, dry_run=dry_run)


@cli.command()
@click.option('--file', '-f', help='Archivo Excel o CSV específico con las historias')
@click.option('--project', '-p', help='Key del proyecto en Jira (ej: MYPROJ)')
@click.option('--batch-size', '-b', default=10, help='Tamaño del lote de procesamiento')
@click.option('--dry-run', is_flag=True, help='Modo de prueba sin crear issues')
@click.pass_context
def process(ctx, file, project, batch_size, dry_run):
    """Procesa archivo(s) y crea historias de usuario en Jira.

    Args:
        ctx: Contexto de click
        file: Archivo específico a procesar
        project: Clave del proyecto en Jira
        batch_size: Tamaño del lote de procesamiento
        dry_run: Modo de prueba sin crear issues
    """
    # Cargar configuración
    settings = Settings()
    if project:
        settings.project_key = project
    if dry_run:
        settings.dry_run = True
    settings.batch_size = batch_size

    # Configurar logging
    setup_logging(settings, ctx.obj['log_level'])
    logger = logging.getLogger(__name__)

    try:
        # Determinar archivos a procesar
        if file:
            files_to_process = [file]
            logger.info("Procesando archivo específico: %s", file)
        else:
            files_to_process = find_input_files(settings)
            if not files_to_process:
                click.echo(f"No se encontraron archivos CSV/Excel en {settings.input_directory}")
                return
            logger.info("Procesando %d archivos automáticamente", len(files_to_process))

        logger.info("Proyecto: %s", settings.project_key)
        logger.info("Modo dry-run: %s", settings.dry_run)

        # Inicializar servicios
        file_processor = FileProcessor()
        jira_client = JiraClient(settings)

        # Validar conexión
        if not settings.dry_run:
            if not jira_client.test_connection():
                click.echo("Error: No se pudo conectar a Jira", err=True)
                sys.exit(1)

            if not jira_client.validate_project(settings.project_key):
                click.echo(f"Error: Proyecto {settings.project_key} no encontrado", err=True)
                sys.exit(1)

            # Validar tipo de subtarea si hay archivos con subtareas
            has_subtasks = any(
                any(story.subtareas for story in file_processor.process_file(f))
                for f in files_to_process
            )

            subtask_valid = jira_client.validate_subtask_issue_type(settings.project_key)
            if has_subtasks and not subtask_valid:
                click.echo(f"Error: Tipo de subtarea '{settings.subtask_issue_type}' no válido", err=True)
                sys.exit(1)

            # Verificar si hay parents y validar tipo de feature
            has_parents = any(
                any(story.parent for story in file_processor.process_file(f))
                for f in files_to_process
            )

            feature_valid = jira_client.validate_feature_issue_type()
            if has_parents and not feature_valid:
                click.echo(f"Error: Tipo de feature '{settings.feature_issue_type}' no válido", err=True)
                sys.exit(1)

        # Procesar cada archivo
        total_files = len(files_to_process)
        overall_results = []

        for file_index, current_file in enumerate(files_to_process, 1):
            click.echo(f"\n{'='*60}")
            click.echo(f"PROCESANDO ARCHIVO {file_index}/{total_files}: {Path(current_file).name}")
            click.echo(f"{'='*60}")

            try:
                # Procesar archivo
                results: List[ProcessResult] = []
                batch_count = 0

                click.echo(f"Procesando historias en lotes de {settings.batch_size}...")

                for row_number, story in enumerate(file_processor.process_file(current_file), start=1):
                    result = jira_client.create_user_story(story, row_number)
                    results.append(result)

                    if result.success:
                        click.echo(f"[OK] Fila {row_number}: {result.jira_key} - {story.titulo}")

                        # Mostrar información de feature si se creó/utilizó
                        if result.feature_info:
                            if result.feature_info.was_created:
                                click.echo(f"    + Feature creada: {result.feature_info.feature_key}")
                            else:
                                click.echo(f"    = Parent utilizado: {result.feature_info.feature_key}")

                        if result.subtasks_created > 0:
                            click.echo(f"    + {result.subtasks_created} subtarea(s) creada(s)")
                        if result.subtasks_failed > 0:
                            click.echo(f"    - {result.subtasks_failed} subtarea(s) fallaron", err=True)
                    else:
                        click.echo(f"[ERROR] Fila {row_number}: {result.error_message}", err=True)

                    batch_count += 1
                    if batch_count >= settings.batch_size:
                        click.echo(f"Lote completado. Procesadas {len(results)} historias...")
                        batch_count = 0

                # Mostrar resumen del archivo
                batch_result = BatchResult(
                    total_processed=len(results),
                    successful=sum(1 for r in results if r.success),
                    failed=sum(1 for r in results if not r.success),
                    results=results
                )

                click.echo(f"\nRESUMEN DE {Path(current_file).name}:")
                click.echo(f"Total procesadas: {batch_result.total_processed}")
                click.echo(f"Exitosas: {batch_result.successful}")
                click.echo(f"Fallidas: {batch_result.failed}")

                if batch_result.failed > 0:
                    click.echo("Errores encontrados:")
                    for result in results:
                        if not result.success:
                            click.echo(f"  Fila {result.row_number}: {result.error_message}")

                # Mostrar errores de subtareas para historias exitosas
                for result in results:
                    if result.success and result.subtask_errors:
                        click.echo(f"Errores de subtareas en fila {result.row_number} ({result.jira_key}):")
                        for error in result.subtask_errors:
                            click.echo(f"  • {error}")

                overall_results.extend(results)
                logger.info("Archivo completado: %d/%d exitosas", batch_result.successful, batch_result.total_processed)

                # Mover archivo a procesados si el procesamiento fue exitoso
                if batch_result.successful > 0:
                    move_file_to_processed(current_file, settings)
                    click.echo(f"[OK] Archivo movido a directorio de procesados")
                else:
                    logger.warning("Archivo no movido debido a fallos: %s", current_file)
                    click.echo(f"[WARNING] Archivo no movido debido a fallos")

            except Exception as e:
                logger.error("Error procesando archivo %s: %s", current_file, str(e))
                click.echo(f"[ERROR] Error en archivo {Path(current_file).name}: {str(e)}", err=True)
                continue

        # Resumen general
        if total_files > 1:
            overall_batch_result = BatchResult(
                total_processed=len(overall_results),
                successful=sum(1 for r in overall_results if r.success),
                failed=sum(1 for r in overall_results if not r.success),
                results=overall_results
            )

            click.echo(f"\n{'='*60}")
            click.echo("RESUMEN GENERAL")
            click.echo(f"{'='*60}")
            click.echo(f"Archivos procesados: {total_files}")
            click.echo(f"Total historias procesadas: {overall_batch_result.total_processed}")
            click.echo(f"Total exitosas: {overall_batch_result.successful}")
            click.echo(f"Total fallidas: {overall_batch_result.failed}")

            logger.info("Procesamiento general completado. %d/%d exitosas en %d archivos", 
                        overall_batch_result.successful, overall_batch_result.total_processed, total_files)

    except Exception as e:
        logger.error("Error durante el procesamiento: %s", str(e))
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--file', '-f', required=True, help='Archivo Excel o CSV a validar')
@click.option('--rows', '-r', default=5, help='Número de filas a mostrar en preview')
def validate(file, rows):
    """Valida el formato del archivo sin crear issues.

    Args:
        file: Ruta del archivo a validar
        rows: Número de filas a mostrar en preview
    """
    logger = logging.getLogger(__name__)

    try:
        file_processor = FileProcessor()

        # Mostrar preview
        click.echo(f"Preview de {file} (primeras {rows} filas):")
        click.echo("="*60)

        df = file_processor.preview_file(file, rows)
        click.echo(df.to_string(index=False))

        # Validar estructura
        click.echo("\n" + "="*60)
        click.echo("VALIDACIÓN DE ESTRUCTURA")
        click.echo("="*60)

        # Procesar todas las filas para validar datos
        stories = list(file_processor.process_file(file))

        click.echo(f"[OK] Archivo válido")
        click.echo(f"[OK] {len(stories)} historias encontradas")
        click.echo(f"[OK] Todas las filas tienen formato correcto")

        # Mostrar estadísticas
        with_subtasks = sum(1 for s in stories if s.subtareas)
        with_parent = sum(1 for s in stories if s.parent)
        total_subtasks = sum(len(s.subtareas) if s.subtareas else 0 for s in stories)

        click.echo(f"  - Con subtareas: {with_subtasks}")
        click.echo(f"  - Total subtareas: {total_subtasks}")
        click.echo(f"  - Con parent: {with_parent}")

        # Validar subtareas
        invalid_subtasks = 0
        for story in stories:
            if story.subtareas:
                invalid_subtasks += sum(1 for s in story.subtareas if not s.strip() or len(s.strip()) > 255)

        if invalid_subtasks > 0:
            click.echo(f"  - Subtareas inválidas: {invalid_subtasks}", err=True)
            click.echo("    (vacías o >255 caracteres)", err=True)

    except Exception as e:
        logger.error("Error en validación: %s", str(e))
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def test_connection():
    """Prueba la conexión con Jira usando la configuración actual."""
    try:
        settings = Settings()
        jira_client = JiraClient(settings)

        click.echo("Probando conexión con Jira...")

        if jira_client.test_connection():
            click.echo("[OK] Conexión exitosa")

            if jira_client.validate_project(settings.project_key):
                click.echo(f"[OK] Proyecto {settings.project_key} encontrado")
            else:
                click.echo(f"[ERROR] Proyecto {settings.project_key} no encontrado", err=True)
        else:
            click.echo("[ERROR] Error de conexión", err=True)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--project', '-p', help='Key del proyecto (override settings)')
def diagnose(project):
    """Diagnostica configuración y campos obligatorios para features.

    Args:
        project: Key del proyecto a diagnosticar
    """
    logger = logging.getLogger(__name__)

    try:
        settings = Settings()
        if project:
            settings.project_key = project

        setup_logging(settings)
        logger.info("Iniciando diagnóstico de features para proyecto: %s", settings.project_key)

        click.echo("="*60)
        click.echo("DIAGNÓSTICO DE CONFIGURACIÓN PARA FEATURES")
        click.echo("="*60)

        # Probar conexión
        jira_client = JiraClient(settings)
        if not jira_client.test_connection():
            click.echo("Error de conexión con Jira", err=True)
            sys.exit(1)

        click.echo("+ Conexión con Jira exitosa")

        # Validar proyecto
        if not jira_client.validate_project(settings.project_key):
            click.echo(f"Error: Proyecto {settings.project_key} no encontrado", err=True)
            sys.exit(1)

        click.echo(f"+ Proyecto {settings.project_key} válido")

        # Validar tipo de feature
        if not jira_client.validate_feature_issue_type():
            click.echo(f"Error: Tipo de feature '{settings.feature_issue_type}' no válido", err=True)
            sys.exit(1)

        click.echo(f"+ Tipo de feature '{settings.feature_issue_type}' válido")

        # Obtener campos obligatorios
        click.echo(f"\nAnalizando campos obligatorios para '{settings.feature_issue_type}'...")
        required_fields = jira_client.feature_manager.get_required_fields_for_feature()

        if required_fields:
            click.echo(f"\nCAMPOS OBLIGATORIOS ENCONTRADOS:")
            for field_id, field_value in required_fields.items():
                click.echo(f"   * {field_id}: {field_value}")

            # Generar configuración sugerida
            import json
            click.echo(f"\nCONFIGURACIÓN SUGERIDA PARA .env:")
            click.echo(f"FEATURE_REQUIRED_FIELDS='{json.dumps(required_fields)}'")

            click.echo(f"\nNOTA: Revisa los logs para ver todos los valores disponibles")
            click.echo(f"      y cambiar IDs si el valor por defecto no es apropiado")

        else:
            click.echo("+ No se encontraron campos obligatorios adicionales")

        # Configuración actual
        click.echo(f"\nCONFIGURACIÓN ACTUAL:")
        click.echo(f"   FEATURE_ISSUE_TYPE: {settings.feature_issue_type}")
        click.echo(f"   FEATURE_REQUIRED_FIELDS: {settings.feature_required_fields or 'No configurado'}")

        click.echo(f"\nDiagnóstico completado")

    except Exception as e:
        logger.error("Error durante el diagnóstico: %s", str(e))
        click.echo(f"Error: {str(e)}", err=True)


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    cli()
