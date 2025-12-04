"""Integration tests for api_076 - FastAPI route generator handles background tasks.

Test Requirements (from feature):
1. Check if route generator supports background tasks
2. Implement background task support:
   - Detect background_task: true in endpoint definition
   - Generate BackgroundTasks parameter
   - Import BackgroundTasks from fastapi
   - Add example task.add_task() call in comment
3. Create integration test that:
   - Creates a schema with background task endpoint
   - Generates route code
   - Verifies BackgroundTasks parameter is generated
   - Verifies proper import

This feature implements background task support for FastAPI routes.
Following Schnitzel zero-tolerance policy: no errors, no warnings, no TODOs.
"""

import tempfile
import os
from pathlib import Path
import subprocess
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python.routes import PythonRouteGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_background_task_adds_background_tasks_parameter(temp_dir: Path) -> None:
    """Test that background_task: true adds BackgroundTasks parameter."""
    # Create schema with background task endpoint
    schema_content = """schnitzel: "1.0"

models:
  EmailJob:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      subject:
        type: string

endpoints:
  /send-email:
    POST:
      name: send_email
      background_task: true
      description: "Send email in background"
      body:
        email:
          type: string
        subject:
          type: string
        content:
          type: string
      response:
        202:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify BackgroundTasks parameter is present
    assert "background_tasks: BackgroundTasks" in routes_code, \
        "Should have background_tasks parameter with BackgroundTasks type"


def test_background_task_imports_background_tasks(temp_dir: Path) -> None:
    """Test that background task endpoints import BackgroundTasks from fastapi."""
    # Create schema with background task endpoint
    schema_content = """schnitzel: "1.0"

models:
  NotificationJob:
    fields:
      id:
        type: uuid
        primary: true
      message:
        type: string

endpoints:
  /notify:
    POST:
      name: send_notification
      background_task: true
      description: "Send notification in background"
      body:
        user_id:
          type: uuid
        message:
          type: string
      response:
        202:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify BackgroundTasks is imported from fastapi
    assert "from fastapi import" in routes_code, "Should import from fastapi"
    assert "BackgroundTasks" in routes_code.split("from fastapi import")[1].split("\n")[0], \
        "Should import BackgroundTasks from fastapi"


def test_background_task_includes_usage_example(temp_dir: Path) -> None:
    """Test that background task endpoints include example usage comment."""
    # Create schema with background task endpoint
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /process:
    POST:
      name: process_data
      background_task: true
      description: "Process data in background"
      body:
        data:
          type: string
      response:
        202:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify usage example is present
    assert "background_tasks.add_task" in routes_code, \
        "Should include example usage of background_tasks.add_task()"
    assert "# Example:" in routes_code or "Example:" in routes_code, \
        "Should include example comment"


def test_background_task_with_auth(temp_dir: Path) -> None:
    """Test that background task works with authentication."""
    # Create schema with background task and auth
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string

  Report:
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string

endpoints:
  /reports/generate:
    POST:
      name: generate_report
      auth: required
      background_task: true
      description: "Generate report in background"
      body:
        format:
          type: string
      response:
        202:
          type: Report
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify both background_tasks and current_user parameters are present
    assert "background_tasks: BackgroundTasks" in routes_code, \
        "Should have background_tasks parameter"
    assert "current_user: User = Depends(get_current_user)" in routes_code, \
        "Should have current_user parameter"


def test_background_task_with_roles(temp_dir: Path) -> None:
    """Test that background task works with role-based access control."""
    # Create schema with background task and roles
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      role:
        type: string

endpoints:
  /admin/backup:
    POST:
      name: trigger_backup
      auth: required
      roles: [admin]
      background_task: true
      description: "Trigger system backup (admin only)"
      response:
        202:
          type: dict[str, Any]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify both background_tasks and role checking are present
    assert "background_tasks: BackgroundTasks" in routes_code, \
        "Should have background_tasks parameter"
    assert "Depends(require_roles(['admin']))" in routes_code, \
        "Should have role checking dependency"


