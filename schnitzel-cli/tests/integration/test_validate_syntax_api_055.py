"""Integration tests for API_055 - Validate command checks schema syntax.

Test Requirements:
1. Run schnitzel validate
2. Verify YAML syntax is validated
3. Verify schema structure is validated
4. Verify error messages are helpful

This test validates that the `schnitzel validate` command:
- Detects and reports YAML syntax errors with helpful messages
- Validates schema structure (required fields, model definitions)
- Validates field types and constraints
- Validates relationships between models
- Provides clear, actionable error messages
"""

import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

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


def test_validate_command_exists(temp_dir: Path) -> None:
    """Test that the validate command is registered and accessible."""
    # Create a minimal valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate command
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Command should succeed
    assert result.exit_code == 0, f"Validate command failed: {result.stdout}"


def test_validate_accepts_yaml_file(temp_dir: Path) -> None:
    """Test that validate command accepts a YAML schema file."""
    # Create a valid schema
    schema_content = """schnitzel: "1.0"

models:
  Product:
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

    # Run validate command
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should succeed
    assert result.exit_code == 0
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()


def test_validate_detects_yaml_syntax_errors(temp_dir: Path) -> None:
    """Test that validate detects YAML syntax errors."""
    # Create a schema with invalid YAML syntax (missing colon)
    invalid_yaml = """schnitzel "1.0"

models:
  User:
    fields:
      id
        type: uuid
"""
    schema_file = temp_dir / "invalid.yaml"
    schema_file.write_text(invalid_yaml)

    # Run validate command
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention YAML or syntax error
    assert "yaml" in result.stdout.lower() or "syntax" in result.stdout.lower()


def test_validate_detects_missing_schema_version(temp_dir: Path) -> None:
    """Test that validate detects missing schema version."""
    # Create a schema without version
    schema_content = """models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "no_version.yaml"
    schema_file.write_text(schema_content)

    # Run validate command
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention version
    assert "version" in result.stdout.lower()


def test_validate_detects_unsupported_field_type(temp_dir: Path) -> None:
    """Test that validate detects unsupported field types."""
    # Create a schema with an unsupported field type
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      age:
        type: invalid_type
"""
    schema_file = temp_dir / "bad_type.yaml"
    schema_file.write_text(schema_content)

    # Run validate command
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention the unsupported type
    assert "unsupported" in result.stdout.lower() or "invalid" in result.stdout.lower()


def test_validate_detects_missing_field_type(temp_dir: Path) -> None:
    """Test that validate detects fields missing type definition."""
    # Create a schema with a field missing type
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "missing_type.yaml"
    schema_file.write_text(schema_content)

    # Run validate command
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention missing type
    assert "type" in result.stdout.lower()


def test_validate_detects_invalid_relationship(temp_dir: Path) -> None:
    """Test that validate detects relationships to non-existent models."""
    # Create a schema with invalid relationship
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
    relations:
      author:
        type: belongsTo
        model: User
"""
    schema_file = temp_dir / "bad_relation.yaml"
    schema_file.write_text(schema_content)

    # Run validate command
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention relationship or model not found
    assert (
        "relationship" in result.stdout.lower()
        or "does not exist" in result.stdout.lower()
        or "user" in result.stdout.lower()
    )


def test_validate_shows_helpful_error_messages(temp_dir: Path) -> None:
    """Test that error messages are helpful and actionable."""
    # Create a schema with an unsupported type
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      score:
        type: decimal
"""
    schema_file = temp_dir / "test.yaml"
    schema_file.write_text(schema_content)

    # Run validate command
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1

    # Error message should be helpful:
    # - Mention the field and model
    # - Suggest valid types
    assert "decimal" in result.stdout.lower() or "score" in result.stdout.lower()
    assert "supported" in result.stdout.lower() or "did you mean" in result.stdout.lower()


def test_validate_detects_naming_convention_violations(temp_dir: Path) -> None:
    """Test that validate detects naming convention violations."""
    # Create a schema with naming violations
    schema_content = """schnitzel: "1.0"

models:
  user_model:
    fields:
      id:
        type: uuid
        primary: true
      UserName:
        type: string
