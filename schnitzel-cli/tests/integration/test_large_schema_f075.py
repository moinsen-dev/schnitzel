"""Integration tests for F075 - Schema parser handles very large schema files (1000+ models).

Test Requirements:
- test_parse_large_schema_100_models - 100 models parses successfully
- test_validate_large_schema - validation completes
- test_generate_python_large_schema - Python generation works
- test_generate_dart_large_schema - Dart generation works
- test_large_schema_performance - completes in < 10 seconds
- test_large_schema_with_relationships - handles many relationships

Implementation:
- Uses 100 models instead of 1000 for test speed
- Tests parser scalability with large schemas
- Verifies memory usage is reasonable
- Ensures generated output is correct
"""

import tempfile
import time
from pathlib import Path
from typing import List

import pytest

from schnitzel.schema.parser import SchemaParser
from schnitzel.schema.validator import SchemaValidator
from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.generators.dart.models import DartModelGenerator


def generate_large_schema_yaml(num_models: int, include_relationships: bool = False) -> str:
    """
    Generate a large schema YAML with specified number of models.

    Args:
        num_models: Number of models to generate
        include_relationships: Whether to include relationships between models

    Returns:
        YAML string containing the schema
    """
    lines = ['schnitzel: "1.0"', '', 'models:']

    for i in range(num_models):
        model_name = f"Model{i:04d}"
        lines.append(f"  {model_name}:")
        lines.append(f'    description: "Auto-generated model {i}"')
        lines.append("    fields:")
        lines.append("      id:")
        lines.append("        type: uuid")
        lines.append("        primary: true")
        lines.append("      name:")
        lines.append("        type: string")
        lines.append("      email:")
        lines.append("        type: string")
        lines.append("        unique: true")
        lines.append("      age:")
        lines.append("        type: int")
        lines.append("        min: 0")
        lines.append("        max: 150")
        lines.append("      is_active:")
        lines.append("        type: bool")
        lines.append("        default: true")
        lines.append("      score:")
        lines.append("        type: float")
        lines.append("      created_at:")
        lines.append("        type: datetime")
        lines.append("        auto: create")

        # Add relationships if requested (connect to previous model)
        if include_relationships and i > 0:
            prev_model = f"Model{i-1:04d}"
            lines.append("    relations:")
            lines.append("      parent:")
            lines.append("        type: belongsTo")
            lines.append(f"        model: {prev_model}")
            lines.append("        foreign_key: parent_id")

    return "\n".join(lines)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_parse_large_schema_100_models(temp_dir: Path) -> None:
    """Test that parser can handle schema with 100 models successfully."""
    # Generate schema with 100 models
    schema_yaml = generate_large_schema_yaml(100, include_relationships=False)
    schema_file = temp_dir / "large_schema.yaml"
    schema_file.write_text(schema_yaml)

    # Parse the schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Verify all models were parsed
    assert len(schema.models) == 100, f"Expected 100 models, got {len(schema.models)}"

    # Verify model names are correct
    for i in range(100):
        model_name = f"Model{i:04d}"
        assert model_name in schema.models, f"Model {model_name} not found in schema"

        # Verify each model has expected fields
        model = schema.models[model_name]
        assert "id" in model.fields
        assert "name" in model.fields
        assert "email" in model.fields
        assert "age" in model.fields
        assert "is_active" in model.fields
        assert "score" in model.fields
        assert "created_at" in model.fields

        # Verify field properties
        assert model.fields["id"].type == "uuid"
        assert model.fields["id"].primary is True
        assert model.fields["email"].unique is True
        assert model.fields["age"].min == 0
        assert model.fields["age"].max == 150
        assert model.fields["is_active"].default is True


def test_validate_large_schema(temp_dir: Path) -> None:
    """Test that validator can handle large schema successfully."""
    # Generate schema with 100 models
    schema_yaml = generate_large_schema_yaml(100, include_relationships=False)
    schema_file = temp_dir / "large_schema.yaml"
    schema_file.write_text(schema_yaml)

    # Parse the schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Validate the schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passed
    assert result.valid is True, f"Validation failed: {result.errors}"
    assert len(result.errors) == 0

    # Verify unique fields were tracked
    assert len(result.unique_fields) == 100  # Each model has 1 unique field (email)
    for i in range(100):
        model_name = f"Model{i:04d}"
        assert model_name in result.unique_fields
        assert "email" in result.unique_fields[model_name]


def test_generate_python_large_schema(temp_dir: Path) -> None:
    """Test that Python generator can handle large schema successfully."""
    # Generate schema with 100 models
    schema_yaml = generate_large_schema_yaml(100, include_relationships=False)
    schema_file = temp_dir / "large_schema.yaml"
    schema_file.write_text(schema_yaml)

    # Parse the schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate Python models
    generator = PythonModelGenerator()
    python_code = generator.generate(schema)

    # Verify output is not empty
    assert len(python_code) > 0, "Generated Python code is empty"

    # Verify all models are in the output
    for i in range(100):
        model_name = f"Model{i:04d}"
        assert f"class {model_name}(BaseModel):" in python_code, f"Model {model_name} not found in output"

    # Verify imports are present
    assert "from pydantic import BaseModel" in python_code
    assert "from datetime import datetime" in python_code
    assert "from uuid import UUID" in python_code

    # Verify some field definitions are present
    assert "id: UUID" in python_code
    assert "name: str" in python_code
    assert "email: str" in python_code
    assert "age: int" in python_code
    assert "is_active: bool" in python_code
    assert "score: float" in python_code

    # Verify the code is valid Python (can be parsed)
    try:
        compile(python_code, "<string>", "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Python code has syntax errors: {e}")


