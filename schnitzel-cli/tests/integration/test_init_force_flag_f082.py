"""Integration tests for F082 - Init command with --force flag overwrites existing directory.

Feature: F082 - Init command with --force flag overwrites existing directory
Context: The CLI init command is at src/schnitzel/cli/commands/init.py.

Expected Behavior:
- Init with --force should overwrite existing directories/files
- Init without --force should fail if directory already exists
- Both --force and -f short form should work

Test Requirements:
- test_init_force_overwrites - --force should overwrite existing
- test_init_without_force_fails - without --force should fail on existing dir
- test_force_short_flag - -f should work as short form
"""

import tempfile
import os
from pathlib import Path
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


def test_init_force_overwrites(temp_dir: Path) -> None:
    """Test that init with --force flag overwrites existing directory.

    Verification:
    - Create an existing directory with files
    - Run init with --force flag
    - Command should succeed (exit code 0)
    - Old files should be gone, new project files should exist
    """
    project_name = "test-project"
    project_path = temp_dir / project_name

    # Create existing directory with a file
    project_path.mkdir()
    old_file = project_path / "old-file.txt"
    old_file.write_text("This should be deleted")

    # Verify directory exists with old file
    assert project_path.exists(), "Precondition: Directory should exist"
    assert old_file.exists(), "Precondition: Old file should exist"

    # Run init command with --force
    result = runner.invoke(app, ["init", project_name, "--force"])

    # Verify command succeeded
    assert result.exit_code == 0, (
        f"Command should succeed with --force flag. "
        f"Got exit code: {result.exit_code}\n"
        f"Output: {result.stdout}"
    )

    # Verify project was created
    assert project_path.exists(), "Project directory should exist"

    # Verify new project files were created
    schema_file = project_path / "schema.schnitzel.yaml"
    docker_file = project_path / "docker-compose.yaml"
    assert schema_file.exists(), "schema.schnitzel.yaml should be created"
    assert docker_file.exists(), "docker-compose.yaml should be created"

    # Verify old file was removed
    assert not old_file.exists(), "Old file should be removed"


def test_init_without_force_fails(temp_dir: Path) -> None:
    """Test that init without --force fails when directory exists.

    Verification:
    - Create an existing directory
    - Run init without --force flag
    - Command should fail (exit code 1)
    - Error message should mention directory exists
    """
    project_name = "existing-project"
    project_path = temp_dir / project_name

    # Create existing directory
    project_path.mkdir()

    # Run init command without --force
    result = runner.invoke(app, ["init", project_name])

    # Verify command failed
    assert result.exit_code == 1, (
        f"Command should fail without --force when directory exists. "
        f"Got exit code: {result.exit_code}\n"
        f"Output: {result.stdout}"
    )

    # Verify error message mentions directory exists
    assert "already exists" in result.stdout, (
        f"Error message should mention 'already exists'. Got: {result.stdout}"
    )


def test_force_short_flag(temp_dir: Path) -> None:
    """Test that -f works as short form of --force.

    Verification:
    - Create an existing directory
    - Run init with -f flag
    - Command should succeed (exit code 0)
    - New project should be created
    """
    project_name = "test-project"
    project_path = temp_dir / project_name

    # Create existing directory with a file
    project_path.mkdir()
    old_file = project_path / "old-file.txt"
    old_file.write_text("This should be deleted")

    # Run init command with -f (short form)
    result = runner.invoke(app, ["init", project_name, "-f"])

    # Verify command succeeded
    assert result.exit_code == 0, (
        f"Command should succeed with -f flag. "
        f"Got exit code: {result.exit_code}\n"
        f"Output: {result.stdout}"
    )

    # Verify project was created
    assert project_path.exists(), "Project directory should exist"

    # Verify new project files were created
    schema_file = project_path / "schema.schnitzel.yaml"
    assert schema_file.exists(), "schema.schnitzel.yaml should be created"

    # Verify old file was removed
    assert not old_file.exists(), "Old file should be removed"


def test_force_overwrites_with_subdirectories(temp_dir: Path) -> None:
    """Test that --force overwrites directories with complex structure.

    Verification:
    - Create directory with subdirectories and nested files
    - Run init with --force
    - Should succeed and create clean new project
    - Old structure should be completely removed
    """
    project_name = "complex-project"
    project_path = temp_dir / project_name

    # Create complex directory structure
    project_path.mkdir()
    (project_path / "src").mkdir()
    (project_path / "src" / "nested").mkdir()
    (project_path / "src" / "file.py").write_text("old code")
    (project_path / "src" / "nested" / "deep.py").write_text("deep code")
    (project_path / "config.json").write_text('{"old": "config"}')

    # Verify complex structure exists
    assert (project_path / "src" / "nested" / "deep.py").exists()

    # Run init with --force
    result = runner.invoke(app, ["init", project_name, "--force"])

    # Verify command succeeded
    assert result.exit_code == 0

    # Verify old structure is gone
    assert not (project_path / "src" / "file.py").exists()
    assert not (project_path / "src" / "nested" / "deep.py").exists()
    assert not (project_path / "config.json").exists()

    # Verify new project structure exists
    schema_file = project_path / "schema.schnitzel.yaml"
    assert schema_file.exists(), "New project should be created"


