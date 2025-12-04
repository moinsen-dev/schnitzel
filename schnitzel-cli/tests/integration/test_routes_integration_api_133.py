"""Integration tests for api_133 - Generated routes integrate with FastAPI app.

Test Requirements (from feature):
1. Verify generated routes can be imported and registered with FastAPI
2. Generate code that creates an APIRouter properly
3. Ensure routes use proper decorators (@router.get, @router.post, etc.)
4. Verify generated code includes proper imports (from fastapi import APIRouter, Depends, etc.)
5. Write a test that generates routes and verifies they can be registered with a FastAPI app

This test ensures the generated routes are not just syntactically correct but can
actually be imported and used with a real FastAPI application.
"""

import tempfile
import os
import sys
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


def test_generated_routes_have_apirouter_import(temp_dir: Path) -> None:
    """Test that generated routes include APIRouter import."""
    # Create schema with basic endpoint
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

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify APIRouter import
    assert "from fastapi import APIRouter" in routes_code, \
        "Generated routes must import APIRouter from fastapi"


def test_generated_routes_create_router_instance(temp_dir: Path) -> None:
    """Test that generated routes create an APIRouter instance."""
    # Create schema with basic endpoint
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

    # Verify router instance creation
    assert "router = APIRouter()" in routes_code, \
        "Generated routes must create a router instance with 'router = APIRouter()'"


def test_generated_routes_use_router_decorators(temp_dir: Path) -> None:
    """Test that generated routes use @router decorators for each HTTP method."""
    # Create schema with multiple HTTP methods
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
    PUT:
      name: update_user
      body: CreateUserRequest
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

    # Verify all HTTP method decorators are present
    assert "@router.get(" in routes_code, "Should have @router.get decorator"
    assert "@router.post(" in routes_code, "Should have @router.post decorator"
    assert "@router.put(" in routes_code, "Should have @router.put decorator"
    assert "@router.delete(" in routes_code, "Should have @router.delete decorator"

    # Verify decorators are properly formatted with paths
    assert "@router.get('/users'" in routes_code
    assert "@router.post('/users'" in routes_code
    assert "@router.get('/users/{id}'" in routes_code
    assert "@router.put('/users/{id}'" in routes_code
    assert "@router.delete('/users/{id}'" in routes_code


def test_generated_routes_have_necessary_imports(temp_dir: Path) -> None:
    """Test that generated routes include all necessary imports."""
    # Create schema with various features requiring different imports
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
      auth: required
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

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify necessary imports are present
    assert "from fastapi import" in routes_code, "Should have FastAPI imports"
    assert "APIRouter" in routes_code, "Should import APIRouter"
    assert "from uuid import UUID" in routes_code, "Should import UUID for path parameters"
    assert "from .models import" in routes_code, "Should import models"

    # Since we have query parameters, should import Query
    assert "Query" in routes_code, "Should import Query for query parameters"

    # Since we have auth requirement, should import Depends
    assert "Depends" in routes_code, "Should import Depends for authentication"


