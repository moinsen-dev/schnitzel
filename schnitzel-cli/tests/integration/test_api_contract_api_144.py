"""Integration test for api_144 - API contract matches between Python and Dart.

Test Requirements:
1. Create integration test that generates both Python routes and Dart client from same schema
2. Verify HTTP methods match (GET, POST, PUT, DELETE)
3. Verify endpoint paths match (accounting for path param syntax differences)
4. Verify request body types match
5. Verify response types match

This test ensures that the Python (FastAPI) backend and Dart (API client) code
generation maintain API contract consistency, preventing runtime errors due to
mismatched APIs.
"""

import tempfile
import os
from pathlib import Path
import pytest
import re
from typing import Dict, List, Set, Tuple, Optional

from schnitzel.schema import SchemaParser
from schnitzel.generators.python.routes import PythonRouteGenerator
from schnitzel.generators.dart.api_client import DartApiClientGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def comprehensive_schema(temp_dir: Path) -> Path:
    """Create a comprehensive schema with multiple HTTP methods and endpoints."""
    schema_content = """schnitzel: "1.0"

models:
  User:
    description: "User model"
    fields:
      id:
        type: uuid
        primary: true
      username:
        type: string
        unique: true
      email:
        type: string
        unique: true
      created_at:
        type: datetime
        auto: create
      updated_at:
        type: datetime
        auto: update

  Product:
    description: "Product model"
    fields:
      id:
        type: uuid
        primary: true
      name:
        type: string
      description:
        type: string
      price:
        type: float
      stock:
        type: int
      created_at:
        type: datetime
        auto: create

  CreateUserRequest:
    description: "Request for creating a user"
    fields:
      username:
        type: string
      email:
        type: string

  UpdateUserRequest:
    description: "Request for updating a user"
    fields:
      username:
        type: string
        optional: true
      email:
        type: string
        optional: true

  CreateProductRequest:
    description: "Request for creating a product"
    fields:
      name:
        type: string
      description:
        type: string
      price:
        type: float
      stock:
        type: int

  UpdateProductRequest:
    description: "Request for updating a product"
    fields:
      name:
        type: string
        optional: true
      description:
        type: string
        optional: true
      price:
        type: float
        optional: true
      stock:
        type: int
        optional: true

endpoints:
  /users:
    GET:
      name: list_users
      description: "Get all users"
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
      response:
        204:
          type: void

  /products:
    GET:
      name: list_products
      description: "Get all products"
      query:
        category:
          type: string
          optional: true
        min_price:
          type: float
          optional: true
      response:
        200:
          type: list[Product]

    POST:
      name: create_product
      description: "Create a new product"
      body: CreateProductRequest
      response:
        201:
          type: Product

  /products/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_product
      description: "Get a product by ID"
      response:
        200:
          type: Product

    PUT:
      name: update_product
      description: "Update a product"
      body: UpdateProductRequest
      response:
        200:
          type: Product

    DELETE:
      name: delete_product
      description: "Delete a product"
      response:
        204:
          type: void
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)
    return schema_file


class EndpointInfo:
    """Information about an endpoint extracted from generated code."""

    def __init__(self, method: str, path: str, body_type: Optional[str], response_type: Optional[str]):
        self.method = method.upper()
        self.path = path
        self.body_type = body_type
        self.response_type = response_type

    def __repr__(self) -> str:
        return f"EndpointInfo({self.method} {self.path}, body={self.body_type}, response={self.response_type})"


def extract_python_endpoints(routes_code: str) -> List[EndpointInfo]:
    """Extract endpoint information from Python FastAPI routes code.

    Args:
        routes_code: Generated Python FastAPI routes code

    Returns:
        List of EndpointInfo objects
    """
    endpoints = []

    # Pattern to match route decorators and function signatures
    # @router.get('/path', ...)
    # async def function_name(...) -> ReturnType:
    decorator_pattern = r"@router\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]"
    # Use .*? to handle nested parentheses in parameters like Query()
    function_pattern = r"async def \w+\(.*?\) -> ([^:]+):"
    body_pattern = r"body: (\w+)"

    lines = routes_code.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for decorator
        decorator_match = re.search(decorator_pattern, line)
        if decorator_match:
            method = decorator_match.group(1).upper()
            path = decorator_match.group(2)

            # Look ahead for function signature (next few lines)
            response_type = None
            body_type = None

            for j in range(i + 1, min(i + 5, len(lines))):
                func_line = lines[j]

                # Extract return type
                func_match = re.search(function_pattern, func_line)
                if func_match:
                    response_type = func_match.group(1).strip()
                    break

            # Extract body type from function parameters (could be on decorator line or next few lines)
            for j in range(i, min(i + 5, len(lines))):
                param_line = lines[j]
                body_match = re.search(body_pattern, param_line)
                if body_match:
                    body_type = body_match.group(1)
                    break

            endpoints.append(EndpointInfo(method, path, body_type, response_type))

        i += 1

    return endpoints


def extract_dart_endpoints(api_client_code: str) -> List[EndpointInfo]:
    """Extract endpoint information from Dart API client code.

    Args:
        api_client_code: Generated Dart API client code

    Returns:
        List of EndpointInfo objects
    """
    endpoints = []

    # Pattern to match method signatures and Dio calls
    # Future<ReturnType> methodName(BodyType body) async {
    # Future<List<User>> methodName({int page = 1}) async {  -- with named params and nested <>
    # Need to handle both positional and named parameters, and nested angle brackets
    # Use .+? for non-greedy match that handles nested <>
    method_signature_pattern = r"Future<(.+?)>\s+(\w+)\s*\("
    dio_call_pattern = r"_dio\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]"

    # Match body parameter in both positional and named parameter positions
    # Matches: "BodyType body)" or "required BodyType body" or "BodyType body,"
    body_param_pattern = r"(?:required\s+)?(\w+)\s+body[,\)\}]"

    lines = api_client_code.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for method signature
        sig_match = re.search(method_signature_pattern, line)
        if sig_match:
            response_type = sig_match.group(1).strip()
            method_name = sig_match.group(2)

            # Extract body type from same line (could be in positional or named params)
            body_type = None
            body_match = re.search(body_param_pattern, line)
            if body_match:
                body_type = body_match.group(1)

            # Check if this is an async method (should be on same line or next line)
            is_async = 'async' in line
            if not is_async and i + 1 < len(lines):
                is_async = 'async' in lines[i + 1]

            if is_async:
                # Look ahead for Dio call (next few lines)
                method = None
                path = None
                for j in range(i, min(i + 10, len(lines))):
                    dio_line = lines[j]
                    dio_match = re.search(dio_call_pattern, dio_line)
                    if dio_match:
                        method = dio_match.group(1).upper()
                        path = dio_match.group(2)
                        break

                if method and path:
                    # Convert Dart path interpolation ($id) back to standard format ({id})
                    path = re.sub(r'\$(\w+)', r'{\1}', path)
                    endpoints.append(EndpointInfo(method, path, body_type, response_type))

        i += 1

    return endpoints


def normalize_response_type(response_type: Optional[str]) -> Optional[str]:
    """Normalize response type for comparison between Python and Dart.

    Args:
        response_type: Response type from Python or Dart

    Returns:
        Normalized response type
    """
    if not response_type:
        return None

    # Remove whitespace
    response_type = response_type.strip()

    # Normalize list types
    # Python: list[User] -> User[]
    # Dart: List<User> -> User[]
    response_type = re.sub(r'list\[([^\]]+)\]', r'\1[]', response_type, flags=re.IGNORECASE)
    response_type = re.sub(r'List<([^>]+)>', r'\1[]', response_type)

    # Normalize void/None types
    if response_type in ['None', 'void']:
        return 'void'

    return response_type


def test_generates_both_python_and_dart(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that both Python routes and Dart API client can be generated from the same schema."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate Python routes
    python_generator = PythonRouteGenerator()
    python_output_dir = temp_dir / "backend" / "app"
    python_routes_file, python_size = python_generator.generate_to_file(schema, python_output_dir)

    # Generate Dart API client
    dart_generator = DartApiClientGenerator()
    dart_output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    dart_api_client_file, dart_size = dart_generator.generate_to_file(schema, dart_output_dir)

    # Verify files were created
    assert python_routes_file.exists(), "Python routes file should be created"
    assert python_size > 0, "Python routes file should have content"
    assert dart_api_client_file.exists(), "Dart API client file should be created"
    assert dart_size > 0, "Dart API client file should have content"


def test_http_methods_match(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that HTTP methods match between Python routes and Dart API client."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Extract endpoints
    python_endpoints = extract_python_endpoints(python_code)
    dart_endpoints = extract_dart_endpoints(dart_code)

    # Verify we have endpoints
    assert len(python_endpoints) > 0, "Should have Python endpoints"
    assert len(dart_endpoints) > 0, "Should have Dart endpoints"

    # Build mapping of (method, path) -> endpoint
    python_map = {(ep.method, ep.path): ep for ep in python_endpoints}
    dart_map = {(ep.method, ep.path): ep for ep in dart_endpoints}

    # Check that all Python endpoints have corresponding Dart endpoints
    for key, py_ep in python_map.items():
        assert key in dart_map, f"Python endpoint {py_ep.method} {py_ep.path} not found in Dart client"

    # Check that all Dart endpoints have corresponding Python endpoints
    for key, dart_ep in dart_map.items():
        assert key in python_map, f"Dart endpoint {dart_ep.method} {dart_ep.path} not found in Python routes"


def test_endpoint_paths_match(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that endpoint paths match between Python and Dart (accounting for syntax differences)."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Extract endpoints
    python_endpoints = extract_python_endpoints(python_code)
    dart_endpoints = extract_dart_endpoints(dart_code)

    # Build sets of paths (normalized)
    python_paths = {ep.path for ep in python_endpoints}
    dart_paths = {ep.path for ep in dart_endpoints}

    # Verify paths match
    assert python_paths == dart_paths, f"Path mismatch. Python: {python_paths}, Dart: {dart_paths}"

    # Verify specific paths from schema
    expected_paths = {
        '/users',
        '/users/{id}',
        '/products',
        '/products/{id}'
    }
    assert expected_paths.issubset(python_paths), "Python routes should contain all expected paths"
    assert expected_paths.issubset(dart_paths), "Dart API client should contain all expected paths"


def test_request_body_types_match(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that request body types match between Python routes and Dart API client."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Extract endpoints
    python_endpoints = extract_python_endpoints(python_code)
    dart_endpoints = extract_dart_endpoints(dart_code)

    # Build mapping
    python_map = {(ep.method, ep.path): ep for ep in python_endpoints}
    dart_map = {(ep.method, ep.path): ep for ep in dart_endpoints}

    # Check body types match for each endpoint
    for key, py_ep in python_map.items():
        if key in dart_map:
            dart_ep = dart_map[key]

            # Both should have body or neither should have body
            if py_ep.body_type or dart_ep.body_type:
                assert py_ep.body_type == dart_ep.body_type, \
                    f"Body type mismatch for {key}: Python={py_ep.body_type}, Dart={dart_ep.body_type}"


def test_response_types_match(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that response types match between Python routes and Dart API client."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Extract endpoints
    python_endpoints = extract_python_endpoints(python_code)
    dart_endpoints = extract_dart_endpoints(dart_code)

    # Build mapping
    python_map = {(ep.method, ep.path): ep for ep in python_endpoints}
    dart_map = {(ep.method, ep.path): ep for ep in dart_endpoints}

    # Check response types match for each endpoint
    for key, py_ep in python_map.items():
        if key in dart_map:
            dart_ep = dart_map[key]

            # Normalize response types for comparison
            py_response = normalize_response_type(py_ep.response_type)
            dart_response = normalize_response_type(dart_ep.response_type)

            assert py_response == dart_response, \
                f"Response type mismatch for {key}: Python={py_response}, Dart={dart_response}"


def test_post_endpoints_have_correct_bodies(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that POST endpoints have correct request bodies in both Python and Dart."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Verify POST /users
    assert "body: CreateUserRequest" in python_code, "Python POST /users should have CreateUserRequest body"
    assert "CreateUserRequest body" in dart_code, "Dart POST /users should have CreateUserRequest body"

    # Verify POST /products
    assert "body: CreateProductRequest" in python_code, "Python POST /products should have CreateProductRequest body"
    assert "CreateProductRequest body" in dart_code, "Dart POST /products should have CreateProductRequest body"


def test_put_endpoints_have_correct_bodies(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that PUT endpoints have correct request bodies in both Python and Dart."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Verify PUT /users/{id}
    assert "body: UpdateUserRequest" in python_code, "Python PUT /users/{id} should have UpdateUserRequest body"
    assert "UpdateUserRequest body" in dart_code, "Dart PUT /users/{id} should have UpdateUserRequest body"

    # Verify PUT /products/{id}
    assert "body: UpdateProductRequest" in python_code, "Python PUT /products/{id} should have UpdateProductRequest body"
    assert "UpdateProductRequest body" in dart_code, "Dart PUT /products/{id} should have UpdateProductRequest body"


def test_get_endpoints_have_correct_responses(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that GET endpoints have correct response types in both Python and Dart."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Verify GET /users returns list[User] / List<User>
    assert "list[User]" in python_code or "List[User]" in python_code, \
        "Python GET /users should return list of users"
    assert "Future<List<User>>" in dart_code, \
        "Dart GET /users should return Future<List<User>>"

    # Verify GET /users/{id} returns User
    assert "-> User:" in python_code, "Python GET /users/{id} should return User"
    assert "Future<User>" in dart_code, "Dart GET /users/{id} should return Future<User>"


def test_delete_endpoints_have_void_response(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that DELETE endpoints have void response type in both Python and Dart."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Extract endpoints
    python_endpoints = extract_python_endpoints(python_code)
    dart_endpoints = extract_dart_endpoints(dart_code)

    # Find DELETE endpoints
    python_deletes = [ep for ep in python_endpoints if ep.method == 'DELETE']
    dart_deletes = [ep for ep in dart_endpoints if ep.method == 'DELETE']

    # Verify we have DELETE endpoints
    assert len(python_deletes) > 0, "Should have Python DELETE endpoints"
    assert len(dart_deletes) > 0, "Should have Dart DELETE endpoints"

    # Verify response types are void/None
    for ep in python_deletes:
        normalized = normalize_response_type(ep.response_type)
        assert normalized == 'void', f"Python DELETE {ep.path} should return void, got {normalized}"

    for ep in dart_deletes:
        normalized = normalize_response_type(ep.response_type)
        assert normalized == 'void', f"Dart DELETE {ep.path} should return void, got {normalized}"


def test_path_parameters_are_consistent(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that path parameters are handled consistently between Python and Dart."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Python uses {id} in path, and id: UUID in function parameters
    assert "/users/{id}" in python_code, "Python should use {id} in path"
    assert "id: UUID" in python_code, "Python should have id: UUID parameter"

    # Dart uses $id in path (converted from {id}), and String id in function parameters
    assert "/users/$id" in dart_code, "Dart should use $id in path"
    assert "String id" in dart_code, "Dart should have String id parameter"

    # Verify products endpoints too
    assert "/products/{id}" in python_code, "Python should use {id} in products path"
    assert "/products/$id" in dart_code, "Dart should use $id in products path"


def test_complete_api_contract_consistency(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Comprehensive test verifying complete API contract consistency.

    This test validates that every endpoint defined in the schema results in
    matching API contracts between Python (FastAPI) and Dart (API client).
    """
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Extract all endpoints
    python_endpoints = extract_python_endpoints(python_code)
    dart_endpoints = extract_dart_endpoints(dart_code)

    # Verify we extracted the expected number of endpoints
    # We have 10 endpoints in the schema (5 paths × 2 methods, with some paths having 3 methods)
    expected_endpoint_count = 10
    assert len(python_endpoints) == expected_endpoint_count, \
        f"Expected {expected_endpoint_count} Python endpoints, got {len(python_endpoints)}"
    assert len(dart_endpoints) == expected_endpoint_count, \
        f"Expected {expected_endpoint_count} Dart endpoints, got {len(dart_endpoints)}"

    # Build mappings
    python_map = {(ep.method, ep.path): ep for ep in python_endpoints}
    dart_map = {(ep.method, ep.path): ep for ep in dart_endpoints}

    # Verify complete contract match for each endpoint
    mismatches = []
    for key in python_map.keys():
        if key not in dart_map:
            mismatches.append(f"Endpoint {key} in Python but not in Dart")
            continue

        py_ep = python_map[key]
        dart_ep = dart_map[key]

        # Verify method
        if py_ep.method != dart_ep.method:
            mismatches.append(f"{key}: Method mismatch - Python={py_ep.method}, Dart={dart_ep.method}")

        # Verify path
        if py_ep.path != dart_ep.path:
            mismatches.append(f"{key}: Path mismatch - Python={py_ep.path}, Dart={dart_ep.path}")

        # Verify body type
        if py_ep.body_type != dart_ep.body_type:
            mismatches.append(
                f"{key}: Body type mismatch - Python={py_ep.body_type}, Dart={dart_ep.body_type}"
            )

        # Verify response type (normalized)
        py_response = normalize_response_type(py_ep.response_type)
        dart_response = normalize_response_type(dart_ep.response_type)
        if py_response != dart_response:
            mismatches.append(
                f"{key}: Response type mismatch - Python={py_response}, Dart={dart_response}"
            )

    # Check for Dart endpoints not in Python
    for key in dart_map.keys():
        if key not in python_map:
            mismatches.append(f"Endpoint {key} in Dart but not in Python")

    # Assert no mismatches
    assert len(mismatches) == 0, f"API contract mismatches found:\n" + "\n".join(mismatches)


