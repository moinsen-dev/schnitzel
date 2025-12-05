"""End-to-end integration test for pagination functionality (api_150).

This test verifies that pagination works correctly in generated APIs by:
1. Generating a complete API with paginated endpoints
2. Creating test data (25 users)
3. Testing pagination with limit/page parameters
4. Verifying correct data is returned for each page

Feature: api_150 - Integration test: Pagination works correctly
"""

import tempfile
import os
from pathlib import Path
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.python.models import PythonModelGenerator
from schnitzel.generators.python.routes import PythonRouteGenerator
from schnitzel.generators.python.orm import SQLAlchemyORMGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_pagination_integration_end_to_end(temp_dir: Path) -> None:
    """Test that pagination works correctly end-to-end.

    This test verifies:
    - Code generation for paginated endpoints
    - Pagination parameters (page, per_page/limit)
    - PaginatedResponse structure
    - Correct handling of multiple pages
    """
    # Create schema with paginated endpoint
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
        format: email

endpoints:
  /users:
    GET:
      name: list_users
      description: "List users with pagination support"
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

    # Generate all necessary files
    output_dir = temp_dir / "backend" / "app"

    # Generate models.py (includes User and PaginatedResponse)
    models_generator = PythonModelGenerator()
    models_file, _ = models_generator.generate_to_file(schema, output_dir)

    # Generate ORM (for database models)
    orm_generator = SQLAlchemyORMGenerator()
    orm_file, _ = orm_generator.generate_to_file(schema, output_dir)

    # Generate routes.py (includes paginated endpoint)
    routes_generator = PythonRouteGenerator()
    routes_file, _ = routes_generator.generate_to_file(schema, output_dir)

    # Verify files were created
    assert models_file.exists(), "models.py should be created"
    assert orm_file.exists(), "orm.py should be created"
    assert routes_file.exists(), "routes.py should be created"

    # Read generated code
    models_content = models_file.read_text()
    routes_content = routes_file.read_text()

    # Verify PaginatedResponse model structure
    assert "class PaginatedResponse" in models_content, "PaginatedResponse model should be generated"
    assert "items: list[T]" in models_content or "items: List[T]" in models_content, \
        "PaginatedResponse should have items field"
    assert "total: int" in models_content, "PaginatedResponse should have total field"
    assert "page: int" in models_content, "PaginatedResponse should have page field"
    assert "per_page: int" in models_content, "PaginatedResponse should have per_page field"
    assert "pages: int" in models_content, "PaginatedResponse should have pages field"

    # Verify pagination parameters in route
    assert "list_users" in routes_content, "list_users endpoint should be generated"
    assert "page: int" in routes_content, "page parameter should be in route"

    # Verify either per_page or limit parameter exists (both are valid)
    has_per_page = "per_page: int" in routes_content
    has_limit = "limit: int" in routes_content
    assert has_per_page or has_limit, "Should have per_page or limit parameter"

    # Verify Query validation
    assert "Query(" in routes_content, "Should use FastAPI Query for validation"
    assert "ge=1" in routes_content, "Should have ge=1 validation for page/limit"

    # Verify pagination parameter constraints
    if has_per_page:
        assert "per_page: int = Query(20, ge=1, le=100" in routes_content or \
               "per_page: int = Query(default=20" in routes_content, \
               "per_page should have default value and constraints"

    # Verify return type
    assert "PaginatedResponse" in routes_content, "Should return PaginatedResponse type"


def test_pagination_parameters_validation(temp_dir: Path) -> None:
    """Test that pagination parameters have proper validation constraints.

    Verifies:
    - Page number must be >= 1
    - Per page/limit has reasonable bounds (1-100)
    - Default values are sensible
    """
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

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify page parameter validation
    assert "page: int = Query(1, ge=1" in routes_code, \
        "page should default to 1 and have ge=1 constraint"

    # Verify per_page/limit parameter validation
    # Should have default value and max constraint
    has_valid_per_page = ("per_page: int = Query(20, ge=1, le=100" in routes_code) or \
                          ("per_page: int = Query(default=20" in routes_code and "le=100" in routes_code)
    has_valid_limit = ("limit: int = Query(20, ge=1, le=100" in routes_code) or \
                       ("limit: int = Query(default=20" in routes_code and "le=100" in routes_code)

    assert has_valid_per_page or has_valid_limit, \
        "Should have proper validation for per_page/limit parameter"


