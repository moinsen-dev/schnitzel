"""Integration tests for F065 - Docker Compose environment variable substitution.

Test Requirements:
- test_postgres_uses_env_vars - environment variables use ${VAR:-default} syntax
- test_postgres_has_default_values - default values are present
- test_redis_port_configurable - redis port uses env var
- test_backend_uses_env_vars - backend has env var config
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


def test_postgres_uses_env_vars(temp_dir: Path) -> None:
    """Test that postgres environment variables use ${VAR:-default} syntax."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify environment variable syntax is present in the raw content
    assert "${POSTGRES_USER:-" in compose_content, \
        "docker-compose.yaml should use ${POSTGRES_USER:-default} syntax"
    assert "${POSTGRES_PASSWORD:-" in compose_content, \
        "docker-compose.yaml should use ${POSTGRES_PASSWORD:-default} syntax"
    assert "${POSTGRES_DB:-" in compose_content, \
        "docker-compose.yaml should use ${POSTGRES_DB:-default} syntax"
    assert "${POSTGRES_PORT:-" in compose_content, \
        "docker-compose.yaml should use ${POSTGRES_PORT:-default} syntax"


def test_postgres_has_default_values(temp_dir: Path) -> None:
    """Test that postgres environment variables have sensible default values."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Check for default values in the raw content
    assert "${POSTGRES_USER:-schnitzel}" in compose_content, \
        "POSTGRES_USER should default to 'schnitzel'"
    assert "${POSTGRES_PASSWORD:-schnitzel_dev}" in compose_content, \
        "POSTGRES_PASSWORD should default to 'schnitzel_dev'"
    assert "${POSTGRES_DB:-schnitzel_db}" in compose_content, \
        "POSTGRES_DB should default to 'schnitzel_db'"
    assert "${POSTGRES_PORT:-5432}" in compose_content, \
        "POSTGRES_PORT should default to '5432'"


def test_postgres_port_configurable(temp_dir: Path) -> None:
    """Test that postgres port is configurable via environment variable."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify port mapping uses environment variable
    assert '"${POSTGRES_PORT:-5432}:5432"' in compose_content, \
        "postgres port mapping should use ${POSTGRES_PORT:-5432} syntax"


def test_redis_port_configurable(temp_dir: Path) -> None:
    """Test that redis port uses environment variable syntax."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify Redis port is configurable
    assert "${REDIS_PORT:-" in compose_content, \
        "docker-compose.yaml should use ${REDIS_PORT:-default} syntax"
    assert "${REDIS_PORT:-6379}" in compose_content, \
        "REDIS_PORT should default to '6379'"
    assert '"${REDIS_PORT:-6379}:6379"' in compose_content, \
        "redis port mapping should use ${REDIS_PORT:-6379} syntax"


def test_backend_uses_env_vars(temp_dir: Path) -> None:
    """Test that backend service uses environment variables in configuration."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify backend port is configurable
    assert "${BACKEND_PORT:-" in compose_content, \
        "backend should use ${BACKEND_PORT:-default} syntax"
    assert "${BACKEND_PORT:-8000}" in compose_content, \
        "BACKEND_PORT should default to '8000'"

    # Verify DATABASE_URL uses environment variables
    assert "DATABASE_URL: postgresql://${POSTGRES_USER:-schnitzel}" in compose_content, \
        "DATABASE_URL should use ${POSTGRES_USER:-schnitzel}"
    assert "${POSTGRES_PASSWORD:-schnitzel_dev}" in compose_content, \
        "DATABASE_URL should use ${POSTGRES_PASSWORD:-schnitzel_dev}"
    assert "${POSTGRES_DB:-schnitzel_db}" in compose_content, \
        "DATABASE_URL should use ${POSTGRES_DB:-schnitzel_db}"

    # Verify ENVIRONMENT variable is configurable
    assert "${ENVIRONMENT:-" in compose_content, \
        "backend should use ${ENVIRONMENT:-default} syntax"
    assert "${ENVIRONMENT:-development}" in compose_content, \
        "ENVIRONMENT should default to 'development'"


