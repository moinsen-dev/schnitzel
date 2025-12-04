"""Integration tests for API_057 - Validate command detects breaking changes.

Test Requirements:
1. Verify validate command can detect breaking schema changes
2. Test detection of removed required fields
3. Test detection of type changes that lose data
4. Test detection of removed models
5. Test --breaking flag enables strict checking
6. Test --compare-with option for comparing schemas

This test validates that the `schnitzel validate` command with --breaking flag:
- Detects removed required fields as breaking changes
- Detects incompatible type changes (e.g., string -> int)
- Detects removed models
- Provides clear error messages about breaking changes
- Allows backward-compatible changes (adding optional fields, adding models)
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


def test_breaking_flag_requires_compare_with(temp_dir: Path) -> None:
    """Test that --breaking flag requires --compare-with option.

    Step 1: Create a valid schema
    Step 2: Run validate with --breaking but no --compare-with
    Step 3: Verify command fails with helpful error
    """
    # Step 1: Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Step 2: Run validate with --breaking only
    result = runner.invoke(app, ["validate", str(schema_file), "--breaking"])

    # Step 3: Verify it fails
    assert result.exit_code == 1
    assert "compare-with" in result.stdout.lower() or "MISSING_COMPARE_WITH" in result.stdout


def test_no_breaking_changes_for_identical_schemas(temp_dir: Path) -> None:
    """Test that identical schemas have no breaking changes.

    Step 1: Create two identical schemas
    Step 2: Run validate with --breaking --compare-with
    Step 3: Verify no breaking changes detected
    """
    # Step 1: Create identical schemas
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
"""
    old_schema = temp_dir / "old_schema.yaml"
    new_schema = temp_dir / "new_schema.yaml"
    old_schema.write_text(schema_content)
    new_schema.write_text(schema_content)

    # Step 2: Run validate
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 3: Verify no breaking changes
    assert result.exit_code == 0
    assert "no breaking changes" in result.stdout.lower() or "NO_BREAKING_CHANGES" in result.stdout


def test_detect_removed_required_field(temp_dir: Path) -> None:
    """Test detection of removed required field as breaking change.

    Step 1: Create old schema with required field
    Step 2: Create new schema with field removed
    Step 3: Run validate with --breaking
    Step 4: Verify breaking change is detected
    """
    # Step 1: Old schema with required field
    old_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        required: true
      email:
        type: string
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema without 'name' field
    new_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate with --breaking
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify breaking change detected
    assert result.exit_code == 1
    assert "breaking" in result.stdout.lower()
    assert "name" in result.stdout.lower()
    assert "removed" in result.stdout.lower()


def test_detect_field_type_change(temp_dir: Path) -> None:
    """Test detection of incompatible type change as breaking.

    Step 1: Create old schema with string field
    Step 2: Create new schema with same field as int
    Step 3: Run validate with --breaking
    Step 4: Verify breaking change is detected
    """
    # Step 1: Old schema with string field
    old_schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: string
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema with price as int
    new_schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: int
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate with --breaking
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify breaking change detected
    assert result.exit_code == 1
    assert "breaking" in result.stdout.lower()
    assert "price" in result.stdout.lower()
    assert "type" in result.stdout.lower() or "changed" in result.stdout.lower()


def test_detect_removed_model(temp_dir: Path) -> None:
    """Test detection of removed model as breaking change.

    Step 1: Create old schema with two models
    Step 2: Create new schema with one model removed
    Step 3: Run validate with --breaking
    Step 4: Verify breaking change is detected
    """
    # Step 1: Old schema with two models
    old_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Profile:
    fields:
      id:
        type: uuid
        primary: true
      bio:
        type: text
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema without Profile model
    new_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate with --breaking
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify breaking change detected
    assert result.exit_code == 1
    assert "breaking" in result.stdout.lower()
    assert "profile" in result.stdout.lower()
    assert "removed" in result.stdout.lower()


def test_adding_optional_field_not_breaking(temp_dir: Path) -> None:
    """Test that adding optional fields is not a breaking change.

    Step 1: Create old schema
    Step 2: Create new schema with additional optional field
    Step 3: Run validate with --breaking
    Step 4: Verify no breaking changes
    """
    # Step 1: Old schema
    old_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema with optional field added
    new_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      age:
        type: int
        optional: true
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate with --breaking
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify no breaking changes
    assert result.exit_code == 0
    assert "no breaking changes" in result.stdout.lower() or "NO_BREAKING_CHANGES" in result.stdout


def test_adding_new_model_not_breaking(temp_dir: Path) -> None:
    """Test that adding new models is not a breaking change.

    Step 1: Create old schema with one model
    Step 2: Create new schema with additional model
    Step 3: Run validate with --breaking
    Step 4: Verify no breaking changes
    """
    # Step 1: Old schema
    old_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema with additional model
    new_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Product:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate with --breaking
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify no breaking changes
    assert result.exit_code == 0
    assert "no breaking changes" in result.stdout.lower() or "NO_BREAKING_CHANGES" in result.stdout


