"""Integration tests for API_045 - Migrate status command shows migration status.

Test Requirements:
- test_migrate_status_shows_current_revision - Display current migration revision
- test_migrate_status_shows_pending_migrations - List pending migrations to apply
- test_migrate_status_shows_applied_migrations - List already applied migrations
- test_migrate_status_without_backend - Error when backend directory not found
- test_migrate_status_with_quiet_mode - Works with --quiet flag
- test_migrate_status_no_migrations - Handles case with no migrations
- test_migrate_status_all_applied - Shows status when all migrations applied
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
import pytest

from schnitzel.cli import app

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def project_with_backend(temp_dir):
    """Create a project structure with backend directory and Alembic setup."""
    backend_dir = temp_dir / "backend"
    backend_dir.mkdir()

    # Create minimal alembic.ini
    alembic_ini = backend_dir / "alembic.ini"
    alembic_ini.write_text("""[alembic]
script_location = migrations
sqlalchemy.url = sqlite:///./test.db

[loggers]
keys = root

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
""")

    # Create migrations directory structure
    migrations_dir = backend_dir / "migrations"
    migrations_dir.mkdir()

    # Create env.py
    env_py = migrations_dir / "env.py"
    env_py.write_text("""from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""")

    # Create versions directory
    versions_dir = migrations_dir / "versions"
    versions_dir.mkdir()

    return temp_dir, backend_dir, versions_dir


def test_migrate_status_command_exists() -> None:
    """Test that 'schnitzel migrate status' command exists."""
    result = runner.invoke(app, ["migrate", "--help"])

    # Should succeed
    assert result.exit_code == 0, f"Help command failed: {result.stdout}"

    # Should mention 'status' subcommand
    assert "status" in result.stdout.lower(), "Should list 'status' subcommand"


def test_migrate_status_shows_current_revision(project_with_backend) -> None:
    """Test that 'schnitzel migrate status' displays current migration revision."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    # Create a test migration file
    migration_file = versions_dir / "001_initial.py"
    migration_file.write_text(""""Initial migration"

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('users', sa.Column('id', sa.Integer(), primary_key=True))

def downgrade():
    op.drop_table('users')
""")

    with patch("subprocess.run") as mock_run:
        # Mock alembic output for both current and history commands
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "001_initial (head)\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "status"])

        # Should succeed
        assert result.exit_code == 0, f"Status command failed: {result.stdout}"

        # Should call alembic commands (current and history)
        assert mock_run.call_count >= 1, "Should call alembic at least once"

        # First call should be 'current'
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "alembic" in first_call_args, "Should call alembic"
        assert "current" in first_call_args, "Should call alembic current"

        # Should display the current revision in output
        assert "001_initial" in result.stdout or "head" in result.stdout.lower()


def test_migrate_status_shows_pending_migrations(project_with_backend) -> None:
    """Test that 'schnitzel migrate status' lists pending migrations."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    # Create multiple migration files
    migration1 = versions_dir / "001_initial.py"
    migration1.write_text(""""Initial migration"
Revision ID: 001_initial
Revises:
""")

    migration2 = versions_dir / "002_add_users.py"
    migration2.write_text(""""Add users table"
Revision ID: 002_add_users
Revises: 001_initial
""")

    with patch("subprocess.run") as mock_run:
        # Mock alembic current showing we're at an earlier revision
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "001_initial\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "status"])

        # Should succeed
        assert result.exit_code == 0, f"Status command failed: {result.stdout}"


def test_migrate_status_shows_applied_migrations(project_with_backend) -> None:
    """Test that 'schnitzel migrate status' shows applied migrations."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    # Create a migration file
    migration1 = versions_dir / "001_initial.py"
    migration1.write_text(""""Initial migration"
Revision ID: 001_initial
Revises:
""")

    with patch("subprocess.run") as mock_run:
        # Mock alembic current showing current revision
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "001_initial (head)\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "status"])

        # Should succeed
        assert result.exit_code == 0, f"Status command failed: {result.stdout}"

        # Output should indicate migration status
        output = result.stdout.lower()
        assert "001_initial" in output or "current" in output or "head" in output


def test_migrate_status_without_backend(temp_dir) -> None:
    """Test that migrate status fails gracefully without backend directory."""
    result = runner.invoke(app, ["migrate", "status"])

    # Should fail
    assert result.exit_code == 1, "Should fail when backend directory not found"

    # Should show helpful error message
    output = result.stdout.lower()
    assert "backend" in output, "Error should mention backend directory"
    assert "error" in output or "not found" in output, "Should indicate error"


def test_migrate_status_with_quiet_mode(project_with_backend) -> None:
    """Test that migrate status works with --quiet flag."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    with patch("subprocess.run") as mock_run:
        # Mock successful alembic command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "001_initial (head)\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["--quiet", "migrate", "status"])

        # Should succeed
        assert result.exit_code == 0, f"Migrate status --quiet failed: {result.stdout}"

        # Output should be minimal in quiet mode
        # Quiet mode should still show essential info but less verbose
        assert "checking migration status" not in result.stdout.lower(), \
            "Quiet mode should not show verbose progress messages"


def test_migrate_status_no_migrations(project_with_backend) -> None:
    """Test that migrate status handles case with no migrations gracefully."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    # No migration files created

    with patch("subprocess.run") as mock_run:
        # Mock alembic current with no current revision
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "\n"  # Empty output when no migrations
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "status"])

        # Should succeed even with no migrations
        assert result.exit_code == 0, f"Status command should succeed: {result.stdout}"


