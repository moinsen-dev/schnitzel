"""Integration tests for F053 - Generate command with --target python generates only Python files.

Test Requirements:
- test_generate_python_creates_models_file
- test_generate_python_does_not_create_dart
- test_generate_python_uses_python_generator
- test_generate_python_output_is_valid
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


def test_generate_python_creates_models_file(temp_dir: Path) -> None:
    """Test that generate command with --target python creates backend/app/models.py."""
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

    # Run generate command with --target python
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Generating Python models" in result.stdout
    assert "Generated Python models" in result.stdout or "Generated backend/app/models.py" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify models.py was created
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists(), "models.py should be created"

    # Verify models.py contains the User model
    models_content = models_file.read_text()
    assert "class User(BaseModel):" in models_content
    assert "from pydantic import BaseModel" in models_content
    assert "from uuid import UUID" in models_content


def test_generate_python_does_not_create_dart(temp_dir: Path) -> None:
    """Test that generate command with --target python does NOT create Dart files."""
    # Create a valid schema file
    schema_content = """schnitzel: "1.0"

models:
  Post:
    description: "A blog post"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with --target python
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify Dart files were NOT created
    dart_models_dir = temp_dir / "packages" / "app" / "lib" / "models"
    assert not dart_models_dir.exists(), "Dart models directory should NOT be created with --target python"

    # Verify Docker compose was NOT created
    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert not docker_compose_file.exists(), "docker-compose.yaml should NOT be created with --target python"

    # Verify Python models were created
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists(), "Python models.py should be created"


def test_generate_python_uses_python_generator(temp_dir: Path) -> None:
    """Test that generate command with --target python uses PythonModelGenerator."""
    # Create a schema with multiple models and relationships
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A user in the system"
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
        min: 0
        max: 150
      is_active:
        type: bool
        default: true
    relations:
      posts:
        type: hasMany
        model: Post

  Post:
    description: "A blog post"
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
    relations:
      author:
        type: belongsTo
        model: User
        foreign_key: author_id

  Comment:
    description: "A comment on a post"
    fields:
      id:
        type: uuid
        primary: true
      content:
        type: string
      post_id:
        type: uuid
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with --target python
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "3 models" in result.stdout

    # Read generated models.py
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists()
    models_content = models_file.read_text()

    # Verify PythonModelGenerator output characteristics:
    # 1. Uses Pydantic v2 syntax with | None instead of Optional
    assert "| None" in models_content, "Should use Pydantic v2 union syntax"
    assert "Optional[" not in models_content, "Should NOT use old Optional syntax"

    # 2. Uses __future__ annotations for forward references
    assert "from __future__ import annotations" in models_content

    # 3. Contains all three models
    assert "class User(BaseModel):" in models_content
    assert "class Post(BaseModel):" in models_content
    assert "class Comment(BaseModel):" in models_content

    # 4. Contains proper imports
    assert "from pydantic import BaseModel" in models_content
    assert "from uuid import UUID" in models_content

    # 5. Contains relationships
    assert "posts: list[Post] = []" in models_content  # hasMany
    assert "author: User | None = None" in models_content  # belongsTo

    # 6. Contains constraints
    assert "Field(ge=0, le=150" in models_content  # min/max constraints on age

    # 7. Has generation header
    assert "Generated by Schnitzel Framework" in models_content
    assert "DO NOT EDIT" in models_content


def test_generate_python_output_is_valid(temp_dir: Path) -> None:
    """Test that generated Python code is syntactically valid and can be imported."""
    # Create a schema with various field types
    schema_content = """schnitzel: "1.0"

models:
  Product:
    description: "A product in the catalog"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      description:
        type: string
        optional: true
      price:
        type: float
        min: 0.0
      quantity:
        type: int
        default: 0
      is_available:
        type: bool
        default: true
      created_at:
        type: datetime
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with --target python
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read generated models.py
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists()
    models_content = models_file.read_text()

    # Verify Python syntax by compiling
    try:
        compile(models_content, str(models_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Python code has syntax errors: {e}")

    # Verify it can be imported and used
    import sys
    sys.path.insert(0, str(temp_dir / "backend" / "app"))
    try:
        import models

        # Verify the Product class exists
        assert hasattr(models, "Product")

        # Verify we can create an instance
        from uuid import uuid4
        from datetime import datetime

        product = models.Product(
            id=uuid4(),
            name="Test Product",
            price=19.99,
            created_at=datetime.now()
        )

        # Verify fields
        assert product.name == "Test Product"
        assert product.price == 19.99
        assert product.quantity == 0  # default value
        assert product.is_available is True  # default value
        assert product.description is None  # optional field

    except ImportError as e:
        pytest.fail(f"Generated Python code cannot be imported: {e}")
    finally:
        sys.path.remove(str(temp_dir / "backend" / "app"))


def test_generate_python_with_three_models(temp_dir: Path) -> None:
    """Test that generate command correctly reports '3 models' in output."""
    # Create schema with exactly 3 models
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "A user"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Post:
    description: "A post"
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

  Comment:
    description: "A comment"
    fields:
      id:
        type: uuid
        primary: true
      content:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Run generate command with --target python
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify output mentions "3 models"
    assert "(3 models)" in result.stdout or "3 models" in result.stdout

    # Verify models.py was created with all 3 models
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists()
    models_content = models_file.read_text()
    assert "class User(BaseModel):" in models_content
    assert "class Post(BaseModel):" in models_content
    assert "class Comment(BaseModel):" in models_content


def test_generate_python_creates_directory_structure(temp_dir: Path) -> None:
    """Test that generate command creates the backend/app directory structure."""
    # Create a simple schema
    schema_content = """schnitzel: "1.0"

models:
  Item:
    description: "An item"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Verify backend/app doesn't exist yet
    backend_dir = temp_dir / "backend"
    app_dir = temp_dir / "backend" / "app"
    assert not backend_dir.exists()
    assert not app_dir.exists()

    # Run generate command with --target python
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify directory structure was created
    assert backend_dir.exists() and backend_dir.is_dir()
    assert app_dir.exists() and app_dir.is_dir()

    # Verify models.py exists
    models_file = app_dir / "models.py"
    assert models_file.exists() and models_file.is_file()
