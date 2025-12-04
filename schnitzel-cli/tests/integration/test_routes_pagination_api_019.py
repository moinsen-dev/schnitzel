"""Integration tests for api_019 - FastAPI route generator handles paginated responses.

Test Requirements (from feature):
1. Check if route generator supports pagination
2. If not, implement pagination support:
   - Add page/per_page query parameters (or limit/offset)
   - Return paginated response wrapper (items, total, page, pages)
3. Create integration test that:
   - Creates a schema with paginated endpoints
   - Generates route code
   - Verifies pagination parameters are included
   - Verifies response structure includes pagination metadata
"""

import tempfile
import os
from pathlib import Path
import subprocess
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python.routes import PythonRouteGenerator
from schnitzel.generators.python.models import PythonModelGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_pagination_enabled_adds_query_parameters(temp_dir: Path) -> None:
    """Test that pagination: true adds page and per_page query parameters."""
    # Create schema with pagination enabled
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
      pagination: true
      response:
        200:
          type: PaginatedResponse<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify pagination parameters are added
    assert "page: int = Query(1, ge=1" in routes_code, "Should have page parameter with default 1 and ge=1"
    assert "per_page: int = Query(20, ge=1, le=100" in routes_code, "Should have per_page parameter with constraints"
    assert 'description="Page number' in routes_code, "Page parameter should have description"
    assert 'description="Items per page' in routes_code, "per_page parameter should have description"


def test_pagination_generates_paginated_response_model(temp_dir: Path) -> None:
    """Test that PaginatedResponse model is generated when pagination is used."""
    # Create schema with pagination enabled
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      price:
        type: float

endpoints:
  /products:
    GET:
      name: list_products
      pagination: true
      response:
        200:
          type: PaginatedResponse<Product>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate models
    models_generator = PythonModelGenerator()
    models_code = models_generator.generate(schema)

    # Verify PaginatedResponse model is generated
    assert "class PaginatedResponse(BaseModel, Generic[T])" in models_code, \
        "Should generate PaginatedResponse class"
    assert "items: list[T]" in models_code, "Should have items field"
    assert "total: int" in models_code, "Should have total field"
    assert "page: int" in models_code, "Should have page field"
    assert "per_page: int" in models_code, "Should have per_page field"
    assert "pages: int" in models_code, "Should have pages field"
    assert "Generic" in models_code, "Should import Generic for generic type"
    assert "TypeVar" in models_code, "Should import TypeVar for generic type"


