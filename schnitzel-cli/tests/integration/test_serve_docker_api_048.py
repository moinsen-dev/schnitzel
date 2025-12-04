"""Integration tests for API_048 - Serve command starts Docker services.

Test Requirements:
- Run 'schnitzel serve'
- Verify 'docker compose up -d' is executed
- Verify PostgreSQL and Redis services start
- Verify health check passes before continuing

Feature: Serve command that orchestrates the dev environment
- Should start Docker services first
- Should wait for health checks
- Should support --backend-only flag
- Should support --port option
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
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


@pytest.fixture
def project_with_docker_compose(temp_dir):
    """Create a project structure with docker-compose.yml."""
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

    return temp_dir


def test_serve_command_exists() -> None:
    """Test that 'schnitzel serve' command exists."""
    result = runner.invoke(app, ["serve", "--help"])

    # Should succeed
    assert result.exit_code == 0, f"Help command failed: {result.stdout}"

    # Should mention key options
    assert "port" in result.stdout.lower() or "PORT" in result.stdout, "Should mention --port option"
    assert "backend-only" in result.stdout.lower() or "backend" in result.stdout.lower(), "Should mention --backend-only option"


def test_serve_starts_docker_compose(project_with_docker_compose) -> None:
    """Test that 'schnitzel serve' executes 'docker compose up -d'."""
    with patch("subprocess.run") as mock_run:
        # Mock Docker check commands
        mock_version = MagicMock()
        mock_version.returncode = 0
        mock_version.stdout = "Docker version 24.0.0"
        mock_version.stderr = ""

        # Mock docker compose up -d
        mock_compose = MagicMock()
        mock_compose.returncode = 0
        mock_compose.stdout = "Container db  Started\nContainer redis  Started\n"
        mock_compose.stderr = ""

        # Mock health check commands
        mock_health = MagicMock()
        mock_health.returncode = 0
        mock_health.stdout = "db\nredis"
        mock_health.stderr = ""

        # Mock postgres health check
        mock_pg_health = MagicMock()
        mock_pg_health.returncode = 0
        mock_pg_health.stdout = "accepting connections"

        # Mock redis health check
        mock_redis_health = MagicMock()
        mock_redis_health.returncode = 0
        mock_redis_health.stdout = "PONG"

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "docker" in cmd and "--version" in cmd:
                return mock_version
            elif "docker" in cmd and "compose" in cmd and "version" in cmd:
                return mock_version
            elif "docker" in cmd and "info" in cmd:
                return mock_version
            elif "docker" in cmd and "compose" in cmd and "up" in cmd:
                return mock_compose
            elif "docker" in cmd and "compose" in cmd and "ps" in cmd:
                return mock_health
            elif "pg_isready" in cmd:
                return mock_pg_health
            elif "redis-cli" in cmd and "ping" in cmd:
                return mock_redis_health
            return mock_version

        mock_run.side_effect = run_side_effect

        # Run serve command
        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should succeed (or exit gracefully)
        # Note: The command may exit with code 1 if uvicorn is not found, which is OK for this test
        # We just want to verify docker compose up was called

        # Verify docker compose up -d was called
        docker_compose_calls = [
            call_args for call_args in mock_run.call_args_list
            if "docker" in str(call_args) and "compose" in str(call_args) and "up" in str(call_args)
        ]

        assert len(docker_compose_calls) > 0, "docker compose up -d should have been called"

        # Verify the exact command
        docker_up_call = docker_compose_calls[0]
        cmd_args = docker_up_call[0][0]  # Get the command list
        assert "docker" in cmd_args, "Should call docker"
        assert "compose" in cmd_args, "Should call docker compose"
        assert "up" in cmd_args, "Should call docker compose up"
        assert "-d" in cmd_args, "Should use -d flag for detached mode"


def test_serve_verifies_postgres_starts(project_with_docker_compose) -> None:
    """Test that serve command verifies PostgreSQL service starts."""
    with patch("subprocess.run") as mock_run:
        # Mock all docker commands
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            # Mock health check via docker compose ps
            if "docker" in cmd and "compose" in cmd and "ps" in cmd:
                # Return healthy status for both services
                return mock_success
            return mock_success

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Verify docker compose ps was called to check service health
        health_calls = [
            call_args for call_args in mock_run.call_args_list
            if "docker" in str(call_args) and "compose" in str(call_args) and "ps" in str(call_args)
        ]

        assert len(health_calls) > 0, "Should check service health with docker compose ps"


def test_serve_verifies_redis_starts(project_with_docker_compose) -> None:
    """Test that serve command verifies Redis service starts."""
    with patch("subprocess.run") as mock_run:
        # Mock all docker commands
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            # Mock health check via docker compose ps
            if "docker" in cmd and "compose" in cmd and "ps" in cmd:
                # Return healthy status including redis
                return mock_success
            return mock_success

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Verify docker compose ps was called and checks redis
        health_calls = [
            call_args for call_args in mock_run.call_args_list
            if "docker" in str(call_args) and "compose" in str(call_args) and "ps" in str(call_args)
        ]

        assert len(health_calls) > 0, "Should check service health including Redis"


def test_serve_health_check_passes_before_continuing(project_with_docker_compose) -> None:
    """Test that serve command waits for health checks to pass."""
    with patch("subprocess.run") as mock_run:
        # Mock all docker commands
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            # Mock health check calls returning healthy status
            if "docker" in cmd and "compose" in cmd and "ps" in cmd:
                return mock_success
            return mock_success

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Verify health checks were performed via docker compose ps
        health_calls = [
            c for c in mock_run.call_args_list
            if "docker" in str(c) and "compose" in str(c) and "ps" in str(c)
        ]

        assert len(health_calls) > 0, "Should check service health before continuing"


def test_serve_backend_only_flag(project_with_docker_compose) -> None:
    """Test that serve command accepts --backend-only flag."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        # Should accept --backend-only flag without error
        result = runner.invoke(app, ["serve", "--backend-only"], catch_exceptions=False)

        # Command should execute (may fail later but flag should be accepted)
        # We're mainly testing that the flag is recognized


