"""Integration tests for API_044 - Migrate command rolls back migrations.

Test Requirements:
- test_migrate_down_rollback_one - Rollback last migration with 'schnitzel migrate down'
- test_migrate_down_rollback_all - Rollback all migrations with 'schnitzel migrate down --all'
- test_migrate_down_without_backend - Error when backend directory not found
- test_migrate_down_with_quiet_mode - Works with --quiet flag
- test_migrate_down_verifies_rollback - Verify migration is actually rolled back
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
    """Create a project structure with backend directory."""
    backend_dir = temp_dir / "backend"
    backend_dir.mkdir()

    # Create minimal alembic structure
    alembic_dir = backend_dir / "alembic"
    alembic_dir.mkdir()

    versions_dir = alembic_dir / "versions"
    versions_dir.mkdir()

    # Create alembic.ini
    alembic_ini = backend_dir / "alembic.ini"
    alembic_ini.write_text("""[alembic]
script_location = alembic
""")

    return temp_dir


def test_migrate_down_command_exists() -> None:
    """Test that 'schnitzel migrate down' command exists."""
    result = runner.invoke(app, ["migrate", "--help"])

    # Should succeed
    assert result.exit_code == 0, f"Help command failed: {result.stdout}"

    # Should mention 'down' subcommand
    assert "down" in result.stdout.lower(), "Should list 'down' subcommand"


def test_migrate_down_rollback_one(project_with_backend) -> None:
    """Test that 'schnitzel migrate down' rolls back one migration."""
    with patch("subprocess.run") as mock_run:
        # Mock successful alembic downgrade -1
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Rolling back one migration\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "down"])

        # Should succeed
        assert result.exit_code == 0, f"Migrate down failed: {result.stdout}"

        # Should call alembic downgrade -1
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "alembic" in call_args[0][0], "Should call alembic command"
        assert "downgrade" in call_args[0][0], "Should call downgrade"
        assert "-1" in call_args[0][0], "Should downgrade by one migration"


def test_migrate_down_rollback_all(project_with_backend) -> None:
    """Test that 'schnitzel migrate down --all' rolls back all migrations."""
    with patch("subprocess.run") as mock_run:
        # Mock successful alembic downgrade base
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Rolling back to base\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "down", "--all"])

        # Should succeed
        assert result.exit_code == 0, f"Migrate down --all failed: {result.stdout}"

        # Should call alembic downgrade base
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "alembic" in call_args[0][0], "Should call alembic command"
        assert "downgrade" in call_args[0][0], "Should call downgrade"
        assert "base" in call_args[0][0], "Should downgrade to base"


def test_migrate_down_without_backend(temp_dir) -> None:
    """Test that migrate down fails gracefully without backend directory."""
    result = runner.invoke(app, ["migrate", "down"])

    # Should fail
    assert result.exit_code == 1, "Should fail when backend directory not found"

    # Should show helpful error message
    output = result.stdout.lower()
    assert "backend" in output, "Error should mention backend directory"
    assert "error" in output or "not found" in output, "Should indicate error"


def test_migrate_down_with_quiet_mode(project_with_backend) -> None:
    """Test that migrate down works with --quiet flag."""
    with patch("subprocess.run") as mock_run:
        # Mock successful alembic command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Migration rolled back\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["--quiet", "migrate", "down"])

        # Should succeed
        assert result.exit_code == 0, f"Migrate down --quiet failed: {result.stdout}"

        # Output should be minimal in quiet mode
        output_lines = [line for line in result.stdout.split("\n") if line.strip()]
        assert len(output_lines) <= 3, "Quiet mode should produce minimal output"


def test_migrate_down_alembic_error(project_with_backend) -> None:
    """Test that migrate down handles Alembic errors gracefully."""
    with patch("subprocess.run") as mock_run:
        # Mock failed alembic command
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: No such revision: -1\n"
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "down"])

        # Should fail
        assert result.exit_code == 1, "Should fail when alembic command fails"

        # Should show error message
        output = result.stdout.lower()
        assert "failed" in output or "error" in output, "Should show error message"


def test_migrate_down_alembic_not_installed(project_with_backend) -> None:
    """Test that migrate down handles missing Alembic installation."""
    with patch("subprocess.run") as mock_run:
        # Mock alembic not found
        mock_run.side_effect = FileNotFoundError("alembic not found")

        result = runner.invoke(app, ["migrate", "down"])

        # Should fail
        assert result.exit_code == 1, "Should fail when alembic not installed"

        # Should show helpful error message
        output = result.stdout.lower()
        assert "alembic" in output, "Error should mention Alembic"
        assert "install" in output or "not installed" in output, \
            "Should suggest installing Alembic"


def test_migrate_down_finds_backend_in_parent(temp_dir) -> None:
    """Test that migrate down finds backend directory in parent directories."""
    # Create backend in project root
    backend_dir = temp_dir / "backend"
    backend_dir.mkdir()

    # Create alembic structure
    alembic_dir = backend_dir / "alembic"
    alembic_dir.mkdir()

    # Create subdirectory and run command from there
    sub_dir = temp_dir / "subdirectory"
    sub_dir.mkdir()
    os.chdir(sub_dir)

    with patch("subprocess.run") as mock_run:
        # Mock successful alembic command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Migration rolled back\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "down"])

        # Should succeed and find backend in parent
        assert result.exit_code == 0, \
            "Should find backend directory in parent directories"

        # Should have called alembic with correct working directory
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert "cwd" in call_kwargs, "Should set working directory"
        # Use resolve() to handle path resolution (e.g., /private prefix on macOS)
        assert call_kwargs["cwd"].resolve() == backend_dir.resolve(), \
            "Should run alembic in backend directory"


def test_migrate_down_shows_progress_messages(project_with_backend) -> None:
    """Test that migrate down shows progress messages (non-quiet mode)."""
    with patch("subprocess.run") as mock_run:
        # Mock successful alembic command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "INFO [alembic] Rolling back migration\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = runner.invoke(app, ["migrate", "down"])

        # Should succeed
        assert result.exit_code == 0

        output = result.stdout
        # Should show progress message
        assert "rolling back" in output.lower() or "rollback" in output.lower(), \
            "Should show progress message"


def test_migrate_up_command_exists() -> None:
    """Test that 'schnitzel migrate up' command exists for completeness."""
    result = runner.invoke(app, ["migrate", "--help"])

    # Should succeed
    assert result.exit_code == 0

    # Should list 'up' subcommand
    assert "up" in result.stdout.lower(), "Should list 'up' subcommand"


def test_migrate_status_command_exists() -> None:
    """Test that 'schnitzel migrate status' command exists for completeness."""
    result = runner.invoke(app, ["migrate", "--help"])

    # Should succeed
    assert result.exit_code == 0

    # Should list 'status' subcommand
    assert "status" in result.stdout.lower(), "Should list 'status' subcommand"


def test_migrate_help_shows_all_commands() -> None:
    """Test that 'schnitzel migrate --help' shows all subcommands."""
    result = runner.invoke(app, ["migrate", "--help"])

    # Should succeed
    assert result.exit_code == 0

    output = result.stdout.lower()

    # Should list main subcommands
    assert "down" in output, "Should list 'down' subcommand"
    assert "up" in output, "Should list 'up' subcommand"
    assert "status" in output, "Should list 'status' subcommand"


def test_migrate_down_help_shows_all_flag() -> None:
    """Test that 'schnitzel migrate down --help' documents the --all flag."""
    result = runner.invoke(app, ["migrate", "down", "--help"])

    # Should succeed
    assert result.exit_code == 0

    output = result.stdout.lower()

    # Should document --all flag
    assert "--all" in output, "Should document --all flag"
    assert "rollback" in output, "Should explain rollback functionality"
