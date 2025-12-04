"""Integration tests for F084 - Generate command with --schema flag uses specified schema file.

Test Requirements:
- test_schema_flag_uses_specified_file - --schema custom.yaml should work
- test_schema_short_flag - -s should work as short form
- test_schema_flag_file_not_found - should error if file doesn't exist
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


def test_schema_flag_uses_specified_file(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that --schema flag uses the specified schema file."""
    # Create a custom schema file with a non-standard name
    custom_schema = temp_dir / "custom.yaml"
    custom_schema.write_text(valid_schema_content)

    # Run generate command with --schema flag
    result = runner.invoke(app, ["generate", "--schema", str(custom_schema)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    assert "Generation complete" in result.stdout


def test_schema_short_flag(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that -s short flag works as an alias for --schema."""
    # Create a custom schema file
    custom_schema = temp_dir / "my_schema.yaml"
    custom_schema.write_text(valid_schema_content)

    # Run generate command with -s short flag
    result = runner.invoke(app, ["generate", "-s", str(custom_schema)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    assert "Generation complete" in result.stdout


def test_schema_flag_file_not_found(temp_dir: Path) -> None:
    """Test that --schema flag shows error when file doesn't exist."""
    # Use a non-existent file path
    nonexistent_file = temp_dir / "nonexistent.yaml"

    # Run generate command with --schema flag pointing to non-existent file
    result = runner.invoke(app, ["generate", "--schema", str(nonexistent_file)])

    # Verify failure
    assert result.exit_code == 1, "Command should fail when schema file not found"
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


def test_schema_flag_overrides_default(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that --schema flag overrides the default schema.schnitzel.yaml."""
    # Create both default and custom schema files with different content
    default_schema = temp_dir / "schema.schnitzel.yaml"
    default_content = """schnitzel: "1.0"

models:
  DefaultModel:
    description: "Default model"
    fields:
      id:
        type: uuid
        primary: true
      default_field:
        type: string
"""
    default_schema.write_text(default_content)

    custom_schema = temp_dir / "custom.yaml"
    custom_content = """schnitzel: "1.0"

models:
  CustomModel:
    description: "Custom model"
    fields:
      id:
        type: uuid
        primary: true
      custom_field:
        type: string
"""
    custom_schema.write_text(custom_content)

    # Run generate command with --schema flag
    result = runner.invoke(app, ["generate", "--schema", str(custom_schema)])

    # Verify that custom schema was used (not default)
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "CustomModel" in result.stdout, "Should use custom schema model"
    # DefaultModel should not appear since we're using custom schema
    assert "DefaultModel" not in result.stdout, "Should not use default schema model"


def test_schema_flag_with_other_options(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that --schema flag works with other command options like --target."""
    # Create a custom schema file
    custom_schema = temp_dir / "app.schema.yaml"
    custom_schema.write_text(valid_schema_content)

    # Run generate command with --schema and --target flags
    result = runner.invoke(app, [
        "generate",
        "--schema", str(custom_schema),
        "--target", "python"
    ])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Generating Python models" in result.stdout or "Generated backend/app/models.py" in result.stdout


def test_schema_flag_with_dry_run(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that --schema flag works with --dry-run option."""
    # Create a custom schema file
    custom_schema = temp_dir / "test.schema.yaml"
    custom_schema.write_text(valid_schema_content)

    # Run generate command with --schema and --dry-run flags
    result = runner.invoke(app, [
        "generate",
        "--schema", str(custom_schema),
        "--dry-run"
    ])

    # Verify success and dry-run behavior
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "DRY RUN MODE" in result.stdout
    assert "No files were written" in result.stdout


def test_schema_flag_with_relative_path(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that --schema flag works with relative paths."""
    # Create a custom schema file
    custom_schema = temp_dir / "relative.yaml"
    custom_schema.write_text(valid_schema_content)

    # Run generate command with relative path
    result = runner.invoke(app, ["generate", "--schema", "relative.yaml"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout


def test_positional_arg_still_works(temp_dir: Path, valid_schema_content: str) -> None:
    """Test that the positional argument still works for backward compatibility."""
    # Create a custom schema file
    schema_file = temp_dir / "positional.yaml"
    schema_file.write_text(valid_schema_content)

    # Run generate command with positional argument (no --schema flag)
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Generation complete" in result.stdout
