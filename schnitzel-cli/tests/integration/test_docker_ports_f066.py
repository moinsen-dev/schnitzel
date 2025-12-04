"""Integration tests for F066 - Docker Compose port collision prevention.

Test Requirements:
- test_services_have_unique_ports - no port collisions in defaults
- test_postgres_default_port - 5432
- test_redis_default_port - 6379
- test_backend_default_port - 8000
- test_all_ports_configurable - all ports use env vars
"""

import tempfile
import os
from pathlib import Path
import pytest
import yaml
import re
from collections import defaultdict

from schnitzel.generators.docker.compose import DockerComposeGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_services_have_unique_ports(temp_dir: Path) -> None:
    """Test that no port collisions exist in default port assignments."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Extract all port mappings from all services
    services = compose_data.get("services", {})
    port_usage = defaultdict(list)  # port -> [service_names]

    for service_name, service_config in services.items():
        if "ports" in service_config:
            for port_mapping in service_config["ports"]:
                # Port mapping can be "host:container" or just "port"
                # Examples: "${POSTGRES_PORT:-5432}:5432" or "8000:8000"
                port_str = str(port_mapping)

                # Extract default port from ${VAR:-PORT}:CONTAINER_PORT format
                # Match pattern: ${VAR_NAME:-PORT}:CONTAINER_PORT
                match = re.search(r'\$\{[A-Z_]+:-(\d+)\}:(\d+)', port_str)
                if match:
                    default_port = match.group(1)
                    port_usage[default_port].append(service_name)
                elif ":" in port_str:
                    # Fallback for simple "HOST:CONTAINER" format
                    host_port = port_str.split(":")[0]
                    if host_port.isdigit():
                        port_usage[host_port].append(service_name)

    # Check for collisions
    collisions = {port: services for port, services in port_usage.items() if len(services) > 1}

    assert not collisions, \
        f"Port collisions detected: {collisions}. Each port should be used by only one service."

    # Verify we found ports (sanity check)
    assert len(port_usage) > 0, "Should have found port mappings in docker-compose.yaml"


def test_postgres_default_port(temp_dir: Path) -> None:
    """Test that PostgreSQL service uses default port 5432."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML to verify structure
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get postgres/db service
    services = compose_data["services"]
    postgres_service = services.get("postgres") or services.get("db")

    assert postgres_service is not None, "No postgres/db service found"
    assert "ports" in postgres_service, "postgres service missing ports configuration"

    # Check the raw content for the exact port syntax
    compose_content = compose_file.read_text(encoding="utf-8")

    # Verify PostgreSQL uses port 5432 as default
    assert "${POSTGRES_PORT:-5432}" in compose_content, \
        "PostgreSQL should use port 5432 as default (via ${POSTGRES_PORT:-5432})"

    # Verify the port mapping format
    assert '"${POSTGRES_PORT:-5432}:5432"' in compose_content, \
        "PostgreSQL port mapping should be ${POSTGRES_PORT:-5432}:5432"


def test_redis_default_port(temp_dir: Path) -> None:
    """Test that Redis service uses default port 6379."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML to verify structure
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get redis service
    services = compose_data["services"]
    redis_service = services.get("redis")

    assert redis_service is not None, "No redis service found"
    assert "ports" in redis_service, "redis service missing ports configuration"

    # Check the raw content for the exact port syntax
    compose_content = compose_file.read_text(encoding="utf-8")

    # Verify Redis uses port 6379 as default
    assert "${REDIS_PORT:-6379}" in compose_content, \
        "Redis should use port 6379 as default (via ${REDIS_PORT:-6379})"

    # Verify the port mapping format
    assert '"${REDIS_PORT:-6379}:6379"' in compose_content, \
        "Redis port mapping should be ${REDIS_PORT:-6379}:6379"


def test_backend_default_port(temp_dir: Path) -> None:
    """Test that backend service uses default port 8000."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML to verify structure
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    # Get backend service
    services = compose_data["services"]
    backend_service = services.get("backend")

    assert backend_service is not None, "No backend service found"
    assert "ports" in backend_service, "backend service missing ports configuration"

    # Check the raw content for the exact port syntax
    compose_content = compose_file.read_text(encoding="utf-8")

    # Verify backend uses port 8000 as default
    assert "${BACKEND_PORT:-8000}" in compose_content, \
        "Backend should use port 8000 as default (via ${BACKEND_PORT:-8000})"

    # Verify the port mapping format
    assert '"${BACKEND_PORT:-8000}:8000"' in compose_content, \
        "Backend port mapping should be ${BACKEND_PORT:-8000}:8000"


def test_all_ports_configurable(temp_dir: Path) -> None:
    """Test that all service ports are configurable via environment variables."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Define expected port environment variables with their defaults
    expected_port_vars = {
        "POSTGRES_PORT": "5432",
        "REDIS_PORT": "6379",
        "BACKEND_PORT": "8000",
    }

    for var_name, default_port in expected_port_vars.items():
        # Verify the environment variable syntax exists
        assert f"${{{var_name}:-{default_port}}}" in compose_content, \
            f"{var_name} should be configurable with default {default_port}"

        # Verify it's used in a port mapping (format: "${VAR:-PORT}:PORT")
        assert f'"${{{var_name}:-{default_port}}}:{default_port}"' in compose_content, \
            f"{var_name} should be used in port mapping format"


def test_port_documentation_exists(temp_dir: Path) -> None:
    """Test that all ports are documented with comments."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify port documentation comments exist
    port_comments = [
        "# PostgreSQL port - default: 5432",
        "# Redis port - default: 6379",
        "# Backend API port - default: 8000",
    ]

    for comment in port_comments:
        assert comment in compose_content, \
            f"Port documentation comment missing: {comment}"


