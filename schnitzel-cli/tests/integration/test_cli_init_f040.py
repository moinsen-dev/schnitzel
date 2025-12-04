"""Integration tests for F040 - Init command creates project directory structure.

Test Requirements:
- test_init_creates_project_directory
- test_init_creates_packages_directory
- test_init_creates_backend_directory
- test_init_uses_project_name
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
import pytest

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


def test_init_creates_project_directory(temp_dir: Path) -> None:
    """Test that init command creates the project directory."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify project directory was created
    project_path = temp_dir / project_name
    assert project_path.exists(), f"Project directory not created at {project_path}"
    assert project_path.is_dir(), "Project path is not a directory"


def test_init_creates_packages_directory(temp_dir: Path) -> None:
    """Test that init command creates the packages/app directory structure."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify packages/app directory exists
    packages_dir = temp_dir / project_name / "packages"
    app_dir = packages_dir / "app"

    assert packages_dir.exists(), "packages/ directory not created"
    assert packages_dir.is_dir(), "packages/ is not a directory"
    assert app_dir.exists(), "packages/app/ directory not created"
    assert app_dir.is_dir(), "packages/app/ is not a directory"


def test_init_creates_backend_directory(temp_dir: Path) -> None:
    """Test that init command creates the backend/app directory structure."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify backend/app directory exists
    backend_dir = temp_dir / project_name / "backend"
    app_dir = backend_dir / "app"

    assert backend_dir.exists(), "backend/ directory not created"
    assert backend_dir.is_dir(), "backend/ is not a directory"
    assert app_dir.exists(), "backend/app/ directory not created"
    assert app_dir.is_dir(), "backend/app/ is not a directory"


def test_init_uses_project_name(temp_dir: Path) -> None:
    """Test that init command uses the provided project name correctly."""
    project_name = "my-custom-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify project was created with correct name
    project_path = temp_dir / project_name
    assert project_path.exists(), f"Project directory not created with name {project_name}"

    # Verify schema file exists
    schema_file = project_path / "schema.schnitzel.yaml"
    assert schema_file.exists(), "schema.schnitzel.yaml not created"
    assert schema_file.is_file(), "schema.schnitzel.yaml is not a file"

    # Verify docker-compose file exists
    docker_compose_file = project_path / "docker-compose.yaml"
    assert docker_compose_file.exists(), "docker-compose.yaml not created"
    assert docker_compose_file.is_file(), "docker-compose.yaml is not a file"


def test_init_creates_schema_file_with_content(temp_dir: Path) -> None:
    """Test that schema.schnitzel.yaml is created with valid content."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Verify schema file has content
    schema_file = temp_dir / project_name / "schema.schnitzel.yaml"
    content = schema_file.read_text()

    # Check for either version format (old: "version:", new: "schnitzel:")
    assert "version:" in content or "schnitzel:" in content, "Schema file missing version field"
    assert "models:" in content, "Schema file missing models field"


def test_init_creates_docker_compose_with_content(temp_dir: Path) -> None:
    """Test that docker-compose.yaml is created with valid content."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Verify docker-compose file has content
    docker_compose_file = temp_dir / project_name / "docker-compose.yaml"
    content = docker_compose_file.read_text()

    assert "version:" in content, "Docker compose missing version"
    assert "services:" in content, "Docker compose missing services"
    assert "backend:" in content, "Docker compose missing backend service"
    assert "db:" in content, "Docker compose missing db service"


def test_init_fails_if_directory_exists(temp_dir: Path) -> None:
    """Test that init command fails if project directory already exists."""
    project_name = "existing-project"
    existing_dir = temp_dir / project_name
    existing_dir.mkdir()

    # Run init command
    result = runner.invoke(app, ["init", project_name])

    # Verify command failed
    assert result.exit_code == 1, "Command should fail when directory exists"
    assert "already exists" in result.stdout.lower(), "Error message should mention directory exists"


def test_init_creates_readme_files(temp_dir: Path) -> None:
    """Test that README files are created in packages/app and backend/app."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Verify README files exist
    packages_readme = temp_dir / project_name / "packages" / "app" / "README.md"
    backend_readme = temp_dir / project_name / "backend" / "app" / "README.md"

    assert packages_readme.exists(), "packages/app/README.md not created"
    assert backend_readme.exists(), "backend/app/README.md not created"

    # Verify README files have content
    assert len(packages_readme.read_text()) > 0, "packages README is empty"
    assert len(backend_readme.read_text()) > 0, "backend README is empty"


def test_init_output_shows_success_message(temp_dir: Path) -> None:
    """Test that init command outputs a success message."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Verify success message
    output = result.stdout.lower()
    assert "created successfully" in output or "✓" in output, "Missing success message"
    assert project_name in output, "Success message should mention project name"


def test_init_output_shows_next_steps(temp_dir: Path) -> None:
    """Test that init command outputs next steps guidance."""
    project_name = "test-project"

    # Run init command
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0

    # Verify next steps are shown
    output = result.stdout.lower()
    assert "next steps" in output or "cd " in output, "Missing next steps guidance"
