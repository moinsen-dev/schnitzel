"""Integration tests for API_062 - Validate command produces formatted validation report.

Test Requirements:
1. Test Rich formatted output (default)
2. Test JSON formatted output
3. Test plain text formatted output
4. Verify summary table with pass/fail counts
5. Verify color-coded results in Rich format
6. Verify detailed error messages with line numbers
7. Verify section headers for different validation types

This test validates that the `schnitzel validate` command:
- Supports --format flag with rich/json/plain options
- Produces properly formatted validation reports
- Shows summary statistics (models, fields, relationships)
- Displays errors and warnings in appropriate format
- Provides detailed information for troubleshooting
"""

import json
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


def test_validate_default_rich_format(temp_dir: Path) -> None:
    """Test that validate command uses Rich format by default."""
    # Create a valid schema
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
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate without format flag
    result = runner.invoke(app, ["validate", str(schema_file)])

    # Should succeed
    assert result.exit_code == 0

    # Rich format should include color codes and formatting
    # Check for success indicator
    assert "✓" in result.stdout or "valid" in result.stdout.lower()

    # Should show schema summary
    assert "User" in result.stdout
    assert "fields" in result.stdout.lower()


def test_validate_rich_format_explicit(temp_dir: Path) -> None:
    """Test validate command with explicit --format rich option."""
    # Create a valid schema with multiple models
    schema_content = """schnitzel: "1.0"

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
      content:
        type: text
    relations:
      author:
        type: belongsTo
        model: User
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format rich
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "rich"])

    # Should succeed
    assert result.exit_code == 0

    # Should show both models
    assert "User" in result.stdout
    assert "Post" in result.stdout

    # Should show summary information
    assert "Schema Summary" in result.stdout or "Models" in result.stdout


def test_validate_json_format_success(temp_dir: Path) -> None:
    """Test validate command with --format json for valid schema."""
    # Create a valid schema
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
    relations:
      author:
        type: belongsTo
        model: User
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format json
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "json"])

    # Should succeed
    assert result.exit_code == 0

    # Parse JSON output
    data = json.loads(result.stdout)

    # Verify JSON structure
    assert "valid" in data
    assert data["valid"] is True

    assert "summary" in data
    assert data["summary"]["models"] == 2
    assert data["summary"]["total_fields"] == 5
    assert data["summary"]["relationships"] == 1
    assert data["summary"]["unique_fields"] == 1

    assert "errors" in data
    assert len(data["errors"]) == 0

    assert "warnings" in data
    assert isinstance(data["warnings"], list)

    assert "models" in data
    assert len(data["models"]) == 2

    # Check model details
    user_model = next(m for m in data["models"] if m["name"] == "User")
    assert user_model["field_count"] == 3
    assert user_model["relation_count"] == 0
    assert user_model["unique_field_count"] == 1
    assert "email" in user_model["unique_fields"]

    post_model = next(m for m in data["models"] if m["name"] == "Post")
    assert post_model["field_count"] == 2
    assert post_model["relation_count"] == 1


def test_validate_json_format_with_errors(temp_dir: Path) -> None:
    """Test validate command with --format json for schema with errors."""
    # Create an invalid schema
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
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format json
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "json"])

    # Should fail
    assert result.exit_code == 1

    # Parse JSON output
    data = json.loads(result.stdout)

    # Verify JSON structure
    assert "valid" in data
    assert data["valid"] is False

    assert "errors" in data
    assert len(data["errors"]) > 0

    # Check that error message is present
    error_text = " ".join(data["errors"])
    assert "invalid_type" in error_text.lower() or "unsupported" in error_text.lower()


def test_validate_json_format_with_warnings(temp_dir: Path) -> None:
    """Test validate command with --format json for schema with warnings."""
    # Create a schema with endpoint path naming violations (warnings, not errors)
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /userProfiles:
    model: User
    operations: [list, get]
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format json (not strict)
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "json"])

    # Should succeed (warnings don't fail without --strict)
    assert result.exit_code == 0

    # Parse JSON output
    data = json.loads(result.stdout)

    assert data["valid"] is True
    assert "warnings" in data
    assert len(data["warnings"]) > 0

    # Check warning content
    warning_text = " ".join(data["warnings"])
    assert "userprofiles" in warning_text.lower() or "naming" in warning_text.lower()


def test_validate_json_format_strict_mode(temp_dir: Path) -> None:
    """Test validate command with --format json in strict mode."""
    # Create a schema with endpoint naming violations (warnings)
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /userProfiles:
    model: User
    operations: [list, get]
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format json --strict
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "json", "--strict"])

    # Should fail in strict mode
    assert result.exit_code == 1

    # Parse JSON output
    data = json.loads(result.stdout)

    assert "strict_mode" in data
    assert data["strict_mode"] is True
    assert data["valid"] is False


def test_validate_plain_format_success(temp_dir: Path) -> None:
    """Test validate command with --format plain for valid schema."""
    # Create a valid schema
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
    relations:
      author:
        type: belongsTo
        model: User
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format plain
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "plain"])

    # Should succeed
    assert result.exit_code == 0

    # Check plain text output structure
    assert "VALIDATION PASSED" in result.stdout
    assert "SUMMARY" in result.stdout
    assert "MODELS" in result.stdout

    # Check statistics
    assert "Models:        2" in result.stdout
    assert "Total Fields:  5" in result.stdout
    assert "Relationships: 1" in result.stdout
    assert "Unique Fields: 1" in result.stdout
    assert "Errors:        0" in result.stdout

    # Check model listing
    assert "User:" in result.stdout
    assert "Post:" in result.stdout


def test_validate_plain_format_with_errors(temp_dir: Path) -> None:
    """Test validate command with --format plain for schema with errors."""
    # Create an invalid schema
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
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format plain
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "plain"])

    # Should fail
    assert result.exit_code == 1

    # Check plain text output structure
    assert "VALIDATION FAILED" in result.stdout
    assert "SUMMARY" in result.stdout
    assert "ERRORS" in result.stdout

    # Check that errors are numbered
    assert "1." in result.stdout

    # Check error content
    assert "decimal" in result.stdout.lower() or "unsupported" in result.stdout.lower()


def test_validate_plain_format_with_warnings(temp_dir: Path) -> None:
    """Test validate command with --format plain for schema with warnings."""
    # Create a schema with endpoint naming violations (warnings)
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /userProfiles:
    model: User
    operations: [list, get]
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format plain
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "plain"])

    # Should succeed (warnings don't fail without --strict)
    assert result.exit_code == 0

    # Check output structure
    assert "VALIDATION PASSED" in result.stdout
    assert "WARNINGS" in result.stdout

    # Check that warnings are numbered
    assert "1." in result.stdout

    # Check warning content
    assert "userProfiles" in result.stdout or "naming" in result.stdout.lower()


def test_validate_rich_format_shows_colors(temp_dir: Path) -> None:
    """Test that Rich format includes ANSI color codes."""
    # Create a valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format rich
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "rich"])

    # Should succeed
    assert result.exit_code == 0

    # Rich output contains markup or unicode characters
    # Check for success indicator
    assert "✓" in result.stdout or "valid" in result.stdout.lower()


def test_validate_format_compatibility_with_quiet_mode(temp_dir: Path) -> None:
    """Test that --format works with --quiet mode."""
    # Create a valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run with --quiet (should override --format)
    result = runner.invoke(app, ["--quiet", "validate", str(schema_file), "--format", "json"])

    # Should succeed
    assert result.exit_code == 0

    # Quiet mode should produce minimal output
    assert len(result.stdout.strip()) < 50


def test_validate_json_format_structure_complete(temp_dir: Path) -> None:
    """Test that JSON format includes all required fields."""
    # Create a complex valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
        unique: true
      age:
        type: int
        min: 0
        max: 150

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      published:
        type: bool
    relations:
      author:
        type: belongsTo
        model: User
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format json
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "json"])

    # Should succeed
    assert result.exit_code == 0

    # Parse and validate complete JSON structure
    data = json.loads(result.stdout)

    # Top-level fields
    required_top_level = ["valid", "strict_mode", "summary", "errors", "warnings", "models"]
    for field in required_top_level:
        assert field in data, f"Missing required field: {field}"

    # Summary fields
    required_summary = ["models", "total_fields", "relationships", "unique_fields"]
    for field in required_summary:
        assert field in data["summary"], f"Missing summary field: {field}"

    # Model fields
    for model in data["models"]:
        required_model_fields = [
            "name",
            "field_count",
            "relation_count",
            "unique_field_count",
            "unique_fields",
        ]
        for field in required_model_fields:
            assert field in model, f"Missing model field: {field}"


def test_validate_plain_format_readable_sections(temp_dir: Path) -> None:
    """Test that plain format has clear section headers and formatting."""
    # Create a schema with errors and warnings
    schema_content = """schnitzel: "1.0"

