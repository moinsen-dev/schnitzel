"""Generate command for Schnitzel CLI - parses and validates schema before generation."""

from pathlib import Path
from datetime import datetime
import signal
import subprocess
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from watchfiles import watch

from schnitzel.schema import SchemaParser, SchemaValidator
from schnitzel.schema.exceptions import (
    YAMLParseError,
    ValidationError,
    CircularImportError,
    SchemaError,
    VersionError,
)
from schnitzel.generators.python.main import FastAPIMainGenerator
from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator
from schnitzel.generators.python.routes import PythonRouteGenerator
from schnitzel.generators.python.auth.jwt import JWTAuthGenerator
from schnitzel.generators.python.auth.oauth import OAuthIntegrationGenerator
from schnitzel.generators.python.auth.rbac import RBACPermissionGenerator
from schnitzel.generators.python.auth.sessions import SessionManagementGenerator
from schnitzel.generators.python.auth.mfa import MFAGenerator
from schnitzel.generators.python.auth.migrations import AuthMigrationGenerator
from schnitzel.generators.dart.models import DartModelGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator
from schnitzel.utils.logging import get_logger
from schnitzel.utils.network_errors import NetworkErrorHandler

console = Console()
logger = get_logger(__name__)

# Global flag for graceful shutdown
_shutdown_requested = False


def _is_quiet_mode() -> bool:
    """Check if quiet mode is enabled via CLI.

    Returns:
        bool: True if quiet mode is enabled
    """
    from schnitzel.cli import is_quiet_mode
    return is_quiet_mode()


def _signal_handler(signum: int, frame: object) -> None:
    """Handle Ctrl+C gracefully in watch mode."""
    global _shutdown_requested
    _shutdown_requested = True
    console.print("\n[yellow]Stopping watch mode...[/yellow]")
    sys.exit(0)


def _cleanup_files(files: list[Path]) -> None:
    """Clean up partially generated files on error.

    Args:
        files: List of file paths to remove
    """
    for file_path in files:
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                console.print(f"[yellow]Cleaned up partial file:[/yellow] {file_path}")
            except Exception as cleanup_error:
                console.print(f"[yellow]Warning: Could not clean up {file_path}:[/yellow] {cleanup_error}")


