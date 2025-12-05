# GitHub Actions CI/CD Configuration

This directory contains GitHub Actions workflows for continuous integration and continuous deployment.

## Workflows

### test.yml - Main Test Suite

Runs on every push to any branch and on pull requests to `main` or `develop` branches.

#### Jobs

1. **python-tests** - Python Unit Tests
   - Runs on Python 3.11, 3.12, and 3.13
   - Executes pytest with coverage reporting
   - Uploads coverage to Codecov (Python 3.11 only)
   - Uses UV for package management

2. **python-lint** - Code Quality Checks
   - Runs ruff format checker
   - Runs ruff linter
   - Ensures code follows style guidelines

3. **python-type-check** - Static Type Analysis
   - Runs pyright type checker
   - Ensures type safety across the codebase

4. **dart-analyze** - Flutter/Dart Analysis
   - Automatically detects Flutter projects
   - Runs `flutter analyze` on all packages
   - Skips if no Flutter projects found

5. **integration-tests** - End-to-End Tests
   - Spins up Redis and PostgreSQL services
   - Runs integration test suite
   - Tests real-world scenarios with dependencies

6. **build-validation** - Package Build Check
   - Builds the Python package
   - Verifies CLI installation works
   - Ensures package can be distributed

7. **all-tests-passed** - Status Check
   - Aggregates results from all jobs
   - Provides single status for branch protection rules
   - Fails if any job fails

## Local Testing

To run tests locally before pushing:

```bash
# Navigate to schnitzel-cli directory
cd schnitzel-cli

# Install dependencies
uv sync --all-extras

# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=src/schnitzel --cov-report=term-missing

# Run linting
uv run ruff check .
uv run ruff format --check .

# Run type checking
uv run pyright src/

# Run integration tests only
uv run pytest tests/integration/ -v
```

## CI/CD Environment Variables

The workflows use the following environment variables:

- `REDIS_URL` - Redis connection string (integration tests only)
- `DATABASE_URL` - PostgreSQL connection string (integration tests only)

## Branch Protection

It's recommended to require the `all-tests-passed` job to pass before merging PRs.

Configure this in GitHub repository settings:
1. Settings → Branches
2. Add branch protection rule for `main` and `develop`
3. Require status checks: `All Tests Passed`

## Troubleshooting

### UV Installation Issues
If UV installation fails, check the installation script URL is current at https://astral.sh/uv

### Flutter Analysis Skipped
The dart-analyze job will skip if no `pubspec.yaml` files are found. This is expected if the project has no Flutter code yet.

### Integration Tests Failing
Ensure Redis and PostgreSQL services start correctly. The workflow includes health checks with automatic retries.

### Coverage Upload Fails
Coverage upload to Codecov is set to `fail_ci_if_error: false` to prevent blocking CI if Codecov is unavailable.

## Performance Optimization

The workflow uses several optimizations:
- Matrix strategy for parallel Python version testing
- Parallel job execution (all jobs run simultaneously)
- Caching via UV's built-in dependency management
- Service containers for integration tests

## Future Enhancements

Potential improvements:
- Add Docker image building and publishing
- Add deployment jobs for releases
- Add security scanning (Snyk, Dependabot)
- Add performance benchmarking
- Add deployment to PyPI on tags