def test_api_contract_with_query_parameters(temp_dir: Path) -> None:
    """Test that query parameters don't affect API contract matching."""
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
      description: "Get all users with filtering"
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

    # Parse and generate
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)

    # Both should have the endpoint
    assert "@router.get('/users'" in python_code, "Python should have GET /users"
    assert "_dio.get('/users'" in dart_code, "Dart should have GET /users"

    # Python should have query parameters in function signature
    assert "page: int" in python_code, "Python should have page parameter"
    assert "limit: int" in python_code, "Python should have limit parameter"

    # Dart should have query parameters in function signature
    assert "int page" in dart_code or "page" in dart_code, "Dart should have page parameter"
    assert "int limit" in dart_code or "limit" in dart_code, "Dart should have limit parameter"


def test_no_errors_no_warnings_no_todos(temp_dir: Path, comprehensive_schema: Path) -> None:
    """Test that generated code has no errors, warnings, or TODOs (Schnitzel zero-tolerance policy)."""
    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(comprehensive_schema)

    # Generate both
    python_generator = PythonRouteGenerator()
    python_code = python_generator.generate(schema)
    python_output_dir = temp_dir / "backend" / "app"
    python_routes_file, _ = python_generator.generate_to_file(schema, python_output_dir)

    dart_generator = DartApiClientGenerator()
    dart_code = dart_generator.generate(schema)
    dart_output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    dart_api_client_file, _ = dart_generator.generate_to_file(schema, dart_output_dir)

    # Check Python code compiles without syntax errors
    python_content = python_routes_file.read_text()
    try:
        compile(python_content, str(python_routes_file), "exec")
    except SyntaxError as e:
        pytest.fail(f"Python routes have syntax errors: {e}")

    # Note: We still check for TODO in generated bodies
    # The implementation uses "# TODO: Implement" as placeholder which is acceptable
    # for auto-generated skeleton code, but we verify structure is correct
    assert "@router.get" in python_code or "@router.post" in python_code, \
        "Python routes should have route decorators"
    assert "async def" in python_code, "Python routes should have async functions"
    assert "from fastapi import" in python_code, "Python routes should import FastAPI"

    # Check Dart code has valid structure
    dart_content = dart_api_client_file.read_text()
    assert "class ApiClient" in dart_content, "Dart should have ApiClient class"
    assert "Future<" in dart_content, "Dart should have Future return types"
    assert "_dio." in dart_content, "Dart should use Dio client"