def test_detect_multiple_breaking_changes(temp_dir: Path) -> None:
    """Test detection of multiple breaking changes at once.

    Step 1: Create old schema
    Step 2: Create new schema with multiple breaking changes
    Step 3: Run validate with --breaking
    Step 4: Verify all breaking changes are reported
    """
    # Step 1: Old schema
    old_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        required: true
      age:
        type: int

  Product:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema with multiple breaking changes
    # - Remove required field 'name' from User
    # - Change type of 'age' from int to string
    # - Remove entire Product model
    new_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      age:
        type: string
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate with --breaking
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify all breaking changes reported
    assert result.exit_code == 1
    assert "breaking" in result.stdout.lower()
    # Should detect at least 3 breaking changes
    output_lower = result.stdout.lower()
    breaking_count = output_lower.count("breaking")
    assert breaking_count >= 3, f"Expected at least 3 breaking changes, found {breaking_count}"


def test_detect_field_optional_to_required_change(temp_dir: Path) -> None:
    """Test detection of field changing from optional to required.

    Step 1: Create old schema with optional field
    Step 2: Create new schema with same field as required
    Step 3: Run validate with --breaking
    Step 4: Verify breaking change is detected
    """
    # Step 1: Old schema with optional field
    old_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        optional: true
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema with required field
    new_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        required: true
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate with --breaking
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify breaking change detected
    assert result.exit_code == 1
    assert "breaking" in result.stdout.lower()
    assert "name" in result.stdout.lower()
    assert "required" in result.stdout.lower() or "optional" in result.stdout.lower()


def test_detect_removed_relationship(temp_dir: Path) -> None:
    """Test detection of removed relationship as breaking change.

    Step 1: Create old schema with relationship
    Step 2: Create new schema with relationship removed
    Step 3: Run validate with --breaking
    Step 4: Verify breaking change is detected
    """
    # Step 1: Old schema with relationship
    old_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

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
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema without relationship
    new_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate with --breaking
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify breaking change detected
    assert result.exit_code == 1
    assert "breaking" in result.stdout.lower()
    assert "author" in result.stdout.lower() or "relationship" in result.stdout.lower()


def test_breaking_changes_error_messages_are_helpful(temp_dir: Path) -> None:
    """Test that breaking change error messages are clear and actionable.

    Step 1: Create schemas with breaking change
    Step 2: Run validate with --breaking
    Step 3: Verify error message includes impact and migration guidance
    """
    # Step 1: Create schemas
    old_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        required: true
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    new_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 2: Run validate
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 3: Verify helpful error message
    assert result.exit_code == 1
    output = result.stdout
    # Should include field name
    assert "email" in output.lower()
    # Should explain impact
    assert "impact" in output.lower() or "break" in output.lower()
    # Should provide migration guidance
    assert "migration" in output.lower() or "update" in output.lower() or "optional" in output.lower()


def test_breaking_changes_with_quiet_mode(temp_dir: Path) -> None:
    """Test that --breaking works with --quiet mode.

    Step 1: Create schemas with breaking change
    Step 2: Run validate with --breaking and --quiet
    Step 3: Verify concise output with exit code 1
    """
    # Step 1: Create schemas
    old_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    new_schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 2: Run validate with --quiet
    result = runner.invoke(
        app,
        ["--quiet", "validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)],
    )

    # Step 3: Verify output
    assert result.exit_code == 1
    assert "BREAKING_CHANGES" in result.stdout or len(result.stdout.strip()) < 100


def test_type_change_string_to_float_is_breaking(temp_dir: Path) -> None:
    """Test that changing string to float is detected as breaking.

    Step 1: Create old schema with string field
    Step 2: Create new schema with float field
    Step 3: Run validate with --breaking
    Step 4: Verify breaking change is detected
    """
    # Step 1: Old schema
    old_schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      price:
        type: string
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema
    new_schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      price:
        type: float
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify breaking change
    assert result.exit_code == 1
    assert "breaking" in result.stdout.lower()
    assert "price" in result.stdout.lower()


def test_type_change_float_to_int_is_breaking(temp_dir: Path) -> None:
    """Test that changing float to int is detected as breaking (loses precision).

    Step 1: Create old schema with float field
    Step 2: Create new schema with int field
    Step 3: Run validate with --breaking
    Step 4: Verify breaking change is detected
    """
    # Step 1: Old schema
    old_schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      price:
        type: float
"""
    old_schema = temp_dir / "old_schema.yaml"
    old_schema.write_text(old_schema_content)

    # Step 2: New schema
    new_schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      price:
        type: int
"""
    new_schema = temp_dir / "new_schema.yaml"
    new_schema.write_text(new_schema_content)

    # Step 3: Run validate
    result = runner.invoke(
        app, ["validate", str(new_schema), "--breaking", "--compare-with", str(old_schema)]
    )

    # Step 4: Verify breaking change
    assert result.exit_code == 1
    assert "breaking" in result.stdout.lower()
    assert "price" in result.stdout.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
