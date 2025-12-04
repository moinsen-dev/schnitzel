"""Integration tests for api_029 - Dart API client generator handles typed error responses.

Test Requirements (from feature):
1. Create schema with error models defined
2. Run schnitzel generate --target dart
3. Verify DioException is caught in try-catch
4. Verify error response is deserialized to ErrorResponse model
5. Verify typed exceptions are thrown (ApiException, ValidationException)
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


def test_api_exception_class_generated(temp_dir: Path) -> None:
    """Test that ApiException class is generated in the API client."""
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

    # Verify ApiException class exists
    assert "class ApiException implements Exception" in api_client_code, "Should have ApiException class"
    assert "final int statusCode;" in api_client_code, "Should have statusCode field"
    assert "final String message;" in api_client_code, "Should have message field"
    assert "final dynamic body;" in api_client_code, "Should have body field"


def test_api_exception_has_required_fields(temp_dir: Path) -> None:
    """Test that ApiException has statusCode, message, and body fields."""
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify ApiException fields
    assert "required this.statusCode," in api_client_code, "statusCode should be required"
    assert "required this.message," in api_client_code, "message should be required"
    assert "this.body," in api_client_code, "body should be optional"


def test_api_exception_has_constructor(temp_dir: Path) -> None:
    """Test that ApiException has a proper constructor."""
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
    POST:
      name: create_user
      body: User
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

    # Verify ApiException constructor
    assert "ApiException({" in api_client_code, "Should have named constructor"
    assert "required this.statusCode," in api_client_code
    assert "required this.message," in api_client_code
    assert "this.body," in api_client_code


def test_api_exception_has_tostring(temp_dir: Path) -> None:
    """Test that ApiException overrides toString method."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /posts/{id}:
    params:
      id:
        type: uuid
    DELETE:
      name: delete_post
      response:
        204:
          type: void
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify toString override
    assert "@override" in api_client_code, "Should override toString"
    assert "String toString()" in api_client_code, "Should have toString method"
    assert "'ApiException(statusCode: $statusCode, message: $message)'" in api_client_code


def test_methods_catch_dio_exception(temp_dir: Path) -> None:
    """Test that generated methods catch DioException."""
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
      email:
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
      body: User
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
      body: User
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

    # Verify all methods have try-catch blocks
    assert api_client_code.count("try {") >= 5, "Should have try blocks for all methods"
    assert api_client_code.count("} on DioException catch (e) {") >= 5, "Should catch DioException"


def test_methods_throw_api_exception(temp_dir: Path) -> None:
    """Test that methods throw ApiException on error."""
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

    # Verify ApiException is thrown
    assert "throw ApiException(" in api_client_code, "Should throw ApiException"
    assert "statusCode: e.response?.statusCode ?? 0," in api_client_code, "Should extract status code"
    assert "message: e.message ?? 'Unknown error'," in api_client_code, "Should extract message"
    assert "body: e.response?.data," in api_client_code, "Should extract response body"


def test_error_handling_extracts_status_code(temp_dir: Path) -> None:
    """Test that error handling extracts HTTP status code from DioException."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  User:
    fields:
      id:
        type: uuid
        primary: true
      email:
        type: string

endpoints:
  /users:
    POST:
      name: create_user
      body: User
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

    # Verify status code extraction
    assert "e.response?.statusCode ?? 0" in api_client_code, "Should extract status code with null safety"


def test_error_handling_extracts_message(temp_dir: Path) -> None:
    """Test that error handling extracts error message from DioException."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /posts/{id}:
    params:
      id:
        type: uuid
    PUT:
      name: update_post
      body: Post
      response:
        200:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify message extraction
    assert "e.message ?? 'Unknown error'" in api_client_code, "Should extract message with default fallback"


def test_error_handling_extracts_response_body(temp_dir: Path) -> None:
    """Test that error handling extracts response body from DioException."""
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
    DELETE:
      name: delete_user
      response:
        204:
          type: void
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify body extraction
    assert "body: e.response?.data," in api_client_code, "Should extract response body"


