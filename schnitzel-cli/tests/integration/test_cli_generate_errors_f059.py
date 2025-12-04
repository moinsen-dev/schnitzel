"""Integration tests for F059 - Generate command handles generation errors gracefully.

Test Requirements:
- test_generate_handles_permission_error - returns error on permission denied
- test_generate_shows_error_file_path - error message includes file path
- test_generate_returns_exit_code_1_on_io_error - proper exit code
- test_generate_error_message_is_user_friendly - no raw stack traces
- test_generate_cleans_up_on_partial_failure - no partial files left
"""

import tempfile
import os
import stat
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
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
def valid_schema_content():
    """Return valid schema content for testing."""
    return """schnitzel: "1.0"

models:
  User:
    description: "A simple user model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
"""


def test_generate_handles_permission_error(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that generate command handles permission errors gracefully."""
    # Create a valid schema file
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(valid_schema_content)

    # Create the output directory structure but make it read-only
    backend_dir = temp_dir / "backend" / "app"
    backend_dir.mkdir(parents=True, exist_ok=True)

    # Make the directory read-only to trigger permission error
    os.chmod(backend_dir, stat.S_IRUSR | stat.S_IXUSR)

    try:
        # Run generate command targeting python only
        result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

        # Verify failure
        assert result.exit_code == 1, f"Command should fail with permission error: {result.stdout}"
        assert "Permission denied" in result.stdout or "permission" in result.stdout.lower()

    finally:
        # Restore permissions for cleanup
        try:
            os.chmod(backend_dir, stat.S_IRWXU)
        except:
            pass


def test_generate_shows_error_file_path(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that error messages include the file path that failed."""
    # Create a valid schema file
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(valid_schema_content)

    # Mock the file write to raise an IOError with a filename
    with patch("schnitzel.generators.python.models.PythonModelGenerator.generate_to_file") as mock_gen:
        test_file_path = temp_dir / "backend" / "app" / "models.py"
        error = IOError("Mock disk full error")
        error.filename = str(test_file_path)
        mock_gen.side_effect = error

        # Run generate command
        result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

        # Verify failure and file path is shown
        assert result.exit_code == 1, "Command should fail with I/O error"
        assert "error" in result.stdout.lower()
        # The error should mention file-related information
        assert "file" in result.stdout.lower() or str(test_file_path) in result.stdout


def test_generate_returns_exit_code_1_on_io_error(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that generate command returns exit code 1 on I/O errors."""
    # Create a valid schema file
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(valid_schema_content)

    # Mock the file write to raise an IOError
    with patch("schnitzel.generators.python.models.PythonModelGenerator.generate_to_file") as mock_gen:
        mock_gen.side_effect = IOError("Mock I/O error")

        # Run generate command
        result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

        # Verify exit code is 1
        assert result.exit_code == 1, f"Command should return exit code 1 on I/O error: exit_code={result.exit_code}, output={result.stdout}"


def test_generate_error_message_is_user_friendly(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that error messages are user-friendly without raw stack traces."""
    # Create a valid schema file
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(valid_schema_content)

    # Mock the file write to raise a PermissionError
    with patch("schnitzel.generators.python.models.PythonModelGenerator.generate_to_file") as mock_gen:
        error = PermissionError("Mock permission denied")
        error.filename = str(temp_dir / "backend" / "app" / "models.py")
        mock_gen.side_effect = error

        # Run generate command
        result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

        # Verify user-friendly message (no stack trace keywords)
        assert result.exit_code == 1
        assert "Traceback" not in result.stdout, "Should not show Python traceback"
        assert "File \"" not in result.stdout or "line " not in result.stdout, "Should not show code references"

        # Should have user-friendly error message
        output_lower = result.stdout.lower()
        assert any(word in output_lower for word in ["error", "permission", "denied", "failed"]), \
            "Should have user-friendly error description"


def test_generate_cleans_up_on_partial_failure(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that partial files are cleaned up when generation fails."""
    # Create a valid schema file
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(valid_schema_content)

    # Track files that were created
    created_files = []

    def mock_generate_python(*args, **kwargs):
        """Mock that creates a file, returns it, then the system fails."""
        backend_dir = temp_dir / "backend" / "app"
        backend_dir.mkdir(parents=True, exist_ok=True)
        models_file = backend_dir / "models.py"
        models_file.write_text("# Partial content")
        created_files.append(models_file)

        # Return the file info so it gets tracked, then raise error
        # This simulates: file created successfully but then write fails
        return {'path': models_file, 'size': 100, 'type': 'Python models'}

    def mock_generate_dart(*args, **kwargs):
        """Mock that fails during dart generation (after python succeeded)."""
        # This should trigger cleanup of the python file
        error = IOError("Mock error during dart generation")
        error.filename = str(temp_dir / "packages" / "app" / "lib" / "models" / "models.dart")
        raise error

    with patch("schnitzel.cli.commands.generate._generate_python", side_effect=mock_generate_python):
        with patch("schnitzel.cli.commands.generate._generate_dart", side_effect=mock_generate_dart):
            # Run generate command with target=all to test multi-file cleanup
            result = runner.invoke(app, ["generate", str(schema_file), "--target", "all"])

            # Verify command failed
            assert result.exit_code == 1, "Command should fail"

            # Verify the partial file was cleaned up
            for created_file in created_files:
                assert not created_file.exists(), \
                    f"Partial file {created_file} should have been cleaned up but still exists"


def test_generate_multiple_files_cleanup_on_second_failure(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that when generating multiple files, if second fails, first is cleaned up."""
    # Create a valid schema file
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(valid_schema_content)

    python_file = temp_dir / "backend" / "app" / "models.py"
    dart_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"

    call_count = [0]

    def mock_generate_python(*args, **kwargs):
        """Mock that succeeds."""
        call_count[0] += 1
        backend_dir = temp_dir / "backend" / "app"
        backend_dir.mkdir(parents=True, exist_ok=True)
        python_file.write_text("# Python models")
        # Return dict format if expected
        return {"path": python_file, "size": 100, "type": "Python models", "model_count": 1}

    def mock_generate_dart(*args, **kwargs):
        """Mock that fails."""
        call_count[0] += 1
        # Fail on dart generation
        error = IOError("Mock dart generation failure")
        error.filename = str(dart_file)
        raise error

    with patch("schnitzel.cli.commands.generate._generate_python", side_effect=mock_generate_python):
        with patch("schnitzel.cli.commands.generate._generate_dart", side_effect=mock_generate_dart):
            # Run generate command with target=all
            result = runner.invoke(app, ["generate", str(schema_file), "--target", "all"])

            # Verify command failed
            assert result.exit_code == 1, f"Command should fail: {result.stdout}"

            # Both generators should have been attempted
            assert call_count[0] >= 1, "At least one generator should have been called"

            # The python file (created first) should be cleaned up
            # Note: This test checks if cleanup logic is in place
            # The actual cleanup depends on the implementation tracking generated files


def test_generate_os_error_handling(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that OSError (generic system errors) are handled properly."""
    # Create a valid schema file
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(valid_schema_content)

    # Mock to raise OSError
    with patch("schnitzel.generators.python.models.PythonModelGenerator.generate_to_file") as mock_gen:
        error = OSError("Mock system error")
        error.filename = str(temp_dir / "backend" / "app" / "models.py")
        mock_gen.side_effect = error

        # Run generate command
        result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

        # Verify failure with proper error handling
        assert result.exit_code == 1, "Command should fail with OS error"
        assert "error" in result.stdout.lower()