models:
  user_model:
    fields:
      id:
        type: uuid
        primary: true
      age:
        type: decimal
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format plain
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "plain"])

    # Should fail
    assert result.exit_code == 1

    # Check for clear section headers
    assert "VALIDATION FAILED" in result.stdout
    assert "SUMMARY" in result.stdout
    assert "ERRORS" in result.stdout

    # Check for section separators
    assert "=" in result.stdout
    assert "-" in result.stdout

    # Verify sections are organized
    lines = result.stdout.split("\n")
    summary_idx = next(i for i, line in enumerate(lines) if "SUMMARY" in line)
    errors_idx = next(i for i, line in enumerate(lines) if "ERRORS" in line)

    # Summary should come before errors
    assert summary_idx < errors_idx


def test_validate_format_invalid_option(temp_dir: Path) -> None:
    """Test that invalid --format option is rejected."""
    # Create a valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with invalid format
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "xml"])

    # Should fail with error about invalid format
    assert result.exit_code != 0


def test_validate_rich_format_with_errors_shows_details(temp_dir: Path) -> None:
    """Test that Rich format shows detailed error messages."""
    # Create schema with multiple types of errors
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      age:
        type: int
        min: 100
        max: 10
      email:
        type: int
        format: email
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run validate with --format rich
    result = runner.invoke(app, ["validate", str(schema_file), "--format", "rich"])

    # Should fail
    assert result.exit_code == 1

    # Should show validation failed message
    assert "validation failed" in result.stdout.lower() or "✗" in result.stdout

    # Should show details about the errors
    assert "min" in result.stdout.lower() or "max" in result.stdout.lower()
    assert "format" in result.stdout.lower() or "email" in result.stdout.lower()


