"""Integration tests for F072 - Docker Compose services start successfully.

Test Requirements:
- test_docker_compose_has_required_services - db, redis, backend services exist
- test_services_have_images_defined - all services have image specified
- test_services_have_ports_defined - all services expose ports
- test_backend_has_all_dependencies - depends_on db and redis
- test_services_have_healthchecks - db and redis have healthchecks
- test_docker_compose_is_complete_config - no missing required fields

NOTE: Cannot actually start Docker in CI tests, but can verify config completeness.
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


def test_docker_compose_has_required_services(temp_dir: Path) -> None:
    """Test that docker-compose.yaml includes db, redis, and backend services."""
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

    services = compose_data["services"]

    # Check for required services
    required_services = ["db", "redis", "backend"]
    for service_name in required_services:
        assert service_name in services, f"docker-compose.yaml missing {service_name} service"

    # Verify all services are dictionaries with configuration
    for service_name in required_services:
        assert isinstance(services[service_name], dict), \
            f"{service_name} service should be a dictionary with configuration"
        assert len(services[service_name]) > 0, \
            f"{service_name} service should have configuration"


def test_services_have_images_defined(temp_dir: Path) -> None:
    """Test that all services have image or build specified."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # db service should have image
    assert "db" in services, "db service not found"
    db_service = services["db"]
    assert "image" in db_service, "db service missing image field"
    assert db_service["image"], "db service image should not be empty"
    # Should be PostgreSQL with pgvector
    assert "pgvector" in db_service["image"] or "postgres" in db_service["image"], \
        f"db service should use PostgreSQL-based image, got {db_service['image']}"

    # redis service should have image
    assert "redis" in services, "redis service not found"
    redis_service = services["redis"]
    assert "image" in redis_service, "redis service missing image field"
    assert redis_service["image"], "redis service image should not be empty"
    assert "redis" in redis_service["image"], \
        f"redis service should use Redis image, got {redis_service['image']}"

    # backend service should have build or image
    assert "backend" in services, "backend service not found"
    backend_service = services["backend"]
    assert "build" in backend_service or "image" in backend_service, \
        "backend service should have either build or image field"

    if "build" in backend_service:
        assert backend_service["build"], "backend service build should not be empty"
    if "image" in backend_service:
        assert backend_service["image"], "backend service image should not be empty"


def test_services_have_ports_defined(temp_dir: Path) -> None:
    """Test that all services expose ports."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # All three services should expose ports
    required_services = ["db", "redis", "backend"]
    for service_name in required_services:
        assert service_name in services, f"{service_name} service not found"
        service = services[service_name]
        assert "ports" in service, f"{service_name} service missing ports configuration"
        assert isinstance(service["ports"], list), \
            f"{service_name} service ports should be a list"
        assert len(service["ports"]) > 0, \
            f"{service_name} service should expose at least one port"

    # Verify specific ports
    db_service = services["db"]
    db_ports_str = str(db_service["ports"])
    assert "5432" in db_ports_str, "db service should expose PostgreSQL port 5432"

    redis_service = services["redis"]
    redis_ports_str = str(redis_service["ports"])
    assert "6379" in redis_ports_str, "redis service should expose Redis port 6379"

    backend_service = services["backend"]
    backend_ports_str = str(backend_service["ports"])
    assert "8000" in backend_ports_str, "backend service should expose port 8000"


def test_backend_has_all_dependencies(temp_dir: Path) -> None:
    """Test that backend depends_on both db and redis services."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # Verify backend service exists
    assert "backend" in services, "backend service not found"
    backend_service = services["backend"]

    # Verify backend has depends_on
    assert "depends_on" in backend_service, \
        "backend service missing depends_on configuration"

    depends_on = backend_service["depends_on"]
    assert isinstance(depends_on, dict), \
        "backend depends_on should be a dictionary"

    # Backend should depend on both db and redis
    assert "db" in depends_on, "backend should depend on db service"
    assert "redis" in depends_on, "backend should depend on redis service"

    # Dependencies should wait for healthy status
    db_dependency = depends_on["db"]
    redis_dependency = depends_on["redis"]

    assert isinstance(db_dependency, dict), "db dependency should be a dictionary"
    assert "condition" in db_dependency, "db dependency should have condition"
    assert db_dependency["condition"] == "service_healthy", \
        "backend should wait for db to be healthy"

    assert isinstance(redis_dependency, dict), "redis dependency should be a dictionary"
    assert "condition" in redis_dependency, "redis dependency should have condition"
    assert redis_dependency["condition"] == "service_healthy", \
        "backend should wait for redis to be healthy"


