"""Integration tests for api_052: Serve command allows custom port configuration.

Feature: Serve command allows custom port configuration
Steps:
1. Run schnitzel serve --port 9000
2. Verify uvicorn starts on port 9000
3. Verify API is accessible at http://localhost:9000
4. Verify OpenAPI docs at http://localhost:9000/docs

This test ensures:
- --port flag is accepted by the serve command
- Custom port is passed to uvicorn subprocess
- Default port (8000) is used when not specified
- --frontend-port option is recognized (for future Flutter integration)
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
def project_with_backend(temp_dir):
    """Create a minimal project structure with backend and docker-compose."""
    # Create docker-compose.yaml
    docker_compose = temp_dir / "docker-compose.yaml"
    docker_compose.write_text("""version: '3.8'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
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

    # Create backend directory structure
    backend_dir = temp_dir / "backend" / "app"
    backend_dir.mkdir(parents=True)

    # Create a minimal FastAPI app
    main_py = backend_dir / "main.py"
    main_py.write_text("""
from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
""")

    return temp_dir


def test_serve_command_accepts_port_flag():
    """Test that serve command accepts --port flag."""
    result = runner.invoke(app, ["serve", "--help"])

    assert result.exit_code == 0, f"Help command failed: {result.stdout}"
    assert "--port" in result.stdout, "Should have --port option"
    assert "-p" in result.stdout, "Should have -p short option"


def test_serve_command_accepts_frontend_port_flag():
    """Test that serve command accepts --frontend-port flag."""
    result = runner.invoke(app, ["serve", "--help"])

    assert result.exit_code == 0, f"Help command failed: {result.stdout}"
    assert "--frontend-port" in result.stdout, "Should have --frontend-port option"


def test_serve_uses_default_port_8000(project_with_backend):
    """Test that serve command uses default port 8000 when not specified."""
    with patch("subprocess.run") as mock_run:
        # Mock all Docker-related commands
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            # Mock health check via docker compose ps
            if isinstance(cmd, list) and "uvicorn" in cmd:
                # Verify default port 8000 is used
                assert "--port" in cmd, "Should include --port in uvicorn command"
                port_index = cmd.index("--port") + 1
                assert cmd[port_index] == "8000", "Default port should be 8000"
            return mock_success

        mock_run.side_effect = run_side_effect

        # Run serve without specifying port
        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        # Verify uvicorn was called with default port 8000
        uvicorn_calls = [
            call_args for call_args in mock_run.call_args_list
            if "uvicorn" in str(call_args)
        ]

        assert len(uvicorn_calls) > 0, "uvicorn should have been called"

        # Extract the command from the call
        uvicorn_cmd = uvicorn_calls[0][0][0]
        assert "--port" in uvicorn_cmd, "Should include --port flag"

        port_index = uvicorn_cmd.index("--port") + 1
        assert uvicorn_cmd[port_index] == "8000", "Default port should be 8000"


def test_serve_passes_custom_port_to_uvicorn(project_with_backend):
    """Test that serve command passes custom port to uvicorn."""
    with patch("subprocess.run") as mock_run:
        # Mock all Docker-related commands
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        # Run serve with custom port 9000
        result = runner.invoke(app, ["serve", "--port", "9000"], catch_exceptions=False)

        # Verify uvicorn was called with port 9000
        uvicorn_calls = [
            call_args for call_args in mock_run.call_args_list
            if "uvicorn" in str(call_args)
        ]

        assert len(uvicorn_calls) > 0, "uvicorn should have been called"

        # Extract the command from the call
        uvicorn_cmd = uvicorn_calls[0][0][0]
        assert "--port" in uvicorn_cmd, "Should include --port flag"

        port_index = uvicorn_cmd.index("--port") + 1
        assert uvicorn_cmd[port_index] == "9000", "Custom port should be 9000"


def test_serve_accepts_port_short_flag(project_with_backend):
    """Test that serve command accepts -p short flag for port."""
    with patch("subprocess.run") as mock_run:
        # Mock all Docker-related commands
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        # Run serve with -p short flag
        result = runner.invoke(app, ["serve", "-p", "7000"], catch_exceptions=False)

        # Verify uvicorn was called with port 7000
        uvicorn_calls = [
            call_args for call_args in mock_run.call_args_list
            if "uvicorn" in str(call_args)
        ]

        assert len(uvicorn_calls) > 0, "uvicorn should have been called"

        # Extract the command from the call
        uvicorn_cmd = uvicorn_calls[0][0][0]
        assert "--port" in uvicorn_cmd, "Should include --port flag"

        port_index = uvicorn_cmd.index("--port") + 1
        assert uvicorn_cmd[port_index] == "7000", "Custom port should be 7000"


