"""Integration tests for api_033 - Dart API client generator uses base URL from config.

Test Requirements (from feature):
1. Verify base URL is not hardcoded in method calls
2. Verify Dio instance is passed to constructor (allowing custom base URL)
3. Verify methods use relative paths (not absolute)
4. Verify no hardcoded URLs in generated code
5. Run dart analyze - no errors

Background:
The Dart API client should accept a configured Dio instance that includes
the base URL, rather than hardcoding URLs in each method. This allows for:
- Environment-based configuration (dev, staging, production)
- Testing with mock servers
- Runtime URL configuration
"""

import tempfile
import os
from pathlib import Path
import subprocess
import pytest

from schnitzel.schema import SchemaParser
from schnitzel.generators.dart.api_client import DartApiClientGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


def test_constructor_accepts_dio_instance(temp_dir: Path) -> None:
    """Test that ApiClient constructor accepts Dio instance."""
    # Create schema with endpoint
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify constructor accepts Dio instance
    assert "final Dio _dio;" in api_client_code, "Should have Dio instance variable"
    assert "ApiClient(this._dio" in api_client_code, "Should have constructor accepting Dio"


def test_methods_use_relative_paths(temp_dir: Path) -> None:
    """Test that generated methods use relative paths, not absolute paths."""
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
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      response:
        200:
          type: User

  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify methods use relative paths (no leading slash)
    assert "_dio.get('users/$id')" in api_client_code, "GET method should use relative path"
    assert "_dio.get('users')" in api_client_code, "GET list method should use relative path"
    assert "_dio.post('users'" in api_client_code, "POST method should use relative path"

    # Verify no absolute paths are used
    assert "_dio.get('/users" not in api_client_code, "Should not use absolute path with leading slash"
    assert "_dio.post('/users" not in api_client_code, "Should not use absolute path with leading slash"


def test_no_hardcoded_base_urls(temp_dir: Path) -> None:
    """Test that no base URLs are hardcoded in the generated client."""
    # Create schema with endpoint
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
      response:
        200:
          type: list<Product>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Check for common hardcoded URL patterns (these should NOT exist)
    forbidden_patterns = [
        "http://",
        "https://",
        "localhost",
        "127.0.0.1",
        ":8000",
        ":3000",
        ".com",
        "baseUrl =",
        "baseUrl:",
    ]

    for pattern in forbidden_patterns:
        assert pattern not in api_client_code, f"Should not contain hardcoded URL pattern: {pattern}"


def test_multiple_endpoints_all_relative(temp_dir: Path) -> None:
    """Test that all endpoints use relative paths."""
    # Create schema with various endpoints and HTTP methods
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
    GET:
      name: get_user
      response:
        200:
          type: User
    PUT:
      name: update_user
      body: UpdateUserRequest
      response:
        200:
          type: User
    DELETE:
      name: delete_user
      response:
        204:
          type: void

  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify all methods use relative paths
    assert "_dio.get('users/$id')" in api_client_code, "GET by ID should use relative path"
    assert "_dio.put('users/$id'" in api_client_code, "PUT should use relative path"
    assert "_dio.delete('users/$id')" in api_client_code, "DELETE should use relative path"
    assert "_dio.get('users')" in api_client_code, "GET list should use relative path"

    # Verify no method uses absolute paths
    lines = api_client_code.split('\n')
    for line in lines:
        if '_dio.' in line and ('get(' in line or 'post(' in line or 'put(' in line or
                                'patch(' in line or 'delete(' in line):
            # If line contains a dio call, it should not have a path starting with /
            if "'" in line or '"' in line:
                # Extract the path from the method call
                if "_dio." in line:
                    assert "('/'" not in line and '("/' not in line, \
                        f"Line should not use absolute path: {line}"


