"""Migrate command for Schnitzel CLI - database migration management using Alembic."""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from schnitzel.utils.logging import get_logger
from schnitzel.utils.network_errors import NetworkErrorHandler
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
    except subprocess.TimeoutExpired as e:
        should_exit, error_msg = NetworkErrorHandler.handle_database_error(e, quiet)
        return False
    except Exception as e:
        # Check if it's a database connection error
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ["connection", "database", "refused", "timeout"]):
            should_exit, error_msg = NetworkErrorHandler.handle_database_error(e, quiet)
        else:
            console.print(f"[red]✗ Error running Alembic:[/red] {e}")
        return False


def _has_destructive_operations(migrations_dir: Path) -> bool:
    """Check if pending migrations contain destructive operations.

    Args:
        migrations_dir: Directory containing migration files

    Returns:
        True if any pending migration contains destructive operations
    """
    if not migrations_dir.exists():
        return False

    # Get all migration files
    migration_files = sorted(migrations_dir.glob("*.py"))

    for migration_file in migration_files:
        # Skip __init__.py
        if migration_file.name.startswith('__'):
            continue

        try:
            content = migration_file.read_text(encoding='utf-8')

            # Check for destructive operations
            destructive_patterns = [
                'op.drop_table(',
                'op.drop_column(',
                'DROP TABLE',
                'DROP COLUMN',
                'TRUNCATE',
            ]

            for pattern in destructive_patterns:
                if pattern in content:
                    return True

        except Exception as e:
            logger.warning(f"Could not read migration file {migration_file}: {e}")

    return False


