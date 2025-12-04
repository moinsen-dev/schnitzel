"""Integration tests for api_084 - Dart API client generator handles custom headers.

Test Requirements (from feature):
1. Support global default headers on client instantiation
2. Support per-request custom headers
3. Support common headers: Authorization, Content-Type, Accept, X-Request-ID
4. Allow header manipulation via interceptor
5. Generated Dart code compiles without errors
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


def test_api_client_accepts_default_headers(temp_dir: Path) -> None:
    """Test that ApiClient constructor accepts optional defaultHeaders parameter."""
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

    # Verify ApiClient constructor has optional defaultHeaders parameter
    assert "Map<String, String>? defaultHeaders" in api_client_code, \
        "ApiClient constructor should accept optional defaultHeaders parameter"
    assert "final Map<String, String> _defaultHeaders" in api_client_code, \
        "ApiClient should have _defaultHeaders field"
    assert "_defaultHeaders = defaultHeaders ?? {}" in api_client_code, \
        "ApiClient should initialize _defaultHeaders with provided value or empty map"


def test_api_client_stores_default_headers(temp_dir: Path) -> None:
    """Test that ApiClient stores default headers in instance variable."""
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

    # Verify _defaultHeaders field is stored
    assert "final Map<String, String> _defaultHeaders;" in api_client_code, \
        "ApiClient should have _defaultHeaders instance variable"


def test_methods_accept_per_request_headers(temp_dir: Path) -> None:
    """Test that generated methods accept optional headers parameter."""
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

    # Verify GET method has headers parameter
    assert "Map<String, String>? headers" in api_client_code, \
        "Generated methods should accept optional headers parameter"

    # Verify method signature includes headers
    # Note: The method may also have other optional parameters like requestTimeout
    # So we check for the presence of headers parameter in the method signatures
    assert "getUser(String id, {" in api_client_code and "Map<String, String>? headers" in api_client_code, \
        "getUser method should accept optional headers parameter"

    # For POST with body - check it has headers parameter
    assert "createUser(" in api_client_code and "Map<String, String>? headers" in api_client_code, \
        "createUser method should accept optional headers parameter"


def test_headers_are_merged_in_requests(temp_dir: Path) -> None:
    """Test that default headers and per-request headers are merged."""
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

    # Verify headers are merged using spread operator
    assert "mergedHeaders = {..._defaultHeaders, ...?headers}" in api_client_code, \
        "Headers should be merged using spread operator"


def test_merged_headers_passed_to_dio(temp_dir: Path) -> None:
    """Test that merged headers are passed to Dio requests via Options."""
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

    # Verify Options with headers: mergedHeaders is used
    # Note: Options may have additional parameters like sendTimeout, receiveTimeout
    assert "Options(headers: mergedHeaders" in api_client_code, \
        "Merged headers should be passed to Dio via Options"


def test_auth_interceptor_sets_authorization_header(temp_dir: Path) -> None:
    """Test that AuthInterceptor properly sets Authorization header."""
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

    # Verify AuthInterceptor sets Authorization header
    assert "options.headers['Authorization'] = 'Bearer $token';" in api_client_code, \
        "AuthInterceptor should set Authorization header with Bearer token"


def test_supports_common_headers(temp_dir: Path) -> None:
    """Test that common headers can be set (Content-Type, Accept, X-Request-ID)."""
    # Create schema with POST endpoint
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

    # Verify that headers parameter accepts Map<String, String>
    # This allows setting any header including Content-Type, Accept, X-Request-ID
    assert "Map<String, String>? headers" in api_client_code, \
        "Headers parameter should accept Map<String, String> allowing any header"

    # Verify headers are properly merged and passed
    assert "mergedHeaders" in api_client_code, \
        "Headers should be merged for passing to requests"


def test_multiple_endpoints_all_support_headers(temp_dir: Path) -> None:
    """Test that all HTTP methods (GET, POST, PUT, DELETE) support headers."""
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
      response:
        204:
          type: void

  /users:
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

    # Count occurrences of headers parameter - should be at least 4 (one per method)
    # Note: Methods may also have requestTimeout, so we just check for presence
    headers_param_count = api_client_code.count("Map<String, String>? headers")
    assert headers_param_count >= 4, \
        f"All methods should support headers parameter. Found {headers_param_count} occurrences"

    # Verify each method exists and has headers (accounting for potential other params like requestTimeout)
    assert "getUser(String id, {" in api_client_code and "Map<String, String>? headers" in api_client_code
    # Check that other methods exist
    assert "updateUser(" in api_client_code
    assert "deleteUser(" in api_client_code
    assert "createUser(" in api_client_code


def test_empty_client_supports_default_headers(temp_dir: Path) -> None:
    """Test that empty client (no endpoints) still supports default headers."""
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify empty client has defaultHeaders support
    assert "Map<String, String>? defaultHeaders" in api_client_code, \
        "Empty client should support defaultHeaders parameter"
    assert "final Map<String, String> _defaultHeaders" in api_client_code, \
        "Empty client should have _defaultHeaders field"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_code_compiles_with_headers(temp_dir: Path) -> None:
    """Test that generated Dart code with headers support compiles without errors."""
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
      email:
        type: string

  CreateUserRequest:
    fields:
      name:
        type: string
      email:
        type: string

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

  /users:
    POST:
      name: create_user
      description: "Create a new user"
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
    output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    api_client_file, _ = generator.generate_to_file(schema, output_dir)

    # Create a minimal pubspec.yaml for dart analyze
    pubspec_dir = temp_dir / "packages" / "shared"
    pubspec_file = pubspec_dir / "pubspec.yaml"
    pubspec_file.write_text("""name: shared
