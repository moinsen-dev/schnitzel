"""Docker Compose generator for Schnitzel schemas.

Generates docker-compose.yaml configuration files for database and backend services.

Port Assignments (F066 - Port Collision Prevention):
- PostgreSQL: 5432 (POSTGRES_PORT) - Standard PostgreSQL port
- Redis: 6379 (REDIS_PORT) - Standard Redis port
- Backend: 8000 (BACKEND_PORT) - Common Python web framework port

All ports are configurable via environment variables to prevent collisions.
Each service uses a unique default port to ensure no conflicts in development.

Custom Ports (F094):
- Custom ports can be specified in the schema services section
- Supports per-service port configuration (db, redis, backend)
- Falls back to default ports when not specified
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from schnitzel import __version__
from schnitzel.schema.models import SchnitzelSchema


class DockerComposeGenerator:
    """Generates docker-compose.yaml files for Schnitzel projects."""

    # Default port mappings (F066)
    DEFAULT_PORTS = {
        "db": 5432,
        "redis": 6379,
        "backend": 8000,
    }

    def __init__(self):
        """Initialize the Docker Compose generator."""
        pass

    def _get_port(self, schema: Optional[SchnitzelSchema], service_name: str) -> int:
        """
        Get the port for a service from schema or use default.

        Args:
            schema: Optional SchnitzelSchema object with services configuration
            service_name: Name of the service (db, redis, backend)

        Returns:
            Port number to use for the service
        """
        # If no schema provided, use defaults
        if schema is None or schema.services is None:
            return self.DEFAULT_PORTS[service_name]

        # Check if service has custom port in schema
        service_config = schema.services.get(service_name)
        if service_config and isinstance(service_config, dict):
            port = service_config.get("port")
            if port is not None:
                # Validate port is an integer
                if isinstance(port, int):
                    return port
                elif isinstance(port, str) and port.isdigit():
                    return int(port)

        # Fall back to default port
        return self.DEFAULT_PORTS[service_name]

    def generate(self, schema: Optional[SchnitzelSchema] = None) -> str:
        """
        Generate docker-compose.yaml content with environment variable substitution.

        Environment variables can be overridden via .env file or shell environment.
        Default values are provided for development convenience.

        Port Collision Prevention (F066):
        All services use unique, well-known default ports that can be customized:
        - PostgreSQL: ${POSTGRES_PORT:-5432}
        - Redis: ${REDIS_PORT:-6379}
        - Backend: ${BACKEND_PORT:-8000}

        Custom Ports (F094):
        Custom ports can be specified in the schema services section:
        - services.db.port: Custom PostgreSQL port
        - services.redis.port: Custom Redis port
        - services.backend.port: Custom backend port

        Network Configuration (F095):
        Services are connected via a custom network for better isolation and control:
        - schnitzel_network: Bridge network connecting all services
        - Enables service discovery and inter-service communication
        - Provides network-level isolation from other Docker Compose projects

        Args:
            schema: Optional SchnitzelSchema object with services configuration

        Returns:
            Generated docker-compose.yaml content as a string
        """
        # Get ports from schema or use defaults (F094)
        postgres_port = self._get_port(schema, "db")
        redis_port = self._get_port(schema, "redis")
        backend_port = self._get_port(schema, "backend")

        return f"""version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      # PostgreSQL credentials - override via .env file or environment
      # Default user: schnitzel
      POSTGRES_USER: ${{POSTGRES_USER:-schnitzel}}
      # Default password: schnitzel_dev (change in production!)
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:-schnitzel_dev}}
      # Default database name: schnitzel_db
      POSTGRES_DB: ${{POSTGRES_DB:-schnitzel_db}}
    ports:
      # PostgreSQL port - default: {postgres_port}
      - "${{POSTGRES_PORT:-{postgres_port}}}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER:-schnitzel}} -d ${{POSTGRES_DB:-schnitzel_db}}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - schnitzel_network

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      # Redis port - default: {redis_port}
      - "${{REDIS_PORT:-{redis_port}}}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 5s
    networks:
      - schnitzel_network

  backend:
    build: ./backend
    ports:
      # Backend API port - default: {backend_port}
      - "${{BACKEND_PORT:-{backend_port}}}:8000"
    environment:
      # Database connection URL - uses same env vars as db service
      DATABASE_URL: postgresql://${{POSTGRES_USER:-schnitzel}}:${{POSTGRES_PASSWORD:-schnitzel_dev}}@db:5432/${{POSTGRES_DB:-schnitzel_db}}
      # Redis connection URL
      REDIS_URL: redis://redis:6379
      # Backend environment - default: development
      ENVIRONMENT: ${{ENVIRONMENT:-development}}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    networks:
      - schnitzel_network

volumes:
  postgres_data:
  redis_data:

networks:
  schnitzel_network:
    driver: bridge
"""

    def generate_to_file(
        self,
        output_dir: str | Path,
        dry_run: bool = False,
        schema: Optional[SchnitzelSchema] = None,
    ) -> tuple[Path, int]:
        """
        Generate docker-compose.yaml and write it to a file.

        Creates the output directory if it doesn't exist and writes the
        docker-compose.yaml file with a DO NOT EDIT header.

        Args:
            output_dir: Directory where docker-compose.yaml should be written
            dry_run: If True, return file info without writing (default: False)
            schema: Optional SchnitzelSchema object with services configuration (F094)

        Returns:
            Tuple of (Path object pointing to docker-compose.yaml file, size in bytes)

        Example:
            >>> generator = DockerComposeGenerator()
            >>> output_path, size = generator.generate_to_file(".")
            >>> print(f"Docker Compose written to: {output_path} ({size} bytes)")
        """
        from datetime import datetime

        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the docker-compose content (F094: pass schema for custom ports)
        compose_content = self.generate(schema=schema)

        # Build header comment (F100)
        timestamp = datetime.now().isoformat()
        header = f"""# Generated by Schnitzel Framework v{__version__}
# DO NOT EDIT - This file is auto-generated
# Generated at: {timestamp}

"""

        # Combine header with generated content
        full_content = header + compose_content

        # Calculate file path and size
        compose_file = output_path / "docker-compose.yaml"
        file_size = len(full_content.encode("utf-8"))

        # If dry-run, return without writing
        if dry_run:
            return compose_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Write to file
        compose_file.write_text(full_content, encoding="utf-8")

        return compose_file, file_size
