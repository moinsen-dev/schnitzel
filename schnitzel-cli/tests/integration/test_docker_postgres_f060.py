"""Integration tests for F060 - Docker Compose PostgreSQL 16 service.

Test Requirements:
- test_docker_compose_has_postgres_service - postgres service exists
- test_postgres_uses_version_16 - image is postgres:16
- test_postgres_has_environment_vars - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- test_postgres_has_volume - postgres_data volume defined
- test_postgres_has_healthcheck - healthcheck configured
- test_postgres_exposes_port_5432 - port mapping exists
"""

import tempfile
import os
from pathlib import Path
import pytest
import yaml

from schnitzel.generators.docker.compose import DockerComposeGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_docker_compose_has_postgres_service(temp_dir: Path) -> None:
    """Test that docker-compose.yaml includes a PostgreSQL database service."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, file_size = generator.generate_to_file(temp_dir)

    assert compose_file.exists(), "docker-compose.yaml not created"
    assert file_size > 0, "docker-compose.yaml should not be empty"

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify services section exists
    assert "services" in compose_data, "docker-compose.yaml missing services section"

    # Check for postgres or db service (both are acceptable)
    has_postgres_service = "postgres" in compose_data["services"] or "db" in compose_data["services"]
    assert has_postgres_service, "docker-compose.yaml missing postgres/db service"


def test_postgres_uses_version_16(temp_dir: Path) -> None:
    """Test that postgres service uses postgres:16 or pgvector:pg16 image."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get postgres service (could be named "postgres" or "db")
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"
    assert "image" in postgres_service, "postgres service missing image field"

    # Accept either postgres:16 or pgvector/pgvector:pg16 (which is based on postgres:16)
    image = postgres_service["image"]
    valid_images = ["postgres:16", "pgvector/pgvector:pg16"]
    assert image in valid_images, \
        f"postgres service should use postgres:16 or pgvector/pgvector:pg16 image, got {image}"


def test_postgres_has_environment_vars(temp_dir: Path) -> None:
    """Test that postgres service has POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get postgres service
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"

    # Verify environment variables
    assert "environment" in postgres_service, "postgres service missing environment variables"
    env = postgres_service["environment"]

    # Check required environment variables exist
    assert "POSTGRES_USER" in env, "postgres service missing POSTGRES_USER"
    assert "POSTGRES_PASSWORD" in env, "postgres service missing POSTGRES_PASSWORD"
    assert "POSTGRES_DB" in env, "postgres service missing POSTGRES_DB"

    # Verify they have values (not empty)
    assert env["POSTGRES_USER"], "POSTGRES_USER should have a value"
    assert env["POSTGRES_PASSWORD"], "POSTGRES_PASSWORD should have a value"
    assert env["POSTGRES_DB"], "POSTGRES_DB should have a value"


def test_postgres_has_volume(temp_dir: Path) -> None:
    """Test that postgres_data volume is defined and mounted."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify volumes section exists at root level
    assert "volumes" in compose_data, "docker-compose.yaml missing volumes section"
    assert "postgres_data" in compose_data["volumes"], \
        "volumes section should define postgres_data volume"

    # Verify postgres service mounts the volume
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"
    assert "volumes" in postgres_service, "postgres service missing volumes configuration"

    # Check that postgres_data is mounted to /var/lib/postgresql/data
    volume_found = False
    for volume_mapping in postgres_service["volumes"]:
        if "postgres_data:" in volume_mapping and "/var/lib/postgresql/data" in volume_mapping:
            volume_found = True
            break

    assert volume_found, "postgres service should mount postgres_data:/var/lib/postgresql/data"


def test_postgres_has_healthcheck(temp_dir: Path) -> None:
    """Test that postgres service has healthcheck configured."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get postgres service
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"

    # Verify healthcheck exists
    assert "healthcheck" in postgres_service, "postgres service missing healthcheck configuration"

    healthcheck = postgres_service["healthcheck"]

    # Verify healthcheck has required fields
    assert "test" in healthcheck, "healthcheck missing test command"
    assert "interval" in healthcheck, "healthcheck missing interval"
    assert "timeout" in healthcheck, "healthcheck missing timeout"
    assert "retries" in healthcheck, "healthcheck missing retries"

    # Verify healthcheck uses pg_isready
    test_command = healthcheck["test"]
    assert isinstance(test_command, list), "healthcheck test should be a list"
    assert "pg_isready" in " ".join(test_command), "healthcheck should use pg_isready command"


def test_postgres_exposes_port_5432(temp_dir: Path) -> None:
    """Test that postgres service exposes port 5432."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get postgres service
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"

    # Verify ports configuration
    assert "ports" in postgres_service, "postgres service missing ports configuration"

    # Check that port 5432 is exposed
    ports = postgres_service["ports"]
    assert isinstance(ports, list), "ports should be a list"

    port_found = False
    for port_mapping in ports:
        if "5432:5432" in str(port_mapping) or "5432" in str(port_mapping):
            port_found = True
            break

    assert port_found, "postgres service should expose port 5432"


def test_postgres_healthcheck_details(temp_dir: Path) -> None:
    """Test detailed healthcheck configuration meets requirements."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get postgres service
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"

    healthcheck = postgres_service["healthcheck"]

    # Verify healthcheck test format (should be CMD-SHELL with pg_isready)
    assert healthcheck["test"][0] == "CMD-SHELL", "healthcheck should use CMD-SHELL"
    assert "pg_isready" in healthcheck["test"][1], "healthcheck should use pg_isready"

    # Verify timing values are reasonable (allowing some flexibility)
    interval = healthcheck["interval"]
    timeout = healthcheck["timeout"]
    retries = healthcheck["retries"]

    # Parse interval (e.g., "5s" or "10s")
    assert isinstance(interval, str) and interval.endswith("s"), "interval should be in seconds format"
    interval_value = int(interval[:-1])
    assert 5 <= interval_value <= 30, "healthcheck interval should be between 5-30 seconds"

    # Parse timeout
    assert isinstance(timeout, str) and timeout.endswith("s"), "timeout should be in seconds format"
    timeout_value = int(timeout[:-1])
    assert 1 <= timeout_value <= 10, "healthcheck timeout should be between 1-10 seconds"

    # Check retries
    assert isinstance(retries, int), "retries should be an integer"
    assert 3 <= retries <= 10, "healthcheck retries should be between 3-10"


def test_postgres_volume_persistence(temp_dir: Path) -> None:
    """Test that postgres data volume is properly configured for persistence."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify volumes section at root level
    assert "volumes" in compose_data, "docker-compose.yaml missing volumes section"
    volumes = compose_data["volumes"]

    # postgres_data should be defined (can be empty dict for default driver)
    assert "postgres_data" in volumes, "postgres_data volume should be defined"

    # The volume definition should be a dict (can be empty {} or have config)
    postgres_volume = volumes["postgres_data"]
    assert postgres_volume is None or isinstance(postgres_volume, dict), \
        "postgres_data volume should be None or a dictionary"