def test_generated_routes_can_be_imported_as_python_module(temp_dir: Path) -> None:
    """Test that generated routes file can be imported as a Python module."""
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
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate both models and routes (routes depend on models)
    output_dir = temp_dir / "backend" / "app"

    models_generator = PythonModelGenerator()
    models_file, _ = models_generator.generate_to_file(schema, output_dir)

    routes_generator = PythonRouteGenerator()
    routes_file, _ = routes_generator.generate_to_file(schema, output_dir)

    # Create __init__.py to make it a package
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    # Create parent __init__.py
    parent_init = output_dir.parent / "__init__.py"
    parent_init.write_text("")

    # Verify files were created
    assert models_file.exists(), "models.py should be created"
    assert routes_file.exists(), "routes.py should be created"
    assert init_file.exists(), "__init__.py should be created"

    # Try to import the routes module using subprocess to avoid polluting test environment
    test_script = f"""
import sys
sys.path.insert(0, '{temp_dir}')

try:
    from backend.app import routes
    print("SUCCESS: Module imported")

    # Verify router exists
    assert hasattr(routes, 'router'), "routes module should have 'router' attribute"
    print("SUCCESS: router attribute exists")

    # Verify router is an APIRouter instance (check its type name)
    router_type_name = type(routes.router).__name__
    assert router_type_name == 'APIRouter', f"router should be APIRouter, got {{router_type_name}}"
    print("SUCCESS: router is APIRouter instance")

    # Verify route functions exist
    assert hasattr(routes, 'list_users'), "Should have list_users function"
    assert hasattr(routes, 'create_user'), "Should have create_user function"
    print("SUCCESS: Route functions exist")

except Exception as e:
    print(f"FAILED: {{type(e).__name__}}: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

    test_file = temp_dir / "test_import.py"
    test_file.write_text(test_script)

    # Run the test script
    result = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Check results
    assert "SUCCESS: Module imported" in result.stdout, \
        f"Failed to import routes module. Output: {result.stdout}\nError: {result.stderr}"
    assert "SUCCESS: router attribute exists" in result.stdout, \
        f"router attribute not found. Output: {result.stdout}\nError: {result.stderr}"
    assert "SUCCESS: router is APIRouter instance" in result.stdout, \
        f"router is not APIRouter. Output: {result.stdout}\nError: {result.stderr}"
    assert "SUCCESS: Route functions exist" in result.stdout, \
        f"Route functions not found. Output: {result.stdout}\nError: {result.stderr}"


def test_generated_routes_can_be_registered_with_fastapi_app(temp_dir: Path) -> None:
    """Test that generated routes can be registered with a FastAPI application.

    This is the core test for api_133: verify that generated routes integrate
    properly with a FastAPI app via app.include_router().
    """
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

endpoints:
  /users:
    GET:
      name: list_users
      description: "List all users"
      query:
        page:
          type: int
          default: 1
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

    # Create a test FastAPI app that includes the generated router
    app_script = f"""
import sys
sys.path.insert(0, '{temp_dir}')

from fastapi import FastAPI
from backend.app import routes

try:
    # Create FastAPI app
    app = FastAPI(title="Test App")

    # Include the generated router
    app.include_router(routes.router, prefix="/api", tags=["users"])

    print("SUCCESS: Router registered with FastAPI app")

    # Verify routes were registered by checking app.routes
    route_paths = [route.path for route in app.routes]
    print(f"Registered routes: {{route_paths}}")

    # Verify expected routes are present
    assert "/api/users" in route_paths, "GET /api/users should be registered"
    assert "/api/users/{{id}}" in route_paths, "Routes with path params should be registered"
    print("SUCCESS: Expected routes found in app")

    # Verify route methods - FastAPI stores multiple methods on same path as separate routes
    # Collect all methods for each path
    methods_by_path = {{}}
    for route in app.routes:
        if hasattr(route, 'methods'):
            path = route.path
            if path not in methods_by_path:
                methods_by_path[path] = set()
            methods_by_path[path].update(route.methods)

    print(f"Methods by path: {{methods_by_path}}")

    # Check that we have the expected HTTP methods
    if "/api/users" in methods_by_path:
        methods_set = methods_by_path["/api/users"]
        assert "GET" in methods_set, f"GET should be available on /api/users, found: {{methods_set}}"
        assert "POST" in methods_set, f"POST should be available on /api/users, found: {{methods_set}}"
        print("SUCCESS: HTTP methods correctly registered")

    # Try to get OpenAPI schema (this validates the entire route structure)
    openapi_schema = app.openapi()
    print("SUCCESS: OpenAPI schema generated")

    # Verify paths in OpenAPI schema
    assert "/api/users" in openapi_schema["paths"], "OpenAPI should include /api/users"
    assert "/api/users/{{id}}" in openapi_schema["paths"], "OpenAPI should include /api/users/{{id}}"
    print("SUCCESS: OpenAPI schema includes all endpoints")

    # Verify operation IDs in OpenAPI schema
    users_get = openapi_schema["paths"]["/api/users"].get("get")
    assert users_get is not None, "GET /api/users should exist in OpenAPI"
    assert users_get.get("operationId") == "list_users", "operationId should match endpoint name"
    print("SUCCESS: Operation IDs correctly set")