"""
    schema_file = temp_dir / "bad_names.yaml"
    schema_file.write_text(schema_content)

    # Run validate command
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention naming convention
    assert (
        "naming" in result.stdout.lower()
        or "pascalcase" in result.stdout.lower()
        or "snake_case" in result.stdout.lower()
    )


def test_validate_with_strict_flag(temp_dir: Path) -> None:
    """Test that --strict flag is accepted."""
    # Create a valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "test.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --strict
    result = runner.invoke(app, ["validate", str(schema_file), "--strict"])

    # Should succeed (schema is valid)
    assert result.exit_code == 0


def test_validate_with_breaking_flag(temp_dir: Path) -> None:
    """Test that --breaking flag requires --compare-with option."""
    # Create a valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "test.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --breaking but no --compare-with
    result = runner.invoke(app, ["validate", str(schema_file), "--breaking"])

    # Should fail since --compare-with is required
    assert result.exit_code == 1
    assert "compare-with" in result.stdout.lower() or "MISSING_COMPARE_WITH" in result.stdout


def test_validate_shows_schema_summary(temp_dir: Path) -> None:
    """Test that validate shows a summary of the schema."""
    # Create a schema with multiple models
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
    relations:
      author:
        type: belongsTo
        model: User
"""
    schema_file = temp_dir / "test.yaml"
    schema_file.write_text(schema_content)

    # Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should succeed
    assert result.exit_code == 0

    # Should show summary with model names
    assert "user" in result.stdout.lower() or "User" in result.stdout
    assert "post" in result.stdout.lower() or "Post" in result.stdout


def test_validate_detects_duplicate_field_names(temp_dir: Path) -> None:
    """Test that validate detects duplicate field names in a model."""
    # Create a schema with duplicate field names
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      name:
        type: string
"""
    schema_file = temp_dir / "duplicate_fields.yaml"
    schema_file.write_text(schema_content)

    # Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention duplicate
    assert "duplicate" in result.stdout.lower()


def test_validate_detects_circular_dependencies(temp_dir: Path) -> None:
    """Test that validate detects circular relationship dependencies."""
    # Create a schema with circular belongsTo relationships
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
    relations:
      profile:
        type: belongsTo
        model: Profile

  Profile:
    fields:
      id:
        type: uuid
        primary: true
    relations:
      user:
        type: belongsTo
        model: User
"""
    schema_file = temp_dir / "circular.yaml"
    schema_file.write_text(schema_content)

    # Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention circular dependency
    assert "circular" in result.stdout.lower()


def test_validate_works_with_quiet_mode(temp_dir: Path) -> None:
    """Test that validate works with --quiet mode."""
    # Create a valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "test.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --quiet
    result = runner.invoke(app, ["--quiet", "validate", str(schema_file)])

    # Should succeed
    assert result.exit_code == 0
    # Output should be minimal
    assert len(result.stdout.strip()) < 50


def test_validate_detects_invalid_constraints(temp_dir: Path) -> None:
    """Test that validate detects invalid field constraints."""
    # Create a schema with invalid min/max constraints
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      price:
        type: float
        min: 100
        max: 10
"""
    schema_file = temp_dir / "bad_constraints.yaml"
    schema_file.write_text(schema_content)

    # Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention constraint error
    assert (
        "constraint" in result.stdout.lower()
        or "min" in result.stdout.lower()
        or "max" in result.stdout.lower()
    )


def test_validate_detects_format_on_non_string(temp_dir: Path) -> None:
    """Test that validate detects format constraint on non-string fields."""
    # Create a schema with format on non-string field
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      age:
        type: int
        format: email
"""
    schema_file = temp_dir / "bad_format.yaml"
    schema_file.write_text(schema_content)

    # Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should fail
    assert result.exit_code == 1
    # Should mention format constraint
    assert "format" in result.stdout.lower()


def test_validate_complex_valid_schema(temp_dir: Path) -> None:
    """Test validate with a complex but valid schema."""
    # Create a complex schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "Application user"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
        format: email
      name:
        type: string
      age:
        type: int
        min: 0
        max: 150
      created_at:
        type: datetime
    relations:
      posts:
        type: hasMany
        model: Post

  Post:
    description: "Blog post"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
      published:
        type: bool
      views:
        type: int
        min: 0
    relations:
      author:
        type: belongsTo
        model: User
"""
    schema_file = temp_dir / "complex.yaml"
    schema_file.write_text(schema_content)

    # Run validate
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should succeed
    assert result.exit_code == 0
    assert "valid" in result.stdout.lower() or "ok" in result.stdout.lower()
