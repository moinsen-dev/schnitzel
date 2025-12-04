"""Integration tests for F043 - Init command runs flutter create for packages/app.

Test Requirements:
- test_init_without_flutter_flag_creates_empty_packages_app
- test_init_with_flutter_flag_attempts_flutter_create
- test_init_handles_flutter_not_installed (mock subprocess)
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


def test_init_without_flutter_flag_creates_empty_packages_app(temp_dir: Path) -> None:
    """Test that init command without --with-flutter flag creates empty packages/app directory."""
    project_name = "test-project"

    # Run init command without --with-flutter flag
    result = runner.invoke(app, ["init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify packages/app directory exists and is empty (except README)
    packages_dir = temp_dir / project_name / "packages" / "app"
    assert packages_dir.exists(), "packages/app directory not created"
    assert packages_dir.is_dir(), "packages/app is not a directory"

    # Verify README.md was created (indicating it's a placeholder, not Flutter app)
    readme_file = packages_dir / "README.md"
    assert readme_file.exists(), "README.md should exist for non-Flutter apps"
    readme_content = readme_file.read_text()
    assert "Flutter App" in readme_content or "Flutter application" in readme_content

    # Verify no Flutter project files exist (like pubspec.yaml)
    pubspec_file = packages_dir / "pubspec.yaml"
    assert not pubspec_file.exists(), "pubspec.yaml should not exist without --with-flutter"


def test_init_with_flutter_flag_attempts_flutter_create(temp_dir: Path) -> None:
    """Test that init command with --with-flutter flag attempts to run flutter create."""
    project_name = "test-flutter-project"

    # Mock subprocess to simulate Flutter being installed and working
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # First call: flutter --version (check if installed)
        # Second call: flutter create (actual creation)
        mock_version_result = MagicMock()
        mock_version_result.returncode = 0

        mock_create_result = MagicMock()
        mock_create_result.returncode = 0
        mock_create_result.stderr = ""

        mock_run.side_effect = [mock_version_result, mock_create_result]

        # Run init command with --with-flutter flag
        result = runner.invoke(app, ["init", project_name, "--with-flutter"])

        # Verify command succeeded
        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Verify subprocess.run was called twice
        assert mock_run.call_count == 2, "subprocess.run should be called twice (version check + create)"

        # Verify first call was flutter --version
        first_call = mock_run.call_args_list[0]
        assert first_call[0][0] == ["flutter", "--version"], "First call should be flutter --version"

        # Verify second call was flutter create with correct parameters
        second_call = mock_run.call_args_list[1]
        flutter_create_cmd = second_call[0][0]
        assert flutter_create_cmd[0] == "flutter", "Should call flutter command"
        assert flutter_create_cmd[1] == "create", "Should call create subcommand"
        assert "--project-name" in flutter_create_cmd, "Should include --project-name flag"

        # Project name should be sanitized (hyphens -> underscores)
        project_name_idx = flutter_create_cmd.index("--project-name")
        actual_project_name = flutter_create_cmd[project_name_idx + 1]
        assert actual_project_name == "test_flutter_project_app", \
            f"Should use sanitized project_name_app, got {actual_project_name}"

        # Verify output shows Flutter app creation
        output = result.stdout
        assert "Creating Flutter app" in output or "Flutter" in output


def test_init_handles_flutter_not_installed(temp_dir: Path) -> None:
    """Test that init command handles gracefully when Flutter is not installed."""
    project_name = "test-no-flutter"

    # Mock subprocess to simulate Flutter not being installed
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # Simulate FileNotFoundError when trying to run flutter --version
        mock_run.side_effect = FileNotFoundError("flutter command not found")

        # Run init command with --with-flutter flag
        result = runner.invoke(app, ["init", project_name, "--with-flutter"])

        # Verify command still succeeds (doesn't fail)
        assert result.exit_code == 0, f"Command should succeed even without Flutter: {result.stdout}"

        # Verify packages/app directory was still created
        packages_dir = temp_dir / project_name / "packages" / "app"
        assert packages_dir.exists(), "packages/app directory should still be created"

        # Verify warning message about Flutter not being installed
        output = result.stdout
        assert "Warning" in output or "not installed" in output or "not in PATH" in output, \
            "Should show warning about Flutter not being installed"

        # Verify README.md was created (fallback behavior)
        readme_file = packages_dir / "README.md"
        assert readme_file.exists(), "README.md should be created as fallback"

        # Verify project structure was still created successfully
        schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
        assert schema_file.exists(), "schema.schnitzel.yaml should still be created"


def test_init_with_flutter_flag_handles_flutter_create_failure(temp_dir: Path) -> None:
    """Test that init command handles gracefully when flutter create fails."""
    project_name = "test-flutter-fail"

    # Mock subprocess to simulate Flutter installed but create fails
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # First call: flutter --version (succeeds)
        mock_version_result = MagicMock()
        mock_version_result.returncode = 0

        # Second call: flutter create (fails)
        mock_create_result = MagicMock()
        mock_create_result.returncode = 1
        mock_create_result.stderr = "Error: Failed to create Flutter project"

        mock_run.side_effect = [mock_version_result, mock_create_result]

        # Run init command with --with-flutter flag
        result = runner.invoke(app, ["init", project_name, "--with-flutter"])

        # Verify command still succeeds
        assert result.exit_code == 0, f"Command should succeed even if Flutter create fails: {result.stdout}"

        # Verify packages/app directory was still created (fallback)
        packages_dir = temp_dir / project_name / "packages" / "app"
        assert packages_dir.exists(), "packages/app directory should still be created as fallback"

        # Verify warning message about Flutter create failure
        output = result.stdout
        assert "Warning" in output or "failed" in output, \
            "Should show warning about Flutter create failure"

        # Verify README.md was created (fallback behavior)
        readme_file = packages_dir / "README.md"
        assert readme_file.exists(), "README.md should be created as fallback"


def test_init_with_flutter_creates_project_with_correct_name(temp_dir: Path) -> None:
    """Test that Flutter project is created with correct naming convention (sanitized_project_name_app)."""
    project_name = "my-awesome-project"

    # Mock subprocess to simulate Flutter working
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_version_result = MagicMock()
        mock_version_result.returncode = 0

        mock_create_result = MagicMock()
        mock_create_result.returncode = 0
        mock_create_result.stderr = ""

        mock_run.side_effect = [mock_version_result, mock_create_result]

        # Run init command with --with-flutter flag
        result = runner.invoke(app, ["init", project_name, "--with-flutter"])

        assert result.exit_code == 0

        # Verify the project name passed to flutter create
        second_call = mock_run.call_args_list[1]
        flutter_create_cmd = second_call[0][0]

        # Find --project-name flag and verify next argument
        project_name_idx = flutter_create_cmd.index("--project-name")
        actual_project_name = flutter_create_cmd[project_name_idx + 1]

        # Hyphens should be converted to underscores for valid Dart package names
        assert actual_project_name == "my_awesome_project_app", \
            f"Project name should be 'my_awesome_project_app' (sanitized), got '{actual_project_name}'"


def test_init_with_flutter_sanitizes_project_name(temp_dir: Path) -> None:
    """Test that project names with hyphens and special characters are sanitized for Dart."""
    test_cases = [
        ("test-flutter-demo", "test_flutter_demo_app"),
        ("123project", "app_123project_app"),
        ("My Project!", "my_project_app"),
    ]

    for project_name, expected_dart_name in test_cases:
        # Mock subprocess to simulate Flutter working
        with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
            mock_version_result = MagicMock()
            mock_version_result.returncode = 0

            mock_create_result = MagicMock()
            mock_create_result.returncode = 0
            mock_create_result.stderr = ""

            mock_run.side_effect = [mock_version_result, mock_create_result]

            # Run init command with --with-flutter flag
            result = runner.invoke(app, ["init", project_name, "--with-flutter"])

            # Skip if project already exists from previous test iteration
            if result.exit_code == 1 and "already exists" in result.stdout:
                continue

            assert result.exit_code == 0, f"Command failed for {project_name}: {result.stdout}"

            # Verify the sanitized project name
            second_call = mock_run.call_args_list[1]
            flutter_create_cmd = second_call[0][0]
            project_name_idx = flutter_create_cmd.index("--project-name")
            actual_project_name = flutter_create_cmd[project_name_idx + 1]

            assert actual_project_name == expected_dart_name, \
                f"For project '{project_name}', expected '{expected_dart_name}', got '{actual_project_name}'"


def test_init_with_flutter_timeout_handling(temp_dir: Path) -> None:
    """Test that init command handles flutter create timeout gracefully."""
    project_name = "test-timeout"

    # Mock subprocess to simulate timeout
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # First call: flutter --version (succeeds)
        mock_version_result = MagicMock()
        mock_version_result.returncode = 0

        # Second call: flutter create (times out)
        def side_effect(*args, **kwargs):
            if args[0] == ["flutter", "--version"]:
                return mock_version_result
            else:
                raise subprocess.TimeoutExpired(cmd="flutter create", timeout=120)

        mock_run.side_effect = side_effect

        # Run init command with --with-flutter flag
        result = runner.invoke(app, ["init", project_name, "--with-flutter"])

        # Verify command still succeeds
        assert result.exit_code == 0, f"Command should succeed even if Flutter times out: {result.stdout}"

        # Verify warning about timeout
        output = result.stdout
        assert "timeout" in output.lower() or "Warning" in output, \
            "Should show warning about timeout"

        # Verify fallback directory was created
        packages_dir = temp_dir / project_name / "packages" / "app"
        assert packages_dir.exists(), "packages/app directory should be created as fallback"
