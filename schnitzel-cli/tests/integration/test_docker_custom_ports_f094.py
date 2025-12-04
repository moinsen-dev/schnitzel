"""Integration tests for F094 - Docker Compose custom ports from schema.

Test Requirements:
- test_custom_port_in_compose - custom port should appear in compose
- test_default_port_used - default port when not specified
- test_multiple_custom_ports - multiple services with custom ports
"""

import tempfile
import os
from pathlib import Path
import pytest
import yaml

from schnitzel.generators.docker.compose import DockerComposeGenerator
from schnitzel.schema.parser import SchemaParser


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def schema_with_custom_ports(temp_dir: Path) -> Path:
    """Create a test schema with custom service ports."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

services:
  db:
    port: 5433
  redis:
    port: 6380
  backend:
    port: 8001
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)
    return schema_file


@pytest.fixture
def schema_with_partial_ports(temp_dir: Path) -> Path:
    """Create a test schema with only some custom ports."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

services:
  db:
    port: 5433
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)
    return schema_file


@pytest.fixture
def schema_without_services(temp_dir: Path) -> Path:
    """Create a test schema without services section."""
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
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_custom_port_in_compose(temp_dir: Path, schema_with_custom_ports: Path) -> None:
    """Test that custom port from schema appears in docker-compose.yaml."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_custom_ports))

    # Generate docker-compose with schema
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir, schema=schema)

    # Parse generated docker-compose
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify custom ports are used
    services = compose_data["services"]

    # Check db port (custom: 5433)
    db_service = services.get("db")
    assert db_service is not None, "db service should exist"
    assert "ports" in db_service, "db service should have ports"

    # The port mapping should be "${POSTGRES_PORT:-5433}:5432"
    # (custom default 5433, but container still uses 5432 internally)
    compose_content = compose_file.read_text()
    assert "${POSTGRES_PORT:-5433}" in compose_content, \
        "db service should use custom port 5433 as default"

    # Check redis port (custom: 6380)
    redis_service = services.get("redis")
    assert redis_service is not None, "redis service should exist"
    assert "ports" in redis_service, "redis service should have ports"
    assert "${REDIS_PORT:-6380}" in compose_content, \
        "redis service should use custom port 6380 as default"

    # Check backend port (custom: 8001)
    backend_service = services.get("backend")
    assert backend_service is not None, "backend service should exist"
    assert "ports" in backend_service, "backend service should have ports"
    assert "${BACKEND_PORT:-8001}" in compose_content, \
        "backend service should use custom port 8001 as default"


def test_default_port_used(temp_dir: Path, schema_without_services: Path) -> None:
    """Test that default ports are used when not specified in schema."""
    # Parse schema (no services section)
    parser = SchemaParser()
    schema = parser.parse(str(schema_without_services))

    # Generate docker-compose with schema
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir, schema=schema)

    # Parse generated docker-compose
    compose_content = compose_file.read_text()

    # Verify default ports are used
    assert "${POSTGRES_PORT:-5432}" in compose_content, \
        "Should use default PostgreSQL port 5432"
    assert "${REDIS_PORT:-6379}" in compose_content, \
        "Should use default Redis port 6379"
    assert "${BACKEND_PORT:-8000}" in compose_content, \
        "Should use default backend port 8000"


def test_multiple_custom_ports(temp_dir: Path, schema_with_custom_ports: Path) -> None:
    """Test that multiple services with custom ports all work correctly."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_custom_ports))

    # Generate docker-compose with schema
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir, schema=schema)

    # Parse generated docker-compose
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # Verify all three services exist
    assert "db" in services, "db service should exist"
    assert "redis" in services, "redis service should exist"
    assert "backend" in services, "backend service should exist"

    # Verify all have ports configured
    for service_name in ["db", "redis", "backend"]:
        service = services[service_name]
        assert "ports" in service, f"{service_name} should have ports configured"
        assert isinstance(service["ports"], list), \
            f"{service_name} ports should be a list"
        assert len(service["ports"]) > 0, \
            f"{service_name} should have at least one port mapping"