def _create_database_backup(backend_dir: Path, quiet: bool = False) -> Optional[Path]:
    """Create a database backup before destructive operations.

    Args:
        backend_dir: Path to backend directory
        quiet: Whether to suppress output

    Returns:
        Path to backup file if successful, None otherwise
    """
    # Get DATABASE_URL from environment or .env file
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        # Try to read from .env file in backend directory
        env_file = backend_dir / '.env'
        if env_file.exists():
            try:
                env_content = env_file.read_text()
                for line in env_content.split('\n'):
                    if line.startswith('DATABASE_URL='):
                        database_url = line.split('=', 1)[1].strip()
                        break
            except Exception as e:
                logger.warning(f"Could not read .env file: {e}")

    if not database_url:
        if not quiet:
            console.print("[yellow]⚠ Could not find DATABASE_URL, skipping backup[/yellow]")
        return None

    # Create backups directory
    backups_dir = backend_dir / '.schnitzel' / 'backups'
    backups_dir.mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # Detect database type from URL
        if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
            # PostgreSQL backup using pg_dump
            backup_file = backups_dir / f"backup_{timestamp}.sql"

            if not quiet:
                console.print(f"[blue]Creating PostgreSQL backup...[/blue]")

            # Parse DATABASE_URL to extract connection details
            # Format: postgresql://user:password@host:port/database
            import re
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
            if not match:
                match = re.match(r'postgres://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)

            if match:
                user, password, host, port, database = match.groups()

                # Set PGPASSWORD environment variable for pg_dump
                env = os.environ.copy()
                env['PGPASSWORD'] = password

                # Run pg_dump
                result = subprocess.run(
                    [
                        'pg_dump',
                        '-h', host,
                        '-p', port,
                        '-U', user,
                        '-d', database,
                        '-f', str(backup_file),
                        '--no-owner',
                        '--no-acl',
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    if not quiet:
                        console.print(f"[green]✓ Backup created:[/green] {backup_file}")
                    return backup_file
                else:
                    if not quiet:
                        console.print(f"[yellow]⚠ Backup failed:[/yellow] {result.stderr}")
                    logger.warning(f"pg_dump failed: {result.stderr}")
                    return None
            else:
                if not quiet:
                    console.print("[yellow]⚠ Could not parse DATABASE_URL for backup[/yellow]")
                return None

        elif database_url.startswith('sqlite://'):
            # SQLite backup using simple file copy
            backup_file = backups_dir / f"backup_{timestamp}.db"

            # Extract database file path from URL
            db_path = database_url.replace('sqlite:///', '').replace('sqlite://', '')

            # Handle relative paths
            if not Path(db_path).is_absolute():
                db_path = backend_dir / db_path
            else:
                db_path = Path(db_path)

            if not db_path.exists():
                if not quiet:
                    console.print(f"[yellow]⚠ Database file not found:[/yellow] {db_path}")
                return None

            if not quiet:
                console.print(f"[blue]Creating SQLite backup...[/blue]")

            # Copy database file
            import shutil
            shutil.copy2(db_path, backup_file)

            if not quiet:
                console.print(f"[green]✓ Backup created:[/green] {backup_file}")
            return backup_file

        else:
            if not quiet:
                console.print(f"[yellow]⚠ Unsupported database type for backup:[/yellow] {database_url.split('://')[0]}")
            return None

    except FileNotFoundError as e:
        if not quiet:
            console.print(f"[yellow]⚠ Backup tool not found:[/yellow] {e}")
        return None
    except Exception as e:
        if not quiet:
            console.print(f"[yellow]⚠ Backup failed:[/yellow] {e}")
        logger.exception("Database backup error")
        return None


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
    skip_backup: bool = typer.Option(
        False,
        "--skip-backup",
        help="Skip automatic backup for destructive operations"
    ),
) -> None:
    """Apply pending migrations to the database.

    By default, migrations are validated before being applied to ensure:
    - SQL syntax is correct
    - Referenced tables/columns match the schema
    - No destructive operations without awareness
    - Automatic backup before destructive operations

    Use --no-validate to skip validation (not recommended).
    Use --dry-run to only validate without applying.
    Use --skip-backup to skip automatic backups (not recommended).
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

    # Check for destructive operations and create backup if needed
    if not skip_backup:
        migrations_dir = backend_dir / "migrations" / "versions"
        if not migrations_dir.exists():
            migrations_dir = backend_dir / ".schnitzel" / "migrations"

        if migrations_dir.exists() and _has_destructive_operations(migrations_dir):
            if not quiet:
                console.print("[yellow]⚠ Destructive operations detected in migrations[/yellow]")

            # Create backup
            backup_file = _create_database_backup(backend_dir, quiet)

            if backup_file and not quiet:
                console.print(f"[green]✓ Database backup created before migration[/green]")
                console.print(f"  Location: {backup_file}")

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


@migrate.command()
def squash(
    from_revision: str = typer.Option(
        ...,
        "--from",
        "-f",
        help="First revision to include in squash (oldest)"
    ),
    to_revision: str = typer.Option(
        ...,
        "--to",
        "-t",
        help="Last revision to include in squash (newest)"
    ),
    name: str = typer.Option(
        "squashed_migrations",
        "--name",
        "-n",
        help="Name for the squashed migration"
    ),
    migrations_dir: Path = typer.Option(
        Path(".schnitzel/migrations"),
        "--migrations-dir",
        "-m",
        help="Directory where migrations are stored"
    ),
) -> None:
    """Squash multiple migrations into a single migration.

    This combines multiple sequential migrations into one migration file,
    which can help reduce the number of migration files and improve
    migration performance.

    The squashed migration will have the same net effect as applying
    all the individual migrations in sequence.

    Examples:
        schnitzel migrate squash --from abc123 --to def456
        schnitzel migrate squash --from abc123 --to def456 --name "initial_schema"
    """
    backend_dir = _find_backend_dir()
    if not backend_dir:
        console.print(
            "[red]✗ Error:[/red] Could not find backend directory\n"
            "[yellow]Hint:[/yellow] Run this command from your Schnitzel project root"
        )
        raise typer.Exit(code=1)

    quiet = _is_quiet_mode()

    # Resolve migrations directory
    if not migrations_dir.is_absolute():
        migrations_dir = backend_dir / migrations_dir

    if not migrations_dir.exists():
        console.print(f"[red]✗ Error:[/red] Migrations directory not found: {migrations_dir}")
        raise typer.Exit(code=1)

    if not quiet:
        console.print(f"[blue]Squashing migrations from {from_revision} to {to_revision}...[/blue]")

    try:
        # Find all migration files
        migration_files = sorted(migrations_dir.glob("*.py"))
        if not migration_files:
            console.print("[red]✗ Error:[/red] No migration files found")
            raise typer.Exit(code=1)

        # Parse migration files to build revision chain
        import re
        import hashlib

        revision_map = {}  # revision_id -> (file_path, down_revision, content)

        for migration_file in migration_files:
            if migration_file.name == "__init__.py":
                continue

            content = migration_file.read_text(encoding="utf-8")

            # Extract revision and down_revision
            rev_match = re.search(r"revision = ['\"]([^'\"]+)['\"]", content)
            down_match = re.search(r"down_revision = (?:None|['\"]([^'\"]*)['\"])", content)

            if rev_match:
                revision_id = rev_match.group(1)
                down_revision = down_match.group(1) if down_match and down_match.group(1) else None
                revision_map[revision_id] = (migration_file, down_revision, content)

        # Find the chain of migrations from from_revision to to_revision
        if from_revision not in revision_map:
            console.print(f"[red]✗ Error:[/red] From revision '{from_revision}' not found")
            raise typer.Exit(code=1)

        if to_revision not in revision_map:
            console.print(f"[red]✗ Error:[/red] To revision '{to_revision}' not found")
            raise typer.Exit(code=1)

        # Build the chain by following down_revision pointers backwards from to_revision
        chain = []
        current_rev = to_revision

        while current_rev and current_rev != from_revision:
            if current_rev not in revision_map:
                console.print(f"[red]✗ Error:[/red] Broken chain at revision '{current_rev}'")
                raise typer.Exit(code=1)

            chain.append(current_rev)
            _, down_revision, _ = revision_map[current_rev]
            current_rev = down_revision

        # Add from_revision
        if current_rev == from_revision:
            chain.append(from_revision)
        else:
            console.print(
                f"[red]✗ Error:[/red] Revisions are not sequential\n"
                f"Could not find a path from {from_revision} to {to_revision}"
            )
            raise typer.Exit(code=1)

        # Reverse to get oldest-to-newest order
        chain.reverse()

        if not quiet:
            console.print(f"[blue]Found {len(chain)} migrations to squash:[/blue]")
            for rev in chain:
                file_path, _, _ = revision_map[rev]
                console.print(f"  - {rev[:8]}... ({file_path.name})")

        # Combine upgrade and downgrade operations
        all_upgrade_ops = []
        all_downgrade_ops = []

        for rev in chain:
            _, _, content = revision_map[rev]

            # Extract upgrade operations
            upgrade_match = re.search(
                r"def upgrade\(\) -> None:\s*(.*?)(?=\ndef downgrade|\Z)",
                content,
                re.DOTALL
            )
            if upgrade_match:
                ops_text = upgrade_match.group(1).strip()
                if ops_text and ops_text != "pass":
                    # Extract operation lines (preserve indentation)
                    ops_lines = [line for line in ops_text.split('\n') if line.strip() and line.strip() != 'pass']
                    all_upgrade_ops.extend(ops_lines)

            # Extract downgrade operations (we'll reverse these later)
            downgrade_match = re.search(
                r"def downgrade\(\) -> None:\s*(.*?)(?=\n\n|\Z)",
                content,
                re.DOTALL
            )
            if downgrade_match:
                ops_text = downgrade_match.group(1).strip()
                if ops_text and ops_text != "pass":
                    ops_lines = [line for line in ops_text.split('\n') if line.strip() and line.strip() != 'pass']
                    # Prepend these ops (reverse order for downgrade)
                    all_downgrade_ops = ops_lines + all_downgrade_ops

        # Get the down_revision of the first migration in chain
        _, first_down_revision, _ = revision_map[chain[0]]

        # Generate new revision ID
        timestamp = datetime.now().isoformat()
        content_hash = f"{timestamp}_{name}"
        hash_obj = hashlib.sha256(content_hash.encode("utf-8"))
        new_revision_id = hash_obj.hexdigest()[:8]

        # Build squashed migration file
        create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        down_revision_str = f"'{first_down_revision}'" if first_down_revision else "None"

        squashed_content = f'''"""Squashed migration: {name}

Revision ID: {new_revision_id}
Revises: {first_down_revision or ''}
Create Date: {create_date}

Squashes: {', '.join(chain)}
"""
from alembic import op
import sqlalchemy as sa

revision = '{new_revision_id}'
down_revision = {down_revision_str}
branch_labels = None
depends_on = None


def upgrade() -> None:
'''

        if all_upgrade_ops:
            squashed_content += '\n' + '\n'.join(all_upgrade_ops) + '\n'
        else:
            squashed_content += '    pass\n'

        squashed_content += '''

def downgrade() -> None:
'''

        if all_downgrade_ops:
            squashed_content += '\n' + '\n'.join(all_downgrade_ops) + '\n'
        else:
            squashed_content += '    pass\n'

        # Write the squashed migration file
        sanitized_name = re.sub(r"[^a-zA-Z0-9_]", "", name.replace(" ", "_")).lower()
        squashed_filename = f"{new_revision_id}_{sanitized_name}.py"
        squashed_file = migrations_dir / squashed_filename

        squashed_file.write_text(squashed_content, encoding="utf-8")

        # Mark old migrations as squashed by renaming them
        for rev in chain:
            file_path, _, _ = revision_map[rev]
            # Rename with .squashed suffix
            squashed_old = file_path.with_suffix(".py.squashed")
            file_path.rename(squashed_old)

            if not quiet:
                console.print(f"  [dim]Marked as squashed: {file_path.name}[/dim]")

        console.print(f"[green]✓ Squashed migration created successfully![/green]")
        console.print(f"  File: {squashed_file}")
        console.print(f"  Revision ID: {new_revision_id}")
        console.print(f"  Squashed {len(chain)} migrations")

        if not quiet:
            console.print("\n[yellow]Note:[/yellow] Old migration files have been renamed with .squashed suffix")
            console.print("[yellow]Hint:[/yellow] Test the squashed migration before deleting old files")

    except Exception as e:
        console.print(f"[red]✗ Squash failed:[/red] {e}")
        logger.exception("Migration squash error")
        raise typer.Exit(code=1)


# Export the migrate command group for registration
def migrate_command() -> typer.Typer:
    """Return the migrate command group for registration.

    Returns:
        The migrate Typer app
    """
    return migrate
