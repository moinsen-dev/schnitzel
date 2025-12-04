"""Migrate command for Schnitzel CLI - database migration management using Alembic."""

import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from schnitzel.utils.logging import get_logger
from schnitzel.generators.infra.migration_validator import validate_pending_migrations
from schnitzel.schema import SchemaParser

console = Console()
logger = get_logger(__name__)

# Create the migrate command group
migrate = typer.Typer(
    name="migrate",
    help="Database migration management",
    add_completion=False,
)


def _is_quiet_mode() -> bool:
    """Check if quiet mode is enabled via CLI.

    Returns:
        bool: True if quiet mode is enabled
    """
    from schnitzel.cli import is_quiet_mode
    return is_quiet_mode()


def _find_backend_dir() -> Optional[Path]:
    """Find the backend directory in the current project.

    Returns:
        Path to backend directory if found, None otherwise
    """
    # Check current directory and parent directories
    current = Path.cwd()
    for _ in range(5):  # Search up to 5 levels
        backend_dir = current / "backend"
        if backend_dir.exists() and backend_dir.is_dir():
            return backend_dir
        current = current.parent
        if current == current.parent:  # Reached root
            break
    return None


def _run_alembic_command(args: list[str], backend_dir: Path) -> bool:
    """Run an Alembic command in the backend directory.

    Args:
        args: Command arguments to pass to alembic
        backend_dir: Path to backend directory

    Returns:
        bool: True if command succeeded, False otherwise
    """
    quiet = _is_quiet_mode()

    try:
        # Run alembic command
        if not quiet:
            console.print(f"[blue]Running:[/blue] alembic {' '.join(args)}")

        result = subprocess.run(
            ["alembic"] + args,
            cwd=backend_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            if not quiet:
                if result.stdout:
                    console.print(result.stdout)
                console.print("[green]✓ Migration command completed successfully[/green]")
            return True
        else:
            console.print("[red]✗ Migration command failed:[/red]")
            if result.stderr:
                console.print(result.stderr)
            if result.stdout:
                console.print(result.stdout)
            return False

    except FileNotFoundError:
        console.print(
            "[red]✗ Error:[/red] Alembic is not installed or not in PATH\n"
            "[yellow]Hint:[/yellow] Install Alembic in your backend environment: "
            "uv add alembic"
        )
        return False
    except Exception as e:
        console.print(f"[red]✗ Error running Alembic:[/red] {e}")
        return False


def _validate_migrations(backend_dir: Path, quiet: bool = False) -> bool:
    """Validate pending migrations before applying.

    Args:
        backend_dir: Path to backend directory
        quiet: Whether to suppress detailed output

    Returns:
        bool: True if all migrations are valid
    """
    # Find migrations directory
    migrations_dir = backend_dir / "migrations" / "versions"
    if not migrations_dir.exists():
        migrations_dir = backend_dir / ".schnitzel" / "migrations"

    if not migrations_dir.exists():
        if not quiet:
            console.print("[yellow]⚠ No migrations directory found, skipping validation[/yellow]")
        return True

    # Try to load schema for cross-validation
    schema = None
    schema_path = Path.cwd() / "schema.schnitzel.yaml"
    if schema_path.exists():
        try:
            parser = SchemaParser()
            schema = parser.parse(schema_path)
        except Exception as e:
            if not quiet:
                console.print(f"[yellow]⚠ Could not load schema for validation: {e}[/yellow]")

    # Validate migrations
    if not quiet:
        console.print("[blue]Validating migrations...[/blue]")

    all_valid, results = validate_pending_migrations(migrations_dir, schema)

    if not results:
        if not quiet:
            console.print("[yellow]⚠ No migration files found to validate[/yellow]")
        return True

    # Display results
    if not quiet:
        for migration_file, result in results.items():
            if result.valid:
                console.print(f"[green]✓[/green] {migration_file}")
            else:
                console.print(f"[red]✗[/red] {migration_file}")

            # Show errors
            for error in result.errors:
                console.print(f"  [red]ERROR:[/red] {error.message}")
                if error.line_number:
                    console.print(f"    [dim]Line {error.line_number}[/dim]")

            # Show warnings
            for warning in result.warnings:
                console.print(f"  [yellow]WARNING:[/yellow] {warning.message}")

        # Summary table
        if len(results) > 1:
            table = Table(title="Validation Summary")
            table.add_column("Status", style="bold")
            table.add_column("Count", justify="right")

            total = len(results)
            valid = sum(1 for r in results.values() if r.valid)
            invalid = total - valid
            total_errors = sum(len(r.errors) for r in results.values())
            total_warnings = sum(len(r.warnings) for r in results.values())

            table.add_row("[green]Valid[/green]", str(valid))
            if invalid > 0:
                table.add_row("[red]Invalid[/red]", str(invalid))
            if total_errors > 0:
                table.add_row("[red]Errors[/red]", str(total_errors))
            if total_warnings > 0:
                table.add_row("[yellow]Warnings[/yellow]", str(total_warnings))

            console.print()
            console.print(table)

    return all_valid


@migrate.command()
def up(
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate migrations before applying (default: True)"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate only, do not apply migrations"
    ),
) -> None:
    """Apply pending migrations to the database.

    By default, migrations are validated before being applied to ensure:
    - SQL syntax is correct
    - Referenced tables/columns match the schema
    - No destructive operations without awareness

    Use --no-validate to skip validation (not recommended).
    Use --dry-run to only validate without applying.
    """
    backend_dir = _find_backend_dir()
    if not backend_dir:
        console.print(
            "[red]✗ Error:[/red] Could not find backend directory\n"
            "[yellow]Hint:[/yellow] Run this command from your Schnitzel project root"
        )
        raise typer.Exit(code=1)

    quiet = _is_quiet_mode()

    # Validate migrations if requested
    if validate or dry_run:
        validation_passed = _validate_migrations(backend_dir, quiet)
        if not validation_passed:
            console.print("[red]✗ Migration validation failed[/red]")
            console.print("[yellow]Hint:[/yellow] Fix validation errors before applying migrations")
            raise typer.Exit(code=1)

        if dry_run:
            if not quiet:
                console.print("[green]✓ All migrations validated successfully (dry-run)[/green]")
            return

    if not quiet:
        console.print("[blue]Applying pending migrations...[/blue]")

        # Show progress with Rich spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Running alembic upgrade head...", total=None)
            success = _run_alembic_command(["upgrade", "head"], backend_dir)
    else:
        success = _run_alembic_command(["upgrade", "head"], backend_dir)

    if not success:
        raise typer.Exit(code=1)


