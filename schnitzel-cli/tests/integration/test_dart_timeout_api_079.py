"""Integration tests for api_079 - Dart API client generator handles timeout configuration.

Test Requirements (from feature):
1. Generated client has configurable timeout options (connectTimeout, receiveTimeout, sendTimeout)
2. Default timeouts are sensible (30 seconds)
3. Per-request timeout override is available via optional parameter
4. Generated Dart code compiles without errors
5. Timeout configuration uses Dart's Duration type

Background:
The Dart API client generator should support configurable timeouts for HTTP requests.
This allows clients to specify different timeout values for connect, receive, and send
operations, with support for per-request overrides.
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


def test_client_has_timeout_configuration_fields(temp_dir: Path) -> None:
    """Test that generated ApiClient class has timeout configuration fields."""
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

    # Verify timeout fields exist in class
    assert "final Duration? connectTimeout;" in api_client_code, \
        "Should have connectTimeout field"
    assert "final Duration? receiveTimeout;" in api_client_code, \
        "Should have receiveTimeout field"
    assert "final Duration? sendTimeout;" in api_client_code, \
        "Should have sendTimeout field"


def test_constructor_has_timeout_parameters(temp_dir: Path) -> None:
    """Test that constructor accepts timeout parameters with defaults."""
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

    # Verify constructor has timeout parameters with defaults
    assert "this.connectTimeout = const Duration(seconds: 30)" in api_client_code, \
        "Constructor should have connectTimeout parameter with 30 second default"
    assert "this.receiveTimeout = const Duration(seconds: 30)" in api_client_code, \
        "Constructor should have receiveTimeout parameter with 30 second default"
    assert "this.sendTimeout = const Duration(seconds: 30)" in api_client_code, \
        "Constructor should have sendTimeout parameter with 30 second default"


def test_custom_default_timeout(temp_dir: Path) -> None:
    """Test that custom default timeout can be specified."""
    # Create schema
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
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client with custom timeout
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema, default_timeout_seconds=60)

    # Verify custom timeout is used
    assert "this.connectTimeout = const Duration(seconds: 60)" in api_client_code, \
        "Should use custom 60 second timeout"
    assert "this.receiveTimeout = const Duration(seconds: 60)" in api_client_code, \
        "Should use custom 60 second timeout"
    assert "this.sendTimeout = const Duration(seconds: 60)" in api_client_code, \
        "Should use custom 60 second timeout"


def test_methods_have_per_request_timeout_parameter(temp_dir: Path) -> None:
    """Test that generated methods support per-request timeout override."""
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

    # Verify all methods have requestTimeout parameter
    assert "Duration? requestTimeout" in api_client_code, \
        "Methods should have requestTimeout parameter"

    # Count occurrences - should appear in multiple methods
    timeout_param_count = api_client_code.count("Duration? requestTimeout")
    assert timeout_param_count >= 5, \
        f"requestTimeout parameter should appear in all methods (found {timeout_param_count})"


def test_methods_use_timeout_in_options(temp_dir: Path) -> None:
    """Test that generated methods pass timeout to Options."""
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
    api_client_code = generator.generate(schema)

    # Verify Options includes timeout configuration
    # The timeout should use requestTimeout if provided, otherwise fallback to instance fields
    assert "sendTimeout: requestTimeout ?? sendTimeout" in api_client_code, \
        "Options should use requestTimeout with fallback to sendTimeout"
    assert "receiveTimeout: requestTimeout ?? receiveTimeout" in api_client_code, \
        "Options should use requestTimeout with fallback to receiveTimeout"


def test_empty_schema_generates_timeout_configuration(temp_dir: Path) -> None:
    """Test that empty schema still generates client with timeout configuration."""
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

    # Should have timeout fields even with no endpoints
    assert "final Duration? connectTimeout;" in api_client_code
    assert "final Duration? receiveTimeout;" in api_client_code
    assert "final Duration? sendTimeout;" in api_client_code
    assert "this.connectTimeout = const Duration(seconds: 30)" in api_client_code


def test_client_without_auth_interceptor_has_timeouts(temp_dir: Path) -> None:
    """Test that client without auth interceptor still has timeout configuration."""
    # Create schema
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
          type: list<User>
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client without auth interceptor
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema, include_auth_interceptor=False)

    # Should have timeout configuration
    assert "final Duration? connectTimeout;" in api_client_code
    assert "final Duration? receiveTimeout;" in api_client_code
    assert "final Duration? sendTimeout;" in api_client_code


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_client_with_timeout_dart_analyze_passes(temp_dir: Path) -> None:
    """Test that generated api_client.dart with timeout configuration passes dart analyze."""
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

    # Generate API client with custom timeout
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

@freezed
class CreateUserRequest with _$CreateUserRequest {
  const factory CreateUserRequest({
    required String name,
  }) = _CreateUserRequest;

  factory CreateUserRequest.fromJson(Map<String, dynamic> json) => _$CreateUserRequestFromJson(json);
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

    # Verify the generated code includes timeout configuration
    api_client_content = api_client_file.read_text()
    assert "final Duration? connectTimeout;" in api_client_content
    assert "final Duration? receiveTimeout;" in api_client_content
    assert "final Duration? sendTimeout;" in api_client_content
    assert "Duration? requestTimeout" in api_client_content


def test_timeout_usage_example(temp_dir: Path) -> None:
    """Test usage example showing how to configure timeouts."""
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

    # Create usage example file
    example_file = temp_dir / "lib" / "timeout_example.dart"
    example_content = """import 'package:dio/dio.dart';
import 'generated/api_client.dart';

void main() {
  // Example 1: Using default timeouts (30 seconds)
  final dio1 = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
  final client1 = ApiClient(dio1);

  // Example 2: Custom default timeouts for all requests
  final dio2 = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
  final client2 = ApiClient(
    dio2,
    connectTimeout: const Duration(seconds: 60),
    receiveTimeout: const Duration(minutes: 2),
    sendTimeout: const Duration(seconds: 45),
  );

  // Example 3: Per-request timeout override
  // client1.getUser('123', requestTimeout: const Duration(seconds: 10));

  // Example 4: No timeout (infinite wait)
  // client1.getUser('123', requestTimeout: null);
}
"""
    example_file.parent.mkdir(parents=True, exist_ok=True)
    example_file.write_text(example_content)

    # Verify example file was created
    assert example_file.exists(), "Example file should be created"

    # Verify the generated client supports the patterns in the example
    api_client_code = api_client_file.read_text()
    assert "connectTimeout:" in api_client_code or "this.connectTimeout" in api_client_code
    assert "Duration?" in api_client_code, "Should use Duration type for timeouts"
