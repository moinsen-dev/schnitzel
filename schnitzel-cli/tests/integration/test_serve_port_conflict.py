"""Integration tests for serve command port conflict handling."""

import socket
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from schnitzel.cli.commands.serve import _start_uvicorn
from schnitzel.utils.port import is_port_available


class TestServeCommandPortConflict:
    """Test serve command handles port conflicts gracefully."""

    def test_start_uvicorn_detects_port_conflict(self, tmp_path):
        """Test that _start_uvicorn detects and reports port conflicts."""
        # Create a minimal project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        backend_dir = project_dir / "backend" / "app"
        backend_dir.mkdir(parents=True)

        # Create a minimal FastAPI app
        main_py = backend_dir / "main.py"
        main_py.write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello"}
""")

        # Bind to port 8000 to simulate a conflict
        test_port = 62000  # Use a high port for testing
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", test_port))
            sock.listen(1)

            # Verify port is not available
            assert is_port_available(test_port, "127.0.0.1") is False

            # Mock subprocess.run to avoid actually starting uvicorn
            with patch("schnitzel.cli.commands.serve.subprocess.run") as mock_run:
                # Call _start_uvicorn with the occupied port
                exit_code = _start_uvicorn(
                    project_dir,
                    port=test_port,
                    host="127.0.0.1",
                    reload=False
                )

                # Should return error code 1 without trying to start uvicorn
                assert exit_code == 1
                # subprocess.run should NOT have been called
                mock_run.assert_not_called()

    def test_start_uvicorn_proceeds_with_available_port(self, tmp_path):
        """Test that _start_uvicorn proceeds when port is available."""
        # Create a minimal project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        backend_dir = project_dir / "backend" / "app"
        backend_dir.mkdir(parents=True)

        # Create a minimal FastAPI app
        main_py = backend_dir / "main.py"
        main_py.write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello"}
""")

        # Use a high port that's likely available
        test_port = 63000

        # Verify port is available
        assert is_port_available(test_port, "127.0.0.1") is True

        # Mock subprocess.run to avoid actually starting uvicorn
        with patch("schnitzel.cli.commands.serve.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Call _start_uvicorn with an available port
            exit_code = _start_uvicorn(
                project_dir,
                port=test_port,
                host="127.0.0.1",
                reload=False
            )

            # Should return success code
            assert exit_code == 0
            # subprocess.run should have been called
            mock_run.assert_called_once()

            # Verify uvicorn command was called with correct port
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert "uvicorn" in cmd
            assert "--port" in cmd
            assert str(test_port) in cmd

    def test_port_conflict_with_different_hosts(self):
        """Test port conflict detection works with different host bindings."""
        test_port = 64000

        # Bind to localhost only
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", test_port))
            sock.listen(1)

            # Port should not be available on localhost
            assert is_port_available(test_port, "127.0.0.1") is False

            # Port might still be available on 0.0.0.0 (depends on OS)
            # This is expected behavior - we test that we can detect conflicts

    def test_runtime_port_conflict_handling(self, tmp_path):
        """Test that runtime port conflicts are caught and reported."""
        # Create a minimal project structure
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        backend_dir = project_dir / "backend" / "app"
        backend_dir.mkdir(parents=True)

        # Create a minimal FastAPI app
        main_py = backend_dir / "main.py"
        main_py.write_text("""
from fastapi import FastAPI

app = FastAPI()
""")

        test_port = 65000

        # Mock subprocess.run to simulate a runtime port conflict
        with patch("schnitzel.cli.commands.serve.subprocess.run") as mock_run:
            # Simulate OSError with "Address already in use"
            mock_run.side_effect = OSError("[Errno 48] Address already in use")

            # Call _start_uvicorn
            exit_code = _start_uvicorn(
                project_dir,
                port=test_port,
                host="127.0.0.1",
                reload=False
            )

            # Should return error code 1
            assert exit_code == 1
            # subprocess.run should have been called (port check passed, but binding failed)
            mock_run.assert_called_once()


class TestPortConflictMessageQuality:
    """Test that port conflict messages are helpful."""

    def test_conflict_message_includes_alternatives(self):
        """Test that conflict messages suggest alternative ports."""
        from schnitzel.utils.port import get_port_conflict_message

        port = 60000  # Use a port within valid range
        message = get_port_conflict_message(port, suggest_alternative=True)

        # Should include basic conflict info
        assert f"Port {port} is already in use" in message

        # Should include alternatives
        assert "schnitzel serve start --port" in message

        # Should include diagnostic commands
        assert "lsof -i" in message or "netstat" in message

    def test_conflict_message_without_alternatives(self):
        """Test conflict messages without alternative suggestions."""
        from schnitzel.utils.port import get_port_conflict_message

        port = 67000
        message = get_port_conflict_message(port, suggest_alternative=False)

        # Should include basic conflict info
        assert f"Port {port} is already in use" in message

        # Should include diagnostic commands
        assert "lsof -i" in message or "netstat" in message

        # Should NOT include alternatives
        assert "schnitzel serve start --port" not in message or "Suggested alternatives" not in message
