"""Integration tests for F068 - Full generation pipeline produces working code.

Test Requirements:
- test_full_pipeline_creates_all_files: runs generate, checks all outputs exist
- test_generated_python_is_syntactically_valid: compile Python code
- test_generated_python_imports_work: imports don't error
- test_generated_docker_compose_is_valid_yaml: parses as YAML
- test_full_pipeline_with_relationships: handles complex schema
- test_full_pipeline_with_enums: handles enum types
"""

import tempfile
import os
import sys
from pathlib import Path
from typer.testing import CliRunner
import pytest
import yaml

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


@pytest.fixture
def simple_schema(temp_dir: Path) -> Path:
    """Create a simple schema file for basic testing."""
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
    return schema_file


@pytest.fixture
def complex_schema_with_relationships(temp_dir: Path) -> Path:
    """Create a complex schema with relationships for advanced testing."""
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
      created_at:
        type: datetime
        auto: create
    relations:
      posts:
        type: hasMany
        model: Post
      profile:
        type: hasOne
        model: Profile

  Post:
    description: "Blog post model"
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
      comments:
        type: hasMany
        model: Comment

  Comment:
    description: "Comment model"
    fields:
      id:
        type: uuid
        primary: true
      content:
        type: string
      post_id:
        type: uuid
      author_id:
        type: uuid
      created_at:
        type: datetime
        auto: create
    relations:
      post:
        type: belongsTo
        model: Post
        foreign_key: post_id
      author:
        type: belongsTo
        model: User
        foreign_key: author_id

  Profile:
    description: "User profile model"
    fields:
      id:
        type: uuid
        primary: true
      user_id:
        type: uuid
        unique: true
      bio:
        type: string
        optional: true
      avatar_url:
        type: string
        optional: true
    relations:
      user:
        type: belongsTo
        model: User
        foreign_key: user_id
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


