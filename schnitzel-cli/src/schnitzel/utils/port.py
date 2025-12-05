"""Port availability utilities for Schnitzel CLI."""

import socket
from typing import Optional


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """Check if a port is available for binding.

    Args:
        port: Port number to check
        host: Host address to check (default: 0.0.0.0)

    Returns:
        bool: True if port is available, False if already in use
    """
    # Validate port range
    if port < 1 or port > 65535:
        return False

    try:
        # Try to bind to the port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except OSError:
        # Port is already in use
        return False


def find_available_port(
    start_port: int,
    host: str = "0.0.0.0",
    max_attempts: int = 10
) -> Optional[int]:
    """Find the next available port starting from a given port.

    Args:
        start_port: Port number to start searching from
        host: Host address to check (default: 0.0.0.0)
        max_attempts: Maximum number of ports to try (default: 10)

    Returns:
        Optional[int]: First available port number, or None if none found
    """
    for offset in range(max_attempts):
        port = start_port + offset
        # Stop if we exceed valid port range
        if port > 65535:
            break
        if is_port_available(port, host):
            return port
    return None


def get_port_conflict_message(
    port: int,
    host: str = "0.0.0.0",
    suggest_alternative: bool = True
) -> str:
    """Get a helpful error message for port conflicts.

    Args:
        port: The conflicting port number
        host: Host address (default: 0.0.0.0)
        suggest_alternative: Whether to suggest an alternative port

    Returns:
        str: Formatted error message with suggestions
    """
    message = f"Port {port} is already in use"

    if host != "0.0.0.0":
        message += f" on {host}"

    if suggest_alternative:
        alternative = find_available_port(port + 1, host, max_attempts=10)
        if alternative:
            message += f"\n\nSuggested alternatives:"
            message += f"\n  - Use port {alternative}: schnitzel serve start --port {alternative}"

            # Show a few more options
            other_ports = []
            for offset in range(1, 4):
                check_port = port + offset
                if check_port != alternative and is_port_available(check_port, host):
                    other_ports.append(check_port)

            if other_ports:
                message += f"\n  - Other available ports: {', '.join(map(str, other_ports))}"
        else:
            message += "\n\nNo available ports found in the range. Try specifying a different port with --port"

    message += f"\n\nTo check what's using port {port}:"
    message += f"\n  - On macOS/Linux: lsof -i :{port}"
    message += f"\n  - On Windows: netstat -ano | findstr :{port}"

    return message
