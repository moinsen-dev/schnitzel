"""Integration tests for F148 - Large schema performance test (100+ models).

Test Requirements:
- test_generate_100_models - Generate 100 simple models
- test_performance_under_5_seconds - Generation completes in reasonable time
- test_large_schema_parses - Large schema parses successfully
- test_all_models_generated - All 100 models are in output
"""

import tempfile
from pathlib import Path
import time
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python import PythonModelGenerator
from schnitzel.generators.dart import DartModelGenerator


def generate_large_schema(num_models: int = 100) -> str:
    """Generate a schema with many models."""
    schema_lines = ['schnitzel: "1.0"', '', 'models:']

    for i in range(num_models):
        model_name = f"Model{i:03d}"
        schema_lines.extend([
            f"  {model_name}:",
            f'    description: "Auto-generated model {i}"',
            "    fields:",
            "      id:",
            "        type: uuid",
            "        primary: true",
            "      name:",
            "        type: string",
            "      value:",
            "        type: int",
            ""
        ])

    return '\n'.join(schema_lines)


def test_generate_100_models() -> None:
    """Test that we can generate 100 simple models."""
    schema_yaml = generate_large_schema(100)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Should have 100 models
        assert len(schema.models) == 100, f"Expected 100 models, got {len(schema.models)}"

        # Generate Python code
        generator = PythonModelGenerator()
        code = generator.generate(schema)

        # Verify all models are in code
        for i in range(100):
            model_name = f"Model{i:03d}"
            assert f"class {model_name}(BaseModel):" in code, f"Model {model_name} not found"

    finally:
        schema_path.unlink()


def test_performance_under_5_seconds() -> None:
    """Test that generation of 100 models completes in under 5 seconds."""
    schema_yaml = generate_large_schema(100)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        # Measure parsing time
        start_time = time.time()
        parser = SchemaParser()
        schema = parser.parse(schema_path)
        parse_time = time.time() - start_time

        # Measure Python generation time
        start_time = time.time()
        python_generator = PythonModelGenerator()
        python_code = python_generator.generate(schema)
        python_gen_time = time.time() - start_time

        # Measure Dart generation time
        start_time = time.time()
        dart_generator = DartModelGenerator()
        dart_code = dart_generator.generate(schema)
        dart_gen_time = time.time() - start_time

        total_time = parse_time + python_gen_time + dart_gen_time

        # Should complete in under 5 seconds
        assert total_time < 5.0, f"Generation took {total_time:.2f}s, should be under 5s"

        # Log performance for informational purposes
        print(f"\nPerformance metrics for 100 models:")
        print(f"  Parsing: {parse_time:.3f}s")
        print(f"  Python generation: {python_gen_time:.3f}s")
        print(f"  Dart generation: {dart_gen_time:.3f}s")
        print(f"  Total: {total_time:.3f}s")

    finally:
        schema_path.unlink()


def test_large_schema_parses() -> None:
    """Test that large schema parses successfully without errors."""
    schema_yaml = generate_large_schema(150)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Should parse successfully
        assert schema is not None
        assert len(schema.models) == 150
        assert schema.schnitzel in ["1.0", "1.0.0"]

    finally:
        schema_path.unlink()


def test_all_models_generated() -> None:
    """Test that all models from large schema are in generated output."""
    num_models = 50
    schema_yaml = generate_large_schema(num_models)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Generate Python code
        python_generator = PythonModelGenerator()
        python_code = python_generator.generate(schema)

        # Generate Dart code
        dart_generator = DartModelGenerator()
        dart_code = dart_generator.generate(schema)

        # Check all models are present in both outputs
        for i in range(num_models):
            model_name = f"Model{i:03d}"
            assert f"class {model_name}(BaseModel):" in python_code, \
                f"Python: Model {model_name} not found"
            assert f"class {model_name} with" in dart_code, \
                f"Dart: Model {model_name} not found"

    finally:
        schema_path.unlink()


def test_large_schema_with_relationships() -> None:
    """Test performance with a schema that has many relationships."""
    # Create a schema with 50 models, each having relationships
    schema_lines = ['schnitzel: "1.0"', '', 'models:']

    for i in range(50):
        model_name = f"Entity{i:02d}"
        next_model = f"Entity{(i + 1) % 50:02d}"

        schema_lines.extend([
            f"  {model_name}:",
            "    fields:",
            "      id:",
            "        type: uuid",
            "        primary: true",
            "      name:",
            "        type: string",
            "      related_id:",
            "        type: uuid",
            "        optional: true",
            "    relations:",
            "      related:",
            "        type: belongsTo",
            f"        model: {next_model}",
            "        foreign_key: related_id",
            ""
        ])

    schema_yaml = '\n'.join(schema_lines)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        start_time = time.time()

        parser = SchemaParser()
        schema = parser.parse(schema_path)

        python_generator = PythonModelGenerator()
        python_code = python_generator.generate(schema)

        elapsed = time.time() - start_time

        # Should complete quickly even with relationships
        assert elapsed < 3.0, f"Generation with relationships took {elapsed:.2f}s"

        # Verify relationships are present
        assert "from __future__ import annotations" in python_code
        assert "| None" in python_code  # Relationships create optional fields

    finally:
        schema_path.unlink()


def test_memory_efficiency_large_schema() -> None:
    """Test that large schemas don't consume excessive memory."""
    # Generate a very large schema
    schema_yaml = generate_large_schema(200)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_yaml)
        schema_path = Path(f.name)

    try:
        parser = SchemaParser()
        schema = parser.parse(schema_path)

        # Generate code
        python_generator = PythonModelGenerator()
        python_code = python_generator.generate(schema)

        # Basic sanity check - code should be reasonable size
        # Each model is roughly 150 bytes, so 200 models = ~30KB + imports
        assert len(python_code) < 1_000_000, "Generated code is unreasonably large"
        assert len(python_code) > 10_000, "Generated code seems too small"

    finally:
        schema_path.unlink()