def test_environment_variables_documented(temp_dir: Path) -> None:
    """Test that environment variables are documented with comments."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify comments are present
    assert "# PostgreSQL credentials" in compose_content, \
        "postgres credentials should be documented"
    assert "# Default user:" in compose_content, \
        "default user should be documented"
    assert "# Default password:" in compose_content, \
        "default password should be documented"
    assert "# Default database name:" in compose_content, \
        "default database name should be documented"
    assert "# PostgreSQL port" in compose_content, \
        "postgres port should be documented"
    assert "# Redis port" in compose_content, \
        "redis port should be documented"
    assert "# Backend API port" in compose_content, \
        "backend port should be documented"


def test_healthcheck_uses_env_vars(temp_dir: Path) -> None:
    """Test that healthcheck commands use environment variables."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify healthcheck uses environment variables
    assert "pg_isready -U ${POSTGRES_USER:-schnitzel}" in compose_content, \
        "healthcheck should use ${POSTGRES_USER:-schnitzel}"
    assert "-d ${POSTGRES_DB:-schnitzel_db}" in compose_content, \
        "healthcheck should use ${POSTGRES_DB:-schnitzel_db}"


def test_generated_file_contains_env_vars(temp_dir: Path) -> None:
    """Test that the generated file contains environment variables when written to disk."""
    # Generate docker-compose.yaml to file
    generator = DockerComposeGenerator()
    compose_file, file_size = generator.generate_to_file(temp_dir)

    assert compose_file.exists(), "docker-compose.yaml should be created"
    assert file_size > 0, "docker-compose.yaml should not be empty"

    # Read the file and verify it contains environment variable syntax
    content = compose_file.read_text(encoding="utf-8")

    assert "${POSTGRES_USER:-schnitzel}" in content, \
        "generated file should contain ${POSTGRES_USER:-schnitzel}"
    assert "${POSTGRES_PASSWORD:-schnitzel_dev}" in content, \
        "generated file should contain ${POSTGRES_PASSWORD:-schnitzel_dev}"
    assert "${REDIS_PORT:-6379}" in content, \
        "generated file should contain ${REDIS_PORT:-6379}"
    assert "${BACKEND_PORT:-8000}" in content, \
        "generated file should contain ${BACKEND_PORT:-8000}"


def test_all_ports_configurable(temp_dir: Path) -> None:
    """Test that all service ports are configurable via environment variables."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Collect all port-related environment variables
    port_vars = {
        "POSTGRES_PORT": "5432",
        "REDIS_PORT": "6379",
        "BACKEND_PORT": "8000",
    }

    for var_name, default_port in port_vars.items():
        assert f"${{{var_name}:-{default_port}}}" in compose_content, \
            f"{var_name} should have environment variable with default {default_port}"


def test_redis_service_present(temp_dir: Path) -> None:
    """Test that Redis service is present in docker-compose.yaml."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Verify Redis service exists
    assert "services" in compose_data, "docker-compose.yaml should have services section"
    assert "redis" in compose_data["services"], "Redis service should be present"

    # Verify Redis has port configuration
    redis_service = compose_data["services"]["redis"]
    assert "ports" in redis_service, "Redis service should have ports configuration"


def test_backend_environment_variables(temp_dir: Path) -> None:
    """Test that backend service has all required environment variables."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify backend has all expected environment variables
    backend_env_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "ENVIRONMENT",
    ]

    for env_var in backend_env_vars:
        assert f"{env_var}:" in compose_content, \
            f"backend should have {env_var} environment variable"


def test_env_var_syntax_consistency(temp_dir: Path) -> None:
    """Test that all environment variables use consistent ${VAR:-default} syntax."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Find all environment variable references
    import re
    env_var_pattern = r'\$\{[A-Z_]+:-[^}]+\}'
    env_vars = re.findall(env_var_pattern, compose_content)

    # Verify we found environment variables
    assert len(env_vars) > 0, "should find environment variables in the content"

    # Verify each follows the pattern ${VAR:-default}
    for env_var in env_vars:
        assert env_var.startswith("${"), f"{env_var} should start with ${{"
        assert ":-" in env_var, f"{env_var} should contain :-"
        assert env_var.endswith("}"), f"{env_var} should end with }}"


def test_production_password_warning(temp_dir: Path) -> None:
    """Test that there's a warning about changing password in production."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify warning comment is present
    assert "change in production" in compose_content.lower(), \
        "should warn about changing password in production"
