"""Integration tests for F054 - Generate command with --target flutter generates only Dart files.

Test Requirements:
- test_generate_flutter_creates_models_file
- test_generate_flutter_does_not_create_python
- test_generate_flutter_uses_dart_generator
- test_generate_flutter_output_is_freezed_format
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


def test_generate_flutter_creates_models_file(temp_dir: Path) -> None:
    """Test that generate --target flutter creates Dart models file."""
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
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with flutter target
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    assert "Generating Dart models" in result.stdout
    assert "Generation complete!" in result.stdout

    # Verify that Dart models file was created
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists(), "Dart models file should be created"

    # Verify content of Dart models file
    dart_content = dart_models_file.read_text()
    assert "class User" in dart_content
    assert "@freezed" in dart_content
    assert "freezed_annotation" in dart_content


def test_generate_flutter_does_not_create_python(temp_dir: Path) -> None:
    """Test that generate --target flutter does NOT create Python models."""
    # Create a valid schema file
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
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with flutter target
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify that Python models file was NOT created
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    assert not python_models_file.exists(), "Python models file should NOT be created with flutter target"


def test_generate_flutter_does_not_create_docker(temp_dir: Path) -> None:
    """Test that generate --target flutter does NOT create docker-compose.yaml."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  Order:
    description: "An order model"
    fields:
      id:
        type: uuid
        primary: true
      total:
        type: float
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with flutter target
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify that docker-compose.yaml was NOT created
    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert not docker_compose_file.exists(), "docker-compose.yaml should NOT be created with flutter target"


def test_generate_flutter_uses_dart_generator(temp_dir: Path) -> None:
    """Test that generate --target flutter uses the Dart generator."""
    # Create a schema with multiple models
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
      author_id:
        type: uuid
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id

  Comment:
    description: "Comment model"
    fields:
      id:
        type: uuid
        primary: true
      content:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with flutter target
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Models found: 3" in result.stdout

    # Verify that Dart models file contains all three models
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists()

    dart_content = dart_models_file.read_text()
    assert "class User" in dart_content
    assert "class Post" in dart_content
    assert "class Comment" in dart_content


def test_generate_flutter_output_is_freezed_format(temp_dir: Path) -> None:
    """Test that generate --target flutter output is in Freezed format."""
    # Create a schema with various field types
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with various field types"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string
        unique: true
      age:
        type: int
        optional: true
      is_active:
        type: bool
        default: true
      created_at:
        type: datetime
        auto: create
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with flutter target
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify that Dart models file is in Freezed format
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists()

    dart_content = dart_models_file.read_text()

    # Check for Freezed annotations
    assert "@freezed" in dart_content
    assert "import 'package:freezed_annotation/freezed_annotation.dart';" in dart_content

    # Check for part directives (required for Freezed)
    assert "part 'models.freezed.dart';" in dart_content
    assert "part 'models.g.dart';" in dart_content

    # Check for JSON serialization
    assert "fromJson" in dart_content
    assert "Map<String, dynamic>" in dart_content

    # Check for factory constructor pattern
    assert "const factory User(" in dart_content

    # Check for proper field types
    assert "String id" in dart_content or "required String id" in dart_content
    assert "String name" in dart_content or "required String name" in dart_content
    assert "bool isActive" in dart_content or "bool is_active" in dart_content

    # Check for default value annotation
    assert "@Default" in dart_content


def test_generate_flutter_handles_relationships(temp_dir: Path) -> None:
    """Test that generate --target flutter properly handles model relationships."""
    # Create a schema with relationships
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
      author_id:
        type: uuid
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with flutter target
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify that Dart models file contains relationships
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists()

    dart_content = dart_models_file.read_text()

    # Check for hasMany relationship (should be List<Post>?)
    assert "List<Post>?" in dart_content or "posts" in dart_content

    # Check for belongsTo relationship (should be User?)
    assert "User?" in dart_content or "author" in dart_content


def test_generate_flutter_creates_output_directory(temp_dir: Path) -> None:
    """Test that generate --target flutter creates the output directory if it doesn't exist."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  TestModel:
    description: "Test model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Ensure the output directory does NOT exist
    output_dir = temp_dir / "packages" / "app" / "lib" / "models"
    assert not output_dir.exists(), "Output directory should not exist before generation"

    # Run generate command with flutter target
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify that the output directory was created
    assert output_dir.exists(), "Output directory should be created"
    assert output_dir.is_dir(), "Output path should be a directory"

    # Verify that models.dart was created
    models_file = output_dir / "models.dart"
    assert models_file.exists(), "models.dart should be created"


def test_generate_flutter_includes_generation_metadata(temp_dir: Path) -> None:
    """Test that generated Dart file includes metadata comments."""
    # Create a valid schema file
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
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with flutter target
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify that Dart models file includes metadata
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists()

    dart_content = dart_models_file.read_text()

    # Check for generation metadata
    assert "Generated by Schnitzel Framework" in dart_content
    assert "DO NOT EDIT" in dart_content
    assert "schema.schnitzel.yaml" in dart_content
