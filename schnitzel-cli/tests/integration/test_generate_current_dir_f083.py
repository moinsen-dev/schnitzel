"""Integration tests for F083 - Generate command runs in current directory if schema exists.

Test Requirements:
- test_generate_uses_default_schema - uses schema.schnitzel.yaml by default
- test_generate_explicit_path_works - explicit path still works
- test_generate_fails_if_no_schema - should fail if no schema found
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


@pytest.fixture
def simple_schema_content() -> str:
    """Return simple schema content for testing."""
    return """schnitzel: "1.0"

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
      created_at:
        type: datetime
        auto: create
"""


def test_generate_uses_default_schema(temp_dir: Path, simple_schema_content: str) -> None:
    """Test that generate command uses schema.schnitzel.yaml by default in current directory."""
    # Create schema.schnitzel.yaml in current directory (temp_dir)
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    default_schema_file.write_text(simple_schema_content)

    # Run generate command WITHOUT specifying schema path
    result = runner.invoke(app, ["generate"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify that files were generated
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    assert python_models_file.exists(), "Python models should be generated using default schema"

    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists(), "Dart models should be generated using default schema"

    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert docker_compose_file.exists(), "Docker Compose should be generated using default schema"

    # Verify content of generated files
    python_content = python_models_file.read_text()
    assert "class User" in python_content, "User model should be in generated Python code"

    dart_content = dart_models_file.read_text()
    assert "class User" in dart_content, "User model should be in generated Dart code"


def test_generate_explicit_path_works(temp_dir: Path, simple_schema_content: str) -> None:
    """Test that generate command still works with explicit schema path."""
    # Create schema in a subdirectory with a custom name
    schemas_dir = temp_dir / "schemas"
    schemas_dir.mkdir()
    custom_schema_file = schemas_dir / "custom.schnitzel.yaml"
    custom_schema_file.write_text(simple_schema_content)

    # Run generate command WITH explicit schema path
    result = runner.invoke(app, ["generate", str(custom_schema_file)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Schema validation passed" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify that files were generated
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    assert python_models_file.exists(), "Python models should be generated with explicit path"

    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists(), "Dart models should be generated with explicit path"

    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert docker_compose_file.exists(), "Docker Compose should be generated with explicit path"


def test_generate_fails_if_no_schema(temp_dir: Path) -> None:
    """Test that generate command fails gracefully if no schema file is found."""
    # Ensure no schema.schnitzel.yaml exists in current directory
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists(), "Schema file should not exist for this test"

    # Run generate command without specifying schema path
    result = runner.invoke(app, ["generate"])

    # Verify failure
    assert result.exit_code == 1, "Command should fail when schema file doesn't exist"
    assert "Error: Schema file not found" in result.stdout or "not found" in result.stdout

    # Verify that NO files were generated
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_compose_file = temp_dir / "docker-compose.yaml"

    assert not python_models_file.exists(), "No Python models should be generated without schema"
    assert not dart_models_file.exists(), "No Dart models should be generated without schema"
    assert not docker_compose_file.exists(), "No Docker Compose should be generated without schema"


def test_generate_default_schema_with_target_option(temp_dir: Path, simple_schema_content: str) -> None:
    """Test that generate command works with default schema and --target option."""
    # Create schema.schnitzel.yaml in current directory
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    default_schema_file.write_text(simple_schema_content)

    # Run generate command without schema path but with --target python
    result = runner.invoke(app, ["generate", "--target", "python"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Schema parsed successfully" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify only Python models were generated
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    assert python_models_file.exists(), "Python models should be generated"

    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    assert not dart_models_file.exists(), "Dart models should NOT be generated with python target"

    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert not docker_compose_file.exists(), "Docker Compose should NOT be generated with python target"


def test_generate_default_schema_with_output_option(temp_dir: Path, simple_schema_content: str) -> None:
    """Test that generate command works with default schema and --output option."""
    # Create schema.schnitzel.yaml in current directory
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    default_schema_file.write_text(simple_schema_content)

    # Create custom output directory
    custom_output = temp_dir / "custom_output"
    custom_output.mkdir()

    # Run generate command without schema path but with --output
    result = runner.invoke(app, ["generate", "--output", str(custom_output)])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify files were generated in custom output directory
    python_models_file = custom_output / "backend" / "app" / "models.py"
    assert python_models_file.exists(), "Python models should be in custom output directory"

    dart_models_file = custom_output / "packages" / "app" / "lib" / "models" / "models.dart"
    assert dart_models_file.exists(), "Dart models should be in custom output directory"

    docker_compose_file = custom_output / "docker-compose.yaml"
    assert docker_compose_file.exists(), "Docker Compose should be in custom output directory"


def test_generate_default_schema_with_force_option(temp_dir: Path, simple_schema_content: str) -> None:
    """Test that generate command works with default schema and --force option."""
    # Create schema.schnitzel.yaml in current directory
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    default_schema_file.write_text(simple_schema_content)

    # First generation
    result1 = runner.invoke(app, ["generate"])
    assert result1.exit_code == 0

    # Modify generated file
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    original_content = python_models_file.read_text()
    python_models_file.write_text("# Modified\n" + original_content)

    # Second generation with --force (without schema path)
    result2 = runner.invoke(app, ["generate", "--force"])
    assert result2.exit_code == 0, f"Command failed: {result2.stdout}"

    # Verify file was overwritten
    final_content = python_models_file.read_text()
    assert "# Modified" not in final_content, "File should be overwritten"
    assert "class User" in final_content


def test_generate_default_schema_with_dry_run(temp_dir: Path, simple_schema_content: str) -> None:
    """Test that generate command works with default schema and --dry-run option."""
    # Create schema.schnitzel.yaml in current directory
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    default_schema_file.write_text(simple_schema_content)

    # Run generate command with --dry-run (without schema path)
    result = runner.invoke(app, ["generate", "--dry-run"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "DRY RUN MODE" in result.stdout
    assert "Files that would be generated" in result.stdout
    assert "No files were written" in result.stdout

    # Verify NO files were actually created
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    dart_models_file = temp_dir / "packages" / "app" / "lib" / "models" / "models.dart"
    docker_compose_file = temp_dir / "docker-compose.yaml"

    assert not python_models_file.exists(), "No files should be created in dry-run mode"
    assert not dart_models_file.exists(), "No files should be created in dry-run mode"
    assert not docker_compose_file.exists(), "No files should be created in dry-run mode"


def test_generate_default_vs_explicit_produce_same_output(temp_dir: Path, simple_schema_content: str) -> None:
    """Test that using default schema and explicit path produce equivalent output."""
    # Create schema.schnitzel.yaml in current directory
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    default_schema_file.write_text(simple_schema_content)

    # Run with default schema
    result1 = runner.invoke(app, ["generate", "--target", "python"])
    assert result1.exit_code == 0

    # Save generated content
    python_models_file = temp_dir / "backend" / "app" / "models.py"
    default_content = python_models_file.read_text()

    # Delete generated file
    python_models_file.unlink()

    # Run with explicit path
    result2 = runner.invoke(app, ["generate", str(default_schema_file), "--target", "python"])
    assert result2.exit_code == 0

    # Compare content - check that both have the same structure (ignoring timestamp)
    explicit_content = python_models_file.read_text()

    # Both should have the same User class
    assert "class User" in default_content
    assert "class User" in explicit_content

    # Both should have the same fields
    assert "id:" in default_content or "id :" in default_content
    assert "id:" in explicit_content or "id :" in explicit_content
    assert "name:" in default_content or "name :" in default_content
    assert "name:" in explicit_content or "name :" in explicit_content
    assert "email:" in default_content or "email :" in default_content
    assert "email:" in explicit_content or "email :" in explicit_content

    # Both should have the same imports
    assert "from pydantic import" in default_content
    assert "from pydantic import" in explicit_content

    # Both should have generation comments
    assert "Generated by Schnitzel Framework" in default_content
    assert "Generated by Schnitzel Framework" in explicit_content


def test_generate_default_schema_with_different_name_fails(temp_dir: Path, simple_schema_content: str) -> None:
    """Test that generate command fails if schema has a different name than default."""
    # Create schema with different name
    custom_schema_file = temp_dir / "my_custom_schema.yaml"
    custom_schema_file.write_text(simple_schema_content)

    # Ensure default schema doesn't exist
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists()

    # Run generate command without specifying path
    result = runner.invoke(app, ["generate"])

    # Verify failure
    assert result.exit_code == 1, "Command should fail when default schema doesn't exist"
    assert "Error: Schema file not found" in result.stdout or "not found" in result.stdout


def test_generate_default_schema_in_subdirectory_fails(temp_dir: Path, simple_schema_content: str) -> None:
    """Test that generate command doesn't automatically find schema in subdirectories."""
    # Create schema in a subdirectory
    subdir = temp_dir / "config"
    subdir.mkdir()
    schema_in_subdir = subdir / "schema.schnitzel.yaml"
    schema_in_subdir.write_text(simple_schema_content)

    # Ensure default schema doesn't exist in current directory
    default_schema_file = temp_dir / "schema.schnitzel.yaml"
    assert not default_schema_file.exists()

    # Run generate command without specifying path
    result = runner.invoke(app, ["generate"])

    # Verify failure - it should not find the schema in subdirectory
    assert result.exit_code == 1, "Command should fail when schema is not in current directory"
    assert "Error: Schema file not found" in result.stdout or "not found" in result.stdout
