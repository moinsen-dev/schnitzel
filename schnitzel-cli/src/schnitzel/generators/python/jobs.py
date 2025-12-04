"""Python Temporal job generator for Schnitzel schemas.

Generates Temporal workflow definitions with proper scheduling, retry policies,
and timeout configurations from the jobs section of a Schnitzel schema.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from jinja2 import Environment, PackageLoader, select_autoescape

from schnitzel.schema.models import SchnitzelSchema, JobConfig
from schnitzel.generators.validation_utils import validate_cron_expression, validate_timeout_format


def _parse_duration(duration_str: str | int) -> int:
    """Parse a duration string into seconds.

    Args:
        duration_str: Duration as string (e.g., "30m", "1h", "3600") or integer (seconds)

    Returns:
        Duration in seconds

    Examples:
        >>> _parse_duration("30m")
        1800
        >>> _parse_duration("1h")
        3600
        >>> _parse_duration("1d")
        86400
        >>> _parse_duration(300)
        300
        >>> _parse_duration("300")
        300
    """
    # If already an integer, return as-is
    if isinstance(duration_str, int):
        return duration_str

    # If string representation of an integer, convert it
    if isinstance(duration_str, str):
        duration_str = duration_str.strip()
        if duration_str.isdigit():
            return int(duration_str)

        # Parse time units
        unit_map = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
        }

        # Extract number and unit
        if len(duration_str) < 2:
            raise ValueError(f"Invalid duration format: {duration_str}")

        number_part = duration_str[:-1]
        unit_part = duration_str[-1].lower()

        if unit_part not in unit_map:
            raise ValueError(f"Unknown time unit: {unit_part}. Use s, m, h, or d")

        try:
            number = int(number_part)
        except ValueError as e:
            raise ValueError(f"Invalid duration number: {number_part}") from e

        return number * unit_map[unit_part]

    raise ValueError(f"Duration must be string or int, got {type(duration_str)}")


def _to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase.

    Args:
        snake_str: String in snake_case format

    Returns:
        String in PascalCase format

    Examples:
        >>> _to_pascal_case("sync_menu_embeddings")
        'SyncMenuEmbeddings'
        >>> _to_pascal_case("send_daily_promotions")
        'SendDailyPromotions'
    """
    components = snake_str.split('_')
    return ''.join(word.capitalize() for word in components)