def test_services_have_healthchecks(temp_dir: Path) -> None:
    """Test that db and redis services have healthcheck configurations."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # db service healthcheck
    assert "db" in services, "db service not found"
    db_service = services["db"]
    assert "healthcheck" in db_service, "db service missing healthcheck configuration"

    db_healthcheck = db_service["healthcheck"]
    assert isinstance(db_healthcheck, dict), "db healthcheck should be a dictionary"
    assert "test" in db_healthcheck, "db healthcheck missing test command"
    assert "interval" in db_healthcheck, "db healthcheck missing interval"
    assert "timeout" in db_healthcheck, "db healthcheck missing timeout"
    assert "retries" in db_healthcheck, "db healthcheck missing retries"

    # Verify db healthcheck uses pg_isready
    test_command = db_healthcheck["test"]
    test_str = " ".join(test_command) if isinstance(test_command, list) else test_command
    assert "pg_isready" in test_str, "db healthcheck should use pg_isready command"

    # redis service healthcheck
    assert "redis" in services, "redis service not found"
    redis_service = services["redis"]
    assert "healthcheck" in redis_service, "redis service missing healthcheck configuration"

    redis_healthcheck = redis_service["healthcheck"]
    assert isinstance(redis_healthcheck, dict), "redis healthcheck should be a dictionary"
    assert "test" in redis_healthcheck, "redis healthcheck missing test command"
    assert "interval" in redis_healthcheck, "redis healthcheck missing interval"
    assert "timeout" in redis_healthcheck, "redis healthcheck missing timeout"
    assert "retries" in redis_healthcheck, "redis healthcheck missing retries"

    # Verify redis healthcheck uses redis-cli ping
    test_command = redis_healthcheck["test"]
    test_str = " ".join(test_command) if isinstance(test_command, list) else test_command
    assert "redis-cli" in test_str or "ping" in test_str, \
        "redis healthcheck should use redis-cli ping command"


def test_docker_compose_is_complete_config(temp_dir: Path) -> None:
    """Test that docker-compose.yaml has no missing required fields."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Root level required fields
    assert "version" in compose_data, "docker-compose.yaml missing version field"
    assert "services" in compose_data, "docker-compose.yaml missing services section"
    assert "volumes" in compose_data, "docker-compose.yaml missing volumes section"

    # Verify version is valid
    version = compose_data["version"]
    assert version in ["3", "3.8", "3.9"], \
        f"docker-compose version should be 3.x, got {version}"

    services = compose_data["services"]

    # db service completeness
    db_service = services["db"]
    db_required_fields = ["image", "environment", "ports", "volumes", "healthcheck"]
    for field in db_required_fields:
        assert field in db_service, f"db service missing required field: {field}"

    # Verify db environment variables are complete
    db_env = db_service["environment"]
    db_env_vars = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
    for env_var in db_env_vars:
        assert env_var in db_env, f"db service missing environment variable: {env_var}"

    # redis service completeness
    redis_service = services["redis"]
    redis_required_fields = ["image", "command", "volumes", "ports", "healthcheck"]
    for field in redis_required_fields:
        assert field in redis_service, f"redis service missing required field: {field}"

    # Verify redis persistence command
    redis_command = redis_service["command"]
    redis_command_str = " ".join(redis_command) if isinstance(redis_command, list) else redis_command
    assert "appendonly" in redis_command_str, \
        "redis command should include appendonly for persistence"

    # backend service completeness
    backend_service = services["backend"]
    backend_required_fields = ["build", "ports", "environment", "depends_on", "volumes"]
    for field in backend_required_fields:
        # backend can have either build or image, not necessarily both
        if field == "build" and "image" in backend_service:
            continue
        assert field in backend_service, f"backend service missing required field: {field}"

    # Verify backend environment variables are complete
    backend_env = backend_service["environment"]
    backend_env_vars = ["DATABASE_URL", "REDIS_URL"]
    for env_var in backend_env_vars:
        assert env_var in backend_env, f"backend service missing environment variable: {env_var}"

    # Verify volumes section is complete
    volumes = compose_data["volumes"]
    required_volumes = ["postgres_data", "redis_data"]
    for volume_name in required_volumes:
        assert volume_name in volumes, f"volumes section missing {volume_name}"


