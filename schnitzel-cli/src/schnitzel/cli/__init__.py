"""Schnitzel CLI - Schema-driven full-stack code generator."""

import typer
from pathlib import Path
from rich.console import Console

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


# Import and register validate command
from schnitzel.cli.commands.validate import validate_command
app.command(name="validate")(validate_command)


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

# Import and register migrate command group
from schnitzel.cli.commands.migrate import migrate_command
app.add_typer(migrate_command(), name="migrate")

# Import and register serve command
from schnitzel.cli.commands.serve import serve_command
app.command(name="serve")(serve_command)

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
