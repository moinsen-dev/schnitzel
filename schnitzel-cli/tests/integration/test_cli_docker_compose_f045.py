"""Integration tests for F045 - Init command generates comprehensive docker-compose.yaml.

Test Requirements:
- test_docker_compose_has_db_service
- test_docker_compose_has_backend_service
- test_docker_compose_has_volumes
- test_docker_compose_db_has_healthcheck
- test_docker_compose_is_valid_yaml
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
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_docker_compose_has_db_service(temp_dir: Path) -> None:
    """Test that docker-compose.yaml includes a PostgreSQL database service."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read docker-compose.yaml
    docker_compose_file = temp_dir / project_name / "docker-compose.yaml"
    assert docker_compose_file.exists(), "docker-compose.yaml not created"

    # Parse YAML
    with open(docker_compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify db service exists
    assert "services" in compose_data, "docker-compose.yaml missing services section"
    assert "db" in compose_data["services"], "docker-compose.yaml missing db service"

    db_service = compose_data["services"]["db"]

    # Verify db service configuration
    assert db_service["image"] == "postgres:16", "db service should use postgres:16 image"

    # Verify environment variables
    assert "environment" in db_service, "db service missing environment variables"
    env = db_service["environment"]
    assert env["POSTGRES_USER"] == "schnitzel", "POSTGRES_USER should be 'schnitzel'"
    assert env["POSTGRES_PASSWORD"] == "schnitzel", "POSTGRES_PASSWORD should be 'schnitzel'"
    assert env["POSTGRES_DB"] == "schnitzel", "POSTGRES_DB should be 'schnitzel'"

    # Verify ports
    assert "ports" in db_service, "db service missing ports configuration"
    assert "5432:5432" in db_service["ports"], "db service should expose port 5432"

    # Verify volumes
    assert "volumes" in db_service, "db service missing volumes configuration"
    assert "postgres_data:/var/lib/postgresql/data" in db_service["volumes"], \
        "db service should mount postgres_data volume"


def test_docker_compose_has_backend_service(temp_dir: Path) -> None:
    """Test that docker-compose.yaml includes a backend service with proper configuration."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read docker-compose.yaml
    docker_compose_file = temp_dir / project_name / "docker-compose.yaml"
    with open(docker_compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify backend service exists
    assert "backend" in compose_data["services"], "docker-compose.yaml missing backend service"

    backend_service = compose_data["services"]["backend"]

    # Verify backend service configuration
    assert backend_service["build"] == "./backend", "backend service should build from ./backend"

    # Verify ports
    assert "ports" in backend_service, "backend service missing ports configuration"
    assert "8000:8000" in backend_service["ports"], "backend service should expose port 8000"

    # Verify environment variables
    assert "environment" in backend_service, "backend service missing environment variables"
    env = backend_service["environment"]
    expected_db_url = "postgresql://schnitzel:schnitzel@db:5432/schnitzel"
    assert env["DATABASE_URL"] == expected_db_url, \
        f"DATABASE_URL should be '{expected_db_url}'"

    # Verify volumes (backend should mount ./backend:/app)
    assert "volumes" in backend_service, "backend service missing volumes configuration"
    assert "./backend:/app" in backend_service["volumes"], \
        "backend service should mount ./backend:/app"


def test_docker_compose_has_volumes(temp_dir: Path) -> None:
    """Test that docker-compose.yaml defines volumes section."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read docker-compose.yaml
    docker_compose_file = temp_dir / project_name / "docker-compose.yaml"
    with open(docker_compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify volumes section exists
    assert "volumes" in compose_data, "docker-compose.yaml missing volumes section"
    assert "postgres_data" in compose_data["volumes"], \
        "volumes section should define postgres_data volume"


def test_docker_compose_db_has_healthcheck(temp_dir: Path) -> None:
    """Test that the db service includes a healthcheck configuration."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read docker-compose.yaml
    docker_compose_file = temp_dir / project_name / "docker-compose.yaml"
    with open(docker_compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    db_service = compose_data["services"]["db"]

    # Verify healthcheck exists
    assert "healthcheck" in db_service, "db service missing healthcheck configuration"

    healthcheck = db_service["healthcheck"]

    # Verify healthcheck configuration
    assert "test" in healthcheck, "healthcheck missing test command"
    assert healthcheck["test"] == ["CMD-SHELL", "pg_isready -U schnitzel"], \
        "healthcheck test should use pg_isready"

    assert "interval" in healthcheck, "healthcheck missing interval"
    assert healthcheck["interval"] == "5s", "healthcheck interval should be 5s"

    assert "timeout" in healthcheck, "healthcheck missing timeout"
    assert healthcheck["timeout"] == "5s", "healthcheck timeout should be 5s"

    assert "retries" in healthcheck, "healthcheck missing retries"
    assert healthcheck["retries"] == 5, "healthcheck retries should be 5"


def test_docker_compose_is_valid_yaml(temp_dir: Path) -> None:
    """Test that docker-compose.yaml is valid YAML and can be parsed."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read docker-compose.yaml
    docker_compose_file = temp_dir / project_name / "docker-compose.yaml"
    assert docker_compose_file.exists(), "docker-compose.yaml not created"

    # Verify it's valid YAML
    try:
        with open(docker_compose_file, "r") as f:
            compose_data = yaml.safe_load(f)
        assert compose_data is not None, "docker-compose.yaml parsed to None"
        assert isinstance(compose_data, dict), "docker-compose.yaml should parse to a dictionary"
    except yaml.YAMLError as e:
        pytest.fail(f"docker-compose.yaml is not valid YAML: {e}")

    # Verify version
    assert "version" in compose_data, "docker-compose.yaml missing version field"
    assert compose_data["version"] == "3.8", "docker-compose.yaml version should be 3.8"


def test_docker_compose_backend_depends_on_db_health(temp_dir: Path) -> None:
    """Test that backend service depends on db service with health condition."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read docker-compose.yaml
    docker_compose_file = temp_dir / project_name / "docker-compose.yaml"
    with open(docker_compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    backend_service = compose_data["services"]["backend"]

    # Verify depends_on configuration
    assert "depends_on" in backend_service, "backend service missing depends_on configuration"
    depends_on = backend_service["depends_on"]

    # Verify it depends on db with service_healthy condition
    assert "db" in depends_on, "backend service should depend on db"
    assert isinstance(depends_on["db"], dict), "depends_on db should be a dictionary"
    assert "condition" in depends_on["db"], "depends_on db missing condition"
    assert depends_on["db"]["condition"] == "service_healthy", \
        "backend should wait for db to be healthy"


def test_docker_compose_network_configuration(temp_dir: Path) -> None:
    """Test that services are properly configured for network communication."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Read docker-compose.yaml
    docker_compose_file = temp_dir / project_name / "docker-compose.yaml"
    with open(docker_compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify both services exist (they'll be on the same default network)
    assert "db" in compose_data["services"], "db service should exist"
    assert "backend" in compose_data["services"], "backend service should exist"

    # Verify DATABASE_URL references the db service by name
    backend_env = compose_data["services"]["backend"]["environment"]
    assert "db:5432" in backend_env["DATABASE_URL"], \
        "DATABASE_URL should reference db service by name"