@migrate.command()
def down(
    rollback_all: bool = typer.Option(
        False,
        "--all",
        help="Rollback all migrations to the base (empty database)"
    )
) -> None:
    """Rollback the last migration, or all migrations with --all.

    Examples:
        schnitzel migrate down         # Rollback one migration
        schnitzel migrate down --all   # Rollback all migrations
    """
    backend_dir = _find_backend_dir()
    if not backend_dir:
        console.print(
            "[red]✗ Error:[/red] Could not find backend directory\n"
            "[yellow]Hint:[/yellow] Run this command from your Schnitzel project root"
        )
        raise typer.Exit(code=1)

    quiet = _is_quiet_mode()

    if rollback_all:
        if not quiet:
            console.print("[blue]Rolling back all migrations to base...[/blue]")
        success = _run_alembic_command(["downgrade", "base"], backend_dir)
    else:
        if not quiet:
            console.print("[blue]Rolling back last migration...[/blue]")
        success = _run_alembic_command(["downgrade", "-1"], backend_dir)

    if not success:
        raise typer.Exit(code=1)


@migrate.command()
def status() -> None:
    """Show the current migration status.

    Displays:
    - Current migration revision
    - Pending migrations (not yet applied)
    - Applied migrations (already applied)
    """
    backend_dir = _find_backend_dir()
    if not backend_dir:
        console.print(
            "[red]✗ Error:[/red] Could not find backend directory\n"
            "[yellow]Hint:[/yellow] Run this command from your Schnitzel project root"
        )
        raise typer.Exit(code=1)

    quiet = _is_quiet_mode()
    if not quiet:
        console.print("[blue]Checking migration status...[/blue]")

    # Show current revision
    success = _run_alembic_command(["current"], backend_dir)
    if not success:
        raise typer.Exit(code=1)

    # Show migration history to see applied migrations
    if not quiet:
        console.print("\n[blue]Applied migrations:[/blue]")
    success = _run_alembic_command(["history"], backend_dir)
    if not success:
        # Don't fail if history command fails, as current already succeeded
        if not quiet:
            console.print("[yellow]Warning:[/yellow] Could not retrieve migration history")