def test_docker_compose_healthcheck_completeness(temp_dir: Path) -> None:
    """Test that healthchecks have all required configuration fields."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # Check db healthcheck completeness
    db_healthcheck = services["db"]["healthcheck"]
    db_healthcheck_fields = ["test", "interval", "timeout", "retries", "start_period"]
    for field in db_healthcheck_fields:
        assert field in db_healthcheck, f"db healthcheck missing field: {field}"

    # Verify interval and timeout formats
    assert db_healthcheck["interval"].endswith("s"), \
        "db healthcheck interval should be in seconds format"
    assert db_healthcheck["timeout"].endswith("s"), \
        "db healthcheck timeout should be in seconds format"
    assert isinstance(db_healthcheck["retries"], int), \
        "db healthcheck retries should be an integer"

    # Check redis healthcheck completeness
    redis_healthcheck = services["redis"]["healthcheck"]
    redis_healthcheck_fields = ["test", "interval", "timeout", "retries", "start_period"]
    for field in redis_healthcheck_fields:
        assert field in redis_healthcheck, f"redis healthcheck missing field: {field}"

    # Verify interval and timeout formats
    assert redis_healthcheck["interval"].endswith("s"), \
        "redis healthcheck interval should be in seconds format"
    assert redis_healthcheck["timeout"].endswith("s"), \
        "redis healthcheck timeout should be in seconds format"
    assert isinstance(redis_healthcheck["retries"], int), \
        "redis healthcheck retries should be an integer"


def test_docker_compose_valid_yaml_structure(temp_dir: Path) -> None:
    """Test that generated docker-compose.yaml has valid YAML structure."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML - this will raise an exception if YAML is invalid
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify it's a dictionary (not a list or string)
    assert isinstance(compose_data, dict), \
        "docker-compose.yaml should parse to a dictionary"

    # Verify services is a dictionary
    assert isinstance(compose_data["services"], dict), \
        "services section should be a dictionary"

    # Verify volumes is a dictionary
    assert isinstance(compose_data["volumes"], dict), \
        "volumes section should be a dictionary"

    # Verify each service is a dictionary
    for service_name, service_config in compose_data["services"].items():
        assert isinstance(service_config, dict), \
            f"{service_name} service configuration should be a dictionary"


def test_docker_compose_startup_readiness(temp_dir: Path) -> None:
    """Test that docker-compose.yaml configuration is ready for startup."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # Verify db service is startup-ready
    db_service = services["db"]
    assert "image" in db_service and db_service["image"], \
        "db service needs image to start"
    assert "environment" in db_service, "db service needs environment variables to start"
    assert "healthcheck" in db_service, "db service needs healthcheck for depends_on condition"

    # Verify redis service is startup-ready
    redis_service = services["redis"]
    assert "image" in redis_service and redis_service["image"], \
        "redis service needs image to start"
    assert "healthcheck" in redis_service, \
        "redis service needs healthcheck for depends_on condition"

    # Verify backend service is startup-ready
    backend_service = services["backend"]
    assert "build" in backend_service or "image" in backend_service, \
        "backend service needs build or image to start"
    assert "depends_on" in backend_service, \
        "backend service should wait for dependencies"
    assert "environment" in backend_service, \
        "backend service needs environment variables for DB connection"

    # Verify dependencies have healthy conditions
    depends_on = backend_service["depends_on"]
    for dependency_name, dependency_config in depends_on.items():
        if isinstance(dependency_config, dict):
            assert "condition" in dependency_config, \
                f"dependency {dependency_name} should have condition"
            assert dependency_config["condition"] == "service_healthy", \
                f"dependency {dependency_name} should wait for healthy condition"

    # Verify required volumes are defined
    volumes = compose_data["volumes"]
    assert "postgres_data" in volumes, "postgres_data volume needed for db persistence"
    assert "redis_data" in volumes, "redis_data volume needed for redis persistence"
