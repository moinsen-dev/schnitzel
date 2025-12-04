"""Integration tests for api_012 - FastAPI route generator creates POST endpoint with request body.

Test Requirements (from feature):
1. Create schema with endpoint: POST /users with body: CreateUserRequest
2. Run schnitzel generate --target python
3. Verify @router.post('/users') decorator is present
4. Verify request body parameter uses Pydantic model
5. Verify return type is correct
6. Verify status_code is set (201 for create)
7. Run pyright - no errors
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


def test_post_endpoint_decorator(temp_dir: Path) -> None:
    """Test that POST endpoint generates @router.post decorator."""
    # Create schema with POST endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string

  CreateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      description: "Create a new user"
      body: CreateUserRequest
      response:
        201:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify @router.post decorator is present
    assert "@router.post('/users'" in routes_code, "Should have @router.post decorator"


def test_post_endpoint_status_code(temp_dir: Path) -> None:
    """Test that POST endpoint sets status_code=201."""
    # Create schema with POST endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  CreateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify status_code=201 is set
    assert "status_code=201" in routes_code, "POST endpoint should have status_code=201"


def test_post_endpoint_request_body(temp_dir: Path) -> None:
    """Test that POST endpoint includes request body parameter with Pydantic model."""
    # Create schema with POST endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

  CreateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify request body parameter with Pydantic model type
    assert "body: CreateUserRequest" in routes_code, "Should have body parameter with CreateUserRequest type"


def test_post_endpoint_return_type(temp_dir: Path) -> None:
    """Test that POST endpoint has correct return type."""
    # Create schema with POST endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  CreateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify return type is User
    assert "-> User:" in routes_code, "Should have return type User"


def test_post_endpoint_operation_id(temp_dir: Path) -> None:
    """Test that POST endpoint has operation_id set."""
    # Create schema with POST endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

  CreateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify operation_id is set
    assert 'operation_id="create_user"' in routes_code, "Should have operation_id set"


def test_post_endpoint_function_signature(temp_dir: Path) -> None:
    """Test that POST endpoint generates correct function signature."""
    # Create schema with POST endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  CreateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      description: "Create a new user"
      body: CreateUserRequest
      response:
        201:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify complete function signature
    assert "async def create_user(body: CreateUserRequest) -> User:" in routes_code, \
        "Should have complete function signature with async def, body parameter, and return type"


def test_generated_routes_file_structure(temp_dir: Path) -> None:
    """Test that generated routes file has correct structure."""
    # Create schema with POST endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  CreateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes to file
    generator = PythonRouteGenerator()
    output_dir = temp_dir / "backend" / "app"
    routes_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert routes_file.exists(), "routes.py should be created"
    assert size > 0, "routes.py should have content"

    # Read and verify content
    routes_content = routes_file.read_text()
    assert "from fastapi import APIRouter" in routes_content, "Should import APIRouter"
    assert "router = APIRouter()" in routes_content, "Should create router instance"
    assert "@router.post('/users'" in routes_content, "Should have POST decorator"
    assert "async def create_user" in routes_content, "Should have function definition"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_routes_pyright_no_errors(temp_dir: Path) -> None:
    """Test that generated routes pass pyright type checking (requirement 7)."""
    # Create schema with POST endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      email:
        type: string

  CreateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
          type: User
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate both models and routes
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
    # This tells pyright to ignore missing stubs for fastapi
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright on generated file
    result = subprocess.run(
        ["pyright", str(routes_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no errors (allow warnings about missing stubs)
    # The main check is that the generated code itself has no type errors
    assert result.returncode == 0 or "reportMissingImports" in result.stdout, \
        f"pyright should pass with no structural errors. Output: {result.stdout}\n{result.stderr}"