class TemporalJobGenerator:
    """Generates Temporal workflow definitions from Schnitzel schemas."""

    def __init__(self):
        """Initialize the Temporal job generator."""
        self.env = Environment(
            loader=PackageLoader('schnitzel', 'templates/python'),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, schema: SchnitzelSchema) -> str:
        """
        Generate Python Temporal workflow definitions from a schema.

        Args:
            schema: The Schnitzel schema to generate workflows from

        Returns:
            Generated Python code as a string
        """
        # Check if schema has jobs
        if not schema.jobs:
            return self._generate_empty_jobs()

        # Parse jobs and prepare data for template
        jobs_data = []
        for job_name, job_def in schema.jobs.items():
            # Handle both dict (for raw YAML parsing) and JobConfig model instances
            job_info = self._parse_job_definition(job_name, job_def)
            jobs_data.append(job_info)

        # Load and render template
        template = self.env.get_template('jobs.py.j2')
        return template.render(jobs=jobs_data)

    def generate_to_file(
        self,
        schema: SchnitzelSchema,
        output_dir: str | Path,
        schema_source: str = "schema.schnitzel.yaml",
        dry_run: bool = False,
    ) -> tuple[Path, int]:
        """
        Generate Python Temporal workflows and write them to a file.

        Creates the output directory if it doesn't exist, adds a header comment with
        generation metadata, and writes the workflows to 'jobs.py' in the specified directory.

        Args:
            schema: The Schnitzel schema to generate workflows from
            output_dir: Directory where jobs.py should be written (can be string or Path)
            schema_source: Optional name of the source schema file for documentation
            dry_run: If True, return file info without writing (default: False)

        Returns:
            Tuple of (Path object pointing to jobs.py file, size in bytes)

        Example:
            >>> generator = TemporalJobGenerator()
            >>> output_path, size = generator.generate_to_file(schema, "backend/app/generated")
            >>> print(f"Jobs written to: {output_path} ({size} bytes)")
        """
        # Convert to Path object
        output_path = Path(output_dir)

        # Generate the workflow code
        jobs_code = self.generate(schema)

        # Build header comment
        timestamp = datetime.now().isoformat()
        header = f"""# Generated by Schnitzel Framework
# DO NOT EDIT - This file is auto-generated
# Generated at: {timestamp}
# Source: {schema_source}

"""

        # Combine header with generated code
        full_code = header + jobs_code

        # Calculate file path and size
        jobs_file = output_path / "jobs.py"
        file_size = len(full_code.encode("utf-8"))

        # If dry-run, return without writing
        if dry_run:
            return jobs_file, file_size

        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Warn if file already exists
        if jobs_file.exists():
            print(f"Warning: Overwriting existing file: {jobs_file}")

        jobs_file.write_text(full_code, encoding="utf-8")

        return jobs_file, file_size

    def _generate_empty_jobs(self) -> str:
        """Generate a minimal jobs file when no jobs are defined."""
        return '''"""No Temporal workflows defined in schema."""

# No jobs section found in schema
# To add scheduled jobs, add a 'jobs' section to your schema.schnitzel.yaml
'''

    def _parse_job_definition(self, job_name: str, job_def: Dict[str, Any] | JobConfig) -> Dict[str, Any]:
        """Parse a job definition into template-ready data.

        Args:
            job_name: Name of the job (e.g., "sync_menu_embeddings")
            job_def: Job definition from schema (dict or JobConfig model)

        Returns:
            Dictionary with job information for template rendering

        Raises:
            ValueError: If validation fails
        """
        # Handle JobConfig model instances
        if isinstance(job_def, JobConfig):
            # Extract values from JobConfig model
            workflow_name = job_def.workflow
            timeout_raw = job_def.timeout
            schedule = job_def.schedule  # Can be None for manual-trigger jobs
            description = job_name  # JobConfig doesn't have description field
            params = job_def.params or {}  # Workflow parameters

            # Parse retry policy from model
            if job_def.retry_policy:
                retry_max_attempts = job_def.retry_policy.max_attempts
                retry_initial_raw = job_def.retry_policy.initial_interval
                retry_backoff_coefficient = job_def.retry_policy.backoff_coefficient or 1.0
            else:
                retry_max_attempts = 1
                retry_initial_raw = "1m"
                retry_backoff_coefficient = 1.0
        else:
            # Handle dict format (for raw YAML parsing)
            workflow_name = job_def.get("workflow", job_name)
            timeout_raw = job_def.get("timeout", 300)
            schedule = job_def.get("schedule")  # Can be None
            description = job_def.get("description", f"Scheduled job: {job_name}")
            params = job_def.get("params", {})  # Workflow parameters

            # Parse retry policy from dict
            retry_config = job_def.get("retry", {})
            retry_max_attempts = retry_config.get("max_attempts", 1)
            retry_initial_raw = retry_config.get("initial_interval", "1m")

            # Determine backoff coefficient based on backoff strategy
            backoff_strategy = retry_config.get("backoff", "linear")
            if backoff_strategy == "exponential":
                retry_backoff_coefficient = 2.0
            elif backoff_strategy == "linear":
                retry_backoff_coefficient = 1.0
            else:
                retry_backoff_coefficient = 1.0

        # Validate cron expression if schedule is provided (F99)
        if schedule:
            try:
                validate_cron_expression(schedule)
            except ValueError as e:
                raise ValueError(f"Job '{job_name}': {e}") from e

        # Validate timeout format (F100)
        try:
            validate_timeout_format(str(timeout_raw))
        except ValueError as e:
            raise ValueError(f"Job '{job_name}': {e}") from e

        # Generate class name from job name (PascalCase + Workflow suffix)
        class_name = _to_pascal_case(job_name) + "Workflow"

        # Parse timeout (default: 300 seconds = 5 minutes)
        timeout_seconds = _parse_duration(timeout_raw)

        # Parse initial interval for retry
        retry_initial_interval_seconds = _parse_duration(retry_initial_raw)

        # Parse workflow parameters with Python type mapping
        from schnitzel.schema.models import PYTHON_TYPE_MAP
        workflow_params = []
        for param_name, param_type in params.items():
            python_type = PYTHON_TYPE_MAP.get(param_type.lower(), param_type)
            workflow_params.append({
                "name": param_name,
                "type": python_type,
                "schema_type": param_type
            })

        return {
            "name": job_name,
            "class_name": class_name,
            "workflow_name": workflow_name,
            "description": description,
            "schedule": schedule,  # Can be None
            "has_schedule": schedule is not None and schedule != "",
            "timeout_seconds": timeout_seconds,
            "retry_max_attempts": retry_max_attempts,
            "retry_initial_interval_seconds": retry_initial_interval_seconds,
            "retry_backoff_coefficient": retry_backoff_coefficient,
            "params": workflow_params,
            "has_params": len(workflow_params) > 0,
        }


# Backward-compatible alias
PythonJobGenerator = TemporalJobGenerator
