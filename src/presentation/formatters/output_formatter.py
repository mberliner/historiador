"""Formateador de salida para la CLI."""
from typing import List, Dict, Any

import click

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
        click.echo(f"\n{'='*70}")
        click.echo(f"PROCESANDO ARCHIVO [{file_index}/{total_files}]: {file_name}")
        click.echo(f"{'='*70}")
        click.echo("Iniciando procesamiento...\n")

    def print_story_result(self, result: ProcessResult, story_title: str) -> None:
        """Imprime resultado de procesamiento de historia."""
        if result.success:
            click.echo(f"Historia de Usuario creada: {result.jira_key}")
            click.echo(f"  Titulo: {story_title}")

            # Información de feature
            if result.feature_info:
                if result.feature_info.was_created:
                    click.echo(f"  Feature CREADA: {result.feature_info.feature_key}")
                else:
                    click.echo(f"  Feature UTILIZADA: {result.feature_info.feature_key}")

            # Información de subtareas
            if result.subtasks_created > 0:
                click.echo(f"  Subtareas creadas: {result.subtasks_created}")
            if result.subtasks_failed > 0:
                click.echo(f"  Subtareas fallidas: {result.subtasks_failed}")

            click.echo("")  # Línea en blanco para separar
        else:
            click.echo(f"ERROR - Fila {result.row_number}: {result.error_message}")
            click.echo("")

    def print_batch_summary(self, file_name: str, batch_result: BatchResult) -> None:
        """Imprime resumen de procesamiento de archivo."""
        click.echo(f"{'-'*70}")
        click.echo(f"RESUMEN DEL ARCHIVO: {file_name}")
        click.echo(f"{'-'*70}")

        # Contar features creadas/usadas y subtareas
        features_created = 0
        features_used = 0
        total_subtasks = 0

        for result in batch_result.results:
            if result.success and result.feature_info:
                if result.feature_info.was_created:
                    features_created += 1
                else:
                    features_used += 1
            if result.success:
                total_subtasks += result.subtasks_created

        click.echo("Historias de Usuario:")
        click.echo(f"  - Creadas: {batch_result.successful}")
        click.echo(f"  - Fallidas: {batch_result.failed}")

        click.echo("Features:")
        click.echo(f"  - Creadas: {features_created}")
        click.echo(f"  - Utilizadas: {features_used}")

        click.echo("Subtareas:")
        click.echo(f"  - Creadas: {total_subtasks}")

        # Estado general
        if batch_result.total_processed > 0:
            success_rate = (batch_result.successful / batch_result.total_processed) * 100
            click.echo(f"\nEstado: {success_rate:.0f}% exitoso")

        click.echo("")  # Línea en blanco

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
        click.echo(f"{'='*70}")
        click.echo("RESUMEN FINAL DE PROCESAMIENTO")
        click.echo(f"{'='*70}")

        # Contar totales
        total_features_created = 0
        total_features_used = 0
        total_subtasks = 0

        for result in overall_result.results:
            if result.success and result.feature_info:
                if result.feature_info.was_created:
                    total_features_created += 1
                else:
                    total_features_used += 1
            if result.success:
                total_subtasks += result.subtasks_created

        click.echo(f"Archivos procesados: {total_files}")
        click.echo("\nHistorias de Usuario:")
        click.echo(f"  - Total creadas: {overall_result.successful}")
        click.echo(f"  - Total fallidas: {overall_result.failed}")

        click.echo("\nFeatures:")
        click.echo(f"  - Total creadas: {total_features_created}")
        click.echo(f"  - Total utilizadas: {total_features_used}")

        click.echo("\nSubtareas:")
        click.echo(f"  - Total creadas: {total_subtasks}")

        # Estado final
        if overall_result.total_processed > 0:
            success_rate = (overall_result.successful / overall_result.total_processed) * 100
            click.echo(f"\nTasa de exito: {success_rate:.0f}%")

            if success_rate == 100:
                click.echo("RESULTADO: Procesamiento completado exitosamente!")
            elif success_rate >= 80:
                click.echo("RESULTADO: Procesamiento completado con exito parcial")
            else:
                click.echo("RESULTADO: Procesamiento completado con errores significativos")

        click.echo(f"{'='*70}")

    def print_results(self, results: Dict[str, Any]) -> None:
        """Imprime resultados completos del procesamiento."""
        total_files = results['total_files']
        file_results = results['file_results']
        overall_result = results['overall_result']

        # Procesar cada archivo
        for file_data in file_results:
            if 'error' in file_data:
                # Error procesando archivo
                self.print_file_header(file_data['file_index'], total_files, file_data['file_name'])
                self.print_error(f"Error procesando archivo: {file_data['error']}")
                continue

            # Mostrar header del archivo
            self.print_file_header(file_data['file_index'], total_files, file_data['file_name'])

            # Mostrar resultados individuales
            batch_result = file_data['batch_result']
            if hasattr(batch_result, 'stories') and batch_result.stories:
                for result, story in zip(batch_result.results, batch_result.stories):
                    self.print_story_result(result, story.titulo)
            else:
                # Fallback si no hay stories
                for result in batch_result.results:
                    self.print_story_result(result, "Historia sin título")

            # Mostrar resumen del archivo
            self.print_batch_summary(file_data['file_name'], batch_result)

        # Mostrar resumen general si hay resultados
        if overall_result:
            self.print_general_summary(total_files, overall_result)


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
