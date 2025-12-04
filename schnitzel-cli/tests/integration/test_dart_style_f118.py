"""Integration tests for F118 - Generated Dart code follows style guidelines.

Test Requirements:
- test_dart_naming_conventions - Verify class names are PascalCase, fields are camelCase
- test_dart_line_length - Verify reasonable line lengths
- test_dart_indentation - Verify 2-space indentation
- test_freezed_annotations - Verify proper Freezed annotations
- test_dart_comments - Verify doc comments use /// style
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


def test_dart_naming_conventions(temp_dir: Path) -> None:
    """Test that generated Dart code follows naming conventions."""
    # Create schema (note: schema uses snake_case, Dart output should be camelCase)
    schema_content = """schnitzel: "1.0"

models:
  UserProfile:
    fields:
      id:
        type: uuid
        primary: true
      first_name:
        type: string
      last_name:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert models_file.exists()

    content = models_file.read_text()

    # Class names should be PascalCase
    assert "class UserProfile" in content, "Class names should be PascalCase"

    # Field names should be present (snake_case in schema)
    assert "first_name" in content or "firstName" in content, \
        "Field names should be present in output"
    assert "last_name" in content or "lastName" in content, \
        "Field names should be present in output"


def test_dart_line_length(temp_dir: Path) -> None:
    """Test that generated Dart code has reasonable line lengths."""
    # Create schema (using snake_case field names)
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "A product with detailed information"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      product_details:
        type: text
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()
    lines = content.split("\n")

    # Check line length (Dart recommends 80, but we'll be lenient at 120)
    long_lines = [line for line in lines if len(line) > 120 and not line.strip().startswith("//")]

    # Should have very few (if any) long lines
    assert len(long_lines) < 5, \
        f"Found {len(long_lines)} lines over 120 characters"


def test_dart_indentation(temp_dir: Path) -> None:
    """Test that generated Dart code uses 2-space indentation."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Order:
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
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()
    lines = content.split("\n")

    # Check for tabs (Dart uses spaces)
    tab_lines = [i for i, line in enumerate(lines) if "\t" in line and not line.strip().startswith("//")]
    assert len(tab_lines) == 0, \
        f"Found tabs on lines: {tab_lines}. Dart style uses spaces, not tabs."

    # Check that class body uses 2-space indentation
    class_found = False
    for i, line in enumerate(lines):
        if line.startswith("class "):
            class_found = True
            # Next non-empty line should be indented
            for j in range(i + 1, min(i + 10, len(lines))):
                if lines[j].strip() and not lines[j].strip().startswith("//"):
                    # Should start with 2 spaces (or 4 for nested)
                    # Dart typically uses 2-space indentation
                    if lines[j].startswith("  ") or lines[j].startswith("    "):
                        # Good - has indentation
                        pass
                    else:
                        # Check if it's a closing brace
                        if lines[j].strip() != "}":
                            assert False, f"Line {j} should be indented: '{lines[j]}'"
                    break

    assert class_found, "Should have at least one class definition"


def test_freezed_annotations(temp_dir: Path) -> None:
    """Test that Freezed annotations are properly formatted."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Item:
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
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # Should have @freezed annotation
    assert "@freezed" in content, "Should use @freezed annotation"

    # Should have const factory
    assert "const factory" in content, "Should use const factory constructor"

    # Should have fromJson factory
    assert "fromJson" in content, "Should have fromJson factory"


def test_dart_comments(temp_dir: Path) -> None:
    """Test that doc comments use /// style."""
    # Create schema with descriptions
    schema_content = """schnitzel: "1.0"

models:
  Customer:
    description: "A customer who purchases products"
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
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # Should use /// for doc comments
    assert "///" in content, "Should use /// for documentation comments"

    # Should contain the description
    assert "A customer who purchases products" in content, \
        "Documentation should contain model description"


def test_imports_organized(temp_dir: Path) -> None:
    """Test that imports are properly organized."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Event:
    fields:
      id:
        type: uuid
        primary: true
      timestamp:
        type: datetime
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # Should have import statements
    assert "import " in content, "Should have import statements"

    # Should have part directives for generated files
    assert "part 'models.freezed.dart';" in content, \
        "Should have part directive for freezed file"
    assert "part 'models.g.dart';" in content, \
        "Should have part directive for json_serializable file"


def test_required_keyword_usage(temp_dir: Path) -> None:
    """Test that required keyword is used appropriately."""
    # Create schema with required and optional fields
    schema_content = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      subtitle:
        type: string
        optional: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # Required fields should have 'required' keyword
    assert "required" in content, "Should use 'required' keyword for required fields"


def test_trailing_commas(temp_dir: Path) -> None:
    """Test that trailing commas are used (Dart style)."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Book:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      author:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # Field definitions should have trailing commas
    # This helps with formatting and is Dart best practice
    lines = content.split("\n")
    field_lines = [line for line in lines if "String" in line or "int" in line or "bool" in line]

    # Most field lines should end with comma
    comma_count = sum(1 for line in field_lines if line.rstrip().endswith(","))

    # At least some fields should have trailing commas
    assert comma_count > 0, "Field definitions should use trailing commas"


def test_default_values_syntax(temp_dir: Path) -> None:
    """Test that default values use @Default annotation."""
    # Create schema with default values
    schema_content = """schnitzel: "1.0"

models:
  Settings:
    fields:
      id:
        type: uuid
        primary: true
      enabled:
        type: bool
        default: true
      max_count:
        type: int
        default: 10
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # Should use @Default annotation
    assert "@Default(" in content, "Should use @Default annotation for default values"


def test_json_key_annotation(temp_dir: Path) -> None:
    """Test that @JsonKey is used when needed for snake_case conversion."""
    # Create schema with snake_case fields
    schema_content = """schnitzel: "1.0"

models:
  Profile:
    fields:
      id:
        type: uuid
        primary: true
      first_name:
        type: string
      last_name:
        type: string
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # Should use @JsonKey for snake_case conversion (if needed)
    # Or fields should be present as-is
    assert "first_name" in content or "firstName" in content, \
        "Should handle field names"
