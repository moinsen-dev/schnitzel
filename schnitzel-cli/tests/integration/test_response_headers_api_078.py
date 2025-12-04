"""Integration tests for api_078 - FastAPI route generator adds response headers.

Test Requirements (from feature):
1. Update the route generator to support custom response headers defined in schema
2. Use FastAPI's Response object to set headers when needed
3. Support both static headers (always included) and dynamic headers (computed at runtime)
4. Common headers to support: X-Request-ID, Cache-Control, X-Total-Count (for pagination)

This feature ensures generated FastAPI routes can set custom HTTP response headers
as specified in the schema, supporting both static and dynamic header values.
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


def test_static_response_headers_generated(temp_dir: Path) -> None:
    """Test that static response headers are properly generated in route code."""
    # Create schema with static response headers
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
          headers:
            X-Request-ID:
              value: "fixed-id-123"
            Cache-Control:
              value: "max-age=3600, public"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify Response parameter is added
    assert "response: Response" in routes_code, \
        "Function should have Response parameter when headers are defined"

    # Verify Response is imported from fastapi
    assert "from fastapi import" in routes_code and "Response" in routes_code, \
        "Should import Response from fastapi"

    # Verify header setting code is generated
    assert 'response.headers["X-Request-ID"]' in routes_code, \
        "Should set X-Request-ID header"
    assert 'response.headers["Cache-Control"]' in routes_code, \
        "Should set Cache-Control header"
    assert '"max-age=3600, public"' in routes_code, \
        "Should set Cache-Control value"


def test_dynamic_response_headers_generated(temp_dir: Path) -> None:
    """Test that dynamic response headers have proper placeholders."""
    # Create schema with dynamic response headers
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /items:
    GET:
      name: list_items
      description: "List all items with pagination"
      pagination: true
      response:
        200:
          type: PaginatedResponse<Item>
          headers:
            X-Total-Count:
              dynamic: true
              placeholder: total_count
              description: "Total number of items"
            X-Page:
              dynamic: true
              placeholder: page
              description: "Current page number"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify Response parameter is added
    assert "response: Response" in routes_code, \
        "Function should have Response parameter for dynamic headers"

    # Verify dynamic header comments are present
    assert "# Set dynamic header: X-Total-Count" in routes_code, \
        "Should have comment for dynamic X-Total-Count header"
    assert "# Set dynamic header: X-Page" in routes_code, \
        "Should have comment for dynamic X-Page header"

    # Verify header setting code uses placeholders
    assert 'response.headers["X-Total-Count"] = str(total_count)' in routes_code, \
        "Should set X-Total-Count header with placeholder"
    assert 'response.headers["X-Page"] = str(page)' in routes_code, \
        "Should set X-Page header with placeholder"


def test_mixed_static_and_dynamic_headers(temp_dir: Path) -> None:
    """Test that endpoints can have both static and dynamic headers."""
    # Create schema with mixed headers
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
  /products:
    GET:
      name: list_products
      description: "List all products"
      pagination: true
      response:
        200:
          type: PaginatedResponse<Product>
          headers:
            Cache-Control:
              value: "no-cache, no-store"
            X-Total-Count:
              dynamic: true
              placeholder: total_count
            X-API-Version:
              value: "v1"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify both static and dynamic headers are present
    assert 'response.headers["Cache-Control"] = "no-cache, no-store"' in routes_code, \
        "Should set static Cache-Control header"
    assert 'response.headers["X-API-Version"] = "v1"' in routes_code, \
        "Should set static X-API-Version header"
    assert 'response.headers["X-Total-Count"] = str(total_count)' in routes_code, \
        "Should set dynamic X-Total-Count header"


def test_simple_string_header_syntax(temp_dir: Path) -> None:
    """Test that simple string header values work (shorthand syntax)."""
    # Create schema with simple string header values
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
      description: "Get a user by ID"
      response:
        200:
          type: User
          headers:
            X-Custom-Header: "custom-value"
            X-Another-Header: "another-value"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify simple string headers are set
    assert 'response.headers["X-Custom-Header"] = "custom-value"' in routes_code, \
        "Should set X-Custom-Header with simple string syntax"
    assert 'response.headers["X-Another-Header"] = "another-value"' in routes_code, \
        "Should set X-Another-Header with simple string syntax"


def test_response_headers_in_fastapi_app(temp_dir: Path) -> None:
    """Test that response headers code is properly generated and can be loaded.

    This is the core integration test: verify header setting code is correctly
    integrated into the route function.
    """
    # Create schema with response headers
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /items:
    GET:
      name: list_items
      description: "List items"
      response:
        200:
          type: list[Item]
          headers:
            X-Request-ID:
              value: "test-request-123"
            Cache-Control:
              value: "max-age=300"
            X-API-Version:
              value: "v1.0"
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

    # Read the generated routes file
    routes_content = routes_file.read_text()

    # Verify all three headers are set in the generated code
    assert 'response.headers["X-Request-ID"] = "test-request-123"' in routes_content, \
        "Should set X-Request-ID header in generated code"
    assert 'response.headers["Cache-Control"] = "max-age=300"' in routes_content, \
        "Should set Cache-Control header in generated code"
    assert 'response.headers["X-API-Version"] = "v1.0"' in routes_content, \
        "Should set X-API-Version header in generated code"

    # Create a test script to verify the code loads and FastAPI app can be created
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

    # Verify router was created successfully
    assert routes.router is not None, "Router should be created"
    print("SUCCESS: Router loaded successfully")

    # Get OpenAPI schema to verify endpoint exists
    openapi_schema = app.openapi()
    assert "/api/items" in openapi_schema["paths"], "Should have /api/items endpoint"
    print("SUCCESS: Endpoint registered in OpenAPI schema")

    # Verify endpoint has GET method
    items_path = openapi_schema["paths"]["/api/items"]
    assert "get" in items_path, "Should have GET method"
    print("SUCCESS: GET method registered")

    print("SUCCESS: All verification passed")

except AssertionError as e:
    print(f"ASSERTION FAILED: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {{type(e).__name__}}: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

    app_file = temp_dir / "test_response_headers.py"
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
        f"Response headers test failed. Output: {result.stdout}\nError: {result.stderr}"

    assert "SUCCESS: Router loaded successfully" in result.stdout, \
        "Router should load successfully"
    assert "SUCCESS: Endpoint registered in OpenAPI schema" in result.stdout, \
        "Endpoint should be registered"
    assert "SUCCESS: GET method registered" in result.stdout, \
        "GET method should be registered"


def test_pagination_with_total_count_header(temp_dir: Path) -> None:
    """Test pagination endpoint with X-Total-Count header."""
    # Create schema with paginated endpoint and X-Total-Count header
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
      description: "List products with pagination"
      pagination: true
      response:
        200:
          type: PaginatedResponse<Product>
          headers:
            X-Total-Count:
              dynamic: true
              placeholder: total_count
              description: "Total number of products across all pages"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify pagination parameters are present
    assert "page: int = Query(1, ge=1" in routes_code, \
        "Should have pagination page parameter"
    assert "per_page: int = Query(20, ge=1, le=100" in routes_code, \
        "Should have pagination per_page parameter"

    # Verify Response parameter is added
    assert "response: Response" in routes_code, \
        "Function should have Response parameter"

    # Verify X-Total-Count header is set dynamically
    assert "# Set dynamic header: X-Total-Count" in routes_code, \
        "Should have comment for X-Total-Count header"
    assert 'response.headers["X-Total-Count"] = str(total_count)' in routes_code, \
        "Should set X-Total-Count header"


def test_no_response_param_when_no_headers(temp_dir: Path) -> None:
    """Test that Response parameter is not added when no headers are defined."""
    # Create schema without response headers
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
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify Response parameter is NOT added when no headers
    assert "response: Response" not in routes_code, \
        "Function should not have Response parameter when no headers defined"

    # Verify no header setting code
    assert 'response.headers[' not in routes_code, \
        "Should not have any header setting code"


def test_headers_with_post_endpoint(temp_dir: Path) -> None:
    """Test that response headers work with POST endpoints."""
    # Create schema with POST endpoint and headers
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
          headers:
            X-Request-ID:
              dynamic: true
              placeholder: request_id
            Location:
              dynamic: true
              placeholder: user_location
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify POST decorator and 201 status code
    assert "@router.post('/users'" in routes_code, \
        "Should have POST decorator"
    assert "status_code=201" in routes_code, \
        "POST should have 201 status code"

    # Verify Response parameter is added
    assert "response: Response" in routes_code, \
        "POST function should have Response parameter"

    # Verify headers are set
    assert 'response.headers["X-Request-ID"] = str(request_id)' in routes_code, \
        "Should set X-Request-ID header"
    assert 'response.headers["Location"] = str(user_location)' in routes_code, \
        "Should set Location header"


def test_headers_with_multiple_endpoints(temp_dir: Path) -> None:
    """Test that headers are correctly set for multiple endpoints."""
    # Create schema with multiple endpoints with different headers
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
      description: "List users"
      response:
        200:
          type: list[User]
          headers:
            Cache-Control:
              value: "max-age=3600"

  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      description: "Get user by ID"
      response:
        200:
          type: User
          headers:
            Cache-Control:
              value: "max-age=300"
            X-Resource-Type:
              value: "user"
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify both endpoints have Response parameter
    # Count occurrences - should appear at least twice (once per endpoint)
    response_param_count = routes_code.count("response: Response")
    assert response_param_count >= 2, \
        f"Should have Response parameter in both endpoints, found {response_param_count}"

    # Verify different Cache-Control values for different endpoints
    assert '"max-age=3600"' in routes_code, \
        "Should have Cache-Control with max-age=3600 for list endpoint"
    assert '"max-age=300"' in routes_code, \
        "Should have Cache-Control with max-age=300 for get endpoint"
    assert 'X-Resource-Type' in routes_code, \
        "Should have X-Resource-Type header"


def test_generated_code_passes_syntax_check(temp_dir: Path) -> None:
    """Test that generated code with headers passes Python syntax check."""
    # Create schema with various header types
    schema_content = """schnitzel: "1.0"

models:
  Item:
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string

endpoints:
  /items:
    GET:
      name: list_items
      description: "List items"
      response:
        200:
          type: list[Item]
          headers:
            X-Static:
              value: "static-value"
            X-Dynamic:
              dynamic: true
              placeholder: dynamic_value
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate to files
    output_dir = temp_dir / "backend" / "app"

    models_generator = PythonModelGenerator()
    models_file, _ = models_generator.generate_to_file(schema, output_dir)

    routes_generator = PythonRouteGenerator()
    routes_file, _ = routes_generator.generate_to_file(schema, output_dir)

    # Verify files exist
    assert models_file.exists(), "models.py should be created"
    assert routes_file.exists(), "routes.py should be created"

    # Check Python syntax by compiling
    routes_content = routes_file.read_text()
    try:
        compile(routes_content, str(routes_file), 'exec')
        print("SUCCESS: Generated code passes Python syntax check")
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}\nCode:\n{routes_content}")
