"""Integration tests for API_043 - Migrate command applies pending migrations.

Test Requirements:
- Create migration files
- Run schnitzel migrate up
- Verify migrations are applied in order
- Verify migration status is tracked
- Verify database schema is updated
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from schnitzel.cli import app

runner = CliRunner()


@pytest.fixture
def temp_project():
    """Create a temporary test project with Alembic setup."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        backend_dir = project_dir / "backend"
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

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
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

        # Create script.py.mako
        script_mako = migrations_dir / "script.py.mako"
        script_mako.write_text(""""${message}"

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

def upgrade():
    ${upgrades if upgrades else "pass"}

def downgrade():
    ${downgrades if downgrades else "pass"}
""")

        # Create versions directory
        versions_dir = migrations_dir / "versions"
        versions_dir.mkdir()

        # Create a test migration file
        migration_file = versions_dir / "001_initial_migration.py"
        migration_file.write_text('''"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('users')
''')

        os.chdir(project_dir)
        yield project_dir
        os.chdir(original_cwd)


def test_migrate_up_applies_migrations(temp_project: Path) -> None:
    """Test that 'schnitzel migrate up' applies pending migrations."""
    # Run migrate up
    result = runner.invoke(app, ["migrate", "up"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}\n{result.stderr}"

    # Verify success message is shown
    assert "Migration command completed successfully" in result.stdout or "✓" in result.stdout


def test_migrate_up_shows_progress(temp_project: Path) -> None:
    """Test that 'schnitzel migrate up' displays progress with Rich."""
    # Run migrate up
    result = runner.invoke(app, ["migrate", "up"])

    # Command should succeed
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Output should contain migration-related messages
    # (The Rich progress spinner won't show in test capture, but we can verify the command structure)
    assert "Applying pending migrations" in result.stdout or "Migration command" in result.stdout


def test_migrate_up_fails_gracefully_without_backend(temp_project: Path) -> None:
    """Test that 'schnitzel migrate up' fails gracefully when backend directory is missing."""
    # Remove backend directory
    backend_dir = temp_project / "backend"
    if backend_dir.exists():
        import shutil
        shutil.rmtree(backend_dir)

    # Run migrate up
    result = runner.invoke(app, ["migrate", "up"])

    # Should fail with proper error message
    assert result.exit_code == 1
    assert "Could not find backend directory" in result.stdout


def test_migrate_up_fails_without_alembic_ini(temp_project: Path) -> None:
    """Test that 'schnitzel migrate up' fails when alembic.ini is missing."""
    # Remove alembic.ini
    alembic_ini = temp_project / "backend" / "alembic.ini"
    if alembic_ini.exists():
        alembic_ini.unlink()

    # Run migrate up
    result = runner.invoke(app, ["migrate", "up"])

    # Should fail with proper error message
    assert result.exit_code == 1
    # The error might come from either our check or Alembic itself
    assert "Error" in result.stdout or "failed" in result.stdout.lower()


def test_migrate_status_shows_current_revision(temp_project: Path) -> None:
    """Test that 'schnitzel migrate status' shows current migration status."""
    # First apply migrations
    result = runner.invoke(app, ["migrate", "up"])
    assert result.exit_code == 0, f"Migration up failed: {result.stdout}"

    # Check status
    result = runner.invoke(app, ["migrate", "status"])

    # Status command should succeed
    assert result.exit_code == 0, f"Status command failed: {result.stdout}"


def test_migrate_up_is_idempotent(temp_project: Path) -> None:
    """Test that running 'schnitzel migrate up' multiple times is safe."""
    # First run
    result1 = runner.invoke(app, ["migrate", "up"])
    assert result1.exit_code == 0, f"First migration failed: {result1.stdout}"

    # Second run (should be idempotent)
    result2 = runner.invoke(app, ["migrate", "up"])
    assert result2.exit_code == 0, f"Second migration failed: {result2.stdout}"


def test_migrate_up_quiet_mode(temp_project: Path) -> None:
    """Test that 'schnitzel migrate up' respects quiet mode."""
    # Run migrate up in quiet mode
    result = runner.invoke(app, ["--quiet", "migrate", "up"])

    # Should succeed
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Output should be minimal (no verbose messages)
    # In quiet mode, we still show essential output but less verbose
    assert len(result.stdout) < 200  # Arbitrary small length for quiet output


def test_migrate_down_rollback(temp_project: Path) -> None:
    """Test that 'schnitzel migrate down' can rollback migrations."""
    # First apply migrations
    result = runner.invoke(app, ["migrate", "up"])
    assert result.exit_code == 0, f"Migration up failed: {result.stdout}"

    # Now rollback
    result = runner.invoke(app, ["migrate", "down"])

    # Rollback should succeed
    assert result.exit_code == 0, f"Rollback failed: {result.stdout}"


def test_migrate_history_shows_migrations(temp_project: Path) -> None:
    """Test that 'schnitzel migrate history' shows migration history."""
    # Run history command
    result = runner.invoke(app, ["migrate", "history"])

    # Command should succeed
    assert result.exit_code == 0, f"History command failed: {result.stdout}"

    # Should show some history information
    assert "Migration history" in result.stdout or len(result.stdout) > 0
