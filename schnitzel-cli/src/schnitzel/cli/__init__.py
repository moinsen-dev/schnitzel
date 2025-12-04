"""Schnitzel CLI - Schema-driven full-stack code generator."""

import typer
from pathlib import Path
from rich.console import Console

from schnitzel.schema import SchemaParser
from schnitzel.utils.logging import set_verbose, get_logger

app = typer.Typer(
    name="schnitzel",
    help="Schema-driven full-stack code generator for Flutter and FastAPI",
    add_completion=False,
)

console = Console()
logger = get_logger(__name__)

# Global state for quiet mode
_quiet_mode = False


def set_quiet_mode(quiet: bool) -> None:
    """Set the global quiet mode state.

    Args:
        quiet: Whether to enable quiet mode
    """
    global _quiet_mode
    _quiet_mode = quiet


def is_quiet_mode() -> bool:
    """Check if quiet mode is enabled.

    Returns:
        bool: True if quiet mode is enabled
    """
    return _quiet_mode


@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging output"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Minimal output mode - show only essential information"
    )
) -> None:
    """Global CLI options."""
    if verbose:
        set_verbose(True)
        logger.debug("Verbose logging enabled")

    set_quiet_mode(quiet)


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
        if not is_quiet_mode():
            console.print(f"[blue]Validating schema:[/blue] {schema_path}")

        parser = SchemaParser()
        schema = parser.parse(schema_path)

        if not is_quiet_mode():
            console.print(f"[green]✓ Schema is valid![/green]")
            console.print(f"  Models: {len(schema.models)}")

            if schema.models:
                console.print("\n  Models defined:")
                for model_name, model in schema.models.items():
                    field_count = len(model.fields)
                    console.print(f"    - {model_name} ({field_count} fields)")
        else:
            # In quiet mode, just print success indicator
            console.print("OK")

    except Exception as e:
        # Always show errors, even in quiet mode
        console.print(f"[red]✗ Schema validation failed:[/red]")
        console.print(f"  {e}")
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Show Schnitzel CLI version."""
    from schnitzel import __version__
    console.print(f"Schnitzel CLI version {__version__}")


# Import and register init command
from schnitzel.cli.commands.init import init_command
app.command(name="init")(init_command)

# Import and register generate command
from schnitzel.cli.commands.generate import generate_command
app.command(name="generate")(generate_command)

# Export both app and main
__all__ = ["app", "main"]


def main() -> None:
    """Main entry point with KeyboardInterrupt handling."""
    try:
        app()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully without showing traceback
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130)


if __name__ == "__main__":
    main()
