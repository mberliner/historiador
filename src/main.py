"""Aplicación principal refactorizada."""

import sys
from pathlib import Path

import click

# Agregar el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from src.presentation.cli.commands import (
    diagnose_command,
    process_command,
    test_connection_command,
    validate_command,
)


@click.group(invoke_without_command=True)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
)
@click.option("--file", "-f", help="Archivo Excel o CSV específico con las historias")
@click.option("--project", "-p", help="Key del proyecto en Jira (ej: MYPROJ)")
@click.option("--dry-run", is_flag=True, help="Modo de prueba sin crear issues")
@click.pass_context
def cli(ctx, log_level, file, project, dry_run):
    """Jira Batch Importer - Crea historias de usuario desde archivos Excel/CSV."""
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level

    # Si no se especifica comando, ejecutar process por defecto
    if ctx.invoked_subcommand is None:
        ctx.invoke(
            process_command,
            file=file,
            project=project,
            dry_run=dry_run,
            log_level=log_level,
        )


# Registrar comandos
cli.add_command(process_command, name="process")
cli.add_command(validate_command, name="validate")
cli.add_command(test_connection_command, name="test-connection")
cli.add_command(diagnose_command, name="diagnose")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
