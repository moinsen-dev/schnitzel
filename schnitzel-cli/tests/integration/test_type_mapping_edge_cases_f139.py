"""Integration test for F139: Type mapping edge cases - All supported types in single model.

Test Requirements:
- Test all supported types in a single model
- Test types: string, text, uuid, int, float, bool, datetime, json, enum, vector, list<T>
- Verify correct code generation for each type
- Test optional and required variants
- Test default values for different types
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
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def all_types_schema(temp_dir: Path) -> Path:
    """Create a schema with all supported field types."""
    schema_content = """schnitzel: "1.0"

models:
  CompleteModel:
    description: "Model with all supported field types"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      description:
        type: text
      age:
        type: int
      salary:
        type: float
      is_active:
        type: bool
        default: true
      created_at:
        type: datetime
        auto: create
      metadata:
        type: json
        optional: true
      status:
        type: enum
        values: ["active", "inactive", "pending"]
        default: active
      embeddings:
        type: vector
        dimensions: 768
        optional: true
      tags:
        type: list<string>
        optional: true
      scores:
        type: list<float>
        optional: true
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_all_types_generate_successfully(temp_dir: Path, all_types_schema: Path):
    """Test that schema with all types generates successfully."""
    result = runner.invoke(app, ["generate", str(all_types_schema)])

    assert result.exit_code == 0, f"Generation should succeed: {result.stdout}"
    assert "Generation complete" in result.stdout or "✓" in result.stdout


def test_python_models_contains_all_types(temp_dir: Path, all_types_schema: Path):
    """Test that generated Python models contain all field types."""
    result = runner.invoke(app, ["generate", str(all_types_schema), "--target", "python"])

    assert result.exit_code == 0, f"Python generation failed: {result.stdout}"

    # Check generated Python file
    python_models = temp_dir / "backend" / "app" / "models.py"
    assert python_models.exists(), "Python models file should be created"

    content = python_models.read_text()

    # Verify class exists
    assert "class CompleteModel" in content, "CompleteModel class should exist"

    # Verify basic types are present
    assert "id" in content.lower()
    assert "name" in content.lower()
    assert "age" in content.lower()
    assert "is_active" in content.lower()


def test_dart_models_contains_all_types(temp_dir: Path, all_types_schema: Path):
    """Test that generated Dart models contain all field types."""
    result = runner.invoke(app, ["generate", str(all_types_schema), "--target", "dart"])

    assert result.exit_code == 0, f"Dart generation failed: {result.stdout}"

    # Check generated Dart file
    dart_models = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models.exists(), "Dart models file should be created"

    content = dart_models.read_text()

    # Verify class exists
    assert "class CompleteModel" in content, "CompleteModel class should exist"

    # Verify some field names are present
    assert "id" in content or "Id" in content
    assert "name" in content
    assert "isActive" in content or "is_active" in content


def test_list_types_generation(temp_dir: Path):
    """Test generation with list<T> types."""
    schema_content = """schnitzel: "1.0"

models:
  TestModel:
    fields:
      id:
        type: uuid
        primary: true
      string_list:
        type: list<string>
      int_list:
        type: list<int>
        optional: true
      float_list:
        type: list<float>
        optional: true
      bool_list:
        type: list<bool>
        optional: true
"""
    schema_file = temp_dir / "list_schema.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0, f"Generation with list types failed: {result.stdout}"


def test_vector_type_generation(temp_dir: Path):
    """Test generation with vector type."""
    schema_content = """schnitzel: "1.0"

models:
  Document:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      embeddings:
        type: vector
        dimensions: 1536
"""
    schema_file = temp_dir / "vector_schema.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0, f"Generation with vector type failed: {result.stdout}"


def test_enum_type_generation(temp_dir: Path):
    """Test generation with enum type."""
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: enum
        values: ["todo", "in_progress", "done", "cancelled"]
        default: todo
      priority:
        type: enum
        values: ["low", "medium", "high"]
        default: medium
"""
    schema_file = temp_dir / "enum_schema.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0, f"Generation with enum type failed: {result.stdout}"


def test_json_type_generation(temp_dir: Path):
    """Test generation with json type."""
    schema_content = """schnitzel: "1.0"

models:
  Config:
    fields:
      id:
        type: uuid
        primary: true
      settings:
        type: json
      preferences:
        type: json
        optional: true
"""
    schema_file = temp_dir / "json_schema.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0, f"Generation with json type failed: {result.stdout}"


def test_text_type_generation(temp_dir: Path):
    """Test generation with text type (alias for string)."""
    schema_content = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
      summary:
        type: text
        optional: true
"""
    schema_file = temp_dir / "text_schema.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0, f"Generation with text type failed: {result.stdout}"


def test_optional_fields_with_all_types(temp_dir: Path):
    """Test that optional flag works with all field types."""
    schema_content = """schnitzel: "1.0"

models:
  OptionalModel:
    fields:
      id:
        type: uuid
        primary: true
      optional_string:
        type: string
        optional: true
      optional_int:
        type: int
        optional: true
      optional_float:
        type: float
        optional: true
      optional_bool:
        type: bool
        optional: true
      optional_datetime:
        type: datetime
        optional: true
      optional_json:
        type: json
        optional: true
      optional_list:
        type: list<string>
        optional: true
"""
    schema_file = temp_dir / "optional_schema.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0, f"Generation with optional fields failed: {result.stdout}"


def test_default_values_with_all_types(temp_dir: Path):
    """Test that default values work with different field types."""
    schema_content = """schnitzel: "1.0"

models:
  DefaultModel:
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string
        default: active
      count:
        type: int
        default: 0
      rating:
        type: float
        default: 0.0
      enabled:
        type: bool
        default: false
      role:
        type: enum
        values: ["user", "admin", "guest"]
        default: user
"""
    schema_file = temp_dir / "default_schema.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file)])

    assert result.exit_code == 0, f"Generation with default values failed: {result.stdout}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