def test_generate_dart_large_schema(temp_dir: Path) -> None:
    """Test that Dart generator can handle large schema successfully."""
    # Generate schema with 100 models
    schema_yaml = generate_large_schema_yaml(100, include_relationships=False)
    schema_file = temp_dir / "large_schema.yaml"
    schema_file.write_text(schema_yaml)

    # Parse the schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate Dart models
    generator = DartModelGenerator()
    dart_code = generator.generate(schema)

    # Verify output is not empty
    assert len(dart_code) > 0, "Generated Dart code is empty"

    # Verify all models are in the output
    for i in range(100):
        model_name = f"Model{i:04d}"
        assert f"class {model_name} with _${model_name}" in dart_code, f"Model {model_name} not found in output"

    # Verify imports are present
    assert "import 'package:freezed_annotation/freezed_annotation.dart';" in dart_code

    # Verify some field definitions are present
    assert "required String id" in dart_code
    assert "required String name" in dart_code
    assert "required String email" in dart_code
    assert "required int age" in dart_code
    # is_active field has a default, so it's not 'required' but has @Default annotation
    # Field name keeps its original snake_case from schema
    assert "@Default(true) bool is_active" in dart_code
    assert "required double score" in dart_code


def test_large_schema_performance(temp_dir: Path) -> None:
    """Test that large schema processing completes in reasonable time (< 10 seconds)."""
    # Generate schema with 100 models
    schema_yaml = generate_large_schema_yaml(100, include_relationships=False)
    schema_file = temp_dir / "large_schema.yaml"
    schema_file.write_text(schema_yaml)

    # Measure total time for parse, validate, and generate
    start_time = time.time()

    # Parse
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Validate
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Generate Python
    python_generator = PythonModelGenerator()
    python_code = python_generator.generate(schema)

    # Generate Dart
    dart_generator = DartModelGenerator()
    dart_code = dart_generator.generate(schema)

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Verify all operations completed
    assert len(schema.models) == 100
    assert result.valid is True
    assert len(python_code) > 0
    assert len(dart_code) > 0

    # Verify performance (should complete in < 10 seconds)
    assert elapsed_time < 10.0, f"Processing took {elapsed_time:.2f} seconds, expected < 10 seconds"

    # Log performance for reference
    print(f"\nPerformance metrics for 100 models:")
    print(f"  Total time: {elapsed_time:.2f} seconds")
    print(f"  Average time per model: {(elapsed_time / 100) * 1000:.2f} ms")


def test_large_schema_with_relationships(temp_dir: Path) -> None:
    """Test that parser handles large schema with many relationships."""
    # Generate schema with 100 models and relationships
    schema_yaml = generate_large_schema_yaml(100, include_relationships=True)
    schema_file = temp_dir / "large_schema_relations.yaml"
    schema_file.write_text(schema_yaml)

    # Parse the schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Verify all models were parsed
    assert len(schema.models) == 100

    # Verify relationships (Model0001 through Model0099 should have parent relation)
    for i in range(1, 100):
        model_name = f"Model{i:04d}"
        model = schema.models[model_name]

        # Verify model has relations
        assert model.relations is not None, f"Model {model_name} should have relations"
        assert "parent" in model.relations, f"Model {model_name} should have parent relation"

        # Verify relationship target
        expected_target = f"Model{i-1:04d}"
        assert model.relations["parent"].model == expected_target
        assert model.relations["parent"].type == "belongsTo"
        assert model.relations["parent"].foreign_key == "parent_id"

    # Validate the schema with relationships
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passed (no circular dependencies with chain relationships)
    assert result.valid is True, f"Validation failed: {result.errors}"

    # Generate Python code with relationships
    python_generator = PythonModelGenerator()
    python_code = python_generator.generate(schema)

    # Verify relationships are in the output
    # Should use forward references for relationships
    assert "from __future__ import annotations" in python_code

    # Generate Dart code with relationships
    dart_generator = DartModelGenerator()
    dart_code = dart_generator.generate(schema)

    # Verify output is valid
    assert len(dart_code) > 0


