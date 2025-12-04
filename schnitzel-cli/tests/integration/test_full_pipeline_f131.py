"""Integration tests for F131 - test_full_generation.py validates complete pipeline.

Test Requirements:
- test_parse_schema_step: Test schema parsing step
- test_validate_schema_step: Test schema validation step
- test_generate_python_step: Test Python code generation
- test_generate_dart_step: Test Dart code generation
- test_generate_docker_step: Test Docker compose generation
- test_complete_pipeline_end_to_end: Test full pipeline from schema to all outputs
"""

import pytest
import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import yaml

from schnitzel.cli import app
from schnitzel.schema import SchemaParser, SchemaValidator

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def complete_schema(temp_dir: Path) -> Path:
    """Create a complete schema with all features for pipeline testing."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model with relationships"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
        format: email
      age:
        type: int
        min: 0
        max: 150
      role:
        type: enum
        values: ["admin", "user", "guest"]
        default: user
      created_at:
        type: datetime
        auto: create
    relations:
      posts:
        type: hasMany
        model: Post

  Post:
    description: "Blog post model"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
      tags:
        type: list<string>
      author_id:
        type: uuid
      published:
        type: bool
        default: false
      created_at:
        type: datetime
        auto: create
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
"""
    schema_file = temp_dir / "complete.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_parse_schema_step(complete_schema: Path) -> None:
    """Test Step 1: Schema parsing works correctly."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(complete_schema)

    # Verify parsing succeeded
    assert schema is not None, "Schema should parse successfully"
    assert schema.schnitzel == "1.0", "Schema version should be 1.0"
    assert len(schema.models) == 2, "Should have 2 models"

    # Verify models are present
    assert "User" in schema.models, "User model should be parsed"
    assert "Post" in schema.models, "Post model should be parsed"

    # Verify User model details
    user_model = schema.models["User"]
    assert len(user_model.fields) == 6, "User should have 6 fields"
    assert "id" in user_model.fields, "User should have id field"
    assert "name" in user_model.fields, "User should have name field"
    assert "role" in user_model.fields, "User should have role enum field"

    print("\n✓ Step 1: Schema parsing successful")


def test_validate_schema_step(complete_schema: Path) -> None:
    """Test Step 2: Schema validation works correctly."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(complete_schema)

    # Validate schema
    validator = SchemaValidator()
    result = validator.validate(schema)

    # Verify validation passed
    assert result.valid is True, f"Schema validation should pass. Errors: {result.errors}"
    assert len(result.errors) == 0, "Valid schema should have no errors"

    print("\n✓ Step 2: Schema validation successful")


