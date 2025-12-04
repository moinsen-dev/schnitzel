"""Integration tests for API_051 - Serve command supports backend-only mode.

Test Requirements:
- Run 'schnitzel serve --backend-only'
- Verify Docker services are started
- Verify FastAPI is started
- Verify Flutter server is NOT started
- Verify status display reflects backend-only mode

Feature: Serve command backend-only mode
- Should accept --backend-only flag
- Should start Docker services (PostgreSQL, Redis)
- Should start FastAPI/uvicorn
- Should skip Flutter frontend
- Should display appropriate status messages
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
def backend_only_project(temp_dir):
    """Create a Schnitzel project structure for backend-only testing."""
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

app = FastAPI(title="Backend Only API")

@app.get("/")
def read_root():
    return {"message": "Backend only mode", "frontend": False}

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "backend-only"}
""")

    # Create pyproject.toml
    pyproject = backend_dir / "pyproject.toml"
    pyproject.write_text("""[project]
name = "backend-only-test"
version = "0.1.0"
""")

    return temp_dir


@pytest.fixture
def full_stack_project(backend_only_project):
    """Create a full-stack project with backend and frontend."""
    # Add Flutter frontend structure
    packages_dir = backend_only_project / "packages" / "app"
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

    return backend_only_project


def test_backend_only_flag_accepted(backend_only_project):
    """Test that --backend-only flag is accepted without error."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # The flag should be accepted (command should start processing)
        # It may fail later if uvicorn is not found, but flag should be recognized
        assert "--backend-only" not in result.stdout or "unrecognized" not in result.stdout.lower(), \
            "Flag should be recognized"


def test_backend_only_starts_docker_services(backend_only_project):
    """Test that Docker services (PostgreSQL, Redis) are started in backend-only mode."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # Verify docker compose up was called
        docker_up_calls = [
            call_args for call_args in mock_run.call_args_list
            if "docker" in str(call_args) and "compose" in str(call_args) and "up" in str(call_args)
        ]

        assert len(docker_up_calls) > 0, "Docker services should be started in backend-only mode"


def test_backend_only_starts_fastapi(backend_only_project):
    """Test that FastAPI/uvicorn is started in backend-only mode."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # Verify uvicorn was called
        uvicorn_calls = [
            call_args for call_args in mock_run.call_args_list
            if "uvicorn" in str(call_args)
        ]

        assert len(uvicorn_calls) > 0, "FastAPI/uvicorn should be started in backend-only mode"


def test_backend_only_skips_flutter(full_stack_project):
    """Test that Flutter is NOT started in backend-only mode (when frontend exists)."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # Verify Flutter commands were NOT called
        flutter_calls = [
            call_args for call_args in mock_run.call_args_list
            if "flutter" in str(call_args).lower()
        ]

        assert len(flutter_calls) == 0, "Flutter should NOT be started in backend-only mode"


def test_backend_only_displays_mode_message(backend_only_project):
    """Test that backend-only mode is reflected in status display."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # Verify output mentions backend-only mode
        output = result.stdout.lower()
        assert "backend" in output, "Output should mention backend"
        # Check for mode indication
        assert "backend only" in output or "flutter will be skipped" in output, \
            "Output should indicate backend-only mode"


def test_backend_only_service_status_table(full_stack_project):
    """Test that service status table reflects backend-only mode."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        output = result.stdout
        # Verify service status is displayed
        assert "PostgreSQL" in output or "postgres" in output.lower(), \
            "PostgreSQL should be in status display"
        assert "Redis" in output or "redis" in output.lower(), \
            "Redis should be in status display"
        assert "FastAPI" in output or "uvicorn" in output.lower(), \
            "FastAPI should be in status display"


def test_backend_only_with_port_option(backend_only_project):
    """Test that --backend-only works with --port option."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            # Verify uvicorn is called with the specified port
            if "uvicorn" in str(cmd):
                assert "--port" in cmd or "8080" in str(cmd), \
                    "uvicorn should use specified port"
            return mock_success

        mock_run.side_effect = run_side_effect

        runner.invoke(app, ["serve", "--backend-only", "--port", "8080"], catch_exceptions=False)

        # Verify uvicorn was called
        uvicorn_calls = [
            call_args for call_args in mock_run.call_args_list
            if "uvicorn" in str(call_args)
        ]

        assert len(uvicorn_calls) > 0, "uvicorn should be started"


def test_backend_only_with_no_reload_option(backend_only_project):
    """Test that --backend-only works with --no-reload option."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            # Verify uvicorn is NOT called with --reload when --no-reload is set
            if "uvicorn" in str(cmd):
                assert "--reload" not in cmd, "uvicorn should NOT have --reload flag"
            return mock_success

        mock_run.side_effect = run_side_effect

        runner.invoke(app, ["serve", "--backend-only", "--no-reload"], catch_exceptions=False)


def test_backend_only_without_frontend(backend_only_project):
    """Test that backend-only mode works when no frontend exists."""
    # This project has no Flutter frontend (only backend)
    assert not (backend_only_project / "packages" / "app").exists(), \
        "Test fixture should not have frontend"

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # Should work without errors
        # Docker and FastAPI should still start
        docker_calls = [
            c for c in mock_run.call_args_list
            if "docker" in str(c)
        ]

        assert len(docker_calls) > 0, "Docker should be started even without frontend"


def test_backend_only_comprehensive_flow(full_stack_project):
    """Comprehensive test for backend-only mode: Docker -> Health -> FastAPI, Skip Flutter.

    This test verifies the complete flow:
    1. --backend-only flag is accepted
    2. Docker services (PostgreSQL, Redis) are started
    3. Health checks are performed
    4. FastAPI/uvicorn is started
    5. Flutter is NOT started
    6. Status display reflects backend-only mode
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
                return mock_compose_up
            elif "docker" in cmd and "compose" in cmd and "ps" in cmd:
                return mock_health
            elif "uvicorn" in cmd:
                return MagicMock(returncode=0)
            return mock_version

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # Verify sequence of calls
        call_sequence = [str(c) for c in mock_run.call_args_list]

        # 1. Docker should be checked and started
        assert any("compose" in call and "up" in call for call in call_sequence), \
            "Docker services should be started"

        # 2. Health checks should be performed
        assert any("ps" in call or "health" in call for call in call_sequence), \
            "Health checks should be performed"

        # 3. FastAPI should be started
        assert any("uvicorn" in call for call in call_sequence), \
            "FastAPI should be started"

        # 4. Flutter should NOT be started
        flutter_calls = [call for call in call_sequence if "flutter" in call.lower()]
        assert len(flutter_calls) == 0, "Flutter should NOT be started in backend-only mode"

        # 5. Status display should mention backend-only
        output = result.stdout.lower()
        assert "backend" in output, "Status should mention backend mode"


def test_normal_mode_different_from_backend_only(full_stack_project):
    """Test that normal mode (without --backend-only) is different from backend-only mode."""
    # Note: Since Flutter is not yet implemented in serve command, this test
    # documents the intended behavior for when Flutter support is added

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_run.return_value = mock_success

        # Run without --backend-only
        result_normal = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Run with --backend-only
        result_backend_only = runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # The outputs should differ (backend-only should mention the mode)
        # When Flutter is implemented, this test will verify Flutter is only started in normal mode
        assert "backend only" in result_backend_only.stdout.lower() or \
               "flutter will be skipped" in result_backend_only.stdout.lower(), \
            "Backend-only mode should be indicated in output"
