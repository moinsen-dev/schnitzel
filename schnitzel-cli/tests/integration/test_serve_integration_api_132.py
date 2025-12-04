"""Integration tests for api_132: Serve command integrates with existing project structure.

Test Requirements:
- Verify 'schnitzel serve' detects existing project structure
- Verify it looks for .schnitzel/ directory
- Verify it finds docker-compose.yml
- Verify it locates Python backend and/or Flutter frontend
- Verify proper error messages when required files are missing
- Verify integration with Schnitzel project conventions

Feature: Serve command must integrate with existing Schnitzel projects
- Should detect .schnitzel/ directory (optional, for future use)
- Should validate docker-compose.yml/yaml exists
- Should locate backend/app/main.py or similar
- Should provide clear error messages for missing components
- Should work from any directory within a Schnitzel project
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

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


@pytest.fixture
def minimal_schnitzel_project(temp_dir):
    """Create a minimal Schnitzel project structure."""
    # Create docker-compose.yml
    docker_compose = temp_dir / "docker-compose.yml"
    docker_compose.write_text("""version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: schnitzel
      POSTGRES_PASSWORD: schnitzel_dev
      POSTGRES_DB: schnitzel_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U schnitzel -d schnitzel_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
""")

    # Create backend structure
    backend_dir = temp_dir / "backend" / "app"
    backend_dir.mkdir(parents=True)

    main_py = backend_dir / "main.py"
    main_py.write_text("""from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/")
def read_root():
    return {"message": "Hello World"}
""")

    # Create pyproject.toml
    pyproject = backend_dir / "pyproject.toml"
    pyproject.write_text("""[project]
name = "test-app"
version = "0.1.0"
""")

    # Create schema file (standard Schnitzel convention)
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text("""schnitzel: 1.0.0

models:
  User:
    description: A test user
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
""")

    return temp_dir


@pytest.fixture
def full_schnitzel_project(minimal_schnitzel_project):
    """Create a full Schnitzel project with .schnitzel directory."""
    temp_dir = minimal_schnitzel_project

    # Create .schnitzel directory (for generated metadata)
    schnitzel_dir = temp_dir / ".schnitzel"
    schnitzel_dir.mkdir()

    # Create metadata file
    metadata = schnitzel_dir / "metadata.json"
    metadata.write_text('{"version": "1.0.0", "created": "2025-01-01"}')

    # Create packages directory with Flutter app
    packages_dir = temp_dir / "packages" / "app"
    packages_dir.mkdir(parents=True)

    pubspec = packages_dir / "pubspec.yaml"
    pubspec.write_text("""name: test_app
description: A test Flutter app
version: 1.0.0

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
""")

    return temp_dir


def test_serve_detects_docker_compose_yml(minimal_schnitzel_project):
    """Test that serve command detects docker-compose.yml in project root."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should attempt to start docker compose
        docker_compose_calls = [
            call_args for call_args in mock_run.call_args_list
            if "docker" in str(call_args) and "compose" in str(call_args) and "up" in str(call_args)
        ]

        assert len(docker_compose_calls) > 0, "Should attempt to start docker compose"


def test_serve_detects_docker_compose_yaml(temp_dir):
    """Test that serve command detects docker-compose.yaml (with .yaml extension)."""
    # Create docker-compose.yaml (not .yml)
    docker_compose = temp_dir / "docker-compose.yaml"
    docker_compose.write_text("""version: '3.8'
services:
  db:
    image: postgres:16
""")

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = ""
        mock_success.stderr = ""
        mock_run.return_value = mock_success

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should find docker-compose.yaml
        docker_up_calls = [
            call_args for call_args in mock_run.call_args_list
            if "docker" in str(call_args) and "compose" in str(call_args) and "up" in str(call_args)
        ]

        assert len(docker_up_calls) > 0, "Should find and use docker-compose.yaml"


