#!/usr/bin/env python3
"""Demo script for F062 - Docker Compose Redis 7 Service.

This script demonstrates the Redis 7 service generation in docker-compose.yaml.
"""

import tempfile
from pathlib import Path
import yaml

from schnitzel.generators.docker.compose import DockerComposeGenerator


def demo_redis_service():
    """Demonstrate Redis 7 service in docker-compose.yaml."""
    print("=" * 80)
    print("F062 Demo: Docker Compose Redis 7 Service Generator")
    print("=" * 80)
    print()

    # Create a temporary directory for demonstration
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Generate docker-compose.yaml
        print("1. Generating docker-compose.yaml with Redis 7 service...")
        generator = DockerComposeGenerator()
        compose_file, file_size = generator.generate_to_file(temp_path)

        print(f"   ✓ Generated: {compose_file}")
        print(f"   ✓ File size: {file_size} bytes")
        print()

        # Parse and display Redis service configuration
        with open(compose_file, "r") as f:
            compose_data = yaml.safe_load(f)

        print("2. Redis Service Configuration:")
        print("-" * 80)
        redis_service = compose_data["services"]["redis"]

        print(f"   Image:      {redis_service['image']}")
        print(f"   Command:    {redis_service['command']}")
        print(f"   Ports:      {redis_service['ports']}")
        print(f"   Volumes:    {redis_service['volumes']}")

        if 'healthcheck' in redis_service:
            print(f"   Healthcheck:")
            for key, value in redis_service['healthcheck'].items():
                print(f"     - {key}: {value}")
        print()

        print("3. Volume Configuration:")
        print("-" * 80)
        volumes = compose_data["volumes"]
        if "redis_data" in volumes:
            print("   ✓ redis_data volume defined for data persistence")
        print()

        print("4. Key Features:")
        print("-" * 80)
        print("   ✓ Redis 7 Alpine image (lightweight)")
        print("   ✓ AOF (Append Only File) persistence enabled")
        print("   ✓ Port 6379 exposed for connections")
        print("   ✓ Named volume for data persistence")
        if 'healthcheck' in redis_service:
            print("   ✓ Health check configured with redis-cli ping")
        print()

        print("5. Backend Integration:")
        print("-" * 80)
        backend_service = compose_data["services"]["backend"]
        if "REDIS_URL" in backend_service.get("environment", {}):
            redis_url = backend_service["environment"]["REDIS_URL"]
            print(f"   ✓ Backend has REDIS_URL: {redis_url}")
        if "depends_on" in backend_service and "redis" in backend_service["depends_on"]:
            print("   ✓ Backend waits for Redis to be healthy")
        print()

        print("6. Generated docker-compose.yaml (Redis section):")
        print("-" * 80)
        print("  redis:")
        print(f"    image: {redis_service['image']}")
        print(f"    command: {redis_service['command']}")
        print("    volumes:")
        for vol in redis_service['volumes']:
            print(f"      - {vol}")
        print("    ports:")
        for port in redis_service['ports']:
            print(f"      - {port}")
        if 'healthcheck' in redis_service:
            print("    healthcheck:")
            print(f"      test: {redis_service['healthcheck']['test']}")
            print(f"      interval: {redis_service['healthcheck']['interval']}")
            print(f"      timeout: {redis_service['healthcheck']['timeout']}")
            print(f"      retries: {redis_service['healthcheck']['retries']}")
            print(f"      start_period: {redis_service['healthcheck']['start_period']}")
        print()

        print("7. Usage:")
        print("-" * 80)
        print("   To start the services:")
        print("   $ docker-compose up -d")
        print()
        print("   To connect to Redis:")
        print("   $ redis-cli -h localhost -p 6379")
        print()
        print("   To check Redis status:")
        print("   $ docker-compose ps redis")
        print("   $ docker-compose exec redis redis-cli ping")
        print()

    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    demo_redis_service()
