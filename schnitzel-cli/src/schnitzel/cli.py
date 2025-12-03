"""Schnitzel CLI - Schema-driven full-stack code generator."""

import typer
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax

from .schema import SchemaParser

app = typer.Typer(
    name="schnitzel",
    help="Schema-driven full-stack code generator for Flutter and FastAPI",
    add_completion=False,
)

console = Console()


@app.command()
def validate(
    schema_path: Path = typer.Argument(
        ...,
        help="Path to the Schnitzel schema YAML file",
        exists=True,
    )
) -> None:
    """Validate a Schnitzel schema file."""
    try:
        console.print(f"[blue]Validating schema:[/blue] {schema_path}")

        parser = SchemaParser()
        schema = parser.parse(schema_path)

        console.print(f"[green]✓ Schema is valid![/green]")
        console.print(f"  Models: {len(schema.models)}")

        if schema.models:
            console.print("\n  Models defined:")
            for model_name, model in schema.models.items():
                field_count = len(model.fields)
                console.print(f"    - {model_name} ({field_count} fields)")

    except Exception as e:
        console.print(f"[red]✗ Schema validation failed:[/red]")
        console.print(f"  {e}")
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Show Schnitzel CLI version."""
    from . import __version__
    console.print(f"Schnitzel CLI version {__version__}")


if __name__ == "__main__":
    app()