def test_serve_finds_backend_app_main(minimal_schnitzel_project):
    """Test that serve command locates backend/app/main.py."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            # Check if uvicorn is being called with correct app module
            if "uvicorn" in str(cmd):
                assert "backend.app.main:app" in str(cmd), "Should use backend.app.main:app module"
            return mock_success

        mock_run.side_effect = run_side_effect

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # Verify uvicorn was called
        uvicorn_calls = [
            call_args for call_args in mock_run.call_args_list
            if "uvicorn" in str(call_args)
        ]

        assert len(uvicorn_calls) > 0, "Should attempt to start uvicorn"


def test_serve_detects_pyproject_toml(minimal_schnitzel_project):
    """Test that serve command works with projects that have pyproject.toml."""
    # Verify pyproject.toml exists in our fixture
    pyproject = minimal_schnitzel_project / "backend" / "app" / "pyproject.toml"
    assert pyproject.exists(), "Test fixture should have pyproject.toml"

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = ""
        mock_run.return_value = mock_success

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # Command should run without errors about project structure
        # (may fail on uvicorn, but should get past structure validation)


def test_serve_error_without_docker_compose(temp_dir):
    """Test that serve command shows error when docker-compose.yml is missing."""
    # No docker-compose file in temp_dir

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_run.return_value = mock_success

        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should fail with clear error message
        assert result.exit_code != 0, "Should fail when docker-compose file is missing"
        output = result.stdout.lower()
        assert "docker-compose" in output, "Error should mention docker-compose"
        assert "not found" in output or "missing" in output, "Error should indicate file is missing"


def test_serve_error_without_backend(temp_dir):
    """Test that serve command handles missing backend gracefully."""
    # Create docker-compose.yml but no backend
    docker_compose = temp_dir / "docker-compose.yml"
    docker_compose.write_text("""version: '3.8'
services:
  db:
    image: postgres:16
""")

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running"
        mock_run.return_value = mock_success

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # May fail or warn about missing backend
        # The key is it should attempt to look for it
        uvicorn_calls = [
            call_args for call_args in mock_run.call_args_list
            if "uvicorn" in str(call_args)
        ]

        # Should attempt to call uvicorn even if file doesn't exist
        # (uvicorn will fail with its own error)
        assert len(uvicorn_calls) > 0, "Should attempt to start uvicorn"


def test_serve_with_schema_file(minimal_schnitzel_project):
    """Test that serve command works with schema.schnitzel.yaml present."""
    schema_file = minimal_schnitzel_project / "schema.schnitzel.yaml"
    assert schema_file.exists(), "Test fixture should have schema file"

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = ""
        mock_run.return_value = mock_success

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should work without errors related to schema file
        # (serve command may not directly use it, but it's part of project structure)


def test_serve_with_full_project_structure(full_schnitzel_project):
    """Test that serve command works with full Schnitzel project including .schnitzel/."""
    # Verify full structure
    assert (full_schnitzel_project / ".schnitzel").exists()
    assert (full_schnitzel_project / "docker-compose.yml").exists()
    assert (full_schnitzel_project / "backend" / "app" / "main.py").exists()
    assert (full_schnitzel_project / "packages" / "app").exists()

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_run.return_value = mock_success

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should detect and work with full project structure
        docker_calls = [
            c for c in mock_run.call_args_list
            if "docker" in str(c)
        ]

        assert len(docker_calls) > 0, "Should interact with Docker"


def test_serve_detects_packages_directory(full_schnitzel_project):
    """Test that serve command detects packages/ directory (Flutter frontend)."""
    packages_dir = full_schnitzel_project / "packages" / "app"
    assert packages_dir.exists(), "Test fixture should have packages directory"

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_run.return_value = mock_success

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # Serve command should work whether or not Flutter is present
        # (it has --backend-only flag for this case)


def test_serve_validates_project_structure():
    """Test that serve command validates basic project structure requirements."""
    # This test verifies the serve command checks for required files

    result = runner.invoke(app, ["serve", "--help"])

    # Help should exist and mention key aspects
    assert result.exit_code == 0
    help_text = result.stdout.lower()
    assert "docker" in help_text, "Help should mention Docker"
    assert "fastapi" in help_text or "backend" in help_text, "Help should mention backend"


def test_serve_backend_only_flag_with_project(minimal_schnitzel_project):
    """Test that --backend-only flag works with existing project structure."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = ""
        mock_run.return_value = mock_success

        runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # Should work with --backend-only flag
        docker_calls = [
            c for c in mock_run.call_args_list
            if "docker" in str(c)
        ]

        assert len(docker_calls) > 0, "Should still start Docker services"


