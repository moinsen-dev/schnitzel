"""Integration tests for api_021 - FastAPI route generator includes OpenAPI metadata.

Test Requirements (from feature):
1. Verify route generator includes OpenAPI metadata in decorators:
   - operation_id from endpoint name
   - summary/description from schema
   - tags for grouping endpoints
2. Create integration test that:
   - Creates schema with endpoints
   - Generates routes
   - Verifies operation_id is set
   - Verifies tags are included if specified in schema

This feature ensures generated FastAPI routes include proper OpenAPI metadata
for documentation and API client generation.
Following Schnitzel zero-tolerance policy: no errors, no warnings, no TODOs.
"""

import tempfile
import os
from pathlib import Path
import subprocess
import sys
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


def test_generated_routes_include_operation_id(temp_dir: Path) -> None:
    """Test that generated routes include operation_id in decorator."""
    # Create schema with endpoints
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
      description: "List all users"
      response:
        200:
          type: list[User]
    POST:
      name: create_user
      description: "Create a new user"
      body:
        name:
          type: string
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

    # Verify operation_id is included for GET endpoint
    assert 'operation_id="list_users"' in routes_code, \
        "GET endpoint should include operation_id='list_users'"

    # Verify operation_id is included for POST endpoint
    assert 'operation_id="create_user"' in routes_code, \
        "POST endpoint should include operation_id='create_user'"


def test_operation_id_matches_endpoint_name(temp_dir: Path) -> None:
    """Test that operation_id matches the endpoint name from schema."""
    # Create schema with custom endpoint names
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
      name: get_all_products
      description: "Retrieve all products"
      response:
        200:
          type: list[Product]

  /products/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_product_by_id
      description: "Retrieve a single product"
      response:
        200:
          type: Product
    PUT:
      name: update_product_details
      description: "Update product information"
      body: Product
      response:
        200:
          type: Product
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify operation_ids match endpoint names
    assert 'operation_id="get_all_products"' in routes_code, \
        "Should have operation_id matching endpoint name 'get_all_products'"
    assert 'operation_id="get_product_by_id"' in routes_code, \
        "Should have operation_id matching endpoint name 'get_product_by_id'"
    assert 'operation_id="update_product_details"' in routes_code, \
        "Should have operation_id matching endpoint name 'update_product_details'"


def test_generated_routes_include_summary_metadata(temp_dir: Path) -> None:
    """Test that generated routes include summary in decorator when provided."""
    # Create schema with summary field
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
      summary: "Get all users"
      description: "Retrieve a list of all registered users in the system"
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

    # Verify summary is included in decorator
    assert 'summary="Get all users"' in routes_code, \
        "Should include summary in route decorator"


def test_generated_routes_include_description_in_docstring(temp_dir: Path) -> None:
    """Test that generated routes include description as docstring."""
    # Create schema with description
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
      description: "List all orders with pagination support"
      response:
        200:
          type: list[Order]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify description is included as docstring
    assert '"""List all orders with pagination support"""' in routes_code, \
        "Should include description as function docstring"


def test_generated_routes_include_tags_metadata(temp_dir: Path) -> None:
    """Test that generated routes include tags in decorator when provided."""
    # Create schema with tags
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
      description: "List all users"
      tags: [users, admin]
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

    # Verify tags are included in decorator
    assert 'tags=["users", "admin"]' in routes_code or "tags=['users', 'admin']" in routes_code, \
        "Should include tags in route decorator"


