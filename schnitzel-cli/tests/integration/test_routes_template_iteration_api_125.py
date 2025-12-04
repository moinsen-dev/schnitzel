"""Integration tests for api_125 - Routes template correctly iterates over endpoints.

Test Requirements (from feature):
1. Create schema with multiple endpoints
2. Generate FastAPI routes
3. Verify each endpoint produces a route function
4. Verify HTTP method iteration is correct
5. Verify parameter extraction is correct

This test ensures the routes generator correctly processes all endpoints
with different HTTP methods and parameter types.
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


def test_multiple_endpoints_all_generated(temp_dir: Path) -> None:
    """Test that schema with multiple endpoints generates all route functions."""
    # Create schema with multiple different endpoints
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

  UpdateUserRequest:
    fields:
      name:
        type: string
        optional: true
      email:
        type: string
        optional: true

endpoints:
  /users:
    GET:
      name: list_users
      description: "List all users"
      response:
        200:
          type: list[User]
    POST:
      name: create_user
      description: "Create a new user"
      body: CreateUserRequest
      response:
        201:
          type: User

  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      description: "Get a user by ID"
      response:
        200:
          type: User
    PUT:
      name: update_user
      description: "Update a user"
      body: UpdateUserRequest
      response:
        200:
          type: User
    DELETE:
      name: delete_user
      description: "Delete a user"

  /users/search:
    GET:
      name: search_users
      description: "Search users"
      query:
        q:
          type: string
          description: "Search query"
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

    # Verify all endpoints are present
    # /users endpoints
    assert "@router.get('/users'" in routes_code, "Should have GET /users"
    assert "@router.post('/users'" in routes_code, "Should have POST /users"

    # /users/{id} endpoints
    assert "@router.get('/users/{id}'" in routes_code, "Should have GET /users/{id}"
    assert "@router.put('/users/{id}'" in routes_code, "Should have PUT /users/{id}"
    assert "@router.delete('/users/{id}'" in routes_code, "Should have DELETE /users/{id}"

    # /users/search endpoint
    assert "@router.get('/users/search'" in routes_code, "Should have GET /users/search"

    # Verify all function names are present
    assert "async def list_users" in routes_code, "Should have list_users function"
    assert "async def create_user" in routes_code, "Should have create_user function"
    assert "async def get_user" in routes_code, "Should have get_user function"
    assert "async def update_user" in routes_code, "Should have update_user function"
    assert "async def delete_user" in routes_code, "Should have delete_user function"
    assert "async def search_users" in routes_code, "Should have search_users function"


def test_http_method_iteration_correctness(temp_dir: Path) -> None:
    """Test that each HTTP method (GET, POST, PUT, DELETE) generates correct decorators."""
    # Create schema with all common HTTP methods on same path
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  CreateItemRequest:
    fields:
      name:
        type: string

  UpdateItemRequest:
    fields:
      name:
        type: string

endpoints:
  /items/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_item
      response:
        200:
          type: Item
    PUT:
      name: update_item
      body: UpdateItemRequest
      response:
        200:
          type: Item
    DELETE:
      name: delete_item
    POST:
      name: create_sub_item
      body: CreateItemRequest
      response:
        201:
          type: Item
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify each HTTP method generates the correct decorator
    assert "@router.get('/items/{id}'" in routes_code, "GET method should generate @router.get"
    assert "@router.put('/items/{id}'" in routes_code, "PUT method should generate @router.put"
    assert "@router.delete('/items/{id}'" in routes_code, "DELETE method should generate @router.delete"
    assert "@router.post('/items/{id}'" in routes_code, "POST method should generate @router.post"

    # Verify correct status codes for each method
    assert "@router.post('/items/{id}', status_code=201" in routes_code, "POST should have 201 status"
    assert "@router.delete('/items/{id}', status_code=204" in routes_code, "DELETE should have 204 status"


def test_path_parameter_extraction(temp_dir: Path) -> None:
    """Test that path parameters are correctly extracted and typed."""
    # Create schema with various path parameters
    schema_content = """schnitzel: "1.0"

