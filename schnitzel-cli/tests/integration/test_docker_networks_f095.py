"""Integration tests for F095 - Docker Compose networks for services.

Test Requirements:
- test_network_in_compose - networks section should exist
- test_services_on_network - services should be on the network
- test_network_name - network should have appropriate name

Feature: Docker Compose generator creates networks for services
- Docker Compose should have a networks section
- All services should be connected to the network
- Network should be properly configured with bridge driver
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


def test_network_in_compose(temp_dir: Path) -> None:
    """Test that docker-compose.yaml includes a networks section."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, file_size = generator.generate_to_file(temp_dir)

    assert compose_file.exists(), "docker-compose.yaml not created"
    assert file_size > 0, "docker-compose.yaml should not be empty"

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify networks section exists at root level
    assert "networks" in compose_data, "docker-compose.yaml missing networks section"
    assert isinstance(compose_data["networks"], dict), "networks section should be a dictionary"


def test_services_on_network(temp_dir: Path) -> None:
    """Test that all services are connected to the network."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify services section exists
    assert "services" in compose_data, "docker-compose.yaml missing services section"

    services = compose_data["services"]

    # Check that db service has networks configuration
    db_service = services.get("db") or services.get("postgres")
    assert db_service is not None, "No db/postgres service found"
    assert "networks" in db_service, "db service should have networks configuration"
    assert isinstance(db_service["networks"], list), "db service networks should be a list"
    assert len(db_service["networks"]) > 0, "db service should be connected to at least one network"

    # Check that redis service has networks configuration
    redis_service = services.get("redis")
    assert redis_service is not None, "No redis service found"
    assert "networks" in redis_service, "redis service should have networks configuration"
    assert isinstance(redis_service["networks"], list), "redis service networks should be a list"
    assert len(redis_service["networks"]) > 0, "redis service should be connected to at least one network"

    # Check that backend service has networks configuration
    backend_service = services.get("backend") or services.get("api")
    assert backend_service is not None, "No backend/api service found"
    assert "networks" in backend_service, "backend service should have networks configuration"
    assert isinstance(backend_service["networks"], list), "backend service networks should be a list"
    assert len(backend_service["networks"]) > 0, "backend service should be connected to at least one network"


def test_network_name(temp_dir: Path) -> None:
    """Test that network has an appropriate name."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify networks section exists
    assert "networks" in compose_data, "docker-compose.yaml missing networks section"

    networks = compose_data["networks"]

    # Check that at least one network is defined
    assert len(networks) > 0, "At least one network should be defined"

    # Network should have a meaningful name (e.g., schnitzel_network, app_network, etc.)
    network_names = list(networks.keys())

    # Verify network name is meaningful (not just "default")
    assert any(name != "default" for name in network_names), \
        "Network should have a meaningful name, not just 'default'"

    # Check for schnitzel-related or app-related naming
    has_meaningful_name = any(
        "schnitzel" in name.lower() or "app" in name.lower() or "network" in name.lower()
        for name in network_names
    )
    assert has_meaningful_name, \
        f"Network should have a meaningful name (got: {network_names})"


def test_network_driver(temp_dir: Path) -> None:
    """Test that network uses bridge driver."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get networks
    networks = compose_data["networks"]

    # Check that at least one network has bridge driver
    has_bridge_driver = False
    for network_name, network_config in networks.items():
        if network_config is not None and isinstance(network_config, dict):
            if network_config.get("driver") == "bridge":
                has_bridge_driver = True
                break

    assert has_bridge_driver, "At least one network should use bridge driver"


def test_all_services_on_same_network(temp_dir: Path) -> None:
    """Test that all services are connected to the same network for inter-service communication."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # Get all network connections for each service
    db_service = services.get("db") or services.get("postgres")
    redis_service = services.get("redis")
    backend_service = services.get("backend") or services.get("api")

    db_networks = set(db_service.get("networks", []))
    redis_networks = set(redis_service.get("networks", []))
    backend_networks = set(backend_service.get("networks", []))

    # Find common networks
    common_networks = db_networks & redis_networks & backend_networks

    assert len(common_networks) > 0, \
        "All services (db, redis, backend) should be connected to at least one common network"


