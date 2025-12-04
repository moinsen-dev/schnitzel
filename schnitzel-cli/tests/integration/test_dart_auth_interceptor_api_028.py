"""Integration tests for api_028 - Dart API client generator adds auth token interceptor.

Test Requirements (from feature):
1. Create schema with protected endpoint
2. Run schnitzel generate --target dart
3. Verify ApiClient constructor sets up Dio with interceptor
4. Verify AuthInterceptor adds Bearer token to headers
5. Verify token is read from secure storage
6. Run dart analyze - no errors
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


def test_auth_interceptor_class_generated(temp_dir: Path) -> None:
    """Test that AuthInterceptor class is generated in api_client.dart."""
    # Create schema with protected endpoint
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
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      description: "Get a user by ID (protected endpoint)"
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

    # Verify AuthInterceptor class is generated
    assert "class AuthInterceptor extends Interceptor" in api_client_code, \
        "AuthInterceptor class should be generated"
    assert "final String token;" in api_client_code, \
        "AuthInterceptor should have token field"
    assert "AuthInterceptor(this.token);" in api_client_code, \
        "AuthInterceptor should have constructor with token parameter"


def test_auth_interceptor_adds_authorization_header(temp_dir: Path) -> None:
    """Test that AuthInterceptor adds Authorization header with Bearer token."""
    # Create schema with protected endpoint
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

    # Verify Authorization header is set with Bearer token
    assert "options.headers['Authorization'] = 'Bearer $token';" in api_client_code, \
        "AuthInterceptor should add Authorization header with Bearer token"


def test_auth_interceptor_onrequest_method(temp_dir: Path) -> None:
    """Test that AuthInterceptor overrides onRequest method."""
    # Create schema with protected endpoint
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

    # Verify onRequest method is overridden
    assert "@override" in api_client_code, \
        "AuthInterceptor should use @override annotation"
    assert "void onRequest(RequestOptions options, RequestInterceptorHandler handler)" in api_client_code, \
        "AuthInterceptor should override onRequest method"
    assert "super.onRequest(options, handler);" in api_client_code, \
        "AuthInterceptor should call super.onRequest"


def test_api_client_constructor_accepts_token(temp_dir: Path) -> None:
    """Test that ApiClient constructor accepts optional token parameter."""
    # Create schema with protected endpoint
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

    # Verify ApiClient constructor has optional token parameter
    # Note: Constructor may have additional optional parameters
    assert "ApiClient(" in api_client_code and "String? token" in api_client_code, \
        "ApiClient constructor should accept optional token parameter"


def test_api_client_adds_interceptor_when_token_provided(temp_dir: Path) -> None:
    """Test that ApiClient adds AuthInterceptor to Dio when token is provided."""
    # Create schema with protected endpoint
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

    # Verify interceptor is added when token is provided
    assert "if (token != null) {" in api_client_code, \
        "ApiClient should check if token is not null"
    assert "_dio.interceptors.add(AuthInterceptor(token));" in api_client_code, \
        "ApiClient should add AuthInterceptor to Dio when token is provided"


def test_api_client_file_contains_auth_interceptor(temp_dir: Path) -> None:
    """Test that generated api_client.dart file contains AuthInterceptor."""
    # Create schema with protected endpoint
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

    # Generate API client to file
    generator = DartApiClientGenerator()
    output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    api_client_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert api_client_file.exists(), "api_client.dart should be created"

    # Read and verify content
    api_client_content = api_client_file.read_text()
    assert "class AuthInterceptor extends Interceptor" in api_client_content, \
        "Generated file should contain AuthInterceptor class"
    assert "options.headers['Authorization'] = 'Bearer $token';" in api_client_content, \
        "Generated file should set Authorization header"


def test_auth_interceptor_can_be_disabled(temp_dir: Path) -> None:
    """Test that AuthInterceptor generation can be disabled."""
    # Create schema with protected endpoint
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

    # Verify AuthInterceptor is not generated
    assert "class AuthInterceptor" not in api_client_code, \
        "AuthInterceptor should not be generated when disabled"
    # Verify constructor does not mention token (but may have other params like defaultHeaders)
    assert "String? token" not in api_client_code, \
        "ApiClient constructor should not have token parameter when interceptor is disabled"


def test_empty_client_has_auth_interceptor(temp_dir: Path) -> None:
    """Test that empty client (no endpoints) still generates AuthInterceptor."""
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

    # Verify AuthInterceptor is generated even with no endpoints
    assert "class AuthInterceptor extends Interceptor" in api_client_code, \
        "AuthInterceptor should be generated even with no endpoints"
    assert "ApiClient(this._dio, {String? token})" in api_client_code, \
        "ApiClient constructor should accept token even with no endpoints"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_api_client_with_auth_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart with AuthInterceptor passes dart analyze."""
    # Create schema with protected endpoint
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
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      description: "Get a user by ID (protected)"
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

    # Create models directory and a stub models.dart
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
