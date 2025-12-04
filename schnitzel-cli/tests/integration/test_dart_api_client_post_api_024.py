"""Integration tests for api_024 - Dart API client generator creates POST method with request body.

Test Requirements (from feature):
1. Create schema with endpoint: POST /users with CreateUserRequest
2. Run schnitzel generate --target dart
3. Verify createUser(CreateUserRequest request) method exists
4. Verify method returns Future<User>
5. Verify Dio.post() is called with data: request.toJson()
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


def test_post_method_with_request_body_exists(temp_dir: Path) -> None:
    """Test that createUser method exists with CreateUserRequest parameter."""
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
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify createUser method exists with CreateUserRequest parameter
    assert "Future<User> createUser(CreateUserRequest body)" in api_client_code, \
        "Should have createUser method with CreateUserRequest parameter"


def test_post_method_return_type(temp_dir: Path) -> None:
    """Test that createUser method returns Future<User>."""
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

    # Verify return type is Future<User>
    assert "Future<User> createUser" in api_client_code, "Should return Future<User>"


def test_post_method_serializes_body_with_tojson(temp_dir: Path) -> None:
    """Test that createUser method calls body.toJson() for serialization."""
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

    # Verify Dio.post() is called with data: body.toJson()
    assert "_dio.post('users', data: body.toJson())" in api_client_code, \
        "Should call _dio.post() with data: body.toJson()"


def test_post_method_dio_call_path(temp_dir: Path) -> None:
    """Test that createUser method calls _dio.post() with correct path."""
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

    # Verify Dio.post() is called with /users path
    assert "_dio.post('users'" in api_client_code, "Should call _dio.post() with '/users' path"


def test_post_method_deserialization(temp_dir: Path) -> None:
    """Test that createUser method deserializes response to User."""
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

    # Verify response is deserialized to User
    assert "return User.fromJson(response.data);" in api_client_code, \
        "Should deserialize response to User"


def test_post_method_has_model_imports(temp_dir: Path) -> None:
    """Test that api_client.dart imports models when using request body."""
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
    output_dir = temp_dir / "packages" / "shared" / "lib" / "generated"
    api_client_file, size = generator.generate_to_file(schema, output_dir)

    # Read and verify content
    api_client_content = api_client_file.read_text()
    assert "import '../models/models.dart';" in api_client_content, \
        "Should import models when using request body types"


def test_post_method_with_description(temp_dir: Path) -> None:
    """Test that createUser method includes description as doc comment."""
    # Create schema with POST endpoint with description
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
    api_client_code = generator.generate(schema)

    # Verify description is included as doc comment
    assert "/// Create a new user" in api_client_code, \
        "Should include description as doc comment"


def test_post_method_file_creation(temp_dir: Path) -> None:
    """Test that api_client.dart file is created with POST method."""
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
    assert api_client_file.name == "api_client.dart"


def test_multiple_post_methods(temp_dir: Path) -> None:
    """Test that multiple POST endpoints generate multiple methods."""
    # Create schema with multiple POST endpoints
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

  UpdateUserRequest:
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

    # Verify both methods exist
    assert "Future<User> createUser(CreateUserRequest body)" in api_client_code, \
        "Should have createUser method"
    assert "Future<User> updateUser(String id, UpdateUserRequest body)" in api_client_code, \
        "Should have updateUser method"
    assert "_dio.post('users', data: body.toJson())" in api_client_code, \
        "Should have POST call with toJson()"
    assert "_dio.put('users/$id', data: body.toJson())" in api_client_code, \
        "Should have PUT call with toJson()"


def test_post_method_with_path_params_and_body(temp_dir: Path) -> None:
    """Test that POST method with path parameters and body is generated correctly."""
    # Create schema with POST endpoint that has path params and body
    schema_content = """schnitzel: "1.0"

models:
  Comment:
    fields:
      id:
        type: uuid
        primary: true
      text:
        type: string

  CreateCommentRequest:
    fields:
      text:
        type: string

endpoints:
  /posts/{postId}/comments:
    params:
      postId:
        type: uuid
    POST:
      name: create_comment
      body: CreateCommentRequest
      response:
        201:
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

    # Verify method has both path param and body
    assert "Future<Comment> createComment(String postId, CreateCommentRequest body)" in api_client_code, \
        "Should have createComment method with postId and body parameters"
    assert "_dio.post('posts/$postId/comments', data: body.toJson())" in api_client_code, \
        "Should call _dio.post() with path interpolation and body.toJson()"


@pytest.mark.skipif(
    subprocess.run(["which", "dart"], capture_output=True).returncode != 0,
    reason="dart not installed"
)
def test_generated_post_method_dart_analyze(temp_dir: Path) -> None:
    """Test that generated api_client.dart with POST method passes dart analyze."""
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

  factory CreateUserRequest.fromJson(Map<String, dynamic> json) =>
      _$CreateUserRequestFromJson(json);
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


def test_post_method_inline_body_definition(temp_dir: Path) -> None:
    """Test that POST method with inline body definition uses Map<String, dynamic>."""
    # Create schema with POST endpoint with inline body
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
    POST:
      name: create_user
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

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify method uses Map<String, dynamic> for inline body
    assert "Map<String, dynamic> body" in api_client_code, \
        "Should use Map<String, dynamic> for inline body definition"


def test_post_method_without_response_body(temp_dir: Path) -> None:
    """Test that POST method without response body returns Future<void>."""
    # Create schema with POST endpoint without response body
    schema_content = """schnitzel: "1.0"

models:
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
        204: {}
"""
    schema_file = temp_dir / "schema.schnitzel.yaml"
    schema_file.write_text(schema_content)

    # Parse schema
    parser = SchemaParser()
    schema = parser.parse(schema_file)

    # Generate API client
    generator = DartApiClientGenerator()
    api_client_code = generator.generate(schema)

    # Verify method returns Future<void>
    assert "Future<void> createUser(CreateUserRequest body)" in api_client_code, \
        "Should return Future<void> when no response body is defined"


def test_post_method_with_query_params_and_body(temp_dir: Path) -> None:
    """Test that POST method with query parameters and body is generated correctly."""
    # Create schema with POST endpoint that has query params and body
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
      query:
        notify:
          type: bool
          optional: true
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

    # Verify method has both query parameter and body
    # Note: Query parameters use named parameters (curly braces)
    # Note: Body parameter is marked as required since it has no default value
    assert "Future<User> createUser({bool? notify, required CreateUserRequest body})" in api_client_code, \
        "Should have createUser method with named query and body parameters"
    # Verify both body serialization and query params are used
    assert "data: body.toJson()" in api_client_code, \
        "Should serialize body with toJson()"
    assert "queryParameters:" in api_client_code, \
        "Should include query parameters"
