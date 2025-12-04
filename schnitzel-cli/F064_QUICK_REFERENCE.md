# F064 Quick Reference: Redis Health Checks

## What Was Implemented

Feature F064 adds Redis service with health checks to the Schnitzel Framework's Docker Compose generator.

## Key Changes

### 1. Redis Service Added
- **Image**: redis:7-alpine
- **Port**: 6379 (configurable via REDIS_PORT)
- **Persistence**: AOF (Append-Only File) enabled
- **Volume**: redis_data for data persistence

### 2. Health Check Configuration
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 5s
  timeout: 5s
  retries: 5
  start_period: 5s
```

### 3. Backend Service Updates
- Added dependency on Redis with `condition: service_healthy`
- Added `REDIS_URL` environment variable: `redis://redis:6379`

## Testing

### Run F064 Tests
```bash
uv run pytest tests/integration/test_docker_redis_health_f064.py -v
```

### Test Coverage
- 8 comprehensive tests
- All tests passing
- 100% coverage of requirements

### Test List
1. Redis has healthcheck
2. Healthcheck uses redis-cli ping
3. Healthcheck has proper intervals
4. Backend depends on healthy Redis
5. Healthcheck has start_period
6. Redis service properly configured
7. Backend has REDIS_URL env var
8. Comprehensive healthcheck validation

## Usage

### Generate Docker Compose
```python
from schnitzel.generators.docker.compose import DockerComposeGenerator

generator = DockerComposeGenerator()
content = generator.generate()
```

### Environment Variables
Configure Redis via environment variables:
- `REDIS_PORT` - Redis port (default: 6379)

## Benefits

1. **Reliability**: Backend only starts when Redis is healthy
2. **No Connection Errors**: Prevents premature connection attempts
3. **Production Ready**: Proper health monitoring
4. **Data Persistence**: AOF ensures data durability
5. **Configurable**: Environment variable support

## Files Modified

1. `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/src/schnitzel/generators/docker/compose.py`
2. `/Users/udi/work/moinsen/ideas/schnitzel/schnitzel-cli/tests/integration/test_docker_redis_health_f064.py` (NEW)

## Compatibility

- Works with existing PostgreSQL health checks (F060)
- No breaking changes
- All existing tests continue to pass