except AssertionError as e:
    print(f"ASSERTION FAILED: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {{type(e).__name__}}: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

    app_file = temp_dir / "test_app.py"
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
        f"FastAPI integration failed. Output: {result.stdout}\nError: {result.stderr}"

    assert "SUCCESS: Router registered with FastAPI app" in result.stdout, \
        "Router should be successfully registered"
    assert "SUCCESS: Expected routes found in app" in result.stdout, \
        "Expected routes should be found in FastAPI app"
    assert "SUCCESS: HTTP methods correctly registered" in result.stdout, \
        "HTTP methods should be correctly registered"
    assert "SUCCESS: OpenAPI schema generated" in result.stdout, \
        "OpenAPI schema should be generated successfully"
    assert "SUCCESS: OpenAPI schema includes all endpoints" in result.stdout, \
        "All endpoints should appear in OpenAPI schema"
    assert "SUCCESS: Operation IDs correctly set" in result.stdout, \
        "Operation IDs should match endpoint names from schema"


def test_generated_routes_with_auth_dependency(temp_dir: Path) -> None:
    """Test that routes with auth dependencies can be integrated with FastAPI."""
    # Create schema with auth-protected endpoints
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
      auth: required
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

    # Verify Depends import for auth
    assert "from fastapi import" in routes_code and "Depends" in routes_code, \
        "Should import Depends for authentication"

    # Verify auth dependency in function signature
    assert "current_user" in routes_code, \
        "Should have current_user parameter for authenticated endpoints"
    assert "Depends(get_current_user)" in routes_code, \
        "Should use Depends with get_current_user function"


def test_empty_schema_generates_minimal_valid_router(temp_dir: Path) -> None:
    """Test that schema with no endpoints still generates a valid importable router."""
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
    output_dir = temp_dir / "backend" / "app"
    routes_file, _ = generator.generate_to_file(schema, output_dir)

    # Create necessary __init__.py files
    init_file = output_dir / "__init__.py"
    init_file.write_text("")

    parent_init = output_dir.parent / "__init__.py"
    parent_init.write_text("")

    # Try to import and use the empty router
    test_script = f"""
import sys
sys.path.insert(0, '{temp_dir}')

from fastapi import FastAPI
from backend.app import routes

try:
    # Create FastAPI app
    app = FastAPI(title="Test App")

    # Include the empty router (should work without errors)
    app.include_router(routes.router)

    print("SUCCESS: Empty router can be registered with FastAPI app")

except Exception as e:
    print(f"FAILED: {{type(e).__name__}}: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

    test_file = temp_dir / "test_empty_router.py"
    test_file.write_text(test_script)

    # Run the test script
    result = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=True,
        text=True,
        cwd=temp_dir
    )

    # Verify success
    assert result.returncode == 0, \
        f"Empty router integration failed. Output: {result.stdout}\nError: {result.stderr}"
    assert "SUCCESS: Empty router can be registered with FastAPI app" in result.stdout, \
        "Empty router should be successfully registered"


def test_generated_routes_file_structure_for_integration(temp_dir: Path) -> None:
    """Test that generated routes file has the correct structure for FastAPI integration."""
    # Create schema
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
      response:
        200:
          type: list[Item]
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate routes
    generator = PythonRouteGenerator()
    routes_code = generator.generate(schema)

    # Verify structure is correct for FastAPI integration
    lines = routes_code.split('\n')

    # Should have imports at the top
    import_section_found = False
    for line in lines[:20]:  # Check first 20 lines
        if "from fastapi import" in line:
            import_section_found = True
            break
    assert import_section_found, "Should have FastAPI imports at the top"

    # Should have router creation before route definitions
    router_line = None
    first_decorator_line = None
    for i, line in enumerate(lines):
        if "router = APIRouter()" in line:
            router_line = i
        if "@router." in line and first_decorator_line is None:
            first_decorator_line = i

    assert router_line is not None, "Should create router instance"
    if first_decorator_line is not None:
        assert router_line < first_decorator_line, \
            "Router creation should come before route decorators"

    # Each route function should have:
    # 1. Decorator (@router.method)
    # 2. Async function definition
    # 3. Function body
    assert "@router.get('/items'" in routes_code, "Should have route decorator"
    assert "async def list_items" in routes_code, "Should have async function"
    assert "-> list[Item]:" in routes_code, "Should have return type annotation"