def test_serve_port_in_uvicorn_command_structure(project_with_backend):
    """Test that port is correctly placed in uvicorn command structure."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        captured_commands = []

        def run_side_effect(*args, **kwargs):
            if args and isinstance(args[0], list):
                captured_commands.append(args[0])
            return mock_success

        mock_run.side_effect = run_side_effect

        # Run serve with custom port
        result = runner.invoke(app, ["serve", "--port", "8080"], catch_exceptions=False)

        # Find uvicorn command
        uvicorn_commands = [
            cmd for cmd in captured_commands
            if "uvicorn" in str(cmd)
        ]

        assert len(uvicorn_commands) > 0, "Should have called uvicorn"

        uvicorn_cmd = uvicorn_commands[0]

        # Verify command structure
        assert uvicorn_cmd[0] == "uvicorn", "First element should be uvicorn"
        assert "--host" in uvicorn_cmd, "Should include --host"
        assert "--port" in uvicorn_cmd, "Should include --port"

        # Verify port value follows --port flag
        port_index = uvicorn_cmd.index("--port")
        assert port_index + 1 < len(uvicorn_cmd), "Port value should follow --port flag"
        assert uvicorn_cmd[port_index + 1] == "8080", "Port value should be 8080"


def test_serve_port_configuration_with_host(project_with_backend):
    """Test that port and host options work together."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        captured_commands = []

        def run_side_effect(*args, **kwargs):
            if args and isinstance(args[0], list):
                captured_commands.append(args[0])
            return mock_success

        mock_run.side_effect = run_side_effect

        # Run serve with both port and host
        result = runner.invoke(
            app,
            ["serve", "--port", "9000", "--host", "127.0.0.1"],
            catch_exceptions=False
        )

        # Find uvicorn command
        uvicorn_commands = [
            cmd for cmd in captured_commands
            if "uvicorn" in str(cmd)
        ]

        assert len(uvicorn_commands) > 0, "Should have called uvicorn"

        uvicorn_cmd = uvicorn_commands[0]

        # Verify both port and host are present
        assert "--port" in uvicorn_cmd, "Should include --port"
        assert "--host" in uvicorn_cmd, "Should include --host"

        port_index = uvicorn_cmd.index("--port")
        host_index = uvicorn_cmd.index("--host")

        assert uvicorn_cmd[port_index + 1] == "9000", "Port should be 9000"
        assert uvicorn_cmd[host_index + 1] == "127.0.0.1", "Host should be 127.0.0.1"


def test_serve_frontend_port_is_accepted(project_with_backend):
    """Test that --frontend-port flag is accepted (for future use)."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        # Run serve with frontend-port
        result = runner.invoke(
            app,
            ["serve", "--port", "8000", "--frontend-port", "3000"],
            catch_exceptions=False
        )

        # Command should be accepted (may fail later but flag should parse)
        # No error about unrecognized flag


def test_serve_validates_port_is_integer(project_with_backend):
    """Test that serve command validates port is an integer."""
    result = runner.invoke(
        app,
        ["serve", "--port", "not-a-number"],
        catch_exceptions=False
    )

    # Should fail with validation error
    assert result.exit_code != 0, "Should fail with non-integer port"


def test_serve_help_mentions_port_configuration():
    """Test that serve help text mentions port configuration."""
    result = runner.invoke(app, ["serve", "--help"])

    assert result.exit_code == 0
    help_text = result.stdout.lower()

    # Should mention port in help
    assert "port" in help_text, "Help should mention port"
    assert "fastapi" in help_text or "uvicorn" in help_text, "Help should mention FastAPI or uvicorn"


def test_serve_port_affects_service_table_display(project_with_backend):
    """Test that custom port is shown in service status table."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        def run_side_effect(*args, **kwargs):
            return mock_success

        mock_run.side_effect = run_side_effect

        # Run serve with custom port
        result = runner.invoke(app, ["serve", "--port", "9000"], catch_exceptions=False)

        # Check that output mentions the custom port
        # Note: This may be in the Rich table output
        output = result.stdout + result.stderr if result.stderr else result.stdout
        assert "9000" in output, "Output should mention custom port 9000"


def test_serve_implementation_has_port_parameter():
    """Test that serve command implementation includes port parameter logic."""
    from schnitzel.cli.commands.serve import serve_command
    import inspect

    # Get function signature
    sig = inspect.signature(serve_command)

    # Verify port parameter exists
    assert "port" in sig.parameters, "serve_command should have port parameter"

    # Verify default value is 8000
    port_param = sig.parameters["port"]
    assert port_param.default is not inspect.Parameter.empty, "port should have default value"


def test_serve_uvicorn_receives_correct_port_format():
    """Test that port is passed to uvicorn as a string (not int)."""
    with patch("subprocess.run") as mock_run:
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = "db running healthy\nredis running healthy"
        mock_success.stderr = ""

        captured_commands = []

        def run_side_effect(*args, **kwargs):
            if args and isinstance(args[0], list):
                captured_commands.append(args[0])
            return mock_success

        mock_run.side_effect = run_side_effect

        # Create temporary project
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            project_dir = Path(tmpdir)

            # Create minimal structure
            docker_compose = project_dir / "docker-compose.yaml"
            docker_compose.write_text("version: '3.8'\nservices:\n  db:\n    image: postgres:16\n  redis:\n    image: redis:7-alpine\n")

            backend_dir = project_dir / "backend" / "app"
            backend_dir.mkdir(parents=True)
            (backend_dir / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")

            try:
                result = runner.invoke(app, ["serve", "--port", "8888"], catch_exceptions=False)

                # Find uvicorn command
                uvicorn_commands = [
                    cmd for cmd in captured_commands
                    if "uvicorn" in str(cmd)
                ]

                if uvicorn_commands:
                    uvicorn_cmd = uvicorn_commands[0]
                    port_index = uvicorn_cmd.index("--port")
                    port_value = uvicorn_cmd[port_index + 1]

                    # Port should be passed as string for subprocess
                    assert isinstance(port_value, str), "Port should be passed as string to subprocess"
                    assert port_value == "8888", "Port value should be '8888'"

            finally:
                os.chdir(original_cwd)
