"""Integration tests for F047 - Init command generates backend pyproject.toml with dependencies.

Test Requirements:
- test_backend_has_pyproject_toml
- test_pyproject_has_fastapi_dependency
- test_pyproject_has_sqlalchemy_dependency
- test_pyproject_uses_project_name
"""

import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
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


def test_backend_has_pyproject_toml(temp_dir: Path) -> None:
    """Test that init command with --with-backend creates pyproject.toml."""
    project_name = "test-project"

    # Mock subprocess.run to simulate successful uv execution
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # Mock uv --version check (first call)
        # Mock uv init (second call)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),  # uv --version
            MagicMock(returncode=0, stdout="Initialized project", stderr="")  # uv init
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        # Verify command succeeded
        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Verify pyproject.toml was created
        pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
        assert pyproject_file.exists(), "pyproject.toml should exist in backend/app/"
        assert pyproject_file.is_file(), "pyproject.toml should be a file"


def test_pyproject_has_fastapi_dependency(temp_dir: Path) -> None:
    """Test that pyproject.toml includes FastAPI dependency."""
    project_name = "test-project"

    # Mock subprocess.run to simulate successful uv execution
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),
            MagicMock(returncode=0, stdout="Initialized project", stderr="")
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Read and verify pyproject.toml content
        pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
        content = pyproject_file.read_text()

        # Verify FastAPI dependency is present
        assert "fastapi" in content.lower(), "pyproject.toml should include fastapi dependency"
        assert "fastapi>=0.109.0" in content, "FastAPI should have version constraint"


def test_pyproject_has_sqlalchemy_dependency(temp_dir: Path) -> None:
    """Test that pyproject.toml includes SQLAlchemy dependency."""
    project_name = "test-project"

    # Mock subprocess.run to simulate successful uv execution
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),
            MagicMock(returncode=0, stdout="Initialized project", stderr="")
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Read and verify pyproject.toml content
        pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
        content = pyproject_file.read_text()

        # Verify SQLAlchemy dependency is present
        assert "sqlalchemy" in content.lower(), "pyproject.toml should include sqlalchemy dependency"
        assert "sqlalchemy>=2.0.0" in content, "SQLAlchemy should have version constraint"


def test_pyproject_uses_project_name(temp_dir: Path) -> None:
    """Test that pyproject.toml uses project name in package naming."""
    project_name = "my-awesome-app"

    # Mock subprocess.run to simulate successful uv execution
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),
            MagicMock(returncode=0, stdout="Initialized project", stderr="")
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Read and verify pyproject.toml content
        pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
        content = pyproject_file.read_text()

        # Verify project name is used in package name
        assert f'name = "{project_name}-backend"' in content, "Package name should use project name"
        assert f'description = "FastAPI backend for {project_name}"' in content, "Description should include project name"


def test_pyproject_has_all_required_dependencies(temp_dir: Path) -> None:
    """Test that pyproject.toml includes all required dependencies."""
    project_name = "test-project"

    # Mock subprocess.run to simulate successful uv execution
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),
            MagicMock(returncode=0, stdout="Initialized project", stderr="")
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Read and verify pyproject.toml content
        pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
        content = pyproject_file.read_text()

        # Verify all required dependencies are present
        required_deps = [
            "fastapi>=0.109.0",
            "uvicorn[standard]>=0.27.0",
            "sqlalchemy>=2.0.0",
            "pydantic>=2.0.0",
            "alembic>=1.13.0",
            "psycopg2-binary>=2.9.0",
        ]

        for dep in required_deps:
            assert dep in content, f"pyproject.toml should include {dep}"


def test_pyproject_has_correct_python_version(temp_dir: Path) -> None:
    """Test that pyproject.toml specifies correct Python version."""
    project_name = "test-project"

    # Mock subprocess.run to simulate successful uv execution
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),
            MagicMock(returncode=0, stdout="Initialized project", stderr="")
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Read and verify pyproject.toml content
        pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
        content = pyproject_file.read_text()

        # Verify Python version requirement
        assert "requires-python" in content, "pyproject.toml should specify Python version"
        assert ">=3.11" in content, "Python version should be >=3.11"


def test_pyproject_has_build_system(temp_dir: Path) -> None:
    """Test that pyproject.toml includes build system configuration."""
    project_name = "test-project"

    # Mock subprocess.run to simulate successful uv execution
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),
            MagicMock(returncode=0, stdout="Initialized project", stderr="")
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Read and verify pyproject.toml content
        pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
        content = pyproject_file.read_text()

        # Verify build system configuration
        assert "[build-system]" in content, "pyproject.toml should include [build-system] section"
        assert "hatchling" in content, "Build system should use hatchling"


def test_pyproject_created_when_uv_init_fails(temp_dir: Path) -> None:
    """Test that pyproject.toml is created even when uv init fails."""
    project_name = "test-project"

    # Mock subprocess.run to simulate uv init failure
    with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
        # Mock successful version check but failed uv init
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),  # uv --version
            MagicMock(returncode=1, stdout="", stderr="Error: failed to init")  # uv init fails
        ]

        # Run init command with --with-backend flag
        result = runner.invoke(app, ["init", project_name, "--with-backend"])

        # Verify command succeeded (continues with fallback)
        assert result.exit_code == 0, f"Command should succeed with fallback: {result.stdout}"

        # Verify pyproject.toml was still created
        pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
        assert pyproject_file.exists(), "pyproject.toml should exist even when uv init fails"

        # Verify content is correct
        content = pyproject_file.read_text()
        assert "fastapi>=0.109.0" in content, "pyproject.toml should have FastAPI dependency"


def test_pyproject_not_created_without_backend_flag(temp_dir: Path) -> None:
    """Test that pyproject.toml is not created when --with-backend is not used."""
    project_name = "test-project"

    # Run init command without --with-backend flag
    result = runner.invoke(app, ["init", project_name])

    # Verify command succeeded
    assert result.exit_code == 0, f"Command failed: {result.stdout}"

    # Verify pyproject.toml was NOT created
    pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
    assert not pyproject_file.exists(), "pyproject.toml should not exist without --with-backend flag"


def test_pyproject_with_different_project_names(temp_dir: Path) -> None:
    """Test that pyproject.toml correctly uses various project names."""
    test_cases = [
        "simple-name",
        "complex_project_123",
        "My-Project",
    ]

    for project_name in test_cases:
        # Clean up before each test
        project_dir = temp_dir / project_name
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)

        # Mock subprocess.run to simulate successful uv execution
        with patch('schnitzel.cli.commands.init.subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="uv 0.1.0", stderr=""),
                MagicMock(returncode=0, stdout="Initialized project", stderr="")
            ]

            # Run init command with --with-backend flag
            result = runner.invoke(app, ["init", project_name, "--with-backend"])

            assert result.exit_code == 0, f"Command failed for {project_name}: {result.stdout}"

            # Read and verify pyproject.toml content
            pyproject_file = temp_dir / project_name / "backend" / "app" / "pyproject.toml"
            content = pyproject_file.read_text()

            # Verify project name is used
            assert f'name = "{project_name}-backend"' in content, f"Package name should use {project_name}"