def test_openapi_metadata_in_fastapi_app(temp_dir: Path) -> None:
    """Test that OpenAPI metadata is properly exposed in FastAPI application.

    This is the core test for api_021: verify that operation_id and other metadata
    appear correctly in the OpenAPI schema.
    """
    # Create schema with comprehensive metadata
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
    GET:
      name: list_users
      summary: "List users"
      description: "Retrieve a list of all users"
      tags: [users]
      response:
        200:
          type: list[User]
    POST:
      name: create_user
      summary: "Create user"
      description: "Create a new user account"
      tags: [users]
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
      summary: "Get user by ID"
      description: "Retrieve a single user by their ID"
      tags: [users]
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
    output_dir = temp_dir / "backend" / "app"

    models_generator = PythonModelGenerator()
    models_file, _ = models_generator.generate_to_file(schema, output_dir)

    routes_generator = PythonRouteGenerator()
    routes_file, _ = routes_generator.generate_to_file(schema, output_dir)

    # Create __init__.py files
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    parent_init = output_dir.parent / "__init__.py"
    parent_init.write_text("")

    # Create a test FastAPI app and check OpenAPI schema
    app_script = f"""
import sys
sys.path.insert(0, '{temp_dir}')

from fastapi import FastAPI
from backend.app import routes

try:
    # Create FastAPI app
    app = FastAPI(title="Test App")

    # Include the generated router
    app.include_router(routes.router, prefix="/api")

    # Get OpenAPI schema
    openapi_schema = app.openapi()
    print("SUCCESS: OpenAPI schema generated")

    # Verify paths exist
    assert "/api/users" in openapi_schema["paths"], "Should have /api/users path"
    assert "/api/users/{{id}}" in openapi_schema["paths"], "Should have /api/users/{{id}} path"
    print("SUCCESS: Paths found in OpenAPI schema")

    # Verify operation_id for GET /users
    users_get = openapi_schema["paths"]["/api/users"]["get"]
    assert "operationId" in users_get, "GET /api/users should have operationId"
    assert users_get["operationId"] == "list_users", \
        f"operationId should be 'list_users', got '{{users_get['operationId']}}'"
    print("SUCCESS: operation_id 'list_users' verified")

    # Verify operation_id for POST /users
    users_post = openapi_schema["paths"]["/api/users"]["post"]
    assert "operationId" in users_post, "POST /api/users should have operationId"
    assert users_post["operationId"] == "create_user", \
        f"operationId should be 'create_user', got '{{users_post['operationId']}}'"
    print("SUCCESS: operation_id 'create_user' verified")

    # Verify operation_id for GET /users/{{id}}
    user_get = openapi_schema["paths"]["/api/users/{{id}}"]["get"]
    assert "operationId" in user_get, "GET /api/users/{{id}} should have operationId"
    assert user_get["operationId"] == "get_user", \
        f"operationId should be 'get_user', got '{{user_get['operationId']}}'"
    print("SUCCESS: operation_id 'get_user' verified")

    # Verify summary for GET /users
    assert "summary" in users_get, "GET /api/users should have summary"
    assert users_get["summary"] == "List users", \
        f"summary should be 'List users', got '{{users_get['summary']}}'"
    print("SUCCESS: summary verified for list_users")

    # Verify description for GET /users
    assert "description" in users_get, "GET /api/users should have description"
    assert users_get["description"] == "Retrieve a list of all users", \
        f"description mismatch: got '{{users_get['description']}}'"
    print("SUCCESS: description verified for list_users")

    # Verify tags for GET /users
    assert "tags" in users_get, "GET /api/users should have tags"
    assert "users" in users_get["tags"], \
        f"tags should contain 'users', got {{users_get['tags']}}"
    print("SUCCESS: tags verified for list_users")

    # Verify all endpoints have operation_id
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                assert "operationId" in operation, \
                    f"{{method.upper()}} {{path}} should have operationId"
    print("SUCCESS: All endpoints have operation_id")

except AssertionError as e:
    print(f"ASSERTION FAILED: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {{type(e).__name__}}: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

    app_file = temp_dir / "test_openapi_metadata.py"
    app_file.write_text(app_script)

    # Run the test script
    result = subprocess.run(
        [sys.executable, str(app_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify success
    assert result.returncode == 0, \
        f"OpenAPI metadata test failed. Output: {result.stdout}\nError: {result.stderr}"

    assert "SUCCESS: OpenAPI schema generated" in result.stdout, \
        "OpenAPI schema should be generated"
    assert "SUCCESS: operation_id 'list_users' verified" in result.stdout, \
        "operation_id should be set for list_users"
    assert "SUCCESS: operation_id 'create_user' verified" in result.stdout, \
        "operation_id should be set for create_user"
    assert "SUCCESS: operation_id 'get_user' verified" in result.stdout, \
        "operation_id should be set for get_user"
    assert "SUCCESS: summary verified for list_users" in result.stdout, \
        "summary should be included in OpenAPI metadata"
    assert "SUCCESS: description verified for list_users" in result.stdout, \
        "description should be included in OpenAPI metadata"
    assert "SUCCESS: tags verified for list_users" in result.stdout, \
        "tags should be included in OpenAPI metadata"
    assert "SUCCESS: All endpoints have operation_id" in result.stdout, \
        "All endpoints should have operation_id"


def test_operation_id_unique_across_endpoints(temp_dir: Path) -> None:
    """Test that each endpoint has a unique operation_id."""
    # Create schema with multiple endpoints
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true

  Post:
    fields:
      id:
        type: uuid
        primary: true

  Comment:
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

  /posts:
    GET:
      name: list_posts
      response:
        200:
          type: list[Post]

  /comments:
    GET:
      name: list_comments
      response:
        200:
          type: list[Comment]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Extract all operation_ids
    import re
    operation_ids = re.findall(r'operation_id="([^"]+)"', routes_code)

    # Verify all operation_ids are unique
    assert len(operation_ids) == len(set(operation_ids)), \
        f"operation_ids should be unique, found duplicates in: {operation_ids}"

    # Verify expected operation_ids are present
    assert "list_users" in operation_ids, "Should have list_users operation_id"
    assert "list_posts" in operation_ids, "Should have list_posts operation_id"
    assert "list_comments" in operation_ids, "Should have list_comments operation_id"


def test_tags_array_format_in_decorator(temp_dir: Path) -> None:
    """Test that tags are formatted as an array in the decorator."""
    # Create schema with multiple tags
    schema_content = """schnitzel: "1.0"