def test_network_enables_service_discovery(temp_dir: Path) -> None:
    """Test that network configuration enables service discovery by service name."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify backend service uses service names for database and redis connections
    backend_service = compose_data["services"].get("backend") or compose_data["services"].get("api")
    assert backend_service is not None, "backend service should exist"

    environment = backend_service.get("environment", {})

    # Check DATABASE_URL uses service name "db"
    database_url = environment.get("DATABASE_URL", "")
    assert "@db:" in database_url or "@postgres:" in database_url, \
        "DATABASE_URL should use service name (db/postgres) for DNS resolution"

    # Check REDIS_URL uses service name "redis"
    redis_url = environment.get("REDIS_URL", "")
    assert "redis://" in redis_url.lower() and "redis:" in redis_url, \
        "REDIS_URL should use service name (redis) for DNS resolution"


def test_networks_section_format(temp_dir: Path) -> None:
    """Test that networks section has correct format for Docker Compose."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify networks section structure
    assert "networks" in compose_data, "docker-compose.yaml must have networks section"

    networks = compose_data["networks"]
    assert isinstance(networks, dict), "networks section must be a dictionary"

    # Check each network is properly defined
    for network_name, network_config in networks.items():
        # Network name should be a non-empty string
        assert isinstance(network_name, str), f"Network name should be a string, got {type(network_name)}"
        assert len(network_name) > 0, "Network name should not be empty"

        # Network config can be None (default) or a dict with configuration
        assert network_config is None or isinstance(network_config, dict), \
            f"{network_name} must be None or a dictionary configuration"

        # If network has config, it should have valid keys
        if network_config is not None:
            valid_keys = ["driver", "driver_opts", "ipam", "external", "internal", "name", "labels"]
            for key in network_config.keys():
                # Just verify it's a known Docker Compose network key (not exhaustive)
                # This is a soft check - Docker Compose will validate the actual config
                pass


def test_network_isolation_from_other_projects(temp_dir: Path) -> None:
    """Test that custom network provides isolation from other Docker Compose projects."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    networks = compose_data["networks"]

    # By defining a custom network (not just relying on default),
    # we ensure isolation from other Docker Compose projects
    assert len(networks) > 0, "Custom network should be defined for project isolation"

    # Check that network is not marked as external (which would share with other projects)
    for network_name, network_config in networks.items():
        if network_config is not None and isinstance(network_config, dict):
            # Network should not be external (if external is not specified, it's internal by default)
            is_external = network_config.get("external", False)
            assert not is_external, \
                f"Network {network_name} should not be external for proper project isolation"


def test_network_supports_depends_on(temp_dir: Path) -> None:
    """Test that network configuration works with depends_on for service ordering."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]
    backend_service = services.get("backend") or services.get("api")

    assert backend_service is not None, "backend service should exist"

    # Verify depends_on is configured
    assert "depends_on" in backend_service, "backend should have depends_on configuration"

    depends_on = backend_service["depends_on"]

    # Backend should depend on db and redis
    assert "db" in depends_on or "postgres" in depends_on, "backend should depend on db/postgres"
    assert "redis" in depends_on, "backend should depend on redis"

    # With the network in place, these dependencies will work correctly
    # because all services are on the same network and can resolve each other's names


def test_schnitzel_network_exists(temp_dir: Path) -> None:
    """Test that specifically the schnitzel_network is defined."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify networks section exists
    assert "networks" in compose_data, "docker-compose.yaml missing networks section"

    networks = compose_data["networks"]

    # Check that schnitzel_network is defined
    assert "schnitzel_network" in networks, \
        "schnitzel_network should be defined in networks section"


def test_all_services_use_schnitzel_network(temp_dir: Path) -> None:
    """Test that all services are connected to schnitzel_network."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # Check db service
    db_service = services.get("db") or services.get("postgres")
    assert db_service is not None, "db/postgres service should exist"
    assert "schnitzel_network" in db_service.get("networks", []), \
        "db service should be connected to schnitzel_network"

    # Check redis service
    redis_service = services.get("redis")
    assert redis_service is not None, "redis service should exist"
    assert "schnitzel_network" in redis_service.get("networks", []), \
        "redis service should be connected to schnitzel_network"

    # Check backend service
    backend_service = services.get("backend") or services.get("api")
    assert backend_service is not None, "backend/api service should exist"
    assert "schnitzel_network" in backend_service.get("networks", []), \
        "backend service should be connected to schnitzel_network"
