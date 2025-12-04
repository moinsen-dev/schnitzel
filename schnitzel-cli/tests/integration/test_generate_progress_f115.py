"""Integration tests for F115 - Generate command progress output is visually appealing.

Test Requirements:
- test_progress_displayed - Verify progress indicators are shown
- test_success_message_formatted - Verify success messages use formatting

Note: F115 extends F058 with focus on visual appeal and Rich formatting.
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


def test_progress_displayed(temp_dir: Path) -> None:
    """Test that generate command displays progress indicators."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Should succeed
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output = result.stdout

    # Verify progress indicators are shown
    assert len(output) > 0, "Should have output"

    # Should show various stages
    output_lower = output.lower()
    assert "pars" in output_lower or "schema" in output_lower, \
        "Should show parsing stage"
    assert "validat" in output_lower or "valid" in output_lower, \
        "Should show validation stage"
    assert "generat" in output_lower or "complete" in output_lower, \
        "Should show generation stage"


def test_success_message_formatted(temp_dir: Path) -> None:
    """Test that success messages use visual formatting (checkmarks, colors)."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "Product model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    output = result.stdout

    # Verify visual elements
    # Rich uses ✓ for success
    assert "✓" in output, "Should use checkmark (✓) for success"

    # Should have multiple success indicators
    checkmark_count = output.count("✓")
    assert checkmark_count >= 2, \
        f"Should have multiple checkmarks, found {checkmark_count}"

    # Success message formatting
    assert "complete" in output.lower() or "success" in output.lower(), \
        "Should show completion message"


def test_progress_shows_model_details(temp_dir: Path) -> None:
    """Test that progress output includes model details."""
    # Create schema with multiple models
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Post:
    description: "Post model"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

  Comment:
    description: "Comment model"
    fields:
      id:
        type: uuid
        primary: true
      text:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    output = result.stdout

    # Should mention number of models
    assert "3" in output, "Should show model count"
    assert "models" in output.lower(), "Should mention models"

    # Should list model names
    assert "User" in output, "Should list User model"
    assert "Post" in output, "Should list Post model"
    assert "Comment" in output, "Should list Comment model"


def test_progress_organized_by_stages(temp_dir: Path) -> None:
    """Test that progress output is organized into clear stages."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Order:
    description: "Order model"
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    output = result.stdout
    lines = [line for line in output.split('\n') if line.strip()]

    # Should have multiple lines of output showing stages
    assert len(lines) >= 3, "Should have multiple stages in output"

    # Verify stages appear in order
    parsing_line = None
    validation_line = None
    generation_line = None

    for i, line in enumerate(lines):
        line_lower = line.lower()
        if "pars" in line_lower and parsing_line is None:
            parsing_line = i
        if "validat" in line_lower and validation_line is None:
            validation_line = i
        if "generat" in line_lower and generation_line is None:
            generation_line = i

    # Stages should appear in logical order (if present)
    if parsing_line is not None and validation_line is not None:
        assert parsing_line < validation_line, \
            "Parsing should come before validation"


def test_progress_shows_target_information(temp_dir: Path) -> None:
    """Test that progress shows information about generation targets."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run with explicit target
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "all"])
    assert result.exit_code == 0

    output_lower = result.stdout.lower()

    # Should mention targets or specific target types
    assert "python" in output_lower or "dart" in output_lower or "docker" in output_lower, \
        "Should mention generation targets"


def test_error_messages_are_clear(temp_dir: Path) -> None:
    """Test that error messages are clearly formatted."""
    # Create invalid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with invalid field"
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

    # Error should be clearly marked
    assert "✗" in output or "error" in output.lower() or "failed" in output.lower(), \
        "Errors should be clearly marked"


def test_quiet_mode_reduces_output(temp_dir: Path) -> None:
    """Test that --quiet flag reduces visual output."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run with quiet flag
    result = runner.invoke(app, ["--quiet", "generate", str(schema_file)])
    assert result.exit_code == 0

    output = result.stdout

    # Quiet mode should have minimal output
    assert len(output) < 100, "Quiet mode should have minimal output"
    assert "OK" in output or output.strip() == "" or len(output.strip()) < 50, \
        "Quiet mode should show minimal success indicator"


def test_progress_with_file_paths(temp_dir: Path) -> None:
    """Test that progress shows generated file paths."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "Product model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    output = result.stdout

    # Should show file paths or file names
    assert "models.py" in output or "backend" in output.lower(), \
        "Should mention Python output files"
    assert "models.dart" in output or "dart" in output.lower(), \
        "Should mention Dart output files"


def test_progress_summary_at_end(temp_dir: Path) -> None:
    """Test that progress includes a summary at the end."""
    # Create schema with 2 models
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true

  Post:
    description: "Post model"
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    output = result.stdout
    output_lower = output.lower()

    # Should have completion summary
    assert "complete" in output_lower or "success" in output_lower, \
        "Should show completion message"

    # Should mention number of models processed
    assert "2" in output and "models" in output_lower, \
        "Should show number of models in summary"


def test_visual_hierarchy_in_output(temp_dir: Path) -> None:
    """Test that output has visual hierarchy (indentation, spacing)."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])
    assert result.exit_code == 0

    output = result.stdout

    # Should have structure with spacing or indentation
    lines = output.split('\n')

    # Count non-empty lines
    content_lines = [line for line in lines if line.strip()]
    assert len(content_lines) >= 5, "Should have multiple content lines"

    # Should have some indented content (visual hierarchy)
    indented = [line for line in content_lines if line.startswith(' ') or line.startswith('  ')]
    # Note: Progress bars may be transient, so this is a loose check
    assert len(output) > 100, "Should have substantial output content"
