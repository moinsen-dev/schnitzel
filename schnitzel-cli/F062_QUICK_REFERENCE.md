# F062 Quick Reference: Redis 7 Service

## Quick Start

### Generate docker-compose.yaml with Redis
```python
from schnitzel.generators.docker.compose import DockerComposeGenerator

generator = DockerComposeGenerator()
compose_file, size = generator.generate_to_file(".")
```

### Run Tests
```bash
uv run pytest tests/integration/test_docker_redis_f062.py -v
```

### Run Demo
```bash
uv run python demo_f062_redis.py
```

## Redis Service Configuration

### Default Configuration
- **Image**: redis:7-alpine
- **Port**: 6379 (configurable via REDIS_PORT)
- **Persistence**: AOF enabled (--appendonly yes)
- **Volume**: redis_data:/data
- **Health Check**: redis-cli ping (every 5s)

### Environment Variables
```bash
# .env file example
REDIS_PORT=6380
```

### Docker Commands
```bash
# Start services
docker-compose up -d

# Check Redis status
docker-compose ps redis

# Connect to Redis CLI
docker-compose exec redis redis-cli

# View Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis

# Stop Redis
docker-compose stop redis
```

### Backend Integration
The backend service automatically gets:
- `REDIS_URL=redis://redis:6379` environment variable
- Dependency on Redis being healthy

### Connection Examples

#### Python (redis-py)
```python
import redis
r = redis.from_url('redis://redis:6379')
r.ping()  # Returns True
```

#### Python (aioredis)
```python
import aioredis
redis = await aioredis.create_redis_pool('redis://redis:6379')
await redis.ping()  # Returns b'PONG'
```

## Test Coverage
✅ 7/7 tests passing:
1. Redis service exists
2. Uses redis:7-alpine image
3. AOF persistence configured
4. redis_data volume defined
5. Port 6379 exposed
6. Volume persistence configured
7. Command configuration validated

## Files
- **Generator**: src/schnitzel/generators/docker/compose.py
- **Tests**: tests/integration/test_docker_redis_f062.py
- **Demo**: demo_f062_redis.py
- **Docs**: F062_IMPLEMENTATION_SUMMARY.md