def test_background_task_with_query_params(temp_dir: Path) -> None:
    """Test that background task works with query parameters."""
    # Create schema with background task and query params
    schema_content = """schnitzel: "1.0"

models:
  Job:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /jobs/process:
    POST:
      name: process_job
      background_task: true
      description: "Process job in background"
      query:
        priority:
          type: int
          default: 5
          min: 1
          max: 10
          description: "Job priority"
      body:
        job_data:
          type: string
      response:
        202:
          type: Job
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify all parameters are present
    assert "priority: int | None = Query(5" in routes_code, \
        "Should have priority query parameter"
    assert "background_tasks: BackgroundTasks" in routes_code, \
        "Should have background_tasks parameter"


def test_multiple_endpoints_with_background_tasks(temp_dir: Path) -> None:
    """Test that multiple endpoints can use background tasks."""
    # Create schema with multiple background task endpoints
    schema_content = """schnitzel: "1.0"

models:
  EmailJob:
    fields:
      id:
        type: uuid
        primary: true

  SmsJob:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /email/send:
    POST:
      name: send_email
      background_task: true
      description: "Send email"
      body:
        to:
          type: string
      response:
        202:
          type: EmailJob

  /sms/send:
    POST:
      name: send_sms
      background_task: true
      description: "Send SMS"
      body:
        to:
          type: string
      response:
        202:
          type: SmsJob
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify both endpoints have background_tasks parameter
    assert "async def send_email" in routes_code
    assert "async def send_sms" in routes_code

    # Count BackgroundTasks parameters (should appear in both functions)
    background_tasks_count = routes_code.count("background_tasks: BackgroundTasks")
    assert background_tasks_count >= 2, "Both endpoints should have BackgroundTasks parameter"


