"""Tests for port conflict handling in serve command."""

import socket
import pytest
from pathlib import Path

from schnitzel.utils.port import (
    is_port_available,
    find_available_port,
    get_port_conflict_message,
)


class TestPortAvailability:
    """Test port availability detection."""

    def test_is_port_available_free_port(self):
        """Test that a high-numbered port is typically available."""
        # Use a very high port number that's unlikely to be in use
        port = 54321
        assert is_port_available(port) is True

    def test_is_port_available_in_use(self):
        """Test detection of port already in use."""
        # Bind a socket to a port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))  # Bind to any available port
            _, actual_port = sock.getsockname()

            # Now check if that port is available (it shouldn't be)
            assert is_port_available(actual_port, "127.0.0.1") is False

    def test_find_available_port(self):
        """Test finding next available port."""
        # Start from a high port number
        start_port = 55000
        available_port = find_available_port(start_port)

        assert available_port is not None
        assert available_port >= start_port
        assert is_port_available(available_port) is True

    def test_find_available_port_with_occupied_ports(self):
        """Test finding available port when some are occupied."""
        # Bind to a few ports
        sockets = []
        start_port = 56000

        try:
            # Occupy ports 56000, 56001, 56002
            for i in range(3):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(("127.0.0.1", start_port + i))
                sockets.append(sock)

            # Find available port starting from 56000
            available_port = find_available_port(start_port, "127.0.0.1")

            # Should find 56003 or higher
            assert available_port is not None
            assert available_port >= start_port + 3
            assert is_port_available(available_port, "127.0.0.1") is True

        finally:
            # Clean up
            for sock in sockets:
                sock.close()

    def test_find_available_port_max_attempts(self):
        """Test that find_available_port respects max_attempts."""
        # Occupy many ports
        sockets = []
        start_port = 57000

        try:
            # Occupy 15 consecutive ports
            for i in range(15):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(("127.0.0.1", start_port + i))
                sockets.append(sock)

            # Try to find available port with max_attempts=10
            available_port = find_available_port(start_port, "127.0.0.1", max_attempts=10)

            # Should return None because we can't find one in 10 attempts
            assert available_port is None

        finally:
            # Clean up
            for sock in sockets:
                sock.close()


class TestPortConflictMessage:
    """Test port conflict error message generation."""

    def test_get_port_conflict_message_basic(self):
        """Test basic port conflict message."""
        message = get_port_conflict_message(8000, suggest_alternative=False)

        assert "Port 8000 is already in use" in message
        assert "lsof -i :8000" in message
        assert "netstat -ano | findstr :8000" in message

    def test_get_port_conflict_message_with_host(self):
        """Test port conflict message with specific host."""
        message = get_port_conflict_message(8000, host="127.0.0.1", suggest_alternative=False)

        assert "Port 8000 is already in use on 127.0.0.1" in message

    def test_get_port_conflict_message_with_alternative(self):
        """Test port conflict message with alternative suggestion."""
        # Use a high port that's likely available
        port = 58000
        message = get_port_conflict_message(port, suggest_alternative=True)

        # Should contain suggestion for using a different port
        assert "Suggested alternatives" in message or "schnitzel serve start --port" in message

    def test_get_port_conflict_message_occupied_port(self):
        """Test port conflict message for actually occupied port."""
        # Bind a socket to a port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            _, actual_port = sock.getsockname()

            message = get_port_conflict_message(actual_port, "127.0.0.1", suggest_alternative=True)

            # Should contain helpful information
            assert f"Port {actual_port} is already in use" in message
            assert "Suggested alternatives" in message
            assert "schnitzel serve start --port" in message


class TestPortConflictIntegration:
    """Integration tests for port conflict handling."""

    def test_port_check_before_server_start(self):
        """Test that port availability is checked before starting server."""
        # This test verifies the logical flow rather than actual server startup
        port = 59000

        # Port should be available
        assert is_port_available(port) is True

        # Bind to the port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", port))

            # Now port should not be available
            assert is_port_available(port, "127.0.0.1") is False

            # Get conflict message
            message = get_port_conflict_message(port, "127.0.0.1")
            assert "Port 59000 is already in use" in message

    def test_find_alternative_port_workflow(self):
        """Test the workflow of finding an alternative port."""
        start_port = 60000

        # Occupy the default port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", start_port))

            # Port should not be available
            assert is_port_available(start_port, "127.0.0.1") is False

            # Find alternative
            alternative = find_available_port(start_port + 1, "127.0.0.1")
            assert alternative is not None
            assert alternative > start_port
            assert is_port_available(alternative, "127.0.0.1") is True