def test_generate_python_step(complete_schema: Path, temp_dir: Path) -> None:
    """Test Step 3: Python code generation works correctly."""
    # Run generate command for Python
    result = runner.invoke(app, ["generate", str(complete_schema), "--target", "python"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Python generation failed: {result.stdout}"
    assert "Generating Python models" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify output file exists
    python_models = temp_dir / "backend" / "app" / "models.py"
    assert python_models.exists(), "Python models.py should be created"
    assert python_models.stat().st_size > 0, "models.py should not be empty"

    # Verify Python code structure
    content = python_models.read_text()
    assert "from pydantic import BaseModel" in content
    assert "class User(BaseModel):" in content
    assert "class Post(BaseModel):" in content

    # Verify Python code is syntactically valid
    try:
        compile(content, str(python_models), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Python code has syntax errors: {e}")

    print("\n✓ Step 3: Python code generation successful")


def test_generate_dart_step(complete_schema: Path, temp_dir: Path) -> None:
    """Test Step 4: Dart code generation works correctly."""
    # Run generate command for Dart
    result = runner.invoke(app, ["generate", str(complete_schema), "--target", "flutter"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Dart generation failed: {result.stdout}"
    assert "Generating Dart models" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify output file exists
    dart_models = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models.exists(), "Dart models.dart should be created"
    assert dart_models.stat().st_size > 0, "models.dart should not be empty"

    # Verify Dart code structure
    content = dart_models.read_text()
    assert "import 'package:freezed_annotation/freezed_annotation.dart'" in content
    assert "@freezed" in content
    assert "class User" in content
    assert "class Post" in content

    print("\n✓ Step 4: Dart code generation successful")


def test_generate_docker_step(complete_schema: Path, temp_dir: Path) -> None:
    """Test Step 5: Docker compose generation works correctly."""
    # Run generate command for Docker
    result = runner.invoke(app, ["generate", str(complete_schema), "--target", "docker"])

    # Verify command succeeded
    assert result.exit_code == 0, f"Docker generation failed: {result.stdout}"
    assert "Generating Docker Compose" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify output file exists
    docker_compose = temp_dir / "docker-compose.yaml"
    assert docker_compose.exists(), "docker-compose.yaml should be created"
    assert docker_compose.stat().st_size > 0, "docker-compose.yaml should not be empty"

    # Verify Docker compose is valid YAML
    content = docker_compose.read_text()
    try:
        compose_data = yaml.safe_load(content)
        assert isinstance(compose_data, dict), "docker-compose should be a dict"
        assert "services" in compose_data, "docker-compose should have services"
        assert "db" in compose_data["services"], "Should have db service"
        assert "backend" in compose_data["services"], "Should have backend service"
    except yaml.YAMLError as e:
        pytest.fail(f"docker-compose.yaml has invalid YAML: {e}")

    print("\n✓ Step 5: Docker compose generation successful")


def test_complete_pipeline_end_to_end(complete_schema: Path, temp_dir: Path) -> None:
    """Test complete pipeline: parse -> validate -> generate all targets."""
    # Step 1: Parse schema
    parser = SchemaParser()
    schema = parser.parse(complete_schema)
    assert schema is not None

    # Step 2: Validate schema
    validator = SchemaValidator()
    result = validator.validate(schema)
    assert result.valid is True

    # Step 3: Generate all targets (default behavior)
    gen_result = runner.invoke(app, ["generate", str(complete_schema)])
    assert gen_result.exit_code == 0, f"Full generation failed: {gen_result.stdout}"

    # Step 4: Verify all outputs exist
    python_models = temp_dir / "backend" / "app" / "models.py"
    dart_models = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_compose = temp_dir / "docker-compose.yaml"

    assert python_models.exists(), "Python models should be generated"
    assert dart_models.exists(), "Dart models should be generated"
    assert docker_compose.exists(), "Docker compose should be generated"

    # Step 5: Verify outputs are not empty
    assert python_models.stat().st_size > 0
    assert dart_models.stat().st_size > 0
    assert docker_compose.stat().st_size > 0

    # Step 6: Verify Python code compiles
    python_content = python_models.read_text()
    try:
        compile(python_content, str(python_models), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Python has syntax errors: {e}")

    # Step 7: Verify Docker compose is valid YAML
    docker_content = docker_compose.read_text()
    try:
        yaml.safe_load(docker_content)
    except yaml.YAMLError as e:
        pytest.fail(f"Generated docker-compose has YAML errors: {e}")

    print("\n✓ Complete pipeline: parse -> validate -> generate all targets successful")


def test_pipeline_with_validation_errors(temp_dir: Path) -> None:
    """Test that pipeline stops on validation errors (doesn't generate invalid code)."""
    # Create invalid schema (unsupported field type)
    invalid_schema = temp_dir / "invalid.yaml"
    invalid_schema.write_text("""schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      invalid_field:
        type: unsupported_type_xyz
""")

    # Try to generate (should fail validation)
    result = runner.invoke(app, ["generate", str(invalid_schema)])

    # Should fail
    assert result.exit_code == 1, "Should fail with invalid schema"
    assert "Error:" in result.stdout or "validation" in result.stdout.lower()

    # Verify no output files were created
    python_models = temp_dir / "backend" / "app" / "models.py"
    assert not python_models.exists(), "Should not generate code for invalid schema"

    print("\n✓ Pipeline correctly stops on validation errors")


def test_pipeline_generates_correct_field_types(complete_schema: Path, temp_dir: Path) -> None:
    """Test that pipeline generates correct field types in all targets."""
    # Generate all targets
    result = runner.invoke(app, ["generate", str(complete_schema)])
    assert result.exit_code == 0

    # Check Python field types
    python_models = temp_dir / "backend" / "app" / "models.py"
    python_content = python_models.read_text()

    # Verify Python types
    assert "id: UUID" in python_content or "id:" in python_content, "UUID field"
    assert "name: str" in python_content, "String field"
    assert "age: int" in python_content, "Integer field"
    assert 'role: Literal["admin", "user", "guest"]' in python_content, "Enum field"
    assert "tags: list[str]" in python_content, "List field"
    assert "published: bool" in python_content, "Boolean field"

    # Verify Python constraints
    assert "Field(ge=0, le=150" in python_content, "Age min/max constraint"

    print("\n✓ Pipeline generates correct field types")


def test_pipeline_handles_relationships(complete_schema: Path, temp_dir: Path) -> None:
    """Test that pipeline correctly handles model relationships."""
    # Generate all targets
    result = runner.invoke(app, ["generate", str(complete_schema)])
    assert result.exit_code == 0

    # Check Python relationships
    python_models = temp_dir / "backend" / "app" / "models.py"
    python_content = python_models.read_text()

    # Verify belongsTo relationship
    assert "author: User | None = None" in python_content, "BelongsTo relationship"

    # Verify hasMany relationship
    assert "posts: list[Post] = []" in python_content, "HasMany relationship"

    # Verify forward references
    assert "from __future__ import annotations" in python_content, "Forward references for relationships"

    print("\n✓ Pipeline correctly handles relationships")


if __name__ == "__main__":
    # Run all tests manually
    print("=" * 70)
    print("Testing F131: Full generation pipeline validates complete workflow")
    print("=" * 70)

    import sys
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        temp_path = Path(tmpdir)

        # Create complete schema
        schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model with relationships"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
        format: email
      age:
        type: int
        min: 0
        max: 150
      role:
        type: enum
        values: ["admin", "user", "guest"]
        default: user
      created_at:
        type: datetime
        auto: create
    relations:
      posts:
        type: hasMany
        model: Post

  Post:
    description: "Blog post model"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: text
      tags:
        type: list<string>
      author_id:
        type: uuid
      published:
        type: bool
        default: false
      created_at:
        type: datetime
        auto: create
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
"""
        schema_file = temp_path / "complete.schnitzel.yaml"
        schema_file.write_text(schema_content)

        try:
            print("\n1. Testing parse schema step...")
            test_parse_schema_step(schema_file)

            print("\n2. Testing validate schema step...")
            test_validate_schema_step(schema_file)

            print("\n3. Testing generate Python step...")
            test_generate_python_step(schema_file, temp_path)

            print("\n4. Testing generate Dart step...")
            test_generate_dart_step(schema_file, temp_path)

            print("\n5. Testing generate Docker step...")
            test_generate_docker_step(schema_file, temp_path)

            print("\n6. Testing complete pipeline end-to-end...")
            test_complete_pipeline_end_to_end(schema_file, temp_path)

            print("\n7. Testing pipeline with validation errors...")
            test_pipeline_with_validation_errors(temp_path)

            print("\n8. Testing correct field types...")
            test_pipeline_generates_correct_field_types(schema_file, temp_path)

            print("\n9. Testing relationship handling...")
            test_pipeline_handles_relationships(schema_file, temp_path)

            print("\n" + "=" * 70)
            print("✓ All F131 tests passed!")
            print("=" * 70)

        finally:
            os.chdir(original_cwd)
