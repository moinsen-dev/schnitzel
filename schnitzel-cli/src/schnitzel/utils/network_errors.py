"""Network error handling utilities for Schnitzel CLI.

This module provides graceful error handling for network-related issues
such as Docker daemon connectivity, port conflicts, and service availability.
"""

import subprocess
from typing import Optional, Tuple
from rich.console import Console

console = Console()


class NetworkErrorHandler:
    """Handler for network-related errors in CLI commands."""

    @staticmethod
    def handle_docker_error(error: Exception, quiet: bool = False) -> Tuple[bool, str]:
        """Handle Docker-related errors gracefully.

        Args:
            error: The exception that was raised
            quiet: Whether to suppress output

        Returns:
            Tuple of (should_exit, error_message)
        """
        error_type = type(error).__name__
        error_msg = str(error)

        if isinstance(error, FileNotFoundError):
            if not quiet:
                console.print("[red]Error: Docker is not installed[/red]")
                console.print("[dim]Install Docker from: https://docs.docker.com/get-docker/[/dim]")
            return True, "Docker not installed"

        elif isinstance(error, subprocess.TimeoutExpired):
            if not quiet:
                console.print("[red]Error: Docker operation timed out[/red]")
                console.print("[dim]This may indicate:")
                console.print("  - Docker daemon is not running")
                console.print("  - Network connectivity issues")
                console.print("  - Docker resources are exhausted[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Restart Docker: docker restart")
                console.print("  2. Check Docker status: docker info")
            return True, "Docker operation timed out"

        elif "connection refused" in error_msg.lower() or "cannot connect" in error_msg.lower():
            if not quiet:
                console.print("[red]Error: Cannot connect to Docker daemon[/red]")
                console.print("[dim]The Docker daemon is not running or not accessible.[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Start Docker Desktop (on macOS/Windows)")
                console.print("  2. Start Docker daemon: sudo systemctl start docker (on Linux)")
                console.print("  3. Check Docker socket: ls -la /var/run/docker.sock")
            return True, "Docker daemon not accessible"

        elif "port is already allocated" in error_msg.lower() or "address already in use" in error_msg.lower():
            if not quiet:
                console.print("[red]Error: Port is already in use[/red]")
                console.print("[dim]Another service is using the required port.[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Stop conflicting services")
                console.print("  2. Check port usage: lsof -i :<port> or netstat -an | grep <port>")
                console.print("  3. Modify port configuration in docker-compose.yaml")
            return True, "Port already allocated"

        elif "network" in error_msg.lower() or "unreachable" in error_msg.lower():
            if not quiet:
                console.print("[red]Error: Network unreachable[/red]")
                console.print("[dim]Cannot reach Docker network or container.[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Check network connectivity")
                console.print("  2. Restart Docker networking: docker network prune")
                console.print("  3. Check firewall settings")
            return True, "Network unreachable"

        # Generic error
        if not quiet:
            console.print(f"[red]Error: {error_type}[/red]")
            console.print(f"[dim]{error_msg}[/dim]")
        return True, error_msg

    @staticmethod
    def handle_subprocess_error(
        error: Exception,
        command_name: str,
        quiet: bool = False
    ) -> Tuple[bool, str]:
        """Handle subprocess errors gracefully.

        Args:
            error: The exception that was raised
            command_name: Name of the command that failed (e.g., 'flutter', 'uv')
            quiet: Whether to suppress output

        Returns:
            Tuple of (should_exit, error_message)
        """
        error_type = type(error).__name__
        error_msg = str(error)

        if isinstance(error, FileNotFoundError):
            if not quiet:
                console.print(f"[red]Error: '{command_name}' command not found[/red]")
                console.print(f"[dim]'{command_name}' is not installed or not in your PATH.[/dim]")
                if command_name == "flutter":
                    console.print("\n[yellow]Install Flutter:[/yellow]")
                    console.print("  https://docs.flutter.dev/get-started/install")
                elif command_name == "uv":
                    console.print("\n[yellow]Install uv:[/yellow]")
                    console.print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
                elif command_name == "docker":
                    console.print("\n[yellow]Install Docker:[/yellow]")
                    console.print("  https://docs.docker.com/get-docker/")
            return True, f"{command_name} not found"

        elif isinstance(error, subprocess.TimeoutExpired):
            if not quiet:
                console.print(f"[red]Error: '{command_name}' operation timed out[/red]")
                console.print("[dim]This may indicate:")
                console.print(f"  - {command_name} is hanging")
                console.print("  - Network connectivity issues (if downloading packages)")
                console.print("  - Insufficient system resources[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Check network connectivity")
                console.print("  2. Free up system resources")
                console.print("  3. Try again with a stable internet connection")
            return True, f"{command_name} timed out"

        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            if not quiet:
                console.print(f"[red]Error: Network issue during '{command_name}' operation[/red]")
                console.print("[dim]Cannot establish network connection.[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Check internet connectivity")
                console.print("  2. Check proxy settings if behind a corporate firewall")
                console.print("  3. Try again later if package registry is down")
            return True, "Network error"

        # Generic error
        if not quiet:
            console.print(f"[red]Error running '{command_name}': {error_type}[/red]")
            console.print(f"[dim]{error_msg}[/dim]")
        return True, error_msg

    @staticmethod
    def handle_database_error(error: Exception, quiet: bool = False) -> Tuple[bool, str]:
        """Handle database connection errors gracefully.

        Args:
            error: The exception that was raised
            quiet: Whether to suppress output

        Returns:
            Tuple of (should_exit, error_message)
        """
        error_type = type(error).__name__
        error_msg = str(error)

        if "connection refused" in error_msg.lower() or "could not connect" in error_msg.lower():
            if not quiet:
                console.print("[red]Error: Cannot connect to database[/red]")
                console.print("[dim]The database server is not running or not accessible.[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Start database services: schnitzel serve start")
                console.print("  2. Check Docker services: docker ps")
                console.print("  3. Verify DATABASE_URL environment variable")
            return True, "Database connection refused"

        elif "authentication failed" in error_msg.lower() or "password" in error_msg.lower():
            if not quiet:
                console.print("[red]Error: Database authentication failed[/red]")
                console.print("[dim]Invalid database credentials.[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Check DATABASE_URL credentials")
                console.print("  2. Verify database user exists")
                console.print("  3. Reset database password if needed")
            return True, "Database authentication failed"

        elif "does not exist" in error_msg.lower() and "database" in error_msg.lower():
            if not quiet:
                console.print("[red]Error: Database does not exist[/red]")
                console.print("[dim]The specified database has not been created.[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Create database: CREATE DATABASE <name>;")
                console.print("  2. Run migrations: schnitzel migrate upgrade head")
            return True, "Database does not exist"

        elif "timeout" in error_msg.lower():
            if not quiet:
                console.print("[red]Error: Database operation timed out[/red]")
                console.print("[dim]Connection to database timed out.[/dim]")
                console.print("\n[yellow]Try:[/yellow]")
                console.print("  1. Check database is running")
                console.print("  2. Check network connectivity")
                console.print("  3. Increase timeout in connection string")
            return True, "Database timeout"

        # Generic database error
        if not quiet:
            console.print(f"[red]Database Error: {error_type}[/red]")
            console.print(f"[dim]{error_msg}[/dim]")
        return True, error_msg

    @staticmethod
    def check_docker_health(quiet: bool = False) -> Tuple[bool, Optional[str]]:
        """Check if Docker is installed and running.

        Args:
            quiet: Whether to suppress output

        Returns:
            Tuple of (is_healthy, error_message)
        """
        # Check if Docker is installed
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                if not quiet:
                    console.print("[red]Error: Docker command failed[/red]")
                return False, "Docker command failed"
        except FileNotFoundError:
            if not quiet:
                console.print("[red]Error: Docker is not installed[/red]")
                console.print("[dim]Install Docker from: https://docs.docker.com/get-docker/[/dim]")
            return False, "Docker not installed"
        except subprocess.TimeoutExpired:
            if not quiet:
                console.print("[red]Error: Docker command timed out[/red]")
            return False, "Docker timeout"
        except Exception as e:
            return NetworkErrorHandler.handle_docker_error(e, quiet)

        # Check if Docker daemon is running
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                if not quiet:
                    console.print("[red]Error: Docker daemon is not running[/red]")
                    console.print("[dim]Start Docker Desktop or the Docker daemon[/dim]")
                return False, "Docker daemon not running"
        except FileNotFoundError:
            if not quiet:
                console.print("[red]Error: Docker is not installed[/red]")
            return False, "Docker not installed"
        except subprocess.TimeoutExpired:
            if not quiet:
                console.print("[red]Error: Cannot reach Docker daemon[/red]")
                console.print("[dim]Docker daemon may be unresponsive[/dim]")
            return False, "Docker daemon timeout"
        except Exception as e:
            if "connection refused" in str(e).lower():
                if not quiet:
                    console.print("[red]Error: Cannot connect to Docker daemon[/red]")
                    console.print("[dim]Start Docker Desktop or the Docker daemon[/dim]")
                return False, "Cannot connect to Docker daemon"
            return NetworkErrorHandler.handle_docker_error(e, quiet)

        return True, None

    @staticmethod
    def check_port_available(port: int, quiet: bool = False) -> Tuple[bool, Optional[str]]:
        """Check if a port is available.

        Args:
            port: Port number to check
            quiet: Whether to suppress output

        Returns:
            Tuple of (is_available, error_message)
        """
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    # Port is in use
                    if not quiet:
                        console.print(f"[yellow]Warning: Port {port} is already in use[/yellow]")
                        console.print("[dim]Another service is using this port.[/dim]")
                    return False, f"Port {port} already in use"
                return True, None
        except Exception as e:
            if not quiet:
                console.print(f"[yellow]Warning: Could not check port {port}: {e}[/yellow]")
            return True, None  # Assume available on error
