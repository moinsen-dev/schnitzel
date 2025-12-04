"""Integration tests for F058 - Generate command displays generation progress with Rich.

Test Requirements:
- test_generate_shows_parsing_step - output contains parsing indicator
- test_generate_shows_validation_step - output contains validation indicator
- test_generate_shows_generation_steps - output shows generation progress
- test_generate_shows_success_indicator - output shows success checkmark/message
- test_generate_shows_model_count - output displays number of models processed
- test_generate_progress_with_multiple_targets - shows progress for each target
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


def test_generate_shows_parsing_step(temp_dir: Path) -> None:
    """Test that generate command shows parsing step indicator."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A simple user model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify parsing step completed (progress bar is transient but result is shown)
    assert "Schema parsed successfully" in result.stdout, \
        "Missing parsing success indicator"
    assert "✓" in result.stdout, "Missing success checkmark"


def test_generate_shows_validation_step(temp_dir: Path) -> None:
    """Test that generate command shows validation step indicator."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "A product model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify validation step is shown
    assert "Validating" in result.stdout or "validation" in result.stdout.lower(), \
        "Missing validation step indicator"
    assert "Schema validation passed" in result.stdout or "validated" in result.stdout.lower(), \
        "Missing validation success message"


def test_generate_shows_generation_steps(temp_dir: Path) -> None:
    """Test that generate command shows generation progress for each step."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with default target (all)
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify generation steps are shown
    output_lower = result.stdout.lower()
    assert "generating" in output_lower, "Missing 'generating' indicator"

    # Should show progress for generation
    assert "python" in output_lower or "dart" in output_lower or "docker" in output_lower, \
        "Missing target-specific generation indicators"


def test_generate_shows_success_indicator(temp_dir: Path) -> None:
    """Test that generate command shows success checkmark/message."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  Post:
    description: "Post model"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify success indicators
    assert "✓" in result.stdout, "Missing success checkmark (✓)"
    assert "Generation complete" in result.stdout or "complete" in result.stdout.lower(), \
        "Missing generation complete message"

    # Should have multiple success checkmarks (parsing, validation, generation)
    checkmark_count = result.stdout.count("✓")
    assert checkmark_count >= 2, \
        f"Expected at least 2 success checkmarks, found {checkmark_count}"


def test_generate_shows_model_count(temp_dir: Path) -> None:
    """Test that generate command displays number of models processed."""
    # Create a schema with multiple models
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
    schema_file = temp_dir / "multi_model.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify model count is displayed
    assert "3 models" in result.stdout.lower() or "models found: 3" in result.stdout, \
        "Missing model count display"

    # Verify all models are mentioned
    assert "User" in result.stdout, "User model not mentioned"
    assert "Post" in result.stdout, "Post model not mentioned"
    assert "Comment" in result.stdout, "Comment model not mentioned"


def test_generate_progress_with_multiple_targets(temp_dir: Path) -> None:
    """Test that generate command shows progress for each target when using --target all."""
    # Create a valid schema file
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
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with target=all (explicit)
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "all"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output_lower = result.stdout.lower()

    # Verify progress indicators for multiple targets
    # Should mention the number of targets
    assert "3 targets" in output_lower or "targets" in output_lower, \
        "Missing target count in progress"

    # Should show generation for each target
    assert "python" in output_lower, "Missing Python generation indicator"
    assert "dart" in output_lower, "Missing Dart generation indicator"
    assert "docker" in output_lower, "Missing Docker generation indicator"


def test_generate_progress_with_single_target_python(temp_dir: Path) -> None:
    """Test that generate command shows appropriate progress for single target (python)."""
    # Create a valid schema file
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
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with target=python
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output_lower = result.stdout.lower()

    # Verify single target progress
    assert "1 target" in output_lower or "python" in output_lower, \
        "Missing single target indicator"

    # Verify Python-specific output
    assert "python" in output_lower, "Missing Python generation indicator"
    assert "backend/app/models.py" in output_lower or "models.py" in output_lower, \
        "Missing Python output file indicator"


def test_generate_progress_with_single_target_dart(temp_dir: Path) -> None:
    """Test that generate command shows appropriate progress for single target (dart)."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  Order:
    description: "Order model"
    fields:
      id:
        type: uuid
        primary: true
      order_number:
        type: string
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with target=dart
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    output_lower = result.stdout.lower()

    # Verify single target progress
    assert "1 target" in output_lower or "dart" in output_lower, \
        "Missing single target indicator"

    # Verify Dart-specific output
    assert "dart" in output_lower, "Missing Dart generation indicator"


def test_generate_progress_format(temp_dir: Path) -> None:
    """Test that generate command progress output follows expected format."""
    # Create a valid schema file
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
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Expected format:
    # - Parsing indicator
    # - ✓ Schema parsed successfully
    # - Validation indicator
    # - ✓ Schema validation passed
    # - Generation indicator(s)
    # - ✓ Generation complete

    lines = result.stdout.split('\n')

    # Find key progress lines
    has_parsing = any("pars" in line.lower() for line in lines)
    has_validation = any("validat" in line.lower() for line in lines)
    has_generation = any("generat" in line.lower() for line in lines)
    has_complete = any("complete" in line.lower() for line in lines)

    assert has_parsing, "Missing parsing progress"
    assert has_validation, "Missing validation progress"
    assert has_generation, "Missing generation progress"
    assert has_complete, "Missing completion message"


def test_generate_progress_on_validation_failure(temp_dir: Path) -> None:
    """Test that progress indicators work correctly even when validation fails."""
    # Create a schema with validation errors
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with invalid field type"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: invalid_type
"""
    schema_file = temp_dir / "invalid_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify failure
    assert result.exit_code == 1, "Command should fail with invalid schema"

    # Should still show parsing step (which succeeded)
    assert "pars" in result.stdout.lower(), "Missing parsing step"
    assert "✓" in result.stdout, "Missing success indicator for parsing"

    # Should show validation failure
    assert "validation" in result.stdout.lower(), "Missing validation step"
    assert "failed" in result.stdout.lower() or "✗" in result.stdout, \
        "Missing validation failure indicator"


def test_generate_shows_processed_summary(temp_dir: Path) -> None:
    """Test that generate command shows a summary of processed models and targets."""
    # Create a schema with 2 models
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
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify summary information
    output_lower = result.stdout.lower()
    assert "processed" in output_lower or "models" in output_lower, \
        "Missing processing summary"

    # Should mention the number of models
    assert "2 models" in output_lower or "models found: 2" in result.stdout, \
        "Missing model count in summary"