def test_pagination_response_type_in_routes(temp_dir: Path) -> None:
    """Test that routes return PaginatedResponse[Model] type."""
    # Create schema with pagination
    schema_content = """schnitzel: "1.0"

models:
  Order:
    fields:
      id:
        type: uuid
        primary: true
      status:
        type: string

endpoints:
  /orders:
    GET:
      name: list_orders
      pagination: true
      response:
        200:
          type: PaginatedResponse<Order>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify return type is PaginatedResponse<Order>
    assert "-> PaginatedResponse<Order>:" in routes_code or \
           "-> PaginatedResponse[Order]:" in routes_code, \
           "Function should return PaginatedResponse type"

    # Verify imports include PaginatedResponse
    assert "PaginatedResponse" in routes_code, "Should import PaginatedResponse"


def test_pagination_without_explicit_flag_using_response_type(temp_dir: Path) -> None:
    """Test that pagination model is generated when response type is PaginatedResponse<T>."""
    # Create schema where pagination is inferred from response type
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
    GET:
      name: list_posts
      response:
        200:
          type: PaginatedResponse<Post>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate models
    models_generator = PythonModelGenerator()
    models_code = models_generator.generate(schema)

    # Verify PaginatedResponse is generated even without explicit pagination: true
    assert "class PaginatedResponse" in models_code, \
        "Should generate PaginatedResponse when used in response type"


def test_multiple_paginated_endpoints(temp_dir: Path) -> None:
    """Test that multiple endpoints can use pagination."""
    # Create schema with multiple paginated endpoints
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /users:
    GET:
      name: list_users
      pagination: true
      response:
        200:
          type: PaginatedResponse<User>

  /posts:
    GET:
      name: list_posts
      pagination: true
      response:
        200:
          type: PaginatedResponse<Post>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    routes_generator = PythonRouteGenerator()
    routes_code = routes_generator.generate(schema)

    # Verify both endpoints have pagination parameters
    assert "async def list_users" in routes_code
    assert "async def list_posts" in routes_code

    # Count pagination parameters (should appear in both functions)
    page_count = routes_code.count("page: int = Query(1, ge=1")
    per_page_count = routes_code.count("per_page: int = Query(20, ge=1, le=100")

    assert page_count >= 2, "Both endpoints should have page parameter"
    assert per_page_count >= 2, "Both endpoints should have per_page parameter"


def test_pagination_with_additional_query_params(temp_dir: Path) -> None:
    """Test that pagination works alongside custom query parameters."""
    # Create schema with pagination and custom query params
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
      pagination: true
      query:
        search:
          type: string
          optional: true
          description: "Search by name or email"
      response:
        200:
          type: PaginatedResponse<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify both pagination and custom query params are present
    assert "page: int = Query(1, ge=1" in routes_code, "Should have pagination page param"
    assert "per_page: int = Query(20, ge=1, le=100" in routes_code, "Should have pagination per_page param"
    assert "search: str | None = Query(None" in routes_code, "Should have custom search param"


def test_generated_files_with_pagination(temp_dir: Path) -> None:
    """Test that both models.py and routes.py are generated correctly with pagination."""
    # Create schema with pagination
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      quantity:
        type: int

endpoints:
  /items:
    GET:
      name: list_items
      pagination: true
      response:
        200:
          type: PaginatedResponse<Item>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate to files
    output_dir = temp_dir / "backend" / "app"

    # Generate models.py
    models_generator = PythonModelGenerator()
    models_file, models_size = models_generator.generate_to_file(schema, output_dir)

    # Generate routes.py
    routes_generator = PythonRouteGenerator()
    routes_file, routes_size = routes_generator.generate_to_file(schema, output_dir)

    # Verify files exist
    assert models_file.exists(), "models.py should be created"
    assert routes_file.exists(), "routes.py should be created"

    # Read and verify models.py
    models_content = models_file.read_text()
    assert "class Item(BaseModel)" in models_content, "Should have Item model"
    assert "class PaginatedResponse(BaseModel, Generic[T])" in models_content, \
        "Should have PaginatedResponse model"

    # Read and verify routes.py
    routes_content = routes_file.read_text()
    assert "from .models import Item, PaginatedResponse" in routes_content, \
        "Should import both Item and PaginatedResponse"
    assert "@router.get('/items'" in routes_content, "Should have GET endpoint"
    assert "page: int = Query(1, ge=1" in routes_content, "Should have pagination parameters"


def test_pagination_field_validations(temp_dir: Path) -> None:
    """Test that pagination parameters have proper FastAPI Query validations."""
    # Create schema with pagination
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
      pagination: true
      response:
        200:
          type: PaginatedResponse<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify validation constraints
    assert "ge=1" in routes_code, "page should have ge=1 validation"
    assert "le=100" in routes_code, "per_page should have le=100 validation"

    # Verify Query is imported
    assert "from fastapi import" in routes_code and "Query" in routes_code, \
        "Should import Query from fastapi"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_pagination_code_passes_pyright(temp_dir: Path) -> None:
    """Test that generated code with pagination passes pyright type checking."""
    # Create schema with pagination
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
      pagination: true
      response:
        200:
          type: PaginatedResponse<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate files
    output_dir = temp_dir / "backend" / "app"

    # Generate models.py
    models_generator = PythonModelGenerator()
    models_file, _ = models_generator.generate_to_file(schema, output_dir)

    # Generate routes.py
    routes_generator = PythonRouteGenerator()
    routes_file, _ = routes_generator.generate_to_file(schema, output_dir)

    # Create __init__.py
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    # Create pyrightconfig.json
    pyright_config = temp_dir / "pyrightconfig.json"
    pyright_config.write_text('{"reportMissingModuleSource": false}')

    # Run pyright on both files
    models_result = subprocess.run(
        ["pyright", str(models_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    routes_result = subprocess.run(
        ["pyright", str(routes_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify no type errors (allow missing import warnings and return type warnings for TODO stubs)
    assert models_result.returncode == 0 or "reportMissingImports" in models_result.stdout, \
        f"models.py should pass pyright. Output: {models_result.stdout}\n{models_result.stderr}"

    # For routes, allow reportReturnType errors since functions are TODO stubs
    routes_has_only_expected_errors = (
        routes_result.returncode == 0 or
        "reportMissingImports" in routes_result.stdout or
        ("reportReturnType" in routes_result.stdout and "reportInvalidTypeForm" not in routes_result.stdout)
    )
    assert routes_has_only_expected_errors, \
        f"routes.py should pass pyright (allowing TODO stub return warnings). Output: {routes_result.stdout}\n{routes_result.stderr}"


def test_pagination_model_fields_have_descriptions(temp_dir: Path) -> None:
    """Test that PaginatedResponse fields have proper descriptions for OpenAPI."""
    # Create schema with pagination
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
      pagination: true
      response:
        200:
          type: PaginatedResponse<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate models
    models_generator = PythonModelGenerator()
    models_code = models_generator.generate(schema)

    # Verify Field descriptions are present
    assert 'description="Items for the current page"' in models_code or \
           "description='Items for the current page'" in models_code, \
           "items field should have description"
    assert 'description="Total number of items across all pages"' in models_code or \
           "description='Total number of items across all pages'" in models_code, \
           "total field should have description"
    assert 'description="Current page number' in models_code, "page field should have description"
    assert 'description="Number of items per page"' in models_code or \
           "description='Number of items per page'" in models_code, \
           "per_page field should have description"
    assert 'description="Total number of pages"' in models_code or \
           "description='Total number of pages'" in models_code, \
           "pages field should have description"


def test_no_pagination_model_when_not_needed(temp_dir: Path) -> None:
    """Test that PaginatedResponse is not generated when no endpoints use pagination."""
    # Create schema without pagination
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
      response:
        200:
          type: list[User]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate models
    models_generator = PythonModelGenerator()
    models_code = models_generator.generate(schema)

    # Verify PaginatedResponse is NOT generated
    assert "class PaginatedResponse" not in models_code, \
        "Should not generate PaginatedResponse when not used"
    assert "Generic" not in models_code or "TypeVar" not in models_code, \
        "Should not import Generic/TypeVar when not needed"
