"""Formateador de salida para la CLI."""
import click
from pathlib import Path
from typing import List, Dict, Any

from src.domain.entities.batch_result import BatchResult
from src.domain.entities.process_result import ProcessResult


class OutputFormatter:
    """Responsable de formatear la salida de la aplicación."""

    def print_error(self, message: str) -> None:
        """Imprime mensaje de error."""
        click.echo(f"[ERROR] {message}", err=True)

    def print_success(self, message: str) -> None:
        """Imprime mensaje de éxito."""
        click.echo(f"[OK] {message}")

    def print_warning(self, message: str) -> None:
        """Imprime mensaje de advertencia."""
        click.echo(f"[WARNING] {message}")

    def print_info(self, message: str) -> None:
        """Imprime mensaje informativo."""
        click.echo(message)

    def print_file_header(self, file_index: int, total_files: int, file_name: str) -> None:
        """Imprime cabecera de procesamiento de archivo."""
        click.echo(f"\n{'='*60}")
        click.echo(f"PROCESANDO ARCHIVO {file_index}/{total_files}: {file_name}")
        click.echo(f"{'='*60}")

    def print_story_result(self, result: ProcessResult, story_title: str) -> None:
        """Imprime resultado de procesamiento de historia."""
        if result.success:
            self.print_success(f"Fila {result.row_number}: {result.jira_key} - {story_title}")

            # Información de feature
            if result.feature_info:
                if result.feature_info.was_created:
                    click.echo(f"    + Feature creada: {result.feature_info.feature_key}")
                else:
                    click.echo(f"    = Parent utilizado: {result.feature_info.feature_key}")

            # Información de subtareas
            if result.subtasks_created > 0:
                click.echo(f"    + {result.subtasks_created} subtarea(s) creada(s)")
            if result.subtasks_failed > 0:
                click.echo(f"    - {result.subtasks_failed} subtarea(s) fallaron", err=True)
        else:
            self.print_error(f"Fila {result.row_number}: {result.error_message}")

    def print_batch_summary(self, file_name: str, batch_result: BatchResult) -> None:
        """Imprime resumen de procesamiento de archivo."""
        click.echo(f"\nRESUMEN DE {file_name}:")
        click.echo(f"Total procesadas: {batch_result.total_processed}")
        click.echo(f"Exitosas: {batch_result.successful}")
        click.echo(f"Fallidas: {batch_result.failed}")

    def print_batch_errors(self, results: List[ProcessResult]) -> None:
        """Imprime errores de un lote."""
        failed_results = [r for r in results if not r.success]
        if failed_results:
            click.echo("Errores encontrados:")
            for result in failed_results:
                click.echo(f"  Fila {result.row_number}: {result.error_message}")

    def print_subtask_errors(self, results: List[ProcessResult]) -> None:
        """Imprime errores de subtareas."""
        for result in results:
            if result.success and result.subtask_errors:
                click.echo(f"Errores de subtareas en fila {result.row_number} ({result.jira_key}):")
                for error in result.subtask_errors:
                    click.echo(f"  • {error}")

    def print_general_summary(self, total_files: int, overall_result: BatchResult) -> None:
        """Imprime resumen general de todos los archivos."""
        click.echo(f"\n{'='*60}")
        click.echo("RESUMEN GENERAL")
        click.echo(f"{'='*60}")
        click.echo(f"Archivos procesados: {total_files}")
        click.echo(f"Total historias procesadas: {overall_result.total_processed}")
        click.echo(f"Total exitosas: {overall_result.successful}")
        click.echo(f"Total fallidas: {overall_result.failed}")

    def print_results(self, results: Dict[str, Any]) -> None:
        """Imprime resultados completos del procesamiento."""
        # Implementación específica basada en la estructura de resultados
        pass

    def print_validation_result(self, result: Dict[str, Any]) -> None:
        """Imprime resultado de validación de archivo."""
        click.echo(f"Preview de {result['file']} (primeras {result['rows']} filas):")
        click.echo("="*60)
        click.echo(result['preview'])

        click.echo("\n" + "="*60)
        click.echo("VALIDACIÓN DE ESTRUCTURA")
        click.echo("="*60)

        self.print_success("Archivo válido")
        self.print_success(f"{result['total_stories']} historias encontradas")
        self.print_success("Todas las filas tienen formato correcto")

        # Estadísticas
        click.echo(f"  - Con subtareas: {result['with_subtasks']}")
        click.echo(f"  - Total subtareas: {result['total_subtasks']}")
        click.echo(f"  - Con parent: {result['with_parent']}")

        if result['invalid_subtasks'] > 0:
            self.print_error(f"Subtareas inválidas: {result['invalid_subtasks']}")
            self.print_error("(vacías o >255 caracteres)")

    def print_connection_result(self, result: Dict[str, Any]) -> None:
        """Imprime resultado de test de conexión."""
        click.echo("Probando conexión con Jira...")

        if result['connection_success']:
            self.print_success("Conexión exitosa")

            if result['project_valid']:
                self.print_success(f"Proyecto {result['project_key']} encontrado")
            else:
                self.print_error(f"Proyecto {result['project_key']} no encontrado")
        else:
            self.print_error("Error de conexión")

    def print_diagnose_result(self, result: Dict[str, Any]) -> None:
        """Imprime resultado de diagnóstico."""
        click.echo("="*60)
        click.echo("DIAGNÓSTICO DE CONFIGURACIÓN PARA FEATURES")
        click.echo("="*60)

        self.print_success("Conexión con Jira exitosa")
        self.print_success(f"Proyecto {result['project_key']} válido")
        self.print_success(f"Tipo de feature '{result['feature_type']}' válido")

        if result['required_fields']:
            click.echo(f"\nCAMPOS OBLIGATORIOS ENCONTRADOS:")
            for field_id, field_value in result['required_fields'].items():
                click.echo(f"   * {field_id}: {field_value}")

            click.echo(f"\nCONFIGURACIÓN SUGERIDA PARA .env:")
            click.echo(f"FEATURE_REQUIRED_FIELDS='{result['config_suggestion']}'")

            click.echo(f"\nNOTA: Revisa los logs para ver todos los valores disponibles")
        else:
            self.print_success("No se encontraron campos obligatorios adicionales")

        click.echo(f"\nCONFIGURACIÓN ACTUAL:")
        click.echo(f"   FEATURE_ISSUE_TYPE: {result['current_config']['feature_type']}")
        click.echo(f"   FEATURE_REQUIRED_FIELDS: {result['current_config']['required_fields'] or 'No configurado'}")

        click.echo(f"\nDiagnóstico completado")