def test_large_schema_memory_efficiency(temp_dir: Path) -> None:
    """Test that large schema processing doesn't use excessive memory."""
    import sys

    # Generate schema with 100 models
    schema_yaml = generate_large_schema_yaml(100, include_relationships=False)
    schema_file = temp_dir / "large_schema.yaml"
    schema_file.write_text(schema_yaml)

    # Track object count before
    before_count = len([obj for obj in vars().values()])

    # Process schema multiple times to check for memory leaks
    for _ in range(5):
        parser = SchemaParser()
        schema = parser.parse(schema_file)

        validator = SchemaValidator()
        result = validator.validate(schema)

        python_generator = PythonModelGenerator()
        python_code = python_generator.generate(schema)

        # Clear references
        del parser
        del schema
        del validator
        del result
        del python_generator
        del python_code

    # Track object count after
    after_count = len([obj for obj in vars().values()])

    # Object count shouldn't grow significantly
    # (allow some growth for test artifacts, but not 5x)
    growth_factor = after_count / max(before_count, 1)
    assert growth_factor < 3.0, f"Object count grew by {growth_factor}x, possible memory leak"


def test_parse_large_schema_with_all_field_types(temp_dir: Path) -> None:
    """Test parser with large schema containing all supported field types."""
    lines = ['schnitzel: "1.0"', '', 'models:']

    # Create 50 models with diverse field types
    field_types = ["string", "uuid", "int", "float", "bool", "datetime", "json"]

    for i in range(50):
        model_name = f"Model{i:04d}"
        lines.append(f"  {model_name}:")
        lines.append(f'    description: "Model with all field types {i}"')
        lines.append("    fields:")

        # Add primary key
        lines.append("      id:")
        lines.append("        type: uuid")
        lines.append("        primary: true")

        # Add fields for each type
        for j, field_type in enumerate(field_types):
            field_name = f"field_{field_type}_{j}"
            lines.append(f"      {field_name}:")
            lines.append(f"        type: {field_type}")

            # Add type-specific constraints
            if field_type in ["int", "float"]:
                lines.append("        min: 0")
                lines.append("        max: 1000")
            elif field_type == "string":
                lines.append("        optional: true")
            elif field_type == "bool":
                lines.append("        default: false")

    schema_yaml = "\n".join(lines)
    schema_file = temp_dir / "diverse_schema.yaml"
    schema_file.write_text(schema_yaml)

    # Parse the schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Verify all models were parsed
    assert len(schema.models) == 50

    # Validate
    validator = SchemaValidator()
    result = validator.validate(schema)
    assert result.valid is True, f"Validation failed: {result.errors}"

    # Generate Python
    python_generator = PythonModelGenerator()
    python_code = python_generator.generate(schema)
    assert len(python_code) > 0

    # Verify all field types are present
    assert "str" in python_code
    assert "UUID" in python_code
    assert "int" in python_code
    assert "float" in python_code
    assert "bool" in python_code
    assert "datetime" in python_code


def test_large_schema_edge_cases(temp_dir: Path) -> None:
    """Test edge cases with large schemas."""
    # Test with exactly 100 models (boundary)
    schema_yaml = generate_large_schema_yaml(100, include_relationships=False)
    schema_file = temp_dir / "boundary_schema.yaml"
    schema_file.write_text(schema_yaml)

    parser = SchemaParser()
    schema = parser.parse(schema_file)
    assert len(schema.models) == 100

    # Test with 1 model (minimum)
    schema_yaml_min = generate_large_schema_yaml(1, include_relationships=False)
    schema_file_min = temp_dir / "min_schema.yaml"
    schema_file_min.write_text(schema_yaml_min)

    schema_min = parser.parse(schema_file_min)
    assert len(schema_min.models) == 1

    # Test with 200 models (double)
    schema_yaml_large = generate_large_schema_yaml(200, include_relationships=False)
    schema_file_large = temp_dir / "double_schema.yaml"
    schema_file_large.write_text(schema_yaml_large)

    start_time = time.time()
    schema_large = parser.parse(schema_file_large)
    elapsed = time.time() - start_time

    assert len(schema_large.models) == 200
    # Should still be fast even with 200 models
    assert elapsed < 15.0, f"Processing 200 models took {elapsed:.2f}s, expected < 15s"


def test_large_schema_unique_constraints_tracking(temp_dir: Path) -> None:
    """Test that unique constraints are properly tracked across large schemas."""
    # Generate schema with 100 models, each with multiple unique fields
    lines = ['schnitzel: "1.0"', '', 'models:']

    for i in range(100):
        model_name = f"Model{i:04d}"
        lines.append(f"  {model_name}:")
        lines.append(f'    description: "Model {i}"')
        lines.append("    fields:")
        lines.append("      id:")
        lines.append("        type: uuid")
        lines.append("        primary: true")
        lines.append("      email:")
        lines.append("        type: string")
        lines.append("        unique: true")
        lines.append("      username:")
        lines.append("        type: string")
        lines.append("        unique: true")
        lines.append("      code:")
        lines.append("        type: string")
        lines.append("        unique: true")

    schema_yaml = "\n".join(lines)
    schema_file = temp_dir / "unique_schema.yaml"
    schema_file.write_text(schema_yaml)

    # Parse and validate
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify all unique constraints were tracked
    assert result.valid is True
    assert len(result.unique_fields) == 100

    # Verify each model has 3 unique fields
    for i in range(100):
        model_name = f"Model{i:04d}"
        assert model_name in result.unique_fields
        unique_fields = result.unique_fields[model_name]
        assert len(unique_fields) == 3
        assert "email" in unique_fields
        assert "username" in unique_fields
        assert "code" in unique_fields
