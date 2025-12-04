"""Integration tests for F055 - Generate command with --target docker.

Test Requirements:
- test_generate_docker_creates_compose_file: Verify docker-compose.yaml is created
- test_generate_docker_does_not_create_python: Verify no Python models are generated
- test_generate_docker_does_not_create_dart: Verify no Dart models are generated
- test_generate_docker_has_db_service: Verify docker-compose.yaml has database service
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
def valid_schema(temp_dir: Path) -> Path:
    """Create a valid schema file for testing."""
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
    return schema_file


def test_generate_docker_creates_compose_file(temp_dir: Path, valid_schema: Path) -> None:
    """Test that generate --target docker creates docker-compose.yaml."""
    # Run generate command with docker target
    result = runner.invoke(app, ["generate", str(valid_schema), "--target", "docker"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Generating Docker Compose" in result.stdout
    assert "Generated docker-compose.yaml" in result.stdout
    assert "Generation complete" in result.stdout

    # Verify docker-compose.yaml exists
    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert docker_compose_file.exists(), "docker-compose.yaml should be created"


def test_generate_docker_does_not_create_python(temp_dir: Path, valid_schema: Path) -> None:
    """Test that generate --target docker does NOT create Python models."""
    # Run generate command with docker target
    result = runner.invoke(app, ["generate", str(valid_schema), "--target", "docker"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify no Python models are created
    # Common locations for Python models
    python_locations = [
        temp_dir / "backend" / "app" / "models.py",
        temp_dir / "backend" / "app" / "generated" / "models.py",
        temp_dir / "models.py",
        temp_dir / "generated" / "models.py",
    ]

    for location in python_locations:
        assert not location.exists(), f"Python models should not be created at {location}"


def test_generate_docker_does_not_create_dart(temp_dir: Path, valid_schema: Path) -> None:
    """Test that generate --target docker does NOT create Dart models."""
    # Run generate command with docker target
    result = runner.invoke(app, ["generate", str(valid_schema), "--target", "docker"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify no Dart models are created
    # Common locations for Dart models
    dart_locations = [
        temp_dir / "packages" / "app" / "lib" / "models.dart",
        temp_dir / "packages" / "app" / "lib" / "generated" / "models.dart",
        temp_dir / "lib" / "models.dart",
        temp_dir / "lib" / "generated" / "models.dart",
    ]

    for location in dart_locations:
        assert not location.exists(), f"Dart models should not be created at {location}"


def test_generate_docker_has_db_service(temp_dir: Path, valid_schema: Path) -> None:
    """Test that generated docker-compose.yaml has database service."""
    # Run generate command with docker target
    result = runner.invoke(app, ["generate", str(valid_schema), "--target", "docker"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read docker-compose.yaml
    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert docker_compose_file.exists(), "docker-compose.yaml should exist"

    compose_content = docker_compose_file.read_text()

    # Verify database service exists
    assert "services:" in compose_content, "docker-compose.yaml should have services section"
    assert "db:" in compose_content, "docker-compose.yaml should have db service"
    assert "postgres" in compose_content.lower(), "db service should use PostgreSQL"

    # Verify backend service exists
    assert "backend:" in compose_content, "docker-compose.yaml should have backend service"

    # Verify database configuration
    assert "POSTGRES_USER" in compose_content, "db service should have POSTGRES_USER"
    assert "POSTGRES_PASSWORD" in compose_content, "db service should have POSTGRES_PASSWORD"
    assert "POSTGRES_DB" in compose_content, "db service should have POSTGRES_DB"

    # Verify healthcheck
    assert "healthcheck:" in compose_content, "db service should have healthcheck"
    assert "pg_isready" in compose_content, "db healthcheck should use pg_isready"


def test_generate_docker_respects_existing_file(temp_dir: Path, valid_schema: Path) -> None:
    """Test that generate --target docker does NOT overwrite existing docker-compose.yaml without --force."""
    # Create existing docker-compose.yaml with different content
    docker_compose_file = temp_dir / "docker-compose.yaml"
    original_content = "version: '2.0'\nservices: {}"
    docker_compose_file.write_text(original_content)

    # Run generate command with docker target (no --force flag)
    result = runner.invoke(app, ["generate", str(valid_schema), "--target", "docker"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify file was NOT overwritten (should show warning)
    assert "Warning:" in result.stdout or "already exists" in result.stdout, "Should show warning about existing file"
    compose_content = docker_compose_file.read_text()
    assert compose_content == original_content, "File should NOT be overwritten without --force"


def test_generate_docker_overwrites_existing_file(temp_dir: Path, valid_schema: Path) -> None:
    """Test that generate --target docker overwrites existing docker-compose.yaml with --force."""
    # Create existing docker-compose.yaml with different content
    docker_compose_file = temp_dir / "docker-compose.yaml"
    docker_compose_file.write_text("version: '2.0'\nservices: {}")

    # Run generate command with docker target and --force flag
    result = runner.invoke(app, ["generate", str(valid_schema), "--target", "docker", "--force"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify file was overwritten with new content
    compose_content = docker_compose_file.read_text()
    assert "version: '3.8'" in compose_content, "File should be overwritten with new content"
    assert "db:" in compose_content, "New file should have db service"


def test_generate_docker_with_default_schema_path(temp_dir: Path) -> None:
    """Test that generate --target docker works with default schema path."""
    # Create schema file with default name
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
"""
    default_schema = temp_dir / "schema.schnitzel.yaml"
    default_schema.write_text(schema_content)

    # Run generate command without schema path argument
    result = runner.invoke(app, ["generate", "--target", "docker"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert "Generated docker-compose.yaml" in result.stdout

    # Verify docker-compose.yaml exists
    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert docker_compose_file.exists(), "docker-compose.yaml should be created"


def test_generate_docker_validates_schema_first(temp_dir: Path) -> None:
    """Test that generate --target docker validates schema before generating."""
    # Create invalid schema
    invalid_schema = temp_dir / "invalid.yaml"
    invalid_schema.write_text("""schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: invalid_type
        primary: true
""")

    # Run generate command with docker target
    result = runner.invoke(app, ["generate", str(invalid_schema), "--target", "docker"])

    # Verify failure
    assert result.exit_code == 1, "Command should fail with invalid schema"
    assert "Schema validation failed" in result.stdout

    # Verify docker-compose.yaml was NOT created
    docker_compose_file = temp_dir / "docker-compose.yaml"
    assert not docker_compose_file.exists(), "docker-compose.yaml should not be created on validation failure"


def test_generate_docker_output_format(temp_dir: Path, valid_schema: Path) -> None:
    """Test that generate --target docker has correct output format."""
    # Run generate command with docker target
    result = runner.invoke(app, ["generate", str(valid_schema), "--target", "docker"])

    # Verify success
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify output format matches specification
    output_lines = result.stdout.strip().split("\n")

    # Should contain these key messages (in any order)
    # Note: "Parsing schema:" is in transient progress bar, so we check for success message instead
    assert any("Schema parsed successfully" in line for line in output_lines), "Should show parse success"
    assert any("Schema validation passed" in line for line in output_lines), "Should show validation success"
    assert any("Docker Compose" in line for line in output_lines), "Should show docker generation message"
    assert any("docker-compose.yaml" in line for line in output_lines), "Should show docker completion"
    assert any("Generation complete" in line for line in output_lines), "Should show overall completion"