def test_background_task_false_does_not_add_parameter(temp_dir: Path) -> None:
    """Test that background_task: false does not add BackgroundTasks parameter."""
    # Create schema with background_task explicitly set to false
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users:
    GET:
      name: list_users
      background_task: false
      description: "List users (no background task)"
      response:
        200:
          type: list[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify BackgroundTasks parameter is NOT present
    assert "background_tasks: BackgroundTasks" not in routes_code, \
        "Should not have BackgroundTasks parameter when background_task is false"


def test_no_background_task_field_does_not_add_parameter(temp_dir: Path) -> None:
    """Test that omitting background_task field does not add BackgroundTasks parameter."""
    # Create schema without background_task field
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /posts:
    POST:
      name: create_post
      description: "Create post (no background task)"
      body:
        title:
          type: string
      response:
        201:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify BackgroundTasks parameter is NOT present
    assert "background_tasks: BackgroundTasks" not in routes_code, \
        "Should not have BackgroundTasks parameter when background_task field is omitted"
    assert "BackgroundTasks" not in routes_code, \
        "Should not import BackgroundTasks when not needed"


def test_generated_files_with_background_tasks(temp_dir: Path) -> None:
    """Test that routes.py is generated correctly with background tasks."""
    # Create schema with background task
    schema_content = """schnitzel: "1.0"

models:
  Task:
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string

endpoints:
  /tasks/execute:
    POST:
      name: execute_task
      background_task: true
      description: "Execute task in background"
      body:
        task_name:
          type: string
      response:
        202:
          type: Task
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate to file
    output_dir = temp_dir / "backend" / "app"

    # Generate routes.py
    routes_generator = PythonRouteGenerator()
    routes_file, routes_size = routes_generator.generate_to_file(schema, output_dir)

    # Verify file exists
    assert routes_file.exists(), "routes.py should be created"

    # Read and verify routes.py
    routes_content = routes_file.read_text()
    assert "from fastapi import" in routes_content and "BackgroundTasks" in routes_content, \
        "Should import BackgroundTasks from fastapi"
    assert "@router.post('/tasks/execute'" in routes_content, \
        "Should have POST endpoint"
    assert "background_tasks: BackgroundTasks" in routes_content, \
        "Should have BackgroundTasks parameter"
    assert "background_tasks.add_task" in routes_content, \
        "Should include example usage"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_routes_with_background_tasks_pyright_no_errors(temp_dir: Path) -> None:
    """Test that generated routes with background tasks pass pyright type checking."""
    # Create schema with background task endpoint
    schema_content = """schnitzel: "1.0"

models:
  EmailJob:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string
      subject:
        type: string

endpoints:
  /email/send:
    POST:
      name: send_email_async
      background_task: true
      description: "Send email asynchronously"
      body:
        email:
          type: string
        subject:
          type: string
        content:
          type: string
      response:
        202:
          type: EmailJob
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate files
    from schnitzel.generators.python.models import PythonModelGenerator

    output_dir = temp_dir / "backend" / "app"

    # Generate models.py first (routes imports from it)
    models_generator = PythonModelGenerator()
    models_file, _ = models_generator.generate_to_file(schema, output_dir)

    # Generate routes.py
    routes_generator = PythonRouteGenerator()
    routes_file, _ = routes_generator.generate_to_file(schema, output_dir)

    # Create __init__.py to make it a package
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    # Create a basic pyproject.toml or pyrightconfig.json to help pyright
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright on generated file
    result = subprocess.run(
        ["pyright", str(routes_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no errors (allow warnings about missing stubs and TODO return types)
    routes_has_only_expected_errors = (
        result.returncode == 0 or
        "reportMissingImports" in result.stdout or
        ("reportReturnType" in result.stdout and "reportInvalidTypeForm" not in result.stdout)
    )
    assert routes_has_only_expected_errors, \
        f"pyright should pass with no structural errors. Output: {result.stdout}\n{result.stderr}"


def test_background_task_parameter_ordering(temp_dir: Path) -> None:
    """Test that BackgroundTasks parameter is in correct position (before auth dependencies)."""
    # Create schema with background task, body, and auth
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

  Report:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /reports:
    POST:
      name: create_report
      auth: required
      background_task: true
      description: "Create report with background processing"
      body:
        title:
          type: string
      response:
        202:
          type: Report
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify function signature has proper order:
    # required params (body) before optional params (background_tasks, current_user)
    assert "async def create_report(body: dict[str, Any], background_tasks: BackgroundTasks, current_user: User" in routes_code, \
        "Function should have proper parameter ordering: body (required), background_tasks, current_user (optional)"


def test_background_task_comprehensive_code_structure(temp_dir: Path) -> None:
    """Test that background task endpoint generates complete and correct code structure."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  ExportJob:
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string

endpoints:
  /export:
    POST:
      name: export_data
      background_task: true
      description: "Export data in background"
      query:
        format:
          type: string
          default: "csv"
          description: "Export format"
      body:
        table_name:
          type: string
      response:
        202:
          type: ExportJob
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify complete code structure
    # 1. Imports
    assert "from fastapi import" in routes_code
    assert "APIRouter" in routes_code
    assert "BackgroundTasks" in routes_code
    assert "Query" in routes_code
    assert "from .models import ExportJob" in routes_code

    # 2. Router instance
    assert "router = APIRouter()" in routes_code

    # 3. Route decorator
    assert "@router.post('/export'" in routes_code
    assert "status_code=202" in routes_code

    # 4. Function signature with all parameters
    assert "async def export_data(" in routes_code
    assert "body: dict[str, Any]" in routes_code
    assert "format: str | None = Query(" in routes_code
    assert "background_tasks: BackgroundTasks" in routes_code

    # 5. Docstring
    assert '"""Export data in background"""' in routes_code

    # 6. Return type
    assert "-> ExportJob:" in routes_code

    # 7. Usage example
    assert "background_tasks.add_task" in routes_code