def _is_flutter_installed() -> bool:
    """Check if Flutter is installed and available in PATH."""
    try:
        result = subprocess.run(
            ["flutter", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _is_uv_installed() -> bool:
    """Check if uv is installed and available in PATH."""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _run_flutter_setup(flutter_dir: Path, quiet: bool = False) -> bool:
    """Run flutter pub get and build_runner in the Flutter package.

    Args:
        flutter_dir: Path to the Flutter package directory (packages/app)
        quiet: If True, suppress output

    Returns:
        True if all setup commands succeeded, False otherwise
    """
    if not _is_flutter_installed():
        if not quiet:
            console.print("  [yellow]⚠ Flutter not installed - skipping Flutter setup[/yellow]")
        return False

    # Check if pubspec.yaml exists
    pubspec_file = flutter_dir / "pubspec.yaml"
    if not pubspec_file.exists():
        if not quiet:
            console.print(f"  [yellow]⚠ No pubspec.yaml found in {flutter_dir} - skipping Flutter setup[/yellow]")
        return False

    success = True

    # Step 1: flutter pub get
    if not quiet:
        console.print("  [blue]Running flutter pub get...[/blue]")

    try:
        result = subprocess.run(
            ["flutter", "pub", "get"],
            cwd=flutter_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            if not quiet:
                console.print("  [green]✓ flutter pub get[/green]")
        else:
            if not quiet:
                console.print(f"  [red]✗ flutter pub get failed[/red]")
                if result.stderr:
                    console.print(f"    [dim]{result.stderr.strip()[:200]}[/dim]")
            success = False
    except subprocess.TimeoutExpired as e:
        if not quiet:
            NetworkErrorHandler.handle_subprocess_error(e, "flutter pub get", quiet)
        success = False
    except FileNotFoundError as e:
        if not quiet:
            NetworkErrorHandler.handle_subprocess_error(e, "flutter", quiet)
        success = False
    except Exception as e:
        if not quiet and ("network" in str(e).lower() or "connection" in str(e).lower()):
            NetworkErrorHandler.handle_subprocess_error(e, "flutter pub get", quiet)
        elif not quiet:
            console.print(f"  [red]✗ flutter pub get error: {e}[/red]")
        success = False

    # Step 2: dart run build_runner build (only if pub get succeeded)
    if success:
        if not quiet:
            console.print("  [blue]Running build_runner...[/blue]")

        try:
            result = subprocess.run(
                ["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"],
                cwd=flutter_dir,
                capture_output=True,
                text=True,
                timeout=300  # build_runner can take a while
            )
            if result.returncode == 0:
                if not quiet:
                    console.print("  [green]✓ build_runner build[/green]")
            else:
                if not quiet:
                    console.print(f"  [yellow]⚠ build_runner build failed (may need freezed dependencies)[/yellow]")
                    if result.stderr:
                        # Show first few lines of error
                        error_lines = result.stderr.strip().split('\n')[:3]
                        for line in error_lines:
                            console.print(f"    [dim]{line[:100]}[/dim]")
                # Don't mark as failure - build_runner may not be configured yet
        except subprocess.TimeoutExpired as e:
            if not quiet:
                console.print("  [yellow]⚠ build_runner timed out[/yellow]")
                console.print("  [dim]This may indicate network issues downloading dependencies[/dim]")
        except FileNotFoundError as e:
            if not quiet:
                NetworkErrorHandler.handle_subprocess_error(e, "dart", quiet)
        except Exception as e:
            if not quiet:
                console.print(f"  [yellow]⚠ build_runner error: {e}[/yellow]")

    return success


def _run_python_setup(backend_dir: Path, quiet: bool = False) -> bool:
    """Run uv sync in the Python backend.

    Args:
        backend_dir: Path to the Python backend directory (backend/app)
        quiet: If True, suppress output

    Returns:
        True if setup succeeded, False otherwise
    """
    if not _is_uv_installed():
        if not quiet:
            console.print("  [yellow]⚠ uv not installed - skipping Python setup[/yellow]")
        return False

    # Check if pyproject.toml exists
    pyproject_file = backend_dir / "pyproject.toml"
    if not pyproject_file.exists():
        if not quiet:
            console.print(f"  [yellow]⚠ No pyproject.toml found in {backend_dir} - skipping Python setup[/yellow]")
        return False

    if not quiet:
        console.print("  [blue]Running uv sync...[/blue]")

    try:
        result = subprocess.run(
            ["uv", "sync"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            if not quiet:
                console.print("  [green]✓ uv sync[/green]")
            return True
        else:
            if not quiet:
                console.print(f"  [yellow]⚠ uv sync failed[/yellow]")
                if result.stderr:
                    console.print(f"    [dim]{result.stderr.strip()[:200]}[/dim]")
            return False
    except subprocess.TimeoutExpired as e:
        if not quiet:
            console.print("  [yellow]⚠ uv sync timed out[/yellow]")
            console.print("  [dim]This may indicate network issues downloading dependencies[/dim]")
        return False
    except FileNotFoundError as e:
        if not quiet:
            NetworkErrorHandler.handle_subprocess_error(e, "uv", quiet)
        return False
    except Exception as e:
        if not quiet and ("network" in str(e).lower() or "connection" in str(e).lower()):
            NetworkErrorHandler.handle_subprocess_error(e, "uv sync", quiet)
        elif not quiet:
            console.print(f"  [yellow]⚠ uv sync error: {e}[/yellow]")
        return False


def _run_post_generation_setup(output_path: Path, quiet: bool = False) -> None:
    """Run post-generation setup commands for Flutter and Python.

    Args:
        output_path: Base output directory containing packages/ and backend/
        quiet: If True, suppress output
    """
    if not quiet:
        console.print("\n[blue]Running post-generation setup...[/blue]")

    # Flutter setup
    flutter_dir = output_path / "packages" / "app"
    if flutter_dir.exists():
        _run_flutter_setup(flutter_dir, quiet)

    # Python setup
    backend_dir = output_path / "backend" / "app"
    if backend_dir.exists():
        _run_python_setup(backend_dir, quiet)


def _generate_python(schema, output_dir: Path, schema_path: Path, force: bool, dry_run: bool = False) -> dict | None:
    """Generate Python Pydantic models.

    Args:
        schema: Parsed schema object
        output_dir: Output directory for generated files
        schema_path: Path to the schema file (for documentation)
        force: Whether to overwrite existing files
        dry_run: If True, show what would be generated without writing files

    Returns:
        Dictionary with file info: {'path': Path, 'size': int, 'type': str} or None if skipped
    """
    if not dry_run and not _is_quiet_mode():
        console.print("[blue]Generating Python models...[/blue]")

    # Determine output path: output_dir/backend/app
    python_output_dir = output_dir / "backend" / "app"

    # Check if models.py already exists
    models_file = python_output_dir / "models.py"
    if models_file.exists() and not force and not dry_run:
        console.print(f"[yellow]Warning: {models_file} already exists. Use --force to overwrite.[/yellow]")
        return None

    if dry_run:
        return {'path': models_file, 'size': 0, 'type': 'python'}

    # Generate Python models
    generator = PythonModelGenerator()
    output_file, size = generator.generate_to_file(schema, python_output_dir, schema_source=schema_path.name)

    model_count = len(schema.models)
    if not _is_quiet_mode():
        console.print(f"[green]✓ Generated backend/app/models.py[/green] ({model_count} models)")

    return {
        'path': output_file,
        'size': size,
        'type': 'python'
    }


def _generate_orm(schema, output_dir: Path, schema_path: Path, force: bool, dry_run: bool = False) -> dict | None:
    """Generate SQLAlchemy ORM models.

    Args:
        schema: Parsed schema object
        output_dir: Output directory for generated files
        schema_path: Path to the schema file (for documentation)
        force: Whether to overwrite existing files
        dry_run: If True, show what would be generated without writing files

    Returns:
        Dictionary with file info: {'path': Path, 'size': int, 'type': str} or None if skipped
    """
    if not dry_run and not _is_quiet_mode():
        console.print("[blue]Generating SQLAlchemy ORM models...[/blue]")

    # Determine output path: output_dir/backend/app/generated
    orm_output_dir = output_dir / "backend" / "app" / "generated"

    # Check if orm.py already exists
    orm_file = orm_output_dir / "orm.py"
    if orm_file.exists() and not force and not dry_run:
        console.print(f"[yellow]Warning: {orm_file} already exists. Use --force to overwrite.[/yellow]")
        return None

    if dry_run:
        return {'path': orm_file, 'size': 0, 'type': 'orm'}

    # Generate SQLAlchemy ORM models
    generator = SQLAlchemyORMGenerator()
    output_file, size = generator.generate_to_file(schema, orm_output_dir, schema_source=schema_path.name)

    model_count = len(schema.models)
    if not _is_quiet_mode():
        console.print(f"[green]✓ Generated backend/app/generated/orm.py[/green] ({model_count} models)")

    return {
        'path': output_file,
        'size': size,
        'type': 'orm'
    }


def _generate_routes(schema, output_dir: Path, schema_path: Path, force: bool, dry_run: bool = False) -> dict | None:
    """Generate FastAPI routes.

    Args:
        schema: Parsed schema object
        output_dir: Output directory for generated files
        schema_path: Path to the schema file (for documentation)
        force: Whether to overwrite existing files
        dry_run: If True, show what would be generated without writing files

    Returns:
        Dictionary with file info: {'path': Path, 'size': int, 'type': str} or None if skipped
    """
    if not dry_run and not _is_quiet_mode():
        console.print("[blue]Generating FastAPI routes...[/blue]")

    # Determine output path: output_dir/backend/app/generated
    routes_output_dir = output_dir / "backend" / "app" / "generated"

    # Check if routes.py already exists
    routes_file = routes_output_dir / "routes.py"
    if routes_file.exists() and not force and not dry_run:
        console.print(f"[yellow]Warning: {routes_file} already exists. Use --force to overwrite.[/yellow]")
        return None

    if dry_run:
        return {'path': routes_file, 'size': 0, 'type': 'routes'}

    # Generate FastAPI routes
    generator = PythonRouteGenerator()
    output_file, size = generator.generate_to_file(schema, routes_output_dir, schema_source=schema_path.name)

    endpoint_count = len(schema.endpoints) if schema.endpoints else 0
    if not _is_quiet_mode():
        console.print(f"[green]✓ Generated backend/app/generated/routes.py[/green] ({endpoint_count} endpoints)")

    return {
        'path': output_file,
        'size': size,
        'type': 'routes'
    }


def _generate_main(schema, output_dir: Path, schema_path: Path, force: bool, dry_run: bool = False) -> dict | None:
    """Generate FastAPI main.py entry point with CORS support.

    Args:
        schema: Parsed schema object
        output_dir: Output directory for generated files
        schema_path: Path to the schema file (for documentation)
        force: Whether to overwrite existing files
        dry_run: If True, show what would be generated without writing files

    Returns:
        Dictionary with file info: {'path': Path, 'size': int, 'type': str} or None if skipped
    """
    if not dry_run and not _is_quiet_mode():
        console.print("[blue]Generating FastAPI main.py...[/blue]")

    # Determine output path: output_dir/backend/app
    main_output_dir = output_dir / "backend" / "app"

    # Check if main.py already exists
    main_file = main_output_dir / "main.py"
    if main_file.exists() and not force and not dry_run:
        console.print(f"[yellow]Warning: {main_file} already exists. Use --force to overwrite.[/yellow]")
        return None

    if dry_run:
        return {'path': main_file, 'size': 0, 'type': 'main'}

    # Generate FastAPI main.py
    generator = FastAPIMainGenerator()
    output_file, size = generator.generate_to_file(schema, main_output_dir, schema_source=schema_path.name)

    if not _is_quiet_mode():
        console.print(f"[green]✓ Generated backend/app/main.py[/green] (with CORS middleware)")

    return {
        'path': output_file,
        'size': size,
        'type': 'main'
    }


def _generate_dart(schema, output_dir: Path, schema_path: Path, force: bool, dry_run: bool = False) -> dict | None:
    """Generate Dart Freezed models.

    Args:
        schema: Parsed schema object
        output_dir: Output directory for generated files
        schema_path: Path to the schema file (for documentation)
        force: Whether to overwrite existing files
        dry_run: If True, show what would be generated without writing files

    Returns:
        Dictionary with file info: {'path': Path, 'size': int, 'type': str} or None if skipped
    """
    if not dry_run and not _is_quiet_mode():
        console.print("[blue]Generating Dart models...[/blue]")

    # Determine output path: output_dir/packages/app/lib/models
    dart_output_dir = output_dir / "packages" / "app" / "lib" / "models"

    # Check if models.dart already exists
    models_file = dart_output_dir / "models.dart"
    if models_file.exists() and not force and not dry_run:
        console.print(f"[yellow]Warning: {models_file} already exists. Use --force to overwrite.[/yellow]")
        return None

    if dry_run:
        return {'path': models_file, 'size': 0, 'type': 'dart'}

    # Generate Dart models
    generator = DartModelGenerator()
    output_file, size = generator.generate_to_file(schema, dart_output_dir, schema_source=schema_path.name)

    if not _is_quiet_mode():
        console.print(f"[green]✓ Generated Dart models:[/green] {output_file}")

    return {
        'path': output_file,
        'size': size,
        'type': 'dart'
    }


def _generate_dart_api_client(schema, output_dir: Path, schema_path: Path, force: bool, dry_run: bool = False) -> dict | None:
    """Generate Dart API client.

    Args:
        schema: Parsed schema object
        output_dir: Output directory for generated files
        schema_path: Path to the schema file (for documentation)
        force: Whether to overwrite existing files
        dry_run: If True, show what would be generated without writing files

    Returns:
        Dictionary with file info: {'path': Path, 'size': int, 'type': str} or None if skipped
    """
    if not dry_run and not _is_quiet_mode():
        console.print("[blue]Generating Dart API client...[/blue]")

    # Determine output path: output_dir/packages/shared/lib/generated
    dart_output_dir = output_dir / "packages" / "shared" / "lib" / "generated"

    # Check if api_client.dart already exists
    api_client_file = dart_output_dir / "api_client.dart"
    if api_client_file.exists() and not force and not dry_run:
        console.print(f"[yellow]Warning: {api_client_file} already exists. Use --force to overwrite.[/yellow]")
        return None

    if dry_run:
        return {'path': api_client_file, 'size': 0, 'type': 'dart_api'}

    # Generate Dart API client
    generator = DartApiClientGenerator()
    output_file, size = generator.generate_to_file(schema, dart_output_dir, schema_source=schema_path.name)

    endpoint_count = len(schema.endpoints) if schema.endpoints else 0
    if not _is_quiet_mode():
        console.print(f"[green]✓ Generated packages/shared/lib/generated/api_client.dart[/green] ({endpoint_count} endpoints)")

    return {
        'path': output_file,
        'size': size,
        'type': 'dart_api'
    }


def _generate_auth(schema, output_dir: Path, schema_path: Path, force: bool, dry_run: bool = False) -> list[dict]:
    """Generate authentication utilities based on schema configuration.

    Args:
        schema: Parsed schema object
        output_dir: Output directory for generated files
        schema_path: Path to the schema file (for documentation)
        force: Whether to overwrite existing files
        dry_run: If True, show what would be generated without writing files

    Returns:
        List of dictionaries with file info for each generated auth file
    """
    generated_files = []

    # Check if auth is configured in schema
    if not schema.auth:
        if not dry_run and not _is_quiet_mode():
            console.print("[yellow]No auth configuration found in schema - skipping auth generation[/yellow]")
        return generated_files

    if not dry_run and not _is_quiet_mode():
        console.print("[blue]Generating authentication utilities...[/blue]")

    # Determine output path: output_dir/backend/app/generated/auth
    auth_output_dir = output_dir / "backend" / "app" / "generated" / "auth"

    # Generate JWT if JWT config exists
    if hasattr(schema.auth, 'jwt') and schema.auth.jwt:
        jwt_file = auth_output_dir / "jwt.py"
        if jwt_file.exists() and not force and not dry_run:
            console.print(f"[yellow]Warning: {jwt_file} already exists. Use --force to overwrite.[/yellow]")
        else:
            if not dry_run:
                try:
                    generator = JWTAuthGenerator()
                    output_file, size = generator.generate_to_file(schema, auth_output_dir, schema_source=schema_path.name, dry_run=dry_run)
                    if not _is_quiet_mode():
                        console.print(f"[green]✓ Generated backend/app/generated/auth/jwt.py[/green]")
                    generated_files.append({'path': output_file, 'size': size, 'type': 'auth_jwt'})
                except Exception as e:
                    console.print(f"[red]✗ Failed to generate JWT auth:[/red] {e}")
            else:
                generated_files.append({'path': jwt_file, 'size': 0, 'type': 'auth_jwt'})

    # Generate OAuth if providers are configured
    if hasattr(schema.auth, 'providers') and schema.auth.providers:
        oauth_file = auth_output_dir / "oauth.py"
        if oauth_file.exists() and not force and not dry_run:
            console.print(f"[yellow]Warning: {oauth_file} already exists. Use --force to overwrite.[/yellow]")
        else:
            if not dry_run:
                try:
                    generator = OAuthIntegrationGenerator()
                    output_file, size = generator.generate_to_file(schema, auth_output_dir, schema_source=schema_path.name, dry_run=dry_run)
                    if not _is_quiet_mode():
                        console.print(f"[green]✓ Generated backend/app/generated/auth/oauth.py[/green]")
                    generated_files.append({'path': output_file, 'size': size, 'type': 'auth_oauth'})
                except Exception as e:
                    console.print(f"[red]✗ Failed to generate OAuth:[/red] {e}")
            else:
                generated_files.append({'path': oauth_file, 'size': 0, 'type': 'auth_oauth'})

    # Generate RBAC if roles are configured
    if schema.roles:
        rbac_file = auth_output_dir / "rbac.py"
        if rbac_file.exists() and not force and not dry_run:
            console.print(f"[yellow]Warning: {rbac_file} already exists. Use --force to overwrite.[/yellow]")
        else:
            if not dry_run:
                try:
                    generator = RBACPermissionGenerator()
                    output_file, size = generator.generate_to_file(schema, auth_output_dir, schema_source=schema_path.name, dry_run=dry_run)
                    if not _is_quiet_mode():
                        console.print(f"[green]✓ Generated backend/app/generated/auth/rbac.py[/green]")
                    generated_files.append({'path': output_file, 'size': size, 'type': 'auth_rbac'})
                except Exception as e:
                    console.print(f"[red]✗ Failed to generate RBAC:[/red] {e}")
            else:
                generated_files.append({'path': rbac_file, 'size': 0, 'type': 'auth_rbac'})

    # Generate sessions if session config exists
    if hasattr(schema.auth, 'session') and schema.auth.session:
        sessions_file = auth_output_dir / "sessions.py"
        if sessions_file.exists() and not force and not dry_run:
            console.print(f"[yellow]Warning: {sessions_file} already exists. Use --force to overwrite.[/yellow]")
        else:
            if not dry_run:
                try:
                    generator = SessionManagementGenerator()
                    output_file, size = generator.generate_to_file(schema, auth_output_dir, schema_source=schema_path.name, dry_run=dry_run)
                    if not _is_quiet_mode():
                        console.print(f"[green]✓ Generated backend/app/generated/auth/sessions.py[/green]")
                    generated_files.append({'path': output_file, 'size': size, 'type': 'auth_sessions'})
                except Exception as e:
                    console.print(f"[red]✗ Failed to generate sessions:[/red] {e}")
            else:
                generated_files.append({'path': sessions_file, 'size': 0, 'type': 'auth_sessions'})

    # Generate MFA if MFA config exists and is enabled
    if hasattr(schema.auth, 'mfa') and schema.auth.mfa and schema.auth.mfa.enabled:
        mfa_file = auth_output_dir / "mfa.py"
        if mfa_file.exists() and not force and not dry_run:
            console.print(f"[yellow]Warning: {mfa_file} already exists. Use --force to overwrite.[/yellow]")
        else:
            if not dry_run:
                try:
                    generator = MFAGenerator()
                    output_file, size = generator.generate_to_file(schema, auth_output_dir, schema_source=schema_path.name, dry_run=dry_run)
                    if not _is_quiet_mode():
                        console.print(f"[green]✓ Generated backend/app/generated/auth/mfa.py[/green]")
                    generated_files.append({'path': output_file, 'size': size, 'type': 'auth_mfa'})
                except Exception as e:
                    console.print(f"[red]✗ Failed to generate MFA:[/red] {e}")
            else:
                generated_files.append({'path': mfa_file, 'size': 0, 'type': 'auth_mfa'})

    # Generate auth migration if auth is configured
    # This creates an Alembic migration to add auth fields to the user table
    if schema.auth or schema.roles:
        migration_dir = output_dir / "backend" / "alembic" / "versions"
        migration_file_prefix = f"auth_{datetime.now().strftime('%Y%m%d%H%M%S')}_add_auth_fields.py"
        migration_file = migration_dir / migration_file_prefix

        if not dry_run:
            try:
                generator = AuthMigrationGenerator()
                output_file, size = generator.generate_to_file(schema, migration_dir, dry_run=dry_run)
                if not _is_quiet_mode():
                    console.print(f"[green]✓ Generated auth migration: {output_file.name}[/green]")
                generated_files.append({'path': output_file, 'size': size, 'type': 'auth_migration'})
            except Exception as e:
                # Migration generation is optional - don't fail if alembic dir doesn't exist yet
                if not _is_quiet_mode():
                    console.print(f"[yellow]Note: Skipped auth migration generation:[/yellow] {e}")
                    console.print(f"[dim]  You can generate migrations later using 'schnitzel migrate create'[/dim]")
        else:
            generated_files.append({'path': migration_file, 'size': 0, 'type': 'auth_migration'})

    return generated_files


def _generate_docker(
    schema_path: Path,
    output_dir: Path,
    force: bool,
    dry_run: bool = False,
    schema: Optional["SchnitzelSchema"] = None,
) -> dict | None:
    """Generate Docker Compose file.

    Args:
        schema_path: Path to the schema file (used to determine project root)
        output_dir: Output directory for generated files
        force: Whether to overwrite existing files
        dry_run: If True, show what would be generated without writing files
        schema: Optional parsed schema for custom port configuration (F094)

    Returns:
        Dictionary with file info: {'path': Path, 'size': int, 'type': str} or None if skipped
    """
    from schnitzel.generators.docker.compose import DockerComposeGenerator

    if not dry_run and not _is_quiet_mode():
        console.print("[blue]Generating Docker Compose...[/blue]")

    # Check if docker-compose.yaml already exists
    docker_compose_file = output_dir / "docker-compose.yaml"
    if docker_compose_file.exists() and not force and not dry_run:
        console.print(f"[yellow]Warning: {docker_compose_file} already exists. Use --force to overwrite.[/yellow]")
        return None

    if dry_run:
        return {'path': docker_compose_file, 'size': 0, 'type': 'docker'}

    # Generate docker-compose.yaml (F094: pass schema for custom ports)
    generator = DockerComposeGenerator()
    output_file, size = generator.generate_to_file(output_dir, schema=schema)

    if not _is_quiet_mode():
        console.print(f"[green]✓ Generated docker-compose.yaml:[/green] {output_file}")

    return {
        'path': output_file,
        'size': size,
        'type': 'docker'
    }


def _run_generation(
    schema_path: Path,
    target: str,
    output_path: Path,
    force: bool,
    dry_run: bool = False,
    show_progress: bool = True
) -> bool:
    """Run the generation process once.

    Args:
        schema_path: Path to the schema file
        target: What to generate (all, python, dart, docker)
        output_path: Output directory
        force: Whether to overwrite existing files
        dry_run: If True, show what would be generated without writing files
        show_progress: Whether to show progress bars

    Returns:
        True if generation succeeded, False otherwise
    """
    try:
        # Check if schema file exists
        if not schema_path.exists():
            console.print(f"[red]Error: Schema file not found:[/red] {schema_path}")
            console.print()
            console.print("[yellow]It looks like you're running this command outside a Schnitzel project directory.[/yellow]")
            console.print()
            console.print("[blue]To get started:[/blue]")
            console.print("  1. Initialize a new project:")
            console.print("     [cyan]schnitzel init my-project[/cyan]")
            console.print()
            console.print("  2. Or specify a schema file:")
            console.print(f"     [cyan]schnitzel generate path/to/schema.schnitzel.yaml[/cyan]")
            console.print()
            console.print("[dim]By default, 'schnitzel generate' looks for 'schema.schnitzel.yaml' in the current directory.[/dim]")
            return False

        # Create progress display with spinner
        if show_progress and not _is_quiet_mode():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                transient=True,
            ) as progress:
                # Parsing step
                parse_task = progress.add_task(
                    f"[cyan]Parsing schema: {schema_path.name}...",
                    total=1
                )

                parser = SchemaParser()
                schema = parser.parse(schema_path)

                progress.update(parse_task, completed=1)
                console.print(f"[green]✓ Schema parsed successfully[/green]")
                console.print(f"  Models found: {len(schema.models)}")

                # Validation step
                validate_task = progress.add_task(
                    "[cyan]Validating schema...",
                    total=1
                )

                validator = SchemaValidator()
                validation_result = validator.validate(schema)

                progress.update(validate_task, completed=1)
        else:
            # No progress bars in watch mode after initial run or in quiet mode
            parser = SchemaParser()
            schema = parser.parse(schema_path)
            validator = SchemaValidator()
            validation_result = validator.validate(schema)

        if not validation_result.valid:
            console.print(f"[red]✗ Schema validation failed:[/red]")
            console.print()
            for error in validation_result.errors:
                console.print(f"  [red]Error:[/red]")
                for line in error.split("\n"):
                    console.print(f"    {line}")
                console.print()
            return False

        if show_progress and not _is_quiet_mode():
            console.print(f"[green]✓ Schema validation passed[/green]")

            # Display models
            if schema.models:
                console.print(f"\n[blue]Models validated:[/blue]")
                for model_name, model in schema.models.items():
                    field_count = len(model.fields)
                    console.print(f"  - {model_name} ({field_count} fields)")

            # Display unique fields if any
            if validation_result.unique_fields:
                console.print(f"\n[blue]Unique constraints:[/blue]")
                for model_name, fields in validation_result.unique_fields.items():
                    for field_name in fields:
                        console.print(f"  - {model_name}.{field_name}")

        # Validate target option - support both 'flutter' and 'dart'
        valid_targets = ["all", "docker", "python", "dart", "flutter", "auth"]
        if target not in valid_targets:
            console.print(f"[red]Error: Invalid target '{target}'[/red]")
            console.print(f"  Valid targets: {', '.join(valid_targets)}")
            return False

        # Normalize 'flutter' to 'dart' for consistency
        if target == "flutter":
            target = "dart"

        # Generate based on target
        if show_progress and not _is_quiet_mode():
            console.print()

        # Count total generation steps for progress tracking
        generation_steps = []
        if target == "python":
            generation_steps = ["python", "orm", "routes", "main", "auth"]
        elif target == "dart":
            generation_steps = ["dart", "dart_api"]
        elif target == "docker":
            generation_steps = ["docker"]
        elif target == "auth":
            generation_steps = ["auth"]
        elif target == "all":
            generation_steps = ["python", "orm", "routes", "main", "auth", "dart", "dart_api", "docker"]

        # Handle dry-run mode
        if dry_run:
            if not _is_quiet_mode():
                console.print("\n[yellow]DRY RUN MODE[/yellow] - No files will be written\n")
                console.print("[blue]Files that would be generated:[/blue]\n")

            generated_files = []
            total_size = 0

            for step in generation_steps:
                if step == "python":
                    result = _generate_python(schema, output_path, schema_path, force, dry_run)
                    if result:
                        # Calculate actual size by generating content
                        gen = PythonModelGenerator()
                        content = gen.generate(schema)
                        result['size'] = len(content.encode('utf-8'))
                        result['model_count'] = len(schema.models)
                        generated_files.append(result)
                        total_size += result['size']
                elif step == "orm":
                    result = _generate_orm(schema, output_path, schema_path, force, dry_run)
                    if result:
                        # Calculate actual size by generating content
                        gen = SQLAlchemyORMGenerator()
                        content = gen.generate(schema)
                        result['size'] = len(content.encode('utf-8'))
                        result['model_count'] = len(schema.models)
                        generated_files.append(result)
                        total_size += result['size']
                elif step == "routes":
                    result = _generate_routes(schema, output_path, schema_path, force, dry_run)
                    if result:
                        # Calculate actual size by generating content
                        gen = PythonRouteGenerator()
                        content = gen.generate(schema)
                        result['size'] = len(content.encode('utf-8'))
                        result['endpoint_count'] = len(schema.endpoints) if schema.endpoints else 0
                        generated_files.append(result)
                        total_size += result['size']
                elif step == "main":
                    result = _generate_main(schema, output_path, schema_path, force, dry_run)
                    if result:
                        # Calculate actual size by generating content
                        gen = FastAPIMainGenerator()
                        content = gen.generate(schema)
                        result['size'] = len(content.encode('utf-8'))
                        generated_files.append(result)
                        total_size += result['size']
                elif step == "dart":
                    result = _generate_dart(schema, output_path, schema_path, force, dry_run)
                    if result:
                        gen = DartModelGenerator()
                        content = gen.generate(schema)
                        result['size'] = len(content.encode('utf-8'))
                        result['model_count'] = len(schema.models)
                        generated_files.append(result)
                        total_size += result['size']
                elif step == "dart_api":
                    result = _generate_dart_api_client(schema, output_path, schema_path, force, dry_run)
                    if result:
                        gen = DartApiClientGenerator()
                        content = gen.generate(schema)
                        result['size'] = len(content.encode('utf-8'))
                        result['endpoint_count'] = len(schema.endpoints) if schema.endpoints else 0
                        generated_files.append(result)
                        total_size += result['size']
                elif step == "docker":
                    result = _generate_docker(schema_path, output_path, force, dry_run, schema=schema)
                    if result:
                        from schnitzel.generators.docker.compose import DockerComposeGenerator
                        gen = DockerComposeGenerator()
                        content = gen.generate(schema=schema)
                        result['size'] = len(content.encode('utf-8'))
                        generated_files.append(result)
                        total_size += result['size']
                elif step == "auth":
                    auth_results = _generate_auth(schema, output_path, schema_path, force, dry_run)
                    for result in auth_results:
                        generated_files.append(result)
                        total_size += result['size']

            # Display each file
            if not _is_quiet_mode():
                for file_info in generated_files:
                    console.print(f"  [green]✓[/green] {file_info['path']}")
                    type_display = {
                        'python': 'Python models',
                        'orm': 'SQLAlchemy ORM',
                        'routes': 'FastAPI routes',
                        'main': 'FastAPI main.py',
                        'dart': 'Dart models',
                        'dart_api': 'Dart API client',
                        'docker': 'Docker Compose',
                        'auth_jwt': 'JWT Authentication',
                        'auth_oauth': 'OAuth Integration',
                        'auth_rbac': 'RBAC Permissions',
                        'auth_sessions': 'Session Management',
                        'auth_mfa': 'Multi-Factor Auth',
                        'auth_migration': 'Auth Database Migration'
                    }.get(file_info['type'], file_info['type'])
                    console.print(f"    Type: {type_display}")

                    # Format size
                    size = file_info['size']
                    if size >= 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    elif size >= 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    else:
                        size_str = f"{size} bytes"
                    console.print(f"    Size: {size_str}")

                    if 'model_count' in file_info:
                        console.print(f"    Models: {file_info['model_count']}")
                    if 'endpoint_count' in file_info:
                        console.print(f"    Endpoints: {file_info['endpoint_count']}")
                    console.print()

                # Display summary
                console.print("[blue]Summary:[/blue]")
                console.print(f"  Files to generate: {len(generated_files)}")
                if total_size >= 1024:
                    console.print(f"  Total size: {total_size:,} bytes ({total_size / 1024:.1f} KB)")
                else:
                    console.print(f"  Total size: {total_size:,} bytes")
                console.print(f"  Models: {len(schema.models)}")
                console.print("\n[yellow]No files were written (dry-run mode)[/yellow]")
            else:
                # In quiet mode, just show OK for dry-run
                console.print("OK (dry-run)")
            return True

        # Show progress during generation
        if show_progress and not _is_quiet_mode():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                transient=False,
            ) as progress:
                gen_task = progress.add_task(
                    f"[cyan]Generating code ({len(generation_steps)} targets)...",
                    total=len(generation_steps)
                )

                # Track generated files for cleanup on error
                generated_files: list[Path] = []

                try:
                    for idx, step in enumerate(generation_steps):
                        progress.update(
                            gen_task,
                            description=f"[cyan]Generating {step}... ({idx + 1}/{len(generation_steps)})",
                            completed=idx
                        )

                        if step == "python":
                            result = _generate_python(schema, output_path, schema_path, force, dry_run)
                            if result:
                                generated_files.append(result['path'])
                        elif step == "orm":
                            result = _generate_orm(schema, output_path, schema_path, force, dry_run)
                            if result:
                                generated_files.append(result['path'])
                        elif step == "routes":
                            result = _generate_routes(schema, output_path, schema_path, force, dry_run)
                            if result:
                                generated_files.append(result['path'])
                        elif step == "main":
                            result = _generate_main(schema, output_path, schema_path, force, dry_run)
                            if result:
                                generated_files.append(result['path'])
                        elif step == "dart":
                            result = _generate_dart(schema, output_path, schema_path, force, dry_run)
                            if result:
                                generated_files.append(result['path'])
                        elif step == "dart_api":
                            result = _generate_dart_api_client(schema, output_path, schema_path, force, dry_run)
                            if result:
                                generated_files.append(result['path'])
                        elif step == "docker":
                            result = _generate_docker(schema_path, output_path, force, dry_run, schema=schema)
                            if result:
                                generated_files.append(result['path'])
                        elif step == "auth":
                            auth_results = _generate_auth(schema, output_path, schema_path, force, dry_run)
                            for result in auth_results:
                                generated_files.append(result['path'])

                        progress.update(gen_task, completed=idx + 1)

                except (PermissionError, IOError, OSError) as e:
                    # Clean up partial files
                    _cleanup_files(generated_files)
                    console.print(f"\n[red]✗ File write error:[/red]")
                    console.print(f"  {type(e).__name__}: {e}")
                    if hasattr(e, 'filename') and e.filename:
                        console.print(f"  File: {e.filename}")
                    return False

            if not _is_quiet_mode():
                console.print(f"\n[green]✓ Generation complete![/green]")
                console.print(f"  Processed {len(schema.models)} models across {len(generation_steps)} targets")
            else:
                # In quiet mode, just show OK
                console.print("OK")
        else:
            # In watch mode, generate without progress bars
            generated_files: list[Path] = []
            try:
                for step in generation_steps:
                    if step == "python":
                        result = _generate_python(schema, output_path, schema_path, force, dry_run)
                        if result:
                            generated_files.append(result['path'])
                    elif step == "orm":
                        result = _generate_orm(schema, output_path, schema_path, force, dry_run)
                        if result:
                            generated_files.append(result['path'])
                    elif step == "routes":
                        result = _generate_routes(schema, output_path, schema_path, force, dry_run)
                        if result:
                            generated_files.append(result['path'])
                    elif step == "main":
                        result = _generate_main(schema, output_path, schema_path, force, dry_run)
                        if result:
                            generated_files.append(result['path'])
                    elif step == "dart":
                        result = _generate_dart(schema, output_path, schema_path, force, dry_run)
                        if result:
                            generated_files.append(result['path'])
                    elif step == "dart_api":
                        result = _generate_dart_api_client(schema, output_path, schema_path, force, dry_run)
                        if result:
                            generated_files.append(result['path'])
                    elif step == "docker":
                        result = _generate_docker(schema_path, output_path, force, dry_run, schema=schema)
                        if result:
                            generated_files.append(result['path'])
                    elif step == "auth":
                        auth_results = _generate_auth(schema, output_path, schema_path, force, dry_run)
                        for result in auth_results:
                            generated_files.append(result['path'])
            except (PermissionError, IOError, OSError) as e:
                _cleanup_files(generated_files)
                console.print(f"\n[red]✗ File write error:[/red]")
                console.print(f"  {type(e).__name__}: {e}")
                if hasattr(e, 'filename') and e.filename:
                    console.print(f"  File: {e.filename}")
                return False

        return True

    except FileNotFoundError as e:
        console.print(f"[red]✗ File not found:[/red]")
        console.print(f"  {e}")
        return False

    except YAMLParseError as e:
        console.print(f"[red]✗ YAML parsing failed:[/red]")
        console.print(f"  {e}")
        return False

    except CircularImportError as e:
        console.print(f"[red]✗ Circular import detected:[/red]")
        console.print(f"  {e}")
        return False

    except ValidationError as e:
        console.print(f"[red]✗ Schema validation failed:[/red]")
        console.print(f"  {e}")
        return False

    except VersionError as e:
        console.print(f"[red]✗ Schema version error:[/red]")
        console.print(f"  {e}")
        return False

    except SchemaError as e:
        console.print(f"[red]✗ Schema error:[/red]")
        console.print(f"  {e}")
        return False

    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red]")
        console.print(f"  {type(e).__name__}: {e}")
        return False


def generate_command(
    schema_path: Path = typer.Argument(
        "schema.schnitzel.yaml",
        help="Path to the Schnitzel schema YAML file",
    ),
    schema: Path | None = typer.Option(
        None,
        "--schema",
        "-s",
        help="Path to the Schnitzel schema YAML file (overrides positional argument)",
    ),
    target: str = typer.Option(
        "all",
        "--target",
        "-t",
        help="What to generate: all, python, flutter, auth, docker",
    ),
    output_dir: str = typer.Option(
        ".",
        "--output",
        "-o",
        help="Output directory",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be generated without writing files",
    ),
    watch_mode: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Watch schema file for changes and regenerate automatically",
    ),
    setup: bool = typer.Option(
        True,
        "--setup/--no-setup",
        help="Run post-generation setup (flutter pub get, build_runner, uv sync)",
    ),
) -> None:
    """
    Generate code from a Schnitzel schema file.

    This command:
    1. Parses the schema file using SchemaParser
    2. Validates the schema using SchemaValidator
    3. Generates code based on the --target option
    4. Reports validation errors if any
    5. Returns exit code 1 if validation fails

    With --watch mode:
    - Monitors the schema file for changes
    - Auto-regenerates when file changes are detected
    - Shows timestamp for each regeneration
    - Press Ctrl+C to exit watch mode gracefully

    Args:
        schema_path: Path to the schema file (default: schema.schnitzel.yaml)
        schema: Optional --schema flag to override positional argument
        target: What to generate (all, python, flutter, docker)
        output_dir: Output directory (default: current directory)
        force: Overwrite existing files without warning
        dry_run: Show what would be generated without writing files
        watch_mode: Enable watch mode for automatic regeneration
    """
    # Use --schema flag if provided, otherwise use positional argument
    if schema is not None:
        schema_path = schema

    # Convert output_dir string to Path
    output_path = Path(output_dir)

    if watch_mode:
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, _signal_handler)

        console.print(f"[blue]Watch mode enabled[/blue]")
        console.print(f"  Watching: {schema_path}")
        console.print(f"  Press Ctrl+C to stop\n")

        # Run initial generation
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(f"[cyan][{timestamp}] Initial generation...[/cyan]")
        success = _run_generation(schema_path, target, output_path, force, dry_run, show_progress=True)

        if success:
            # Run post-generation setup if enabled
            if setup and not dry_run:
                _run_post_generation_setup(output_path, quiet=_is_quiet_mode())
            console.print(f"\n[blue]Watching for changes...[/blue]\n")
        else:
            console.print(f"\n[yellow]Initial generation failed. Watching for changes...[/yellow]\n")

        # Watch for changes
        try:
            # Watch the schema file's parent directory for changes to the specific file
            watch_path = schema_path.parent if schema_path.parent.exists() else Path(".")

            for changes in watch(watch_path):
                # Check if the schema file was modified
                schema_modified = False
                for change_type, changed_path in changes:
                    if Path(changed_path).resolve() == schema_path.resolve():
                        schema_modified = True
                        break

                if not schema_modified:
                    continue

                # Regenerate on change
                timestamp = datetime.now().strftime("%H:%M:%S")
                console.print(f"[cyan][{timestamp}] File change detected, regenerating...[/cyan]")

                success = _run_generation(schema_path, target, output_path, force, dry_run, show_progress=False)

                if success:
                    console.print(f"[green]✓ Regeneration complete[/green]\n")
                else:
                    console.print(f"[red]✗ Regeneration failed[/red]\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Watch mode stopped[/yellow]")
            sys.exit(0)

    else:
        # Normal mode - run once
        success = _run_generation(schema_path, target, output_path, force, dry_run, show_progress=True)

        if not success:
            raise typer.Exit(code=1)

        # Run post-generation setup if enabled and not dry-run
        if setup and not dry_run:
            _run_post_generation_setup(output_path, quiet=_is_quiet_mode())