def test_no_hardcoded_ports_in_environment(temp_dir: Path) -> None:
    """Test that environment variables don't use hardcoded ports that could collide."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})

    # Check backend service environment variables
    backend_service = services.get("backend")
    assert backend_service is not None, "Backend service should exist"

    backend_env = backend_service.get("environment", {})

    # DATABASE_URL should reference the internal container port (5432), not host port
    database_url = backend_env.get("DATABASE_URL", "")
    # The connection should use the internal service name and internal port
    assert "@db:5432/" in database_url, \
        "DATABASE_URL should use internal container port (db:5432) not host port"

    # REDIS_URL should reference the internal container port (6379)
    redis_url = backend_env.get("REDIS_URL", "")
    assert "redis://redis:6379" in redis_url, \
        "REDIS_URL should use internal container port (redis:6379) not host port"


def test_well_known_ports_assigned(temp_dir: Path) -> None:
    """Test that services use well-known standard ports as defaults."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify well-known ports are used
    well_known_ports = {
        "PostgreSQL": ("5432", "POSTGRES_PORT"),
        "Redis": ("6379", "REDIS_PORT"),
        "Backend": ("8000", "BACKEND_PORT"),  # Common Django/FastAPI port
    }

    for service_name, (port, env_var) in well_known_ports.items():
        assert f"${{{env_var}:-{port}}}" in compose_content, \
            f"{service_name} should use well-known port {port}"


def test_port_uniqueness_validation(temp_dir: Path) -> None:
    """Test that all default ports are unique (no duplicates)."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Extract all default port values using regex
    # Pattern: ${VAR_NAME:-PORT} where PORT is the default
    port_pattern = r'\$\{[A-Z_]+_PORT:-(\d+)\}'
    default_ports = re.findall(port_pattern, compose_content)

    # Check for duplicates
    port_counts = defaultdict(int)
    for port in default_ports:
        port_counts[port] += 1

    duplicates = {port: count for port, count in port_counts.items() if count > 1}

    assert not duplicates, \
        f"Duplicate port defaults found: {duplicates}. Each service must have a unique default port."

    # Verify we found the expected ports
    assert "5432" in default_ports, "Should find PostgreSQL default port 5432"
    assert "6379" in default_ports, "Should find Redis default port 6379"
    assert "8000" in default_ports, "Should find Backend default port 8000"


def test_environment_variables_prevent_collisions(temp_dir: Path) -> None:
    """Test that environment variable naming prevents accidental collisions."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Verify each service has its own unique port environment variable
    port_env_vars = ["POSTGRES_PORT", "REDIS_PORT", "BACKEND_PORT"]

    for var in port_env_vars:
        # Check the variable is used in port mapping
        assert f"${{{var}:-" in compose_content, \
            f"{var} should be present in docker-compose.yaml"

    # Verify all port variables are unique
    assert len(port_env_vars) == len(set(port_env_vars)), \
        "All port environment variable names should be unique"


def test_services_count_and_ports(temp_dir: Path) -> None:
    """Test that we have exactly 3 services with 3 unique ports."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_file, _ = generator.generate_to_file(temp_dir)

    # Parse YAML
    with open(compose_file, "r") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})

    # Verify we have 3 services
    assert len(services) >= 3, \
        f"Expected at least 3 services, found {len(services)}: {list(services.keys())}"

    # Count services with port mappings
    services_with_ports = [name for name, config in services.items() if "ports" in config]

    assert len(services_with_ports) >= 3, \
        f"Expected at least 3 services with ports, found {len(services_with_ports)}: {services_with_ports}"


def test_port_mapping_format_consistency(temp_dir: Path) -> None:
    """Test that all port mappings use consistent format with environment variables."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Find all port mapping lines
    # Pattern: lines containing port mappings with env vars
    port_lines = [line for line in compose_content.split('\n')
                  if '${' in line and '_PORT:-' in line and ':' in line]

    # Verify we found port mappings
    assert len(port_lines) >= 3, \
        f"Expected at least 3 port mappings, found {len(port_lines)}"

    # Verify format: "${VAR:-PORT}:PORT"
    port_mapping_pattern = r'"\$\{[A-Z_]+_PORT:-(\d+)\}:\1"'

    for line in port_lines:
        match = re.search(port_mapping_pattern, line)
        assert match, \
            f"Port mapping should follow format '${{VAR:-PORT}}:PORT', found: {line.strip()}"


def test_default_ports_are_documented(temp_dir: Path) -> None:
    """Test that the default port assignments are clearly documented in comments."""
    # Generate docker-compose.yaml
    generator = DockerComposeGenerator()
    compose_content = generator.generate()

    # Expected documentation format
    expected_docs = [
        ("PostgreSQL", "5432"),
        ("Redis", "6379"),
        ("Backend", "8000"),
    ]

    for service_name, port in expected_docs:
        # Check for comment mentioning the port and default
        # Should have format like "# PostgreSQL port - default: 5432"
        assert f"default: {port}" in compose_content, \
            f"Port {port} for {service_name} should be documented as default"
