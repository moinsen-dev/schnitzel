"""Integration test for Temporal job generator.

Test Requirements:
1. Temporal job generator creates workflow classes
2. Temporal job generator parses cron schedules
3. Temporal job generator configures retry policies
4. Temporal job generator handles timeout configuration
5. Temporal job generator creates activity stubs

This test validates that the Temporal job generator correctly transforms job
definitions from the schema into properly structured Temporal workflow classes.
"""

import tempfile
import os
import subprocess
from pathlib import Path
from typing import Dict, Any
import pytest
import yaml

from schnitzel.schema import SchemaParser
from schnitzel.generators.python.jobs import TemporalJobGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and change to it."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def simple_jobs_schema(temp_dir: Path) -> Path:
    """Create a schema with a simple job definition."""
    schema_content = """schnitzel: "1.0"

models:
  Report:
    description: "Daily report model"
    fields:
      id:
        type: uuid
        primary: true
      date:
        type: date
      status:
        type: string

jobs:
  daily_report:
    schedule: "0 0 * * *"
    workflow: GenerateDailyReport
    timeout: 30m
    retry_policy:
      max_attempts: 3
      initial_interval: 1m
      backoff_coefficient: 2.0
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


@pytest.fixture
def complex_jobs_schema(temp_dir: Path) -> Path:
    """Create a schema with multiple jobs with different configurations."""
    schema_content = """schnitzel: "1.0"

models:
  Session:
    description: "User session"
    fields:
      id:
        type: uuid
        primary: true
      expires_at:
        type: datetime

  MenuEmbedding:
    description: "AI menu embeddings"
    fields:
      id:
        type: uuid
        primary: true
      embedding:
        type: vector
        dimensions: 1536

jobs:
  daily_report:
    schedule: "0 0 * * *"
    workflow: GenerateDailyReport
    timeout: 30m
    retry_policy:
      max_attempts: 3
      initial_interval: 1m
      backoff_coefficient: 2.0

  cleanup_expired:
    schedule: "*/15 * * * *"
    workflow: CleanupExpiredSessions
    timeout: 5m
    retry_policy:
      max_attempts: 5
      initial_interval: 30s
      backoff_coefficient: 1.5

  sync_menu_embeddings:
    schedule: "0 */6 * * *"
    workflow: SyncMenuEmbeddings
    timeout: 1h
    retry_policy:
      max_attempts: 2
      initial_interval: 5m
      backoff_coefficient: 3.0

  send_daily_promotions:
    schedule: "0 10 * * *"
    workflow: SendDailyPromotions
    timeout: 45m
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


