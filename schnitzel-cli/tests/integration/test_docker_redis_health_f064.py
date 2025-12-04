"""Integration tests for F064 - Docker Compose Redis service with health checks.

Test Requirements:
- test_redis_has_healthcheck - healthcheck defined
- test_redis_healthcheck_uses_ping - uses redis-cli ping
- test_redis_healthcheck_has_intervals - interval, timeout, retries defined
- test_backend_depends_on_healthy_redis - backend waits for healthy redis
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


def test_redis_has_healthcheck(temp_dir: Path) -> None:
    """Test that Redis service has healthcheck defined."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify services section exists
    assert "services" in compose_data, "docker-compose.yaml missing services section"

    # Check for redis service
    assert "redis" in compose_data["services"], "docker-compose.yaml missing redis service"

    redis_service = compose_data["services"]["redis"]

    # Verify healthcheck exists
    assert "healthcheck" in redis_service, "redis service missing healthcheck configuration"

    healthcheck = redis_service["healthcheck"]

    # Verify healthcheck has required fields
    assert "test" in healthcheck, "healthcheck missing test command"
    assert isinstance(healthcheck["test"], list), "healthcheck test should be a list"


def test_redis_healthcheck_uses_ping(temp_dir: Path) -> None:
    """Test that Redis healthcheck uses redis-cli ping."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    redis_service = compose_data["services"]["redis"]
    healthcheck = redis_service["healthcheck"]

    # Verify healthcheck uses redis-cli ping
    test_command = healthcheck["test"]
    assert isinstance(test_command, list), "healthcheck test should be a list"

    # The test command should be ["CMD", "redis-cli", "ping"]
    assert "CMD" in test_command, "healthcheck should use CMD format"
    assert "redis-cli" in test_command, "healthcheck should use redis-cli"
    assert "ping" in test_command, "healthcheck should use ping command"

    # Verify exact format
    assert test_command == ["CMD", "redis-cli", "ping"], \
        f"healthcheck test should be ['CMD', 'redis-cli', 'ping'], got {test_command}"


def test_redis_healthcheck_has_intervals(temp_dir: Path) -> None:
    """Test that Redis healthcheck has interval, timeout, and retries defined."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    redis_service = compose_data["services"]["redis"]
    healthcheck = redis_service["healthcheck"]

    # Verify all timing parameters are present
    assert "interval" in healthcheck, "healthcheck missing interval"
    assert "timeout" in healthcheck, "healthcheck missing timeout"
    assert "retries" in healthcheck, "healthcheck missing retries"

    # Verify interval format and value
    interval = healthcheck["interval"]
    assert isinstance(interval, str) and interval.endswith("s"), "interval should be in seconds format"
    interval_value = int(interval[:-1])
    assert interval_value == 5, f"healthcheck interval should be 5s, got {interval}"

    # Verify timeout format and value
    timeout = healthcheck["timeout"]
    assert isinstance(timeout, str) and timeout.endswith("s"), "timeout should be in seconds format"
    timeout_value = int(timeout[:-1])
    assert timeout_value == 5, f"healthcheck timeout should be 5s, got {timeout}"

    # Verify retries value
    retries = healthcheck["retries"]
    assert isinstance(retries, int), "retries should be an integer"
    assert retries == 5, f"healthcheck retries should be 5, got {retries}"


def test_backend_depends_on_healthy_redis(temp_dir: Path) -> None:
    """Test that backend service waits for healthy Redis status."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify backend service exists
    assert "backend" in compose_data["services"], "docker-compose.yaml missing backend service"

    backend_service = compose_data["services"]["backend"]

    # Verify depends_on exists
    assert "depends_on" in backend_service, "backend service missing depends_on configuration"

    depends_on = backend_service["depends_on"]

    # Verify depends_on includes redis
    assert "redis" in depends_on, "backend service should depend on redis"

    # Verify redis dependency has service_healthy condition
    redis_dependency = depends_on["redis"]
    assert isinstance(redis_dependency, dict), "redis dependency should be a dictionary with condition"
    assert "condition" in redis_dependency, "redis dependency missing condition"
    assert redis_dependency["condition"] == "service_healthy", \
        f"redis dependency should have condition: service_healthy, got {redis_dependency['condition']}"


def test_redis_healthcheck_has_start_period(temp_dir: Path) -> None:
    """Test that Redis healthcheck has start_period defined."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    redis_service = compose_data["services"]["redis"]
    healthcheck = redis_service["healthcheck"]

    # Verify start_period is present
    assert "start_period" in healthcheck, "healthcheck missing start_period"

    # Verify start_period format and value
    start_period = healthcheck["start_period"]
    assert isinstance(start_period, str) and start_period.endswith("s"), \
        "start_period should be in seconds format"
    start_period_value = int(start_period[:-1])
    assert start_period_value == 5, f"healthcheck start_period should be 5s, got {start_period}"


def test_redis_service_configuration(temp_dir: Path) -> None:
    """Test that Redis service has proper configuration."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    redis_service = compose_data["services"]["redis"]

    # Verify image
    assert "image" in redis_service, "redis service missing image"
    assert "redis" in redis_service["image"], "redis service should use redis image"

    # Verify ports
    assert "ports" in redis_service, "redis service missing ports configuration"
    ports = redis_service["ports"]
    assert isinstance(ports, list), "ports should be a list"

    # Check that port 6379 is exposed
    port_found = False
    for port_mapping in ports:
        if "6379" in str(port_mapping):
            port_found = True
            break

    assert port_found, "redis service should expose port 6379"


def test_backend_has_redis_environment_variable(temp_dir: Path) -> None:
    """Test that backend service has REDIS_URL environment variable."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    backend_service = compose_data["services"]["backend"]

    # Verify environment variables exist
    assert "environment" in backend_service, "backend service missing environment variables"
    env = backend_service["environment"]

    # Check REDIS_URL exists
    assert "REDIS_URL" in env, "backend service missing REDIS_URL environment variable"

    # Verify REDIS_URL points to redis service
    redis_url = env["REDIS_URL"]
    assert "redis" in redis_url.lower(), "REDIS_URL should reference redis service"
    assert "6379" in redis_url, "REDIS_URL should include default Redis port 6379"


def test_redis_healthcheck_comprehensive(temp_dir: Path) -> None:
    """Comprehensive test for Redis healthcheck configuration."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    redis_service = compose_data["services"]["redis"]
    healthcheck = redis_service["healthcheck"]

    # Verify all required healthcheck fields
    required_fields = ["test", "interval", "timeout", "retries", "start_period"]
    for field in required_fields:
        assert field in healthcheck, f"healthcheck missing required field: {field}"

    # Verify exact configuration matches requirements
    assert healthcheck["test"] == ["CMD", "redis-cli", "ping"]
    assert healthcheck["interval"] == "5s"
    assert healthcheck["timeout"] == "5s"
    assert healthcheck["retries"] == 5
    assert healthcheck["start_period"] == "5s"
