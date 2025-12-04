"""Integration tests for F061 - Docker Compose pgvector extension support.

Test Requirements:
- test_docker_compose_uses_pgvector_image - image is pgvector/pgvector:pg16
- test_docker_compose_has_init_script - init script volume mounted
- test_pgvector_extension_mentioned - pgvector mentioned in config
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


def test_docker_compose_uses_pgvector_image(temp_dir: Path) -> None:
    """Test that docker-compose.yaml uses pgvector/pgvector:pg16 image."""
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

    # Get postgres/db service
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"
    assert "image" in postgres_service, "postgres service missing image field"

    # Verify pgvector image is used
    assert postgres_service["image"] == "pgvector/pgvector:pg16", \
        f"postgres service should use pgvector/pgvector:pg16 image, got {postgres_service['image']}"


def test_docker_compose_has_init_script(temp_dir: Path) -> None:
    """Test that docker-compose.yaml has init script volume mounted."""
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

    # Check for init script volume mount
    volumes = postgres_service["volumes"]
    assert isinstance(volumes, list), "volumes should be a list"

    # Look for init.sql mount in docker-entrypoint-initdb.d
    init_script_found = False
    for volume_mapping in volumes:
        volume_str = str(volume_mapping)
        if "init.sql" in volume_str and "docker-entrypoint-initdb.d" in volume_str:
            init_script_found = True
            break

    assert init_script_found, \
        "postgres service should mount init.sql to /docker-entrypoint-initdb.d/init.sql"


def test_pgvector_extension_mentioned(temp_dir: Path) -> None:
    """Test that pgvector is mentioned in the docker-compose configuration."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Read the file content
    with open(compose_file, "r") as f:
        compose_content = f.read()

    # Verify pgvector is mentioned (in image name)
    assert "pgvector" in compose_content, \
        "docker-compose.yaml should mention pgvector (in image name or comments)"


def test_init_script_volume_path(temp_dir: Path) -> None:
    """Test that init script volume uses correct source path."""
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

    volumes = postgres_service["volumes"]

    # Find the init script volume
    init_script_volume = None
    for volume_mapping in volumes:
        if "init.sql" in str(volume_mapping):
            init_script_volume = volume_mapping
            break

    assert init_script_volume is not None, "init.sql volume mount not found"

    # Verify the path structure
    assert "./docker/postgres/init.sql" in init_script_volume, \
        "init script should be mounted from ./docker/postgres/init.sql"
    assert "/docker-entrypoint-initdb.d/init.sql" in init_script_volume, \
        "init script should be mounted to /docker-entrypoint-initdb.d/init.sql"


def test_pgvector_image_version(temp_dir: Path) -> None:
    """Test that pgvector image uses PostgreSQL 16."""
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

    image = postgres_service["image"]

    # Verify it uses pg16
    assert "pg16" in image, \
        f"pgvector image should specify PostgreSQL 16 (pg16), got {image}"


def test_postgres_data_volume_still_exists(temp_dir: Path) -> None:
    """Test that the postgres_data volume is still configured alongside init script."""
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

    volumes = postgres_service["volumes"]

    # Check that postgres_data volume still exists
    data_volume_found = False
    for volume_mapping in volumes:
        if "postgres_data:" in str(volume_mapping) and "/var/lib/postgresql/data" in str(volume_mapping):
            data_volume_found = True
            break

    assert data_volume_found, \
        "postgres service should still have postgres_data:/var/lib/postgresql/data volume"
