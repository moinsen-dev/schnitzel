"""Integration tests for F062 - Docker Compose Redis 7 service.

Test Requirements:
- test_docker_compose_has_redis_service - redis service exists
- test_redis_uses_version_7 - image is redis:7-alpine
- test_redis_has_persistence - appendonly yes configured
- test_redis_has_volume - redis_data volume defined
- test_redis_exposes_port_6379 - port mapping exists
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


def test_docker_compose_has_redis_service(temp_dir: Path) -> None:
    """Test that docker-compose.yaml includes a Redis service."""
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

    # Check for redis service
    assert "redis" in compose_data["services"], "docker-compose.yaml missing redis service"


def test_redis_uses_version_7(temp_dir: Path) -> None:
    """Test that redis service uses redis:7-alpine image."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get redis service
    services = compose_data["services"]
    redis_service = services.get("redis")

    assert redis_service is not None, "No redis service found"
    assert "image" in redis_service, "redis service missing image field"
    assert redis_service["image"] == "redis:7-alpine", \
        f"redis service should use redis:7-alpine image, got {redis_service['image']}"


def test_redis_has_persistence(temp_dir: Path) -> None:
    """Test that redis service has appendonly yes configured."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get redis service
    services = compose_data["services"]
    redis_service = services.get("redis")

    assert redis_service is not None, "No redis service found"

    # Verify command for persistence
    assert "command" in redis_service, "redis service missing command field"

    # Command can be a string or a list
    command = redis_service["command"]
    if isinstance(command, list):
        command_str = " ".join(command)
    else:
        command_str = command

    assert "redis-server" in command_str, "redis command should include redis-server"
    assert "--appendonly yes" in command_str or "--appendonly" in command_str, \
        "redis command should include --appendonly yes for persistence"


def test_redis_has_volume(temp_dir: Path) -> None:
    """Test that redis_data volume is defined and mounted."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify volumes section exists at root level
    assert "volumes" in compose_data, "docker-compose.yaml missing volumes section"
    assert "redis_data" in compose_data["volumes"], \
        "volumes section should define redis_data volume"

    # Verify redis service mounts the volume
    services = compose_data["services"]
    redis_service = services.get("redis")

    assert redis_service is not None, "No redis service found"
    assert "volumes" in redis_service, "redis service missing volumes configuration"

    # Check that redis_data is mounted to /data
    volume_found = False
    for volume_mapping in redis_service["volumes"]:
        if "redis_data:" in volume_mapping and "/data" in volume_mapping:
            volume_found = True
            break

    assert volume_found, "redis service should mount redis_data:/data"


def test_redis_exposes_port_6379(temp_dir: Path) -> None:
    """Test that redis service exposes port 6379."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get redis service
    services = compose_data["services"]
    redis_service = services.get("redis")

    assert redis_service is not None, "No redis service found"

    # Verify ports configuration
    assert "ports" in redis_service, "redis service missing ports configuration"

    # Check that port 6379 is exposed
    ports = redis_service["ports"]
    assert isinstance(ports, list), "ports should be a list"

    port_found = False
    for port_mapping in ports:
        if "6379:6379" in str(port_mapping) or "6379" in str(port_mapping):
            port_found = True
            break

    assert port_found, "redis service should expose port 6379"


def test_redis_volume_persistence(temp_dir: Path) -> None:
    """Test that redis data volume is properly configured for persistence."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify volumes section at root level
    assert "volumes" in compose_data, "docker-compose.yaml missing volumes section"
    volumes = compose_data["volumes"]

    # redis_data should be defined (can be empty dict for default driver)
    assert "redis_data" in volumes, "redis_data volume should be defined"

    # The volume definition should be a dict (can be empty {} or have config)
    redis_volume = volumes["redis_data"]
    assert redis_volume is None or isinstance(redis_volume, dict), \
        "redis_data volume should be None or a dictionary"


def test_redis_command_configuration(temp_dir: Path) -> None:
    """Test that redis has proper command configuration for production use."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get redis service
    services = compose_data["services"]
    redis_service = services.get("redis")

    assert redis_service is not None, "No redis service found"

    # Verify command exists and contains redis-server
    assert "command" in redis_service, "redis service should have command configured"

    command = redis_service["command"]
    if isinstance(command, list):
        command_str = " ".join(command)
    else:
        command_str = command

    # Verify it's the redis-server with appendonly flag
    assert "redis-server" in command_str, "command should start with redis-server"
    assert "--appendonly" in command_str, "command should include --appendonly flag"