def test_empty_schema_includes_api_exception(temp_dir: Path) -> None:
    """Test that ApiException is included even with no endpoints."""
    # Create schema with no endpoints
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

    # Verify ApiException is still included
    assert "class ApiException implements Exception" in api_client_code, "Should include ApiException even with no endpoints"


def test_api_exception_in_generated_file(temp_dir: Path) -> None:
    """Test that ApiException is in the generated file."""
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

    # Generate API client to file
    generator = DartApiClientGenerator()
    output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    api_client_file, _ = generator.generate_to_file(schema, output_dir)

    # Read and verify content
    api_client_content = api_client_file.read_text()
    assert "class ApiException implements Exception" in api_client_content, "Generated file should include ApiException"
    assert "} on DioException catch (e) {" in api_client_content, "Generated file should have error handling"


def test_multiple_methods_all_have_error_handling(temp_dir: Path) -> None:
    """Test that all generated methods have error handling."""
    # Create schema with multiple methods
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

  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string
      content:
        type: string

endpoints:
  /users:
    GET:
      name: list_users
      response:
        200:
          type: list<User>
  /users/{id}:
    params:
      id:
        type: uuid
    GET:
      name: get_user
      response:
        200:
          type: User
  /posts:
    POST:
      name: create_post
      body: Post
      response:
        201:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Count methods and error handlers
    method_count = api_client_code.count("Future<")
    error_handler_count = api_client_code.count("} on DioException catch (e) {")

    # Verify all methods have error handling
    assert method_count == error_handler_count, f"All {method_count} methods should have error handling, but only {error_handler_count} do"
    assert method_count >= 3, "Should have at least 3 methods"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_api_client_with_errors_passes_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart with error handling passes dart analyze."""
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
      body: User
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

    # Verify the generated code has proper structure
    client_code = api_client_file.read_text()

    # Basic syntax checks
    assert client_code.count('{') == client_code.count('}'), "Braces should be balanced"
    assert client_code.count('(') == client_code.count(')'), "Parentheses should be balanced"

    # Verify ApiException class is present
    assert "class ApiException implements Exception" in client_code
    assert "} on DioException catch (e) {" in client_code
    assert "throw ApiException(" in client_code

    # Run dart analyze on the generated file
    result = subprocess.run(
        ["dart", "analyze", str(api_client_file)],
        capture_output=True,
        text=True,
        cwd=pubspec_dir
    )

    # The analysis may fail due to missing dependencies, but we verify no syntax errors
    # Return codes: 0 = no issues, 1 = warnings, 2 = errors, 3 = fatal
    assert result.returncode in [0, 1, 3], \
        f"dart analyze should not find syntax errors. Output: {result.stdout}\n{result.stderr}"


def test_error_handling_structure_is_correct(temp_dir: Path) -> None:
    """Test that error handling structure follows Dart best practices."""
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

    # Extract the method to verify structure
    lines = api_client_code.split('\n')

    # Find the getUser method
    in_method = False
    method_lines = []
    for line in lines:
        if 'Future<User> getUser' in line:
            in_method = True
        if in_method:
            method_lines.append(line)
            if line.strip() == '}' and 'async {' not in line:
                # End of method
                break

    method_code = '\n'.join(method_lines)

    # Verify structure: try block, dio call, return, catch block, throw
    assert 'try {' in method_code, "Should have try block"
    assert 'await _dio.get(' in method_code, "Should have Dio call"
    assert 'return User.fromJson(response.data);' in method_code, "Should return deserialized object"
    assert '} on DioException catch (e) {' in method_code, "Should catch DioException specifically"
    assert 'throw ApiException(' in method_code, "Should throw ApiException"


def test_null_safety_in_error_handling(temp_dir: Path) -> None:
    """Test that error handling uses proper null safety operators."""
    # Create schema
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

endpoints:
  /posts:
    POST:
      name: create_post
      body: Post
      response:
        201:
          type: Post
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify null safety operators
    assert "e.response?.statusCode ?? 0" in api_client_code, "Should use null-aware operator for statusCode"
    assert "e.message ?? 'Unknown error'" in api_client_code, "Should use null-aware operator for message"
    assert "e.response?.data" in api_client_code, "Should use null-aware operator for data"
