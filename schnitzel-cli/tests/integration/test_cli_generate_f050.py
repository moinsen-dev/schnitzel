"""Integration tests for F050 - Generate command parses and validates schema before generation.

Test Requirements:
- test_generate_parses_valid_schema
- test_generate_validates_schema
- test_generate_fails_on_invalid_yaml
- test_generate_uses_default_schema_path
- test_generate_accepts_custom_schema_path
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


def test_generate_parses_valid_schema(temp_dir: Path) -> None:
    """Test that generate command successfully parses a valid schema."""
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
      email:
        type: string
        unique: true
"""
    schema_file = temp_dir / "test_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    # With F053, the command now actually generates code (default target is 'all')
    assert "Generation complete" in result.stdout


def test_generate_validates_schema(temp_dir: Path) -> None:
    """Test that generate command validates the schema and reports validation errors."""
    # Create a schema with validation errors (unsupported type)
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
    assert "Schema validation failed" in result.stdout
    assert "Unsupported field type" in result.stdout or "invalid_type" in result.stdout


def test_generate_fails_on_invalid_yaml(temp_dir: Path) -> None:
    """Test that generate command fails gracefully on invalid YAML syntax."""
    # Create a file with invalid YAML syntax
    invalid_yaml = """schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
      name: [unclosed bracket
"""
    schema_file = temp_dir / "bad_yaml.yaml"
    schema_file.write_text(invalid_yaml)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify failure
    assert result.exit_code == 1, "Command should fail with invalid YAML"
    assert "YAML parsing failed" in result.stdout or "error" in result.stdout.lower()


def test_generate_uses_default_schema_path(temp_dir: Path) -> None:
    """Test that generate command uses default schema.schnitzel.yaml path."""
    # Create schema file with default name
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
    default_schema = temp_dir / "schema.schnitzel.yaml"
    default_schema.write_text(schema_content)

    # Run generate command without specifying schema path
    result = runner.invoke(app, ["generate"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    # The schema file name is shown in the transient progress bar, so we check for successful parsing
    assert "Schema parsed successfully" in result.stdout
    assert "Product" in result.stdout or "1 fields" in result.stdout or "3 fields" in result.stdout


def test_generate_accepts_custom_schema_path(temp_dir: Path) -> None:
    """Test that generate command accepts custom schema file paths."""
    # Create schema file with custom name
    schema_content = """schnitzel: "1.0"

models:
  Order:
    description: "An order model"
    fields:
      id:
        type: uuid
        primary: true
      order_number:
        type: string
        unique: true
      total:
        type: float
"""
    custom_schema = temp_dir / "custom_schema.yaml"
    custom_schema.write_text(schema_content)

    # Run generate command with custom schema path
    result = runner.invoke(app, ["generate", str(custom_schema)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    # The schema file name is shown in the transient progress bar, so we check for successful parsing
    assert "Schema parsed successfully" in result.stdout
    assert "Order" in result.stdout or "3 fields" in result.stdout


def test_generate_fails_on_missing_file(temp_dir: Path) -> None:
    """Test that generate command fails when schema file doesn't exist."""
    nonexistent_file = temp_dir / "nonexistent.yaml"

    # Run generate command with nonexistent file
    result = runner.invoke(app, ["generate", str(nonexistent_file)])

    # Verify failure
    assert result.exit_code == 1, "Command should fail with missing file"
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


def test_generate_validates_field_naming_convention(temp_dir: Path) -> None:
    """Test that generate command validates field naming conventions."""
    # Create schema with invalid field name (not snake_case)
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with invalid field name"
    fields:
      id:
        type: uuid
        primary: true
      userName:
        type: string
"""
    schema_file = temp_dir / "invalid_naming.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify failure
    assert result.exit_code == 1, "Command should fail with invalid field naming"
    assert "Schema validation failed" in result.stdout
    assert "naming convention" in result.stdout.lower() or "snake_case" in result.stdout.lower()


def test_generate_validates_model_naming_convention(temp_dir: Path) -> None:
    """Test that generate command validates model naming conventions."""
    # Create schema with invalid model name (not PascalCase)
    schema_content = """schnitzel: "1.0"

models:
  user_model:
    description: "Invalid model name"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "invalid_model_naming.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify failure
    assert result.exit_code == 1, "Command should fail with invalid model naming"
    assert "Schema validation failed" in result.stdout
    assert "naming convention" in result.stdout.lower() or "PascalCase" in result.stdout.lower()


def test_generate_shows_model_count(temp_dir: Path) -> None:
    """Test that generate command displays count of models found."""
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
      content:
        type: string
"""
    schema_file = temp_dir / "multi_model.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success and model count
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Models found: 2" in result.stdout or "2 models" in result.stdout.lower()
    assert "User" in result.stdout
    assert "Post" in result.stdout


def test_generate_shows_unique_constraints(temp_dir: Path) -> None:
    """Test that generate command displays unique constraints."""
    # Create schema with unique fields
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with unique constraints"
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
      username:
        type: string
        unique: true
"""
    schema_file = temp_dir / "unique_constraints.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success and unique constraints shown
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Unique constraints" in result.stdout
    assert "User.email" in result.stdout
    assert "User.username" in result.stdout


def test_generate_validates_relationships(temp_dir: Path) -> None:
    """Test that generate command validates relationship targets."""
    # Create schema with invalid relationship target
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
    schema_file = temp_dir / "invalid_relation.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify failure
    assert result.exit_code == 1, "Command should fail with invalid relationship"
    assert "Schema validation failed" in result.stdout
    assert "NonexistentUser" in result.stdout or "does not exist" in result.stdout


def test_generate_validates_numeric_constraints(temp_dir: Path) -> None:
    """Test that generate command validates min/max constraints."""
    # Create schema with invalid constraints (min > max)
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

    # Verify failure
    assert result.exit_code == 1, "Command should fail with invalid constraints"
    assert "Schema validation failed" in result.stdout
    assert "constraint" in result.stdout.lower() or "minimum" in result.stdout.lower()


def test_generate_parses_complex_schema(temp_dir: Path) -> None:
    """Test that generate command handles complex schemas with all features."""
    # Create comprehensive schema
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
      name:
        type: string
      bio:
        type: string
        optional: true
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
    description: "Post model"
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
    schema_file = temp_dir / "complex_schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    assert "Models found: 2" in result.stdout
    assert "User" in result.stdout
    assert "Post" in result.stdout
    assert "Unique constraints" in result.stdout
    assert "User.email" in result.stdout


def test_generate_default_schema_not_found(temp_dir: Path) -> None:
    """Test that generate command fails gracefully when default schema doesn't exist."""
    # Don't create any schema file
    # Run generate command without arguments (should look for default)
    result = runner.invoke(app, ["generate"])

    # Verify failure
    assert result.exit_code == 1, "Command should fail when default schema not found"
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()
