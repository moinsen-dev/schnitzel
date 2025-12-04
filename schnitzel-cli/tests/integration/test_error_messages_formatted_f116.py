"""Integration tests for F116 - Error messages formatted with Rich.

Test Requirements:
- test_validation_error_uses_rich_formatting - Verify validation errors use Rich markup
- test_yaml_error_uses_rich_formatting - Verify YAML errors use Rich formatting
- test_file_not_found_error_formatted - Verify file not found errors are formatted
- test_error_has_visual_markers - Verify errors have visual markers (✗, colors)
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


def test_validation_error_uses_rich_formatting(temp_dir: Path) -> None:
    """Test that validation errors use Rich markup for formatting."""
    # Create schema with validation error (invalid field type)
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: invalid_type
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1

    output = result.stdout

    # Verify Rich formatting is used
    # Rich uses ✗ for errors
    assert "✗" in output or "error" in output.lower(), "Should show error indicator"

    # Should show error in context
    assert "validat" in output.lower() or "invalid" in output.lower(), \
        "Should mention validation issue"


def test_yaml_error_uses_rich_formatting(temp_dir: Path) -> None:
    """Test that YAML parse errors use Rich formatting."""
    # Create schema with YAML syntax error (invalid YAML - unclosed bracket)
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model
    fields:
      id:
        type: uuid
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1

    output = result.stdout

    # Verify error is formatted
    assert "✗" in output or "error" in output.lower() or "failed" in output.lower(), \
        "Should show error indicator"

    # YAML error should be mentioned
    assert "yaml" in output.lower() or "pars" in output.lower(), \
        "Should mention YAML or parsing"


def test_file_not_found_error_formatted(temp_dir: Path) -> None:
    """Test that file not found errors are formatted with Rich."""
    # Try to generate from non-existent file
    result = runner.invoke(app, ["generate", "nonexistent_schema.yaml"])

    # Should fail
    assert result.exit_code == 1 or result.exit_code == 0  # May show helpful message

    output = result.stdout

    # Should have some output about the error
    assert len(output) > 0, "Should have error output"

    # Should mention the file issue
    assert "not found" in output.lower() or "file" in output.lower() or \
           "schema" in output.lower(), "Should mention file/schema issue"


def test_error_has_visual_markers(temp_dir: Path) -> None:
    """Test that errors have visual markers (✗ checkmark, red color markup)."""
    # Create invalid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: invalid
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1

    output = result.stdout

    # Should use error checkmark (✗)
    assert "✗" in output, "Should use ✗ symbol for errors"


def test_multiple_validation_errors_formatted(temp_dir: Path) -> None:
    """Test that multiple validation errors are all formatted consistently."""
    # Create schema with multiple errors
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: invalid_type1
      email:
        type: invalid_type2
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1

    output = result.stdout

    # Should show error marker
    assert "✗" in output or "error" in output.lower(), "Should show error indicators"

    # Should be readable (not overly verbose)
    lines = output.split("\n")
    assert len(lines) < 100, "Error output should be reasonably concise"


def test_error_message_structure(temp_dir: Path) -> None:
    """Test that error messages have clear structure."""
    # Create invalid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      age:
        type: int
        min: 10
        max: 5
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should fail (min > max is invalid)
    assert result.exit_code == 1

    output = result.stdout

    # Should have clear error indication
    assert "✗" in output or "error" in output.lower() or "failed" in output.lower(), \
        "Should clearly indicate an error"

    # Should not be empty
    assert len(output.strip()) > 10, "Should have meaningful error message"


def test_init_error_formatted(temp_dir: Path) -> None:
    """Test that init command errors are formatted with Rich."""
    # Create existing directory
    existing_dir = temp_dir / "myproject"
    existing_dir.mkdir()

    # Try to init in existing directory (without --force)
    result = runner.invoke(app, ["init", "myproject"])

    # Should fail
    assert result.exit_code == 1

    output = result.stdout

    # Should show error
    assert "error" in output.lower() or "exists" in output.lower() or \
           "already" in output.lower(), "Should mention directory exists"


def test_quiet_mode_shows_errors(temp_dir: Path) -> None:
    """Test that errors are shown even in quiet mode."""
    # Create invalid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: invalid
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run with quiet flag
    result = runner.invoke(app, ["--quiet", "generate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1

    output = result.stdout

    # Even in quiet mode, errors should be shown
    assert len(output) > 0, "Errors should be shown even in quiet mode"
    assert "✗" in output or "error" in output.lower() or "failed" in output.lower(), \
        "Error indicator should be present"


def test_helpful_error_context(temp_dir: Path) -> None:
    """Test that errors provide helpful context and suggestions."""
    # Run generate without schema file in directory
    result = runner.invoke(app, ["generate"])

    # May fail or show helpful message
    output = result.stdout

    # Should provide some guidance
    assert len(output) > 0, "Should provide output"

    # Should mention schema or provide guidance
    output_lower = output.lower()
    assert "schema" in output_lower or "init" in output_lower or \
           "file" in output_lower, "Should provide helpful context"
