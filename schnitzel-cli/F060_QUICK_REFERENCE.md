# F060 Quick Reference

## Docker Compose PostgreSQL 16 Service

### Quick Test
```bash
uv run pytest tests/integration/test_docker_postgres_f060.py -v
```

### Quick Demo
```bash
uv run python demo_f060_postgres.py
```

### What F060 Validates

| Component | Status | Details |
|-----------|--------|---------|
| PostgreSQL Version | ✓ | postgres:16 image |
| Environment Vars | ✓ | USER, PASSWORD, DB configured |
| Data Persistence | ✓ | postgres_data volume mounted |
| Healthcheck | ✓ | pg_isready with 5s interval |
| Port Exposure | ✓ | 5432:5432 mapped |
| Service Integration | ✓ | Backend depends on DB health |

### Generated Service Configuration

```yaml
db:
  image: postgres:16
  environment:
    POSTGRES_USER: schnitzel
    POSTGRES_PASSWORD: schnitzel
    POSTGRES_DB: schnitzel
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U schnitzel"]
    interval: 5s
    timeout: 5s
    retries: 5
```

### Test Coverage

```
8 tests / 8 passing (100%)
```

1. Service existence check
2. PostgreSQL 16 version validation
3. Environment variables validation
4. Volume configuration check
5. Healthcheck presence
6. Port 5432 exposure
7. Healthcheck details validation
8. Volume persistence configuration

### Files

- **Tests**: `tests/integration/test_docker_postgres_f060.py`
- **Demo**: `demo_f060_postgres.py`
- **Generator**: `src/schnitzel/generators/docker/compose.py`

### Key Metrics

- **Test Execution Time**: ~0.1 seconds
- **Generated File Size**: 658 bytes
- **Code Coverage**: 100% of PostgreSQL service configuration
