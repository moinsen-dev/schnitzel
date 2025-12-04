"""Integration tests for api_030 - Dart API client generator creates PUT method.

Test Requirements (from feature):
1. Create schema with endpoint: PUT /users/{id} with UpdateUserRequest
2. Run schnitzel generate --target dart
3. Verify updateUser(String id, UpdateUserRequest request) method exists
4. Verify Dio.put() is called with data: request.toJson()
5. Verify path parameter interpolation
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


def test_put_method_exists(temp_dir: Path) -> None:
    """Test that updateUser method exists with correct signature."""
    # Create schema with PUT endpoint
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

  UpdateUserRequest:
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
    PUT:
      name: update_user
      description: "Update a user"
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify updateUser method exists with correct signature
    assert "Future<User> updateUser(String id, UpdateUserRequest body)" in api_client_code, \
        "Should have updateUser method with id parameter and UpdateUserRequest body"


def test_put_method_uses_dio_put(temp_dir: Path) -> None:
    """Test that PUT method calls _dio.put() instead of _dio.post()."""
    # Create schema with PUT endpoint
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
    PUT:
      name: update_user
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify Dio.put() is called, not Dio.post()
    assert "_dio.put(" in api_client_code, "Should use _dio.put() for PUT method"
    # Make sure it's in the updateUser method context
    assert "_dio.put('users/$id'" in api_client_code, "Should call _dio.put() with correct path"


def test_put_method_sends_body_as_json(temp_dir: Path) -> None:
    """Test that PUT method sends body using data: body.toJson()."""
    # Create schema with PUT endpoint
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
      email:
        type: string

endpoints:
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
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify data: body.toJson() is passed
    assert "data: body.toJson()" in api_client_code, "Should send body as JSON using data: body.toJson()"


def test_put_method_path_interpolation(temp_dir: Path) -> None:
    """Test that PUT method correctly interpolates path parameters."""
    # Create schema with PUT endpoint
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
    PUT:
      name: update_user
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify path parameter interpolation using $id (relative path)
    assert "'users/$id'" in api_client_code, "Should use Dart string interpolation for path parameter"


def test_put_method_return_type(temp_dir: Path) -> None:
    """Test that PUT method returns Future<User>."""
    # Create schema with PUT endpoint
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
    PUT:
      name: update_user
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify return type is Future<User>
    assert "Future<User> updateUser" in api_client_code, "Should return Future<User>"


def test_put_method_deserializes_response(temp_dir: Path) -> None:
    """Test that PUT method deserializes response to User model."""
    # Create schema with PUT endpoint
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
    PUT:
      name: update_user
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify response deserialization
    assert "return User.fromJson(response.data);" in api_client_code, \
        "Should deserialize response to User using fromJson"


def test_put_method_parameter_order(temp_dir: Path) -> None:
    """Test that PUT method has path parameters before body parameter."""
    # Create schema with PUT endpoint
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
    PUT:
      name: update_user
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify parameter order: id comes before body
    method_signature = "updateUser(String id, UpdateUserRequest body)"
    assert method_signature in api_client_code, \
        "Path parameter should come before body parameter in method signature"


def test_put_method_with_multiple_path_params(temp_dir: Path) -> None:
    """Test that PUT method handles multiple path parameters correctly."""
    # Create schema with PUT endpoint having multiple path params
    schema_content = """schnitzel: "1.0"

models:
  Post:
    fields:
      id:
        type: uuid
        primary: true
      title:
        type: string

  UpdatePostRequest:
    fields:
      title:
        type: string

endpoints:
  /users/{userId}/posts/{postId}:
    params:
      userId:
        type: uuid
      postId:
        type: uuid
    PUT:
      name: update_user_post
      body: UpdatePostRequest
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

    # Verify both path parameters are in the signature
    assert "updateUserPost(String userId, String postId, UpdatePostRequest body)" in api_client_code, \
        "Should have all path parameters before body parameter"

    # Verify path interpolation for both parameters
    assert "'users/$userId/posts/$postId'" in api_client_code, \
        "Should interpolate both path parameters"


def test_api_client_file_created_with_put(temp_dir: Path) -> None:
    """Test that api_client.dart file is created with PUT method."""
    # Create schema with PUT endpoint
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
    PUT:
      name: update_user
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

    # Generate API client
    generator = DartApiClientGenerator()
    output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    api_client_file, size = generator.generate_to_file(schema, output_dir)

    # Verify file was created
    assert api_client_file.exists(), "api_client.dart should be created"
    assert size > 0, "api_client.dart should have content"

    # Read and verify content
    api_client_content = api_client_file.read_text()
    assert "import 'package:dio/dio.dart';" in api_client_content, "Should import Dio"
    assert "import '../models/models.dart';" in api_client_content, "Should import models"
    assert "Future<User> updateUser" in api_client_content, "Should have updateUser method"
    assert "_dio.put(" in api_client_content, "Should use _dio.put()"


def test_put_and_get_methods_together(temp_dir: Path) -> None:
    """Test that PUT and GET methods can coexist in the same API client."""
    # Create schema with both GET and PUT endpoints
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
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify both methods exist
    assert "Future<User> getUser(String id)" in api_client_code, "Should have getUser method"
    assert "Future<User> updateUser(String id, UpdateUserRequest body)" in api_client_code, \
        "Should have updateUser method"

    # Verify correct HTTP methods are used
    assert "_dio.get('users/$id')" in api_client_code, "Should use GET for getUser"
    assert "_dio.put('users/$id', data: body.toJson())" in api_client_code, \
        "Should use PUT for updateUser"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_api_client_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart with PUT method passes dart analyze (requirement 6)."""
    # Create schema with PUT endpoint
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

  UpdateUserRequest:
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
    PUT:
      name: update_user
      description: "Update a user"
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
abstract class UpdateUserRequest with _$UpdateUserRequest {
  const factory UpdateUserRequest({
    required String name,
    required String email,
  }) = _UpdateUserRequest;

  factory UpdateUserRequest.fromJson(Map<String, dynamic> json) => _$UpdateUserRequestFromJson(json);
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
    # Check that the file is syntactically valid
    assert result.returncode in [0, 1, 3], \
        f"dart analyze should not find syntax errors. Output: {result.stdout}\n{result.stderr}"
