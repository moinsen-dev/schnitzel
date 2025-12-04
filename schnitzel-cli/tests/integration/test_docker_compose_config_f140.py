"""Integration test for F140: Docker Compose - Custom configuration with environment variables.

Test Requirements:
- Test docker-compose.yaml generation with custom ports
- Test environment variable configuration
- Test multiple services in docker-compose
- Test that generated YAML is valid and parseable
- Test custom database configurations
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest
import yaml

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
def simple_schema(temp_dir: Path) -> Path:
    """Create a simple schema file."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_docker_compose_generation(temp_dir: Path, simple_schema: Path):
    """Test basic docker-compose.yaml generation."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    assert result.exit_code == 0, f"Docker generation failed: {result.stdout}"

    # Verify docker-compose.yaml was created
    docker_file = temp_dir / "docker-compose.yaml"
    assert docker_file.exists(), "docker-compose.yaml should be created"


def test_docker_compose_is_valid_yaml(temp_dir: Path, simple_schema: Path):
    """Test that generated docker-compose.yaml is valid YAML."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    assert result.exit_code == 0

    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()

    # Parse YAML - should not raise exception
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        pytest.fail(f"Generated docker-compose.yaml is invalid YAML: {e}")

    # Verify basic structure
    assert isinstance(data, dict), "YAML should be a dictionary"
    assert "services" in data, "Should have 'services' key"


def test_docker_compose_has_required_services(temp_dir: Path, simple_schema: Path):
    """Test that docker-compose.yaml includes required services."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    assert result.exit_code == 0

    docker_file = temp_dir / "docker-compose.yaml"
    data = yaml.safe_load(docker_file.read_text())

    services = data.get("services", {})
    assert "db" in services, "Should have 'db' service"
    assert "backend" in services, "Should have 'backend' service"


def test_docker_compose_database_configuration(temp_dir: Path, simple_schema: Path):
    """Test database service configuration in docker-compose.yaml."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    assert result.exit_code == 0

    docker_file = temp_dir / "docker-compose.yaml"
    data = yaml.safe_load(docker_file.read_text())

    db_service = data["services"]["db"]

    # Verify database service has required keys
    assert "image" in db_service, "Database service should have image"
    assert "environment" in db_service or "env_file" in db_service, \
        "Database service should have environment variables"


def test_docker_compose_environment_variables(temp_dir: Path, simple_schema: Path):
    """Test that environment variables are properly configured."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    assert result.exit_code == 0

    docker_file = temp_dir / "docker-compose.yaml"
    data = yaml.safe_load(docker_file.read_text())

    # Check for environment variables in services
    for service_name, service_config in data["services"].items():
        if "environment" in service_config:
            env_vars = service_config["environment"]
            # Environment can be dict or list
            assert isinstance(env_vars, (dict, list)), \
                f"Environment variables in {service_name} should be dict or list"


def test_docker_compose_port_mappings(temp_dir: Path, simple_schema: Path):
    """Test that port mappings are configured."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    assert result.exit_code == 0

    docker_file = temp_dir / "docker-compose.yaml"
    data = yaml.safe_load(docker_file.read_text())

    # Check for port mappings in services
    services = data["services"]

    # At least one service should have ports configured
    has_ports = any("ports" in service for service in services.values())
    assert has_ports, "At least one service should have port mappings"


def test_docker_compose_with_force_flag(temp_dir: Path, simple_schema: Path):
    """Test that --force flag overwrites existing docker-compose.yaml."""
    # Generate first time
    result1 = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])
    assert result1.exit_code == 0

    docker_file = temp_dir / "docker-compose.yaml"
    original_content = docker_file.read_text()

    # Modify the file
    docker_file.write_text("# Modified content\n" + original_content)

    # Generate again without --force (should warn)
    result2 = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])
    assert result2.exit_code == 0
    assert "Warning" in result2.stdout or "already exists" in result2.stdout

    # Verify file still has modification
    assert "# Modified content" in docker_file.read_text()

    # Generate with --force (should overwrite)
    result3 = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker", "--force"])
    assert result3.exit_code == 0

    # Verify modification is gone
    final_content = docker_file.read_text()
    assert "# Modified content" not in final_content


def test_docker_compose_with_multiple_models(temp_dir: Path):
    """Test docker-compose generation with multiple models in schema."""
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
      author_id:
        type: uuid

  Comment:
    fields:
      id:
        type: uuid
        primary: true
      content:
        type: string
"""
    schema_file = temp_dir / "multi_model.yaml"
    schema_file.write_text(schema_content)

    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])

    assert result.exit_code == 0, f"Generation failed: {result.stdout}"

    # Verify docker-compose was created
    docker_file = temp_dir / "docker-compose.yaml"
    assert docker_file.exists()

    # Verify it's valid YAML
    data = yaml.safe_load(docker_file.read_text())
    assert "services" in data


def test_docker_compose_structure_validity(temp_dir: Path, simple_schema: Path):
    """Test that docker-compose.yaml has valid structure for docker-compose CLI."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    assert result.exit_code == 0

    docker_file = temp_dir / "docker-compose.yaml"
    data = yaml.safe_load(docker_file.read_text())

    # Verify top-level keys are valid
    valid_top_level_keys = ["version", "services", "networks", "volumes"]
    for key in data.keys():
        assert key in valid_top_level_keys, \
            f"Invalid top-level key '{key}' in docker-compose.yaml"

    # Verify services structure
    if "services" in data:
        services = data["services"]
        assert isinstance(services, dict), "services should be a dictionary"

        for service_name, service_config in services.items():
            assert isinstance(service_config, dict), \
                f"Service '{service_name}' config should be a dictionary"


def test_docker_compose_size_reasonable(temp_dir: Path, simple_schema: Path):
    """Test that generated docker-compose.yaml has reasonable size."""
    result = runner.invoke(app, ["generate", str(simple_schema), "--target", "docker"])

    assert result.exit_code == 0

    docker_file = temp_dir / "docker-compose.yaml"
    file_size = docker_file.stat().st_size

    # File should be between 100 bytes and 10KB for a simple schema
    assert file_size > 100, "docker-compose.yaml seems too small"
    assert file_size < 10 * 1024, "docker-compose.yaml seems too large for simple schema"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
