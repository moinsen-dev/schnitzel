"""Integration tests for F063 - Docker Compose PostgreSQL health checks.

Test Requirements:
- test_postgres_has_healthcheck - healthcheck defined
- test_postgres_healthcheck_uses_pg_isready - uses pg_isready command
- test_postgres_healthcheck_has_intervals - interval, timeout, retries defined
- test_backend_depends_on_healthy_postgres - backend waits for healthy db
- test_postgres_healthcheck_start_period - start_period is configured
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


def test_postgres_has_healthcheck(temp_dir: Path) -> None:
    """Test that postgres service has healthcheck defined."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get postgres service (db)
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"

    # Verify healthcheck exists
    assert "healthcheck" in postgres_service, "postgres service missing healthcheck configuration"

    healthcheck = postgres_service["healthcheck"]

    # Verify healthcheck has test command
    assert "test" in healthcheck, "healthcheck missing test command"


def test_postgres_healthcheck_uses_pg_isready(temp_dir: Path) -> None:
    """Test that postgres healthcheck uses pg_isready command."""
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

    # Verify healthcheck uses pg_isready
    test_command = healthcheck["test"]
    assert isinstance(test_command, list), "healthcheck test should be a list"

    # Should use CMD-SHELL format
    assert test_command[0] == "CMD-SHELL", "healthcheck should use CMD-SHELL format"

    # Should contain pg_isready in the command
    command_str = " ".join(test_command)
    assert "pg_isready" in command_str, "healthcheck should use pg_isready command"

    # Should specify username with -U flag (can be hardcoded or env var)
    assert ("-U schnitzel" in command_str or "-U=schnitzel" in command_str or
            "-U ${POSTGRES_USER" in command_str), \
        "healthcheck should specify username with -U flag"

    # Should specify database with -d flag (can be hardcoded or env var)
    assert ("-d schnitzel_db" in command_str or "-d=schnitzel_db" in command_str or
            "-d ${POSTGRES_DB" in command_str), \
        "healthcheck should specify database with -d flag"


def test_postgres_healthcheck_has_intervals(temp_dir: Path) -> None:
    """Test that postgres healthcheck has interval, timeout, retries defined."""
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

    # Verify healthcheck has interval
    assert "interval" in healthcheck, "healthcheck missing interval"
    interval = healthcheck["interval"]
    assert isinstance(interval, str) and interval.endswith("s"), \
        "interval should be in seconds format (e.g., '5s')"

    # Verify healthcheck has timeout
    assert "timeout" in healthcheck, "healthcheck missing timeout"
    timeout = healthcheck["timeout"]
    assert isinstance(timeout, str) and timeout.endswith("s"), \
        "timeout should be in seconds format (e.g., '5s')"

    # Verify healthcheck has retries
    assert "retries" in healthcheck, "healthcheck missing retries"
    retries = healthcheck["retries"]
    assert isinstance(retries, int) and retries > 0, \
        "retries should be a positive integer"

    # Verify reasonable values
    interval_value = int(interval[:-1])
    timeout_value = int(timeout[:-1])

    assert interval_value > 0, "interval should be greater than 0 seconds"
    assert timeout_value > 0, "timeout should be greater than 0 seconds"
    assert retries >= 3, "retries should be at least 3"


def test_backend_depends_on_healthy_postgres(temp_dir: Path) -> None:
    """Test that backend service waits for healthy db status."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get backend service
    services = compose_data["services"]
    assert "backend" in services, "backend service not found"

    backend_service = services["backend"]

    # Verify backend has depends_on
    assert "depends_on" in backend_service, "backend service missing depends_on configuration"

    depends_on = backend_service["depends_on"]

    # depends_on should have db entry
    assert "db" in depends_on or "postgres" in depends_on, \
        "backend should depend on db/postgres service"

    # Get the db dependency config
    db_dependency = depends_on.get("db") or depends_on.get("postgres")

    # Should be a dictionary with condition
    assert isinstance(db_dependency, dict), \
        "db dependency should be a dictionary with condition"

    # Should specify service_healthy condition
    assert "condition" in db_dependency, \
        "db dependency missing condition"
    assert db_dependency["condition"] == "service_healthy", \
        "backend should wait for db to be healthy (condition: service_healthy)"


def test_postgres_healthcheck_start_period(temp_dir: Path) -> None:
    """Test that postgres healthcheck has start_period configured."""
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

    # Verify healthcheck has start_period
    assert "start_period" in healthcheck, "healthcheck missing start_period"

    start_period = healthcheck["start_period"]
    assert isinstance(start_period, str) and start_period.endswith("s"), \
        "start_period should be in seconds format (e.g., '10s')"

    # Verify reasonable value
    start_period_value = int(start_period[:-1])
    assert start_period_value > 0, "start_period should be greater than 0 seconds"
    assert start_period_value >= 5, \
        "start_period should be at least 5 seconds to allow postgres initialization"


def test_postgres_healthcheck_comprehensive(temp_dir: Path) -> None:
    """Test comprehensive healthcheck configuration meets all requirements."""
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

    # Verify all required fields are present
    required_fields = ["test", "interval", "timeout", "retries", "start_period"]
    for field in required_fields:
        assert field in healthcheck, f"healthcheck missing required field: {field}"

    # Verify test command format
    test_command = healthcheck["test"]
    assert len(test_command) == 2, "healthcheck test should have 2 elements: [CMD-SHELL, command]"
    assert test_command[0] == "CMD-SHELL", "first element should be CMD-SHELL"

    # Verify pg_isready with proper flags
    command = test_command[1]
    assert "pg_isready" in command, "should use pg_isready"
    # Username can be hardcoded or use environment variable
    assert ("-U schnitzel" in command or "-U ${POSTGRES_USER" in command), \
        "should specify user with -U flag"
    # Database can be hardcoded or use environment variable
    assert ("-d schnitzel_db" in command or "-d ${POSTGRES_DB" in command), \
        "should specify database with -d flag"

    # Verify timing values
    assert healthcheck["interval"] == "5s", "interval should be 5s"
    assert healthcheck["timeout"] == "5s", "timeout should be 5s"
    assert healthcheck["retries"] == 5, "retries should be 5"
    assert healthcheck["start_period"] == "10s", "start_period should be 10s"
