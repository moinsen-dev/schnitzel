# F063 Quick Reference: PostgreSQL Health Checks

## Overview
PostgreSQL service now includes comprehensive health checks to ensure database readiness before dependent services start.

## Health Check Configuration

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-schnitzel} -d ${POSTGRES_DB:-schnitzel_db}"]
  interval: 5s        # Check every 5 seconds
  timeout: 5s         # Max time for check to complete
  retries: 5          # Number of consecutive failures before unhealthy
  start_period: 10s   # Grace period for initialization
```

## Service Dependencies

Backend waits for healthy database:
```yaml
backend:
  depends_on:
    db:
      condition: service_healthy  # Wait for db to be healthy
```

## Testing

### Run F063 Tests
```bash
uv run pytest tests/integration/test_docker_postgres_health_f063.py -v
```

### Run All Docker Tests
```bash
uv run pytest tests/integration/test_docker*.py -v
```

## Usage Examples

### Check Health Status
```bash
# View all services with health status
docker-compose ps

# Check health of database only
docker-compose ps db
```

### View Health Check Logs
```bash
# View database logs including health checks
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f db
```

### Manual Health Check
```bash
# Run health check manually
docker-compose exec db pg_isready -U schnitzel -d schnitzel_db

# With custom credentials
docker-compose exec db pg_isready -U myuser -d mydb
```

## Environment Variables

Health check respects environment configuration:

```env
# .env file
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydb
```

The health check automatically uses these values via `${POSTGRES_USER:-schnitzel}` syntax.

## Common Scenarios

### Database is Healthy
```
$ docker-compose ps
NAME    SERVICE    STATUS           PORTS
db      db         Up (healthy)     0.0.0.0:5432->5432/tcp
```

### Database is Starting
```
$ docker-compose ps
NAME    SERVICE    STATUS            PORTS
db      db         Up (starting)     0.0.0.0:5432->5432/tcp
```

### Database is Unhealthy
```
$ docker-compose ps
NAME    SERVICE    STATUS              PORTS
db      db         Up (unhealthy)      0.0.0.0:5432->5432/tcp
```

## Timing Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `interval` | 5s | How often to run the health check |
| `timeout` | 5s | Max time allowed for check to complete |
| `retries` | 5 | Failures needed before marking unhealthy |
| `start_period` | 10s | Grace period during startup (checks don't count as failures) |

### Calculation
- **Maximum startup time**: 10s (start_period) + (5s × 5 retries) = 35s max before unhealthy
- **Recovery time after failure**: 5s × 5 retries = 25s to become healthy again

## Health Check States

1. **starting** - Within start_period, health checks run but failures don't count
2. **healthy** - Health check passing
3. **unhealthy** - Failed health checks after retries exhausted

## Troubleshooting

### Backend Starts Before Database is Ready
**Symptom**: Backend shows database connection errors
**Solution**: Verify `depends_on` with `condition: service_healthy` is set

### Health Check Always Failing
**Symptom**: Database shows as `unhealthy`
**Checks**:
1. Verify database credentials match health check parameters
2. Check database logs: `docker-compose logs db`
3. Manually test: `docker-compose exec db pg_isready -U schnitzel -d schnitzel_db`

### Slow Startup
**Symptom**: Takes long time for services to become healthy
**Adjustment**: Increase `start_period` if PostgreSQL needs more initialization time:
```yaml
healthcheck:
  start_period: 30s  # Give more time for large databases
```

## Test Coverage

All 6 F063 tests passing:
- ✅ Health check is defined
- ✅ Uses `pg_isready` command
- ✅ Has proper intervals, timeout, retries
- ✅ Backend depends on healthy database
- ✅ Has start_period configured
- ✅ Comprehensive validation of all settings

## Integration

Works seamlessly with:
- **F060**: PostgreSQL 16 base configuration
- **F061**: pgvector extension support
- **F062**: Redis service
- **F064**: Redis health checks
- **F065**: Environment variable configuration

## Production Recommendations

1. **Monitor Health Status**: Set up alerts for unhealthy services
2. **Adjust Timing**: Tune intervals based on production load
3. **Log Retention**: Capture health check failures for debugging
4. **Resource Limits**: Ensure PostgreSQL has sufficient resources to respond within timeout

## Quick Commands

```bash
# Generate docker-compose.yaml
uv run python -c "from schnitzel.generators.docker.compose import DockerComposeGenerator; DockerComposeGenerator().generate_to_file('.')"

# Start with health checks
docker-compose up -d

# Watch health status
watch -n 1 docker-compose ps

# Restart unhealthy service
docker-compose restart db

# Force recreate
docker-compose up -d --force-recreate db
```

## Files Modified

- `src/schnitzel/generators/docker/compose.py` - Added health check configuration
- `tests/integration/test_docker_postgres_health_f063.py` - Complete test coverage

## Status
✅ Implemented and tested
✅ All 48 Docker integration tests passing
✅ Production ready
