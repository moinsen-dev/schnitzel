"""Integration tests for F051 - Generate command stops if schema validation fails.

Test Requirements:
- test_generate_stops_on_validation_failure
- test_generate_shows_validation_errors
- test_generate_returns_exit_code_1_on_failure
- test_generate_does_not_write_files_on_failure
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


def test_generate_stops_on_validation_failure(temp_dir: Path) -> None:
    """Test that generate command stops execution when schema validation fails.

    Verifies that:
    - Schema parsing succeeds
    - Validation runs
    - Execution stops when validation fails
    - No code generation messages appear
    """
    # Create schema with validation error (invalid model naming)
    schema_content = """schnitzel: "1.0"

models:
  user:
    description: "Invalid model name - should be PascalCase"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "invalid_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify command stopped on validation failure
    assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"
    assert "Schema parsed successfully" in result.stdout, "Schema parsing should succeed"
    # Validation step is shown in transient progress bar, so we check for failure message
    assert "validation failed" in result.stdout.lower(), "Should show validation failed message"

    # Verify no code generation happened
    assert "Schema is ready for code generation" not in result.stdout, \
        "Should not proceed to code generation"
    assert "Generating Python" not in result.stdout, "Should not show generation messages"


def test_generate_shows_validation_errors(temp_dir: Path) -> None:
    """Test that generate command displays clear validation error messages.

    Verifies that:
    - All validation errors are shown
    - Error messages are clear and actionable
    - Suggested fixes are provided
    """
    # Create schema with multiple validation errors
    schema_content = """schnitzel: "1.0"

models:
  user:
    description: "Model with multiple validation errors"
    fields:
      id:
        type: uuid
        primary: true
      userName:
        type: string
      age:
        type: decimal
"""
    schema_file = temp_dir / "multi_error_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify validation errors are displayed
    assert result.exit_code == 1, "Command should fail with validation errors"
    assert "Schema validation failed" in result.stdout

    # Check that model naming error is shown
    assert "user" in result.stdout.lower() or "naming convention" in result.stdout.lower()
    assert "PascalCase" in result.stdout or "pascal" in result.stdout.lower()

    # Check that field naming error is shown
    assert "userName" in result.stdout or "snake_case" in result.stdout.lower()

    # Check that unsupported type error is shown
    assert "decimal" in result.stdout or "Unsupported" in result.stdout


def test_generate_returns_exit_code_1_on_failure(temp_dir: Path) -> None:
    """Test that generate command returns exit code 1 on validation failure.

    This is critical for CI/CD pipelines and automation scripts.
    """
    # Create schema with validation error
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with invalid field type"
    fields:
      id:
        type: uuid
        primary: true
      score:
        type: unsupported_type
"""
    schema_file = temp_dir / "invalid_type_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify exit code is 1
    assert result.exit_code == 1, \
        f"Expected exit code 1 for validation failure, got {result.exit_code}"
    assert "Schema validation failed" in result.stdout


def test_generate_does_not_write_files_on_failure(temp_dir: Path) -> None:
    """Test that generate command does not create any files when validation fails.

    Verifies that:
    - No output files are created
    - No partial generation occurs
    - Directory remains clean
    """
    # Create schema with validation error
    schema_content = """schnitzel: "1.0"

models:
  InvalidModel:
    description: "Model with invalid field"
    fields:
      id:
        type: uuid
        primary: true
      badField:
        type: string
"""
    schema_file = temp_dir / "bad_schema.yaml"
    schema_file.write_text(schema_content)

    # Get list of files before running command
    files_before = set(temp_dir.iterdir())

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Get list of files after running command
    files_after = set(temp_dir.iterdir())

    # Verify no new files were created
    new_files = files_after - files_before
    assert len(new_files) == 0, \
        f"No files should be created on validation failure, but found: {[f.name for f in new_files]}"

    # Verify command failed
    assert result.exit_code == 1, "Command should fail with validation error"
    assert "Schema validation failed" in result.stdout


def test_generate_validation_failure_with_invalid_format(temp_dir: Path) -> None:
    """Test validation failure with invalid string format constraint."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with invalid format"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: invalid_format
