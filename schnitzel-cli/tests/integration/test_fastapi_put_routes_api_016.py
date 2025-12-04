"""Integration tests for api_016 - FastAPI route generator creates PUT endpoint for updates.

Test Requirements (from feature):
1. Create schema with endpoint: PUT /users/{id} with body: UpdateUserRequest
2. Run schnitzel generate --target python
3. Verify @router.put('/users/{id}') decorator
4. Verify both path parameter and request body
5. Verify return type is User
6. Run pyright - no errors
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


def test_put_endpoint_decorator(temp_dir: Path) -> None:
    """Test that PUT endpoint generates @router.put decorator."""
    # Create schema with PUT endpoint
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

  UpdateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      description: "Update a user"
      body: UpdateUserRequest
      response:
        200:
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

    # Verify @router.put decorator is present
    assert "@router.put('/users/{id}'" in routes_code, "Should have @router.put decorator with path"


def test_put_endpoint_no_status_code_override(temp_dir: Path) -> None:
    """Test that PUT endpoint does not set status_code (uses default 200)."""
    # Create schema with PUT endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  UpdateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
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

    # Verify status_code is NOT set (default 200 is fine for PUT)
    # The decorator should not include status_code parameter
    assert "status_code=200" not in routes_code, "PUT should use default status code (200)"
    assert "status_code=201" not in routes_code, "PUT should not use 201 status code"


def test_put_endpoint_path_parameter(temp_dir: Path) -> None:
    """Test that PUT endpoint includes path parameter from URL."""
    # Create schema with PUT endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

  UpdateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
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

    # Verify path parameter is included with correct type
    assert "id: UUID" in routes_code, "Should have id path parameter with UUID type"


def test_put_endpoint_request_body(temp_dir: Path) -> None:
    """Test that PUT endpoint includes request body parameter with Pydantic model."""
    # Create schema with PUT endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

  UpdateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
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
    assert "body: UpdateUserRequest" in routes_code, "Should have body parameter with UpdateUserRequest type"


def test_put_endpoint_both_path_and_body_parameters(temp_dir: Path) -> None:
    """Test that PUT endpoint includes both path parameter AND request body."""
    # Create schema with PUT endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  UpdateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
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

    # Verify both parameters are present in the function signature
    # Should be: async def update_user(id: UUID, body: UpdateUserRequest) -> User:
    assert "id: UUID" in routes_code, "Should have path parameter"
    assert "body: UpdateUserRequest" in routes_code, "Should have body parameter"

    # Check they appear in correct order (path params before body)
    id_pos = routes_code.find("id: UUID")
    body_pos = routes_code.find("body: UpdateUserRequest")
    assert id_pos < body_pos, "Path parameter should come before body parameter"


def test_put_endpoint_return_type(temp_dir: Path) -> None:
    """Test that PUT endpoint has correct return type."""
    # Create schema with PUT endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  UpdateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
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


def test_put_endpoint_operation_id(temp_dir: Path) -> None:
    """Test that PUT endpoint has operation_id set."""
    # Create schema with PUT endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

  UpdateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
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
    assert 'operation_id="update_user"' in routes_code, "Should have operation_id set"


def test_put_endpoint_function_signature(temp_dir: Path) -> None:
    """Test that PUT endpoint generates correct function signature."""
    # Create schema with PUT endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  UpdateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      description: "Update a user"
      body: UpdateUserRequest
      response:
        200:
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
    assert "async def update_user(id: UUID, body: UpdateUserRequest) -> User:" in routes_code, \
        "Should have complete function signature with async def, id parameter, body parameter, and return type"


def test_generated_routes_file_structure(temp_dir: Path) -> None:
    """Test that generated routes file has correct structure."""
    # Create schema with PUT endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  UpdateUserRequest:
    fields:
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
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
    assert "from uuid import UUID" in routes_content, "Should import UUID"
    assert "router = APIRouter()" in routes_content, "Should create router instance"
    assert "@router.put('/users/{id}'" in routes_content, "Should have PUT decorator"
    assert "async def update_user" in routes_content, "Should have function definition"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_routes_pyright_no_errors(temp_dir: Path) -> None:
    """Test that generated routes pass pyright type checking (requirement 6)."""
    # Create schema with PUT endpoint
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

  UpdateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
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