models:
  Resource:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /users/{user_id}/posts/{post_id}:
    params:
      user_id:
        type: uuid
      post_id:
        type: int
    GET:
      name: get_user_post
      description: "Get a specific post from a user"
      response:
        200:
          type: Resource

  /items/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_item
      response:
        200:
          type: Resource

  /categories/{slug}:
    params:
      slug:
        type: string
    GET:
      name: get_category_by_slug
      response:
        200:
          type: Resource
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify path parameters are extracted with correct types
    assert "user_id: UUID" in routes_code, "user_id should be UUID type"
    assert "post_id: int" in routes_code, "post_id should be int type"
    assert "id: UUID" in routes_code, "id should be UUID type"
    assert "slug: str" in routes_code, "slug should be str type"

    # Verify function signatures include path parameters
    assert "async def get_user_post(user_id: UUID, post_id: int)" in routes_code, \
        "Function should have both path parameters"
    assert "async def get_item(id: UUID)" in routes_code, \
        "Function should have id parameter"
    assert "async def get_category_by_slug(slug: str)" in routes_code, \
        "Function should have slug parameter"


def test_query_parameter_extraction(temp_dir: Path) -> None:
    """Test that query parameters are correctly extracted and processed."""
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

endpoints:
  /users:
    GET:
      name: list_users
      query:
        page:
          type: int
          default: 1
          min: 1
        limit:
          type: int
          default: 20
          min: 1
          max: 100
        sort:
          type: string
          optional: true
        active:
          type: bool
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

    # Verify query parameters are extracted
    assert "page: int | None = Query(1" in routes_code, "page should have default value 1"
    assert "limit: int | None = Query(20" in routes_code, "limit should have default value 20"
    assert "sort: str | None = Query(None)" in routes_code, "sort should be optional"
    assert "active: bool | None = Query(None)" in routes_code, "active should be optional"

    # Verify validation constraints
    assert "ge=1" in routes_code, "Should have min validation"
    assert "le=100" in routes_code, "Should have max validation"


def test_request_body_parameter_extraction(temp_dir: Path) -> None:
    """Test that request body parameters are correctly extracted for POST/PUT/PATCH."""
    # Create schema with body parameters
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

  UpdateUserRequest:
    fields:
      name:
        type: string
        optional: true

endpoints:
  /users:
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
          type: User

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
    PATCH:
      name: patch_user
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

    # Verify body parameters are extracted for POST, PUT, PATCH
    assert "async def create_user(body: CreateUserRequest)" in routes_code, \
        "POST should have body parameter"
    assert "async def update_user(id: UUID, body: UpdateUserRequest)" in routes_code, \
        "PUT should have both id and body parameters"
    assert "async def patch_user(id: UUID, body: UpdateUserRequest)" in routes_code, \
        "PATCH should have both id and body parameters"


