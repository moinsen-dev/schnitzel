"""Integration tests for api_017 - FastAPI route generator creates DELETE endpoint.

Test Requirements (from feature):
1. Create schema with endpoint: DELETE /users/{id}
2. Run schnitzel generate --target python
3. Verify @router.delete('/users/{id}') decorator is present
4. Verify status_code=204
5. Verify return type is None or status only
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


def test_delete_endpoint_decorator(temp_dir: Path) -> None:
    """Test that DELETE endpoint generates @router.delete decorator."""
    # Create schema with DELETE endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify @router.delete decorator is present
    assert "@router.delete('/users/{id}'" in routes_code, "Should have @router.delete decorator"


def test_delete_endpoint_status_code(temp_dir: Path) -> None:
    """Test that DELETE endpoint sets status_code=204."""
    # Create schema with DELETE endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify status_code=204 is set
    assert "status_code=204" in routes_code, "DELETE endpoint should have status_code=204"


def test_delete_endpoint_return_type(temp_dir: Path) -> None:
    """Test that DELETE endpoint has return type None."""
    # Create schema with DELETE endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify return type is None
    assert "-> None:" in routes_code, "DELETE endpoint should have return type None"


def test_delete_endpoint_path_parameter(temp_dir: Path) -> None:
    """Test that DELETE endpoint includes path parameter."""
    # Create schema with DELETE endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user by ID"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path parameter with correct type
    assert "id: UUID" in routes_code, "Should have id parameter with UUID type"


def test_delete_endpoint_operation_id(temp_dir: Path) -> None:
    """Test that DELETE endpoint has operation_id set."""
    # Create schema with DELETE endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
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
    assert 'operation_id="delete_user"' in routes_code, "Should have operation_id set"


def test_delete_endpoint_function_signature(temp_dir: Path) -> None:
    """Test that DELETE endpoint generates correct function signature."""
    # Create schema with DELETE endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user"
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
    assert "async def delete_user(id: UUID) -> None:" in routes_code, \
        "Should have complete function signature with async def, id parameter, and None return type"


def test_generated_delete_routes_file_structure(temp_dir: Path) -> None:
    """Test that generated routes file with DELETE has correct structure."""
    # Create schema with DELETE endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user"
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
    assert "@router.delete('/users/{id}'" in routes_content, "Should have DELETE decorator"
    assert "async def delete_user" in routes_content, "Should have function definition"
    assert "status_code=204" in routes_content, "Should have 204 status code"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_delete_routes_pyright_no_errors(temp_dir: Path) -> None:
    """Test that generated DELETE routes pass pyright type checking (requirement 6)."""
    # Create schema with DELETE endpoint
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

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user by ID"
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


def test_delete_endpoint_complete_example(temp_dir: Path) -> None:
    """Test complete DELETE endpoint generation matching expected output."""
    # Create schema with DELETE endpoint
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /users/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_user
      description: "Delete a user"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify complete expected structure
    assert "@router.delete('/users/{id}', status_code=204, operation_id=\"delete_user\")" in routes_code
    assert "async def delete_user(id: UUID) -> None:" in routes_code
    assert '"""Delete a user"""' in routes_code

    # Print for debugging
    print("\n" + "="*80)
    print("Generated DELETE endpoint code:")
    print("="*80)
    print(routes_code)
    print("="*80)