@pytest.fixture
def schema_with_enums(temp_dir: Path) -> Path:
    """Create a schema with enum types."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User with role enum"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      role:
        type: enum
        values: ["admin", "moderator", "user", "guest"]
        default: user

  Order:
    description: "Order with status enum"
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: enum
        values: ["pending", "processing", "shipped", "delivered", "cancelled"]
        default: pending
      total:
        type: float
      user_id:
        type: uuid
    relations:
      user:
        type: belongsTo
        model: User
        foreign_key: user_id
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_full_pipeline_creates_all_files(temp_dir: Path, simple_schema: Path) -> None:
    """Test that full generation pipeline creates all expected output files."""
    # Run generate command with all targets (default behavior)
    result = runner.invoke(app, ["generate", str(simple_schema)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify Python models file was created
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    assert python_models_file.exists(), "Python models.py should be created"
    assert python_models_file.stat().st_size > 0, "Python models.py should not be empty"

    # Verify Dart models file was created
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists(), "Dart models.dart should be created"
    assert dart_models_file.stat().st_size > 0, "Dart models.dart should not be empty"

    # Verify docker-compose.yaml was created
    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert docker_compose_file.exists(), "docker-compose.yaml should be created"
    assert docker_compose_file.stat().st_size > 0, "docker-compose.yaml should not be empty"


def test_generated_python_is_syntactically_valid(temp_dir: Path, simple_schema: Path) -> None:
    """Test that generated Python code is syntactically valid and can be compiled."""
    # Run generate command
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read generated Python models
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists(), "Python models.py should exist"

    models_content = models_file.read_text()

    # Verify Python syntax by compiling
    try:
        compile(models_content, str(models_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Python code has syntax errors: {e}")

    # Verify it contains expected Pydantic patterns
    assert "from pydantic import BaseModel" in models_content or "BaseModel" in models_content
    assert "class User" in models_content
    assert "id:" in models_content or "id :" in models_content


def test_generated_python_imports_work(temp_dir: Path, simple_schema: Path) -> None:
    """Test that generated Python code can be imported without errors."""
    # Run generate command
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read generated Python models
    models_file = temp_dir / "backend" / "app" / "models.py"
    assert models_file.exists()

    models_content = models_file.read_text()

    # Add the backend/app directory to sys.path
    backend_app_dir = temp_dir / "backend" / "app"
    sys.path.insert(0, str(backend_app_dir))

    try:
        # Try to import the models module
        # Note: We need to make sure the module name is unique to avoid conflicts
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_models_f068", models_file)
        assert spec is not None, "Could not create module spec"
        assert spec.loader is not None, "Module spec has no loader"

        models_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models_module)

        # Verify the User class exists
        assert hasattr(models_module, "User"), "User class should be defined"

        # Verify we can instantiate the User class (basic structure test)
        User = getattr(models_module, "User")
        assert User is not None
        assert callable(User), "User should be a class"

    except ImportError as e:
        pytest.fail(f"Generated Python code cannot be imported: {e}")
    except Exception as e:
        pytest.fail(f"Error when importing/using generated Python code: {e}")
    finally:
        # Clean up sys.path
        if str(backend_app_dir) in sys.path:
            sys.path.remove(str(backend_app_dir))


def test_generated_docker_compose_is_valid_yaml(temp_dir: Path, simple_schema: Path) -> None:
    """Test that generated docker-compose.yaml is valid YAML and can be parsed."""
    # Run generate command
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read docker-compose.yaml
    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert docker_compose_file.exists(), "docker-compose.yaml should exist"

    compose_content = docker_compose_file.read_text()

    # Verify YAML syntax by parsing
    try:
        compose_data = yaml.safe_load(compose_content)
    except yaml.YAMLError as e:
        pytest.fail(f"Generated docker-compose.yaml has YAML syntax errors: {e}")

    # Verify basic structure of docker-compose.yaml
    assert isinstance(compose_data, dict), "docker-compose.yaml should be a dictionary"
    assert "services" in compose_data, "docker-compose.yaml should have 'services' key"
    assert isinstance(compose_data["services"], dict), "services should be a dictionary"

    # Verify expected services exist
    services = compose_data["services"]
    assert "db" in services, "docker-compose.yaml should have 'db' service"
    assert "backend" in services, "docker-compose.yaml should have 'backend' service"


def test_generated_dart_has_valid_structure(temp_dir: Path, simple_schema: Path) -> None:
    """Test that generated Dart code has valid structure (basic syntax check)."""
    # Run generate command
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "flutter"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read generated Dart models
    models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert models_file.exists(), "Dart models.dart should exist"

    dart_content = models_file.read_text()

    # Verify basic Dart/Freezed structure
    assert "import 'package:freezed_annotation/freezed_annotation.dart';" in dart_content
    assert "part 'models.freezed.dart';" in dart_content
    assert "part 'models.g.dart';" in dart_content
    assert "@freezed" in dart_content
    assert "class User" in dart_content
    assert "factory User.fromJson" in dart_content or "fromJson" in dart_content

    # Verify basic Dart syntax patterns (class declaration, factory constructors)
    assert "const factory User(" in dart_content or "factory User(" in dart_content

    # Check for required fields
    assert "String id" in dart_content or "required String id" in dart_content
    assert "String name" in dart_content or "required String name" in dart_content


def test_full_pipeline_with_relationships(temp_dir: Path, complex_schema_with_relationships: Path) -> None:
    """Test that full pipeline handles complex schema with relationships correctly."""
    # Run generate command with all targets
    result = runner.invoke(app, ["generate", str(complex_schema_with_relationships)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Models found: 4" in result.stdout

    # Verify all output files were created
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_compose_file = temp_dir / "docker-compose.yaml"

    assert python_models_file.exists()
    assert dart_models_file.exists()
    assert docker_compose_file.exists()

    # Verify Python code is syntactically valid
    python_content = python_models_file.read_text()
    try:
        compile(python_content, str(python_models_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Python code with relationships has syntax errors: {e}")

    # Verify all models are present
    assert "class User" in python_content
    assert "class Post" in python_content
    assert "class Comment" in python_content
    assert "class Profile" in python_content

    # Verify Dart code contains all models
    dart_content = dart_models_file.read_text()
    assert "class User" in dart_content
    assert "class Post" in dart_content
    assert "class Comment" in dart_content
    assert "class Profile" in dart_content

    # Verify docker-compose.yaml is valid
    try:
        compose_data = yaml.safe_load(docker_compose_file.read_text())
        assert "services" in compose_data
        assert "db" in compose_data["services"]
    except yaml.YAMLError as e:
        pytest.fail(f"docker-compose.yaml with relationships has YAML errors: {e}")


def test_full_pipeline_with_enums(temp_dir: Path, schema_with_enums: Path) -> None:
    """Test that full pipeline handles enum types correctly."""
    # Run generate command with all targets
    result = runner.invoke(app, ["generate", str(schema_with_enums)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify all output files were created
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_compose_file = temp_dir / "docker-compose.yaml"

    assert python_models_file.exists()
    assert dart_models_file.exists()
    assert docker_compose_file.exists()

    # Verify Python code with enums is syntactically valid
    python_content = python_models_file.read_text()
    try:
        compile(python_content, str(python_models_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated Python code with enums has syntax errors: {e}")

    # Verify enums are defined in Python (inline enums in Literal or Enum)
    # The Python generator should create enum fields
    assert "class User" in python_content
    assert "class Order" in python_content

    # Check that role and status fields exist
    assert "role" in python_content
    assert "status" in python_content

    # Verify Dart code contains models
    dart_content = dart_models_file.read_text()
    assert "class User" in dart_content
    assert "class Order" in dart_content

    # Verify enum fields are present in Dart
    assert "role" in dart_content
    assert "status" in dart_content

    # Verify docker-compose.yaml is valid
    try:
        compose_data = yaml.safe_load(docker_compose_file.read_text())
        assert "services" in compose_data
    except yaml.YAMLError as e:
        pytest.fail(f"docker-compose.yaml with enums has YAML errors: {e}")


def test_full_pipeline_default_target_generates_all(temp_dir: Path, simple_schema: Path) -> None:
    """Test that generate command without --target flag generates all targets."""
    # Run generate command without --target (should default to 'all')
    result = runner.invoke(app, ["generate", str(simple_schema)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify all three types of files were created
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_compose_file = temp_dir / "docker-compose.yaml"

    assert python_models_file.exists(), "Python models should be generated with default target"
    assert dart_models_file.exists(), "Dart models should be generated with default target"
    assert docker_compose_file.exists(), "Docker Compose should be generated with default target"


def test_full_pipeline_with_force_flag(temp_dir: Path, simple_schema: Path) -> None:
    """Test that full pipeline with --force flag overwrites existing files."""
    # First generation
    result1 = runner.invoke(app, ["generate", str(simple_schema)])
    assert result1.exit_code == 0

    # Modify one of the generated files
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    original_content = python_models_file.read_text()
    python_models_file.write_text("# Modified content\n" + original_content)

    # Second generation without --force (should warn)
    result2 = runner.invoke(app, ["generate", str(simple_schema)])
    assert result2.exit_code == 0
    assert "Warning:" in result2.stdout or "already exists" in result2.stdout

    # Verify file was NOT overwritten (still has our modification)
    modified_content = python_models_file.read_text()
    assert "# Modified content" in modified_content

    # Third generation with --force (should overwrite)
    result3 = runner.invoke(app, ["generate", str(simple_schema), "--force"])
    assert result3.exit_code == 0

    # Verify file WAS overwritten (no longer has our modification)
    final_content = python_models_file.read_text()
    assert "# Modified content" not in final_content
    assert "class User" in final_content


def test_full_pipeline_validates_schema_before_generation(temp_dir: Path) -> None:
    """Test that full pipeline validates schema before attempting generation."""
    # Create invalid schema (unsupported field type)
    invalid_schema = temp_dir / "invalid.yaml"
    invalid_schema.write_text("""schnitzel: "1.0"

models:
  User:
    description: "User with invalid field type"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: invalid_type_xyz
""")

    # Run generate command
    result = runner.invoke(app, ["generate", str(invalid_schema)])

    # Verify failure
    assert result.exit_code == 1, "Command should fail with invalid schema"
    assert "Schema validation failed" in result.stdout or "Error:" in result.stdout

    # Verify NO files were created (validation failed before generation)
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_compose_file = temp_dir / "docker-compose.yaml"

    assert not python_models_file.exists(), "Python models should NOT be created on validation failure"
    assert not dart_models_file.exists(), "Dart models should NOT be created on validation failure"
    assert not docker_compose_file.exists(), "Docker Compose should NOT be created on validation failure"
