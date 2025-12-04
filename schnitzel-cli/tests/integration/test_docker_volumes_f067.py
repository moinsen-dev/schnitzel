"""Integration tests for F067 - Docker Compose volume mounts for data persistence.

Test Requirements:
- test_volumes_section_exists - volumes section defined
- test_postgres_volume_defined - postgres_data in volumes
- test_redis_volume_defined - redis_data in volumes
- test_postgres_mount_path - correct mount path
- test_redis_mount_path - correct mount path
- test_volumes_are_named - using named volumes not bind mounts
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


def test_volumes_section_exists(temp_dir: Path) -> None:
    """Test that docker-compose.yaml includes a volumes section at root level."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, file_size = generator.generate_to_file(temp_dir)

    assert compose_file.exists(), "docker-compose.yaml not created"
    assert file_size > 0, "docker-compose.yaml should not be empty"

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify volumes section exists at root level
    assert "volumes" in compose_data, "docker-compose.yaml missing volumes section"
    assert isinstance(compose_data["volumes"], dict), "volumes section should be a dictionary"


def test_postgres_volume_defined(temp_dir: Path) -> None:
    """Test that postgres_data volume is defined in the volumes section."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify volumes section exists
    assert "volumes" in compose_data, "docker-compose.yaml missing volumes section"

    # Verify postgres_data is defined
    volumes = compose_data["volumes"]
    assert "postgres_data" in volumes, "postgres_data volume should be defined in volumes section"

    # The volume definition should be None or a dict (empty {} means default driver)
    postgres_volume = volumes["postgres_data"]
    assert postgres_volume is None or isinstance(postgres_volume, dict), \
        "postgres_data volume should be None or a dictionary"


def test_redis_volume_defined(temp_dir: Path) -> None:
    """Test that redis_data volume is defined in the volumes section."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify volumes section exists
    assert "volumes" in compose_data, "docker-compose.yaml missing volumes section"

    # Verify redis_data is defined
    volumes = compose_data["volumes"]
    assert "redis_data" in volumes, "redis_data volume should be defined in volumes section"

    # The volume definition should be None or a dict
    redis_volume = volumes["redis_data"]
    assert redis_volume is None or isinstance(redis_volume, dict), \
        "redis_data volume should be None or a dictionary"


def test_postgres_mount_path(temp_dir: Path) -> None:
    """Test that postgres service mounts postgres_data to correct path /var/lib/postgresql/data."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get postgres/db service
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"
    assert "volumes" in postgres_service, "postgres service missing volumes configuration"

    # Check that postgres_data is mounted to /var/lib/postgresql/data
    volumes = postgres_service["volumes"]
    assert isinstance(volumes, list), "service volumes should be a list"

    # Find the postgres_data mount
    postgres_data_mount = None
    for volume_mapping in volumes:
        if "postgres_data:" in volume_mapping:
            postgres_data_mount = volume_mapping
            break

    assert postgres_data_mount is not None, "postgres service should mount postgres_data volume"
    assert "postgres_data:/var/lib/postgresql/data" in postgres_data_mount, \
        "postgres_data should be mounted to /var/lib/postgresql/data"


def test_redis_mount_path(temp_dir: Path) -> None:
    """Test that redis service mounts redis_data to correct path /data."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get redis service
    services = compose_data["services"]
    assert "redis" in services, "redis service should exist"

    redis_service = services["redis"]
    assert "volumes" in redis_service, "redis service missing volumes configuration"

    # Check that redis_data is mounted to /data
    volumes = redis_service["volumes"]
    assert isinstance(volumes, list), "service volumes should be a list"

    # Find the redis_data mount
    redis_data_mount = None
    for volume_mapping in volumes:
        if "redis_data:" in volume_mapping:
            redis_data_mount = volume_mapping
            break

    assert redis_data_mount is not None, "redis service should mount redis_data volume"
    assert "redis_data:/data" in redis_data_mount, \
        "redis_data should be mounted to /data"


def test_volumes_are_named(temp_dir: Path) -> None:
    """Test that services use named volumes (not bind mounts) for data persistence."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get services
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")
    redis_service = services.get("redis")

    # Check postgres volumes
    assert postgres_service is not None, "postgres/db service should exist"
    if "volumes" in postgres_service:
        for volume in postgres_service["volumes"]:
            if "postgres_data" in volume:
                # Named volumes start with volume name followed by colon
                assert volume.startswith("postgres_data:"), \
                    "postgres should use named volume postgres_data:, not a bind mount"
                # Should not contain absolute paths (which would indicate bind mount)
                assert not volume.startswith("/"), \
                    "postgres volume should not be a bind mount (starting with /)"
                assert not volume.startswith("./"), \
                    "postgres volume should not be a relative bind mount (starting with ./)"

    # Check redis volumes
    assert redis_service is not None, "redis service should exist"
    if "volumes" in redis_service:
        for volume in redis_service["volumes"]:
            if "redis_data" in volume:
                # Named volumes start with volume name followed by colon
                assert volume.startswith("redis_data:"), \
                    "redis should use named volume redis_data:, not a bind mount"
                # Should not contain absolute paths
                assert not volume.startswith("/"), \
                    "redis volume should not be a bind mount (starting with /)"
                assert not volume.startswith("./"), \
                    "redis volume should not be a relative bind mount (starting with ./)"


def test_all_stateful_services_have_volumes(temp_dir: Path) -> None:
    """Test that all stateful services (postgres, redis) have volume mounts."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get services
    services = compose_data["services"]

    # PostgreSQL is stateful - should have volumes
    postgres_service = services.get("postgres") or services.get("db")
    assert postgres_service is not None, "postgres/db service should exist"
    assert "volumes" in postgres_service, "postgres service should have volumes for data persistence"

    postgres_volumes = postgres_service["volumes"]
    assert any("postgres_data" in vol for vol in postgres_volumes), \
        "postgres service should mount postgres_data volume"

    # Redis is stateful - should have volumes
    redis_service = services.get("redis")
    assert redis_service is not None, "redis service should exist"
    assert "volumes" in redis_service, "redis service should have volumes for data persistence"

    redis_volumes = redis_service["volumes"]
    assert any("redis_data" in vol for vol in redis_volumes), \
        "redis service should mount redis_data volume"


