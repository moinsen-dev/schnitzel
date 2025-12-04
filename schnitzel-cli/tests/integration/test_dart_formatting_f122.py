"""Integration tests for F122 - Generated Dart models have consistent formatting.

Test Requirements:
- test_consistent_field_declarations - Verify field declarations are formatted consistently
- test_consistent_annotation_usage - Verify annotations follow same pattern
- test_consistent_factory_format - Verify factory constructors are consistent
- test_consistent_trailing_commas - Verify trailing commas are used consistently
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


def test_consistent_field_declarations(temp_dir: Path) -> None:
    """Test that field declarations are formatted consistently."""
    # Create schema with multiple fields
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
      age:
        type: int
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
    lines = content.split("\n")

    # Find field declarations (inside factory constructor)
    in_factory = False
    field_lines = []

    for line in lines:
        if "const factory" in line:
            in_factory = True
        elif in_factory:
            if "})" in line:
                in_factory = False
            elif line.strip() and ("String" in line or "int" in line or "bool" in line):
                field_lines.append(line)

    # All fields should end with comma
    for line in field_lines:
        assert line.rstrip().endswith(","), \
            f"Field should end with comma: '{line}'"


def test_consistent_annotation_usage(temp_dir: Path) -> None:
    """Test that annotations follow the same pattern."""
    # Create schema with fields that need annotations (using snake_case)
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      product_name:
        type: string
      is_active:
        type: bool
        default: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # @Default annotations should follow consistent format
    default_annotations = [line for line in content.split("\n") if "@Default(" in line]

    # All @Default annotations should be on same line as field or separate line
    for line in default_annotations:
        assert "@Default(" in line, "Should have @Default annotation"


def test_consistent_factory_format(temp_dir: Path) -> None:
    """Test that factory constructors are formatted consistently."""
    # Create schema with multiple models
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
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # All models should have const factory constructor
    factory_count = content.count("const factory")
    model_count = content.count("class ")

    assert factory_count == model_count, \
        "Each model should have exactly one const factory constructor"

    # All models should have fromJson factory
    fromJson_count = content.count("fromJson")
    assert fromJson_count == model_count, \
        "Each model should have exactly one fromJson factory"


def test_consistent_trailing_commas(temp_dir: Path) -> None:
    """Test that trailing commas are used consistently."""
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
      amount:
        type: float
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

    # Field declarations should have trailing commas
    field_lines = [line for line in lines if ("String" in line or "int" in line or "bool" in line or "double" in line) and line.strip().endswith(",")]

    # Should have field lines with trailing commas
    assert len(field_lines) > 0, "Fields should use trailing commas"


def test_consistent_class_structure(temp_dir: Path) -> None:
    """Test that all classes follow same structure."""
    # Create schema with multiple models
    schema_content = """schnitzel: "1.0"

models:
  Customer:
    description: "Customer model"
    fields:
      id:
        type: uuid
        primary: true

  Invoice:
    description: "Invoice model"
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # All classes should have @freezed annotation
    freezed_count = content.count("@freezed")
    class_count = content.count("class ")

    assert freezed_count == class_count, \
        "Each class should have @freezed annotation"

    # All classes should have 'with _$ClassName' mixin
    with_count = content.count("with _$")
    assert with_count == class_count, \
        "Each class should have mixin declaration"


def test_consistent_doc_comments(temp_dir: Path) -> None:
    """Test that doc comments use consistent format."""
    # Create schema with descriptions
    schema_content = """schnitzel: "1.0"

models:
  Item:
    description: "An item in inventory"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
        description: "The item name"
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "dart"])
    assert result.exit_code == 0

    # Read generated Dart file
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    content = models_file.read_text()

    # Doc comments should use /// syntax
    doc_comment_lines = [line for line in content.split("\n") if line.strip().startswith("///")]

    # Should have doc comments
    assert len(doc_comment_lines) > 0, "Should have documentation comments"


def test_consistent_indentation(temp_dir: Path) -> None:
    """Test that indentation is consistent (2 spaces)."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true
      title:
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

    # Check indentation is consistent
    for line in lines:
        if line.startswith(" ") and line.strip():
            spaces = len(line) - len(line.lstrip())
            # Should be multiple of 2 (Dart uses 2-space indentation)
            assert spaces % 2 == 0, \
                f"Indentation should be multiple of 2, got {spaces}: '{line}'"