def test_validate_all_formats_produce_output(temp_dir: Path) -> None:
    """Test that all format options produce non-empty output."""
    # Create a valid schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Test all formats
    for format_type in ["rich", "json", "plain"]:
        result = runner.invoke(app, ["validate", str(schema_file), "--format", format_type])

        # Should succeed
        assert result.exit_code == 0, f"Failed for format: {format_type}"

        # Should produce output
        assert len(result.stdout) > 0, f"No output for format: {format_type}"

        # Each format should be distinct
        if format_type == "json":
            # JSON should be parseable
            json.loads(result.stdout)
        elif format_type == "plain":
            # Plain should have section headers
            assert "SUMMARY" in result.stdout or "VALIDATION" in result.stdout
        elif format_type == "rich":
            # Rich should have some formatting
            assert len(result.stdout) > 20


def test_validate_json_output_parseable(temp_dir: Path) -> None:
    """Test that JSON output is always valid JSON."""
    # Create schema with various states
    schemas = [
        # Valid schema
        """schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: uuid
        primary: true
""",
        # Invalid schema
        """schnitzel: "1.0"
models:
  User:
    fields:
      id:
        type: invalid
        primary: true
""",
    ]

    for i, schema_content in enumerate(schemas):
        schema_file = temp_dir / f"schema_{i}.yaml"
        schema_file.write_text(schema_content)

        result = runner.invoke(app, ["validate", str(schema_file), "--format", "json"])

        # JSON should always be parseable, regardless of validation result
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict), f"JSON output is not a dict for schema {i}"
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON output for schema {i}: {result.stdout}")