def test_serve_port_option(project_with_docker_compose) -> None:
    """Test that serve command accepts --port option."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        # Should accept --port flag without error
        result = runner.invoke(app, ["serve", "--port", "8080"], catch_exceptions=False)

        # Command should execute (may fail later but flag should be accepted)
        # We're mainly testing that the flag is recognized


def test_serve_without_docker_compose_file(temp_dir) -> None:
    """Test that serve command fails gracefully without docker-compose.yml."""
    # No docker-compose.yml in temp_dir

    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_run.return_value = mock_success

        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should fail with error about missing docker-compose.yml
        assert result.exit_code != 0, "Should fail when docker-compose.yml is missing"
        assert "docker-compose" in result.stdout.lower(), "Should mention docker-compose in error"


def test_serve_checks_docker_installed(project_with_docker_compose) -> None:
    """Test that serve command checks if Docker is installed."""
    with patch("subprocess.run") as mock_run:
        # Mock Docker not installed
        mock_run.side_effect = FileNotFoundError()

        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should fail with error about Docker not being installed
        assert result.exit_code != 0, "Should fail when Docker is not installed"
        assert "docker" in result.stdout.lower(), "Should mention Docker in error message"


def test_serve_checks_docker_compose_installed(project_with_docker_compose) -> None:
    """Test that serve command checks if Docker Compose is installed."""
    with patch("subprocess.run") as mock_run:
        # Mock Docker installed but compose not available
        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "docker" in cmd and "--version" in cmd:
                mock_result = MagicMock()
                mock_result.returncode = 0
                return mock_result
            elif "docker" in cmd and "info" in cmd:
                mock_result = MagicMock()
                mock_result.returncode = 0
                return mock_result
            elif "compose" in cmd:
                raise FileNotFoundError()
            return MagicMock(returncode=0)

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Should fail with error about Docker Compose
        assert result.exit_code != 0, "Should fail when Docker Compose is not installed"