@migrate.command()
def history() -> None:
    """Show migration history."""
    backend_dir = _find_backend_dir()
    if not backend_dir:
        console.print(
            "[red]✗ Error:[/red] Could not find backend directory\n"
            "[yellow]Hint:[/yellow] Run this command from your Schnitzel project root"
        )
        raise typer.Exit(code=1)

    quiet = _is_quiet_mode()
    if not quiet:
        console.print("[blue]Migration history:[/blue]")

    success = _run_alembic_command(["history"], backend_dir)
    if not success:
        raise typer.Exit(code=1)


@migrate.command()
def diff(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Name/description for the migration"
    ),
    schema_path: Path = typer.Option(
        Path("schema.schnitzel.yaml"),
        "--schema",
        "-s",
        help="Path to the Schnitzel schema file"
    ),
    migrations_dir: Path = typer.Option(
        Path(".schnitzel/migrations"),
        "--migrations-dir",
        "-m",
        help="Directory where migrations are stored"
    ),
) -> None:
    """Generate a new migration by analyzing the schema.

    This command reads your Schnitzel schema and generates an Alembic
    migration file with CREATE TABLE statements for all models.

    Examples:
        schnitzel migrate diff --name "initial"
        schnitzel migrate diff --name "add_user_profile"
    """
    quiet = _is_quiet_mode()

    # Validate schema file exists
    if not schema_path.exists():
        console.print(f"[red]✗ Error:[/red] Schema file not found: {schema_path}")
        raise typer.Exit(code=1)

    if not quiet:
        console.print(f"[blue]Generating migration:[/blue] {name}")
        console.print(f"  Schema: {schema_path}")
        console.print(f"  Migrations dir: {migrations_dir}")

    try:
        # Parse the schema
        from schnitzel.schema import SchemaParser
        from schnitzel.generators.infra.migrations import AlembicMigrationGenerator

        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Check if schema has models
        if not schema.models:
            console.print("[yellow]Warning:[/yellow] Schema has no models defined")
            console.print("No migration generated.")
            raise typer.Exit(code=0)

        # Find the last migration to get down_revision
        down_revision = _find_last_migration_revision(migrations_dir)

        # Generate the migration
        generator = AlembicMigrationGenerator()
        migration_file, revision_id = generator.generate_migration_to_file(
            schema=schema,
            migration_name=name,
            migrations_dir=migrations_dir,
            down_revision=down_revision,
        )

        console.print(f"[green]✓ Migration generated successfully![/green]")
        console.print(f"  File: {migration_file}")
        console.print(f"  Revision ID: {revision_id}")
        console.print(f"  Models: {len(schema.models)}")

        # Show tables that will be created
        if not quiet:
            console.print("\n  Tables to create:")
            for model_name in schema.models.keys():
                table_name = _pluralize_table_name(_to_snake_case(model_name))
                console.print(f"    - {table_name}")

    except Exception as e:
        console.print(f"[red]✗ Migration generation failed:[/red] {e}")
        logger.exception("Migration generation error")
        raise typer.Exit(code=1)


def _find_last_migration_revision(migrations_dir: Path) -> Optional[str]:
    """Find the revision ID of the last migration.

    Args:
        migrations_dir: Directory containing migrations

    Returns:
        Revision ID of the last migration, or None if no migrations exist
    """
    if not migrations_dir.exists():
        return None

    # Get all Python files in migrations directory
    migration_files = sorted(migrations_dir.glob("*.py"))

    if not migration_files:
        return None

    # Read the last migration file and extract revision ID
    last_file = migration_files[-1]
    content = last_file.read_text(encoding="utf-8")

    # Extract revision ID using regex
    import re
    match = re.search(r"revision = ['\"]([^'\"]+)['\"]", content)

    if match:
        return match.group(1)

    return None


def _to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _pluralize_table_name(snake_name: str) -> str:
    """Pluralize a snake_case table name."""
    if snake_name.endswith("y") and len(snake_name) > 1 and snake_name[-2] not in "aeiou":
        return snake_name[:-1] + "ies"
    elif snake_name.endswith("s") or snake_name.endswith("x") or snake_name.endswith("z"):
        return snake_name + "es"
    else:
        return snake_name + "s"


# Export the migrate command group for registration
def migrate_command() -> typer.Typer:
    """Return the migrate command group for registration.

    Returns:
        The migrate Typer app
    """
    return migrate