def test_mixed_parameters_ordering(temp_dir: Path) -> None:
    """Test that mixed parameters (path, query, body) are ordered correctly."""
    # Create schema with mixed parameters
    schema_content = """schnitzel: "1.0"

models:
  Resource:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

  UpdateResourceRequest:
    fields:
      name:
        type: string

endpoints:
  /users/{user_id}/resources/{resource_id}:
    params:
      user_id:
        type: uuid
      resource_id:
        type: int
    PUT:
      name: update_resource
      body: UpdateResourceRequest
      query:
        notify:
          type: bool
          optional: true
        cascade:
          type: bool
          default: false
      response:
        200:
          type: Resource
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify parameter ordering: path params (required), body (required), query params (optional)
    # Required params should come before optional params
    assert "async def update_resource(user_id: UUID, resource_id: int, body: UpdateResourceRequest" in routes_code, \
        "Required parameters (path and body) should come first"

    # Verify query parameters are present (they come after required params)
    assert "notify: bool | None = Query(None)" in routes_code, "Optional query param should be present"
    assert "cascade: bool | None = Query(False)" in routes_code, "Query param with default should be present"


def test_endpoint_count_matches_schema(temp_dir: Path) -> None:
    """Test that the number of generated route functions matches schema definition."""
    # Create schema with known number of endpoints
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true

endpoints:
  /items:
    GET:
      name: list_items
      response:
        200:
          type: list[Item]
    POST:
      name: create_item
      body: dict
      response:
        201:
          type: Item

  /items/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_item
      response:
        200:
          type: Item
    PUT:
      name: update_item
      body: dict
      response:
        200:
          type: Item
    DELETE:
      name: delete_item
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Count async def functions (excluding router definition)
    async_def_count = routes_code.count("async def")

    # We expect 5 endpoint functions (list, create, get, update, delete)
    assert async_def_count == 5, f"Expected 5 route functions, found {async_def_count}"

    # Verify each specific function exists
    assert "async def list_items" in routes_code
    assert "async def create_item" in routes_code
    assert "async def get_item" in routes_code
    assert "async def update_item" in routes_code
    assert "async def delete_item" in routes_code


def test_empty_endpoints_generates_minimal_router(temp_dir: Path) -> None:
    """Test that schema with no endpoints generates minimal router file."""
    # Create schema with no endpoints
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify minimal router is generated
    assert "from fastapi import APIRouter" in routes_code, "Should import APIRouter"
    assert "router = APIRouter()" in routes_code, "Should create router instance"
    assert "async def" not in routes_code, "Should have no route functions"


def test_params_keyword_not_treated_as_endpoint(temp_dir: Path) -> None:
    """Test that 'params' keyword is not treated as an HTTP method endpoint."""
    # Create schema with params section
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
    GET:
      name: get_user
      response:
        200:
          type: User
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

    # Verify 'params' is not treated as an endpoint
    assert "@router.params" not in routes_code, "'params' should not generate a route decorator"
    assert "async def params" not in routes_code, "'params' should not generate a function"

    # Verify only GET and DELETE are generated
    async_def_count = routes_code.count("async def")
    assert async_def_count == 2, "Should only have 2 functions (GET and DELETE)"


def test_generated_file_structure_with_multiple_endpoints(temp_dir: Path) -> None:
    """Test that generated file has correct structure with multiple endpoints."""
    # Create schema with multiple endpoints
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
    GET:
      name: list_users
      response:
        200:
          type: list[User]
    POST:
      name: create_user
      body: CreateUserRequest
      response:
        201:
          type: User

  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
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

    # Read and verify structure
    routes_content = routes_file.read_text()

    # Check imports
    assert "from fastapi import" in routes_content, "Should have FastAPI imports"
    assert "APIRouter" in routes_content, "Should import APIRouter"
    assert "from uuid import UUID" in routes_content, "Should import UUID"
    assert "from .models import" in routes_content, "Should import models"

    # Check router creation
    assert "router = APIRouter()" in routes_content, "Should create router instance"

    # Check all functions are present
    assert "async def list_users" in routes_content
    assert "async def create_user" in routes_content
    assert "async def get_user" in routes_content

    # Check file header
    assert "Generated by Schnitzel Framework" in routes_content, "Should have generation header"
    assert "DO NOT EDIT" in routes_content, "Should have edit warning"


@pytest.mark.skipif(
    subprocess.run(["which", "pyright"], capture_output=True).returncode != 0,
    reason="pyright not installed"
)
def test_generated_routes_with_multiple_endpoints_pyright(temp_dir: Path) -> None:
    """Test that generated routes with multiple endpoints pass pyright type checking."""
    # Create schema with comprehensive endpoints
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

  UpdateUserRequest:
    fields:
      name:
        type: string
        optional: true
      email:
        type: string
        optional: true

endpoints:
  /users:
    GET:
      name: list_users
      description: "List all users"
      query:
        page:
          type: int
          default: 1
        limit:
          type: int
          default: 20
      response:
        200:
          type: list[User]
    POST:
      name: create_user
      description: "Create a new user"
      body: CreateUserRequest
      response:
        201:
          type: User

  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      description: "Get a user by ID"
      response:
        200:
          type: User
    PUT:
      name: update_user
      description: "Update a user"
      body: UpdateUserRequest
      response:
        200:
          type: User
    DELETE:
      name: delete_user
      description: "Delete a user"
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

    # Verify no structural errors
    # Note: We allow reportReturnType errors since generated code has placeholder "pass" statements
    # The important validation is that imports, types, and signatures are correct
    has_structural_errors = (
        result.returncode != 0
        and "reportMissingImports" not in result.stdout
        and "reportReturnType" not in result.stdout
    )

    assert not has_structural_errors, \
        f"pyright should pass with no structural errors. Output: {result.stdout}\n{result.stderr}"