models:
  Product:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /admin/products:
    GET:
      name: list_admin_products
      description: "List products in admin panel"
      tags: [products, admin, inventory]
      response:
        200:
          type: list[Product]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify tags are in array format
    # Either double or single quotes are acceptable
    has_tags = ('tags=["products", "admin", "inventory"]' in routes_code or
                "tags=['products', 'admin', 'inventory']" in routes_code)
    assert has_tags, \
        "Should include tags as array in route decorator"


def test_summary_defaults_to_description_if_not_provided(temp_dir: Path) -> None:
    """Test that if summary is not provided, description is used for both."""
    # Create schema with only description (no summary)
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
      description: "Get all items"
      response:
        200:
          type: list[Item]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate both models and routes
    output_dir = temp_dir / "backend" / "app"

    models_generator = PythonModelGenerator()
    models_file, _ = models_generator.generate_to_file(schema, output_dir)

    routes_generator = PythonRouteGenerator()
    routes_file, _ = routes_generator.generate_to_file(schema, output_dir)

    # Create __init__.py files
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    parent_init = output_dir.parent / "__init__.py"
    parent_init.write_text("")

    # Create test script to check OpenAPI
    app_script = f"""
import sys
sys.path.insert(0, '{temp_dir}')

from fastapi import FastAPI
from backend.app import routes

try:
    app = FastAPI(title="Test App")
    app.include_router(routes.router, prefix="/api")

    openapi_schema = app.openapi()

    # Check that description is present
    items_get = openapi_schema["paths"]["/api/items"]["get"]
    assert "description" in items_get or "summary" in items_get, \
        "Should have either description or summary"

    # Verify it has the expected text
    desc_or_summary = items_get.get("description") or items_get.get("summary")
    assert "Get all items" in desc_or_summary, \
        f"Should contain description text, got: {{desc_or_summary}}"

    print("SUCCESS: Description or summary is properly set")

except AssertionError as e:
    print(f"ASSERTION FAILED: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {{type(e).__name__}}: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

    app_file = temp_dir / "test_description.py"
    app_file.write_text(app_script)

    # Run the test script
    result = subprocess.run(
        [sys.executable, str(app_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify success
    assert result.returncode == 0, \
        f"Description test failed. Output: {result.stdout}\nError: {result.stderr}"
    assert "SUCCESS: Description or summary is properly set" in result.stdout


def test_endpoint_without_openapi_metadata_still_works(temp_dir: Path) -> None:
    """Test that endpoints without explicit metadata still get operation_id."""
    # Create schema with minimal endpoint definition
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

    # Verify operation_id is still included even without other metadata
    assert 'operation_id="list_users"' in routes_code, \
        "Should include operation_id even without other metadata"


def test_openapi_metadata_with_auth_and_roles(temp_dir: Path) -> None:
    """Test that OpenAPI metadata works correctly with auth and roles."""
    # Create schema with auth and roles
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
  /admin/users:
    GET:
      name: list_all_users
      summary: "List all users"
      description: "Admin endpoint to list all users"
      tags: [admin, users]
      auth: required
      roles: [admin]
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

    # Verify all metadata is present
    assert 'operation_id="list_all_users"' in routes_code, \
        "Should have operation_id"
    assert 'summary="List all users"' in routes_code, \
        "Should have summary"
    assert ('tags=["admin", "users"]' in routes_code or
            "tags=['admin', 'users']" in routes_code), \
        "Should have tags"
    assert "Depends(require_roles(['admin']))" in routes_code, \
        "Should have role checking"


def test_openapi_metadata_with_query_parameters(temp_dir: Path) -> None:
    """Test that OpenAPI metadata works with query parameters."""
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
      name: search_users
      summary: "Search users"
      description: "Search users by name"
      tags: [users, search]
      query:
        name:
          type: string
          optional: true
          description: "User name to search for"
        limit:
          type: int
          default: 20
          description: "Maximum number of results"
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

    # Verify metadata is present alongside query parameters
    assert 'operation_id="search_users"' in routes_code, \
        "Should have operation_id"
    assert 'summary="Search users"' in routes_code, \
        "Should have summary"
    assert 'name: str | None = Query(' in routes_code, \
        "Should have query parameter 'name'"
    assert 'limit: int | None = Query(' in routes_code, \
        "Should have query parameter 'limit'"