def test_force_with_file_not_directory(temp_dir: Path) -> None:
    """Test that --force handles case where a file exists with project name.

    Verification:
    - Create a file (not directory) with project name
    - Run init with --force
    - Should remove file and create directory
    """
    project_name = "project-as-file"
    file_path = temp_dir / project_name

    # Create a file instead of directory
    file_path.write_text("This is a file")
    assert file_path.is_file(), "Precondition: Should be a file"

    # Run init with --force
    result = runner.invoke(app, ["init", project_name, "--force"])

    # Verify command succeeded
    assert result.exit_code == 0

    # Verify file was removed and directory created
    project_path = temp_dir / project_name
    assert project_path.exists(), "Project should exist"
    assert project_path.is_dir(), "Project should be a directory"

    # Verify new project files exist
    schema_file = project_path / "schema.schnitzel.yaml"
    assert schema_file.exists(), "schema.schnitzel.yaml should be created"


def test_force_shows_warning_message(temp_dir: Path) -> None:
    """Test that --force shows a warning before removing directory.

    Verification:
    - Create existing directory
    - Run init with --force
    - Output should contain warning about removal
    """
    project_name = "test-project"
    project_path = temp_dir / project_name
    project_path.mkdir()

    # Run init with --force
    result = runner.invoke(app, ["init", project_name, "--force"])

    # Verify command succeeded
    assert result.exit_code == 0

    # Verify warning message is shown
    output = result.stdout
    assert "Warning" in output or "warning" in output.lower(), (
        f"Output should contain warning about removal. Got: {output}"
    )
    assert project_name in output, (
        f"Warning should mention the project name. Got: {output}"
    )


def test_force_with_templates(temp_dir: Path) -> None:
    """Test that --force works with different template options.

    Verification:
    - Create existing directory
    - Run init with --force and --template full
    - Should succeed and create project with full template
    """
    project_name = "template-project"
    project_path = temp_dir / project_name
    project_path.mkdir()

    # Run init with --force and --template full
    result = runner.invoke(app, ["init", project_name, "--force", "--template", "full"])

    # Verify command succeeded
    assert result.exit_code == 0

    # Verify project was created with full template
    schema_file = project_path / "schema.schnitzel.yaml"
    assert schema_file.exists()

    # Verify full template content (should have example models)
    schema_content = schema_file.read_text()
    assert "User" in schema_content, "Full template should include User model"
    assert "Post" in schema_content, "Full template should include Post model"


def test_force_preserves_behavior_for_nonexistent_dir(temp_dir: Path) -> None:
    """Test that --force doesn't break normal behavior when directory doesn't exist.

    Verification:
    - Ensure directory doesn't exist
    - Run init with --force
    - Should succeed normally (same as without --force)
    """
    project_name = "new-project"
    project_path = temp_dir / project_name

    # Verify directory doesn't exist
    assert not project_path.exists()

    # Run init with --force
    result = runner.invoke(app, ["init", project_name, "--force"])

    # Verify command succeeded
    assert result.exit_code == 0

    # Verify project was created
    assert project_path.exists()
    schema_file = project_path / "schema.schnitzel.yaml"
    assert schema_file.exists()


def test_force_with_backend_and_flutter_flags(temp_dir: Path) -> None:
    """Test that --force works with --with-backend and --with-flutter flags.

    Verification:
    - Create existing directory
    - Run init with --force, --with-backend, and --with-flutter
    - Should succeed and create project with all features
    """
    project_name = "full-stack-project"
    project_path = temp_dir / project_name
    project_path.mkdir()

    # Run init with multiple flags
    result = runner.invoke(app, [
        "init", project_name,
        "--force",
        "--with-backend",
        "--with-flutter"
    ])

    # Verify command succeeded
    assert result.exit_code == 0

    # Verify project structure was created
    assert project_path.exists()
    assert (project_path / "schema.schnitzel.yaml").exists()
    assert (project_path / "packages" / "app").exists()
    assert (project_path / "backend" / "app").exists()


def test_multiple_force_operations(temp_dir: Path) -> None:
    """Test that --force can be used multiple times on the same directory.

    Verification:
    - Create project with init
    - Run init --force to overwrite
    - Run init --force again to overwrite again
    - Should succeed both times
    """
    project_name = "test-project"
    project_path = temp_dir / project_name

    # First init
    result1 = runner.invoke(app, ["init", project_name])
    assert result1.exit_code == 0
    assert project_path.exists()

    # Second init with --force
    result2 = runner.invoke(app, ["init", project_name, "--force"])
    assert result2.exit_code == 0
    assert project_path.exists()

    # Third init with --force
    result3 = runner.invoke(app, ["init", project_name, "--force"])
    assert result3.exit_code == 0
    assert project_path.exists()

    # Verify final project is valid
    schema_file = project_path / "schema.schnitzel.yaml"
    assert schema_file.exists()