def test_volume_persistence_configuration(temp_dir: Path) -> None:
    """Test that volumes are properly configured for data persistence across restarts."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify root-level volumes section exists
    assert "volumes" in compose_data, "docker-compose.yaml must have volumes section for persistence"

    volumes = compose_data["volumes"]

    # Both postgres_data and redis_data should be defined
    assert "postgres_data" in volumes, "postgres_data volume must be defined for PostgreSQL persistence"
    assert "redis_data" in volumes, "redis_data volume must be defined for Redis persistence"

    # Get services
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")
    redis_service = services.get("redis")

    # Verify postgres mounts the data directory
    postgres_volumes = postgres_service.get("volumes", [])
    postgres_data_mounted = any(
        "postgres_data:" in vol and "/var/lib/postgresql/data" in vol
        for vol in postgres_volumes
    )
    assert postgres_data_mounted, \
        "postgres must mount postgres_data to /var/lib/postgresql/data for data persistence"

    # Verify redis mounts the data directory
    redis_volumes = redis_service.get("volumes", [])
    redis_data_mounted = any(
        "redis_data:" in vol and "/data" in vol
        for vol in redis_volumes
    )
    assert redis_data_mounted, \
        "redis must mount redis_data to /data for data persistence"


def test_redis_appendonly_persistence(temp_dir: Path) -> None:
    """Test that redis is configured with appendonly mode for data persistence."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get redis service
    services = compose_data["services"]
    redis_service = services.get("redis")

    assert redis_service is not None, "redis service should exist"

    # Verify redis command includes appendonly mode
    if "command" in redis_service:
        command = redis_service["command"]
        assert "appendonly yes" in command, \
            "redis should be configured with appendonly mode for data persistence"


def test_volume_mount_paths_are_standard(temp_dir: Path) -> None:
    """Test that volume mount paths follow standard conventions for each service."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # PostgreSQL standard data directory
    postgres_service = services.get("postgres") or services.get("db")
    if postgres_service and "volumes" in postgres_service:
        for volume in postgres_service["volumes"]:
            if "postgres_data:" in volume:
                assert "/var/lib/postgresql/data" in volume, \
                    "PostgreSQL should use standard data directory /var/lib/postgresql/data"

    # Redis standard data directory
    redis_service = services.get("redis")
    if redis_service and "volumes" in redis_service:
        for volume in redis_service["volumes"]:
            if "redis_data:" in volume:
                assert "/data" in volume, \
                    "Redis should use standard data directory /data"


def test_volumes_section_format(temp_dir: Path) -> None:
    """Test that volumes section has correct format for Docker Compose."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify volumes section structure
    assert "volumes" in compose_data, "docker-compose.yaml must have volumes section"

    volumes = compose_data["volumes"]
    assert isinstance(volumes, dict), "volumes section must be a dictionary"

    # Check each volume is properly defined
    for volume_name in ["postgres_data", "redis_data"]:
        assert volume_name in volumes, f"{volume_name} should be defined in volumes section"

        # Volume can be None (default) or a dict with configuration
        volume_config = volumes[volume_name]
        assert volume_config is None or isinstance(volume_config, dict), \
            f"{volume_name} must be None or a dictionary configuration"


def test_data_persistence_across_restarts(temp_dir: Path) -> None:
    """Test that configuration ensures data persists across container restarts.

    This test verifies the declarative configuration is correct. Actual persistence
    behavior would be tested in runtime integration tests.
    """
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Requirements for data persistence:
    # 1. Named volumes must be defined at root level
    assert "volumes" in compose_data, "Named volumes must be defined for persistence"
    assert "postgres_data" in compose_data["volumes"], "postgres_data volume required"
    assert "redis_data" in compose_data["volumes"], "redis_data volume required"

    # 2. Services must mount these volumes to correct data directories
    services = compose_data["services"]

    postgres_service = services.get("postgres") or services.get("db")
    assert "volumes" in postgres_service, "postgres must have volumes configuration"
    postgres_volumes_str = str(postgres_service["volumes"])
    assert "postgres_data:/var/lib/postgresql/data" in postgres_volumes_str, \
        "postgres must mount postgres_data to data directory"

    redis_service = services.get("redis")
    assert "volumes" in redis_service, "redis must have volumes configuration"
    redis_volumes_str = str(redis_service["volumes"])
    assert "redis_data:/data" in redis_volumes_str, \
        "redis must mount redis_data to data directory"

    # 3. Redis should use appendonly for durability
    if "command" in redis_service:
        assert "appendonly yes" in redis_service["command"], \
            "redis should use appendonly mode for data durability"
