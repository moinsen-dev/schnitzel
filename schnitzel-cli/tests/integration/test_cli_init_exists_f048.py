"""Integration tests for F048 - Init command fails gracefully if directory already exists.

Feature: F048 - Init command fails gracefully if directory already exists
Context: The CLI init command is at src/schnitzel/cli/commands/init.py.
         This feature should already be implemented based on F040, but verify and add tests.

Expected Behavior:
- Init should check if the project directory already exists before creating
- Should show a clear error message if directory exists
- Should return exit code 1 (failure)
- Should NOT overwrite existing directories

Test Requirements:
- test_init_fails_if_directory_exists
- test_init_shows_error_message_for_existing_dir
- test_init_returns_exit_code_1_for_existing_dir
- test_init_does_not_overwrite_existing_files
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


def test_init_fails_if_directory_exists(temp_dir: Path) -> None:
    """Test that init command fails if project directory already exists.

    Verification:
    - Create an existing directory
    - Attempt to init with same name
    - Command should fail (exit code 1)
    """
    project_name = "existing-project"
    existing_dir = temp_dir / project_name
    existing_dir.mkdir()

    # Verify directory exists before test
    assert existing_dir.exists(), "Precondition: Directory should exist"

    # Run init command with existing directory name
    result = runner.invoke(app, ["init", project_name])

    # Verify command failed
    assert result.exit_code == 1, (
        f"Command should fail (exit code 1) when directory exists. "
        f"Got exit code: {result.exit_code}\n"
        f"Output: {result.stdout}"
    )


def test_init_shows_error_message_for_existing_dir(temp_dir: Path) -> None:
    """Test that init command shows a clear error message when directory exists.

    Verification:
    - Create an existing directory
    - Attempt to init with same name
    - Should display error message mentioning that directory exists
    - Message should include the directory name
    """
    project_name = "existing-project"
    existing_dir = temp_dir / project_name
    existing_dir.mkdir()

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify error message is shown
    output = result.stdout
    assert "Error" in output, f"Output should contain 'Error'. Got: {output}"
    assert "already exists" in output, (
        f"Error message should mention 'already exists'. Got: {output}"
    )
    assert project_name in output, (
        f"Error message should mention the project name '{project_name}'. Got: {output}"
    )


def test_init_returns_exit_code_1_for_existing_dir(temp_dir: Path) -> None:
    """Test that init command returns exit code 1 (failure) for existing directory.

    Verification:
    - Create an existing directory
    - Run init command
    - Should return exit code 1 (not 0 for success, not other codes)
    """
    project_name = "existing-project"
    existing_dir = temp_dir / project_name
    existing_dir.mkdir()

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify exact exit code
    assert result.exit_code == 1, (
        f"Exit code should be exactly 1 for existing directory. "
        f"Got: {result.exit_code}"
    )


def test_init_does_not_overwrite_existing_files(temp_dir: Path) -> None:
    """Test that init command does not overwrite existing files in directory.

    Verification:
    - Create directory with a specific file and content
    - Attempt to init with same name
    - File content should remain unchanged
    - No new files should be created
    """
    project_name = "existing-project"
    existing_dir = temp_dir / project_name
    existing_dir.mkdir()

    # Create a test file with specific content
    test_file = existing_dir / "important-file.txt"
    original_content = "This is important data that should not be lost"
    test_file.write_text(original_content)

    # Get list of existing files
    existing_files = list(existing_dir.rglob("*"))
    existing_file_count = len(existing_files)

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify command failed
    assert result.exit_code == 1, "Command should fail when directory exists"

    # Verify original file still exists with same content
    assert test_file.exists(), "Original file should still exist"
    current_content = test_file.read_text()
    assert current_content == original_content, (
        f"Original file content should not be modified. "
        f"Expected: '{original_content}', Got: '{current_content}'"
    )

    # Verify no new files were created
    current_files = list(existing_dir.rglob("*"))
    current_file_count = len(current_files)
    assert current_file_count == existing_file_count, (
        f"No new files should be created. "
        f"Before: {existing_file_count} files, After: {current_file_count} files"
    )


def test_init_fails_for_empty_existing_directory(temp_dir: Path) -> None:
    """Test that init fails even if existing directory is empty.

    Verification:
    - Create empty directory
    - Attempt to init with same name
    - Should still fail (don't allow even empty directory overwrite)
    """
    project_name = "empty-existing-dir"
    existing_dir = temp_dir / project_name
    existing_dir.mkdir()

    # Verify directory is empty
    assert existing_dir.exists()
    assert list(existing_dir.iterdir()) == [], "Directory should be empty"

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify command failed even for empty directory
    assert result.exit_code == 1, (
        "Command should fail even when directory is empty"
    )
    assert "already exists" in result.stdout


def test_init_fails_for_directory_with_subdirs(temp_dir: Path) -> None:
    """Test that init fails when directory has subdirectories.

    Verification:
    - Create directory with subdirectories
    - Attempt to init
    - Should fail and preserve subdirectories
    """
    project_name = "existing-with-subdirs"
    existing_dir = temp_dir / project_name
    existing_dir.mkdir()

    # Create subdirectories
    subdir1 = existing_dir / "subdir1"
    subdir2 = existing_dir / "subdir2" / "nested"
    subdir1.mkdir()
    subdir2.mkdir(parents=True)

    # Create file in subdirectory
    test_file = subdir1 / "data.txt"
    test_file.write_text("nested data")

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify command failed
    assert result.exit_code == 1

    # Verify subdirectories and files are preserved
    assert subdir1.exists(), "Subdirectory should be preserved"
    assert subdir2.exists(), "Nested subdirectory should be preserved"
    assert test_file.exists(), "Files in subdirectories should be preserved"
    assert test_file.read_text() == "nested data", "File content should be unchanged"


def test_init_succeeds_for_nonexistent_directory(temp_dir: Path) -> None:
    """Test that init succeeds when directory does not exist (positive test).

    Verification:
    - Verify directory doesn't exist
    - Run init command
    - Should succeed with exit code 0
    - Directory should be created
    """
    project_name = "new-project"
    project_path = temp_dir / project_name

    # Verify directory doesn't exist
    assert not project_path.exists(), "Directory should not exist before init"

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, (
        f"Command should succeed for non-existent directory. "
        f"Got exit code: {result.exit_code}\n"
        f"Output: {result.stdout}"
    )

    # Verify directory was created
    assert project_path.exists(), "Directory should be created"
    assert project_path.is_dir(), "Path should be a directory"


def test_init_error_message_format(temp_dir: Path) -> None:
    """Test that error message follows expected format.

    Verification:
    - Error message should be clear and user-friendly
    - Should use proper formatting (e.g., [red] tags for colored output)
    - Should provide actionable information
    """
    project_name = "existing-project"
    existing_dir = temp_dir / project_name
    existing_dir.mkdir()

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    output = result.stdout

    # Check for error indicators
    assert any(indicator in output for indicator in ["Error", "error", "✗"]), (
        "Output should contain error indicator"
    )

    # Check message is not generic
    assert len(output.strip()) > 0, "Error message should not be empty"
    assert project_name in output, "Error should mention the specific project name"


def test_init_prevents_data_loss(temp_dir: Path) -> None:
    """Test that init command prevents accidental data loss.

    Verification:
    - Create directory with multiple files mimicking a real project
    - Attempt to init
    - All original files should remain intact
    """
    project_name = "real-project"
    existing_dir = temp_dir / project_name
    existing_dir.mkdir()

    # Create files mimicking a real project
    files_to_create = {
        "README.md": "# My Project\n\nThis is important documentation.",
        "src/main.py": "def main():\n    print('Hello')\n",
        "config.json": '{"setting": "value"}',
        ".gitignore": "*.pyc\n__pycache__/\n",
    }

    for file_path, content in files_to_create.items():
        full_path = existing_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify command failed
    assert result.exit_code == 1

    # Verify all files still exist with original content
    for file_path, expected_content in files_to_create.items():
        full_path = existing_dir / file_path
        assert full_path.exists(), f"File {file_path} should still exist"
        actual_content = full_path.read_text()
        assert actual_content == expected_content, (
            f"Content of {file_path} should be unchanged"
        )


def test_init_with_file_instead_of_directory(temp_dir: Path) -> None:
    """Test behavior when a file exists with the project name.

    Verification:
    - Create a file (not directory) with project name
    - Attempt to init
    - Should fail gracefully (file.exists() will return True)
    """
    project_name = "project-as-file"
    existing_file = temp_dir / project_name

    # Create a file instead of directory
    existing_file.write_text("This is a file, not a directory")

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Should fail because path already exists
    assert result.exit_code == 1
    assert "already exists" in result.stdout

    # Verify file is unchanged
    assert existing_file.is_file(), "Should still be a file"
    assert existing_file.read_text() == "This is a file, not a directory"