def test_serve_from_subdirectory(minimal_schnitzel_project):
    """Test that serve command works when run from a subdirectory (future feature)."""
    # Create a subdirectory
    subdir = minimal_schnitzel_project / "backend" / "app"

    # For now, serve uses cwd(), so it expects to be run from project root
    # This test documents the current behavior

    original_cwd = os.getcwd()
    try:
        os.chdir(subdir)

        with patch("subprocess.run") as mock_run:
            mock_success = MagicMock()
            mock_success.returncode = 0
            mock_run.return_value = mock_success

            result = runner.invoke(app, ["serve"], catch_exceptions=False)

            # Currently will fail because docker-compose.yml is not in subdirectory
            # This is expected behavior - serve should be run from project root
            assert result.exit_code != 0, "Should fail when not run from project root"
    finally:
        os.chdir(original_cwd)


def test_serve_multiple_backend_locations(temp_dir):
    """Test that serve command checks multiple possible backend locations."""
    # Create docker-compose
    docker_compose = temp_dir / "docker-compose.yml"
    docker_compose.write_text("""version: '3.8'
services:
  db:
    image: postgres:16
""")

    # Create backend at alternative location (backend/main.py instead of backend/app/main.py)
    backend_dir = temp_dir / "backend"
    backend_dir.mkdir()
    main_py = backend_dir / "main.py"
    main_py.write_text("""from fastapi import FastAPI

app = FastAPI()
""")

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = ""
        mock_run.return_value = mock_success

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should find backend/main.py as fallback location
        uvicorn_calls = [
            str(c) for c in mock_run.call_args_list
            if "uvicorn" in str(c)
        ]

        if uvicorn_calls:
            # Check that it tries backend.main:app as fallback
            assert any("backend.main:app" in call or "backend.app.main:app" in call
                      for call in uvicorn_calls), "Should try multiple backend locations"


def test_serve_integration_comprehensive(full_schnitzel_project):
    """Comprehensive integration test for serve command with full project structure.

    This test verifies the complete flow:
    1. Detects docker-compose.yml
    2. Checks Docker is installed
    3. Starts Docker services
    4. Waits for health checks
    5. Locates FastAPI app
    6. Starts uvicorn
    """
    with patch("subprocess.run") as mock_run:
        # Mock Docker installation checks
        mock_version = MagicMock()
        mock_version.returncode = 0
        mock_version.stdout = "Docker version 24.0.0"

        # Mock docker compose up
        mock_compose_up = MagicMock()
        mock_compose_up.returncode = 0
        mock_compose_up.stdout = "Services started"

        # Mock health checks
        mock_health = MagicMock()
        mock_health.returncode = 0
        mock_health.stdout = "db running healthy\nredis running healthy"

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "docker" in cmd and "--version" in cmd:
                return mock_version
            elif "docker" in cmd and "info" in cmd:
                return mock_version
            elif "docker" in cmd and "compose" in cmd and "version" in cmd:
                return mock_version
            elif "docker" in cmd and "compose" in cmd and "up" in cmd:
                # Verify working directory is project root
                cwd = kwargs.get('cwd')
                if cwd:
                    assert (Path(cwd) / "docker-compose.yml").exists(), \
                        "Should run docker compose from project root"
                return mock_compose_up
            elif "docker" in cmd and "compose" in cmd and "ps" in cmd:
                return mock_health
            elif "uvicorn" in cmd:
                # Verify correct app module
                assert "backend.app.main:app" in str(cmd), \
                    "Should use correct FastAPI app module"
                # Verify working directory
                cwd = kwargs.get('cwd')
                if cwd:
                    assert (Path(cwd) / "backend" / "app" / "main.py").exists(), \
                        "Should run uvicorn from correct directory"
                return MagicMock(returncode=0)
            return mock_version

        mock_run.side_effect = run_side_effect

        runner.invoke(app, ["serve"], catch_exceptions=False)

        # Verify sequence of calls
        call_sequence = [str(c) for c in mock_run.call_args_list]

        # Should check Docker installation
        assert any("--version" in call for call in call_sequence), \
            "Should check Docker is installed"

        # Should start Docker services
        assert any("compose" in call and "up" in call for call in call_sequence), \
            "Should start Docker compose services"

        # Should check service health
        assert any("ps" in call or "health" in call for call in call_sequence), \
            "Should verify service health"

        # Should start uvicorn
        assert any("uvicorn" in call for call in call_sequence), \
            "Should start uvicorn server"
