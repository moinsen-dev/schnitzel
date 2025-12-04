"""Integration tests for F119 - docker-compose.yaml follows YAML best practices.

Test Requirements:
- test_yaml_valid_syntax - Verify YAML is syntactically valid
- test_yaml_consistent_indentation - Verify consistent 2-space indentation
- test_yaml_readable_structure - Verify clear structure with sections
- test_yaml_comments - Verify helpful comments are included
- test_no_tabs - Verify no tabs in YAML (spaces only)
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


def test_yaml_valid_syntax(temp_dir: Path) -> None:
    """Test that generated docker-compose.yaml is syntactically valid."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    assert docker_file.exists()

    content = docker_file.read_text()

    # Should be valid YAML
    try:
        parsed = yaml.safe_load(content)
        assert parsed is not None, "YAML should parse to a non-None value"
        assert isinstance(parsed, dict), "Root should be a dictionary"
    except yaml.YAMLError as e:
        pytest.fail(f"Generated YAML is invalid: {e}")


def test_yaml_consistent_indentation(temp_dir: Path) -> None:
    """Test that YAML uses consistent 2-space indentation."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()
    lines = content.split("\n")

    # Check indentation levels
    indented_lines = [line for line in lines if line.startswith(" ") and line.strip()]

    for i, line in enumerate(indented_lines):
        # Count leading spaces
        spaces = len(line) - len(line.lstrip())
        # Should be multiple of 2 (YAML standard indentation)
        assert spaces % 2 == 0, \
            f"Line {i} has {spaces} spaces, should be multiple of 2: '{line}'"


def test_no_tabs(temp_dir: Path) -> None:
    """Test that YAML uses spaces, not tabs."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()
    lines = content.split("\n")

    # Check for tabs
    tab_lines = [i + 1 for i, line in enumerate(lines) if "\t" in line]

    assert len(tab_lines) == 0, \
        f"Found tabs on lines: {tab_lines}. YAML should use spaces, not tabs."


def test_yaml_readable_structure(temp_dir: Path) -> None:
    """Test that YAML has clear, readable structure."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()

    # Parse YAML
    parsed = yaml.safe_load(content)

    # Should have key sections
    assert "version" in parsed, "Should have version field"
    assert "services" in parsed, "Should have services section"

    # Services should include standard services
    services = parsed["services"]
    assert "db" in services, "Should have database service"
    assert "backend" in services, "Should have backend service"


def test_yaml_comments(temp_dir: Path) -> None:
    """Test that YAML includes helpful comments."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Customer:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()

    # Should have comments
    assert "#" in content, "Should include YAML comments"

    # Count comment lines
    lines = content.split("\n")
    comment_lines = [line for line in lines if line.strip().startswith("#")]

    # Should have at least some comments for documentation
    assert len(comment_lines) >= 3, \
        f"Should have helpful comments, found only {len(comment_lines)}"


def test_service_configuration_complete(temp_dir: Path) -> None:
    """Test that service configurations are complete and well-formed."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Event:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()
    parsed = yaml.safe_load(content)

    # Check database service configuration
    db_service = parsed["services"]["db"]
    assert "image" in db_service, "Database should specify image"
    assert "environment" in db_service, "Database should have environment vars"
    assert "ports" in db_service, "Database should expose ports"
    assert "healthcheck" in db_service, "Database should have healthcheck"

    # Check backend service configuration
    backend_service = parsed["services"]["backend"]
    assert "build" in backend_service or "image" in backend_service, \
        "Backend should specify build or image"
    assert "depends_on" in backend_service, "Backend should depend on database"
    assert "environment" in backend_service, "Backend should have environment vars"


def test_healthcheck_present(temp_dir: Path) -> None:
    """Test that services have proper healthcheck configuration."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()
    parsed = yaml.safe_load(content)

    # Database should have healthcheck
    db_service = parsed["services"]["db"]
    assert "healthcheck" in db_service, "Database service should have healthcheck"

    healthcheck = db_service["healthcheck"]
    assert "test" in healthcheck, "Healthcheck should have test command"
    assert "interval" in healthcheck, "Healthcheck should have interval"
    assert "timeout" in healthcheck, "Healthcheck should have timeout"
    assert "retries" in healthcheck, "Healthcheck should have retries"


def test_environment_variables_documented(temp_dir: Path) -> None:
    """Test that environment variables are documented with comments."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Article:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()

    # Should have comments explaining environment variables
    lines = content.split("\n")

    # Find environment sections
    in_env_section = False
    env_comments = 0

    for line in lines:
        if "environment:" in line:
            in_env_section = True
        elif in_env_section:
            if line.strip().startswith("#"):
                env_comments += 1
            elif line and not line.startswith(" "):
                in_env_section = False

    # Should have some comments in environment sections
    assert env_comments > 0, "Environment variables should be documented with comments"


def test_volumes_configured(temp_dir: Path) -> None:
    """Test that volumes are properly configured."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Note:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()
    parsed = yaml.safe_load(content)

    # Should have volumes section
    assert "volumes" in parsed, "Should have volumes section"

    # Database service should use volume
    db_service = parsed["services"]["db"]
    assert "volumes" in db_service, "Database service should have volumes"


def test_port_format_correct(temp_dir: Path) -> None:
    """Test that port mappings are in correct format."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Message:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.yaml"
    schema_file.write_text(schema_content)

    # Run generate command
    result = runner.invoke(app, ["generate", str(schema_file), "--target", "docker"])
    assert result.exit_code == 0

    # Read generated docker-compose.yaml
    docker_file = temp_dir / "docker-compose.yaml"
    content = docker_file.read_text()
    parsed = yaml.safe_load(content)

    # Check port format
    for service_name, service_config in parsed["services"].items():
        if "ports" in service_config:
            ports = service_config["ports"]
            assert isinstance(ports, list), f"{service_name} ports should be a list"

            for port in ports:
                # Should be string format "host:container"
                assert isinstance(port, str), \
                    f"Port mapping should be string, got {type(port)}"