"""
    schema_file = temp_dir / "invalid_format.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify validation failure
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout
    assert "format" in result.stdout.lower()
    assert "invalid_format" in result.stdout or "Unsupported format" in result.stdout


def test_generate_validation_failure_with_invalid_constraints(temp_dir: Path) -> None:
    """Test validation failure with invalid min/max constraints."""
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "Product with invalid constraints"
    fields:
      id:
        type: uuid
        primary: true
      price:
        type: float
        min: 100.0
        max: 10.0
"""
    schema_file = temp_dir / "invalid_constraints.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify validation failure
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout
    assert "constraint" in result.stdout.lower() or "minimum" in result.stdout.lower()


def test_generate_validation_failure_with_missing_relationship(temp_dir: Path) -> None:
    """Test validation failure with missing relationship target model."""
    schema_content = """schnitzel: "1.0"

models:
  Post:
    description: "Post with invalid relationship"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      author_id:
        type: uuid
    relations:
      author:
        type: belongsTo
        model: NonexistentUser
        foreign_key: author_id
"""
    schema_file = temp_dir / "missing_relation.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify validation failure
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout
    assert "NonexistentUser" in result.stdout or "does not exist" in result.stdout


def test_generate_validation_passes_with_valid_schema(temp_dir: Path) -> None:
    """Test that validation passes with a completely valid schema.

    This is a positive test to ensure validation doesn't create false negatives.
    """
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "Valid user model"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        format: email
        unique: true
      name:
        type: string
      age:
        type: int
        min: 0
        max: 150
      is_active:
        type: bool
        default: true
      created_at:
        type: datetime
        auto: create
    relations:
      posts:
        type: hasMany
        model: Post

  Post:
    description: "Valid post model"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string
      author_id:
        type: uuid
      created_at:
        type: datetime
        auto: create
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
"""
    schema_file = temp_dir / "valid_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify validation passes
    assert result.exit_code == 0, f"Valid schema should pass validation: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    # Note: The message might vary based on implementation stage
    assert ("Schema is ready for code generation" in result.stdout or
            "Generation complete" in result.stdout)


def test_generate_error_message_format(temp_dir: Path) -> None:
    """Test that validation error messages follow expected format.

    Verifies that:
    - Error messages are clearly formatted
    - Error indicator (✗) is shown
    - Multiple errors are separated properly
    """
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with validation error"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: invalid_type
"""
    schema_file = temp_dir / "format_test.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify error message format
    assert result.exit_code == 1
    assert "✗ Schema validation failed" in result.stdout or "Schema validation failed" in result.stdout

    # Should show error details
    output_lower = result.stdout.lower()
    assert "error" in output_lower
    assert "invalid_type" in result.stdout or "unsupported" in output_lower


def test_generate_multiple_validation_errors_shown(temp_dir: Path) -> None:
    """Test that all validation errors are shown when multiple errors exist."""
    schema_content = """schnitzel: "1.0"

models:
  invalid_model:
    description: "Model with multiple errors"
    fields:
      id:
        type: uuid
        primary: true
      BadFieldName:
        type: string
      another_field:
        type: wrong_type
"""
    schema_file = temp_dir / "multiple_errors.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify all errors are shown
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout

    # Should show model naming error
    output_lower = result.stdout.lower()
    assert "invalid_model" in result.stdout or "pascalcase" in output_lower

    # Should show field naming error
    assert "BadFieldName" in result.stdout or "snake_case" in output_lower

    # Should show type error
    assert "wrong_type" in result.stdout or "unsupported" in output_lower


def test_generate_validation_with_numeric_constraint_on_wrong_type(temp_dir: Path) -> None:
    """Test validation failure when min/max constraints are on non-numeric fields."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with invalid constraint"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        min: 5
        max: 100
"""
    schema_file = temp_dir / "wrong_constraint_type.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify validation failure
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout
    assert "constraint" in result.stdout.lower() or "numeric" in result.stdout.lower()


def test_generate_validation_with_format_on_wrong_type(temp_dir: Path) -> None:
    """Test validation failure when format constraint is on non-string field."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with invalid format constraint"
    fields:
      id:
        type: uuid
        primary: true
      age:
        type: int
        format: email
"""
    schema_file = temp_dir / "wrong_format_type.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify validation failure
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout
    assert "format" in result.stdout.lower() or "string" in result.stdout.lower()