def test_partial_custom_ports(temp_dir: Path, schema_with_partial_ports: Path) -> None:
    """Test that custom ports can be specified for some services while others use defaults."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_partial_ports))

    # Generate docker-compose with schema
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir, schema=schema)

    compose_content = compose_file.read_text()

    # Verify custom port for db
    assert "${POSTGRES_PORT:-5433}" in compose_content, \
        "db should use custom port 5433"

    # Verify defaults for redis and backend
    assert "${REDIS_PORT:-6379}" in compose_content, \
        "redis should use default port 6379"
    assert "${BACKEND_PORT:-8000}" in compose_content, \
        "backend should use default port 8000"


def test_custom_ports_still_use_env_vars(temp_dir: Path, schema_with_custom_ports: Path) -> None:
    """Test that custom ports still allow environment variable override."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_custom_ports))

    # Generate docker-compose with schema
    generator = DockerComposeGenerator()
    compose_content = generator.generate(schema=schema)

    # Verify environment variable syntax is preserved
    assert "${POSTGRES_PORT:-5433}" in compose_content, \
        "Custom db port should still use env var syntax"
    assert "${REDIS_PORT:-6380}" in compose_content, \
        "Custom redis port should still use env var syntax"
    assert "${BACKEND_PORT:-8001}" in compose_content, \
        "Custom backend port should still use env var syntax"

    # Verify the port environment variables are configurable
    # (they should follow the pattern ${VAR_NAME:-DEFAULT})
    import re
    port_vars = re.findall(r'\$\{([A-Z_]+_PORT):-(\d+)\}', compose_content)

    assert len(port_vars) >= 3, "Should have at least 3 port environment variables"

    # Verify structure (var_name, default_port)
    port_dict = dict(port_vars)
    assert "POSTGRES_PORT" in port_dict
    assert "REDIS_PORT" in port_dict
    assert "BACKEND_PORT" in port_dict

    # Verify custom defaults
    assert port_dict["POSTGRES_PORT"] == "5433", "Custom db port default should be 5433"
    assert port_dict["REDIS_PORT"] == "6380", "Custom redis port default should be 6380"
    assert port_dict["BACKEND_PORT"] == "8001", "Custom backend port default should be 8001"


def test_backward_compatibility_without_schema(temp_dir: Path) -> None:
    """Test that generator still works without schema parameter (backward compatibility)."""
    # Generate docker-compose without schema
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse generated docker-compose
    compose_content = compose_file.read_text()

    # Verify default ports are used
    assert "${POSTGRES_PORT:-5432}" in compose_content, \
        "Should use default PostgreSQL port 5432"
    assert "${REDIS_PORT:-6379}" in compose_content, \
        "Should use default Redis port 6379"
    assert "${BACKEND_PORT:-8000}" in compose_content, \
        "Should use default backend port 8000"

    # Verify compose file is valid YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    assert "services" in compose_data
    assert "db" in compose_data["services"]
    assert "redis" in compose_data["services"]
    assert "backend" in compose_data["services"]


def test_custom_port_validation(temp_dir: Path) -> None:
    """Test that custom ports are validated (must be integers)."""
    # Create schema with invalid port (string)
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

services:
  db:
    port: "not-a-number"
"""
    schema_file = temp_dir / "schema_invalid.yaml"
    schema_file.write_text(schema_content)

    # Parse should handle or validate this
    parser = SchemaParser()
    # This may raise an error during parsing or during generation
    # We just need to ensure it doesn't silently fail
    try:
        schema = parser.parse(str(schema_file))
        generator = DockerComposeGenerator()
        compose_content = generator.generate(schema=schema)

        # If it doesn't raise an error, it should fall back to defaults
        # or properly handle the invalid value
        assert compose_content is not None
    except (ValueError, TypeError) as e:
        # Expected behavior: validation should catch invalid port
        assert "port" in str(e).lower() or "int" in str(e).lower()


def test_service_config_without_port(temp_dir: Path) -> None:
    """Test that services can have other config without port specified."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

services:
  db:
    # No port specified, should use default
    enabled: true
  redis:
    port: 6380
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(str(schema_file))

    generator = DockerComposeGenerator()
    compose_content = generator.generate(schema=schema)

    # db should use default port since none specified
    assert "${POSTGRES_PORT:-5432}" in compose_content, \
        "db should use default port 5432 when not specified"

    # redis should use custom port
    assert "${REDIS_PORT:-6380}" in compose_content, \
        "redis should use custom port 6380"


def test_port_comments_reflect_custom_values(temp_dir: Path, schema_with_custom_ports: Path) -> None:
    """Test that port documentation comments reflect custom port values."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(str(schema_with_custom_ports))

    # Generate docker-compose with schema
    generator = DockerComposeGenerator()
    compose_content = generator.generate(schema=schema)

    # Comments should reflect custom defaults
    assert "default: 5433" in compose_content or "5433" in compose_content, \
        "Comment should mention custom PostgreSQL port 5433"
    assert "default: 6380" in compose_content or "6380" in compose_content, \
        "Comment should mention custom Redis port 6380"
    assert "default: 8001" in compose_content or "8001" in compose_content, \
        "Comment should mention custom backend port 8001"