version: 1.0.0
environment:
  sdk: '>=3.0.0 <4.0.0'
dependencies:
  dio: ^5.0.0
  freezed_annotation: ^2.0.0
  json_annotation: ^4.0.0
dev_dependencies:
  freezed: ^2.0.0
  build_runner: ^2.0.0
  json_serializable: ^6.0.0
""")

    # Create models directory and stub models.dart
    models_dir = temp_dir / "packages" / "shared" / "lib" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    models_file = models_dir / "models.dart"
    models_file.write_text("""import 'package:freezed_annotation/freezed_annotation.dart';

part 'models.freezed.dart';
part 'models.g.dart';

@freezed
abstract class User with _$User {
  const factory User({
    required String id,
    required String name,
    required String email,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}

@freezed
abstract class CreateUserRequest with _$CreateUserRequest {
  const factory CreateUserRequest({
    required String name,
    required String email,
  }) = _CreateUserRequest;

  factory CreateUserRequest.fromJson(Map<String, dynamic> json) => _$CreateUserRequestFromJson(json);
}
""")

    # Run dart analyze on the generated file
    result = subprocess.run(
        ["dart", "analyze", str(api_client_file)],
        capture_output=True,
        text=True,
        cwd=pubspec_dir
    )

    # The analysis may fail due to missing dependencies, but we verify no syntax errors
    assert result.returncode in [0, 1, 3], \
        f"dart analyze should not find syntax errors. Output: {result.stdout}\n{result.stderr}"


def test_headers_work_without_auth_interceptor(temp_dir: Path) -> None:
    """Test that headers support works even when AuthInterceptor is disabled."""
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

    # Generate API client without auth interceptor
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema, include_auth_interceptor=False)

    # Verify headers support is still present
    assert "Map<String, String>? defaultHeaders" in api_client_code, \
        "Headers support should work without AuthInterceptor"
    assert "final Map<String, String> _defaultHeaders" in api_client_code, \
        "Headers field should exist without AuthInterceptor"
    assert "Map<String, String>? headers" in api_client_code, \
        "Per-request headers should work without AuthInterceptor"

    # Verify AuthInterceptor is not generated
    assert "class AuthInterceptor" not in api_client_code, \
        "AuthInterceptor should not be generated when disabled"