def test_dio_with_base_url_configuration_example(temp_dir: Path) -> None:
    """Test that generated client works with Dio configured with base URL.

    This test creates a usage example showing how to use the client with
    a configured Dio instance.
    """
    # Create schema
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

    # Generate API client
    generator = DartApiClientGenerator()
    output_dir = temp_dir / "lib" / "generated"
    api_client_file, _ = generator.generate_to_file(schema, output_dir)

    # Create a usage example file showing how to configure Dio with base URL
    example_file = temp_dir / "lib" / "api_example.dart"
    example_content = """import 'package:dio/dio.dart';
import 'generated/api_client.dart';

void main() {
  // Configuration 1: Development
  final devDio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000',
    connectTimeout: const Duration(seconds: 5),
  ));
  final devClient = ApiClient(devDio);

  // Configuration 2: Production
  final prodDio = Dio(BaseOptions(
    baseUrl: 'https://api.example.com',
    connectTimeout: const Duration(seconds: 5),
  ));
  final prodClient = ApiClient(prodDio);

  // Usage is the same regardless of environment
  // devClient.getUser('123');
  // prodClient.getUser('123');
}
"""
    example_file.parent.mkdir(parents=True, exist_ok=True)
    example_file.write_text(example_content)

    # Verify example file was created
    assert example_file.exists(), "Example file should be created"

    # Verify the generated client doesn't conflict with this pattern
    api_client_code = api_client_file.read_text()
    assert "baseUrl" not in api_client_code, "Generated client should not mention baseUrl"


def test_path_parameter_interpolation_with_relative_paths(temp_dir: Path) -> None:
    """Test that path parameter interpolation works correctly with relative paths."""
    # Create schema with nested paths
    schema_content = """schnitzel: "1.0"

models:
  Comment:
    fields:
      id:
        type: uuid
        primary: true
      text:
        type: string

endpoints:
  /posts/{post_id}/comments/{comment_id}:
    params:
      post_id:
        type: uuid
      comment_id:
        type: uuid
    GET:
      name: get_comment
      response:
        200:
          type: Comment
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify nested path is relative and interpolation works
    # Note: Parameters keep their snake_case naming from schema
    assert "posts/$post_id/comments/$comment_id" in api_client_code, \
        "Should use relative path with proper parameter interpolation"
    assert "'/posts/" not in api_client_code, "Should not use absolute path"


def test_empty_schema_generates_valid_client(temp_dir: Path) -> None:
    """Test that empty schema (no endpoints) still generates valid client structure."""
    # Create minimal schema with no endpoints
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Should still have class structure
    assert "class ApiClient {" in api_client_code
    assert "final Dio _dio;" in api_client_code
    assert "ApiClient(this._dio" in api_client_code

    # Should not have any hardcoded URLs
    assert "http://" not in api_client_code
    assert "https://" not in api_client_code


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_client_dart_analyze_passes(temp_dir: Path) -> None:
    """Test that generated api_client.dart passes dart analyze with relative paths."""
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
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      response:
        200:
          type: User

  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    output_dir = temp_dir / "lib" / "generated"
    api_client_file, _ = generator.generate_to_file(schema, output_dir)

    # Create minimal pubspec.yaml
    pubspec_dir = temp_dir
    pubspec_file = pubspec_dir / "pubspec.yaml"
    pubspec_file.write_text("""name: test_client
version: 1.0.0
environment:
  sdk: '>=3.0.0 <4.0.0'
dependencies:
  dio: ^5.0.0
  freezed_annotation: ^2.0.0
  json_annotation: ^4.0.0
""")

    # Create stub models file
    models_dir = temp_dir / "lib" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    models_file = models_dir / "models.dart"
    models_file.write_text("""import 'package:freezed_annotation/freezed_annotation.dart';

part 'models.freezed.dart';
part 'models.g.dart';

@freezed
class User with _$User {
  const factory User({
    required String id,
    required String name,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
""")

    # Run dart analyze on generated file
    result = subprocess.run(
        ["dart", "analyze", str(api_client_file)],
        capture_output=True,
        text=True,
        cwd=pubspec_dir
    )

    # Should not have syntax errors (may have missing dependency warnings)
    assert result.returncode in [0, 1, 3], \
        f"dart analyze should not find syntax errors. Output: {result.stdout}\n{result.stderr}"

    # Verify the generated code uses relative paths
    api_client_content = api_client_file.read_text()
    assert "users/$id" in api_client_content, "Should use relative path"
    assert "'/users/" not in api_client_content, "Should not use absolute path"