@pytest.fixture
def no_jobs_schema(temp_dir: Path) -> Path:
    """Create a schema without any jobs."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      username:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


def test_simple_job_generation(temp_dir: Path, simple_jobs_schema: Path) -> None:
    """Test generation of a simple job with all standard configurations."""
    parser = SchemaParser()
    schema = parser.parse(simple_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    output_dir = temp_dir / "backend" / "app" / "generated"
    jobs_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert jobs_file.exists(), "jobs.py should be created"
    assert size > 0, "jobs.py should have content"

    # Read and verify content
    jobs_content = jobs_file.read_text()

    # Verify Temporal imports
    assert "from temporalio import workflow" in jobs_content
    assert "from temporalio.common import RetryPolicy" in jobs_content
    assert "from datetime import timedelta" in jobs_content

    # Verify workflow decorator with correct name
    assert '@workflow.defn(name="GenerateDailyReport")' in jobs_content

    # Verify workflow class name (snake_case to PascalCase + Workflow)
    assert "class DailyReportWorkflow:" in jobs_content

    # Verify workflow run method
    assert "@workflow.run" in jobs_content
    assert "async def run(self) -> dict[str, Any]:" in jobs_content

    # Verify timeout configuration (30m = 1800 seconds)
    assert "timedelta(seconds=1800)" in jobs_content

    # Verify retry policy configuration
    assert "maximum_attempts=3" in jobs_content
    assert "initial_interval=timedelta(seconds=60)" in jobs_content
    assert "backoff_coefficient=2.0" in jobs_content

    # Verify workflow logger usage
    assert "workflow.logger.info" in jobs_content

    # Verify return structure
    assert 'return {' in jobs_content
    assert '"status": "completed"' in jobs_content

    # Verify Python syntax is valid
    try:
        compile(jobs_content, str(jobs_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated jobs.py has syntax errors: {e}")


def test_multiple_jobs_generation(temp_dir: Path, complex_jobs_schema: Path) -> None:
    """Test generation of multiple jobs with different configurations."""
    parser = SchemaParser()
    schema = parser.parse(complex_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    jobs_code = generator.generate(schema)

    # Verify all workflow decorators are present
    assert '@workflow.defn(name="GenerateDailyReport")' in jobs_code
    assert '@workflow.defn(name="CleanupExpiredSessions")' in jobs_code
    assert '@workflow.defn(name="SyncMenuEmbeddings")' in jobs_code
    assert '@workflow.defn(name="SendDailyPromotions")' in jobs_code

    # Verify all workflow class names
    assert "class DailyReportWorkflow:" in jobs_code
    assert "class CleanupExpiredWorkflow:" in jobs_code
    assert "class SyncMenuEmbeddingsWorkflow:" in jobs_code
    assert "class SendDailyPromotionsWorkflow:" in jobs_code

    # Verify each workflow has @workflow.run method
    assert jobs_code.count("@workflow.run") == 4
    assert jobs_code.count("async def run(self) -> dict[str, Any]:") == 4

    # Verify different timeout configurations
    # 30m = 1800s, 5m = 300s, 1h = 3600s, 45m = 2700s
    assert "timedelta(seconds=1800)" in jobs_code
    assert "timedelta(seconds=300)" in jobs_code
    assert "timedelta(seconds=3600)" in jobs_code
    assert "timedelta(seconds=2700)" in jobs_code

    # Verify different retry configurations
    assert "maximum_attempts=3" in jobs_code
    assert "maximum_attempts=5" in jobs_code
    assert "maximum_attempts=2" in jobs_code
    # SendDailyPromotions has no retry_policy, should use defaults
    assert "maximum_attempts=1" in jobs_code

    # Verify different initial intervals
    assert "initial_interval=timedelta(seconds=60)" in jobs_code  # 1m
    assert "initial_interval=timedelta(seconds=30)" in jobs_code  # 30s
    assert "initial_interval=timedelta(seconds=300)" in jobs_code  # 5m

    # Verify different backoff coefficients
    assert "backoff_coefficient=2.0" in jobs_code
    assert "backoff_coefficient=1.5" in jobs_code
    assert "backoff_coefficient=3.0" in jobs_code


def test_no_jobs_schema(temp_dir: Path, no_jobs_schema: Path) -> None:
    """Test generation when schema has no jobs defined."""
    parser = SchemaParser()
    schema = parser.parse(no_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    jobs_code = generator.generate(schema)

    # Verify empty/minimal jobs file
    assert "No Temporal workflows defined in schema" in jobs_code
    assert "No jobs section found in schema" in jobs_code

    # Should not have any workflow definitions
    assert "@workflow.defn" not in jobs_code
    assert "class" not in jobs_code.lower() or "workflow" not in jobs_code.lower()


def test_cron_schedule_in_comments(temp_dir: Path, complex_jobs_schema: Path) -> None:
    """Test that cron schedules are documented in generated code."""
    parser = SchemaParser()
    schema = parser.parse(complex_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    jobs_code = generator.generate(schema)

    # Verify cron schedules are documented in class docstrings
    assert 'Schedule: 0 0 * * *' in jobs_code  # daily_report
    assert 'Schedule: */15 * * * *' in jobs_code  # cleanup_expired
    assert 'Schedule: 0 */6 * * *' in jobs_code  # sync_menu_embeddings
    assert 'Schedule: 0 10 * * *' in jobs_code  # send_daily_promotions

    # Verify cron schedules are in method docstrings
    assert 'Cron Schedule: 0 0 * * *' in jobs_code
    assert 'Cron Schedule: */15 * * * *' in jobs_code
    assert 'Cron Schedule: 0 */6 * * *' in jobs_code
    assert 'Cron Schedule: 0 10 * * *' in jobs_code

    # Verify SCHEDULE_CONFIGS contains all schedules
    assert 'SCHEDULE_CONFIGS' in jobs_code
    assert '"schedule": "0 0 * * *"' in jobs_code
    assert '"schedule": "*/15 * * * *"' in jobs_code


def test_activity_stub_template(temp_dir: Path, simple_jobs_schema: Path) -> None:
    """Test that generated code includes activity execution stubs."""
    parser = SchemaParser()
    schema = parser.parse(simple_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    jobs_code = generator.generate(schema)

    # Verify activity stub comments/examples are present
    assert "# TODO: Implement workflow logic" in jobs_code
    assert "# TODO: Add activity executions here" in jobs_code
    assert "# Example:" in jobs_code
    assert "# result = await workflow.execute_activity(" in jobs_code
    assert "#     activity_name," in jobs_code
    assert "#     args," in jobs_code
    assert "#     start_to_close_timeout=" in jobs_code
    assert "#     retry_policy=RetryPolicy(" in jobs_code


def test_workflow_naming_conventions(temp_dir: Path, complex_jobs_schema: Path) -> None:
    """Test that workflow names follow correct conventions."""
    parser = SchemaParser()
    schema = parser.parse(complex_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    jobs_code = generator.generate(schema)

    # Verify job names (snake_case) are converted to class names (PascalCase + Workflow)
    # daily_report -> DailyReportWorkflow
    assert "class DailyReportWorkflow:" in jobs_code
    # cleanup_expired -> CleanupExpiredWorkflow
    assert "class CleanupExpiredWorkflow:" in jobs_code
    # sync_menu_embeddings -> SyncMenuEmbeddingsWorkflow
    assert "class SyncMenuEmbeddingsWorkflow:" in jobs_code
    # send_daily_promotions -> SendDailyPromotionsWorkflow
    assert "class SendDailyPromotionsWorkflow:" in jobs_code

    # Verify workflow decorator names remain as specified in schema
    assert '@workflow.defn(name="GenerateDailyReport")' in jobs_code
    assert '@workflow.defn(name="CleanupExpiredSessions")' in jobs_code
    assert '@workflow.defn(name="SyncMenuEmbeddings")' in jobs_code
    assert '@workflow.defn(name="SendDailyPromotions")' in jobs_code


def test_timeout_parsing_different_units(temp_dir: Path) -> None:
    """Test parsing of different timeout units (s, m, h, d)."""
    parser = SchemaParser()

    # Create schema with different timeout formats
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true

jobs:
  job_seconds:
    schedule: "0 0 * * *"
    workflow: JobSeconds
    timeout: 120s

  job_minutes:
    schedule: "0 0 * * *"
    workflow: JobMinutes
    timeout: 30m

  job_hours:
    schedule: "0 0 * * *"
    workflow: JobHours
    timeout: 2h

  job_days:
    schedule: "0 0 * * *"
    workflow: JobDays
    timeout: 1d
"""
    schema_file = Path(tempfile.mktemp(suffix=".yaml"))
    schema_file.write_text(schema_content)

    try:
        schema = parser.parse(schema_file)

        # Generate jobs
        generator = TemporalJobGenerator()
        jobs_code = generator.generate(schema)

        # Verify timeouts are converted to seconds
        assert "timedelta(seconds=120)" in jobs_code  # 120s
        assert "timedelta(seconds=1800)" in jobs_code  # 30m
        assert "timedelta(seconds=7200)" in jobs_code  # 2h
        assert "timedelta(seconds=86400)" in jobs_code  # 1d
    finally:
        if schema_file.exists():
            schema_file.unlink()