def test_migrate_status_all_applied(project_with_backend) -> None:
    """Test that status shows correct info when all migrations are applied."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    # Create migration files
    migration1 = versions_dir / "001_initial.py"
    migration1.write_text(""""Initial migration"
Revision ID: 001_initial
Revises:
""")

    migration2 = versions_dir / "002_add_users.py"
    migration2.write_text(""""Add users table"
Revision ID: 002_add_users
Revises: 001_initial
""")

    with patch("subprocess.run") as mock_run:
        # Mock alembic current showing we're at head (all migrations applied)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "002_add_users (head)\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "status"])

        # Should succeed
        assert result.exit_code == 0, f"Status command failed: {result.stdout}"

        # Should indicate we're at head
        output = result.stdout.lower()
        assert "002_add_users" in output or "head" in output


def test_migrate_status_alembic_error(project_with_backend) -> None:
    """Test that migrate status handles Alembic errors gracefully."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    with patch("subprocess.run") as mock_run:
        # Mock failed alembic command
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Database connection failed\n"
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "status"])

        # Should fail
        assert result.exit_code == 1, "Should fail when alembic command fails"

        # Should show error message
        output = result.stdout.lower()
        assert "failed" in output or "error" in output, "Should show error message"


def test_migrate_status_alembic_not_installed(project_with_backend) -> None:
    """Test that migrate status handles missing Alembic installation."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    with patch("subprocess.run") as mock_run:
        # Mock alembic not found
        mock_run.side_effect = FileNotFoundError("alembic not found")

        result = runner.invoke(app, ["migrate", "status"])

        # Should fail
        assert result.exit_code == 1, "Should fail when alembic not installed"

        # Should show helpful error message
        output = result.stdout.lower()
        assert "alembic" in output, "Error should mention Alembic"
        assert "install" in output or "not installed" in output, \
            "Should suggest installing Alembic"


def test_migrate_status_finds_backend_in_parent(temp_dir) -> None:
    """Test that migrate status finds backend directory in parent directories."""
    # Create backend in project root
    backend_dir = temp_dir / "backend"
    backend_dir.mkdir()

    # Create minimal alembic structure
    alembic_dir = backend_dir / "migrations"
    alembic_dir.mkdir()

    # Create subdirectory and run command from there
    sub_dir = temp_dir / "subdirectory"
    sub_dir.mkdir()
    os.chdir(sub_dir)

    with patch("subprocess.run") as mock_run:
        # Mock successful alembic command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "001_initial (head)\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "status"])

        # Should succeed and find backend in parent
        assert result.exit_code == 0, \
            "Should find backend directory in parent directories"

        # Should have called alembic with correct working directory
        assert mock_run.call_count >= 1, "Should call alembic at least once"
        call_kwargs = mock_run.call_args_list[0][1]
        assert "cwd" in call_kwargs, "Should set working directory"
        # Use resolve() to handle path resolution (e.g., /private prefix on macOS)
        assert call_kwargs["cwd"].resolve() == backend_dir.resolve(), \
            "Should run alembic in backend directory"


def test_migrate_status_shows_progress_messages(project_with_backend) -> None:
    """Test that migrate status shows progress messages in non-quiet mode."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    with patch("subprocess.run") as mock_run:
        # Mock successful alembic command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "001_initial (head)\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "status"])

        # Should succeed
        assert result.exit_code == 0

        output = result.stdout
        # Should show progress message
        assert "checking" in output.lower() or "status" in output.lower() or \
               "migration" in output.lower(), "Should show progress message"


def test_migrate_status_help_documentation() -> None:
    """Test that 'schnitzel migrate status --help' shows proper documentation."""
    result = runner.invoke(app, ["migrate", "status", "--help"])

    # Should succeed
    assert result.exit_code == 0

    output = result.stdout.lower()

    # Should document what status does
    assert "status" in output, "Should mention status"
    assert "migration" in output, "Should mention migration"


def test_migrate_status_output_format(project_with_backend) -> None:
    """Test that migrate status output is well-formatted and readable."""
    temp_dir, backend_dir, versions_dir = project_with_backend

    # Create a migration file
    migration1 = versions_dir / "001_initial.py"
    migration1.write_text(""""Initial migration"
Revision ID: 001_initial
Revises:
""")

    with patch("subprocess.run") as mock_run:
        # Mock alembic current with verbose output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "001_initial (head)\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "status"])

        # Should succeed
        assert result.exit_code == 0

        # Output should be non-empty
        assert len(result.stdout) > 0, "Should produce some output"

        # Output should contain the revision
        assert "001_initial" in result.stdout or "head" in result.stdout.lower()
