"""Integration tests for F044 - Init command runs uv init for backend.

Test Requirements:
- test_init_without_backend_flag_creates_empty_backend_app
- test_init_with_backend_flag_attempts_uv_init
- test_init_handles_uv_not_installed (mock subprocess)
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
import subprocess
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


def test_init_without_backend_flag_creates_empty_backend_app(temp_dir: Path) -> None:
    """Test that init command without --with-backend flag creates empty backend/app directory."""
    project_name = "test-project"

    # Run init command without --with-backend flag
    result = runner.invoke(app, ["init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify backend/app directory exists
    backend_dir = temp_dir / project_name / "backend" / "app"
    assert backend_dir.exists(), "backend/app/ directory not created"
    assert backend_dir.is_dir(), "backend/app/ is not a directory"

    # Verify README.md was created (not created by uv init)
    backend_readme = backend_dir / "README.md"
    assert backend_readme.exists(), "backend README should exist when uv init not used"
    assert "FastAPI Backend" in backend_readme.read_text()

    # Verify pyproject.toml was NOT created (would be created by uv init)
    pyproject_file = backend_dir / "pyproject.toml"
    assert not pyproject_file.exists(), "pyproject.toml should not exist without --with-backend"


def test_init_with_backend_flag_attempts_uv_init(temp_dir: Path) -> None:
    """Test that init command with --with-backend flag attempts to run uv init."""
    project_name = "test-project"

    # Mock subprocess.run to simulate successful uv execution
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # Mock uv --version check (first call)
        # Mock uv init (second call)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),  # uv --version
            MagicMock(returncode=0, stdout="Initialized project", stderr="")  # uv init
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        # Verify command succeeded
        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Verify uv init was called
        assert mock_run.call_count == 2, "Expected 2 subprocess calls (version check + uv init)"

        # Verify the second call was uv init with correct path
        init_call = mock_run.call_args_list[1]
        assert init_call[0][0][0] == "uv", "Expected uv command"
        assert init_call[0][0][1] == "init", "Expected init subcommand"

        # Verify success message
        assert "Python backend initialized successfully" in result.stdout or "✓" in result.stdout


def test_init_handles_uv_not_installed(temp_dir: Path) -> None:
    """Test that init command handles gracefully when uv is not installed."""
    project_name = "test-project"

    # Mock subprocess.run to simulate uv not being installed
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # Simulate FileNotFoundError when checking for uv --version
        mock_run.side_effect = FileNotFoundError("uv not found")

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        # Verify command succeeded (continues without backend init)
        assert result.exit_code == 0, f"Command should succeed even without uv: {result.stdout}"

        # Verify warning message was shown
        assert "uv not installed" in result.stdout, \
            f"Expected uv not installed message in output: {result.stdout}"

        # Verify backend directory still exists (fallback)
        backend_dir = temp_dir / project_name / "backend" / "app"
        assert backend_dir.exists(), "backend/app/ should exist as fallback"

        # Verify README.md was created (fallback behavior)
        backend_readme = backend_dir / "README.md"
        assert backend_readme.exists(), "backend README should exist as fallback"


def test_init_with_backend_flag_handles_uv_init_failure(temp_dir: Path) -> None:
    """Test that init handles gracefully when uv init fails."""
    project_name = "test-project"

    # Mock subprocess.run to simulate uv init failure
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # Mock successful version check but failed uv init
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),  # uv --version
            MagicMock(returncode=1, stdout="", stderr="Error: failed to init")  # uv init fails
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        # Verify command succeeded (continues with fallback)
        assert result.exit_code == 0, f"Command should succeed with fallback: {result.stdout}"

        # Verify warning message was shown
        assert "uv init failed" in result.stdout, \
            f"Expected uv init failed message in output: {result.stdout}"

        # Verify backend directory exists (fallback)
        backend_dir = temp_dir / project_name / "backend" / "app"
        assert backend_dir.exists(), "backend/app/ should exist as fallback"


def test_init_with_backend_shows_progress(temp_dir: Path) -> None:
    """Test that init command shows progress/status messages during uv init."""
    project_name = "test-project"

    # Mock subprocess.run to simulate successful uv execution
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),  # uv --version
            MagicMock(returncode=0, stdout="Initialized project", stderr="")  # uv init
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        # Verify progress messages are shown
        # With the new progress format, we show "✓ Created backend/app/ (Python project)"
        assert "backend/app" in result.stdout, "Should show backend creation message"
        assert "✓" in result.stdout or "successfully" in result.stdout.lower(), "Should show success message"


def test_init_backend_creates_in_correct_directory(temp_dir: Path) -> None:
    """Test that uv init is called with the correct directory path."""
    project_name = "test-project"

    # Mock subprocess.run
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),
            MagicMock(returncode=0, stdout="", stderr="")
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Verify uv init was called with backend/app path
        init_call = mock_run.call_args_list[1]
        backend_path = str(temp_dir / project_name / "backend" / "app")
        assert backend_path in str(init_call[0][0][2]), f"Expected backend/app path in uv init call"


def test_init_with_both_flutter_and_backend_flags(temp_dir: Path) -> None:
    """Test that both --with-flutter and --with-backend flags can be used together."""
    project_name = "test-project"

    # Mock subprocess.run for both flutter and uv
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # Mock: flutter --version, uv --version, flutter create, uv init
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Flutter 3.0", stderr=""),  # flutter --version
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),  # uv --version
            MagicMock(returncode=0, stdout="Flutter app created", stderr=""),  # flutter create
            MagicMock(returncode=0, stdout="Initialized project", stderr="")  # uv init
        ]

        # Run init command with both flags
        result = runner.invoke(app, ["init", project_name, "--with-flutter", "--with-backend"])

        # Verify command succeeded
        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Verify both flutter and backend messages appear
        assert "Flutter" in result.stdout or "packages/app" in result.stdout, \
            "Should show Flutter creation message"
        assert "backend/app" in result.stdout, "Should show backend creation message"


def test_init_backend_timeout_handling(temp_dir: Path) -> None:
    """Test that init handles uv init timeout gracefully."""
    project_name = "test-project"

    # Mock subprocess.run to simulate timeout
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),  # uv --version
            subprocess.TimeoutExpired("uv", 60)  # uv init times out
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        # Verify command succeeded with fallback
        assert result.exit_code == 0, f"Command should handle timeout gracefully: {result.stdout}"

        # Verify warning message (with new format, timeouts show as "uv init failed")
        output_lower = result.stdout.lower()
        assert "uv init failed" in output_lower or "✗" in result.stdout, \
            f"Expected failure message in output: {result.stdout}"

        # Verify fallback directory exists
        backend_dir = temp_dir / project_name / "backend" / "app"
        assert backend_dir.exists(), "backend/app/ should exist as fallback after timeout"