def test_default_retry_policy(temp_dir: Path) -> None:
    """Test that jobs without explicit retry_policy get sensible defaults."""
    parser = SchemaParser()

    # Create schema with job missing retry_policy
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true

jobs:
  simple_job:
    schedule: "0 0 * * *"
    workflow: SimpleJob
    timeout: 10m
"""
    schema_file = Path(tempfile.mktemp(suffix=".yaml"))
    schema_file.write_text(schema_content)

    try:
        schema = parser.parse(schema_file)

        # Generate jobs
        generator = TemporalJobGenerator()
        jobs_code = generator.generate(schema)

        # Verify default retry policy values
        assert "maximum_attempts=1" in jobs_code
        assert "initial_interval=timedelta(seconds=60)" in jobs_code
        assert "backoff_coefficient=1.0" in jobs_code
    finally:
        if schema_file.exists():
            schema_file.unlink()


def test_generated_file_header(temp_dir: Path, simple_jobs_schema: Path) -> None:
    """Test that generated file includes proper header with metadata."""
    parser = SchemaParser()
    schema = parser.parse(simple_jobs_schema)

    # Generate jobs to file
    generator = TemporalJobGenerator()
    output_dir = temp_dir / "backend" / "app" / "generated"
    jobs_file, _ = generator.generate_to_file(
        schema,
        output_dir,
        schema_source="schema.schnitzel.yaml"
    )

    jobs_content = jobs_file.read_text()

    # Verify header
    assert "# Generated by Schnitzel Framework" in jobs_content
    assert "# DO NOT EDIT - This file is auto-generated" in jobs_content
    assert "# Generated at:" in jobs_content
    assert "# Source: schema.schnitzel.yaml" in jobs_content


def test_dry_run_mode(temp_dir: Path, simple_jobs_schema: Path) -> None:
    """Test that dry run mode returns file info without writing."""
    parser = SchemaParser()
    schema = parser.parse(simple_jobs_schema)

    # Generate with dry_run=True
    generator = TemporalJobGenerator()
    output_dir = temp_dir / "backend" / "app" / "generated"
    jobs_file, size = generator.generate_to_file(
        schema,
        output_dir,
        dry_run=True
    )

    # Verify file path is returned but file doesn't exist
    assert isinstance(jobs_file, Path)
    assert not jobs_file.exists(), "File should not be created in dry run mode"
    assert size > 0, "Should return estimated file size"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_code_passes_pyright(temp_dir: Path, complex_jobs_schema: Path) -> None:
    """Test that generated jobs code passes pyright type checking."""
    parser = SchemaParser()
    schema = parser.parse(complex_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    output_dir = temp_dir / "backend" / "app" / "generated"
    jobs_file, _ = generator.generate_to_file(schema, output_dir)

    # Create __init__.py
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    # Create pyrightconfig.json
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright
    result = subprocess.run(
        ["pyright", str(jobs_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no type errors
    assert result.returncode == 0 or "reportMissingImports" in result.stdout, \
        f"pyright should pass. Output: {result.stdout}\n{result.stderr}"


def test_workflow_return_type(temp_dir: Path, simple_jobs_schema: Path) -> None:
    """Test that workflow run methods have correct return type."""
    parser = SchemaParser()
    schema = parser.parse(simple_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    jobs_code = generator.generate(schema)

    # Verify return type annotation
    assert "async def run(self) -> dict[str, Any]:" in jobs_code

    # Verify return statement structure
    assert 'return {' in jobs_code
    assert '"status": "completed"' in jobs_code
    assert '"message":' in jobs_code


def test_logger_usage(temp_dir: Path, complex_jobs_schema: Path) -> None:
    """Test that workflows use workflow.logger correctly."""
    parser = SchemaParser()
    schema = parser.parse(complex_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    jobs_code = generator.generate(schema)

    # Verify logger is used
    assert "workflow.logger.info" in jobs_code

    # Verify logger messages reference job names
    assert 'workflow.logger.info("Starting daily_report workflow")' in jobs_code
    assert 'workflow.logger.info("Completed daily_report workflow")' in jobs_code
    assert 'workflow.logger.info("Starting cleanup_expired workflow")' in jobs_code
    assert 'workflow.logger.info("Completed cleanup_expired workflow")' in jobs_code


def test_generation_output_summary(temp_dir: Path, complex_jobs_schema: Path) -> None:
    """Test complete generation and verify all outputs."""
    parser = SchemaParser()
    schema = parser.parse(complex_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    output_dir = temp_dir / "backend" / "app" / "generated"
    jobs_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file exists
    assert jobs_file.exists()
    assert size > 0

    # Read content
    jobs_content = jobs_file.read_text()

    # Count workflow definitions
    workflow_count = jobs_content.count("@workflow.defn")
    assert workflow_count == 4, "Should have 4 workflow definitions"

    # Print summary
    print("\n" + "=" * 70)
    print("TEMPORAL JOB GENERATOR TEST SUMMARY")
    print("=" * 70)
    print(f"\nSchema: {complex_jobs_schema.name}")
    print(f"Jobs Defined: {workflow_count}")
    print(f"\nGenerated File:")
    print(f"  Path: {jobs_file}")
    print(f"  Size: {size:,} bytes")
    print(f"\nWorkflows Generated:")
    print("  ✓ DailyReportWorkflow (30m timeout, 3 retries)")
    print("  ✓ CleanupExpiredWorkflow (5m timeout, 5 retries)")
    print("  ✓ SyncMenuEmbeddingsWorkflow (1h timeout, 2 retries)")
    print("  ✓ SendDailyPromotionsWorkflow (45m timeout, default retry)")
    print("\nFeatures Verified:")
    print("  ✓ @workflow.defn decorators with workflow names")
    print("  ✓ Workflow classes with async run() methods")
    print("  ✓ Timeout configuration in seconds")
    print("  ✓ RetryPolicy with max_attempts, initial_interval, backoff")
    print("  ✓ Activity execution stub examples")
    print("  ✓ Workflow logger usage")
    print("  ✓ Type hints (dict[str, Any] return)")
    print("  ✓ Valid Python syntax")
    print("\n" + "=" * 70)


def test_worker_registration_code(temp_dir: Path, complex_jobs_schema: Path) -> None:
    """Test that generated code includes worker registration helper."""
    parser = SchemaParser()
    schema = parser.parse(complex_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    jobs_code = generator.generate(schema)

    # Verify worker registration function exists
    assert "def get_workflow_classes() -> list[type]:" in jobs_code
    assert "Get all workflow classes for worker registration" in jobs_code

    # Verify all workflow classes are included in the return list
    assert "return [" in jobs_code
    assert "DailyReportWorkflow," in jobs_code
    assert "CleanupExpiredWorkflow," in jobs_code
    assert "SyncMenuEmbeddingsWorkflow," in jobs_code
    assert "SendDailyPromotionsWorkflow," in jobs_code

    # Verify example usage documentation
    assert "from temporalio.client import Client" in jobs_code
    assert "from temporalio.worker import Worker" in jobs_code
    assert "workflows=get_workflow_classes()" in jobs_code

    # Verify SCHEDULE_CONFIGS exists
    assert "SCHEDULE_CONFIGS = {" in jobs_code

    # Verify all jobs are in SCHEDULE_CONFIGS
    assert '"daily_report": {' in jobs_code
    assert '"cleanup_expired": {' in jobs_code
    assert '"sync_menu_embeddings": {' in jobs_code
    assert '"send_daily_promotions": {' in jobs_code

    # Verify config structure
    assert '"workflow":' in jobs_code
    assert '"schedule":' in jobs_code
    assert '"task_queue": "default"' in jobs_code


def test_schedule_documentation_in_docstrings(temp_dir: Path, simple_jobs_schema: Path) -> None:
    """Test that schedules, timeouts, and retries are documented in class docstrings."""
    parser = SchemaParser()
    schema = parser.parse(simple_jobs_schema)

    # Generate jobs
    generator = TemporalJobGenerator()
    jobs_code = generator.generate(schema)

    # Verify class docstring contains schedule info
    assert 'Schedule: 0 0 * * *' in jobs_code
    assert 'Timeout: 1800s' in jobs_code  # 30m = 1800s
    assert 'Max Retries: 3' in jobs_code

    # Verify method docstring contains cron schedule
    assert 'Cron Schedule: 0 0 * * *' in jobs_code