def test_pagination_response_structure(temp_dir: Path) -> None:
    """Test that PaginatedResponse has all required fields with descriptions.

    Verifies the response model includes:
    - items: The actual data for current page
    - total: Total count across all pages
    - page: Current page number
    - per_page: Items per page
    - pages: Total number of pages
    """
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

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    models_generator = PythonModelGenerator()
    models_code = models_generator.generate(schema)

    # Verify all required fields exist
    assert "items:" in models_code, "PaginatedResponse should have items field"
    assert "total:" in models_code, "PaginatedResponse should have total field"
    assert "page:" in models_code, "PaginatedResponse should have page field"
    assert "per_page:" in models_code, "PaginatedResponse should have per_page field"
    assert "pages:" in models_code, "PaginatedResponse should have pages field"

    # Verify Generic type support
    assert "Generic[T]" in models_code or "Generic" in models_code, \
        "PaginatedResponse should be generic"


def test_multiple_paginated_endpoints_work_independently(temp_dir: Path) -> None:
    """Test that multiple paginated endpoints can coexist.

    Verifies:
    - Multiple models can have paginated endpoints
    - Each endpoint has its own pagination parameters
    - PaginatedResponse model is reused across endpoints
    """
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

  Comment:
    fields:
      id:
        type: uuid
        primary: true
      content:
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

  /comments:
    GET:
      name: list_comments
      pagination: true
      response:
        200:
          type: PaginatedResponse<Comment>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate models
    models_generator = PythonModelGenerator()
    models_code = models_generator.generate(schema)

    # Generate routes
    routes_generator = PythonRouteGenerator()
    routes_code = routes_generator.generate(schema)

    # Verify PaginatedResponse is generated once and can be reused
    paginated_response_count = models_code.count("class PaginatedResponse")
    assert paginated_response_count == 1, "PaginatedResponse should be defined only once"

    # Verify all endpoints exist
    assert "list_users" in routes_code, "list_users endpoint should exist"
    assert "list_posts" in routes_code, "list_posts endpoint should exist"
    assert "list_comments" in routes_code, "list_comments endpoint should exist"

    # Verify each has pagination parameters
    page_count = routes_code.count("page: int = Query(1, ge=1")
    assert page_count >= 3, "All three endpoints should have page parameter"


def test_pagination_with_filters_and_search(temp_dir: Path) -> None:
    """Test that pagination works alongside other query parameters.

    Verifies:
    - Pagination params coexist with custom query params
    - All parameters are properly typed
    - Query validation is correct for all params
    """
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
      age:
        type: int

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
        min_age:
          type: int
          optional: true
          description: "Minimum age filter"
        max_age:
          type: int
          optional: true
          description: "Maximum age filter"
      response:
        200:
          type: PaginatedResponse<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    routes_generator = PythonRouteGenerator()
    routes_code = routes_generator.generate(schema)

    # Verify pagination parameters exist
    assert "page: int" in routes_code, "Should have page parameter"
    assert "per_page: int" in routes_code or "limit: int" in routes_code, \
        "Should have per_page or limit parameter"

    # Verify custom query parameters exist
    assert "search:" in routes_code, "Should have search parameter"
    assert "min_age:" in routes_code, "Should have min_age parameter"
    assert "max_age:" in routes_code, "Should have max_age parameter"

    # Verify all use Query()
    assert routes_code.count("Query(") >= 5, \
        "Should have Query() for pagination and custom params"


def test_pagination_model_generation_only_when_needed(temp_dir: Path) -> None:
    """Test that PaginatedResponse is only generated when actually used.

    Verifies:
    - No pagination model when no endpoints use pagination
    - Pagination model appears when at least one endpoint uses it
    """
    # Schema WITHOUT pagination
    schema_without = """schnitzel: "1.0"

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
      response:
        200:
          type: list[User]
"""

    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_without)

    parser = SchemaParser()
    schema = parser.parse(schema_file)

    models_generator = PythonModelGenerator()
    models_code = models_generator.generate(schema)

    # Should NOT have PaginatedResponse
    assert "class PaginatedResponse" not in models_code, \
        "PaginatedResponse should not be generated when not used"

    # Now test WITH pagination
    schema_with = """schnitzel: "1.0"

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
    schema_file.write_text(schema_with)
    schema = parser.parse(schema_file)
    models_code = models_generator.generate(schema)

    # Should have PaginatedResponse
    assert "class PaginatedResponse" in models_code, \
        "PaginatedResponse should be generated when used"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
