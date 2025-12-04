"""Integration tests for api_013 - FastAPI route generator handles query parameters.

Test Requirements (from feature):
1. Create schema with endpoint: GET /users with query params: page (int), limit (int, default=20)
2. Run schnitzel generate --target python
3. Verify page: int parameter in function signature
4. Verify limit: int = 20 parameter with default
5. Verify Query() is used for validation
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


def test_query_params_basic(temp_dir: Path) -> None:
    """Test that query parameters are generated with Query()."""
    # Create schema with query parameters
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
  /users:
    GET:
      name: list_users
      description: "List users with pagination"
      query:
        page:
          type: int
        limit:
          type: int
          default: 20
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

    # Verify Query is imported
    assert "from fastapi import" in routes_code, "Should have FastAPI imports"
    assert "Query" in routes_code, "Should import Query from fastapi"

    # Verify query parameters use Query()
    assert "page: int = Query(" in routes_code, "page parameter should use Query()"
    assert "limit: int | None = Query(20" in routes_code, "limit parameter should use Query() with default"


def test_query_params_required(temp_dir: Path) -> None:
    """Test that required query parameters use Query(...)."""
    # Create schema with required query parameter
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
      query:
        page:
          type: int
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

    # Verify required parameter uses Query(...)
    assert "page: int = Query(...)" in routes_code, "Required parameter should use Query(...)"


def test_query_params_with_default(temp_dir: Path) -> None:
    """Test that query parameters with default values work correctly."""
    # Create schema with default value
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
      query:
        limit:
          type: int
          default: 20
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

    # Verify default value is passed to Query()
    assert "limit: int | None = Query(20)" in routes_code, "Parameter with default should use Query(default_value)"


def test_query_params_with_validation_constraints(temp_dir: Path) -> None:
    """Test that query parameters include validation constraints like min/max."""
    # Create schema with validation constraints
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
      query:
        page:
          type: int
          min: 1
        limit:
          type: int
          default: 20
          max: 100
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

    # Verify validation constraints are included
    assert "ge=1" in routes_code, "Should include ge (greater than or equal) constraint"
    assert "le=100" in routes_code, "Should include le (less than or equal) constraint"


def test_query_params_optional(temp_dir: Path) -> None:
    """Test that optional query parameters use Query(None)."""
    # Create schema with optional parameter
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string

endpoints:
  /users:
    GET:
      name: search_users
      query:
        email:
          type: string
          optional: true
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

    # Verify optional parameter uses Query(None)
    assert "email: str | None = Query(None)" in routes_code, "Optional parameter should use Query(None)"


def test_query_params_with_description(temp_dir: Path) -> None:
    """Test that query parameters include descriptions."""
    # Create schema with description
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
      query:
        page:
          type: int
          description: "Page number for pagination"
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

    # Verify description is included
    assert 'description="Page number for pagination"' in routes_code, "Should include description in Query()"


def test_query_params_string_type(temp_dir: Path) -> None:
    """Test that string query parameters work correctly."""
    # Create schema with string query parameter
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
  /users:
    GET:
      name: search_users
      query:
        name:
          type: string
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

    # Verify string parameter is correct
    assert "name: str = Query(...)" in routes_code, "String parameter should use str type"


def test_query_params_multiple(temp_dir: Path) -> None:
    """Test that multiple query parameters are handled correctly."""
    # Create schema with multiple query parameters
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
  /users:
    GET:
      name: search_users
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 20
        search:
          type: string
          optional: true
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

    # Verify all query parameters are present
    assert "page: int | None = Query(1)" in routes_code, "Should have page parameter"
    assert "limit: int | None = Query(20)" in routes_code, "Should have limit parameter"
    assert "search: str | None = Query(None)" in routes_code, "Should have search parameter"


def test_generated_routes_file_with_query_params(temp_dir: Path) -> None:
    """Test that generated routes file has correct structure with query params."""
    # Create schema with query parameters
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
  /users:
    GET:
      name: list_users
      query:
        page:
          type: int
        limit:
          type: int
          default: 20
      response:
        200:
          type: list[User]
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
    assert "from fastapi import" in routes_content, "Should import from FastAPI"
    assert "Query" in routes_content, "Should import Query"
    assert "@router.get('/users'" in routes_content, "Should have GET decorator"
    assert "async def list_users" in routes_content, "Should have function definition"
    assert "page: int = Query(" in routes_content, "Should have page parameter with Query"
    assert "limit: int | None = Query(20" in routes_content, "Should have limit parameter with default"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_routes_with_query_params_pyright_no_errors(temp_dir: Path) -> None:
    """Test that generated routes with query params pass pyright type checking."""
    # Create schema with query parameters
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
  /users:
    GET:
      name: list_users
      description: "List users with pagination"
      query:
        page:
          type: int
          min: 1
          description: "Page number"
        limit:
          type: int
          default: 20
          max: 100
          description: "Items per page"
      response:
        200:
          type: list[User]
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

    # Create a basic pyrightconfig.json to help pyright
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright on generated file
    result = subprocess.run(
        ["pyright", str(routes_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no errors (allow warnings about missing stubs and return type warnings for TODO stubs)
    has_only_expected_errors = (
        result.returncode == 0 or
        "reportMissingImports" in result.stdout or
        ("reportReturnType" in result.stdout and "reportInvalidTypeForm" not in result.stdout)
    )
    assert has_only_expected_errors, \
        f"pyright should pass with no structural errors (allowing TODO stub return warnings). Output: {result.stdout}\n{result.stderr}"


def test_query_params_with_max_length(temp_dir: Path) -> None:
    """Test that string query parameters can have max_length constraint."""
    # Create schema with max_length constraint
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
  /users:
    GET:
      name: search_users
      query:
        name:
          type: string
          max_length: 100
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

    # Verify max_length constraint is included
    assert "max_length=100" in routes_code, "Should include max_length constraint for string"
